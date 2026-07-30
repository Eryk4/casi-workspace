from __future__ import annotations

import json
import unittest

from app.db import get_connection
from tests.http_server_support import HttpServerTestCase


class InternalNotificationSchedulerHttpTests(HttpServerTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.admin = self.services["auth_service"].list_users()[0]
        self.organization = self.services["organization_service"].create_organization(
            {"name": "Scheduler HTTP", "slug": "scheduler-http", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.other = self.services["organization_service"].create_organization(
            {"name": "Scheduler Other", "slug": "scheduler-other", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.organization_id = int(self.organization["organization_id"])
        self.user = self.services["auth_service"].create_user(
            {
                "login": "scheduler-http-user",
                "display_name": "Scheduler HTTP User",
                "password": "Scheduler123!",
                "role": "organization_admin",
                "organization_id": self.organization_id,
                "is_active": 1,
            },
            actor_login="admin",
            actor_user_id=int(self.admin["user_id"]),
            actor_user=self.admin,
        )
        self.cookie = self._login("scheduler-http-user", "Scheduler123!")
        self.headers = {"Cookie": self.cookie}

    @staticmethod
    def _counts() -> dict[str, int]:
        with get_connection() as connection:
            return {
                table: int(connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"])
                for table in ("internal_notification_schedules", "internal_notification_schedule_runs", "internal_notifications", "event_logs")
            }

    def test_get_defaults_and_history_are_read_only(self) -> None:
        before = self._counts()
        response, payload = self._request(
            "GET", f"/api/internal-notifications/schedule?organization_id={self.organization_id}", headers=self.headers,
        )
        self.assertEqual(response.status, 200, payload.decode())
        settings = json.loads(payload)
        self.assertFalse(settings["exists"])
        self.assertFalse(settings["enabled"])
        self.assertEqual(settings["local_time"], "08:00")
        self.assertEqual(settings["timezone_name"], "Europe/Warsaw")
        response, payload = self._request(
            "GET", f"/api/internal-notifications/schedule/runs?organization_id={self.organization_id}", headers=self.headers,
        )
        self.assertEqual(response.status, 200, payload.decode())
        self.assertEqual(json.loads(payload)["items"], [])
        self.assertEqual(self._counts(), before)

    def test_explicit_save_upserts_audits_and_does_not_materialize(self) -> None:
        before = self._counts()
        body = json.dumps({
            "enabled": True,
            "local_time": "08:30",
            "timezone_name": "Europe/Warsaw",
            "cadence": "daily",
        })
        for expected_time in ("08:30", "09:15"):
            current_body = body if expected_time == "08:30" else json.dumps({
                "enabled": True, "local_time": expected_time, "timezone_name": "Europe/Warsaw", "cadence": "daily",
            })
            response, payload = self._request(
                "POST", f"/api/internal-notifications/schedule?organization_id={self.organization_id}",
                body=current_body, headers={**self.headers, "Content-Type": "application/json"},
            )
            self.assertEqual(response.status, 200, payload.decode())
            self.assertEqual(json.loads(payload)["local_time"], expected_time)
        after = self._counts()
        self.assertEqual(after["internal_notification_schedules"] - before["internal_notification_schedules"], 1)
        self.assertEqual(after["internal_notification_schedule_runs"], before["internal_notification_schedule_runs"])
        self.assertEqual(after["internal_notifications"], before["internal_notifications"])
        self.assertEqual(after["event_logs"] - before["event_logs"], 2)

    def test_invalid_payloads_and_foreign_scope_are_rejected(self) -> None:
        invalid_payloads = (
            {"enabled": True, "local_time": "25:00", "timezone_name": "Europe/Warsaw"},
            {"enabled": True, "local_time": "08:00", "timezone_name": "Invalid/Zone"},
            {"enabled": True, "local_time": "08:00", "timezone_name": "Europe/Warsaw", "cadence": "hourly"},
            {"enabled": True, "local_time": "08:00", "timezone_name": "Europe/Warsaw", "organization_id": 999},
            {"enabled": "true", "local_time": "08:00", "timezone_name": "Europe/Warsaw"},
        )
        for payload_value in invalid_payloads:
            response, _ = self._request(
                "POST", f"/api/internal-notifications/schedule?organization_id={self.organization_id}",
                body=json.dumps(payload_value), headers={**self.headers, "Content-Type": "application/json"},
            )
            self.assertEqual(response.status, 400)
        response, payload = self._request(
            "GET", f"/api/internal-notifications/schedule?organization_id={int(self.other['organization_id'])}", headers=self.headers,
        )
        self.assertIn(response.status, {403, 404}, payload.decode())


if __name__ == "__main__":
    unittest.main()
