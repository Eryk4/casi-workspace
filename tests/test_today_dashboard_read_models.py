from __future__ import annotations

from datetime import datetime
import hashlib
import json
from unittest.mock import patch

from app import db as db_module
from app.data_migration_manifest import MIGRATION_MANIFEST
from app.db import get_connection
from app.domain.constants import KNOWLEDGE_READ_CAPABILITY
from tests.http_server_support import HttpServerTestCase


REFERENCE_NOW = datetime(2026, 3, 29, 12, 0)
REFERENCE_DATE = "2026-03-29"


class TodayDashboardReadModelsTests(HttpServerTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.auth_service = self.services["auth_service"]
        self.admin = self.auth_service.list_users()[0]
        self.organization = self.services["organization_service"].create_organization(
            {"name": "Today Read Models", "slug": "today-read-models", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.organization_id = int(self.organization["organization_id"])
        self.other_organization = self.services["organization_service"].create_organization(
            {"name": "Today Other", "slug": "today-other", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.other_organization_id = int(self.other_organization["organization_id"])
        self.users = {"system_owner": self.admin}
        for role in ("organization_admin", "coordinator", "operator", "guest"):
            self.users[role] = self.auth_service.create_user(
                {
                    "login": f"today-{role}",
                    "display_name": f"Today {role}",
                    "password": "Today123!",
                    "role": role,
                    "organization_id": self.organization_id,
                    "is_active": 1,
                    "capabilities": [KNOWLEDGE_READ_CAPABILITY],
                },
                actor_login="admin",
                actor_user_id=int(self.admin["user_id"]),
                actor_user=self.admin,
            )

    def _cookie(self, role: str) -> str:
        if role == "system_owner":
            return self._login("admin", "Admin1234")
        return self._login(f"today-{role}", "Today123!")

    def _insert_task(
        self,
        title: str,
        *,
        organization_id: int | None = None,
        owner_user_id: int | None = None,
        assigned_user_id: int | None = None,
        visibility_scope: str = "prywatne",
        due_at: str | None = None,
        remind_at: str | None = None,
        status: str = "nowe",
        visible_user_ids: tuple[int, ...] = (),
    ) -> int:
        organization_id = organization_id or self.organization_id
        owner_user_id = owner_user_id or int(self.users["organization_admin"]["user_id"])
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO tasks (
                    organization_id, task_type, visibility_scope, owner_user_id, title, description,
                    status, priority, due_at, remind_at, recurrence_pattern, recurrence_interval,
                    assigned_user_id, created_by_user_id, created_at, updated_at
                ) VALUES (?, 'zadanie', ?, ?, ?, 'PRIVATE DESCRIPTION', ?, 'normalny', ?, ?,
                    'brak', 1, ?, ?, '2026-03-01T10:00:00+00:00', '2026-03-01T10:00:00+00:00')
                """,
                (
                    organization_id,
                    visibility_scope,
                    owner_user_id,
                    title,
                    status,
                    due_at,
                    remind_at,
                    assigned_user_id,
                    owner_user_id,
                ),
            )
            task_id = int(cursor.lastrowid)
            for user_id in visible_user_ids:
                connection.execute(
                    """
                    INSERT INTO task_visibility_users (task_id, organization_id, user_id, created_at)
                    VALUES (?, ?, ?, '2026-03-01T10:00:00+00:00')
                    """,
                    (task_id, organization_id, user_id),
                )
        return task_id

    def _insert_billing_event(
        self,
        title: str,
        *,
        organization_id: int | None = None,
        target_type: str = "work_queue_issue",
        target_id: int | None = None,
        event_action: str = "planned",
        parent_event_id: int | None = None,
        planned_for: str | None = None,
    ) -> int:
        return self.services["billing_repository"].add_next_step_event(
            {
                "parent_event_id": parent_event_id,
                "organization_id": organization_id or self.organization_id,
                "target_type": target_type,
                "target_id": target_id,
                "related_issue_key": f"issue-{title}",
                "step_type": "call",
                "event_action": event_action,
                "title": title,
                "note_text": "PRIVATE BILLING NOTE",
                "planned_for": planned_for,
                "created_by_user_id": int(self.users["organization_admin"]["user_id"]),
            }
        )

    def _seed_task_scenarios(self) -> dict[str, int]:
        operator_id = int(self.users["operator"]["user_id"])
        admin_id = int(self.users["organization_admin"]["user_id"])
        coordinator_id = int(self.users["coordinator"]["user_id"])
        ids = {
            "owner_overdue": self._insert_task(
                "Owner overdue", owner_user_id=operator_id, due_at="2026-03-27T08:00"
            ),
            "boundary_overdue": self._insert_task(
                "Boundary 23:59", owner_user_id=operator_id, due_at="2026-03-28T23:59"
            ),
            "assignee_today": self._insert_task(
                "Assignee today", owner_user_id=admin_id, assigned_user_id=operator_id,
                due_at="2026-03-29T00:00"
            ),
            "explicit_today": self._insert_task(
                "Explicit today", owner_user_id=admin_id, visibility_scope="wybrane_osoby",
                visible_user_ids=(operator_id,), due_at="2026-03-29T09:00"
            ),
            "organization_today": self._insert_task(
                "Organization today", owner_user_id=admin_id, visibility_scope="organizacja",
                due_at="2026-03-29T10:00"
            ),
            "reminder_only": self._insert_task(
                "Reminder only", owner_user_id=operator_id, remind_at="2026-03-30T08:00"
            ),
            "upcoming": self._insert_task(
                "Upcoming", owner_user_id=operator_id, due_at="2026-03-31T08:00"
            ),
        }
        self._insert_task(
            "HIDDEN SECRET TITLE", owner_user_id=coordinator_id, due_at="2026-03-26T08:00"
        )
        self._insert_task(
            "OTHER ORG SECRET TITLE", organization_id=self.other_organization_id,
            owner_user_id=admin_id, due_at="2026-03-26T08:00"
        )
        self._insert_task("Closed", owner_user_id=operator_id, due_at="2026-03-28T08:00", status="zakonczone")
        self._insert_task("Undated", owner_user_id=operator_id)
        self._insert_task("Far future", owner_user_id=operator_id, due_at="2026-04-05T00:00")
        return ids

    def _seed_billing_scenarios(self) -> dict[str, int]:
        repository = self.services["billing_repository"]
        payer_id = repository.create_payer(
            {
                "organization_id": self.organization_id,
                "display_name": "PRIVATE PAYER NAME",
                "contact_phone": "+48111111111",
                "payment_identifier": "111111111",
            }
        )
        account_id = repository.create_bank_account(
            {
                "organization_id": self.organization_id,
                "account_name": "PRIVATE ACCOUNT",
                "iban": "PL00111111111111111111111111",
            }
        )
        payment_id = repository.create_transaction(
            {
                "organization_id": self.organization_id,
                "billing_bank_account_id": account_id,
                "booking_date": "2026-03-29",
                "amount": 987.65,
                "direction": "uznanie",
                "title": "PRIVATE PAYMENT METADATA",
                "transaction_hash": "today-payment-hash",
            }
        )
        ids = {
            "overdue": self._insert_billing_event(
                "Overdue payer step", target_type="payer", target_id=payer_id, planned_for="2026-03-27"
            ),
            "payment_today": self._insert_billing_event(
                "Payment today", target_type="payment", target_id=payment_id, planned_for=REFERENCE_DATE
            ),
            "tie_one": self._insert_billing_event("Tie one", planned_for=REFERENCE_DATE),
            "tie_two": self._insert_billing_event("Tie two", planned_for=REFERENCE_DATE),
        }
        snoozed_parent = self._insert_billing_event("Snoozed parent", planned_for="2026-03-28")
        ids["snoozed_leaf"] = self._insert_billing_event(
            "Snoozed leaf", event_action="snoozed", parent_event_id=snoozed_parent,
            planned_for=REFERENCE_DATE,
        )
        completed_parent = self._insert_billing_event("Completed parent", planned_for="2026-03-26")
        self._insert_billing_event(
            "Completed child", event_action="completed", parent_event_id=completed_parent,
            planned_for="2026-03-26",
        )
        self._insert_billing_event("Future", planned_for="2026-03-30")
        self._insert_billing_event("No date", planned_for=None)
        self._insert_billing_event(
            "OTHER BILLING SECRET", organization_id=self.other_organization_id, planned_for="2026-03-20"
        )
        return ids

    @staticmethod
    def _domain_snapshot(*, include_sessions: bool = True) -> dict[str, tuple[int, str]]:
        snapshot: dict[str, tuple[int, str]] = {}
        with get_connection() as connection:
            for spec in MIGRATION_MANIFEST:
                if not include_sessions and spec.source_table == "user_sessions":
                    continue
                rows = [dict(row) for row in connection.execute(
                    f'SELECT * FROM "{spec.source_table}" ORDER BY 1'
                ).fetchall()]
                canonical = json.dumps(rows, sort_keys=True, separators=(",", ":"), default=str)
                snapshot[spec.source_table] = (
                    len(rows),
                    hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
                )
        return snapshot

    @staticmethod
    def _select_count(callback):
        statements: list[str] = []
        open_connection = db_module._open_sqlite_connection

        def traced_connection():
            connection = open_connection()
            connection.raw_connection.set_trace_callback(statements.append)
            return connection

        with patch.object(db_module, "_open_sqlite_connection", side_effect=traced_connection):
            result = callback()
        count = sum(
            1 for statement in statements
            if statement.lstrip().upper().startswith(("SELECT", "WITH"))
        )
        return result, count

    @staticmethod
    def _captured_selects(callback):
        statements: list[str] = []
        open_connection = db_module._open_sqlite_connection

        def traced_connection():
            connection = open_connection()
            connection.raw_connection.set_trace_callback(statements.append)
            return connection

        with patch.object(db_module, "_open_sqlite_connection", side_effect=traced_connection):
            result = callback()
        selects = [
            statement for statement in statements
            if statement.lstrip().upper().startswith(("SELECT", "WITH"))
        ]
        return result, selects

    def test_tasks_today_contract_acl_order_limit_counts_privacy_and_read_only(self) -> None:
        ids = self._seed_task_scenarios()
        operator = self.users["operator"]
        before = self._domain_snapshot()
        result, query_count = self._select_count(
            lambda: self.services["task_service"].get_today_preview(
                organization_id=self.organization_id,
                viewer_user=operator,
                as_of=REFERENCE_NOW,
            )
        )
        self.assertEqual(query_count, 2)
        self.assertEqual(result["counts"], {"overdue": 2, "today": 3, "upcoming": 2})
        self.assertEqual(len(result["items"]), 5)
        self.assertEqual(
            [item["task_id"] for item in result["items"]],
            [
                ids["owner_overdue"], ids["boundary_overdue"], ids["assignee_today"],
                ids["explicit_today"], ids["organization_today"],
            ],
        )
        self.assertEqual([item["bucket"] for item in result["items"]], ["overdue", "overdue", "today", "today", "today"])
        serialized = json.dumps(result, ensure_ascii=False)
        self.assertNotIn("HIDDEN SECRET TITLE", serialized)
        self.assertNotIn("OTHER ORG SECRET TITLE", serialized)
        self.assertNotIn("PRIVATE DESCRIPTION", serialized)
        self.assertEqual(set(result["items"][0]), {"task_id", "title", "due_at", "bucket", "details_url"})
        self.assertEqual(before, self._domain_snapshot())

        limited_one, count_one = self._select_count(
            lambda: self.services["task_service"].get_today_preview(
                organization_id=self.organization_id, viewer_user=operator, as_of=REFERENCE_NOW, limit=1
            )
        )
        self.assertEqual((len(limited_one["items"]), count_one), (1, 2))
        self.assertEqual(limited_one["counts"], result["counts"])

    def test_tasks_today_boundaries_reminder_only_and_stable_tie(self) -> None:
        operator = self.users["operator"]
        first = self._insert_task("Tie first", owner_user_id=int(operator["user_id"]), due_at="2026-03-30T00:00")
        second = self._insert_task("Tie second", owner_user_id=int(operator["user_id"]), due_at="2026-03-30T00:00")
        reminder = self._insert_task("Reminder only", owner_user_id=int(operator["user_id"]), remind_at="2026-03-29T00:00")
        self._insert_task("Undated", owner_user_id=int(operator["user_id"]))
        result = self.services["task_service"].get_today_preview(
            organization_id=self.organization_id, viewer_user=operator, as_of=REFERENCE_NOW
        )
        self.assertEqual(result["counts"], {"overdue": 0, "today": 1, "upcoming": 2})
        self.assertEqual([item["task_id"] for item in result["items"]], [reminder, first, second])
        self.assertIsNone(result["items"][0]["due_at"])

    def test_tasks_today_http_capabilities_cross_org_and_session_only_touch(self) -> None:
        self._seed_task_scenarios()
        expected = {
            "system_owner": 200,
            "organization_admin": 200,
            "coordinator": 200,
            "operator": 200,
            "guest": 403,
        }
        for role, expected_status in expected.items():
            response, payload = self._request(
                "GET",
                f"/api/dashboard/today/tasks?organization_id={self.organization_id}",
                headers={"Cookie": self._cookie(role)},
            )
            self.assertEqual(response.status, expected_status, (role, payload.decode()))
        operator_cookie = self._cookie("operator")
        before = self._domain_snapshot(include_sessions=False)
        response, payload = self._request(
            "GET",
            f"/api/dashboard/today/tasks?organization_id={self.other_organization_id}",
            headers={"Cookie": operator_cookie},
        )
        self.assertEqual(response.status, 200, payload.decode())
        self.assertNotIn("OTHER ORG SECRET TITLE", payload.decode())
        self.assertEqual(before, self._domain_snapshot(include_sessions=False))

    def test_billing_today_contract_active_leaf_order_counts_privacy_and_no_n_plus_one(self) -> None:
        ids = self._seed_billing_scenarios()
        service = self.services["billing_service"]
        before = self._domain_snapshot()
        result, query_count = self._select_count(
            lambda: service.get_today_billing_preview(
                organization_id=self.organization_id, as_of_date=REFERENCE_DATE
            )
        )
        self.assertEqual(query_count, 3)
        self.assertEqual((result["overdue_count"], result["due_today_count"]), (1, 4))
        self.assertEqual(len(result["items"]), 3)
        self.assertEqual(
            [item["billing_next_step_event_id"] for item in result["items"]],
            [ids["overdue"], ids["payment_today"], ids["tie_one"]],
        )
        self.assertEqual([item["bucket"] for item in result["items"]], ["overdue", "today", "today"])
        self.assertEqual(set(result["items"][0]), {
            "billing_next_step_event_id", "title", "planned_for", "bucket", "details_url"
        })
        serialized = json.dumps(result, ensure_ascii=False).lower()
        for forbidden in ("987.65", "private account", "private payer", "payment metadata", "billing note", "other billing secret"):
            self.assertNotIn(forbidden, serialized)
        self.assertEqual(before, self._domain_snapshot())

        small, small_queries = self._select_count(
            lambda: service.get_today_billing_preview(
                organization_id=self.organization_id, as_of_date=REFERENCE_DATE, limit=1
            )
        )
        self.assertEqual((len(small["items"]), small_queries), (1, 3))
        attention_small, attention_small_queries = self._select_count(
            lambda: service.get_next_step_attention(
                organization_id=self.organization_id, as_of_date=REFERENCE_DATE, limit=1
            )
        )
        attention_full, attention_full_queries = self._select_count(
            lambda: service.get_next_step_attention(
                organization_id=self.organization_id, as_of_date=REFERENCE_DATE, limit=100
            )
        )
        self.assertEqual((attention_small_queries, attention_full_queries), (2, 2))
        self.assertEqual(len(attention_small["candidates"]), 1)
        self.assertEqual(len(attention_full["candidates"]), 5)

    def test_billing_today_http_capabilities_cross_org_and_read_only(self) -> None:
        self._seed_billing_scenarios()
        expected = {
            "system_owner": 200,
            "organization_admin": 200,
            "coordinator": 403,
            "operator": 403,
            "guest": 403,
        }
        for role, expected_status in expected.items():
            response, payload = self._request(
                "GET",
                f"/api/dashboard/today/billing?organization_id={self.organization_id}",
                headers={"Cookie": self._cookie(role)},
            )
            self.assertEqual(response.status, expected_status, (role, payload.decode()))
        admin_cookie = self._cookie("organization_admin")
        before = self._domain_snapshot(include_sessions=False)
        response, payload = self._request(
            "GET",
            f"/api/dashboard/today/billing?organization_id={self.other_organization_id}",
            headers={"Cookie": admin_cookie},
        )
        self.assertEqual(response.status, 200, payload.decode())
        self.assertNotIn("OTHER BILLING SECRET", payload.decode())
        self.assertEqual(before, self._domain_snapshot(include_sessions=False))

    def test_large_fixture_query_plans_and_fresh_schema(self) -> None:
        operator = self.users["operator"]
        operator_id = int(operator["user_id"])
        task_rows = []
        for index in range(2000):
            status = "zakonczone" if index % 19 == 0 else "nowe"
            due_at = None if index % 17 == 0 else (
                "2026-03-28T08:00" if index % 4 == 0 else
                "2026-03-29T08:00" if index % 4 == 1 else
                "2026-03-31T08:00" if index % 4 == 2 else
                "2026-04-20T08:00"
            )
            task_rows.append((
                self.organization_id, operator_id, f"Synthetic task {index}", status,
                due_at, operator_id, f"2026-03-01T10:{index % 60:02d}:00+00:00",
            ))
        event_rows = []
        for index in range(2000):
            action = "completed" if index % 23 == 0 else "planned"
            planned_for = None if index % 17 == 0 else (
                "2026-03-28" if index % 4 == 0 else
                "2026-03-29" if index % 4 == 1 else
                "2026-03-30" if index % 4 == 2 else
                "2026-04-20"
            )
            event_rows.append((
                self.organization_id, f"bulk-{index}", action, f"Synthetic billing {index}",
                planned_for, int(self.users["organization_admin"]["user_id"]),
                f"2026-03-01T10:{index % 60:02d}:00+00:00",
            ))
        with get_connection() as connection:
            connection.raw_connection.executemany(
                """
                INSERT INTO tasks (
                    organization_id, task_type, visibility_scope, owner_user_id, title, status,
                    priority, due_at, recurrence_pattern, recurrence_interval, created_by_user_id,
                    created_at, updated_at
                ) VALUES (?, 'zadanie', 'prywatne', ?, ?, ?, 'normalny', ?, 'brak', 1, ?, ?, ?)
                """,
                [row + (row[-1],) for row in task_rows],
            )
            connection.raw_connection.executemany(
                """
                INSERT INTO billing_next_step_events (
                    organization_id, target_type, related_issue_key, step_type, event_action,
                    title, planned_for, created_by_user_id, created_at
                ) VALUES (?, 'work_queue_issue', ?, 'call', ?, ?, ?, ?, ?)
                """,
                event_rows,
            )

        _, task_selects = self._captured_selects(
            lambda: self.services["task_service"].get_today_preview(
                organization_id=self.organization_id, viewer_user=operator, as_of=REFERENCE_NOW
            )
        )
        _, billing_selects = self._captured_selects(
            lambda: self.services["billing_service"].get_today_billing_preview(
                organization_id=self.organization_id, as_of_date=REFERENCE_DATE
            )
        )
        task_preview_sql = next(sql for sql in task_selects if "WITH eligible AS" in sql and "LIMIT" in sql)
        billing_preview_sql = next(sql for sql in billing_selects if "LEFT JOIN billing_payers payer" in sql)
        with get_connection() as connection:
            task_plan = [dict(row) for row in connection.execute("EXPLAIN QUERY PLAN " + task_preview_sql).fetchall()]
            billing_plan = [dict(row) for row in connection.execute("EXPLAIN QUERY PLAN " + billing_preview_sql).fetchall()]
            table_count = int(connection.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            ).fetchone()[0])
            quick_check = connection.execute("PRAGMA quick_check").fetchone()[0]
        task_details = "\n".join(str(row["detail"]) for row in task_plan)
        billing_details = "\n".join(str(row["detail"]) for row in billing_plan)
        self.assertIn("idx_tasks_organization_id", task_details)
        self.assertIn("idx_task_visibility_users_unique", task_details)
        self.assertIn("idx_billing_next_step_events_org", billing_details)
        self.assertEqual(table_count, 78)
        self.assertEqual(quick_check, "ok")
        print(json.dumps({
            "tasks_preview_queries": 1,
            "tasks_counts_queries": 1,
            "billing_preview_queries": 1,
            "billing_counts_queries": 1,
            "tasks_explain": task_plan,
            "billing_explain": billing_plan,
            "tables": table_count,
            "quick_check": quick_check,
        }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    import unittest

    unittest.main()
