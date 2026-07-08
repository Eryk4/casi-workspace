from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from app.config import SQLITE_DB_PATH, STORAGE_ROOT, database_label, uses_postgresql
from app.db import get_connection, initialize_database, reset_database


TABLE_ORDER = (
    "organizations",
    "users",
    "organization_memberships",
    "organization_modules",
    "user_capabilities",
    "system_settings",
    "user_calendars",
    "user_google_calendar_connections",
    "user_calendar_assignments",
    "system_email_google_connections",
    "tasks",
    "task_visibility_users",
    "task_links",
    "task_notes",
    "task_checklist_items",
    "task_templates",
    "approval_requests",
    "task_attachments",
    "task_history",
    "work_items",
    "work_item_history",
    "contractors",
    "contractor_notes",
    "invoices",
    "invoice_relations",
    "invoice_comments",
    "invoice_handoff_batches",
    "invoice_handoff_batch_items",
    "invoice_ksef_field_overrides",
    "billing_schools",
    "billing_models",
    "billing_payers",
    "billing_students",
    "billing_charge_batches",
    "billing_charges",
    "billing_student_charge_state",
    "billing_payer_charge_state",
    "billing_bank_accounts",
    "billing_statement_imports",
    "billing_transactions",
    "billing_payment_review_events",
    "billing_work_queue_events",
    "billing_payment_matches",
    "billing_payer_ledger_entries",
    "billing_notes",
    "knowledge_documents",
    "knowledge_document_versions",
    "knowledge_processing_jobs",
    "knowledge_folder_watchers",
    "knowledge_document_comments",
    "intake_forms",
    "intake_items",
    "intake_item_comments",
    "intake_item_history",
    "entity_attachments",
    "saved_views",
    "automation_rules",
    "automation_executions",
    "organization_whiteboard_events",
    "event_logs",
    "user_sessions",
)

ORDER_COLUMNS = {
    "organizations": "organization_id",
    "users": "user_id",
    "organization_memberships": "organization_membership_id",
    "organization_modules": "organization_module_id",
    "user_capabilities": "user_capability_id",
    "system_settings": "system_setting_id",
    "user_calendars": "user_calendar_id",
    "user_google_calendar_connections": "user_google_calendar_connection_id",
    "user_calendar_assignments": "user_calendar_assignment_id",
    "system_email_google_connections": "system_email_google_connection_id",
    "tasks": "task_id",
    "task_visibility_users": "task_visibility_user_id",
    "task_links": "task_link_id",
    "task_notes": "task_note_id",
    "task_checklist_items": "task_checklist_item_id",
    "task_templates": "task_template_id",
    "approval_requests": "approval_request_id",
    "task_attachments": "task_attachment_id",
    "task_history": "task_history_id",
    "work_items": "work_item_id",
    "work_item_history": "work_item_history_id",
    "contractors": "contractor_id",
    "contractor_notes": "contractor_note_id",
    "invoices": "id",
    "invoice_relations": "id",
    "invoice_comments": "invoice_comment_id",
    "invoice_handoff_batches": "invoice_handoff_batch_id",
    "invoice_handoff_batch_items": "invoice_handoff_batch_item_id",
    "invoice_ksef_field_overrides": "invoice_ksef_field_override_id",
    "billing_schools": "billing_school_id",
    "billing_models": "billing_model_id",
    "billing_payers": "billing_payer_id",
    "billing_students": "billing_student_id",
    "billing_charge_batches": "billing_charge_batch_id",
    "billing_charges": "billing_charge_id",
    "billing_student_charge_state": "billing_student_charge_state_id",
    "billing_payer_charge_state": "billing_payer_charge_state_id",
    "billing_bank_accounts": "billing_bank_account_id",
    "billing_statement_imports": "billing_statement_import_id",
    "billing_transactions": "billing_transaction_id",
    "billing_payment_review_events": "billing_payment_review_event_id",
    "billing_work_queue_events": "billing_work_queue_event_id",
    "billing_payment_matches": "billing_payment_match_id",
    "billing_payer_ledger_entries": "billing_payer_ledger_entry_id",
    "billing_notes": "billing_note_id",
    "knowledge_documents": "knowledge_document_id",
    "knowledge_document_versions": "knowledge_document_version_id",
    "knowledge_processing_jobs": "knowledge_processing_job_id",
    "knowledge_folder_watchers": "knowledge_folder_watcher_id",
    "knowledge_document_comments": "knowledge_document_comment_id",
    "intake_forms": "intake_form_id",
    "intake_items": "intake_item_id",
    "intake_item_comments": "intake_item_comment_id",
    "intake_item_history": "intake_item_history_id",
    "entity_attachments": "entity_attachment_id",
    "saved_views": "saved_view_id",
    "automation_rules": "automation_rule_id",
    "automation_executions": "automation_execution_id",
    "organization_whiteboard_events": "whiteboard_event_id",
    "event_logs": "id",
    "user_sessions": "session_id",
}

POSTGRES_SEQUENCES = {
    "organizations": "organization_id",
    "users": "user_id",
    "organization_memberships": "organization_membership_id",
    "organization_modules": "organization_module_id",
    "user_capabilities": "user_capability_id",
    "system_settings": "system_setting_id",
    "user_calendars": "user_calendar_id",
    "user_google_calendar_connections": "user_google_calendar_connection_id",
    "user_calendar_assignments": "user_calendar_assignment_id",
    "system_email_google_connections": "system_email_google_connection_id",
    "tasks": "task_id",
    "task_visibility_users": "task_visibility_user_id",
    "task_links": "task_link_id",
    "task_notes": "task_note_id",
    "task_checklist_items": "task_checklist_item_id",
    "task_templates": "task_template_id",
    "approval_requests": "approval_request_id",
    "task_attachments": "task_attachment_id",
    "task_history": "task_history_id",
    "work_items": "work_item_id",
    "work_item_history": "work_item_history_id",
    "contractors": "contractor_id",
    "contractor_notes": "contractor_note_id",
    "invoices": "id",
    "invoice_relations": "id",
    "invoice_comments": "invoice_comment_id",
    "invoice_handoff_batches": "invoice_handoff_batch_id",
    "invoice_handoff_batch_items": "invoice_handoff_batch_item_id",
    "invoice_ksef_field_overrides": "invoice_ksef_field_override_id",
    "billing_schools": "billing_school_id",
    "billing_models": "billing_model_id",
    "billing_payers": "billing_payer_id",
    "billing_students": "billing_student_id",
    "billing_charge_batches": "billing_charge_batch_id",
    "billing_charges": "billing_charge_id",
    "billing_student_charge_state": "billing_student_charge_state_id",
    "billing_payer_charge_state": "billing_payer_charge_state_id",
    "billing_bank_accounts": "billing_bank_account_id",
    "billing_statement_imports": "billing_statement_import_id",
    "billing_transactions": "billing_transaction_id",
    "billing_payment_review_events": "billing_payment_review_event_id",
    "billing_work_queue_events": "billing_work_queue_event_id",
    "billing_payment_matches": "billing_payment_match_id",
    "billing_payer_ledger_entries": "billing_payer_ledger_entry_id",
    "billing_notes": "billing_note_id",
    "knowledge_documents": "knowledge_document_id",
    "knowledge_document_versions": "knowledge_document_version_id",
    "knowledge_processing_jobs": "knowledge_processing_job_id",
    "knowledge_folder_watchers": "knowledge_folder_watcher_id",
    "knowledge_document_comments": "knowledge_document_comment_id",
    "intake_forms": "intake_form_id",
    "intake_items": "intake_item_id",
    "intake_item_comments": "intake_item_comment_id",
    "intake_item_history": "intake_item_history_id",
    "entity_attachments": "entity_attachment_id",
    "saved_views": "saved_view_id",
    "automation_rules": "automation_rule_id",
    "automation_executions": "automation_execution_id",
    "organization_whiteboard_events": "whiteboard_event_id",
    "event_logs": "id",
    "user_sessions": "session_id",
}


def _sqlite_connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def _sqlite_table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _sqlite_table_columns(connection: sqlite3.Connection, table_name: str) -> list[str]:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return [str(row["name"]) for row in rows]


def _target_has_data() -> bool:
    with get_connection() as connection:
        for table_name in ("organizations", "users", "contractors", "invoices", "event_logs"):
            row = connection.execute(f"SELECT COUNT(*) AS total FROM {table_name}").fetchone()
            if row and int(row["total"]) > 0:
                return True
    return False


def _copy_table(source: sqlite3.Connection, table_name: str) -> int:
    if not _sqlite_table_exists(source, table_name):
        return 0

    columns = _sqlite_table_columns(source, table_name)
    if not columns:
        return 0

    rows = source.execute(
        f"SELECT * FROM {table_name} ORDER BY {ORDER_COLUMNS[table_name]} ASC"
    ).fetchall()
    if not rows:
        return 0

    column_list = ", ".join(columns)
    placeholders = ", ".join("?" for _ in columns)

    with get_connection() as target:
        for row in rows:
            target.execute(
                f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})",
                [row[column] for column in columns],
            )
    return len(rows)


def _reset_postgres_sequences() -> None:
    if not uses_postgresql():
        return

    with get_connection() as connection:
        for table_name, id_column in POSTGRES_SEQUENCES.items():
            connection.execute(
                f"""
                SELECT setval(
                    pg_get_serial_sequence('{table_name}', '{id_column}'),
                    COALESCE(MAX({id_column}), 1),
                    MAX({id_column}) IS NOT NULL
                )
                FROM {table_name}
                """
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Przenosi dane z pliku SQLite do obecnie skonfigurowanej bazy docelowej."
    )
    parser.add_argument(
        "--source-sqlite",
        default=str(SQLITE_DB_PATH),
        help="Ścieżka do źródłowej bazy SQLite.",
    )
    parser.add_argument(
        "--reset-target",
        action="store_true",
        help="Czyści docelową bazę przed migracją.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Pozwala uruchomić migrację także wtedy, gdy docelowa baza nie jest pusta.",
    )
    args = parser.parse_args()

    source_sqlite = Path(args.source_sqlite).resolve()
    if not source_sqlite.exists():
        raise SystemExit(f"Nie znaleziono źródłowej bazy SQLite: {source_sqlite}")

    if not uses_postgresql() and source_sqlite == SQLITE_DB_PATH.resolve():
        raise SystemExit(
            "Źródłowa SQLite i docelowa baza wskazują na ten sam plik. "
            "Skonfiguruj docelową bazę PostgreSQL albo podaj inną ścieżkę źródłową."
        )

    if args.reset_target:
        reset_database()
    else:
        initialize_database()

    if _target_has_data() and not args.force:
        raise SystemExit(
            "Docelowa baza nie jest pusta. Użyj --reset-target albo --force, jeśli chcesz kontynuować."
        )

    summary: dict[str, int] = {}
    with _sqlite_connect(source_sqlite) as source:
        for table_name in TABLE_ORDER:
            summary[table_name] = _copy_table(source, table_name)

    _reset_postgres_sequences()

    print(f"Migracja zakończona do bazy: {database_label()}")
    print(f"Źródłowa baza SQLite: {source_sqlite}")
    print("Przeniesione rekordy:")
    for table_name in TABLE_ORDER:
        print(f"- {table_name}: {summary.get(table_name, 0)}")
    print("")
    print("Pamiętaj też o skopiowaniu całego magazynu plików:")
    print(STORAGE_ROOT)


if __name__ == "__main__":
    main()
