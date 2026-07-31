from __future__ import annotations

import importlib.util
import json
import os
import sys
from collections.abc import Callable, Mapping
from zoneinfo import ZoneInfo


os.environ["INVOICE_LOAD_LOCAL_ENV"] = "0"

TRUE_VALUES = frozenset({"1", "true", "yes", "tak", "on"})


def _enabled(value: str | None) -> bool:
    return str(value or "").strip().lower() in TRUE_VALUES


def evaluate_environment(
    environment: Mapping[str, str],
    *,
    database_probe: Callable[[], dict] | None = None,
) -> dict:
    checks: list[dict[str, object]] = []

    def add(check_id: str, passed: bool, detail: str) -> None:
        checks.append({"id": check_id, "status": "pass" if passed else "fail", "detail": detail})

    engine = str(environment.get("INVOICE_DB_ENGINE", "") or "").strip().lower()
    dsn_present = bool(
        str(environment.get("INVOICE_DATABASE_URL", "") or "").strip()
        or str(environment.get("DATABASE_URL", "") or "").strip()
    )
    bootstrap_mode = str(environment.get("INVOICE_DATABASE_BOOTSTRAP_MODE", "") or "").strip().lower()
    storage_backend = str(environment.get("INVOICE_STORAGE_BACKEND", "") or "").strip().lower()
    durable_required = _enabled(environment.get("INVOICE_REQUIRE_DURABLE_STORAGE"))
    seed_enabled = _enabled(environment.get("INVOICE_ENABLE_DEMO_SEED"))
    reset_enabled = _enabled(environment.get("CASI_ALLOW_LOCAL_SANDBOX_RESET"))
    scheduler_enabled = _enabled(environment.get("INTERNAL_NOTIFICATION_SCHEDULER_RUNTIME_ENABLED"))
    storage_tls_required = _enabled(environment.get("INVOICE_S3_REQUIRE_TLS", "true"))

    add("python_runtime", sys.version_info[:3] == (3, 11, 9), "Python 3.11.9")
    for module in ("psycopg", "boto3", "tzdata"):
        add(f"module_{module}", importlib.util.find_spec(module) is not None, f"module {module}")
    add("database_engine", engine in {"postgres", "postgresql"}, "PostgreSQL selected explicitly")
    add("database_dsn", dsn_present, "PostgreSQL DSN present")
    add("bootstrap_mode", bootstrap_mode == "validate", "bootstrap mode validate")
    add("durable_storage", durable_required, "durable storage required")
    add("storage_backend", storage_backend == "s3", "S3-compatible backend selected")
    for key in (
        "INVOICE_S3_ENDPOINT_URL",
        "INVOICE_S3_BUCKET",
        "INVOICE_S3_ACCESS_KEY_ID",
        "INVOICE_S3_SECRET_ACCESS_KEY",
    ):
        add(f"env_{key.lower()}", bool(str(environment.get(key, "") or "").strip()), f"{key} present")
    endpoint = str(environment.get("INVOICE_S3_ENDPOINT_URL", "") or "").strip()
    add("storage_tls_required", storage_tls_required, "S3 TLS requirement enabled")
    add("storage_tls", endpoint.lower().startswith("https://"), "S3 endpoint uses HTTPS")
    try:
        ZoneInfo("Europe/Warsaw")
        timezone_ready = True
    except Exception:
        timezone_ready = False
    add("timezone", timezone_ready, "Europe/Warsaw available")
    add("seed_disabled", not seed_enabled, "demo seed disabled")
    add("reset_disabled", not reset_enabled, "local reset guard disabled")
    add("scheduler_runtime", not scheduler_enabled, "scheduler runtime disabled for initial staging")
    add("no_sqlite_fallback", engine in {"postgres", "postgresql"} and dsn_present, "no SQLite fallback")
    add("no_local_storage_fallback", durable_required and storage_backend == "s3", "no local storage fallback")

    safe_for_probe = (
        engine in {"postgres", "postgresql"}
        and dsn_present
        and bootstrap_mode == "validate"
        and durable_required
        and storage_backend == "s3"
    )
    if safe_for_probe and database_probe is not None:
        try:
            schema_status = database_probe()
            add("database_read_only", True, "read-only database connection")
            add("schema_ready", bool(schema_status.get("ready")), "schema version ready")
        except Exception:
            add("database_read_only", False, "read-only database connection failed")
            add("schema_ready", False, "schema readiness unavailable")
    else:
        add("database_read_only", False, "database probe not safe or unavailable")
        add("schema_ready", False, "schema readiness unavailable")

    passed = all(item["status"] == "pass" for item in checks)
    return {
        "status": "pass" if passed else "fail",
        "checks": checks,
        "scheduler_runtime_enabled": scheduler_enabled,
        "exit_code": 0 if passed else 1,
    }


def _database_probe() -> dict:
    from app.db import database_schema_status_read_only

    return database_schema_status_read_only()


def main() -> int:
    report = evaluate_environment(os.environ, database_probe=_database_probe)
    print(json.dumps(report, ensure_ascii=False, separators=(",", ":")))
    return int(report["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
