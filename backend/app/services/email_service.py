from flask import current_app, render_template
from flask_mail import Message
from extensions import mail
from app.services.audit_service import log_event


def _send(subject, recipients, html, text=None):
    if current_app.config.get("MAIL_SUPPRESS_SEND"):
        current_app.logger.info("MAIL_SUPPRESS_SEND is on; not sending '%s' to %s", subject, recipients)
        return False, "mail_suppressed"
    try:
        msg = Message(subject=subject, recipients=recipients, html=html, body=text or html)
        mail.send(msg)
        return True, None
    except Exception as exc:
        current_app.logger.warning("Email send failed: %s", exc)
        log_event("email_failed", metadata={"to": recipients, "subject": subject, "error": str(exc)})
        return False, str(exc)


def send_new_account_email(user, store, temp_password):
    frontend = current_app.config["FRONTEND_URL"]
    html = render_template(
        "email/new_account.html",
        user=user,
        store=store,
        temp_password=temp_password,
        login_url=f"{frontend}/login",
    )
    text = (
        f"Hello {user.full_name},\n\n"
        f"An account has been created for you to manage the store '{store.name}'.\n"
        f"Login URL: {frontend}/login\n"
        f"Email: {user.email}\n"
        f"Temporary password: {temp_password}\n\n"
        "You will be prompted to change this password after first login.\n"
    )
    return _send(f"Welcome to {store.name} - Account Created", [user.email], html, text)


def send_password_reset_email(user, token):
    frontend = current_app.config["FRONTEND_URL"]
    reset_url = f"{frontend}/reset-password?token={token}"
    html = render_template("email/password_reset.html", user=user, reset_url=reset_url)
    text = (
        f"Hello {user.full_name or user.email},\n\n"
        f"A password reset was requested for your account. Use the link below within "
        f"{current_app.config['PASSWORD_RESET_TTL_MINUTES']} minutes:\n{reset_url}\n\n"
        "If you did not request this, ignore this email.\n"
    )
    return _send("Password Reset Request", [user.email], html, text)


def send_store_disabled_email(user, store, reason):
    html = render_template("email/store_disabled.html", user=user, store=store, reason=reason)
    text = (
        f"Hello {user.full_name or user.email},\n\n"
        f"Your store '{store.name}' has been disabled. Reason: {reason or 'Not specified'}.\n"
        "Please contact the administrator for assistance.\n"
    )
    return _send(f"Store {store.name} has been disabled", [user.email], html, text)


def send_scheduled_summary_email(user, store, summary_payload):
    html = render_template(
        "email/scheduled_summary.html",
        user=user,
        store=store,
        summary=summary_payload,
    )
    return _send(f"{store.name} - Scheduled Analytics Summary", [user.email], html)
