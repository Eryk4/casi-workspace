from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Mapping


os.environ["INVOICE_LOAD_LOCAL_ENV"] = "0"


class MigrationConfigurationError(ValueError):
    pass


def validate_environment(environment: Mapping[str, str] | None = None) -> None:
    source = os.environ if environment is None else environment
    engine = str(source.get("INVOICE_DB_ENGINE", "") or "").strip().lower()
    dsn = str(source.get("INVOICE_DATABASE_URL", "") or "").strip() or str(
        source.get("DATABASE_URL", "") or ""
    ).strip()
    if engine not in {"postgres", "postgresql"}:
        raise MigrationConfigurationError("Jawnie wybierz PostgreSQL.")
    if not dsn:
        raise MigrationConfigurationError("Brakuje jawnego DSN PostgreSQL.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Kontroluje lub stosuje schema-only bootstrap CASI.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    return parser


def _started_at() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _report(**values) -> None:
    print(json.dumps(values, ensure_ascii=False, separators=(",", ":")))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    mode = "check" if args.check else "apply"
    started_at = _started_at()
    started = time.perf_counter()
    try:
        validate_environment()
    except MigrationConfigurationError:
        _report(
            status="configuration_error",
            mode=mode,
            started_at_utc=started_at,
            duration_ms=round((time.perf_counter() - started) * 1000),
            exit_code=1,
        )
        return 1
    try:
        from app.db import database_schema_status_read_only, initialize_database

        if args.apply:
            initialize_database()
        status = database_schema_status_read_only()
    except Exception as error:
        _report(
            status="system_error",
            mode=mode,
            error_code=type(error).__name__,
            started_at_utc=started_at,
            duration_ms=round((time.perf_counter() - started) * 1000),
            exit_code=1,
        )
        return 1
    exit_code = 0 if status["ready"] else 3
    _report(
        status="ready" if status["ready"] else "migration_required",
        mode=mode,
        database_engine="postgresql",
        schema_ready=bool(status["ready"]),
        actual_version=status["actual_version"],
        expected_version=status["expected_version"],
        administrator_created=False,
        seed_executed=False,
        started_at_utc=started_at,
        duration_ms=round((time.perf_counter() - started) * 1000),
        exit_code=exit_code,
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
