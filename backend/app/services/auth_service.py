import hashlib
import secrets
import string
from datetime import datetime, timedelta

from flask import current_app
from extensions import db, bcrypt
from app.models import User, UserRole, PasswordResetToken


def hash_password(plain):
    return bcrypt.generate_password_hash(plain).decode("utf-8")


def verify_password(plain, hashed):
    try:
        return bcrypt.check_password_hash(hashed, plain)
    except Exception:
        return False


def generate_temp_password(length=12):
    alphabet = string.ascii_letters + string.digits + "!@#$%&*"
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(c.islower() for c in pwd)
            and any(c.isupper() for c in pwd)
            and any(c.isdigit() for c in pwd)
        ):
            return pwd


def ensure_super_admin():
    cfg = current_app.config
    email = cfg["SUPER_ADMIN_EMAIL"].lower().strip()
    existing = User.query.filter_by(email=email).first()
    if existing:
        if existing.role != UserRole.SUPER_ADMIN:
            existing.role = UserRole.SUPER_ADMIN
            db.session.commit()
        return existing
    admin = User(
        email=email,
        password_hash=hash_password(cfg["SUPER_ADMIN_PASSWORD"]),
        role=UserRole.SUPER_ADMIN,
        full_name=cfg["SUPER_ADMIN_NAME"],
        is_email_verified=True,
        is_active=True,
        must_change_password=False,
    )
    db.session.add(admin)
    db.session.commit()
    current_app.logger.info("Bootstrapped super admin: %s", email)
    return admin


def register_failed_login(user):
    cfg = current_app.config
    user.failed_login_count = (user.failed_login_count or 0) + 1
    if user.failed_login_count >= cfg["LOGIN_LOCKOUT_THRESHOLD"]:
        user.locked_until = datetime.utcnow() + timedelta(minutes=cfg["LOGIN_LOCKOUT_MINUTES"])
        user.failed_login_count = 0
    db.session.commit()


def register_successful_login(user):
    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = datetime.utcnow()
    db.session.commit()


def _token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_password_reset_token(user, ip=None):
    PasswordResetToken.query.filter_by(user_id=user.id, used_at=None).delete()
    raw = secrets.token_urlsafe(48)
    ttl = current_app.config["PASSWORD_RESET_TTL_MINUTES"]
    token = PasswordResetToken(
        user_id=user.id,
        token_hash=_token_hash(raw),
        expires_at=datetime.utcnow() + timedelta(minutes=ttl),
        created_ip=ip,
    )
    db.session.add(token)
    db.session.commit()
    return raw


def consume_password_reset_token(raw_token):
    token = PasswordResetToken.query.filter_by(token_hash=_token_hash(raw_token)).first()
    if not token or not token.is_valid:
        return None
    return token


def mark_token_used(token):
    token.used_at = datetime.utcnow()
    db.session.commit()
