import os
from datetime import datetime
from flask import Blueprint, jsonify, request, g, send_file, abort

from extensions import db
from app.models import Dataset, DatasetStatus, ScheduledJob, User, UserRole
from app.decorators import store_manager_required, auth_required
from app.services import dataset_service, export_service, scheduler_service
from app.services.audit_service import log_event

bp = Blueprint("store", __name__)


@bp.route("/profile", methods=["GET"])
@store_manager_required
def get_profile():
    return jsonify(g.current_store.to_dict(include_counts=True))


@bp.route("/profile", methods=["PATCH"])
@store_manager_required
def update_profile():
    store = g.current_store
    data = request.get_json(silent=True) or {}
    for field in ("name", "description", "contact_email", "brand_primary_color"):
        if field in data:
            setattr(store, field, (data[field] or None))
    if data.get("theme_mode") in ("light", "dark"):
        store.theme_mode = data["theme_mode"]
    db.session.commit()
    log_event("profile_updated", actor=g.current_user, target_type="store", target_id=store.id, metadata=data)
    return jsonify(store.to_dict(include_counts=True))


@bp.route("/datasets", methods=["GET"])
@store_manager_required
def list_datasets():
    store = g.current_store
    items = Dataset.query.filter_by(store_id=store.id).order_by(Dataset.uploaded_at.desc()).all()
    return jsonify({"items": [d.to_dict(is_active=(d.id == store.active_dataset_id)) for d in items], "active_dataset_id": store.active_dataset_id})


@bp.route("/datasets/upload", methods=["POST"])
@store_manager_required
def upload_dataset():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded", "code": "no_file"}), 400
    file_storage = request.files["file"]
    if not file_storage.filename:
        return jsonify({"error": "Empty filename", "code": "empty_filename"}), 400
    result = dataset_service.process_upload(g.current_store, file_storage, g.current_user)
    if not result.get("ok"):
        return jsonify({"error": result.get("error"), "code": result.get("code", "upload_failed")}), 400
    ds = result["dataset"]
    return jsonify({"ok": True, "dataset": ds.to_dict(is_active=(ds.id == g.current_store.active_dataset_id)), "warnings": result.get("warnings") or {}}), 201


@bp.route("/datasets/<dataset_id>/activate", methods=["POST"])
@store_manager_required
def activate_dataset(dataset_id):
    ds = db.session.get(Dataset, dataset_id)
    if not ds or ds.store_id != g.current_store.id:
        return jsonify({"error": "Dataset not found", "code": "not_found"}), 404
    ok, err = dataset_service.activate_dataset(g.current_store, ds, actor=g.current_user)
    if not ok:
        return jsonify({"error": err, "code": "cannot_activate"}), 400
    return jsonify({"ok": True})


@bp.route("/datasets/<dataset_id>", methods=["DELETE"])
@store_manager_required
def delete_dataset(dataset_id):
    ds = db.session.get(Dataset, dataset_id)
    if not ds or ds.store_id != g.current_store.id:
        return jsonify({"error": "Dataset not found", "code": "not_found"}), 404
    ok, err = dataset_service.delete_dataset(g.current_store, ds, actor=g.current_user)
    if not ok:
        return jsonify({"error": err, "code": "cannot_delete"}), 400
    return jsonify({"ok": True})


@bp.route("/scheduled-job", methods=["GET"])
@store_manager_required
def get_scheduled_job():
    job = ScheduledJob.query.filter_by(store_id=g.current_store.id).first()
    return jsonify(job.to_dict() if job else None)


@bp.route("/scheduled-job", methods=["PUT"])
@store_manager_required
def upsert_scheduled_job():
    data = request.get_json(silent=True) or {}
    job = ScheduledJob.query.filter_by(store_id=g.current_store.id).first()
    if not job:
        job = ScheduledJob(store_id=g.current_store.id)
        db.session.add(job)
    job.is_enabled = bool(data.get("is_enabled", False))
    job.cron_expression = (data.get("cron_expression") or job.cron_expression or "0 2 * * *").strip()
    job.email_summary_to = (data.get("email_summary_to") or "").strip() or None
    db.session.commit()

    from flask import current_app
    if job.is_enabled:
        scheduler_service.register_job(current_app, job)
    else:
        scheduler_service.unregister_job(job.store_id)
    log_event("scheduled_job_updated", actor=g.current_user, target_type="store", target_id=g.current_store.id, metadata={"enabled": job.is_enabled, "cron": job.cron_expression})
    return jsonify(job.to_dict())


@bp.route("/exports/pdf", methods=["POST"])
@store_manager_required
def export_pdf():
    data = request.get_json(silent=True) or {}
    sections = data.get("sections") or ["summary", "top_rules", "top_products"]
    df, dataset = dataset_service.get_active_dataframe(g.current_store)
    if df is None:
        return jsonify({"error": "No active dataset", "code": "no_dataset"}), 409
    from app.services import analytics_service, mba_service
    payloads = {}
    if "summary" in sections:
        payloads["summary"] = analytics_service.compute_summary(df)
    if "top_rules" in sections:
        rules = mba_service.compute_association_rules(df, limit=10)
        payloads["rules"] = rules.get("data", [])
    if "top_products" in sections:
        payloads["products"] = analytics_service.compute_top_products(df, limit=20).get("products", [])

    export_id, path = export_service.generate_pdf_report(g.current_store, sections, payloads)
    log_event("export_generated", actor=g.current_user, target_type="store", target_id=g.current_store.id, metadata={"type": "pdf", "export_id": export_id})
    return jsonify({"export_id": export_id, "download_url": f"/api/store/exports/{export_id}/download"})


@bp.route("/exports/<export_id>/download", methods=["GET"])
@store_manager_required
def download_export(export_id):
    from flask import current_app
    path = os.path.join(current_app.config["STORES_DIR"], str(g.current_store.id), "exports", f"{export_id}.pdf")
    if not os.path.exists(path):
        return jsonify({"error": "Export not found", "code": "not_found"}), 404
    return send_file(path, as_attachment=True, download_name=f"{g.current_store.slug}-report-{export_id[:8]}.pdf")


@bp.route("/exports/csv", methods=["GET"])
@store_manager_required
def export_csv():
    from app.services import analytics_service
    df, dataset = dataset_service.get_active_dataframe(g.current_store)
    if df is None:
        return jsonify({"error": "No active dataset", "code": "no_dataset"}), 409
    kind = request.args.get("type", "top_products")
    if kind == "top_products":
        out_df = __import__("pandas").DataFrame(analytics_service.compute_top_products(df, limit=200).get("products", []))
    elif kind == "summary":
        out_df = __import__("pandas").DataFrame([analytics_service.compute_summary(df)])
    elif kind == "raw":
        out_df = df.head(50000)
    else:
        return jsonify({"error": "Unknown export type", "code": "bad_type"}), 400
    buf = export_service.dataframe_to_csv_stream(out_df)
    log_event("export_generated", actor=g.current_user, target_type="store", target_id=g.current_store.id, metadata={"type": kind})
    from flask import Response
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={g.current_store.slug}-{kind}.csv"},
    )
