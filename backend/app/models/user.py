from datetime import datetime
from extensions import db


class UserRole:
    SUPER_ADMIN = "super_admin"
    STORE_MANAGER = "store_manager"
    ALL = (SUPER_ADMIN, STORE_MANAGER)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False, default=UserRole.STORE_MANAGER)
    full_name = db.Column(db.String(255), nullable=False, default="")
    is_email_verified = db.Column(db.Boolean, nullable=False, default=True)
    email_verification_token = db.Column(db.String(255), nullable=True)
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    must_change_password = db.Column(db.Boolean, nullable=False, default=False)
    last_login_at = db.Column(db.DateTime, nullable=True)
    failed_login_count = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    store = db.relationship(
        "Store",
        foreign_keys=[store_id],
        back_populates="users",
    )

    def to_dict(self, include_store=False):
        data = {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "must_change_password": self.must_change_password,
            "store_id": self.store_id,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_store and self.store:
            data["store"] = self.store.to_dict()
        return data

    @property
    def is_super_admin(self):
        return self.role == UserRole.SUPER_ADMIN

    @property
    def is_store_manager(self):
        return self.role == UserRole.STORE_MANAGER
