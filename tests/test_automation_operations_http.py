from __future__ import annotations

import json
import unittest

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
    def _counts() -> dict[str, int]:
        tables = (
            "internal_notification_schedules", "internal_notification_schedule_runs", "internal_notifications",
            "internal_notification_state_events", "event_logs", "billing_transactions", "billing_charges",
            "billing_payment_matches", "billing_payer_ledger_entries", "billing_next_step_events",
        )
        with get_connection() as connection:
            return {table: int(connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"]) for table in tables}

    def test_dashboard_and_detail_are_read_only(self) -> None:
        before = self._counts()
        response, payload = self._request("GET", f"/api/automations/operations?organization_id={self.organization_id}", headers=self.headers)
        self.assertEqual(response.status, 200, payload.decode())
        dashboard = json.loads(payload)
        self.assertEqual(len(dashboard["items"]), 1)
        self.assertEqual(dashboard["items"][0]["automation_key"], "internal_notification_scheduler")
        response, payload = self._request("GET", f"/api/automations/operations/internal_notification_scheduler?organization_id={self.organization_id}&limit=20", headers=self.headers)
        self.assertEqual(response.status, 200, payload.decode())
        self.assertEqual(json.loads(payload)["history"], [])
        self.assertEqual(self._counts(), before)

    def test_unknown_key_recipient_override_and_cross_org_are_rejected(self) -> None:
        response, _ = self._request("GET", f"/api/automations/operations/unknown?organization_id={self.organization_id}", headers=self.headers)
        self.assertEqual(response.status, 404)
        response, _ = self._request("GET", f"/api/automations/operations?organization_id={self.organization_id}&recipient_user_id=1", headers=self.headers)
        self.assertEqual(response.status, 400)
        response, payload = self._request("GET", f"/api/automations/operations?organization_id={int(self.other['organization_id'])}", headers=self.headers)
        self.assertIn(response.status, {403, 404}, payload.decode())


if __name__ == "__main__":
    unittest.main()
