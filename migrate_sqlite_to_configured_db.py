from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
from contextlib import closing
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping


# This entry point must never inherit laptop-local configuration.
os.environ["INVOICE_LOAD_LOCAL_ENV"] = "0"

from app.data_migration_manifest import (  # noqa: E402
    EXCLUDED_TABLES,
    MANIFEST_BY_TABLE,
    MIGRATED_TABLES,
    MIGRATION_MANIFEST,
    ORDER_COLUMNS,
    POSTGRES_SEQUENCES,
    TABLE_ORDER,
    TableMigrationSpec,
)


IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
WINDOWS_ABSOLUTE_PATTERN = re.compile(r"^[A-Za-z]:[\\/]")
UNC_PATTERN = re.compile(r"^\\\\")


class MigrationError(RuntimeError):
    pass


class MigrationConfigurationError(MigrationError):
    pass


class MigrationValidationError(MigrationError):
    pass


def _quote_identifier(value: str) -> str:
    if not IDENTIFIER_PATTERN.fullmatch(value):
        raise MigrationValidationError("Manifest contains an unsafe SQL identifier.")
    return f'"{value}"'


def _sqlite_uri(path: Path) -> str:
    return f"file:{path.resolve().as_posix()}?mode=ro&immutable=1"


def _sqlite_connect(path: Path) -> sqlite3.Connection:
    source = path.resolve()
    if not source.exists() or not source.is_file():
        raise MigrationConfigurationError("The explicit SQLite source file does not exist.")
    connection = sqlite3.connect(_sqlite_uri(source), uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    return connection


def _sqlite_table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _sqlite_application_tables(connection: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            """
        ).fetchall()
    }


def _sqlite_table_columns(connection: sqlite3.Connection, table_name: str) -> list[str]:
    table = _quote_identifier(table_name)
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    return [str(row["name"]) for row in rows]


def _pk_token(spec: TableMigrationSpec, row: Mapping[str, Any]) -> str:
    return ":".join(str(row[column]) for column in spec.primary_key)


def _normalize_decimal(value: Any) -> str:
    try:
        decimal = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise MigrationValidationError("Invalid decimal value in a declared decimal column.") from error
    if not decimal.is_finite():
        raise MigrationValidationError("Non-finite decimal value is not migration-safe.")
    normalized = format(decimal.normalize(), "f")
    return "0" if normalized in {"-0", "-0.0"} else normalized


def _normalize_boolean(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int) and value in {0, 1}:
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on", "tak"}:
        return 1
    if normalized in {"0", "false", "no", "off", "nie"}:
        return 0
    raise MigrationValidationError("Invalid boolean value in a declared boolean column.")


def _canonical_json(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {"__invalid_json_text__": value}
    return value


def _canonical_timestamp(value: Any) -> str:
    text = str(value)
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return f"text:{text}"
    if parsed.tzinfo is None:
        # Historical naive timestamps retain their existing wall-clock semantics.
        return f"naive:{text}"
    utc_value = parsed.astimezone(timezone.utc).isoformat(timespec="microseconds")
    return utc_value.replace("+00:00", "Z")


def canonical_value(spec: TableMigrationSpec, column: str, value: Any) -> Any:
    if value is None:
        return None
    if column in spec.json_columns:
        return _canonical_json(value)
    if column in spec.decimal_columns:
        return {"decimal": _normalize_decimal(value)}
    if column in spec.boolean_columns:
        return {"boolean": _normalize_boolean(value)}
    if column in spec.timestamp_columns:
        return {"timestamp": _canonical_timestamp(value)}
    if column in spec.date_columns:
        return {"date": str(value)}
    if isinstance(value, bytes):
        return {"blob_base64": base64.b64encode(value).decode("ascii")}
    return value


def transform_for_target(spec: TableMigrationSpec, column: str, value: Any) -> Any:
    if value is None:
        return None
    if column in spec.decimal_columns:
        return Decimal(_normalize_decimal(value))
    if column in spec.boolean_columns:
        return _normalize_boolean(value)
    if column in spec.json_columns and not isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return value


def canonical_row_payload(spec: TableMigrationSpec, row: Mapping[str, Any]) -> bytes:
    payload = [
        [column, canonical_value(spec, column, row[column])]
        for column in spec.columns
    ]
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_row_hash(spec: TableMigrationSpec, row: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_row_payload(spec, row)).hexdigest()


def _legacy_source_defaults(spec: TableMigrationSpec) -> dict[str, Any]:
    return dict(spec.legacy_source_column_defaults)


def _ordered_rows(
    connection: Any,
    spec: TableMigrationSpec,
    *,
    source_compatibility: bool = False,
) -> list[Any]:
    if source_compatibility and not _sqlite_table_exists(connection, spec.source_table):
        if spec.legacy_source_optional:
            return []
        raise MigrationValidationError("A persistent manifest table is missing from the source.")
    table = _quote_identifier(spec.source_table)
    order = ", ".join(_quote_identifier(column) for column in spec.primary_key)
    rows = connection.execute(f"SELECT * FROM {table} ORDER BY {order}").fetchall()
    if not source_compatibility or not spec.legacy_source_column_defaults:
        return rows
    defaults = _legacy_source_defaults(spec)
    normalized_rows = []
    for row in rows:
        normalized = dict(row)
        for column, value in defaults.items():
            normalized.setdefault(column, value)
        normalized_rows.append(normalized)
    return normalized_rows


def _table_snapshot(
    connection: Any,
    spec: TableMigrationSpec,
    *,
    source_compatibility: bool = False,
) -> dict[str, Any]:
    rows = _ordered_rows(connection, spec, source_compatibility=source_compatibility)
    row_hashes = {_pk_token(spec, row): canonical_row_hash(spec, row) for row in rows}
    digest = hashlib.sha256()
    for primary_key, row_hash in sorted(row_hashes.items()):
        digest.update(primary_key.encode("utf-8"))
        digest.update(b"\0")
        digest.update(row_hash.encode("ascii"))
        digest.update(b"\n")
    null_counts = {
        column: sum(1 for row in rows if row[column] is None)
        for column in spec.columns
    }
    keys = list(row_hashes)
    return {
        "count": len(rows),
        "primary_keys": keys,
        "primary_key_min": keys[0] if keys else None,
        "primary_key_max": keys[-1] if keys else None,
        "canonical_hash": digest.hexdigest(),
        "row_hashes": row_hashes,
        "null_counts": null_counts,
    }


def _validate_source_schema(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    actual_tables = _sqlite_application_tables(connection)
    manifest_tables = set(MANIFEST_BY_TABLE)
    for table in sorted(actual_tables - manifest_tables):
        issues.append({"code": "unclassified_source_table", "table": table})
    for table in sorted(manifest_tables - actual_tables):
        spec = MANIFEST_BY_TABLE[table]
        if not spec.migrate or spec.legacy_source_optional:
            continue
        issues.append({"code": "manifest_table_missing_from_source", "table": table})
    for spec in MIGRATION_MANIFEST:
        if spec.source_table not in actual_tables:
            continue
        actual_columns = _sqlite_table_columns(connection, spec.source_table)
        compatible_columns = set(actual_columns) | set(_legacy_source_defaults(spec))
        if compatible_columns != set(spec.columns):
            issues.append(
                {
                    "code": "source_columns_do_not_match_manifest",
                    "table": spec.source_table,
                    "missing_columns": sorted(set(spec.columns) - set(actual_columns)),
                    "unexpected_columns": sorted(set(actual_columns) - set(spec.columns)),
                }
            )
    return issues


def _storage_path_issues(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for spec in MIGRATED_TABLES:
        if not _sqlite_table_exists(connection, spec.source_table):
            continue
        for column in spec.storage_columns:
            if column not in _sqlite_table_columns(connection, spec.source_table):
                continue
            table = _quote_identifier(spec.source_table)
            field = _quote_identifier(column)
            order = ", ".join(_quote_identifier(item) for item in spec.primary_key)
            rows = connection.execute(
                f"SELECT * FROM {table} WHERE {field} IS NOT NULL AND {field} <> '' ORDER BY {order}"
            ).fetchall()
            for row in rows:
                value = str(row[column])
                if WINDOWS_ABSOLUTE_PATTERN.match(value) or UNC_PATTERN.match(value) or value.lower().startswith("file://"):
                    issues.append(
                        {
                            "code": "absolute_storage_path",
                            "table": spec.source_table,
                            "column": column,
                            "primary_key": _pk_token(spec, row),
                        }
                    )
    return issues


def _invalid_json_issues(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for spec in MIGRATED_TABLES:
        if not spec.json_columns or not _sqlite_table_exists(connection, spec.source_table):
            continue
        actual_columns = set(_sqlite_table_columns(connection, spec.source_table))
        for row in _ordered_rows(connection, spec, source_compatibility=True):
            for column in spec.json_columns:
                if column not in actual_columns and column not in _legacy_source_defaults(spec):
                    continue
                value = row[column]
                if value in (None, "") or not isinstance(value, str):
                    continue
                try:
                    json.loads(value)
                except json.JSONDecodeError:
                    issues.append(
                        {
                            "code": "invalid_json",
                            "table": spec.source_table,
                            "column": column,
                            "primary_key": _pk_token(spec, row),
                        }
                    )
    return issues


def _relation_issues(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for row in connection.execute("PRAGMA foreign_key_check").fetchall():
        issues.append(
            {
                "code": "orphaned_foreign_key",
                "table": str(row[0]),
                "row_id": str(row[1]),
                "parent_table": str(row[2]),
            }
        )

    domain_checks = (
        (
            "invoice_ksef_override_mismatch",
            """
            SELECT override.invoice_ksef_field_override_id AS row_id
            FROM invoice_ksef_field_overrides override
            LEFT JOIN invoices invoice
              ON invoice.id = override.invoice_id
            LEFT JOIN approval_requests approval
              ON approval.approval_request_id = override.approval_request_id
            WHERE invoice.id IS NULL
               OR invoice.organization_id <> override.organization_id
               OR (
                    override.approval_request_id IS NULL
                    AND override.status <> 'approved'
               )
               OR (
                    override.approval_request_id IS NOT NULL
                    AND (
                        approval.approval_request_id IS NULL
                        OR approval.organization_id <> override.organization_id
                        OR approval.entity_type <> 'invoice'
                        OR approval.entity_id <> override.invoice_id
                    )
               )
            """,
        ),
        (
            "billing_next_step_parent_mismatch",
            """
            SELECT child.billing_next_step_event_id AS row_id
            FROM billing_next_step_events child
            LEFT JOIN billing_next_step_events parent
              ON parent.billing_next_step_event_id = child.parent_event_id
            WHERE child.parent_event_id IS NOT NULL
              AND (
                parent.billing_next_step_event_id IS NULL
                OR parent.organization_id <> child.organization_id
                OR parent.target_type <> child.target_type
                OR parent.target_id <> child.target_id
              )
            """,
        ),
        (
            "notification_source_mismatch",
            """
            SELECT notification.internal_notification_id AS row_id
            FROM internal_notifications notification
            LEFT JOIN billing_next_step_events source
              ON source.billing_next_step_event_id = notification.source_event_id
            WHERE notification.source_type = 'billing_next_step_attention'
              AND (
                source.billing_next_step_event_id IS NULL
                OR source.organization_id <> notification.organization_id
              )
            """,
        ),
        (
            "notification_state_mismatch",
            """
            SELECT state.internal_notification_state_event_id AS row_id
            FROM internal_notification_state_events state
            LEFT JOIN internal_notifications notification
              ON notification.internal_notification_id = state.notification_id
            WHERE notification.internal_notification_id IS NULL
               OR notification.organization_id <> state.organization_id
               OR notification.recipient_user_id <> state.recipient_user_id
            """,
        ),
        (
            "scheduler_run_mismatch",
            """
            SELECT run.internal_notification_schedule_run_id AS row_id
            FROM internal_notification_schedule_runs run
            LEFT JOIN internal_notification_schedules schedule
              ON schedule.internal_notification_schedule_id = run.schedule_id
            WHERE schedule.internal_notification_schedule_id IS NULL
               OR schedule.organization_id <> run.organization_id
               OR schedule.recipient_user_id <> run.recipient_user_id
            """,
        ),
    )
    actual_tables = _sqlite_application_tables(connection)
    for code, query in domain_checks:
        required = {
            token
            for token in (
                "billing_next_step_events",
                "internal_notifications",
                "internal_notification_state_events",
                "internal_notification_schedules",
                "internal_notification_schedule_runs",
            )
            if token in query
        }
        if not required.issubset(actual_tables):
            continue
        if code == "billing_next_step_parent_mismatch" and "parent_event_id" not in set(
            _sqlite_table_columns(connection, "billing_next_step_events")
        ):
            continue
        for row in connection.execute(query).fetchall():
            issues.append({"code": code, "row_id": str(row["row_id"])})
    return issues


def build_source_plan(source_path: Path) -> dict[str, Any]:
    with closing(_sqlite_connect(source_path)) as source:
        schema_issues = _validate_source_schema(source)
        storage_issues = _storage_path_issues(source)
        json_issues = _invalid_json_issues(source)
        relation_issues = _relation_issues(source)
        table_reports = {
            spec.source_table: {
                key: value
                for key, value in _table_snapshot(
                    source, spec, source_compatibility=True
                ).items()
                if key != "row_hashes"
            }
            for spec in MIGRATED_TABLES
        }
        quick_check = str(source.execute("PRAGMA quick_check").fetchone()[0])
    issues = schema_issues + storage_issues + json_issues + relation_issues
    return {
        "status": "pass" if not issues and quick_check == "ok" else "fail",
        "mode": "plan",
        "source_file": source_path.name,
        "manifest_table_count": len(MIGRATION_MANIFEST),
        "migrated_table_count": len(MIGRATED_TABLES),
        "excluded_table_count": len(EXCLUDED_TABLES),
        "excluded_tables": [
            {
                "table": spec.source_table,
                "category": spec.category,
                "reason": spec.exclusion_reason,
                "rebuild": spec.rebuild_procedure,
            }
            for spec in EXCLUDED_TABLES
        ],
        "tables": table_reports,
        "issues": issues,
        "quick_check": quick_check,
        "read_only": True,
    }


def _validate_target_environment(environment: Mapping[str, str] | None = None) -> None:
    source = os.environ if environment is None else environment
    engine = str(source.get("INVOICE_DB_ENGINE", "") or "").strip().lower()
    dsn = str(source.get("INVOICE_DATABASE_URL", "") or "").strip() or str(
        source.get("DATABASE_URL", "") or ""
    ).strip()
    if engine not in {"postgres", "postgresql"}:
        raise MigrationConfigurationError("Explicit PostgreSQL target is required.")
    if not dsn:
        raise MigrationConfigurationError("Explicit PostgreSQL DSN is required.")


def _target_has_data(connection: Any | None = None) -> bool:
    if connection is None:
        from app.db import get_connection

        with get_connection() as opened:
            return _target_has_data(opened)
    for spec in MIGRATED_TABLES:
        table = _quote_identifier(spec.target_table)
        row = connection.execute(f"SELECT COUNT(*) AS total FROM {table}").fetchone()
        if row and int(row["total"]) > 0:
            return True
    return False


def _insert_statement(spec: TableMigrationSpec) -> str:
    table = _quote_identifier(spec.target_table)
    columns = ", ".join(_quote_identifier(column) for column in spec.columns)
    placeholders = ", ".join("?" for _ in spec.columns)
    return f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"


def _copy_table(source: sqlite3.Connection, table_name: str, target_connection: Any | None = None) -> int:
    spec = MANIFEST_BY_TABLE.get(table_name)
    if spec is None or not spec.migrate:
        raise MigrationValidationError("Table is not explicitly marked for migration.")
    if not _sqlite_table_exists(source, table_name) and not spec.legacy_source_optional:
        raise MigrationValidationError("A persistent manifest table is missing from the source.")
    if not _sqlite_table_exists(source, table_name):
        return 0
    actual_columns = _sqlite_table_columns(source, table_name)
    compatible_columns = set(actual_columns) | set(_legacy_source_defaults(spec))
    if compatible_columns != set(spec.columns):
        raise MigrationValidationError("Source columns do not match the canonical manifest.")
    rows = _ordered_rows(source, spec, source_compatibility=True)

    def execute(target: Any) -> None:
        statement = _insert_statement(spec)
        for row in rows:
            target.execute(
                statement,
                [transform_for_target(spec, column, row[column]) for column in spec.columns],
            )

    if target_connection is None:
        from app.db import get_connection

        with get_connection() as opened:
            execute(opened)
    else:
        execute(target_connection)
    return len(rows)


def _reset_postgres_sequences(connection: Any | None = None) -> None:
    if connection is None:
        from app.db import get_connection

        with get_connection() as opened:
            _reset_postgres_sequences(opened)
        return
    for table_name, id_column in POSTGRES_SEQUENCES.items():
        table = _quote_identifier(table_name)
        column = _quote_identifier(id_column)
        connection.execute(
            f"""
            SELECT setval(
                pg_get_serial_sequence('{table_name}', '{id_column}'),
                COALESCE(MAX({column}), 1),
                MAX({column}) IS NOT NULL
            )
            FROM {table}
            """
        )


def apply_data_migration(source_path: Path) -> dict[str, Any]:
    _validate_target_environment()
    plan = build_source_plan(source_path)
    if plan["status"] != "pass":
        raise MigrationValidationError("Source plan contains blocking issues.")
    from app.db import get_connection, validate_database_schema

    validate_database_schema()
    summary: dict[str, int] = {}
    with closing(_sqlite_connect(source_path)) as source, get_connection() as target:
        if _target_has_data(target):
            raise MigrationValidationError("Target persistent tables must be empty.")
        for spec in MIGRATED_TABLES:
            summary[spec.source_table] = _copy_table(source, spec.source_table, target)
        _reset_postgres_sequences(target)
    return {
        "status": "pass",
        "mode": "apply",
        "source_file": source_path.name,
        "transaction_scope": "all_persistent_tables",
        "target_required_empty": True,
        "tables": summary,
        "sequences_reset": sorted(POSTGRES_SEQUENCES),
    }


def verify_data_migration(source_path: Path) -> dict[str, Any]:
    _validate_target_environment()
    from app.db import get_read_only_connection, validate_database_schema

    validate_database_schema()
    table_reports: dict[str, Any] = {}
    with closing(_sqlite_connect(source_path)) as source, get_read_only_connection() as target:
        for spec in MIGRATED_TABLES:
            source_snapshot = _table_snapshot(source, spec, source_compatibility=True)
            target_snapshot = _table_snapshot(target, spec)
            source_hashes = source_snapshot.pop("row_hashes")
            target_hashes = target_snapshot.pop("row_hashes")
            source_keys = set(source_hashes)
            target_keys = set(target_hashes)
            differing = sorted(
                key
                for key in source_keys & target_keys
                if source_hashes[key] != target_hashes[key]
            )
            table_passed = (
                source_snapshot["count"] == target_snapshot["count"]
                and not (source_keys - target_keys)
                and not (target_keys - source_keys)
                and not differing
                and source_snapshot["canonical_hash"] == target_snapshot["canonical_hash"]
            )
            table_reports[spec.source_table] = {
                "status": "pass" if table_passed else "fail",
                "source_count": source_snapshot["count"],
                "target_count": target_snapshot["count"],
                "source_hash": source_snapshot["canonical_hash"],
                "target_hash": target_snapshot["canonical_hash"],
                "missing_primary_keys": sorted(source_keys - target_keys),
                "extra_primary_keys": sorted(target_keys - source_keys),
                "differing_primary_keys": differing,
            }
    passed = all(report["status"] == "pass" for report in table_reports.values())
    return {
        "status": "pass" if passed else "fail",
        "mode": "verify",
        "source_file": source_path.name,
        "read_only": True,
        "tables": table_reports,
    }


def _sanitized_error(mode: str, error: Exception, started: float) -> dict[str, Any]:
    return {
        "status": "fail",
        "mode": mode,
        "error_code": type(error).__name__,
        "duration_ms": round((time.perf_counter() - started) * 1000),
    }


def _write_report(report: dict[str, Any], output: str | None) -> None:
    serialized = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output:
        Path(output).resolve().write_text(serialized, encoding="utf-8")
    print(serialized, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="One-time, manifest-driven SQLite to empty PostgreSQL data migration."
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)
    for mode in ("plan", "apply", "verify"):
        command = subparsers.add_parser(mode)
        command.add_argument("--source-sqlite", required=True)
        command.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    started = time.perf_counter()
    source_path = Path(args.source_sqlite).resolve()
    try:
        if args.mode == "plan":
            report = build_source_plan(source_path)
        elif args.mode == "apply":
            report = apply_data_migration(source_path)
        else:
            report = verify_data_migration(source_path)
    except (MigrationError, OSError, sqlite3.Error) as error:
        report = _sanitized_error(args.mode, error, started)
        _write_report(report, args.output)
        return 2 if isinstance(error, MigrationConfigurationError) else 3
    report["duration_ms"] = round((time.perf_counter() - started) * 1000)
    _write_report(report, args.output)
    return 0 if report["status"] == "pass" else 3


if __name__ == "__main__":
    raise SystemExit(main())
