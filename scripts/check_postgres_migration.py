from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import ParseResult, urlparse, urlunparse


ENV_NAME = "CASI_TEST_POSTGRES_DATABASE_URL"
ALLOWED_DATABASE_NAME_MARKERS = ("test", "tmp", "local", "casi_migration_test")
BLOCKED_HOST_MARKERS = (
    "digitalocean",
    "ondigitalocean",
    "railway",
    "rlwy",
    "production",
    "prod-db",
    "prod.",
)
REPRESENTATIVE_COUNTS = {
    "organizations": 1,
    "users": 1,
    "organization_memberships": 1,
    "user_calendars": 1,
    "tasks": 1,
    "task_notes": 1,
    "task_attachments": 1,
    "contractors": 1,
    "invoices": 1,
    "invoice_comments": 1,
    "knowledge_documents": 1,
    "intake_forms": 1,
    "intake_items": 1,
    "entity_attachments": 1,
    "saved_views": 1,
}


class SafetyError(RuntimeError):
    pass


@dataclass(frozen=True)
class SafePostgresTarget:
    url: str
    parsed: ParseResult

    @property
    def database_name(self) -> str:
        return self.parsed.path.lstrip("/")

    @property
    def host(self) -> str:
        return self.parsed.hostname or ""

    @property
    def redacted_label(self) -> str:
        return redact_database_url(self.url)


def redact_database_url(raw_url: str) -> str:
    parsed = urlparse(raw_url)
    hostname = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    userinfo = ""
    if parsed.username:
        userinfo = f"{parsed.username}:***@"
    redacted_netloc = f"{userinfo}{hostname}{port}"
    return urlunparse(parsed._replace(netloc=redacted_netloc))


def _validate_postgres_url(raw_url: str) -> SafePostgresTarget:
    value = raw_url.strip()
    if not value:
        raise SafetyError(f"{ENV_NAME} is empty.")

    parsed = urlparse(value)
    if parsed.scheme not in {"postgresql", "postgres"}:
        raise SafetyError("Test database URL must use postgresql:// or postgres://.")
    if not parsed.hostname:
        raise SafetyError("Test database URL must include a host.")

    database_name = parsed.path.lstrip("/").lower()
    if not database_name:
        raise SafetyError("Test database URL must include an explicit database name.")
    if not any(marker in database_name for marker in ALLOWED_DATABASE_NAME_MARKERS):
        raise SafetyError(
            "Refusing to run: database name must contain one of "
            f"{', '.join(ALLOWED_DATABASE_NAME_MARKERS)}."
        )

    host = parsed.hostname.lower()
    if any(marker in host for marker in BLOCKED_HOST_MARKERS):
        raise SafetyError(
            "Refusing to run: host looks like managed, remote, or production infrastructure."
        )

    return SafePostgresTarget(url=value, parsed=parsed)


def load_target_from_env(env: dict[str, str] | None = None) -> SafePostgresTarget:
    source_env = env if env is not None else os.environ
    raw_url = source_env.get(ENV_NAME, "").strip()
    if not raw_url:
        raise SafetyError(
            f"{ENV_NAME} is required. This check never falls back to DATABASE_URL "
            "or INVOICE_DATABASE_URL."
        )
    return _validate_postgres_url(raw_url)


def configure_target_environment(target: SafePostgresTarget) -> None:
    os.environ["INVOICE_DB_ENGINE"] = "postgresql"
    os.environ["INVOICE_DATABASE_URL"] = target.url
    os.environ["DATABASE_URL"] = ""
    os.environ["INVOICE_ENABLE_DEMO_SEED"] = "0"
    os.environ["INVOICE_DB_CONNECT_TIMEOUT_SECONDS"] = os.getenv(
        "INVOICE_DB_CONNECT_TIMEOUT_SECONDS",
        "5",
    )
    os.environ["INVOICE_DB_INIT_MAX_RETRIES"] = os.getenv("INVOICE_DB_INIT_MAX_RETRIES", "1")


def _insert(connection: sqlite3.Connection, table_name: str, values: dict[str, object]) -> None:
    columns = ", ".join(values)
    placeholders = ", ".join("?" for _ in values)
    connection.execute(
        f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})",
        list(values.values()),
    )


def create_synthetic_sqlite(source_path: Path) -> None:
    os.environ.setdefault("INVOICE_DB_ENGINE", "sqlite")
    os.environ.setdefault("INVOICE_DATABASE_URL", "")
    os.environ.setdefault("DATABASE_URL", "")

    from app import db as app_db

    source_path.parent.mkdir(parents=True, exist_ok=True)
    raw_connection = sqlite3.connect(source_path)
    raw_connection.row_factory = sqlite3.Row
    connection = app_db.DatabaseConnection(raw_connection, backend="sqlite", driver_name="sqlite")
    try:
        app_db._apply_database_schema_bootstrap(connection)
        raw_connection.commit()
        _seed_synthetic_data(raw_connection)
        raw_connection.commit()
    finally:
        raw_connection.close()


def _seed_synthetic_data(connection: sqlite3.Connection) -> None:
    now = "2026-06-02T12:00:00Z"
    _insert(
        connection,
        "organizations",
        {
            "organization_id": 100,
            "name": "CASI Migration Test Org",
            "slug": "casi-migration-test-org",
            "created_at": now,
            "updated_at": now,
        },
    )
    _insert(
        connection,
        "users",
        {
            "user_id": 200,
            "login": "migration-test-user",
            "display_name": "Migration Test User",
            "organization_id": 100,
            "password_hash": "synthetic-hash",
            "password_salt": "synthetic-salt",
            "role": "operator_globalny",
            "created_at": now,
            "updated_at": now,
        },
    )
    _insert(
        connection,
        "organization_memberships",
        {
            "organization_membership_id": 300,
            "user_id": 200,
            "organization_id": 100,
            "role": "operator_globalny",
            "membership_status": "active",
            "is_primary": 1,
            "granted_at": now,
            "updated_at": now,
        },
    )
    _insert(
        connection,
        "user_calendars",
        {
            "user_calendar_id": 400,
            "owner_user_id": 200,
            "display_name": "Migration Test Calendar",
            "sync_token": "migration-test-calendar-token",
            "created_at": now,
            "updated_at": now,
        },
    )
    _insert(
        connection,
        "tasks",
        {
            "task_id": 500,
            "organization_id": 100,
            "task_type": "manual",
            "owner_user_id": 200,
            "title": "Migration relation test task",
            "status": "nowe",
            "priority": "normalny",
            "assigned_user_id": 200,
            "calendar_id": 400,
            "created_by_user_id": 200,
            "created_at": now,
            "updated_at": now,
        },
    )
    _insert(
        connection,
        "task_notes",
        {
            "task_note_id": 600,
            "task_id": 500,
            "organization_id": 100,
            "note_text": "Synthetic task note",
            "created_by_user_id": 200,
            "created_at": now,
        },
    )
    _insert(
        connection,
        "task_attachments",
        {
            "task_attachment_id": 700,
            "task_id": 500,
            "organization_id": 100,
            "file_name": "synthetic-task.txt",
            "file_link": "synthetic://task-attachment",
            "file_storage_key": "synthetic/task-attachment.txt",
            "uploaded_by_user_id": 200,
            "created_at": now,
        },
    )
    _insert(
        connection,
        "contractors",
        {
            "contractor_id": 800,
            "organization_id": 100,
            "name": "Synthetic Contractor",
            "nip": "1234567890",
            "created_at": now,
            "updated_at": now,
        },
    )
    _insert(
        connection,
        "invoices",
        {
            "id": 900,
            "organization_id": 100,
            "incoming_date": "2026-06-02",
            "source": "synthetic",
            "file_name": "synthetic-invoice.pdf",
            "invoice_number": "FV/MIG/1",
            "issuer_nip": "1234567890",
            "issuer_name": "Synthetic Contractor",
            "gross_amount": 123.45,
            "status": "do_weryfikacji",
            "contractor_id": 800,
            "file_storage_key": "synthetic/invoice.pdf",
            "storage_backend": "local",
            "invoice_hash": "synthetic-invoice-hash",
            "assigned_user_id": 200,
            "created_at": now,
            "updated_at": now,
        },
    )
    _insert(
        connection,
        "invoice_comments",
        {
            "invoice_comment_id": 1000,
            "invoice_id": 900,
            "organization_id": 100,
            "note_text": "Synthetic invoice comment",
            "created_by_user_id": 200,
            "created_at": now,
        },
    )
    _insert(
        connection,
        "knowledge_documents",
        {
            "knowledge_document_id": 1100,
            "organization_id": 100,
            "title": "Synthetic policy",
            "file_name": "synthetic-policy.txt",
            "file_link": "synthetic://knowledge",
            "file_storage_key": "synthetic/knowledge.txt",
            "content_text": "Synthetic knowledge content",
            "content_hash": "synthetic-knowledge-hash",
            "owner_user_id": 200,
            "created_by_user_id": 200,
            "created_at": now,
            "updated_at": now,
        },
    )
    _insert(
        connection,
        "intake_forms",
        {
            "intake_form_id": 1200,
            "organization_id": 100,
            "form_name": "Synthetic intake",
            "form_slug": "synthetic-intake",
            "public_token": "synthetic-intake-token",
            "created_by_user_id": 200,
            "created_at": now,
            "updated_at": now,
        },
    )
    _insert(
        connection,
        "intake_items",
        {
            "intake_item_id": 1300,
            "organization_id": 100,
            "intake_form_id": 1200,
            "source_kind": "manual",
            "title": "Synthetic intake item",
            "assigned_user_id": 200,
            "linked_task_id": 500,
            "linked_invoice_id": 900,
            "created_by_user_id": 200,
            "created_at": now,
            "updated_at": now,
        },
    )
    _insert(
        connection,
        "entity_attachments",
        {
            "entity_attachment_id": 1400,
            "organization_id": 100,
            "entity_type": "intake_item",
            "entity_id": 1300,
            "file_name": "synthetic-intake.txt",
            "file_link": "synthetic://intake-attachment",
            "file_storage_key": "synthetic/intake-attachment.txt",
            "uploaded_by_user_id": 200,
            "created_at": now,
        },
    )
    _insert(
        connection,
        "saved_views",
        {
            "saved_view_id": 1500,
            "organization_id": 100,
            "module_key": "pulpit",
            "view_slug": "synthetic-dashboard",
            "view_name": "Synthetic dashboard view",
            "view_state_json": '{"filters":[]}',
            "created_by_user_id": 200,
            "created_at": now,
            "updated_at": now,
        },
    )


def _query_scalar(connection, query: str, params: Iterable[object] | None = None) -> int:
    row = connection.execute(query, list(params or [])).fetchone()
    if row is None:
        raise AssertionError(f"Query returned no rows: {query}")
    return int(row["value"])


def run_controlled_migration_check(target: SafePostgresTarget) -> None:
    configure_target_environment(target)

    import migrate_sqlite_to_configured_db as migrator

    with tempfile.TemporaryDirectory(prefix="casi_pg_migration_test_") as tmp:
        source_sqlite = Path(tmp) / "synthetic_source.sqlite3"
        create_synthetic_sqlite(source_sqlite)

        print("Validated test PostgreSQL target:", target.redacted_label)
        print("Resetting only the validated test PostgreSQL schema.")
        print("Synthetic SQLite source:", source_sqlite.name)

        migrator.reset_database()
        summary: dict[str, int] = {}
        with migrator._sqlite_connect(source_sqlite) as source:
            for table_name in migrator.TABLE_ORDER:
                summary[table_name] = migrator._copy_table(source, table_name)
        migrator._reset_postgres_sequences()

    verify_postgres_result(summary)


def verify_postgres_result(summary: dict[str, int]) -> None:
    from app.db import get_connection

    with get_connection() as connection:
        for table_name, expected_count in REPRESENTATIVE_COUNTS.items():
            actual = _query_scalar(
                connection,
                f"SELECT COUNT(*) AS value FROM {table_name}",
            )
            if actual != expected_count:
                raise AssertionError(
                    f"Unexpected row count for {table_name}: expected {expected_count}, got {actual}."
                )
            if summary.get(table_name) != expected_count:
                raise AssertionError(
                    f"Migrator summary mismatch for {table_name}: "
                    f"expected {expected_count}, got {summary.get(table_name)}."
                )

        task_relation_count = _query_scalar(
            connection,
            """
            SELECT COUNT(*) AS value
            FROM tasks t
            JOIN users u ON u.user_id = t.owner_user_id
            JOIN organizations o ON o.organization_id = t.organization_id
            JOIN task_notes n ON n.task_id = t.task_id
            JOIN task_attachments a ON a.task_id = t.task_id
            WHERE t.task_id = ?
            """,
            [500],
        )
        if task_relation_count != 1:
            raise AssertionError("Organization -> user -> task -> note/attachment relation failed.")

        invoice_relation_count = _query_scalar(
            connection,
            """
            SELECT COUNT(*) AS value
            FROM invoices i
            JOIN contractors c ON c.contractor_id = i.contractor_id
            JOIN invoice_comments ic ON ic.invoice_id = i.id
            WHERE i.id = ?
            """,
            [900],
        )
        if invoice_relation_count != 1:
            raise AssertionError("Contractor -> invoice -> comment relation failed.")

        next_org_id = _query_scalar(
            connection,
            "SELECT nextval(pg_get_serial_sequence('organizations', 'organization_id')) AS value",
        )
        if next_org_id <= 100:
            raise AssertionError("PostgreSQL sequence reset failed for organizations.")

    print("PostgreSQL migration check passed.")
    print("Verified representative tables:", len(REPRESENTATIVE_COUNTS))
    print("No production data, file storage, S3, or DigitalOcean resources were used.")


def main() -> int:
    try:
        target = load_target_from_env()
        run_controlled_migration_check(target)
    except SafetyError as error:
        print(f"PostgreSQL migration check not started: {error}")
        return 2
    except Exception as error:
        safe_message = str(error)
        configured_url = os.environ.get("INVOICE_DATABASE_URL", "")
        test_url = os.environ.get(ENV_NAME, "")
        for secret_source in (configured_url, test_url):
            parsed = urlparse(secret_source)
            if parsed.password:
                safe_message = safe_message.replace(parsed.password, "***")
        print(f"PostgreSQL migration check failed: {safe_message}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
