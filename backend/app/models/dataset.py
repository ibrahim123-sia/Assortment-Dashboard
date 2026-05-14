import uuid
from datetime import datetime
from extensions import db


class DatasetStatus:
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


def _uuid():
    return str(uuid.uuid4())


class Dataset(db.Model):
    __tablename__ = "datasets"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    original_filename = db.Column(db.String(512), nullable=False)
    parquet_path = db.Column(db.String(1024), nullable=True)
    row_count = db.Column(db.Integer, nullable=True)
    column_mapping = db.Column(db.JSON, nullable=True)
    date_range_start = db.Column(db.DateTime, nullable=True)
    date_range_end = db.Column(db.DateTime, nullable=True)
    file_size_bytes = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(32), nullable=False, default=DatasetStatus.UPLOADED, index=True)
    validation_errors = db.Column(db.JSON, nullable=True)
    uploaded_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    notes = db.Column(db.Text, nullable=True)

    store = db.relationship(
        "Store",
        foreign_keys=[store_id],
        back_populates="datasets",
    )

    def to_dict(self, is_active=False):
        return {
            "id": self.id,
            "store_id": self.store_id,
            "original_filename": self.original_filename,
            "row_count": self.row_count,
            "file_size_bytes": self.file_size_bytes,
            "status": self.status,
            "validation_errors": self.validation_errors,
            "date_range_start": self.date_range_start.isoformat() if self.date_range_start else None,
            "date_range_end": self.date_range_end.isoformat() if self.date_range_end else None,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "notes": self.notes,
            "is_active": is_active,
        }
