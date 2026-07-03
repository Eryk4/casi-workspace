from __future__ import annotations

from datetime import datetime, timedelta
import unittest

from app.bootstrap import build_services
from app.db import reset_database


class WorkItemServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        self.services["auth_service"].ensure_default_admin()
        self.admin = self.services["auth_service"].list_users()[0]
        self.organization = self.services["organization_service"].create_organization(
            {
                "name": "Organizacja Work Item",
                "slug": "organizacja-work-item",
                "is_active": 1,
            },
            actor_user=self.admin,
            actor_login="admin",
        )
        self.owner = self.services["auth_service"].create_user(
            {
                "login": "owner_work_item",
                "display_name": "Owner",
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
                "login": "assignee_work_item",
                "display_name": "Assignee",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": self.organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )
        self.work_item_service = self.services["work_item_service"]

    def test_create_update_and_close_work_item(self) -> None:
        created = self.work_item_service.create_work_item(
            {
                "title": "Zweryfikowac zgloszenie SLA",
                "description": "Pilne zgloszenie klienta.",
                "source_type": "support",
                "status": "nowe",
                "priority_level": "normalny",
                "due_at": "2099-04-10T10:00",
                "sla_deadline_at": "2099-04-10T09:00",
                "sla_warning_minutes": 90,
                "metadata": {"is_blocker": True},
            },
            actor_user=self.owner,
            actor="Owner",
            organization_id=self.organization["organization_id"],
        )
        self.assertEqual(created["title"], "Zweryfikowac zgloszenie SLA")
        self.assertEqual(created["source_type"], "support")
        self.assertGreater(float(created["priority_score"]), 0)

        assigned = self.work_item_service.assign_work_item(
            int(created["work_item_id"]),
            int(self.assignee["user_id"]),
            actor_user=self.owner,
            actor="Owner",
            organization_id=self.organization["organization_id"],
        )
        self.assertIsNotNone(assigned)
        assert assigned is not None
        self.assertEqual(int(assigned["assigned_user_id"]), int(self.assignee["user_id"]))

        snoozed = self.work_item_service.snooze_work_item(
            int(created["work_item_id"]),
            {"mode": "2h"},
            actor_user=self.owner,
            actor="Owner",
            organization_id=self.organization["organization_id"],
        )
        self.assertIsNotNone(snoozed)
        assert snoozed is not None
        self.assertEqual(snoozed["sla_stage"], "on_track")

        closed = self.work_item_service.close_work_item(
            int(created["work_item_id"]),
            {"reason": "Sprawa zostala domknieta."},
            actor_user=self.owner,
            actor="Owner",
            organization_id=self.organization["organization_id"],
        )
        self.assertIsNotNone(closed)
        assert closed is not None
        self.assertEqual(closed["status"], "zamkniete")
        self.assertEqual(closed["sla_stage"], "resolved")
        self.assertTrue(closed["resolved_at"])

        detail = self.work_item_service.get_work_item_detail(
            int(created["work_item_id"]),
            organization_id=self.organization["organization_id"],
        )
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertTrue(any(item["action_type"] == "work_item_created" for item in detail["history"]))
        self.assertTrue(any(item["action_type"] == "work_item_assigned" for item in detail["history"]))
        self.assertTrue(any(item["action_type"] == "work_item_closed" for item in detail["history"]))

    def test_reopen_and_bulk_apply_work_items(self) -> None:
        first = self.work_item_service.create_work_item(
            {
                "title": "Bulk item A",
                "source_type": "manual",
                "status": "nowe",
                "sla_deadline_at": "2099-04-10T09:00",
            },
            actor_user=self.owner,
            actor="Owner",
            organization_id=self.organization["organization_id"],
        )
        second = self.work_item_service.create_work_item(
            {
                "title": "Bulk item B",
                "source_type": "manual",
                "status": "w_toku",
                "sla_deadline_at": "2099-04-10T10:00",
            },
            actor_user=self.owner,
            actor="Owner",
            organization_id=self.organization["organization_id"],
        )

        bulk_assigned = self.work_item_service.bulk_apply(
            {
                "action": "assign",
                "work_item_ids": [first["work_item_id"], second["work_item_id"]],
                "assigned_user_id": self.assignee["user_id"],
            },
            actor_user=self.owner,
            actor="Owner",
            organization_id=self.organization["organization_id"],
        )
        self.assertEqual(bulk_assigned["updated"], 2)
        self.assertEqual(bulk_assigned["failed"], 0)

        closed = self.work_item_service.close_work_item(
            int(first["work_item_id"]),
            {"reason": "Domkniete przed testem reopen."},
            actor_user=self.owner,
            actor="Owner",
            organization_id=self.organization["organization_id"],
        )
        self.assertIsNotNone(closed)
        assert closed is not None
        self.assertEqual(closed["status"], "zamkniete")

        reopened = self.work_item_service.reopen_work_item(
            int(first["work_item_id"]),
            {"status": "w_toku", "reason": "Ponowne otwarcie."},
            actor_user=self.owner,
            actor="Owner",
            organization_id=self.organization["organization_id"],
        )
        self.assertIsNotNone(reopened)
        assert reopened is not None
        self.assertEqual(reopened["status"], "w_toku")
        self.assertFalse(reopened["is_closed"])

        summary = self.work_item_service.get_summary(organization_id=self.organization["organization_id"])
        self.assertIn("counts", summary)
        self.assertGreaterEqual(int(summary["counts"]["total"]), 2)
        self.assertIn("top_risk", summary)

    def test_sla_sweep_escalates_overdue_work_item(self) -> None:
        created = self.work_item_service.create_work_item(
            {
                "title": "Przekroczone SLA",
                "source_type": "manual",
                "status": "w_toku",
                "priority_level": "normalny",
                "sla_deadline_at": "2000-01-01T00:10",
                "sla_warning_minutes": 30,
            },
            actor_user=self.owner,
            actor="Owner",
            organization_id=self.organization["organization_id"],
        )
        self.assertIn(created["sla_stage"], {"breached", "on_track", "warning"})

        result = self.work_item_service.run_sla_sweep(
            organization_id=self.organization["organization_id"],
            actor="sla-test-worker",
            limit=20,
        )
        self.assertGreaterEqual(result["evaluated"], 1)
        self.assertEqual(result["escalated"], 1)

        detail = self.work_item_service.get_work_item_detail(
            int(created["work_item_id"]),
            organization_id=self.organization["organization_id"],
        )
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail["work_item"]["sla_stage"], "escalated")
        self.assertEqual(detail["work_item"]["priority_level"], "krytyczny")
        self.assertTrue(any(item["action_type"] == "work_item_sla_escalated" for item in detail["history"]))

    def test_work_items_are_scoped_by_organization(self) -> None:
        second_org = self.services["organization_service"].create_organization(
            {
                "name": "Organizacja B",
                "slug": "organizacja-b-work-item",
                "is_active": 1,
            },
            actor_user=self.admin,
            actor_login="admin",
        )
        created = self.work_item_service.create_work_item(
            {
                "title": "Pozycja tylko dla org A",
                "source_type": "manual",
                "status": "nowe",
            },
            actor_user=self.owner,
            actor="Owner",
            organization_id=self.organization["organization_id"],
        )

        detail_org_a = self.work_item_service.get_work_item_detail(
            int(created["work_item_id"]),
            organization_id=self.organization["organization_id"],
        )
        detail_org_b = self.work_item_service.get_work_item_detail(
            int(created["work_item_id"]),
            organization_id=second_org["organization_id"],
        )

        self.assertIsNotNone(detail_org_a)
        self.assertIsNone(detail_org_b)

    def test_sla_policy_workload_and_advanced_filters(self) -> None:
        policy_saved = self.work_item_service.update_sla_policy(
            {
                "auto_deadline_enabled": True,
                "default_warning_minutes": 30,
                "priority_targets_minutes": {
                    "normalny": 180,
                    "krytyczny": 45,
                },
            },
            actor_user=self.owner,
            actor="Owner",
            organization_id=self.organization["organization_id"],
        )
        self.assertEqual(int(policy_saved["policy"]["default_warning_minutes"]), 30)
        self.assertEqual(int(policy_saved["policy"]["priority_targets_minutes"]["krytyczny"]), 45)

        critical = self.work_item_service.create_work_item(
            {
                "title": "Krytyczny bez jawnego SLA",
                "priority_level": "krytyczny",
                "status": "nowe",
                "source_type": "manual",
            },
            actor_user=self.owner,
            actor="Owner",
            organization_id=self.organization["organization_id"],
        )
        self.assertTrue(str(critical.get("sla_deadline_at") or "").strip())
        self.assertEqual(int(critical.get("sla_warning_minutes") or 0), 30)
        now_local = datetime.now().replace(second=0, microsecond=0)
        critical_deadline = datetime.strptime(str(critical["sla_deadline_at"]), "%Y-%m-%dT%H:%M")
        self.assertGreaterEqual(critical_deadline, now_local)
        self.assertLessEqual(critical_deadline, now_local + timedelta(minutes=60))

        unassigned_overdue = self.work_item_service.create_work_item(
            {
                "title": "Nieprzypisane po terminie",
                "priority_level": "normalny",
                "status": "w_toku",
                "source_type": "manual",
                "due_at": "2000-01-01T00:01",
            },
            actor_user=self.owner,
            actor="Owner",
            organization_id=self.organization["organization_id"],
        )
        assigned_future = self.work_item_service.create_work_item(
            {
                "title": "Przypisane na przyszlosc",
                "priority_level": "normalny",
                "status": "w_toku",
                "source_type": "manual",
                "assigned_user_id": self.assignee["user_id"],
                "due_at": "2099-01-01T09:00",
            },
            actor_user=self.owner,
            actor="Owner",
            organization_id=self.organization["organization_id"],
        )

        unassigned_list = self.work_item_service.list_work_items(
            {"unassigned_only": "1"},
            organization_id=self.organization["organization_id"],
            limit=50,
        )
        self.assertTrue(unassigned_list)
        self.assertTrue(all(item.get("assigned_user_id") in {None, 0, "0"} for item in unassigned_list))
        self.assertTrue(any(int(item["work_item_id"]) == int(unassigned_overdue["work_item_id"]) for item in unassigned_list))

        overdue_due = self.work_item_service.list_work_items(
            {"due_overdue_only": "1"},
            organization_id=self.organization["organization_id"],
            limit=50,
        )
        self.assertTrue(any(int(item["work_item_id"]) == int(unassigned_overdue["work_item_id"]) for item in overdue_due))
        self.assertFalse(any(int(item["work_item_id"]) == int(assigned_future["work_item_id"]) for item in overdue_due))

        sorted_due = self.work_item_service.list_work_items(
            {"sort_by": "due_at", "sort_dir": "asc"},
            organization_id=self.organization["organization_id"],
            limit=50,
        )
        sorted_ids = [int(item["work_item_id"]) for item in sorted_due]
        self.assertLess(sorted_ids.index(int(unassigned_overdue["work_item_id"])), sorted_ids.index(int(assigned_future["work_item_id"])))

        workload = self.work_item_service.get_workload(
            organization_id=self.organization["organization_id"],
            limit=20,
        )
        self.assertGreaterEqual(int(workload["summary"]["open_items"]), 3)
        self.assertTrue(any(item["assigned_user_name"] == "Nieprzypisane" for item in workload["items"]))
        self.assertTrue(
            any(int(item.get("assigned_user_id") or 0) == int(self.assignee["user_id"]) for item in workload["items"])
        )


if __name__ == "__main__":
    unittest.main()
