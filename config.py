import os
from datetime import timedelta

from backend.services.hash_service import MAX_UPLOAD_BYTES


class Config:
    APP_VERSION = "2.0.0"
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///cyberguard.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    WTF_CSRF_TIME_LIMIT = 3600
    MAX_UPLOAD_BYTES = MAX_UPLOAD_BYTES
    MAX_CONTENT_LENGTH = 2 * MAX_UPLOAD_BYTES + 128 * 1024
    SESSION_PROTECTION = "strong"
