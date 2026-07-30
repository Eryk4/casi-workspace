from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Mapping
from zoneinfo import ZoneInfo


RUNTIME_ENABLED_ENV = "INTERNAL_NOTIFICATION_SCHEDULER_RUNTIME_ENABLED"
ENABLED_VALUES = frozenset({"1", "true", "yes", "tak", "on"})
DEFAULT_BATCH_LIMIT = 100
CHECK_TIMEZONE_NAME = "Europe/Warsaw"


class RuntimeConfigurationError(ValueError):
    pass


def runtime_enabled(environment: Mapping[str, str] | None = None) -> bool:
    source = os.environ if environment is None else environment
    return str(source.get(RUNTIME_ENABLED_ENV, "") or "").strip().lower() in ENABLED_VALUES


def validate_runtime_environment(environment: Mapping[str, str] | None = None) -> dict[str, str]:
    source = os.environ if environment is None else environment
    engine = str(source.get("INVOICE_DB_ENGINE", "") or "").strip().lower()
    if engine not in {"sqlite", "sqlite3", "postgres", "postgresql"}:
        raise RuntimeConfigurationError("INVOICE_DB_ENGINE musi jawnie wskazywac sqlite albo postgresql.")
    if engine in {"sqlite", "sqlite3"}:
        if not str(source.get("INVOICE_SQLITE_PATH", "") or "").strip():
            raise RuntimeConfigurationError("Dla SQLite wymagane jest jawne INVOICE_SQLITE_PATH.")
        normalized_engine = "sqlite"
    else:
        database_url = str(source.get("INVOICE_DATABASE_URL", "") or "").strip() or str(
            source.get("DATABASE_URL", "") or ""
        ).strip()
        if not database_url:
            raise RuntimeConfigurationError("Dla PostgreSQL wymagane jest INVOICE_DATABASE_URL albo DATABASE_URL.")
        normalized_engine = "postgresql"
    return {"database_engine": normalized_engine}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Uruchamia operacyjny runtime schedulera powiadomien.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--once", action="store_true", help="Wykonaj jeden ograniczony przebieg i zakoncz proces.")
    mode.add_argument("--check", action="store_true", help="Sprawdz konfiguracje i due schedules bez zapisu.")
    return parser


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _duration_ms(started: float) -> int:
    return max(0, round((time.perf_counter() - started) * 1000))


def _print_report(report: dict, *, error: bool = False) -> None:
    target = sys.stderr if error else sys.stdout
    print(json.dumps(report, ensure_ascii=False, separators=(",", ":")), file=target)


def _disabled_report(*, mode: str, started_at: str, started: float) -> dict:
    return {
        "status": "disabled",
        "runtime_status": "disabled",
        "mode": mode,
        "started_at_utc": started_at,
        "duration_ms": _duration_ms(started),
        "exit_code": 0,
    }


def _configuration_error_report(*, mode: str, started_at: str, started: float) -> dict:
    return {
        "status": "configuration_error",
        "runtime_status": "enabled",
        "mode": mode,
        "started_at_utc": started_at,
        "duration_ms": _duration_ms(started),
        "error_code": "invalid_runtime_configuration",
        "exit_code": 1,
    }


def _system_error_report(*, mode: str, started_at: str, started: float, error: Exception) -> dict:
    return {
        "status": "system_error",
        "runtime_status": "enabled",
        "mode": mode,
        "started_at_utc": started_at,
        "duration_ms": _duration_ms(started),
        "error_code": type(error).__name__,
        "exit_code": 1,
    }


def _run_check(*, config: dict[str, str], started_at: str, started: float) -> dict:
    ZoneInfo(CHECK_TIMEZONE_NAME)
    from app.domain.internal_notification_schedule import utc_iso
    from app.repositories.internal_notification_schedule_repository import InternalNotificationScheduleRepository

    due_schedules = InternalNotificationScheduleRepository().count_due_schedules_read_only(
        now_utc=utc_iso(datetime.now(timezone.utc))
    )
    return {
        "status": "ok",
        "runtime_status": "enabled",
        "mode": "check",
        "started_at_utc": started_at,
        "duration_ms": _duration_ms(started),
        "database_engine": config["database_engine"],
        "database_connection": "read_only_ok",
        "timezone": CHECK_TIMEZONE_NAME,
        "timezone_status": "available",
        "due_schedules": due_schedules,
        "batch_limit": DEFAULT_BATCH_LIMIT,
        "exit_code": 0,
    }


def _run_once(*, started_at: str, started: float) -> dict:
    from app.bootstrap import build_services

    report = build_services()["internal_notification_scheduler_service"].run_once(limit=DEFAULT_BATCH_LIMIT)
    runs = list(report.get("runs") or [])
    created_notifications = sum(int(item.get("created_count") or 0) for item in runs)
    existing_notifications = sum(int(item.get("existing_count") or 0) for item in runs)
    return {
        **report,
        "runtime_status": "enabled",
        "mode": "once",
        "started_at_utc": started_at,
        "duration_ms": _duration_ms(started),
        "due_schedules": int(report.get("checked_schedules") or 0),
        "created_notifications": created_notifications,
        "existing_notifications": existing_notifications,
        "batch_limit": DEFAULT_BATCH_LIMIT,
        "exit_code": 0,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    mode = "check" if args.check else "once"
    started_at = _timestamp()
    started = time.perf_counter()
    if not runtime_enabled():
        _print_report(_disabled_report(mode=mode, started_at=started_at, started=started))
        return 0
    try:
        config = validate_runtime_environment()
    except RuntimeConfigurationError:
        _print_report(
            _configuration_error_report(mode=mode, started_at=started_at, started=started),
            error=True,
        )
        return 1
    try:
        report = (
            _run_check(config=config, started_at=started_at, started=started)
            if args.check
            else _run_once(started_at=started_at, started=started)
        )
    except Exception as error:
        _print_report(
            _system_error_report(mode=mode, started_at=started_at, started=started, error=error),
            error=True,
        )
        return 1
    _print_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
