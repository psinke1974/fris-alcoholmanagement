from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    gap_prompt_dismissed_until = db.Column(db.Date, nullable=True)
    # Alleen gezet bij tijdelijke accounts in demo-modus; daarna wordt het account automatisch verwijderd.
    demo_expires_at = db.Column(db.DateTime, nullable=True, index=True)

    profile = db.relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    credentials = db.relationship("WebAuthnCredential", back_populates="user", cascade="all, delete-orphan")
    drink_logs = db.relationship("DrinkLog", back_populates="user", cascade="all, delete-orphan")
    goals = db.relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    journal_entries = db.relationship("JournalEntry", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Profile(db.Model):
    __tablename__ = "profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=True, index=True)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    education = db.Column(db.String(100))
    country = db.Column(db.String(100))

    user = db.relationship("User", back_populates="profile")


class WebAuthnCredential(db.Model):
    __tablename__ = "webauthn_credentials"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    credential_id = db.Column(db.LargeBinary, unique=True, nullable=False)
    public_key = db.Column(db.LargeBinary, nullable=False)
    sign_count = db.Column(db.Integer, default=0)
    device_name = db.Column(db.String(100), default="Passkey")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="credentials")
