from __future__ import annotations

import json
import os
import sqlite3
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.repositories.automation_repository import AutomationRepository
from app.repositories.email_import_repository import EmailImportRepository
from app.repositories.internal_notification_schedule_repository import InternalNotificationScheduleRepository
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.ksef_import_repository import KSeFImportRepository
from app.repositories.task_reminder_outbox_repository import TaskReminderOutboxRepository
from app.db import initialize_database

from app.services.automation_operations_service import (
    AUTOMATION_ACTIVITY_FIELDS,
    AutomationEngineOperationsAdapter,
    AutomationOperationsRegistry,
    AutomationOperationsService,
    EmailImportOperationsAdapter,
    InternalNotificationSchedulerOperationsAdapter,
    KSeFImportOperationsAdapter,
    KnowledgeProcessingOperationsAdapter,
    TaskRemindersOperationsAdapter,
)
from tests.test_automation_activity_prerequisites import AutomationActivityQueryContractTests


class AutomationRecentActivityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scheduler_repository = MagicMock()
        self.reminder_repository = MagicMock()
        self.knowledge_repository = MagicMock()
        self.email_repository = MagicMock()
        self.ksef_repository = MagicMock()
        self.engine_repository = MagicMock()
        self.adapters = (
            InternalNotificationSchedulerOperationsAdapter(self.scheduler_repository),
            TaskRemindersOperationsAdapter(self.reminder_repository, MagicMock()),
            KnowledgeProcessingOperationsAdapter(self.knowledge_repository),
            EmailImportOperationsAdapter(self.email_repository, MagicMock()),
            KSeFImportOperationsAdapter(self.ksef_repository),
            AutomationEngineOperationsAdapter(self.engine_repository),
        )
        self.notification_service = MagicMock()
        self.service = AutomationOperationsService(
            registry=AutomationOperationsRegistry(self.adapters),
            notification_service=self.notification_service,
        )
        self.actor = {"user_id": 7, "organization_id": 1}

    def test_registry_has_six_activity_adapters_and_future_adapter_without_capability_is_ignored(self) -> None:
        self.assertEqual(len(self.adapters), 6)
        self.assertTrue(all("activity" in adapter.capabilities for adapter in self.adapters))

        class FutureAdapter:
            automation_key = "future"
            title = "Future"
            scope = "organization"
            capabilities = frozenset({"summary"})
            get_activity = MagicMock(side_effect=AssertionError("must not run"))

        service = AutomationOperationsService(
            registry=AutomationOperationsRegistry((*self.adapters, FutureAdapter())),
            notification_service=self.notification_service,
        )
        self._empty_sources()
        self.assertEqual(service.recent_activity(
            organization_id=1, recipient_user_id=7, actor_user=self.actor, limit=8
        )["items"], [])

    def test_all_source_mappings_are_safe_terminal_and_canonical(self) -> None:
        self.scheduler_repository.list_activity_runs_read_only.return_value = [
            {"internal_notification_schedule_run_id": 1, "status": "succeeded", "finished_at": "2026-08-13T10:00:00+00:00", "created_count": 3},
            {"internal_notification_schedule_run_id": 2, "status": "failed", "finished_at": "2026-08-13T09:00:00+00:00", "created_count": 0},
        ]
        self.reminder_repository.list_activity_attempts_read_only.return_value = [
            {"task_reminder_outbox_attempt_id": 3, "outcome": "sent", "attempted_at": "2026-08-13T11:00:00Z"},
            {"task_reminder_outbox_attempt_id": 4, "outcome": "dead_letter", "attempted_at": "2026-08-13T08:00:00+00:00"},
            {"task_reminder_outbox_attempt_id": 5, "outcome": "failed", "attempted_at": "legacy-naive"},
        ]
        self.knowledge_repository.list_activity_jobs_read_only.return_value = [
            {"knowledge_processing_job_id": 6, "job_type": "replace", "status": "completed", "finished_at": "2026-08-13T12:00:00+00:00"},
            {"knowledge_processing_job_id": 7, "job_type": "ingest", "status": "failed", "finished_at": "2026-08-13T07:00:00+00:00"},
        ]
        self.email_repository.list_activity_runs_read_only.return_value = [
            {"email_import_run_id": 8, "status": "completed", "finished_at": "2026-08-13T13:00:00+00:00", "imported_invoice_count": 4},
            {"email_import_run_id": 9, "status": "completed_with_issues", "finished_at": "2026-08-13T06:00:00+00:00", "imported_invoice_count": 1},
            {"email_import_run_id": 10, "status": "failed", "finished_at": "2026-08-13T05:00:00+00:00", "imported_invoice_count": 0},
        ]
        self.ksef_repository.list_activity_runs_read_only.return_value = [
            {"ksef_import_run_id": 11, "status": "completed", "finished_at": "2026-08-13T14:00:00+00:00", "imported_invoice_count": 2},
            {"ksef_import_run_id": 12, "status": "failed", "finished_at": None, "imported_invoice_count": 0},
        ]
        self.engine_repository.list_activity_executions_read_only.return_value = [
            {"automation_execution_id": 13, "execution_status": "success", "executed_at": "2026-08-13T15:00:00+00:00"},
            {"automation_execution_id": 14, "execution_status": "failed", "executed_at": "2026-08-13T04:00:00+00:00"},
        ]
        result = self.service.recent_activity(
            organization_id=1, recipient_user_id=7, actor_user=self.actor, limit=20
        )
        self.assertEqual(len(result["items"]), 12)
        self.assertEqual(result["items"][0]["activity_id"], "automation_engine:execution:13")
        self.assertTrue(all(set(item) == AUTOMATION_ACTIVITY_FIELDS for item in result["items"]))
        self.assertTrue(all(item["occurred_at"].endswith("+00:00") for item in result["items"]))
        self.assertEqual({item["status"] for item in result["items"]}, {"succeeded", "failed", "partial"})
        self.assertEqual({item["activity_type"] for item in result["items"]}, {"scheduled_check", "delivery", "processing", "import", "execution"})
        serialized = json.dumps(result, ensure_ascii=False).lower()
        for forbidden in ("secret", "token", "traceback", "subject", "sender", "message-id", "private.pdf", "nip", "xml", "upo", "payload", "task title"):
            self.assertNotIn(forbidden, serialized)
        self.assertIn("lokalne uruchomienie procesu importu ksef", serialized)
        self.assertNotIn("legacy-naive", serialized)

    def test_global_limit_sort_tie_and_one_bounded_call_per_source(self) -> None:
        self._empty_sources()
        self.scheduler_repository.list_activity_runs_read_only.return_value = [
            {"internal_notification_schedule_run_id": source_id, "status": "failed", "finished_at": "2026-08-13T10:00:00+00:00", "created_count": 0}
            for source_id in (1, 2, 3)
        ]
        self.engine_repository.list_activity_executions_read_only.return_value = [
            {"automation_execution_id": 4, "execution_status": "success", "executed_at": "2026-08-13T11:00:00+00:00"},
            {"automation_execution_id": 5, "execution_status": "failed", "executed_at": "2026-08-13T09:00:00+00:00"},
        ]
        result = self.service.recent_activity(
            organization_id=1, recipient_user_id=7, actor_user=self.actor, limit=3
        )
        self.assertEqual([item["activity_id"] for item in result["items"]], [
            "automation_engine:execution:4", "internal_notification_scheduler:run:3", "internal_notification_scheduler:run:2",
        ])
        repository_methods = (
            self.scheduler_repository.list_activity_runs_read_only,
            self.reminder_repository.list_activity_attempts_read_only,
            self.knowledge_repository.list_activity_jobs_read_only,
            self.email_repository.list_activity_runs_read_only,
            self.ksef_repository.list_activity_runs_read_only,
            self.engine_repository.list_activity_executions_read_only,
        )
        for repository_method in repository_methods:
            repository_method.assert_called_once()
            self.assertEqual(repository_method.call_args.kwargs["limit"], 3)

    def test_limit_validation_and_scope_validation(self) -> None:
        self._empty_sources()
        for limit in (1, 20):
            self.assertEqual(self.service.recent_activity(
                organization_id=1, recipient_user_id=7, actor_user=self.actor, limit=limit
            )["limit"], limit)
        for limit in (0, 21, -1):
            with self.assertRaises(ValueError):
                self.service.recent_activity(
                    organization_id=1, recipient_user_id=7, actor_user=self.actor, limit=limit
                )
        self.notification_service.validate_recipient_scope.assert_called()

    def _empty_sources(self) -> None:
        self.scheduler_repository.list_activity_runs_read_only.return_value = []
        self.reminder_repository.list_activity_attempts_read_only.return_value = []
        self.knowledge_repository.list_activity_jobs_read_only.return_value = []
        self.email_repository.list_activity_runs_read_only.return_value = []
        self.ksef_repository.list_activity_runs_read_only.return_value = []
        self.engine_repository.list_activity_executions_read_only.return_value = []


class AutomationRecentActivityRepositoryIntegrationTests(unittest.TestCase):
    def test_real_repositories_preserve_all_78_tables_scope_visibility_and_privacy(self) -> None:
        harness = AutomationActivityQueryContractTests(methodName="test_queries_are_scoped_terminal_bounded_safe_and_deterministic")
        live_root = str(os.getenv("AUTOMATION_RECENT_ACTIVITY_LIVE_ROOT") or "").strip()
        if live_root:
            harness.temporary = None
            harness.path = Path(live_root) / "invoice_ops.sqlite3"
            with patch("app.db.SQLITE_DB_PATH", harness.path):
                initialize_database()
            harness.connection = sqlite3.connect(harness.path)
            harness.connection.row_factory = sqlite3.Row
            harness.connection.execute("PRAGMA foreign_keys = OFF")
            harness._seed()
        else:
            harness.setUp()
        try:
            connection = harness.connection
            for task_id, owner, assignee in ((4, 20, 10), (5, 20, None)):
                connection.execute(
                    """INSERT INTO tasks
                    (task_id, organization_id, task_type, visibility_scope, owner_user_id, assigned_user_id,
                     title, status, priority, created_by_user_id, created_at, updated_at)
                    VALUES (?,1,'zadanie','prywatne',?,?,'private task','nowe','normalny',20,'x','x')""",
                    (task_id, owner, assignee),
                )
            connection.execute("INSERT INTO task_visibility_users (task_id,organization_id,user_id,created_at) VALUES (5,1,10,'x')")
            for attempt_id, task_id in ((7, 4), (8, 5)):
                connection.execute(
                    """INSERT INTO task_reminder_outbox_attempts
                    (task_reminder_outbox_attempt_id,task_reminder_outbox_id,organization_id,task_id,
                     delivery_channel,attempt_no,outcome,attempted_at,worker_name,created_at)
                    VALUES (?,?,1,?,'telegram',1,'sent','2026-01-04T10:00:00+00:00','test','x')""",
                    (attempt_id, attempt_id, task_id),
                )
            connection.commit()
            before = harness._table_hashes()
            self.assertEqual(len(before), 78)

            adapters = (
                InternalNotificationSchedulerOperationsAdapter(InternalNotificationScheduleRepository()),
                TaskRemindersOperationsAdapter(TaskReminderOutboxRepository(), MagicMock()),
                KnowledgeProcessingOperationsAdapter(KnowledgeRepository()),
                EmailImportOperationsAdapter(EmailImportRepository(), MagicMock()),
                KSeFImportOperationsAdapter(KSeFImportRepository()),
                AutomationEngineOperationsAdapter(AutomationRepository()),
            )
            service = AutomationOperationsService(
                registry=AutomationOperationsRegistry(adapters),
                notification_service=MagicMock(),
            )
            with patch("app.db.SQLITE_DB_PATH", harness.path):
                results = {
                    limit: service.recent_activity(
                        organization_id=1,
                        recipient_user_id=10,
                        actor_user={"user_id": 10, "organization_id": 1},
                        limit=limit,
                    )
                    for limit in (8, 3, 20)
                }
                for invalid_limit in (0, 21, -1):
                    with self.assertRaises(ValueError):
                        service.recent_activity(
                            organization_id=1,
                            recipient_user_id=10,
                            actor_user={"user_id": 10, "organization_id": 1},
                            limit=invalid_limit,
                        )
            self.assertEqual({limit: len(value["items"]) for limit, value in results.items()}, {8: 8, 3: 3, 20: 16})
            result = results[20]

            activity_ids = {item["activity_id"] for item in result["items"]}
            self.assertIn("task_reminders:attempt:7", activity_ids, "assignee visibility")
            self.assertIn("task_reminders:attempt:8", activity_ids, "explicit visibility")
            self.assertNotIn("task_reminders:attempt:5", activity_ids, "unauthorized task")
            self.assertFalse(any(item_id.endswith(":99") for item_id in activity_ids), "cross-org rows")
            self.assertFalse(any(item_id.endswith(":1") and item_id.startswith("task_reminders") for item_id in activity_ids), "legacy naive")
            serialized = json.dumps(result, ensure_ascii=False).lower()
            for forbidden in ("private task", "secret.pdf", "secret-key", "private-trigger", "payload", "token", "raw_error"):
                self.assertNotIn(forbidden, serialized)
            self.assertEqual(before, harness._table_hashes())
            self.assertEqual(connection.execute("PRAGMA quick_check").fetchone()[0], "ok")
        finally:
            if live_root:
                harness.connection.close()
            else:
                harness.tearDown()


if __name__ == "__main__":
    unittest.main()
