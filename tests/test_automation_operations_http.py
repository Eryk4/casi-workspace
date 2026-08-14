from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from app.data_migration_manifest import MIGRATION_MANIFEST
from app.db import get_connection
from tests.http_server_support import HttpServerTestCase


class AutomationOperationsHttpTests(HttpServerTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.admin = self.services["auth_service"].list_users()[0]
        self.organization = self.services["organization_service"].create_organization(
            {"name": "Automation HTTP", "slug": "automation-http", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.other = self.services["organization_service"].create_organization(
            {"name": "Automation HTTP Other", "slug": "automation-http-other", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.organization_id = int(self.organization["organization_id"])
        self.user = self.services["auth_service"].create_user(
            {"login": "automation-http-user", "display_name": "Automation HTTP User", "password": "Automation123!", "role": "organization_admin", "organization_id": self.organization_id, "is_active": 1},
            actor_login="admin", actor_user_id=int(self.admin["user_id"]), actor_user=self.admin,
        )
        self.headers = {"Cookie": self._login("automation-http-user", "Automation123!")}

    @staticmethod
    def _counts() -> dict[str, list[dict[str, object]]]:
        tables = (
            "organizations", "email_import_runs", "email_import_items", "ksef_import_runs", "ksef_import_items",
            "invoices", "invoice_relations", "invoice_ksef_field_overrides", "approval_requests",
            "knowledge_processing_jobs", "knowledge_folder_watchers", "knowledge_documents",
            "knowledge_document_versions", "knowledge_document_comments",
            "task_reminder_outbox", "task_reminder_outbox_attempts", "task_reminder_worker_heartbeats", "tasks",
            "automation_rules", "automation_executions",
            "internal_notification_schedules", "internal_notification_schedule_runs", "internal_notifications",
            "internal_notification_state_events", "event_logs", "billing_transactions", "billing_charges",
            "billing_bank_accounts", "billing_charge_batches", "billing_contact_events", "billing_models",
            "billing_next_step_events", "billing_notes", "billing_payer_charge_state", "billing_payer_ledger_entries",
            "billing_payers", "billing_payment_matches", "billing_payment_review_events", "billing_schools",
            "billing_statement_imports", "billing_student_charge_state", "billing_students", "billing_work_queue_events",
        )
        with get_connection() as connection:
            return {table: [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()] for table in tables}

    @staticmethod
    def _full_snapshot() -> dict[str, list[dict[str, object]]]:
        with get_connection() as connection:
            return {
                spec.source_table: [dict(row) for row in connection.execute(f'SELECT * FROM "{spec.source_table}" ORDER BY 1').fetchall()]
                for spec in MIGRATION_MANIFEST
            }

    def test_dashboard_and_detail_are_read_only(self) -> None:
        before = self._counts()
        response, payload = self._request("GET", f"/api/automations/operations?organization_id={self.organization_id}", headers=self.headers)
        self.assertEqual(response.status, 200, payload.decode())
        dashboard = json.loads(payload)
        self.assertEqual(len(dashboard["items"]), 6)
        self.assertEqual(dashboard["summary"]["attention_count"], len(dashboard["attention_items"]))
        self.assertTrue(all(
            attention["automation_key"] in {item["automation_key"] for item in dashboard["items"]}
            for attention in dashboard["attention_items"]
        ))
        self.assertEqual(dashboard["items"][0]["automation_key"], "internal_notification_scheduler")
        self.assertEqual(dashboard["items"][1]["automation_key"], "task_reminders")
        self.assertEqual(dashboard["items"][2]["automation_key"], "knowledge_processing")
        self.assertEqual(dashboard["items"][3]["automation_key"], "email_import")
        self.assertEqual(dashboard["items"][4]["automation_key"], "ksef_import")
        self.assertEqual(dashboard["items"][5]["automation_key"], "automation_engine")
        response, payload = self._request("GET", f"/api/automations/operations/internal_notification_scheduler?organization_id={self.organization_id}&limit=20", headers=self.headers)
        self.assertEqual(response.status, 200, payload.decode())
        self.assertEqual(json.loads(payload)["history"], [])
        response, payload = self._request("GET", f"/api/automations/operations/task_reminders?organization_id={self.organization_id}&limit=20", headers=self.headers)
        self.assertEqual(response.status, 200, payload.decode())
        self.assertEqual(json.loads(payload)["history"], [])
        response, payload = self._request("GET", f"/api/automations/operations/knowledge_processing?organization_id={self.organization_id}&limit=20", headers=self.headers)
        self.assertEqual(response.status, 200, payload.decode())
        knowledge = json.loads(payload)
        self.assertEqual(knowledge["history"], [])
        self.assertEqual(knowledge["watchers"], [])
        response, payload = self._request("GET", f"/api/automations/operations/email_import?organization_id={self.organization_id}&limit=20", headers=self.headers)
        self.assertEqual(response.status, 200, payload.decode())
        email_import = json.loads(payload)
        self.assertEqual(email_import["history"], [])
        self.assertEqual(email_import["item"]["runtime_status"], "unknown")
        response, payload = self._request("GET", f"/api/automations/operations/ksef_import?organization_id={self.organization_id}&limit=20", headers=self.headers)
        self.assertEqual(response.status, 200, payload.decode())
        ksef_import = json.loads(payload)
        self.assertEqual(ksef_import["history"], [])
        self.assertEqual(ksef_import["item"]["runtime_status"], "unknown")
        response, payload = self._request("GET", f"/api/automations/operations/automation_engine?organization_id={self.organization_id}&limit=20", headers=self.headers)
        self.assertEqual(response.status, 200, payload.decode())
        automation_engine = json.loads(payload)
        self.assertTrue(all(entry["history_type"] == "automation_execution" for entry in automation_engine["history"]))
        self.assertTrue(all(rule["title"].startswith("Reguła #") for rule in automation_engine["rules"]))
        serialized_engine = str(automation_engine).lower()
        for forbidden in ("conditions_json", "actions_json", "input_json", "result_json", "traceback", "postgres://", "token"):
            self.assertNotIn(forbidden, serialized_engine)
        self.assertEqual(automation_engine["item"]["runtime_status"], "unknown")
        self.assertEqual(self._counts(), before)

    def test_unknown_key_recipient_override_and_cross_org_are_rejected(self) -> None:
        response, _ = self._request("GET", f"/api/automations/operations/unknown?organization_id={self.organization_id}", headers=self.headers)
        self.assertEqual(response.status, 404)
        response, _ = self._request("GET", f"/api/automations/operations?organization_id={self.organization_id}&recipient_user_id=1", headers=self.headers)
        self.assertEqual(response.status, 400)
        response, payload = self._request("GET", f"/api/automations/operations?organization_id={int(self.other['organization_id'])}", headers=self.headers)
        self.assertEqual(response.status, 404, payload.decode())
        response, payload = self._request("GET", f"/api/automations/operations/knowledge_processing?organization_id={int(self.other['organization_id'])}", headers=self.headers)
        self.assertEqual(response.status, 404, payload.decode())
        response, payload = self._request("GET", f"/api/automations/operations/email_import?organization_id={int(self.other['organization_id'])}", headers=self.headers)
        self.assertEqual(response.status, 404, payload.decode())
        response, payload = self._request("GET", f"/api/automations/operations/ksef_import?organization_id={int(self.other['organization_id'])}", headers=self.headers)
        self.assertEqual(response.status, 404, payload.decode())
        response, payload = self._request("GET", f"/api/automations/operations/automation_engine?organization_id={int(self.other['organization_id'])}", headers=self.headers)
        self.assertEqual(response.status, 404, payload.decode())

    def test_activity_limits_scope_read_only_and_safe_error_isolation(self) -> None:
        before = self._counts()
        full_before = self._full_snapshot()
        service = self.services["automation_operations_service"]
        with patch.object(service, "recent_activity", wraps=service.recent_activity) as recent_activity:
            for suffix, expected_limit in (("", 8), ("&limit=1", 1), ("&limit=20", 20)):
                response, payload = self._request(
                    "GET", f"/api/automations/operations/activity?organization_id={self.organization_id}{suffix}",
                    headers=self.headers,
                )
                self.assertEqual(response.status, 200, payload.decode())
                self.assertEqual(json.loads(payload), {"items": [], "limit": expected_limit})
            self.assertEqual(recent_activity.call_count, 3)
        for invalid in ("0", "21", "-1", "abc", "1.5"):
            response, payload = self._request(
                "GET", f"/api/automations/operations/activity?organization_id={self.organization_id}&limit={invalid}",
                headers=self.headers,
            )
            self.assertEqual(response.status, 400, payload.decode())
        response, _ = self._request(
            "GET", f"/api/automations/operations/activity?organization_id={self.organization_id}&recipient_user_id=1",
            headers=self.headers,
        )
        self.assertEqual(response.status, 400)
        response, _ = self._request(
            "GET", f"/api/automations/operations/activity?organization_id={int(self.other['organization_id'])}",
            headers=self.headers,
        )
        self.assertEqual(response.status, 404)
        self.assertEqual(self._counts(), before)

        with patch.object(service, "recent_activity", side_effect=RuntimeError("SQL secret token traceback")):
            response, payload = self._request(
                "GET", f"/api/automations/operations/activity?organization_id={self.organization_id}",
                headers=self.headers,
            )
            self.assertEqual(response.status, 500)
            serialized = payload.decode().lower()
            self.assertIn("nie udało się pobrać ostatniej aktywności", serialized)
            for forbidden in ("sql", "secret", "token", "traceback"):
                self.assertNotIn(forbidden, serialized)
        response, _ = self._request(
            "GET", f"/api/automations/operations?organization_id={self.organization_id}", headers=self.headers
        )
        self.assertEqual(response.status, 200)
        full_after = self._full_snapshot()
        self.assertEqual(len(full_before), 78)
        for table in full_before:
            if table != "user_sessions":
                self.assertEqual(full_after[table], full_before[table], table)
        normalize_sessions = lambda rows: [
            {key: (None if key == "last_seen_at" else value) for key, value in row.items()}
            for row in rows
        ]
        self.assertEqual(normalize_sessions(full_after["user_sessions"]), normalize_sessions(full_before["user_sessions"]))


if __name__ == "__main__":
    unittest.main()
