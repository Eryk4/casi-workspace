from __future__ import annotations

import os
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"
RAILWAY_VOLUME_MOUNT_PATH = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "").strip()


def _looks_like_test_run() -> bool:
    argv = [part.lower() for part in sys.argv]
    joined = " ".join(argv)
    return "unittest" in joined or any(
        part.endswith(".py") and "test" in Path(part).name.lower()
        for part in argv
    )


def _test_runtime_root() -> Path | None:
    if os.getenv("INVOICE_DISABLE_TEST_ISOLATION", "").strip().lower() in {"1", "true", "tak", "yes"}:
        return None
    if not _looks_like_test_run():
        return None
    runtime_root = DATA_DIR / "test_runtime" / f"pid_{os.getpid()}"
    runtime_root.mkdir(parents=True, exist_ok=True)
    return runtime_root


TEST_RUNTIME_ROOT = _test_runtime_root()


def _load_local_env_files() -> None:
    candidate_files = (
        BASE_DIR / ".env.local",
        DATA_DIR / "local.env",
    )
    for file_path in candidate_files:
        if not file_path.exists() or not file_path.is_file():
            continue
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError):
            continue
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            normalized_key = key.strip().lstrip("\ufeff")
            normalized_value = value.strip()
            if (
                len(normalized_value) >= 2
                and normalized_value[0] == normalized_value[-1]
                and normalized_value[0] in {'"', "'"}
            ):
                normalized_value = normalized_value[1:-1]
            if normalized_key:
                os.environ.setdefault(normalized_key, normalized_value)


_load_local_env_files()


def _resolve_path(raw_value: str, fallback: Path) -> Path:
    candidate = Path(raw_value.strip()) if raw_value.strip() else fallback
    if not candidate.is_absolute():
        candidate = BASE_DIR / candidate
    return candidate.resolve()


def _env_int(name: str, default: int, minimum: int | None = None) -> int:
    raw_value = os.getenv(name, str(default)).strip()
    try:
        parsed = int(raw_value)
    except ValueError:
        parsed = default
    if minimum is not None:
        parsed = max(minimum, parsed)
    return parsed


DB_ENGINE = os.getenv(
    "INVOICE_DB_ENGINE",
    "postgresql",
).strip().lower()
_configured_database_url = os.getenv("INVOICE_DATABASE_URL", "").strip() or os.getenv("DATABASE_URL", "").strip()
DATABASE_URL = _configured_database_url if DB_ENGINE in {"postgres", "postgresql"} else ""
if DB_ENGINE in {"postgres", "postgresql"} and not DATABASE_URL:
    raise RuntimeError(
        "Brakuje konfiguracji PostgreSQL. Ustaw INVOICE_DATABASE_URL albo DATABASE_URL."
    )
ENABLE_DEMO_SEED = os.getenv(
    "INVOICE_ENABLE_DEMO_SEED",
    "0" if DB_ENGINE in {"postgres", "postgresql"} else "1",
).strip().lower() in {"1", "true", "tak", "yes"}
SECURE_COOKIES = os.getenv("INVOICE_SECURE_COOKIES", "0").strip().lower() in {"1", "true", "tak", "yes"}
SESSION_COOKIE_NAME = os.getenv("INVOICE_SESSION_COOKIE_NAME", "sesja_panelu")
SESSION_DURATION_HOURS = _env_int("INVOICE_SESSION_DURATION_HOURS", 24, minimum=1)
DEFAULT_ADMIN_LOGIN = os.getenv("INVOICE_DEFAULT_ADMIN_LOGIN", "admin").strip() or "admin"
DEFAULT_ADMIN_PASSWORD = os.getenv("INVOICE_DEFAULT_ADMIN_PASSWORD", "Admin1234").strip() or "Admin1234"
TELEGRAM_BOT_TOKEN = os.getenv("INVOICE_TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_WEBHOOK_SECRET = os.getenv("INVOICE_TELEGRAM_WEBHOOK_SECRET", "").strip()
SLACK_BOT_TOKEN = os.getenv("INVOICE_SLACK_BOT_TOKEN", "").strip()
SLACK_SIGNING_SECRET = os.getenv("INVOICE_SLACK_SIGNING_SECRET", "").strip()
OCR_TESSERACT_CMD = os.getenv("INVOICE_TESSERACT_CMD", "").strip()
OCR_LANGUAGE = os.getenv("INVOICE_OCR_LANGUAGE", "pol+eng").strip() or "pol+eng"
EMAIL_IMAP_HOST = os.getenv("INVOICE_EMAIL_IMAP_HOST", "").strip()
EMAIL_IMAP_PORT = _env_int("INVOICE_EMAIL_IMAP_PORT", 993, minimum=1)
EMAIL_IMAP_USERNAME = os.getenv("INVOICE_EMAIL_IMAP_USERNAME", "").strip()
EMAIL_IMAP_PASSWORD = os.getenv("INVOICE_EMAIL_IMAP_PASSWORD", "")
EMAIL_IMAP_FOLDER = os.getenv("INVOICE_EMAIL_IMAP_FOLDER", "INBOX").strip() or "INBOX"
EMAIL_IMAP_USE_SSL = os.getenv("INVOICE_EMAIL_IMAP_USE_SSL", "1").strip().lower() in {
    "1",
    "true",
    "tak",
    "yes",
}
EMAIL_FETCH_LIMIT = _env_int("INVOICE_EMAIL_FETCH_LIMIT", 30, minimum=1)
EMAIL_AUTOCHECK_ENABLED = os.getenv("INVOICE_EMAIL_AUTOCHECK_ENABLED", "0").strip().lower() in {
    "1",
    "true",
    "tak",
    "yes",
}
EMAIL_AUTOCHECK_SECONDS = _env_int("INVOICE_EMAIL_AUTOCHECK_SECONDS", 300, minimum=60)
KSEF_FETCH_LIMIT = _env_int("INVOICE_KSEF_FETCH_LIMIT", 25, minimum=1)
ENABLE_TELEGRAM_TASK_REMINDERS = os.getenv(
    "INVOICE_ENABLE_TELEGRAM_TASK_REMINDERS",
    "1",
).strip().lower() in {"1", "true", "tak", "yes"}
TASK_REMINDER_POLL_SECONDS = _env_int("INVOICE_TASK_REMINDER_POLL_SECONDS", 60, minimum=15)
TASK_REMINDER_WORKER_POLL_SECONDS = _env_int("INVOICE_TASK_REMINDER_WORKER_POLL_SECONDS", 15, minimum=5)
TASK_REMINDER_RETRY_MINUTES = _env_int("INVOICE_TASK_REMINDER_RETRY_MINUTES", 15, minimum=1)
TASK_REMINDER_PROCESSING_TIMEOUT_MINUTES = _env_int(
    "INVOICE_TASK_REMINDER_PROCESSING_TIMEOUT_MINUTES",
    10,
    minimum=1,
)
TASK_REMINDER_MAX_ATTEMPTS = _env_int("INVOICE_TASK_REMINDER_MAX_ATTEMPTS", 5, minimum=1)
KNOWLEDGE_PIPELINE_POLL_SECONDS = _env_int("INVOICE_KNOWLEDGE_PIPELINE_POLL_SECONDS", 20, minimum=5)
KNOWLEDGE_FOLDER_SCAN_SECONDS = _env_int("INVOICE_KNOWLEDGE_FOLDER_SCAN_SECONDS", 120, minimum=30)
GOOGLE_CLIENT_ID = os.getenv("INVOICE_GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.getenv("INVOICE_GOOGLE_CLIENT_SECRET", "").strip()
GOOGLE_OAUTH_SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.calendarlist.readonly",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
]
GOOGLE_OAUTH_CALLBACK_PATH = "/api/google-calendar/oauth/callback"
EMAIL_GOOGLE_CLIENT_ID = os.getenv("INVOICE_EMAIL_GOOGLE_CLIENT_ID", GOOGLE_CLIENT_ID).strip()
EMAIL_GOOGLE_CLIENT_SECRET = os.getenv("INVOICE_EMAIL_GOOGLE_CLIENT_SECRET", GOOGLE_CLIENT_SECRET).strip()
EMAIL_GOOGLE_OAUTH_SCOPES = [
    "https://mail.google.com/",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
]
EMAIL_GOOGLE_OAUTH_CALLBACK_PATH = "/api/email/oauth/callback"

default_sqlite_path = (
    TEST_RUNTIME_ROOT / "invoice_ops.sqlite3"
    if TEST_RUNTIME_ROOT is not None
    else (
        Path(RAILWAY_VOLUME_MOUNT_PATH) / "invoice_ops.sqlite3"
        if RAILWAY_VOLUME_MOUNT_PATH
        else DATA_DIR / "invoice_ops.sqlite3"
    )
)
SQLITE_DB_PATH = _resolve_path(
    os.getenv("INVOICE_SQLITE_PATH", str(default_sqlite_path)),
    default_sqlite_path,
)

default_storage_root = (
    TEST_RUNTIME_ROOT / "magazyn"
    if TEST_RUNTIME_ROOT is not None
    else (
        Path(RAILWAY_VOLUME_MOUNT_PATH) / "magazyn"
        if RAILWAY_VOLUME_MOUNT_PATH
        else DATA_DIR / "magazyn"
    )
)
STORAGE_ROOT = _resolve_path(
    os.getenv("INVOICE_STORAGE_ROOT", str(default_storage_root)),
    default_storage_root,
)
DOCUMENTS_DIR = STORAGE_ROOT / "dokumenty"
OCR_DIR = STORAGE_ROOT / "ocr"
KNOWLEDGE_DIR = STORAGE_ROOT / "wiedza"
WHITEBOARD_DIR = STORAGE_ROOT / "tablica"
BACKUPS_DIR = STORAGE_ROOT / "backup"
PUBLIC_BASE_URL = os.getenv("INVOICE_PUBLIC_BASE_URL", "").strip().rstrip("/")

DOCUMENTS_ROUTE_PREFIX = "/pliki/dokumenty/"
OCR_ROUTE_PREFIX = "/pliki/ocr/"
KNOWLEDGE_ROUTE_PREFIX = "/pliki/wiedza/"
WHITEBOARD_ROUTE_PREFIX = "/pliki/tablica/"
APP_RELEASE_ID = os.getenv("INVOICE_APP_RELEASE_ID", "").strip() or "local-dev"


def uses_postgresql() -> bool:
    return DB_ENGINE in {"postgres", "postgresql"}


def database_label() -> str:
    if uses_postgresql():
        return "PostgreSQL"
    return "SQLite"


def telegram_integration_enabled() -> bool:
    return bool(TELEGRAM_BOT_TOKEN and TELEGRAM_WEBHOOK_SECRET)


def slack_integration_enabled() -> bool:
    return bool(SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET)


def google_calendar_direct_enabled() -> bool:
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET and PUBLIC_BASE_URL)


def google_email_direct_enabled() -> bool:
    return bool(EMAIL_GOOGLE_CLIENT_ID and EMAIL_GOOGLE_CLIENT_SECRET and PUBLIC_BASE_URL)


def test_imports_enabled() -> bool:
    return os.getenv("INVOICE_ENABLE_TEST_IMPORTS", "0").strip().lower() in {"1", "true", "tak", "yes"}


def default_login_hint_enabled() -> bool:
    return os.getenv("INVOICE_SHOW_DEFAULT_LOGIN_HINT", "0").strip().lower() in {"1", "true", "tak", "yes"}


def ensure_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    OCR_DIR.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    WHITEBOARD_DIR.mkdir(parents=True, exist_ok=True)
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
