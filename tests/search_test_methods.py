from __future__ import annotations

from app.domain.constants import MANAGER_ASSISTANT_MODULE

from tests.search_test_support import SearchServiceTestCase


class SearchServiceTests(SearchServiceTestCase):
    def test_org_admin_search_returns_admin_module_and_record_groups(self) -> None:
        casi = self.organization_repository.get_by_slug("casi")
        self.assertIsNotNone(casi)
        assert casi is not None
        organization_id = int(casi["organization_id"])
        actor_user = self.users_by_login["casi_admin"]

        module_result = self.search_service.search(
            "uzytkownicy",
            actor_user=actor_user,
            organization_id=organization_id,
        )
        self.assertTrue(any(item["view"] == "users" and item["category"] == "Modul" for item in module_result["modules"]))

        record_result = self.search_service.search(
            "FV/CASI/17/04/2026",
            actor_user=actor_user,
            organization_id=organization_id,
        )
        invoice_items = [
            item
            for group in record_result["groups"]
            if group["key"] == "invoices"
            for item in group["items"]
        ]
        self.assertTrue(invoice_items)
        self.assertTrue(any("FV/CASI/17/04/2026" in item["title"] for item in invoice_items))
        self.assertTrue(all(item["category"] == "Faktury" for item in invoice_items))
        self.assertEqual(record_result["scope_label"], "CASI")

    def test_operator_search_respects_private_tasks_and_admin_boundaries(self) -> None:
        casi = self.organization_repository.get_by_slug("casi")
        self.assertIsNotNone(casi)
        assert casi is not None
        organization_id = int(casi["organization_id"])
        owner_user = self.users_by_login["casi_ola"]
        admin_user = self.users_by_login["casi_admin"]

        owner_result = self.search_service.search(
            "Przygotowac onboarding operatora CASI",
            actor_user=owner_user,
            organization_id=organization_id,
        )
        owner_task_titles = [
            item["title"]
            for group in owner_result["groups"]
            if group["key"] == "tasks"
            for item in group["items"]
        ]
        self.assertIn("Przygotowac onboarding operatora CASI", owner_task_titles)
        self.assertFalse(any(item["view"] == "tasks" for item in owner_result["modules"]))

        admin_result = self.search_service.search(
            "Przygotowac onboarding operatora CASI",
            actor_user=admin_user,
            organization_id=organization_id,
        )
        admin_task_titles = [
            item["title"]
            for group in admin_result["groups"]
            if group["key"] == "tasks"
            for item in group["items"]
        ]
        self.assertNotIn("Przygotowac onboarding operatora CASI", admin_task_titles)

        operator_admin_query = self.search_service.search(
            "uzytkownicy",
            actor_user=owner_user,
            organization_id=organization_id,
        )
        self.assertFalse(any(item["view"] == "users" for item in operator_admin_query["modules"]))
        self.assertFalse(any(group["key"] == "users" for group in operator_admin_query["groups"]))

    def test_tasks_module_card_requires_enabled_org_module(self) -> None:
        admin = self.users_by_login["admin"]
        organization = self.services["organization_service"].create_organization(
            {
                "name": "Klient Bez Task Module",
                "slug": "klient-bez-task-module",
                "is_active": 1,
            },
            actor_user=admin,
            actor_login="admin",
        )
        actor_user = self.auth_service.create_user(
            {
                "login": "no-module-admin",
                "display_name": "No Module Admin",
                "password": "1234",
                "role": "organization_admin",
                "organization_id": organization["organization_id"],
                "is_active": 1,
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )

        without_module = self.search_service.search(
            "zadania",
            actor_user=actor_user,
            organization_id=int(organization["organization_id"]),
        )
        self.assertFalse(any(item["view"] == "tasks" for item in without_module["modules"]))
        self.assertFalse(any(group["key"] == "tasks" for group in without_module["groups"]))

        self.services["organization_repository"].replace_enabled_modules(
            int(organization["organization_id"]),
            [MANAGER_ASSISTANT_MODULE],
            enabled_by_user_id=int(admin["user_id"]),
        )
        actor_user = self.auth_service.list_users(admin, requested_organization_id=int(organization["organization_id"]))[0]
        with_module = self.search_service.search(
            "zadania",
            actor_user=actor_user,
            organization_id=int(organization["organization_id"]),
        )
        self.assertTrue(any(item["view"] == "tasks" for item in with_module["modules"]))

    def test_descriptive_invoice_search_matches_april_invoice(self) -> None:
        casi = self.organization_repository.get_by_slug("casi")
        self.assertIsNotNone(casi)
        assert casi is not None
        organization_id = int(casi["organization_id"])
        actor_user = self.users_by_login["casi_admin"]

        result = self.search_service.search(
            "faktura casi z kwietnia",
            actor_user=actor_user,
            organization_id=organization_id,
        )

        invoice_items = [
            item
            for group in result["groups"]
            if group["key"] == "invoices"
            for item in group["items"]
        ]
        self.assertTrue(invoice_items)
        self.assertTrue(
            any(
                "FV/CASI/24/04/2026" in item["title"] or "FV/CASI/17/04/2026" in item["title"]
                for item in invoice_items
            )
        )

    def test_descriptive_knowledge_search_returns_authorized_document(self) -> None:
        casi = self.organization_repository.get_by_slug("casi")
        self.assertIsNotNone(casi)
        assert casi is not None
        organization_id = int(casi["organization_id"])
        actor_user = self.users_by_login["casi_admin"]

        result = self.search_service.search(
            "dostepy onboarding casi",
            actor_user=actor_user,
            organization_id=organization_id,
        )

        knowledge_items = [
            item
            for group in result["groups"]
            if group["key"] == "knowledge_documents"
            for item in group["items"]
        ]
        self.assertTrue(knowledge_items)
        self.assertTrue(any("Dostepy i onboarding CASI" in item["title"] for item in knowledge_items))
        self.assertTrue(all(item["category"] == "Dokumenty firmowe" for item in knowledge_items))

    def test_descriptive_billing_search_matches_account_and_reference(self) -> None:
        robotyka = self.organization_repository.get_by_slug("misja-robotyka")
        self.assertIsNotNone(robotyka)
        assert robotyka is not None
        organization_id = int(robotyka["organization_id"])
        actor_user = self.users_by_login["robotyka_admin"]

        account_result = self.search_service.search(
            "rachunek iban robotyka",
            actor_user=actor_user,
            organization_id=organization_id,
        )
        account_items = [
            item
            for group in account_result["groups"]
            if group["key"] == "billing_bank_accounts"
            for item in group["items"]
        ]
        self.assertTrue(account_items)
        self.assertTrue(any("Wplaty" in item["title"] for item in account_items))

        transaction_result = self.search_service.search(
            "przelew mr demo 010",
            actor_user=actor_user,
            organization_id=organization_id,
        )
        transaction_items = [
            item
            for group in transaction_result["groups"]
            if group["key"] == "billing_transactions"
            for item in group["items"]
        ]
        self.assertTrue(transaction_items)
        self.assertTrue(any("MR-DEMO-010" in item["title"] for item in transaction_items))
