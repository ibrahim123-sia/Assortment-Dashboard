from datetime import datetime
from flask import Blueprint, jsonify, request, g, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)

from extensions import db
from app.models import User, Store, UserRole
from app.decorators import auth_required
from app.services import auth_service
from app.services.audit_service import log_event
from app.services.email_service import send_password_reset_email

bp = Blueprint("auth", __name__)


def _tokens_for(user):
    identity = str(user.id)
    return {
        "access_token": create_access_token(identity=identity, additional_claims={"role": user.role}),
        "refresh_token": create_refresh_token(identity=identity, additional_claims={"role": user.role}),
    }


def _user_payload(user):
    store = None
    if user.store_id:
        store_obj = db.session.get(Store, user.store_id)
        if store_obj:
            store = store_obj.to_dict()
    return {"user": user.to_dict(), "store": store}


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").lower().strip()
    password = data.get("password") or ""
    if not email or not password:
        return jsonify({"error": "Email and password required", "code": "missing_credentials"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        log_event("login_failed", metadata={"email": email, "reason": "user_not_found"})
        return jsonify({"error": "Invalid credentials", "code": "invalid_credentials"}), 401
    if not user.is_active:
        log_event("login_failed", actor=user, metadata={"reason": "user_inactive"})
        return jsonify({"error": "Account is inactive", "code": "user_inactive"}), 403
    if user.locked_until and user.locked_until > datetime.utcnow():
        return jsonify({"error": "Account temporarily locked", "code": "user_locked"}), 423

    if not auth_service.verify_password(password, user.password_hash):
        auth_service.register_failed_login(user)
        log_event("login_failed", actor=user, metadata={"reason": "bad_password"})
        return jsonify({"error": "Invalid credentials", "code": "invalid_credentials"}), 401

    if user.role == UserRole.STORE_MANAGER and user.store_id:
        store = db.session.get(Store, user.store_id)
        if store and not store.is_active:
            log_event("login_failed", actor=user, metadata={"reason": "store_disabled"})
            return jsonify({"error": "Your store has been disabled", "code": "store_disabled"}), 403

    auth_service.register_successful_login(user)
    log_event("login", actor=user)
    payload = _user_payload(user)
    payload.update(_tokens_for(user))
    return jsonify(payload)


@bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    user = db.session.get(User, int(identity)) if identity else None
    if not user or not user.is_active:
        return jsonify({"error": "Invalid refresh", "code": "invalid_refresh"}), 401
    return jsonify({"access_token": create_access_token(identity=str(user.id), additional_claims={"role": user.role})})


@bp.route("/logout", methods=["POST"])
@auth_required
def logout():
    log_event("logout", actor=g.current_user)
    return jsonify({"ok": True})


@bp.route("/me", methods=["GET"])
@auth_required
def me():
    return jsonify(_user_payload(g.current_user))


@bp.route("/change-password", methods=["POST"])
@auth_required
def change_password():
    data = request.get_json(silent=True) or {}
    current = data.get("current_password") or ""
    new = data.get("new_password") or ""
    if len(new) < 8:
        return jsonify({"error": "New password must be at least 8 characters", "code": "weak_password"}), 400
    user = g.current_user
    if not auth_service.verify_password(current, user.password_hash):
        return jsonify({"error": "Current password is incorrect", "code": "bad_current_password"}), 400
    user.password_hash = auth_service.hash_password(new)
    user.must_change_password = False
    db.session.commit()
    log_event("password_changed", actor=user)
    return jsonify({"ok": True})


@bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").lower().strip()
    log_event("password_reset_requested", metadata={"email": email})
    if email:
        user = User.query.filter_by(email=email).first()
        if user and user.is_active:
            ip = request.headers.get("X-Forwarded-For", request.remote_addr)
            token = auth_service.create_password_reset_token(user, ip=ip)
            send_password_reset_email(user, token)
    return jsonify({"ok": True, "message": "If the account exists, a reset email has been sent."})


@bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json(silent=True) or {}
    raw_token = data.get("token") or ""
    new_password = data.get("new_password") or ""
    if not raw_token or len(new_password) < 8:
        return jsonify({"error": "Invalid token or password", "code": "invalid_input"}), 400
    token = auth_service.consume_password_reset_token(raw_token)
    if not token:
        return jsonify({"error": "Token is invalid or expired", "code": "invalid_token"}), 400
    user = db.session.get(User, token.user_id)
    if not user or not user.is_active:
        return jsonify({"error": "Account not available", "code": "user_inactive"}), 400
    user.password_hash = auth_service.hash_password(new_password)
    user.must_change_password = False
    auth_service.mark_token_used(token)
    log_event("password_reset_completed", actor=user)
    return jsonify({"ok": True})
