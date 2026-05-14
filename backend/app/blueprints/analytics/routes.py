from datetime import datetime
from flask import Blueprint, jsonify, request, g

from app.decorators import store_manager_required
from app.services import dataset_service, cache_service
from app.services import analytics_service, mba_service
from app.utils.filters import apply_filters, extract_filters_from_args

bp = Blueprint("analytics", __name__)


def _df_or_error():
    df, dataset = dataset_service.get_active_dataframe(g.current_store)
    if df is None:
        return None, None, (jsonify({"success": False, "error": "No active dataset for this store. Upload data first.", "code": "no_dataset"}), 409)
    return df, dataset, None


def _cache_key(endpoint, dataset_id):
    return cache_service.make_key(g.current_store.id, dataset_id, endpoint, request.args.to_dict(flat=True))


@bp.route("/health", methods=["GET"])
@store_manager_required
def health():
    df, dataset, err = _df_or_error()
    if err:
        return err
    return jsonify({
        "status": "healthy",
        "store_id": g.current_store.id,
        "dataset_id": dataset.id if dataset else None,
        "data_records": int(len(df)),
        "transactions": int(df["InvoiceNo"].nunique()) if "InvoiceNo" in df.columns else 0,
        "products": int(df["Description"].nunique()) if "Description" in df.columns else 0,
        "total_revenue": float(df["TotalAmount"].sum()) if "TotalAmount" in df.columns else 0,
        "available_columns": list(df.columns),
        "timestamp": datetime.utcnow().isoformat(),
    })


@bp.route("/summary", methods=["GET"])
@store_manager_required
def summary():
    df, dataset, err = _df_or_error()
    if err:
        return err
    key = _cache_key("summary", dataset.id)
    data = cache_service.get_or_set(key, lambda: analytics_service.compute_summary(df))
    return jsonify({"success": True, "data": data, "timestamp": datetime.utcnow().isoformat()})


@bp.route("/association_rules", methods=["GET"])
@store_manager_required
def association_rules_route():
    df, dataset, err = _df_or_error()
    if err:
        return err
    filters = extract_filters_from_args(request.args)
    filtered = apply_filters(df, filters)
    min_support = max(0.001, float(request.args.get("min_support", 0.01)))
    min_confidence = max(0.1, float(request.args.get("min_confidence", 0.3)))
    min_lift = max(0.5, float(request.args.get("min_lift", 1.0)))
    limit = min(100, max(1, int(request.args.get("limit", 50))))
    simple = request.args.get("simple", "true").lower() == "true"
    key = _cache_key("association_rules", dataset.id)
    result = cache_service.get_or_set(
        key,
        lambda: mba_service.compute_association_rules(filtered, min_support, min_confidence, min_lift, limit, simple),
    )
    return jsonify(result)


@bp.route("/product_bundles_filtered", methods=["GET"])
@store_manager_required
def product_bundles():
    df, dataset, err = _df_or_error()
    if err:
        return err
    filters = extract_filters_from_args(request.args)
    filtered = apply_filters(df, filters)
    min_support = max(0.001, float(request.args.get("min_support", 0.01)))
    min_confidence = max(0.1, float(request.args.get("min_confidence", 0.3)))
    min_lift = max(0.5, float(request.args.get("min_lift", 1.0)))
    limit = min(100, max(1, int(request.args.get("limit", 50))))
    key = _cache_key("product_bundles_filtered", dataset.id)
    result = cache_service.get_or_set(
        key,
        lambda: mba_service.compute_product_bundles(filtered, min_support, min_confidence, min_lift, limit, filters),
    )
    return jsonify(result)


@bp.route("/seasonal_data", methods=["GET"])
@store_manager_required
def seasonal_data():
    df, dataset, err = _df_or_error()
    if err:
        return err
    key = _cache_key("seasonal_data", dataset.id)
    data = cache_service.get_or_set(key, lambda: analytics_service.compute_seasonal(df))
    return jsonify({"success": True, **data})


@bp.route("/seasonal_product_analysis", methods=["GET"])
@store_manager_required
def seasonal_product_analysis():
    df, dataset, err = _df_or_error()
    if err:
        return err
    product = request.args.get("product", "").strip()
    year = request.args.get("year", "all")
    month = request.args.get("month", "all")
    key = _cache_key("seasonal_product", dataset.id)
    data = cache_service.get_or_set(key, lambda: analytics_service.compute_seasonal_product(df, product, year, month))
    return jsonify({"success": True, **data})


@bp.route("/revenue_by_country", methods=["GET"])
@store_manager_required
def revenue_by_country():
    df, dataset, err = _df_or_error()
    if err:
        return err
    country = request.args.get("country", "all")
    year = request.args.get("year", "all")
    limit = min(50, max(1, int(request.args.get("limit", 10))))
    key = _cache_key("revenue_by_country", dataset.id)
    data = cache_service.get_or_set(key, lambda: analytics_service.compute_revenue_by_country(df, country, year, limit))
    return jsonify({"success": True, **data})


@bp.route("/frequent_itemsets", methods=["GET"])
@store_manager_required
def frequent_itemsets():
    df, dataset, err = _df_or_error()
    if err:
        return err
    min_support = max(0.001, float(request.args.get("min_support", 0.02)))
    limit = min(100, max(5, int(request.args.get("limit", 20))))
    key = _cache_key("frequent_itemsets", dataset.id)
    result = cache_service.get_or_set(key, lambda: mba_service.compute_network_graph(df, min_support, limit))
    return jsonify(result)


@bp.route("/top_products", methods=["GET"])
@store_manager_required
def top_products():
    df, dataset, err = _df_or_error()
    if err:
        return err
    filters = extract_filters_from_args(request.args)
    filtered = apply_filters(df, filters)
    sort_by = request.args.get("sort_by", "revenue")
    limit = min(100, max(1, int(request.args.get("limit", 20))))
    key = _cache_key("top_products", dataset.id)
    data = cache_service.get_or_set(key, lambda: analytics_service.compute_top_products(filtered, sort_by, limit))
    return jsonify({"success": True, **data})


@bp.route("/filters", methods=["GET"])
@store_manager_required
def filters():
    df, dataset, err = _df_or_error()
    if err:
        return err
    key = _cache_key("filters", dataset.id)
    data = cache_service.get_or_set(key, lambda: analytics_service.compute_filters(df))
    return jsonify({"success": True, "filters": data, "timestamp": datetime.utcnow().isoformat()})


@bp.route("/product_stats", methods=["GET"])
@store_manager_required
def product_stats():
    df, dataset, err = _df_or_error()
    if err:
        return err
    product_name = request.args.get("product", "").strip()
    if not product_name:
        return jsonify({"success": False, "error": "Product name is required"}), 400
    filters_dict = extract_filters_from_args(request.args)
    filtered = apply_filters(df, filters_dict)
    if len(filtered) == 0:
        return jsonify({"success": False, "error": "No data available with current filters"}), 404
    result = analytics_service.compute_product_detail(filtered, product_name)
    if not result:
        return jsonify({"success": False, "error": f"Product '{product_name}' not found"}), 404
    result["metadata"]["filters_applied"] = filters_dict
    return jsonify({"success": True, "product": result})
