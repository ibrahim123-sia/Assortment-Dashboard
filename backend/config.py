import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


def _bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=_int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES"), 900))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=_int(os.environ.get("JWT_REFRESH_TOKEN_EXPIRES"), 604800))
    JWT_TOKEN_LOCATION = ["headers"]

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    STORES_DIR = os.path.join(DATA_DIR, "stores")

    _db_url = os.environ.get("DATABASE_URL", "sqlite:///data/app.sqlite")
    if _db_url.startswith("sqlite:///") and not _db_url.startswith("sqlite:////"):
        rel = _db_url.replace("sqlite:///", "", 1)
        if not os.path.isabs(rel):
            _db_url = "sqlite:///" + os.path.join(BASE_DIR, rel).replace("\\", "/")
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = _int(os.environ.get("MAIL_PORT"), 587)
    MAIL_USE_TLS = _bool(os.environ.get("MAIL_USE_TLS"), True)
    MAIL_USE_SSL = _bool(os.environ.get("MAIL_USE_SSL"), False)
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME") or None
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD") or None
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "no-reply@example.com")
    MAIL_SUPPRESS_SEND = _bool(os.environ.get("MAIL_SUPPRESS_SEND"), False)

    SUPER_ADMIN_EMAIL = os.environ.get("SUPER_ADMIN_EMAIL", "admin@example.com")
    SUPER_ADMIN_PASSWORD = os.environ.get("SUPER_ADMIN_PASSWORD", "Admin@12345")
    SUPER_ADMIN_NAME = os.environ.get("SUPER_ADMIN_NAME", "Super Admin")

    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    ALLOWED_ORIGINS = [
        o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",") if o.strip()
    ]

    MAX_UPLOAD_MB = _int(os.environ.get("MAX_UPLOAD_MB"), 50)
    MAX_CONTENT_LENGTH = MAX_UPLOAD_MB * 1024 * 1024
    MAX_ROWS_PER_DATASET = _int(os.environ.get("MAX_ROWS_PER_DATASET"), 1_000_000)

    PASSWORD_RESET_TTL_MINUTES = _int(os.environ.get("PASSWORD_RESET_TTL_MINUTES"), 60)
    LOGIN_LOCKOUT_THRESHOLD = _int(os.environ.get("LOGIN_LOCKOUT_THRESHOLD"), 5)
    LOGIN_LOCKOUT_MINUTES = _int(os.environ.get("LOGIN_LOCKOUT_MINUTES"), 15)

    DEBUG = _bool(os.environ.get("FLASK_DEBUG"), False)


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


def get_config():
    env = os.environ.get("FLASK_ENV", "development").lower()
    if env == "production":
        return ProductionConfig
    return DevelopmentConfig
