from __future__ import annotations

import json
import unittest

from tests.http_server_support import HttpServerTestCase


class WorkItemHttpTests(HttpServerTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.admin = self.services["auth_service"].list_users()[0]
        self.organization = self.services["organization_service"].create_organization(
            {
                "name": "Organizacja HTTP Work Item",
                "slug": "organizacja-http-work-item",
                "is_active": 1,
            },
            actor_user=self.admin,
            actor_login="admin",
        )
        self.owner = self.services["auth_service"].create_user(
            {
                "login": "olga_work_item",
                "display_name": "Olga Work Item",
                "password": "1234",
                "role": "coordinator",
                "is_active": 1,
                "organization_id": self.organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )
        self.assignee = self.services["auth_service"].create_user(
            {
                "login": "ania_work_item",
                "display_name": "Ania Work Item",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": self.organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )

    def test_http_work_item_endpoints_flow(self) -> None:
        cookie = self._login("olga_work_item", "1234")
        headers = {"Content-Type": "application/json", "Cookie": cookie}

        response, payload = self._request(
            "POST",
            "/api/work-items",
            body=json.dumps(
                {
                    "title": "HTTP Work Item",
                    "description": "Do obsluzenia przez API",
                    "source_type": "support",
                    "status": "nowe",
                    "priority_level": "normalny",
                    "due_at": "2099-04-10T10:00",
                    "sla_deadline_at": "2099-04-10T09:00",
                    "sla_warning_minutes": 120,
                }
            ),
            headers=headers,
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))
        created = json.loads(payload.decode("utf-8"))
        work_item_id = int(created["work_item_id"])

        response, payload = self._request("GET", "/api/work-items?limit=50", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        listed = json.loads(payload.decode("utf-8"))
        self.assertTrue(any(int(item["work_item_id"]) == work_item_id for item in listed))

        response, payload = self._request(
            "POST",
            f"/api/work-items/{work_item_id}/assign",
            body=json.dumps({"assigned_user_id": int(self.assignee["user_id"])}),
            headers=headers,
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        assigned = json.loads(payload.decode("utf-8"))
        self.assertEqual(int(assigned["assigned_user_id"]), int(self.assignee["user_id"]))

        response, payload = self._request(
            "PATCH",
            f"/api/work-items/{work_item_id}",
            body=json.dumps({"status": "w_toku", "metadata": {"is_blocker": True}}),
            headers=headers,
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        updated = json.loads(payload.decode("utf-8"))
        self.assertEqual(updated["status"], "w_toku")

        response, payload = self._request(
            "POST",
            f"/api/work-items/{work_item_id}/snooze",
            body=json.dumps({"mode": "1h"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        snoozed = json.loads(payload.decode("utf-8"))
        self.assertEqual(snoozed["sla_stage"], "on_track")

        response, payload = self._request(
            "POST",
            f"/api/work-items/{work_item_id}/close",
            body=json.dumps({"reason": "Zamkniete testowo przez HTTP."}),
            headers=headers,
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        closed = json.loads(payload.decode("utf-8"))
        self.assertEqual(closed["status"], "zamkniete")
        self.assertEqual(closed["sla_stage"], "resolved")

        response, payload = self._request(
            "POST",
            f"/api/work-items/{work_item_id}/reopen",
            body=json.dumps({"status": "w_toku", "reason": "Ponowne otwarcie przez API."}),
            headers=headers,
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        reopened = json.loads(payload.decode("utf-8"))
        self.assertEqual(reopened["status"], "w_toku")

        response, payload = self._request(
            "POST",
            "/api/work-items/bulk",
            body=json.dumps(
                {
                    "action": "assign",
                    "work_item_ids": [work_item_id],
                    "assigned_user_id": int(self.assignee["user_id"]),
                }
            ),
            headers=headers,
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        bulk = json.loads(payload.decode("utf-8"))
        self.assertEqual(int(bulk["updated"]), 1)

        response, payload = self._request(
            "POST",
            "/api/work-items/sla/sweep",
            body=json.dumps({"limit": 25}),
            headers=headers,
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        sweep = json.loads(payload.decode("utf-8"))
        self.assertIn("result", sweep)
        self.assertIn("evaluated", sweep["result"])

        response, payload = self._request("GET", "/api/work-items/summary", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        summary = json.loads(payload.decode("utf-8"))
        self.assertIn("counts", summary)
        self.assertIn("top_risk", summary)

        response, payload = self._request("GET", f"/api/work-items/{work_item_id}", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        detail = json.loads(payload.decode("utf-8"))
        self.assertEqual(detail["work_item"]["status"], "w_toku")
        self.assertTrue(any(item["action_type"] == "work_item_closed" for item in detail["history"]))
        self.assertTrue(any(item["action_type"] == "work_item_reopened" for item in detail["history"]))

    def test_http_work_item_write_actions_are_organization_scoped(self) -> None:
        admin_cookie = self._login_default_admin()
        admin_headers = {"Content-Type": "application/json", "Cookie": admin_cookie}
        second_organization = self.services["organization_service"].create_organization(
            {
                "name": "Organizacja HTTP Work Item B",
                "slug": "organizacja-http-work-item-b",
                "is_active": 1,
            },
            actor_user=self.admin,
            actor_login="admin",
        )
        org_a_item = self.services["work_item_service"].create_work_item(
            {
                "title": "Pozycja tylko org A",
                "source_type": "manual",
                "status": "nowe",
            },
            actor_user=self.owner,
            actor="Owner",
            organization_id=int(self.organization["organization_id"]),
        )
        org_b_item = self.services["work_item_service"].create_work_item(
            {
                "title": "Pozycja tylko org B",
                "source_type": "manual",
                "status": "nowe",
            },
            actor_user=self.admin,
            actor="admin",
            organization_id=int(second_organization["organization_id"]),
        )
        org_a_item_id = int(org_a_item["work_item_id"])
        org_b_item_id = int(org_b_item["work_item_id"])

        for suffix, body in (
            ("assign", {"assigned_user_id": int(self.assignee["user_id"])}),
            ("snooze", {"mode": "1h"}),
            ("close", {"reason": "Nie powinno zamknac pozycji z innej organizacji."}),
            ("escalate", {"assigned_user_id": int(self.assignee["user_id"])}),
            ("reopen", {"status": "w_toku", "reason": "Nie powinno otworzyc pozycji z innej organizacji."}),
        ):
            response, _payload = self._request(
                "POST",
                f"/api/work-items/{org_b_item_id}/{suffix}?organization_id={self.organization['organization_id']}",
                body=json.dumps(body),
                headers=admin_headers,
            )
            self.assertEqual(response.status, 404)

        response, _payload = self._request(
            "POST",
            f"/api/work-items/{org_a_item_id}/close",
            body=json.dumps({"reason": "Global admin bez organization_id."}),
            headers=admin_headers,
        )
        self.assertEqual(response.status, 400)

        org_b_detail = self.services["work_item_service"].get_work_item_detail(
            org_b_item_id,
            organization_id=int(second_organization["organization_id"]),
        )
        self.assertIsNotNone(org_b_detail)
        assert org_b_detail is not None
        self.assertEqual(org_b_detail["work_item"]["status"], "nowe")
        self.assertIsNone(org_b_detail["work_item"].get("assigned_user_id"))

    def test_http_work_item_write_actions_reject_extra_payload_fields(self) -> None:
        cookie = self._login("olga_work_item", "1234")
        headers = {"Content-Type": "application/json", "Cookie": cookie}

        cases = (
            (
                "assign",
                {"assigned_user_id": int(self.assignee["user_id"])},
                "assigned_user_id",
            ),
            (
                "snooze",
                {"mode": "1h"},
                "mode",
            ),
            (
                "close",
                {"reason": "Nie powinno zamknac pozycji z nadmiarowym payloadem."},
                "reason",
            ),
        )

        for suffix, valid_body, expected_field in cases:
            created = self.services["work_item_service"].create_work_item(
                {
                    "title": f"Payload hardening {suffix}",
                    "source_type": "manual",
                    "status": "w_toku",
                    "priority_level": "normalny",
                    "due_at": "2099-04-10T10:00",
                },
                actor_user=self.owner,
                actor="Owner",
                organization_id=int(self.organization["organization_id"]),
            )
            work_item_id = int(created["work_item_id"])
            before_detail = self.services["work_item_service"].get_work_item_detail(
                work_item_id,
                organization_id=int(self.organization["organization_id"]),
            )
            self.assertIsNotNone(before_detail)
            assert before_detail is not None
            before_item = before_detail["work_item"]
            before_history_count = len(before_detail["history"])

            body = {
                **valid_body,
                "organization_id": 999,
                "work_item_id": 999,
                "actor_user_id": 999,
                "created_at": "2026-07-02T12:00:00",
                "role": "admin",
                "status": "zamkniete",
            }
            response, payload = self._request(
                "POST",
                f"/api/work-items/{work_item_id}/{suffix}",
                body=json.dumps(body),
                headers=headers,
            )
            self.assertEqual(response.status, 400)
            error_payload = json.loads(payload.decode("utf-8"))
            self.assertIn(expected_field, error_payload["error"])

            after_detail = self.services["work_item_service"].get_work_item_detail(
                work_item_id,
                organization_id=int(self.organization["organization_id"]),
            )
            self.assertIsNotNone(after_detail)
            assert after_detail is not None
            after_item = after_detail["work_item"]
            self.assertEqual(after_item["status"], before_item["status"])
            self.assertEqual(after_item.get("assigned_user_id"), before_item.get("assigned_user_id"))
            self.assertEqual(after_item.get("due_at"), before_item.get("due_at"))
            self.assertEqual(after_item.get("sla_stage"), before_item.get("sla_stage"))
            self.assertEqual(len(after_detail["history"]), before_history_count)

    def test_http_work_item_small_backend_actions_reject_extra_payload_fields(self) -> None:
        cookie = self._login("olga_work_item", "1234")
        headers = {"Content-Type": "application/json", "Cookie": cookie}

        escalated_candidate = self.services["work_item_service"].create_work_item(
            {
                "title": "Payload hardening escalate",
                "source_type": "manual",
                "status": "w_toku",
                "priority_level": "normalny",
                "sla_deadline_at": "2099-04-10T10:00",
            },
            actor_user=self.owner,
            actor="Owner",
            organization_id=int(self.organization["organization_id"]),
        )
        escalate_id = int(escalated_candidate["work_item_id"])
        before_detail = self.services["work_item_service"].get_work_item_detail(
            escalate_id,
            organization_id=int(self.organization["organization_id"]),
        )
        self.assertIsNotNone(before_detail)
        assert before_detail is not None
        before_history_count = len(before_detail["history"])

        response, payload = self._request(
            "POST",
            f"/api/work-items/{escalate_id}/escalate",
            body=json.dumps(
                {
                    "assigned_user_id": int(self.assignee["user_id"]),
                    "organization_id": 999,
                    "work_item_id": 999,
                    "priority_level": "krytyczny",
                    "status": "zamkniete",
                    "created_at": "2026-07-02T12:00:00",
                    "role": "admin",
                }
            ),
            headers=headers,
        )
        self.assertEqual(response.status, 400, payload.decode("utf-8"))
        error_payload = json.loads(payload.decode("utf-8"))
        self.assertIn("assigned_user_id", error_payload["error"])
        after_detail = self.services["work_item_service"].get_work_item_detail(
            escalate_id,
            organization_id=int(self.organization["organization_id"]),
        )
        self.assertIsNotNone(after_detail)
        assert after_detail is not None
        self.assertEqual(after_detail["work_item"]["sla_stage"], before_detail["work_item"]["sla_stage"])
        self.assertEqual(after_detail["work_item"]["priority_level"], before_detail["work_item"]["priority_level"])
        self.assertEqual(after_detail["work_item"].get("assigned_user_id"), before_detail["work_item"].get("assigned_user_id"))
        self.assertEqual(len(after_detail["history"]), before_history_count)

        response, payload = self._request(
            "POST",
            f"/api/work-items/{escalate_id}/escalate",
            body=json.dumps({"assigned_user_id": int(self.assignee["user_id"])}),
            headers=headers,
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        escalated = json.loads(payload.decode("utf-8"))
        self.assertEqual(escalated["sla_stage"], "escalated")
        self.assertEqual(int(escalated["assigned_user_id"]), int(self.assignee["user_id"]))

        closed_candidate = self.services["work_item_service"].create_work_item(
            {
                "title": "Payload hardening reopen",
                "source_type": "manual",
                "status": "w_toku",
                "priority_level": "normalny",
            },
            actor_user=self.owner,
            actor="Owner",
            organization_id=int(self.organization["organization_id"]),
        )
        closed = self.services["work_item_service"].close_work_item(
            int(closed_candidate["work_item_id"]),
            {"reason": "Zamkniete przed testem allowlist."},
            actor_user=self.owner,
            actor="Owner",
            organization_id=int(self.organization["organization_id"]),
        )
        self.assertIsNotNone(closed)
        reopen_id = int(closed_candidate["work_item_id"])
        before_detail = self.services["work_item_service"].get_work_item_detail(
            reopen_id,
            organization_id=int(self.organization["organization_id"]),
        )
        self.assertIsNotNone(before_detail)
        assert before_detail is not None
        before_history_count = len(before_detail["history"])

        response, payload = self._request(
            "POST",
            f"/api/work-items/{reopen_id}/reopen",
            body=json.dumps(
                {
                    "status": "w_toku",
                    "reason": "Nie powinno ponownie otworzyc.",
                    "due_at": "2099-04-10T10:00",
                    "sla_deadline_at": "2099-04-10T09:00",
                    "sla_warning_minutes": 30,
                    "sla_warning_at": "2099-04-10T08:30",
                    "organization_id": 999,
                    "work_item_id": 999,
                    "actor_user_id": 999,
                    "role": "admin",
                }
            ),
            headers=headers,
        )
        self.assertEqual(response.status, 400, payload.decode("utf-8"))
        error_payload = json.loads(payload.decode("utf-8"))
        self.assertIn("status", error_payload["error"])
        self.assertIn("sla_warning_at", error_payload["error"])
        after_detail = self.services["work_item_service"].get_work_item_detail(
            reopen_id,
            organization_id=int(self.organization["organization_id"]),
        )
        self.assertIsNotNone(after_detail)
        assert after_detail is not None
        self.assertEqual(after_detail["work_item"]["status"], "zamkniete")
        self.assertEqual(len(after_detail["history"]), before_history_count)

        sweep_candidate = self.services["work_item_service"].create_work_item(
            {
                "title": "Payload hardening SLA sweep",
                "source_type": "manual",
                "status": "w_toku",
                "priority_level": "normalny",
                "sla_deadline_at": "2000-01-01T00:10",
                "sla_warning_minutes": 30,
            },
            actor_user=self.owner,
            actor="Owner",
            organization_id=int(self.organization["organization_id"]),
        )
        sweep_id = int(sweep_candidate["work_item_id"])
        before_detail = self.services["work_item_service"].get_work_item_detail(
            sweep_id,
            organization_id=int(self.organization["organization_id"]),
        )
        self.assertIsNotNone(before_detail)
        assert before_detail is not None
        before_history_count = len(before_detail["history"])

        response, payload = self._request(
            "POST",
            "/api/work-items/sla/sweep",
            body=json.dumps(
                {
                    "limit": 25,
                    "organization_id": 999,
                    "work_item_id": sweep_id,
                    "actor_user_id": 999,
                    "role": "admin",
                }
            ),
            headers=headers,
        )
        self.assertEqual(response.status, 400, payload.decode("utf-8"))
        error_payload = json.loads(payload.decode("utf-8"))
        self.assertIn("limit", error_payload["error"])
        after_detail = self.services["work_item_service"].get_work_item_detail(
            sweep_id,
            organization_id=int(self.organization["organization_id"]),
        )
        self.assertIsNotNone(after_detail)
        assert after_detail is not None
        self.assertEqual(after_detail["work_item"]["sla_stage"], before_detail["work_item"]["sla_stage"])
        self.assertEqual(after_detail["work_item"]["priority_level"], before_detail["work_item"]["priority_level"])
        self.assertEqual(len(after_detail["history"]), before_history_count)

    def test_http_work_item_policy_workload_and_filters(self) -> None:
        cookie = self._login("olga_work_item", "1234")
        headers = {"Content-Type": "application/json", "Cookie": cookie}

        response, payload = self._request(
            "POST",
            "/api/work-items/sla-policy",
            body=json.dumps(
                {
                    "auto_deadline_enabled": True,
                    "default_warning_minutes": 25,
                    "priority_targets_minutes": {
                        "normalny": 120,
                        "krytyczny": 40,
                    },
                }
            ),
            headers=headers,
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        policy_saved = json.loads(payload.decode("utf-8"))
        self.assertEqual(int(policy_saved["policy"]["default_warning_minutes"]), 25)

        response, payload = self._request("GET", "/api/work-items/sla-policy", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        policy_read = json.loads(payload.decode("utf-8"))
        self.assertEqual(int(policy_read["policy"]["priority_targets_minutes"]["krytyczny"]), 40)

        response, payload = self._request(
            "POST",
            "/api/work-items",
            body=json.dumps(
                {
                    "title": "Nieprzypisane po terminie",
                    "source_type": "manual",
                    "status": "w_toku",
                    "priority_level": "normalny",
                    "due_at": "2000-01-01T00:01",
                }
            ),
            headers=headers,
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))
        first = json.loads(payload.decode("utf-8"))
        first_id = int(first["work_item_id"])
        self.assertTrue(str(first.get("sla_deadline_at") or "").strip())

        response, payload = self._request(
            "POST",
            "/api/work-items",
            body=json.dumps(
                {
                    "title": "Przypisane na przyszlosc",
                    "source_type": "manual",
                    "status": "w_toku",
                    "priority_level": "normalny",
                    "assigned_user_id": int(self.assignee["user_id"]),
                    "due_at": "2099-01-01T09:00",
                }
            ),
            headers=headers,
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))
        second = json.loads(payload.decode("utf-8"))
        second_id = int(second["work_item_id"])

        response, payload = self._request("GET", "/api/work-items?unassigned_only=1&limit=50", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        unassigned_rows = json.loads(payload.decode("utf-8"))
        self.assertTrue(any(int(item["work_item_id"]) == first_id for item in unassigned_rows))
        self.assertFalse(any(int(item["work_item_id"]) == second_id for item in unassigned_rows))

        response, payload = self._request("GET", "/api/work-items?due_overdue_only=1&limit=50", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        overdue_rows = json.loads(payload.decode("utf-8"))
        self.assertTrue(any(int(item["work_item_id"]) == first_id for item in overdue_rows))
        self.assertFalse(any(int(item["work_item_id"]) == second_id for item in overdue_rows))

        response, payload = self._request(
            "GET",
            "/api/work-items?sort_by=due_at&sort_dir=asc&limit=50",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        sorted_rows = json.loads(payload.decode("utf-8"))
        sorted_ids = [int(item["work_item_id"]) for item in sorted_rows]
        self.assertLess(sorted_ids.index(first_id), sorted_ids.index(second_id))

        response, payload = self._request("GET", "/api/work-items/workload?limit=20", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        workload = json.loads(payload.decode("utf-8"))
        self.assertIn("summary", workload)
        self.assertGreaterEqual(int(workload["summary"]["open_items"]), 2)
        self.assertTrue(any(item["assigned_user_name"] == "Nieprzypisane" for item in workload["items"]))


if __name__ == "__main__":
    unittest.main()
