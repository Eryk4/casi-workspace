from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor

from app.db import get_connection
from tests.http_server_support import HttpServerTestCase


class InternalNotificationsTests(HttpServerTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.admin = self.services["auth_service"].list_users()[0]
        self.organization = self.services["organization_service"].create_organization(
            {"name": "Notifications Org", "slug": "notifications-org", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.other_organization = self.services["organization_service"].create_organization(
            {"name": "Notifications Other", "slug": "notifications-other", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.organization_id = int(self.organization["organization_id"])
        self.other_organization_id = int(self.other_organization["organization_id"])
        self.recipient_user_id = int(self.admin["user_id"])
        self.service = self.services["internal_notification_service"]
        self.billing = self.services["billing_service"]
        self.cookie = self._login_default_admin()

    def _add_step(self, title: str, planned_for: str | None, *, organization_id: int | None = None, action: str = "planned", parent: int | None = None):
        payload = {
            "target_type": "work_queue_issue",
            "related_issue_key": f"notifications::{title}",
            "step_type": "call",
            "event_action": action,
            "title": title,
            "planned_for": planned_for,
        }
        if parent is not None:
            payload["parent_event_id"] = parent
        return self.billing.add_next_step_event(
            payload,
            actor_user=self.admin,
            actor="admin",
            organization_id=organization_id or self.organization_id,
        )

    @staticmethod
    def _counts() -> dict[str, int]:
        tables = (
            "billing_transactions", "billing_charges", "billing_payment_matches",
            "billing_payer_ledger_entries", "billing_next_step_events", "event_logs",
            "internal_notifications", "internal_notification_state_events",
        )
        with get_connection() as connection:
            return {table: int(connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"]) for table in tables}

    def _materialize(self, as_of_date: str):
        return self.service.materialize_billing_attention(
            organization_id=self.organization_id,
            recipient_user_id=self.recipient_user_id,
            trigger_actor_user=self.admin,
            trigger_actor="admin",
            as_of_date=as_of_date,
        )

    def test_materialization_uses_attention_is_idempotent_and_financially_read_only(self) -> None:
        overdue = self._add_step("Overdue", "2026-07-20")
        today = self._add_step("Today", "2026-07-29")
        self._add_step("Future", "2026-08-02")
        self._add_step("No date", None)
        duplicate_a = self._add_step("Duplicate", "2026-07-21")
        duplicate_b = self._add_step("Duplicate", "2026-07-21")
        snooze_parent = self._add_step("Snoozed", "2026-07-18")
        snoozed = self._add_step("Snoozed", "2026-07-25", action="snoozed", parent=int(snooze_parent["billing_next_step_event_id"]))
        self._add_step("Foreign", "2026-07-20", organization_id=self.other_organization_id)
        before = self._counts()

        first = self._materialize("2026-07-29")
        second = self._materialize("2026-07-29")
        self.assertEqual(first["created_count"], 5)
        self.assertEqual(first["existing_count"], 0)
        self.assertEqual(second["created_count"], 0)
        self.assertEqual(second["existing_count"], 5)
        page = self.service.list_notifications(
            organization_id=self.organization_id, recipient_user_id=self.recipient_user_id,
            actor_user=self.admin, filter_name="inbox", limit=50,
        )
        source_ids = {item["source_event_id"] for item in page["items"]}
        self.assertEqual(source_ids, {
            int(overdue["billing_next_step_event_id"]), int(today["billing_next_step_event_id"]),
            int(duplicate_a["billing_next_step_event_id"]), int(duplicate_b["billing_next_step_event_id"]),
            int(snoozed["billing_next_step_event_id"]),
        })
        after = self._counts()
        for table in ("billing_transactions", "billing_charges", "billing_payment_matches", "billing_payer_ledger_entries", "billing_next_step_events"):
            self.assertEqual(after[table], before[table])

    def test_due_today_and_later_overdue_are_distinct_and_concurrent_calls_dedupe(self) -> None:
        step = self._add_step("Boundary", "2026-07-29")
        today = self._materialize("2026-07-29")
        overdue = self._materialize("2026-07-30")
        self.assertEqual(today["created_count"], 1)
        self.assertEqual(overdue["created_count"], 1)
        self._add_step("Concurrent", "2026-07-20")
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: self._materialize("2026-07-30"), range(2)))
        self.assertEqual(sum(result["created_count"] for result in results), 1)
        with get_connection() as connection:
            reasons = connection.execute(
                "SELECT reason_code FROM internal_notifications WHERE source_event_id = ? ORDER BY reason_code",
                (int(step["billing_next_step_event_id"]),),
            ).fetchall()
        self.assertEqual([row["reason_code"] for row in reasons], ["due_today", "overdue"])

    def test_internal_materialization_accepts_explicit_global_recipient_scope(self) -> None:
        self._add_step("Internal scheduler extension", "2026-07-20")
        result = self.service.materialize_billing_attention(
            organization_id=self.organization_id,
            recipient_user_id=self.recipient_user_id,
            trigger_actor_user=None,
            trigger_actor="internal-test",
            as_of_date="2026-07-29",
        )
        self.assertEqual(result["created_count"], 1)
        self.assertEqual(result["recipient_user_id"], self.recipient_user_id)

    def test_pagination_filters_and_cursor_scope_are_stable(self) -> None:
        repository = self.services["internal_notification_repository"]
        for index in range(105):
            repository.create_notification({
                "organization_id": self.organization_id,
                "recipient_user_id": self.recipient_user_id,
                "source_type": "billing_next_step_attention",
                "source_event_id": 1000 + index,
                "reason_code": "overdue",
                "detected_on": "2026-07-29",
                "planned_for": "2026-07-20",
                "title_snapshot": f"Page {index}",
                "target_type": "billing_summary",
                "target_label_snapshot": "Podsumowanie",
                "dedupe_key": f"page-{index}",
                "created_by_user_id": self.recipient_user_id,
                "created_at": f"2026-07-29T10:{index // 60:02d}:{index % 60:02d}+00:00",
            })
        first = self.service.list_notifications(organization_id=self.organization_id, recipient_user_id=self.recipient_user_id, actor_user=self.admin, limit=50)
        second = self.service.list_notifications(organization_id=self.organization_id, recipient_user_id=self.recipient_user_id, actor_user=self.admin, limit=50, cursor=first["next_cursor"])
        third = self.service.list_notifications(organization_id=self.organization_id, recipient_user_id=self.recipient_user_id, actor_user=self.admin, limit=100, cursor=second["next_cursor"])
        ids = [item["internal_notification_id"] for page in (first, second, third) for item in page["items"]]
        self.assertEqual(len(ids), 105)
        self.assertEqual(len(set(ids)), 105)
        self.assertTrue(first["has_more"])
        self.assertLessEqual(len(first["items"]), 50)
        with self.assertRaises(ValueError):
            self.service.list_notifications(organization_id=self.other_organization_id, recipient_user_id=self.recipient_user_id, actor_user=self.admin, limit=50, cursor=first["next_cursor"])

    def test_state_is_append_only_scoped_audited_and_archived_terminal(self) -> None:
        self._add_step("State", "2026-07-20")
        notification_id = self._materialize("2026-07-29")["created_notification_ids"][0]
        state_before = self._counts()
        read = self.service.add_state_event(notification_id, "read", organization_id=self.organization_id, recipient_user_id=self.recipient_user_id, actor_user=self.admin, actor="admin")
        unread = self.service.add_state_event(notification_id, "unread", organization_id=self.organization_id, recipient_user_id=self.recipient_user_id, actor_user=self.admin, actor="admin")
        archived = self.service.add_state_event(notification_id, "archived", organization_id=self.organization_id, recipient_user_id=self.recipient_user_id, actor_user=self.admin, actor="admin")
        repeated = self.service.add_state_event(notification_id, "archived", organization_id=self.organization_id, recipient_user_id=self.recipient_user_id, actor_user=self.admin, actor="admin")
        self.assertTrue(read["changed"] and unread["changed"] and archived["changed"])
        self.assertFalse(repeated["changed"])
        self.assertEqual([event["action"] for event in self.services["internal_notification_repository"].list_state_events(notification_id)], ["read", "unread", "archived"])
        with self.assertRaises(ValueError):
            self.service.add_state_event(notification_id, "read", organization_id=self.organization_id, recipient_user_id=self.recipient_user_id, actor_user=self.admin, actor="admin")
        with self.assertRaises(Exception):
            self.service.add_state_event(notification_id, "read", organization_id=self.other_organization_id, recipient_user_id=self.recipient_user_id, actor_user=self.admin, actor="admin")
        state_after = self._counts()
        self.assertEqual(state_after["internal_notification_state_events"] - state_before["internal_notification_state_events"], 3)
        self.assertEqual(state_after["event_logs"] - state_before["event_logs"], 3)

    def test_get_endpoints_are_read_only_and_http_writes_are_allowlisted(self) -> None:
        self._add_step("HTTP", "2026-07-20")
        before_get = self._counts()
        headers = {"Cookie": self.cookie}
        for path in (
            f"/api/internal-notifications?organization_id={self.organization_id}",
            f"/api/internal-notifications/unread-count?organization_id={self.organization_id}",
        ):
            response, payload = self._request("GET", path, headers=headers)
            self.assertEqual(response.status, 200, payload.decode())
        self.assertEqual(self._counts(), before_get)
        response, payload = self._request("POST", f"/api/internal-notifications/materialize-attention?organization_id={self.organization_id}", body="{}", headers={**headers, "Content-Type": "application/json"})
        self.assertEqual(response.status, 201, payload.decode())
        materialized = json.loads(payload)
        notification_id = materialized["created_notification_ids"][0]
        response, payload = self._request("POST", f"/api/internal-notifications/{notification_id}/state?organization_id={self.organization_id}", body=json.dumps({"action": "read", "unexpected": 1}), headers={**headers, "Content-Type": "application/json"})
        self.assertEqual(response.status, 400, payload.decode())
        response, payload = self._request("POST", f"/api/internal-notifications/{notification_id}/state?organization_id={self.organization_id}", body=json.dumps({"action": "read"}), headers={**headers, "Content-Type": "application/json"})
        self.assertEqual(response.status, 201, payload.decode())

    def test_historical_snapshot_survives_source_completion(self) -> None:
        step = self._add_step("Historical", "2026-07-20")
        notification_id = self._materialize("2026-07-29")["created_notification_ids"][0]
        self._add_step("Historical", "2026-07-20", action="completed", parent=int(step["billing_next_step_event_id"]))
        page = self.service.list_notifications(organization_id=self.organization_id, recipient_user_id=self.recipient_user_id, actor_user=self.admin, filter_name="all", limit=50)
        notification = next(item for item in page["items"] if item["internal_notification_id"] == notification_id)
        self.assertEqual(notification["title_snapshot"], "Historical")
        self.assertEqual(notification["state"], "unread")


if __name__ == "__main__":
    import unittest
    unittest.main()
