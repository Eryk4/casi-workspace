from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"
RAILWAY_VOLUME_MOUNT_PATH = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "").strip()


def _resolve_path(raw_value: str, fallback: Path) -> Path:
    candidate = Path(raw_value.strip()) if raw_value.strip() else fallback
    if not candidate.is_absolute():
        candidate = BASE_DIR / candidate
    return candidate.resolve()


DATABASE_URL = os.getenv("INVOICE_DATABASE_URL", "").strip() or os.getenv("DATABASE_URL", "").strip()
DB_ENGINE = os.getenv(
    "INVOICE_DB_ENGINE",
    "postgresql" if DATABASE_URL else "sqlite",
).strip().lower()
ENABLE_DEMO_SEED = os.getenv(
    "INVOICE_ENABLE_DEMO_SEED",
    "0" if DB_ENGINE in {"postgres", "postgresql"} else "1",
).strip().lower() in {"1", "true", "tak", "yes"}
SECURE_COOKIES = os.getenv("INVOICE_SECURE_COOKIES", "0").strip().lower() in {"1", "true", "tak", "yes"}
SESSION_COOKIE_NAME = os.getenv("INVOICE_SESSION_COOKIE_NAME", "sesja_panelu")
SESSION_DURATION_HOURS = int(os.getenv("INVOICE_SESSION_DURATION_HOURS", "24"))
DEFAULT_ADMIN_LOGIN = os.getenv("INVOICE_DEFAULT_ADMIN_LOGIN", "admin").strip() or "admin"
DEFAULT_ADMIN_PASSWORD = os.getenv("INVOICE_DEFAULT_ADMIN_PASSWORD", "Admin1234").strip() or "Admin1234"
TELEGRAM_BOT_TOKEN = os.getenv("INVOICE_TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_WEBHOOK_SECRET = os.getenv("INVOICE_TELEGRAM_WEBHOOK_SECRET", "").strip()

default_sqlite_path = (
    Path(RAILWAY_VOLUME_MOUNT_PATH) / "invoice_ops.sqlite3"
    if RAILWAY_VOLUME_MOUNT_PATH
    else DATA_DIR / "invoice_ops.sqlite3"
)
SQLITE_DB_PATH = _resolve_path(
    os.getenv("INVOICE_SQLITE_PATH", str(default_sqlite_path)),
    default_sqlite_path,
)

default_storage_root = (
    Path(RAILWAY_VOLUME_MOUNT_PATH) / "magazyn"
    if RAILWAY_VOLUME_MOUNT_PATH
    else DATA_DIR / "magazyn"
)
STORAGE_ROOT = _resolve_path(
    os.getenv("INVOICE_STORAGE_ROOT", str(default_storage_root)),
    default_storage_root,
)
DOCUMENTS_DIR = STORAGE_ROOT / "dokumenty"
OCR_DIR = STORAGE_ROOT / "ocr"
BACKUPS_DIR = STORAGE_ROOT / "backup"

DOCUMENTS_ROUTE_PREFIX = "/pliki/dokumenty/"
OCR_ROUTE_PREFIX = "/pliki/ocr/"


def uses_postgresql() -> bool:
    return DB_ENGINE in {"postgres", "postgresql"}


def database_label() -> str:
    return "PostgreSQL" if uses_postgresql() else "SQLite"


def telegram_integration_enabled() -> bool:
    return bool(TELEGRAM_BOT_TOKEN and TELEGRAM_WEBHOOK_SECRET)


def test_imports_enabled() -> bool:
    default_value = "0" if uses_postgresql() else "1"
    return os.getenv("INVOICE_ENABLE_TEST_IMPORTS", default_value).strip().lower() in {"1", "true", "tak", "yes"}


def default_login_hint_enabled() -> bool:
    default_value = "0" if uses_postgresql() else "1"
    return os.getenv("INVOICE_SHOW_DEFAULT_LOGIN_HINT", default_value).strip().lower() in {"1", "true", "tak", "yes"}


def ensure_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    OCR_DIR.mkdir(parents=True, exist_ok=True)
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
