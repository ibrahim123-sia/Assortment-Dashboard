import re
from datetime import datetime
from flask import Blueprint, jsonify, request, g

from extensions import db
from app.models import User, Store, UserRole, AuditLog, Dataset, ScheduledJob
from app.decorators import super_admin_required
from app.services import auth_service
from app.services.audit_service import log_event
from app.services.email_service import send_new_account_email, send_store_disabled_email

bp = Blueprint("admin", __name__)


def _slugify(name):
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "store"


def _unique_slug(base):
    slug = base
    i = 1
    while Store.query.filter_by(slug=slug).first() is not None:
        i += 1
        slug = f"{base}-{i}"
    return slug


@bp.route("/stores", methods=["GET"])
@super_admin_required
def list_stores():
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 25))))
    q = Store.query.order_by(Store.created_at.desc())
    pag = q.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "items": [s.to_dict(include_counts=True) for s in pag.items],
        "page": pag.page,
        "per_page": pag.per_page,
        "total": pag.total,
        "pages": pag.pages,
    })


@bp.route("/stores", methods=["POST"])
@super_admin_required
def create_store():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    manager_email = (data.get("manager_email") or "").lower().strip()
    manager_name = (data.get("manager_full_name") or data.get("manager_name") or "").strip() or manager_email.split("@")[0]
    description = (data.get("description") or "").strip() or None
    contact_email = (data.get("contact_email") or manager_email).lower().strip() or None
    theme_mode = data.get("theme_mode") or "light"
    brand_color = data.get("brand_primary_color") or None
    requested_slug = (data.get("slug") or "").strip().lower()

    if not name:
        return jsonify({"error": "Store name is required", "code": "missing_name"}), 400
    if not manager_email or "@" not in manager_email:
        return jsonify({"error": "Valid manager email required", "code": "invalid_email"}), 400
    if User.query.filter_by(email=manager_email).first():
        return jsonify({"error": "A user with this email already exists", "code": "email_exists"}), 409

    slug_base = _slugify(requested_slug or name)
    slug = _unique_slug(slug_base)

    store = Store(
        name=name,
        slug=slug,
        description=description,
        contact_email=contact_email,
        theme_mode=theme_mode if theme_mode in ("light", "dark") else "light",
        brand_primary_color=brand_color,
        is_active=True,
        created_by_user_id=g.current_user.id,
    )
    db.session.add(store)
    db.session.flush()

    temp_password = auth_service.generate_temp_password()
    manager = User(
        email=manager_email,
        password_hash=auth_service.hash_password(temp_password),
        role=UserRole.STORE_MANAGER,
        full_name=manager_name,
        is_email_verified=True,
        is_active=True,
        must_change_password=True,
        store_id=store.id,
    )
    db.session.add(manager)
    db.session.commit()

    log_event("store_created", actor=g.current_user, target_type="store", target_id=store.id, metadata={"name": store.name, "slug": store.slug})
    log_event("manager_created", actor=g.current_user, target_type="user", target_id=manager.id, metadata={"email": manager.email, "store_id": store.id})

    sent, err = send_new_account_email(manager, store, temp_password)
    response = {
        "store": store.to_dict(include_counts=True),
        "manager": manager.to_dict(),
        "email_sent": sent,
    }
    if not sent:
        response["temp_password"] = temp_password
        response["email_error"] = err
    return jsonify(response), 201


@bp.route("/stores/<int:store_id>", methods=["GET"])
@super_admin_required
def get_store(store_id):
    store = db.session.get(Store, store_id)
    if not store:
        return jsonify({"error": "Store not found", "code": "not_found"}), 404
    manager = next((u for u in store.users if u.role == UserRole.STORE_MANAGER), None)
    return jsonify({"store": store.to_dict(include_counts=True), "manager": manager.to_dict() if manager else None})


@bp.route("/stores/<int:store_id>", methods=["PATCH"])
@super_admin_required
def update_store(store_id):
    store = db.session.get(Store, store_id)
    if not store:
        return jsonify({"error": "Store not found", "code": "not_found"}), 404
    data = request.get_json(silent=True) or {}
    for field in ("name", "description", "contact_email", "brand_primary_color"):
        if field in data:
            setattr(store, field, data[field] or None)
    if data.get("theme_mode") in ("light", "dark"):
        store.theme_mode = data["theme_mode"]
    db.session.commit()
    log_event("store_updated", actor=g.current_user, target_type="store", target_id=store.id, metadata=data)
    return jsonify(store.to_dict(include_counts=True))


@bp.route("/stores/<int:store_id>/disable", methods=["POST"])
@super_admin_required
def disable_store(store_id):
    store = db.session.get(Store, store_id)
    if not store:
        return jsonify({"error": "Store not found", "code": "not_found"}), 404
    data = request.get_json(silent=True) or {}
    reason = (data.get("reason") or "").strip() or None
    store.is_active = False
    store.disabled_at = datetime.utcnow()
    store.disabled_reason = reason
    db.session.commit()
    log_event("store_disabled", actor=g.current_user, target_type="store", target_id=store.id, metadata={"reason": reason})
    manager = next((u for u in store.users if u.role == UserRole.STORE_MANAGER), None)
    if manager:
        send_store_disabled_email(manager, store, reason)
    return jsonify(store.to_dict(include_counts=True))


@bp.route("/stores/<int:store_id>/enable", methods=["POST"])
@super_admin_required
def enable_store(store_id):
    store = db.session.get(Store, store_id)
    if not store:
        return jsonify({"error": "Store not found", "code": "not_found"}), 404
    store.is_active = True
    store.disabled_at = None
    store.disabled_reason = None
    db.session.commit()
    log_event("store_enabled", actor=g.current_user, target_type="store", target_id=store.id)
    return jsonify(store.to_dict(include_counts=True))


@bp.route("/stores/<int:store_id>/reset-manager-password", methods=["POST"])
@super_admin_required
def reset_manager_password(store_id):
    store = db.session.get(Store, store_id)
    if not store:
        return jsonify({"error": "Store not found", "code": "not_found"}), 404
    manager = next((u for u in store.users if u.role == UserRole.STORE_MANAGER), None)
    if not manager:
        return jsonify({"error": "Store has no manager", "code": "no_manager"}), 404
    temp = auth_service.generate_temp_password()
    manager.password_hash = auth_service.hash_password(temp)
    manager.must_change_password = True
    manager.failed_login_count = 0
    manager.locked_until = None
    db.session.commit()
    log_event("manager_password_reset", actor=g.current_user, target_type="user", target_id=manager.id)
    sent, err = send_new_account_email(manager, store, temp)
    resp = {"ok": True, "email_sent": sent}
    if not sent:
        resp["temp_password"] = temp
        resp["email_error"] = err
    return jsonify(resp)


@bp.route("/audit-log", methods=["GET"])
@super_admin_required
def audit_log_list():
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(200, max(1, int(request.args.get("per_page", 50))))
    q = AuditLog.query.order_by(AuditLog.created_at.desc())
    actor = request.args.get("actor_id")
    if actor:
        q = q.filter(AuditLog.actor_user_id == int(actor))
    action = request.args.get("action")
    if action:
        q = q.filter(AuditLog.action == action)
    target_type = request.args.get("target_type")
    if target_type:
        q = q.filter(AuditLog.target_type == target_type)
    pag = q.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "items": [a.to_dict() for a in pag.items],
        "page": pag.page,
        "per_page": pag.per_page,
        "total": pag.total,
        "pages": pag.pages,
    })


@bp.route("/stats", methods=["GET"])
@super_admin_required
def admin_stats():
    total_stores = Store.query.count()
    active_stores = Store.query.filter_by(is_active=True).count()
    total_users = User.query.count()
    total_managers = User.query.filter_by(role=UserRole.STORE_MANAGER).count()
    total_datasets = Dataset.query.count()
    return jsonify({
        "total_stores": total_stores,
        "active_stores": active_stores,
        "disabled_stores": total_stores - active_stores,
        "total_users": total_users,
        "total_managers": total_managers,
        "total_datasets": total_datasets,
    })
