from functools import wraps
from datetime import datetime
from flask import jsonify, request, g
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from app.models import User, Store, UserRole


def _resolve_user():
    identity = get_jwt_identity()
    if identity is None:
        return None
    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return None
    return db.session.get(User, user_id)


def auth_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user = _resolve_user()
        if not user or not user.is_active:
            return jsonify({"error": "Account inactive or not found", "code": "user_inactive"}), 401
        if user.locked_until and user.locked_until > datetime.utcnow():
            return jsonify({"error": "Account temporarily locked", "code": "user_locked"}), 423
        g.current_user = user
        return fn(*args, **kwargs)

    return wrapper


def super_admin_required(fn):
    @wraps(fn)
    @auth_required
    def wrapper(*args, **kwargs):
        if g.current_user.role != UserRole.SUPER_ADMIN:
            return jsonify({"error": "Super admin required", "code": "forbidden"}), 403
        return fn(*args, **kwargs)

    return wrapper


def store_manager_required(fn):
    """Allow store managers; super admins can also access if they pass ?store_id=."""
    @wraps(fn)
    @auth_required
    def wrapper(*args, **kwargs):
        user = g.current_user
        if user.role == UserRole.SUPER_ADMIN:
            store_id = request.args.get("store_id")
            if not store_id and request.is_json:
                store_id = (request.get_json(silent=True) or {}).get("store_id")
            if not store_id:
                return jsonify({"error": "store_id query parameter required for super admin", "code": "store_id_required"}), 400
            try:
                store_id = int(store_id)
            except (TypeError, ValueError):
                return jsonify({"error": "Invalid store_id", "code": "invalid_store_id"}), 400
            store = db.session.get(Store, store_id)
            if not store:
                return jsonify({"error": "Store not found", "code": "store_not_found"}), 404
            g.current_store = store
            return fn(*args, **kwargs)

        if user.role != UserRole.STORE_MANAGER:
            return jsonify({"error": "Store manager required", "code": "forbidden"}), 403
        if not user.store_id:
            return jsonify({"error": "User has no store assigned", "code": "no_store"}), 403
        store = db.session.get(Store, user.store_id)
        if not store:
            return jsonify({"error": "Store not found", "code": "store_not_found"}), 404
        if not store.is_active:
            return jsonify({"error": "Store has been disabled", "code": "store_disabled"}), 403
        g.current_store = store
        return fn(*args, **kwargs)

    return wrapper
