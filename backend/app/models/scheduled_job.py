from datetime import datetime
from extensions import db


class ScheduledJob(db.Model):
    __tablename__ = "scheduled_jobs"

    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, unique=True)
    is_enabled = db.Column(db.Boolean, nullable=False, default=False)
    cron_expression = db.Column(db.String(64), nullable=False, default="0 2 * * *")
    email_summary_to = db.Column(db.String(255), nullable=True)
    last_run_at = db.Column(db.DateTime, nullable=True)
    last_run_status = db.Column(db.String(32), nullable=True)
    last_run_error = db.Column(db.Text, nullable=True)
    next_run_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "store_id": self.store_id,
            "is_enabled": self.is_enabled,
            "cron_expression": self.cron_expression,
            "email_summary_to": self.email_summary_to,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "last_run_status": self.last_run_status,
            "last_run_error": self.last_run_error,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
        }
