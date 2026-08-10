from __future__ import annotations

import unittest
from unittest.mock import patch

from app.bootstrap import build_services
from app.db import get_connection, reset_database
from app.services.automation_operations_service import (
    AutomationOperationsRegistry,
    email_import_health,
    ksef_import_health,
    knowledge_processing_health,
    scheduler_health,
    task_reminder_health,
)


class AutomationOperationsTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        self.admin = self.services["auth_service"].ensure_default_admin()
        assert self.admin is not None
        self.organization = self.services["organization_service"].create_organization(
            {"name": "Automation Org", "slug": "automation-org", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.organization_id = int(self.organization["organization_id"])
        self.user = self.services["auth_service"].create_user(
            {
                "login": "automation-user",
                "display_name": "Automation User",
                "password": "Automation123!",
                "role": "organization_admin",
                "organization_id": self.organization_id,
                "is_active": 1,
            },
            actor_login="admin",
            actor_user_id=int(self.admin["user_id"]),
            actor_user=self.admin,
        )
        self.user_id = int(self.user["user_id"])
        self.operations = self.services["automation_operations_service"]
        self.scheduler = self.services["internal_notification_scheduler_service"]
        self.reminders = self.services["task_reminder_service"]

    def _reminder_item(self):
        return next(item for item in self._dashboard()["items"] if item["automation_key"] == "task_reminders")

    def _knowledge_item(self):
        return next(item for item in self._dashboard()["items"] if item["automation_key"] == "knowledge_processing")

    def _email_item(self):
        return next(item for item in self._dashboard()["items"] if item["automation_key"] == "email_import")

    def _ksef_item(self):
        return next(item for item in self._dashboard()["items"] if item["automation_key"] == "ksef_import")

    def _configure_ksef_import(self, *, enabled: bool = True, with_identifier: bool = True) -> None:
        self.services["organization_repository"].update(
            self.organization_id,
            {
                "ksef_integration_enabled": 1 if enabled else 0,
                "ksef_company_identifier": "SYNTHETIC-TAXPAYER-A" if with_identifier else None,
            },
        )

    def _insert_ksef_run(self, *, status: str, day: int, organization_id: int | None = None) -> int:
        timestamp = f"2026-04-{day:02d}T10:00:00+00:00"
        org_id = organization_id or self.organization_id
        with get_connection() as connection:
            cursor = connection.execute(
                """INSERT INTO ksef_import_runs (
                    organization_id, company_identifier, environment, trigger_mode, actor,
                    started_at, finished_at, status, checked_document_count, imported_invoice_count,
                    skipped_existing_count, skipped_error_count, summary_message, details
                ) VALUES (?, 'SYNTHETIC-TAXPAYER-PRIVATE', 'demo', 'manual', 'synthetic-user',
                    ?, ?, ?, 7, 2, 1, 1, 'Private invoice INV-SECRET amount 987.65 XML UPO token secret',
                    '{"ksef_id":"KSEF-PRIVATE-FULL-ID","certificate":"private"}')""",
                (org_id, timestamp, None if status == "running" else timestamp, status),
            )
            run_id = int(cursor.lastrowid)
            connection.execute(
                """INSERT INTO ksef_import_items (
                    ksef_import_run_id, organization_id, source_external_id, ksef_number,
                    invoice_number, issuer_nip, issue_date, item_status, invoice_id, reason, created_at
                ) VALUES (?, ?, 'source-private', 'KSEF-PRIVATE-FULL-ID', 'INV-SECRET',
                    'SYNTHETIC-PRIVATE-NIP', '2026-04-01', 'skipped_error', NULL,
                    'Private company XML UPO amount 987.65', ?)""",
                (run_id, org_id, timestamp),
            )
        return run_id

    def _configure_email_import(self, *, runtime_enabled: bool = True, mailbox_configured: bool = True) -> None:
        self.services["organization_repository"].update(
            self.organization_id,
            {"email_integration_enabled": 1, "email_inbox_address": "route-a@example.invalid"},
        )
        adapter = self.services["automation_operations_registry"].get("email_import")
        assert adapter is not None
        adapter.configuration_status_provider = lambda: {
            "enabled": runtime_enabled,
            "configured": mailbox_configured,
        }

    def _insert_email_run(self, *, status: str, day: int, organization_id: int | None = None) -> int:
        timestamp = f"2026-03-{day:02d}T10:00:00+00:00"
        with get_connection() as connection:
            cursor = connection.execute(
                """INSERT INTO email_import_runs (
                    organization_id, mailbox_address, inbox_address, trigger_mode, actor, routing_mode,
                    started_at, finished_at, status, checked_message_count, matched_message_count,
                    matched_attachment_count, imported_invoice_count, skipped_existing_count,
                    skipped_error_count, summary_message, details
                ) VALUES (?, 'private-mailbox@example.invalid', 'private-route@example.invalid', 'automatic',
                    'mock-worker', 'central_mailbox', ?, ?, ?, 7, 5, 4, 2, 1, 1, ?, ?)""",
                (
                    organization_id or self.organization_id,
                    timestamp,
                    None if status == "running" else timestamp,
                    status,
                    "Private subject sender@example.invalid attachment.pdf token=secret",
                    '{"subject":"private","message_id":"<private@example.invalid>","body":"secret"}',
                ),
            )
            run_id = int(cursor.lastrowid)
            connection.execute(
                """INSERT INTO email_import_items (
                    email_import_run_id, organization_id, imap_uid, message_id, sender_email, subject,
                    recipients, matched_recipient, attachment_name, attachment_type, attachment_index,
                    source_external_id, item_status, invoice_id, reason, created_at
                ) VALUES (?, ?, '123', '<private@example.invalid>', 'sender@example.invalid', 'Private subject',
                    '["recipient@example.invalid"]', 'recipient@example.invalid', 'private-attachment.pdf',
                    'application/pdf', 1, 'private-source', 'skipped_error', NULL, 'Private failure', ?)""",
                (run_id, organization_id or self.organization_id, timestamp),
            )
        return run_id

    def _insert_knowledge_job(
        self,
        *,
        status: str,
        day: int,
        organization_id: int | None = None,
        error: str | None = None,
        job_type: str = "ingest",
    ) -> int:
        timestamp = f"2026-02-{day:02d}T10:00:00+00:00"
        with get_connection() as connection:
            cursor = connection.execute(
                """INSERT INTO knowledge_processing_jobs (
                    organization_id, knowledge_document_id, job_type, status, source_storage_key,
                    source_file_name, source_mime_type, source_type, source_content_hash,
                    supplemental_text, error_message, attempts, max_attempts, created_by_user_id,
                    started_at, finished_at, created_at, updated_at
                ) VALUES (?, NULL, ?, ?, ?, ?, 'text/plain', 'manual', ?, ?, ?, ?, 3, NULL, ?, ?, ?, ?)""",
                (
                    organization_id or self.organization_id,
                    job_type,
                    status,
                    "private/storage/key.txt",
                    "tajny_dokument_klienta.txt",
                    f"hash-{day}",
                    "Poufna treść dokumentu i OCR.",
                    error,
                    1 if status != "pending" else 0,
                    timestamp if status in {"processing", "completed", "failed"} else None,
                    timestamp if status in {"completed", "failed"} else None,
                    timestamp,
                    timestamp,
                ),
            )
            return int(cursor.lastrowid)

    def _insert_reminder(self, *, status: str, outcome: str | None = None, error: str | None = None) -> int:
        task = self.services["task_service"].create_task(
            {"title": "Widoczne przypomnienie", "task_type": "zadanie", "status": "nowe", "priority": "normalny",
             "due_at": "2099-01-01T10:00", "remind_at": "2000-01-01T09:00", "assigned_user_id": self.user_id,
             "visibility_scope": "organizacja"},
            actor_user=self.user, actor="automation-user", organization_id=self.organization_id,
        )
        with get_connection() as connection:
            cursor = connection.execute(
                """INSERT INTO task_reminder_outbox (
                    organization_id, task_id, delivery_channel, delivery_key, delivery_anchor_at,
                    recipient_user_id, recipient_telegram_user_id, available_at, status, retryable,
                    attempt_count, last_attempt_at, last_error, sent_at, payload, created_at, updated_at
                ) VALUES (?, ?, 'telegram', ?, '2026-01-15T07:00', ?, 'fake-user', '2026-01-15T07:00', ?, 0, 1,
                    '2026-01-15T07:01', ?, ?, '{}', '2026-01-15T07:00', '2026-01-15T07:01')""",
                (self.organization_id, int(task["task_id"]), f"test-{task['task_id']}", self.user_id, status, error,
                 "2026-01-15T07:01" if status == "sent" else None),
            )
            outbox_id = int(cursor.lastrowid)
            if outcome:
                connection.execute(
                    """INSERT INTO task_reminder_outbox_attempts (
                        task_reminder_outbox_id, organization_id, task_id, delivery_channel, attempt_no,
                        outcome, attempted_at, worker_name, error_message, details, created_at
                    ) VALUES (?, ?, ?, 'telegram', 1, ?, '2026-01-15T07:01', 'mock-worker', ?, '{}', '2026-01-15T07:01')""",
                    (outbox_id, self.organization_id, int(task["task_id"]), outcome, error),
                )
        return outbox_id

    def _dashboard(self):
        return self.operations.dashboard(
            organization_id=self.organization_id,
            recipient_user_id=self.user_id,
            actor_user=self.user,
        )

    def _save(self, enabled: bool = True) -> dict:
        return self.scheduler.save_settings(
            organization_id=self.organization_id,
            recipient_user_id=self.user_id,
            actor_user=self.user,
            actor="automation-user",
            enabled=enabled,
            local_time="08:15",
            timezone_name="Europe/Warsaw",
        )

    def _run(self, schedule_id: int, *, day: int, status: str, error_summary: str | None = None) -> None:
        timestamp = f"2026-01-{day:02d}T07:00:00+00:00"
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO internal_notification_schedule_runs (
                    schedule_id, organization_id, recipient_user_id, source_type,
                    scheduled_local_date, as_of_date, scheduled_for_utc, status,
                    attempt_count, candidates_count, created_count, existing_count,
                    error_code, error_summary, started_at, finished_at, created_at
                ) VALUES (?, ?, ?, 'billing_next_step_attention', ?, ?, ?, ?, 2, 7, 3, 4, ?, ?, ?, ?, ?)
                """,
                (
                    schedule_id, self.organization_id, self.user_id,
                    f"2026-01-{day:02d}", f"2026-01-{day:02d}", timestamp, status,
                    "materialization_failed" if status == "failed" else None,
                    error_summary, timestamp, f"2026-01-{day:02d}T07:00:01+00:00", timestamp,
                ),
            )

    def test_health_states_and_dashboard_query_does_not_load_history(self) -> None:
        item = self._dashboard()["items"][0]
        self.assertEqual((item["status"], item["health"]), ("not_configured", "disabled"))

        settings = self._save(enabled=False)
        item = self._dashboard()["items"][0]
        self.assertEqual((item["status"], item["health"]), ("disabled", "disabled"))

        self._save(enabled=True)
        item = self._dashboard()["items"][0]
        self.assertEqual((item["status"], item["health"]), ("enabled", "never_run"))

        self._run(int(settings["internal_notification_schedule_id"]), day=15, status="succeeded")
        repository = self.services["internal_notification_schedule_repository"]
        with patch.object(repository, "list_runs_read_only", side_effect=AssertionError("N+1 history query")):
            dashboard = self._dashboard()
        item = dashboard["items"][0]
        self.assertEqual(item["health"], "healthy")
        self.assertIsNotNone(item["next_run_at"])
        self.assertEqual(item["last_run_duration_ms"], 1000)
        self.assertEqual((item["last_candidates_count"], item["last_created_count"], item["last_existing_count"]), (7, 3, 4))

    def test_failed_run_is_attention_and_error_is_sanitized(self) -> None:
        settings = self._save()
        secret = "Traceback password=secret-token DSN=postgres://private"
        self._run(int(settings["internal_notification_schedule_id"]), day=15, status="failed", error_summary=secret)
        item = self._dashboard()["items"][0]
        self.assertEqual(item["health"], "attention")
        self.assertEqual(item["recent_failure_count"], 1)
        self.assertNotIn("secret", item["last_error_summary"].lower())
        detail = self.operations.detail(
            "internal_notification_scheduler",
            organization_id=self.organization_id,
            recipient_user_id=self.user_id,
            actor_user=self.user,
            history_limit=1000,
        )
        self.assertEqual(detail["history_limit"], 50)
        self.assertEqual(len(detail["history"]), 1)
        self.assertNotIn("lease_token", detail["history"][0])
        self.assertNotIn("secret", detail["history"][0]["error_summary"].lower())

    def test_scope_isolation_and_read_paths_do_not_write(self) -> None:
        other = self.services["organization_service"].create_organization(
            {"name": "Other Org", "slug": "automation-other", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        with self.assertRaises((PermissionError, ValueError)):
            self.operations.dashboard(
                organization_id=int(other["organization_id"]),
                recipient_user_id=self.user_id,
                actor_user=self.user,
            )
        with get_connection() as connection:
            before = {
                table: [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()]
                for table in (
                    "organizations", "email_import_runs", "email_import_items", "ksef_import_runs", "ksef_import_items",
                    "invoices", "invoice_relations", "invoice_ksef_field_overrides", "approval_requests",
                    "knowledge_processing_jobs", "knowledge_folder_watchers", "knowledge_documents",
                    "knowledge_document_versions", "knowledge_document_comments",
                    "task_reminder_outbox", "task_reminder_outbox_attempts", "task_reminder_worker_heartbeats", "tasks",
                    "automation_rules", "automation_executions",
                    "internal_notification_schedules", "internal_notification_schedule_runs",
                    "internal_notifications", "internal_notification_state_events", "event_logs",
                    "billing_bank_accounts", "billing_charge_batches", "billing_charges", "billing_contact_events",
                    "billing_models", "billing_next_step_events", "billing_notes", "billing_payer_charge_state",
                    "billing_payer_ledger_entries", "billing_payers", "billing_payment_matches",
                    "billing_payment_review_events", "billing_schools", "billing_statement_imports",
                    "billing_student_charge_state", "billing_students", "billing_transactions", "billing_work_queue_events",
                )
            }
        self._dashboard()
        with get_connection() as connection:
            after = {
                table: [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()]
                for table in before
            }
        self.assertEqual(after, before)

    def test_recipient_scope_never_returns_another_users_schedule(self) -> None:
        other_user = self.services["auth_service"].create_user(
            {
                "login": "automation-other-user", "display_name": "Other User", "password": "Automation123!",
                "role": "organization_admin", "organization_id": self.organization_id, "is_active": 1,
            },
            actor_login="admin", actor_user_id=int(self.admin["user_id"]), actor_user=self.admin,
        )
        self.scheduler.save_settings(
            organization_id=self.organization_id, recipient_user_id=int(other_user["user_id"]), actor_user=other_user,
            actor="automation-other-user", enabled=True, local_time="13:45", timezone_name="Europe/Warsaw",
        )
        own = self._dashboard()["items"][0]
        self.assertEqual(own["status"], "not_configured")
        self.assertNotEqual(own["schedule"]["local_time"], "13:45")

    def test_registry_contract_is_extensible_and_keys_are_unique(self) -> None:
        class Adapter:
            automation_key = "future_adapter"
            scope = "organization"
            capabilities = frozenset({"summary"})

            def get_operation(self, **kwargs):
                return {}

            def get_history(self, **kwargs):
                return []

        adapter = Adapter()
        registry = AutomationOperationsRegistry((adapter,))
        self.assertIs(registry.get("future_adapter"), adapter)
        with self.assertRaises(ValueError):
            AutomationOperationsRegistry((adapter, adapter))
        with self.assertRaises(ValueError):
            AutomationOperationsRegistry.validate_operation({"automation_key": "incomplete"})
        registry = self.services["automation_operations_registry"]
        self.assertEqual(
            [item.automation_key for item in registry.adapters],
            ["internal_notification_scheduler", "task_reminders", "knowledge_processing", "email_import", "ksef_import"],
        )
        self.assertEqual(len({item.automation_key for item in registry.adapters}), 5)
        self.assertTrue(all(item.scope and item.capabilities for item in registry.adapters))
        extended = AutomationOperationsRegistry((*registry.adapters, adapter))
        self.assertEqual(len(extended.adapters), 6)
        self.assertEqual(extended.adapters[:5], registry.adapters)

    def test_health_mapping_is_explicit(self) -> None:
        self.assertEqual(scheduler_health(schedule_exists=False, enabled=False, last_terminal_status=None), ("not_configured", "disabled", "schedule_not_configured"))
        self.assertEqual(scheduler_health(schedule_exists=True, enabled=True, last_terminal_status="succeeded")[1], "healthy")
        self.assertEqual(scheduler_health(schedule_exists=True, enabled=True, last_terminal_status="failed")[1], "attention")
        self.assertEqual(task_reminder_health(enabled=False, failed_count=0, latest_attempt_status=None)[1], "disabled")
        self.assertEqual(task_reminder_health(enabled=True, failed_count=0, latest_attempt_status=None)[1], "never_run")
        self.assertEqual(task_reminder_health(enabled=True, failed_count=0, latest_attempt_status="sent")[1], "healthy")
        self.assertEqual(task_reminder_health(enabled=True, failed_count=1, latest_attempt_status="sent")[1], "attention")
        self.assertEqual(knowledge_processing_health(latest_terminal_status=None, watcher_status=None)[1], "never_run")
        self.assertEqual(knowledge_processing_health(latest_terminal_status="completed", watcher_status="ok")[1], "healthy")
        self.assertEqual(knowledge_processing_health(latest_terminal_status="failed", watcher_status="ok")[1], "attention")
        self.assertEqual(knowledge_processing_health(latest_terminal_status="completed", watcher_status="error")[1], "attention")
        self.assertEqual(email_import_health(runtime_enabled=False, organization_configured=True, mailbox_configured=True, last_terminal_status=None)[1], "disabled")
        self.assertEqual(email_import_health(runtime_enabled=True, organization_configured=True, mailbox_configured=True, last_terminal_status=None)[1], "never_run")
        self.assertEqual(email_import_health(runtime_enabled=True, organization_configured=True, mailbox_configured=True, last_terminal_status="no_new_documents")[1], "healthy")
        self.assertEqual(email_import_health(runtime_enabled=True, organization_configured=True, mailbox_configured=True, last_terminal_status="completed_with_issues")[1], "attention")
        self.assertEqual(ksef_import_health(integration_enabled=False, organization_configured=True, last_terminal_status=None)[1], "disabled")
        self.assertEqual(ksef_import_health(integration_enabled=True, organization_configured=True, last_terminal_status=None)[1], "never_run")
        self.assertEqual(ksef_import_health(integration_enabled=True, organization_configured=True, last_terminal_status="no_new_documents")[1], "healthy")
        self.assertEqual(ksef_import_health(integration_enabled=True, organization_configured=True, last_terminal_status="completed_with_issues")[1], "attention")

    def test_ksef_import_health_metrics_history_privacy_isolation_and_no_n_plus_one(self) -> None:
        self.assertEqual((self._ksef_item()["status"], self._ksef_item()["health"]), ("disabled", "disabled"))
        self._configure_ksef_import(enabled=True, with_identifier=False)
        self.assertEqual(self._ksef_item()["status"], "not_configured")
        self._configure_ksef_import()
        self.assertEqual((self._ksef_item()["health"], self._ksef_item()["runtime_status"]), ("never_run", "unknown"))
        self._insert_ksef_run(status="no_new_documents", day=10)
        self.assertEqual((self._ksef_item()["health"], self._ksef_item()["last_run_status"]), ("healthy", "succeeded"))
        failed_id = self._insert_ksef_run(status="completed_with_issues", day=11)
        with patch.object(
            self.services["ksef_import_repository"],
            "list_runs_read_only",
            side_effect=AssertionError("dashboard loaded KSeF history"),
        ):
            item = self._ksef_item()
        self.assertEqual((item["health"], item["checked_document_count"], item["failed_count"]), ("attention", 7, 1))
        self.assertEqual(item["last_error_code"], "ksef_import_completed_with_issues")
        detail = self.operations.detail(
            "ksef_import", organization_id=self.organization_id, recipient_user_id=self.user_id,
            actor_user=self.user, history_limit=500,
        )
        self.assertEqual((detail["history_limit"], detail["history"][0]["run_id"]), (50, failed_id))
        self.assertEqual(detail["history"][0]["history_type"], "ksef_import_run")
        serialized = str(detail).lower()
        for forbidden in ("synthetic-taxpayer", "private-nip", "inv-secret", "987.65", "xml", "upo", "full-id", "token", "certificate"):
            self.assertNotIn(forbidden, serialized)

        other = self.services["organization_service"].create_organization(
            {"name": "KSeF Other", "slug": "ksef-other", "is_active": 1,
             "ksef_integration_enabled": 1, "ksef_company_identifier": "SYNTHETIC-TAXPAYER-B"},
            actor_user=self.admin, actor_login="admin",
        )
        other_run = self._insert_ksef_run(status="failed", day=12, organization_id=int(other["organization_id"]))
        own_ids = {run["run_id"] for run in self.operations.detail(
            "ksef_import", organization_id=self.organization_id, recipient_user_id=self.user_id,
            actor_user=self.user, history_limit=50,
        )["history"]}
        self.assertNotIn(other_run, own_ids)

    def test_email_import_health_metrics_history_privacy_and_no_n_plus_one(self) -> None:
        self._configure_email_import()
        item = self._email_item()
        self.assertEqual((item["status"], item["health"], item["runtime_status"]), ("enabled", "never_run", "unknown"))
        self.assertEqual(item["configured_connections_count"], 1)
        self._insert_email_run(status="no_new_documents", day=10)
        healthy = self._email_item()
        self.assertEqual((healthy["health"], healthy["last_run_status"]), ("healthy", "succeeded"))
        self.assertEqual((healthy["checked_message_count"], healthy["matched_message_count"]), (7, 5))
        failed_id = self._insert_email_run(status="completed_with_issues", day=11)
        with patch.object(
            self.services["email_import_repository"],
            "list_runs_read_only",
            side_effect=AssertionError("dashboard loaded e-mail history"),
        ):
            attention = self._email_item()
        self.assertEqual((attention["health"], attention["failed_count"]), ("attention", 1))
        self.assertEqual(attention["last_error_code"], "email_import_completed_with_issues")
        detail = self.operations.detail(
            "email_import",
            organization_id=self.organization_id,
            recipient_user_id=self.user_id,
            actor_user=self.user,
            history_limit=500,
        )
        self.assertEqual(detail["history_limit"], 50)
        self.assertEqual(detail["history"][0]["run_id"], failed_id)
        self.assertEqual(detail["history"][0]["history_type"], "email_import_run")
        serialized = str(detail).lower()
        for forbidden in ("private subject", "sender@", "recipient@", "message_id", "private-attachment", "token=", "body"):
            self.assertNotIn(forbidden, serialized)

    def test_email_import_disabled_configuration_and_organization_isolation(self) -> None:
        self._configure_email_import(runtime_enabled=False)
        self.assertEqual((self._email_item()["status"], self._email_item()["health"]), ("disabled", "disabled"))
        self._configure_email_import(runtime_enabled=True, mailbox_configured=False)
        self.assertEqual(self._email_item()["status"], "not_configured")
        self._configure_email_import()
        other = self.services["organization_service"].create_organization(
            {"name": "Email Other", "slug": "email-other", "is_active": 1, "email_integration_enabled": 1,
             "email_inbox_address": "route-b@example.invalid"},
            actor_user=self.admin,
            actor_login="admin",
        )
        self._insert_email_run(status="failed", day=20, organization_id=int(other["organization_id"]))
        own = self._email_item()
        self.assertEqual(own["runs_count"], 0)
        self.assertEqual(own["failed_count"], 0)

    def test_knowledge_processing_health_queue_history_privacy_and_no_n_plus_one(self) -> None:
        item = self._knowledge_item()
        self.assertTrue(item["enabled"])
        self.assertEqual((item["status"], item["health"], item["runtime_status"]), ("enabled", "never_run", "unknown"))

        self._insert_knowledge_job(status="pending", day=10)
        self._insert_knowledge_job(status="processing", day=11)
        self._insert_knowledge_job(status="completed", day=12)
        failed_id = self._insert_knowledge_job(
            status="failed",
            day=13,
            error="Traceback token=secret DSN=postgres://private C:\\Users\\private\\document.txt",
            job_type="replace",
        )
        self.services["knowledge_repository"].upsert_watch_status(
            self.organization_id,
            {
                "watch_mode": "polling",
                "last_scan_started_at": "2026-02-13T09:59:00+00:00",
                "last_scan_completed_at": "2026-02-13T10:01:00+00:00",
                "last_scan_status": "ok",
            },
        )
        with patch.object(
            self.services["knowledge_repository"],
            "list_jobs_read_only",
            side_effect=AssertionError("dashboard loaded history"),
        ):
            item = self._knowledge_item()
        self.assertEqual((item["pending_count"], item["processing_count"], item["succeeded_count"], item["failed_count"]), (1, 1, 1, 1))
        self.assertEqual((item["health"], item["last_job_status"], item["watcher_count"]), ("attention", "failed", 1))
        self.assertEqual(item["runtime_status"], "unknown")
        self.assertNotIn("secret", str(item).lower())

        detail = self.operations.detail(
            "knowledge_processing",
            organization_id=self.organization_id,
            recipient_user_id=self.user_id,
            actor_user=self.user,
            history_limit=500,
        )
        self.assertEqual(detail["history_limit"], 50)
        self.assertEqual(detail["history"][0]["job_id"], failed_id)
        self.assertEqual(detail["history"][0]["history_type"], "knowledge_job")
        self.assertEqual(len(detail["watchers"]), 1)
        serialized = str(detail).lower()
        for forbidden in ("tajny_dokument", "poufna treść", "storage/key", "c:\\users", "dsn=", "token="):
            self.assertNotIn(forbidden, serialized)

    def test_knowledge_processing_completed_job_is_healthy_and_last_activity_is_stable(self) -> None:
        self._insert_knowledge_job(status="completed", day=8)
        item = self._knowledge_item()
        self.assertEqual((item["health"], item["health_reason_code"]), ("healthy", "last_job_completed"))
        self.assertEqual(item["succeeded_count"], 1)
        self.assertEqual(item["last_success_at"], "2026-02-08T10:00:00+00:00")
        self.assertEqual(item["last_activity_at"], "2026-02-08T10:00:00+00:00")

    def test_knowledge_processing_scope_and_watcher_error_are_organization_scoped(self) -> None:
        other = self.services["organization_service"].create_organization(
            {"name": "Knowledge Other", "slug": "knowledge-other", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self._insert_knowledge_job(status="failed", day=20, organization_id=int(other["organization_id"]), error="other org error")
        own = self._knowledge_item()
        self.assertEqual(own["failed_count"], 0)
        self.services["knowledge_repository"].upsert_watch_status(
            self.organization_id,
            {"last_scan_status": "error", "last_error": "C:\\Users\\private\\folder\\scan.txt", "last_scan_completed_at": "2026-02-21T10:00:00+00:00"},
        )
        own = self._knowledge_item()
        self.assertEqual((own["health"], own["health_reason_code"]), ("attention", "last_folder_scan_failed"))
        self.assertEqual(own["last_error_summary"], "Błąd wykonania. Szczegóły techniczne zostały ukryte.")

    def test_task_reminders_health_queue_history_and_sanitization(self) -> None:
        self.assertEqual((self._reminder_item()["status"], self._reminder_item()["health"]), ("disabled", "disabled"))
        self.reminders.runtime_enabled = True
        self.reminders.telegram_adapter.bot_token = "fake-token"
        self.assertEqual(self._reminder_item()["health"], "never_run")
        self._insert_reminder(status="sent", outcome="sent")
        item = self._reminder_item()
        self.assertEqual(item["health"], "healthy")
        self.assertEqual(item["sent_count"], 1)
        self._insert_reminder(status="failed", outcome="dead_letter", error="Traceback token=secret DSN=postgres://private")
        item = self._reminder_item()
        self.assertEqual(item["health"], "attention")
        self.assertEqual(item["failed_count"], 1)
        self.assertNotIn("secret", item["last_error_summary"].lower())
        detail = self.operations.detail("task_reminders", organization_id=self.organization_id,
            recipient_user_id=self.user_id, actor_user=self.user, history_limit=100)
        self.assertEqual(detail["history_limit"], 50)
        self.assertEqual(len(detail["history"]), 2)
        self.assertEqual(len(detail["outbox"]), 2)
        self.assertNotIn("payload", str(detail).lower())
        self.assertNotIn("secret", str(detail).lower())

    def test_task_reminders_respect_private_task_visibility(self) -> None:
        other = self.services["auth_service"].create_user(
            {"login": "private-reminder-user", "display_name": "Private User", "password": "Automation123!",
             "role": "organization_admin", "organization_id": self.organization_id, "is_active": 1},
            actor_login="admin", actor_user_id=int(self.admin["user_id"]), actor_user=self.admin,
        )
        task = self.services["task_service"].create_task(
            {"title": "Prywatne przypomnienie", "task_type": "zadanie", "status": "nowe", "priority": "normalny",
             "due_at": "2099-01-01T10:00", "remind_at": "2000-01-01T09:00", "visibility_scope": "prywatne"},
            actor_user=other, actor="Private User", organization_id=self.organization_id,
        )
        with get_connection() as connection:
            connection.execute(
                """INSERT INTO task_reminder_outbox (organization_id, task_id, delivery_channel, delivery_key,
                    delivery_anchor_at, recipient_user_id, recipient_telegram_user_id, available_at, status,
                    retryable, attempt_count, payload, created_at, updated_at)
                    VALUES (?, ?, 'telegram', ?, '2026-01-15T07:00', ?, 'fake', '2026-01-15T07:00',
                    'queued', 1, 0, '{}', '2026-01-15T07:00', '2026-01-15T07:00')""",
                (self.organization_id, int(task["task_id"]), f"private-{task['task_id']}", int(other["user_id"])),
            )
        self.reminders.runtime_enabled = True
        self.reminders.telegram_adapter.bot_token = "fake-token"
        self.assertEqual(self._reminder_item()["pending_count"], 0)
        other_dashboard = self.operations.dashboard(organization_id=self.organization_id,
            recipient_user_id=int(other["user_id"]), actor_user=other)
        other_item = next(item for item in other_dashboard["items"] if item["automation_key"] == "task_reminders")
        self.assertEqual(other_item["pending_count"], 1)


if __name__ == "__main__":
    unittest.main()
