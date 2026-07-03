from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import migrate_sqlite_to_configured_db as migrator
from scripts import audit_database_migration as audit


ACCESS_CORE_TABLES = (
    "organization_memberships",
    "organization_modules",
    "user_capabilities",
    "system_settings",
)
TASK_WORKFLOW_TABLES = (
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
)
TASK_WORKFLOW_DEPENDENCIES = (
    "user_calendars",
)
INVOICE_OPERATIONS_TABLES = (
    "invoice_comments",
    "invoice_handoff_batches",
    "invoice_handoff_batch_items",
    "invoice_ksef_field_overrides",
)
CRM_CORE_TABLES = (
    "contractor_notes",
)
BILLING_CORE_TABLES = (
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
    "billing_payment_matches",
    "billing_payer_ledger_entries",
)
KNOWLEDGE_CORE_TABLES = (
    "knowledge_documents",
    "knowledge_document_versions",
    "knowledge_processing_jobs",
    "knowledge_folder_watchers",
    "knowledge_document_comments",
)
INTAKE_ATTACHMENTS_CORE_TABLES = (
    "intake_forms",
    "intake_items",
    "intake_item_comments",
    "intake_item_history",
    "entity_attachments",
)
AUTOMATION_CORE_TABLES = (
    "automation_rules",
    "automation_executions",
)
CALENDAR_INTEGRATION_CORE_TABLES = (
    "user_google_calendar_connections",
    "user_calendar_assignments",
    "system_email_google_connections",
)
WHITEBOARD_CORE_TABLES = (
    "organization_whiteboard_events",
)
UI_STATE_CORE_TABLES = (
    "saved_views",
)
LEGACY_TABLES = (
    "organizations",
    "users",
    "contractors",
    "invoices",
    "invoice_relations",
    "event_logs",
    "user_sessions",
)


class SQLiteToConfiguredDbMigratorTests(unittest.TestCase):
    def test_access_core_tables_are_included_after_dependencies(self):
        table_order = list(migrator.TABLE_ORDER)

        for table_name in ACCESS_CORE_TABLES:
            self.assertIn(table_name, table_order)
            self.assertLess(table_order.index("organizations"), table_order.index(table_name))
            self.assertLess(table_order.index("users"), table_order.index(table_name))

    def test_existing_legacy_tables_remain_included(self):
        for table_name in LEGACY_TABLES:
            self.assertIn(table_name, migrator.TABLE_ORDER)
            self.assertIn(table_name, migrator.ORDER_COLUMNS)
            self.assertIn(table_name, migrator.POSTGRES_SEQUENCES)

    def test_access_core_tables_have_order_columns_and_sequences(self):
        expected_ids = {
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
            "contractor_notes": "contractor_note_id",
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
            "billing_payment_matches": "billing_payment_match_id",
            "billing_payer_ledger_entries": "billing_payer_ledger_entry_id",
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
        }
        for table_name, id_column in expected_ids.items():
            self.assertEqual(migrator.ORDER_COLUMNS[table_name], id_column)
            self.assertEqual(migrator.POSTGRES_SEQUENCES[table_name], id_column)

    def test_task_workflow_tables_are_included_after_dependencies(self):
        table_order = list(migrator.TABLE_ORDER)

        self.assertLess(table_order.index("organizations"), table_order.index("user_calendars"))
        self.assertLess(table_order.index("users"), table_order.index("user_calendars"))
        self.assertLess(table_order.index("user_calendars"), table_order.index("tasks"))
        for table_name in TASK_WORKFLOW_TABLES:
            self.assertIn(table_name, table_order)
            self.assertLess(table_order.index("organizations"), table_order.index(table_name))
            self.assertLess(table_order.index("users"), table_order.index(table_name))
        for child_table in (
            "task_visibility_users",
            "task_links",
            "task_notes",
            "task_checklist_items",
            "task_attachments",
            "task_history",
        ):
            self.assertLess(table_order.index("tasks"), table_order.index(child_table))
        self.assertLess(table_order.index("work_items"), table_order.index("work_item_history"))

    def test_invoice_operations_tables_are_included_after_dependencies(self):
        table_order = list(migrator.TABLE_ORDER)

        for table_name in INVOICE_OPERATIONS_TABLES:
            self.assertIn(table_name, table_order)
            self.assertLess(table_order.index("organizations"), table_order.index(table_name))
            self.assertLess(table_order.index("users"), table_order.index(table_name))
            self.assertLess(table_order.index("invoices"), table_order.index(table_name))
        self.assertLess(
            table_order.index("invoice_handoff_batches"),
            table_order.index("invoice_handoff_batch_items"),
        )
        self.assertLess(
            table_order.index("approval_requests"),
            table_order.index("invoice_ksef_field_overrides"),
        )

    def test_crm_core_tables_are_included_after_dependencies(self):
        table_order = list(migrator.TABLE_ORDER)

        for table_name in CRM_CORE_TABLES:
            self.assertIn(table_name, table_order)
            self.assertLess(table_order.index("organizations"), table_order.index(table_name))
            self.assertLess(table_order.index("users"), table_order.index(table_name))
            self.assertLess(table_order.index("contractors"), table_order.index(table_name))

    def test_billing_core_tables_are_included_after_dependencies(self):
        table_order = list(migrator.TABLE_ORDER)

        for table_name in BILLING_CORE_TABLES:
            self.assertIn(table_name, table_order)
            self.assertLess(table_order.index("organizations"), table_order.index(table_name))
        self.assertLess(table_order.index("billing_payers"), table_order.index("billing_students"))
        self.assertLess(table_order.index("billing_schools"), table_order.index("billing_students"))
        self.assertLess(table_order.index("billing_models"), table_order.index("billing_students"))
        self.assertLess(table_order.index("billing_models"), table_order.index("billing_charge_batches"))
        self.assertLess(table_order.index("billing_charge_batches"), table_order.index("billing_charges"))
        self.assertLess(table_order.index("billing_students"), table_order.index("billing_charges"))
        self.assertLess(table_order.index("billing_payers"), table_order.index("billing_charges"))
        self.assertLess(table_order.index("billing_students"), table_order.index("billing_student_charge_state"))
        self.assertLess(table_order.index("billing_payers"), table_order.index("billing_payer_charge_state"))
        self.assertLess(table_order.index("billing_bank_accounts"), table_order.index("billing_statement_imports"))
        self.assertLess(table_order.index("billing_statement_imports"), table_order.index("billing_transactions"))
        self.assertLess(table_order.index("billing_transactions"), table_order.index("billing_payment_matches"))
        self.assertLess(table_order.index("billing_charges"), table_order.index("billing_payment_matches"))
        self.assertLess(table_order.index("billing_payers"), table_order.index("billing_payer_ledger_entries"))
        self.assertLess(table_order.index("billing_charges"), table_order.index("billing_payer_ledger_entries"))
        self.assertLess(table_order.index("billing_transactions"), table_order.index("billing_payer_ledger_entries"))

    def test_knowledge_core_tables_are_included_after_dependencies(self):
        table_order = list(migrator.TABLE_ORDER)

        for table_name in KNOWLEDGE_CORE_TABLES:
            self.assertIn(table_name, table_order)
            self.assertLess(table_order.index("organizations"), table_order.index(table_name))
        for user_scoped_table in (
            "knowledge_documents",
            "knowledge_document_versions",
            "knowledge_processing_jobs",
            "knowledge_document_comments",
        ):
            self.assertLess(table_order.index("users"), table_order.index(user_scoped_table))
        self.assertLess(table_order.index("knowledge_documents"), table_order.index("knowledge_document_versions"))
        self.assertLess(table_order.index("knowledge_documents"), table_order.index("knowledge_processing_jobs"))
        self.assertLess(table_order.index("knowledge_documents"), table_order.index("knowledge_document_comments"))
        self.assertLess(
            table_order.index("knowledge_document_versions"),
            table_order.index("knowledge_document_comments"),
        )

    def test_intake_attachments_core_tables_are_included_after_dependencies(self):
        table_order = list(migrator.TABLE_ORDER)

        for table_name in INTAKE_ATTACHMENTS_CORE_TABLES:
            self.assertIn(table_name, table_order)
            self.assertLess(table_order.index("organizations"), table_order.index(table_name))
        for user_scoped_table in (
            "intake_forms",
            "intake_items",
            "intake_item_comments",
            "entity_attachments",
        ):
            self.assertLess(table_order.index("users"), table_order.index(user_scoped_table))
        self.assertLess(table_order.index("tasks"), table_order.index("intake_items"))
        self.assertLess(table_order.index("invoices"), table_order.index("intake_items"))
        self.assertLess(table_order.index("intake_forms"), table_order.index("intake_items"))
        self.assertLess(table_order.index("intake_items"), table_order.index("intake_item_comments"))
        self.assertLess(table_order.index("intake_items"), table_order.index("intake_item_history"))

    def test_automation_core_tables_are_included_after_dependencies(self):
        table_order = list(migrator.TABLE_ORDER)

        for table_name in AUTOMATION_CORE_TABLES:
            self.assertIn(table_name, table_order)
            self.assertLess(table_order.index("organizations"), table_order.index(table_name))
        self.assertLess(table_order.index("users"), table_order.index("automation_rules"))
        self.assertLess(table_order.index("automation_rules"), table_order.index("automation_executions"))

    def test_calendar_integration_core_tables_are_included_after_dependencies(self):
        table_order = list(migrator.TABLE_ORDER)

        for table_name in CALENDAR_INTEGRATION_CORE_TABLES:
            self.assertIn(table_name, table_order)
        self.assertLess(table_order.index("users"), table_order.index(table_name))
        self.assertLess(table_order.index("user_calendars"), table_order.index("user_calendar_assignments"))

    def test_whiteboard_core_tables_are_included_after_dependencies(self):
        table_order = list(migrator.TABLE_ORDER)

        for table_name in WHITEBOARD_CORE_TABLES:
            self.assertIn(table_name, table_order)
            self.assertLess(table_order.index("organizations"), table_order.index(table_name))
            self.assertLess(table_order.index("users"), table_order.index(table_name))

    def test_ui_state_core_tables_are_included_after_dependencies(self):
        table_order = list(migrator.TABLE_ORDER)

        for table_name in UI_STATE_CORE_TABLES:
            self.assertIn(table_name, table_order)
            self.assertLess(table_order.index("organizations"), table_order.index(table_name))
            self.assertLess(table_order.index("users"), table_order.index(table_name))

    def test_audit_no_longer_reports_access_core_tables_as_missing(self):
        report = audit.build_audit()

        for table_name in ACCESS_CORE_TABLES:
            self.assertNotIn(table_name, report["tables_missing_from_migrator"])
        self.assertEqual(len(report["migrator_tables"]), 58)
        self.assertEqual(len(report["tables_missing_from_migrator"]), 10)
        self.assertEqual(report["blocker_count"], 0)

    def test_audit_no_longer_reports_task_workflow_tables_as_missing(self):
        report = audit.build_audit()

        for table_name in TASK_WORKFLOW_DEPENDENCIES + TASK_WORKFLOW_TABLES:
            self.assertNotIn(table_name, report["tables_missing_from_migrator"])
        self.assertEqual(report["migration_order_issues"], [])

    def test_audit_no_longer_reports_invoice_operations_tables_as_missing(self):
        report = audit.build_audit()

        for table_name in INVOICE_OPERATIONS_TABLES:
            self.assertNotIn(table_name, report["tables_missing_from_migrator"])
        self.assertEqual(report["migration_order_issues"], [])

    def test_audit_no_longer_reports_crm_core_tables_as_missing(self):
        report = audit.build_audit()

        for table_name in CRM_CORE_TABLES:
            self.assertNotIn(table_name, report["tables_missing_from_migrator"])
        self.assertEqual(report["migration_order_issues"], [])

    def test_audit_no_longer_reports_billing_core_tables_as_missing(self):
        report = audit.build_audit()

        for table_name in BILLING_CORE_TABLES:
            self.assertNotIn(table_name, report["tables_missing_from_migrator"])
        self.assertEqual(report["migration_order_issues"], [])

    def test_audit_no_longer_reports_knowledge_core_tables_as_missing(self):
        report = audit.build_audit()

        for table_name in KNOWLEDGE_CORE_TABLES:
            self.assertNotIn(table_name, report["tables_missing_from_migrator"])
        self.assertEqual(report["migration_order_issues"], [])

    def test_audit_no_longer_reports_intake_attachments_core_tables_as_missing(self):
        report = audit.build_audit()

        for table_name in INTAKE_ATTACHMENTS_CORE_TABLES:
            self.assertNotIn(table_name, report["tables_missing_from_migrator"])
        self.assertEqual(report["migration_order_issues"], [])

    def test_audit_no_longer_reports_automation_core_tables_as_missing(self):
        report = audit.build_audit()

        for table_name in AUTOMATION_CORE_TABLES:
            self.assertNotIn(table_name, report["tables_missing_from_migrator"])
        self.assertEqual(report["migration_order_issues"], [])

    def test_audit_no_longer_reports_calendar_integration_core_tables_as_missing(self):
        report = audit.build_audit()

        for table_name in CALENDAR_INTEGRATION_CORE_TABLES:
            self.assertNotIn(table_name, report["tables_missing_from_migrator"])
        self.assertEqual(report["migration_order_issues"], [])

    def test_audit_no_longer_reports_whiteboard_core_tables_as_missing(self):
        report = audit.build_audit()

        for table_name in WHITEBOARD_CORE_TABLES:
            self.assertNotIn(table_name, report["tables_missing_from_migrator"])
        self.assertEqual(report["migration_order_issues"], [])

    def test_audit_no_longer_reports_ui_state_core_tables_as_missing(self):
        report = audit.build_audit()

        for table_name in UI_STATE_CORE_TABLES:
            self.assertNotIn(table_name, report["tables_missing_from_migrator"])
        self.assertEqual(report["migration_order_issues"], [])

    def test_migrator_was_not_expanded_to_all_schema_tables(self):
        report = audit.build_audit()

        self.assertLess(len(report["migrator_tables"]), len(report["sqlite_tables"]))
        self.assertIn("google_calendar_oauth_states", report["tables_missing_from_migrator"])
        self.assertIn("email_import_runs", report["tables_missing_from_migrator"])
        self.assertIn("ksef_import_runs", report["tables_missing_from_migrator"])
        self.assertIn("task_reminder_outbox", report["tables_missing_from_migrator"])
        self.assertIn("user_module_inbox_state", report["tables_missing_from_migrator"])

    def test_database_migration_does_not_run_physical_storage_migration(self):
        migrator_source = Path(migrator.__file__).read_text(encoding="utf-8")

        self.assertNotIn("plan_storage_migration", migrator_source)
        self.assertNotIn("check_s3_storage", migrator_source)
        self.assertNotIn("S3StorageService", migrator_source)
        self.assertNotIn("boto3", migrator_source)

    def test_migrator_console_output_does_not_log_secret_or_token_values(self):
        migrator_source = Path(migrator.__file__).read_text(encoding="utf-8")
        print_lines = [line.strip() for line in migrator_source.splitlines() if "print(" in line]

        for line in print_lines:
            self.assertNotIn("row", line)
            self.assertNotIn("access_token", line)
            self.assertNotIn("refresh_token", line)
            self.assertNotIn("token_hash", line)
            self.assertNotIn("secret", line.lower())

    def test_copy_table_can_copy_access_core_table_between_temp_sqlite_connections(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_path = Path(tmp) / "source.sqlite3"
            target_path = Path(tmp) / "target.sqlite3"
            source = sqlite3.connect(source_path)
            source.row_factory = sqlite3.Row
            target = sqlite3.connect(target_path)
            target.row_factory = sqlite3.Row
            try:
                for connection in (source, target):
                    connection.execute(
                        """
                        CREATE TABLE organization_memberships (
                            organization_membership_id INTEGER PRIMARY KEY,
                            user_id INTEGER NOT NULL,
                            organization_id INTEGER NOT NULL,
                            role TEXT NOT NULL,
                            membership_status TEXT NOT NULL,
                            is_primary INTEGER NOT NULL,
                            granted_at TEXT NOT NULL,
                            updated_at TEXT NOT NULL
                        )
                        """
                    )
                    connection.commit()
                source.execute(
                    """
                    INSERT INTO organization_memberships (
                        organization_membership_id,
                        user_id,
                        organization_id,
                        role,
                        membership_status,
                        is_primary,
                        granted_at,
                        updated_at
                    ) VALUES (1, 10, 20, 'operator_globalny', 'active', 1, '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')
                    """
                )
                source.commit()

                @contextmanager
                def target_connection():
                    yield target
                    target.commit()

                with patch.object(migrator, "get_connection", target_connection):
                    copied = migrator._copy_table(source, "organization_memberships")

                row = target.execute("SELECT * FROM organization_memberships").fetchone()
            finally:
                source.close()
                target.close()

        self.assertEqual(copied, 1)
        self.assertEqual(row["role"], "operator_globalny")
        self.assertEqual(row["organization_id"], 20)

    def test_importing_migrator_does_not_require_postgresql_or_secrets(self):
        self.assertIsInstance(migrator.TABLE_ORDER, tuple)
        self.assertIn("organization_memberships", migrator.TABLE_ORDER)


if __name__ == "__main__":
    unittest.main()
