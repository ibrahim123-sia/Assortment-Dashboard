from datetime import datetime
from extensions import db


class Store(db.Model):
    __tablename__ = "stores"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    contact_email = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    theme_mode = db.Column(db.String(16), nullable=False, default="light")
    brand_primary_color = db.Column(db.String(16), nullable=True)
    brand_logo_path = db.Column(db.String(512), nullable=True)
    active_dataset_id = db.Column(db.String(36), db.ForeignKey("datasets.id", ondelete="SET NULL", use_alter=True, name="fk_store_active_dataset"), nullable=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    disabled_at = db.Column(db.DateTime, nullable=True)
    disabled_reason = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = db.relationship(
        "User",
        foreign_keys="User.store_id",
        back_populates="store",
        cascade="save-update, merge",
    )
    datasets = db.relationship(
        "Dataset",
        foreign_keys="Dataset.store_id",
        back_populates="store",
        cascade="all, delete-orphan",
    )
    active_dataset = db.relationship(
        "Dataset",
        foreign_keys=[active_dataset_id],
        post_update=True,
    )

    def to_dict(self, include_counts=False):
        data = {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "contact_email": self.contact_email,
            "is_active": self.is_active,
            "theme_mode": self.theme_mode,
            "brand_primary_color": self.brand_primary_color,
            "active_dataset_id": self.active_dataset_id,
            "disabled_at": self.disabled_at.isoformat() if self.disabled_at else None,
            "disabled_reason": self.disabled_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_counts:
            manager = next((u for u in self.users if u.role == "store_manager"), None)
            data["manager_email"] = manager.email if manager else None
            data["manager_name"] = manager.full_name if manager else None
            data["dataset_count"] = len(self.datasets)
            last_upload = max((d.uploaded_at for d in self.datasets), default=None)
            data["last_upload_at"] = last_upload.isoformat() if last_upload else None
        return data
