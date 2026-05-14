from flask import request, has_request_context
from extensions import db
from app.models import AuditLog


def log_event(action, actor=None, target_type=None, target_id=None, metadata=None):
    ip = None
    ua = None
    if has_request_context():
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        ua = (request.headers.get("User-Agent") or "")[:512]
    entry = AuditLog(
        actor_user_id=getattr(actor, "id", None),
        actor_email_snapshot=getattr(actor, "email", None),
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id is not None else None,
        ip_address=ip,
        user_agent=ua,
        meta=metadata or None,
    )
    db.session.add(entry)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
