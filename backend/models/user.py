from datetime import datetime, timezone

from flask_login import UserMixin
from sqlalchemy import CheckConstraint
from werkzeug.security import check_password_hash, generate_password_hash

from backend.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("length(username) BETWEEN 3 AND 30", name="ck_users_username_length"),
    )

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30, collation="NOCASE"), unique=True, nullable=False)
    email = db.Column(db.String(254, collation="NOCASE"), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    activities = db.relationship(
        "Activity",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(Activity.timestamp)",
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
