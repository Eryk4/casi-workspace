from __future__ import annotations

import shutil
import unittest

from app.bootstrap import build_services
from app.config import KNOWLEDGE_DIR
from app.db import reset_database
from app.demo_seed import SEED_INVOICES, seed_demo_data


class DemoSeedTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        shutil.rmtree(KNOWLEDGE_DIR, ignore_errors=True)
        KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
        self.services = build_services()
        self.auth_service = self.services["auth_service"]
        self.invoice_service = self.services["invoice_service"]
        self.invoice_repository = self.services["invoice_repository"]
        self.task_service = self.services["task_service"]
        self.billing_service = self.services["billing_service"]
        self.calendar_service = self.services["calendar_service"]
        self.knowledge_service = self.services["knowledge_service"]
        self.work_item_service = self.services["work_item_service"]
        self.dashboard_service = self.services["dashboard_service"]
        self.organization_repository = self.services["organization_repository"]

    def test_seed_demo_data_creates_sample_organizations_and_users(self) -> None:
        self.auth_service.ensure_default_admin()

        seed_demo_data(
            self.invoice_service,
            self.invoice_repository,
            task_service=self.task_service,
            auth_service=self.auth_service,
            billing_service=self.billing_service,
            knowledge_service=self.knowledge_service,
            calendar_service=self.calendar_service,
            work_item_service=self.work_item_service,
        )

        organization_names = {item["name"] for item in self.organization_repository.list_organizations()}
        self.assertIn("CASI", organization_names)
        self.assertIn("Misja Robotyka", organization_names)
        self.assertIn("Biuro Rachunkowe Alfa", organization_names)
        self.assertIn("Klient Archiwalny Demo", organization_names)

        user_logins = {item["login"] for item in self.auth_service.list_users()}
        self.assertIn("demo_operator", user_logins)
        self.assertIn("demo_gosc", user_logins)
        self.assertIn("casi_admin", user_logins)
        self.assertIn("robotyka_marek", user_logins)
        self.assertIn("alfa_ania", user_logins)

        robotyka = self.organization_repository.get_by_slug("misja-robotyka")
        self.assertIsNotNone(robotyka)
        robotyka_id = int(robotyka["organization_id"])

        model_names = {item["name"] for item in self.billing_service.list_models(organization_id=robotyka_id)}
        self.assertGreaterEqual(len(model_names), 5)
        self.assertIn("26/27 Poniedzialek", model_names)
        self.assertIn("26/27 Wtorek", model_names)
        self.assertIn("26/27 Piatek", model_names)
        self.assertIn("26/27 Sroda Semestr", model_names)

        schools = self.billing_service.list_schools(organization_id=robotyka_id)
        self.assertGreaterEqual(len(schools), 4)
        self.assertTrue(any(item["short_name"] == "NSP ROBOTIK" for item in schools))

        payers = self.billing_service.list_payers(organization_id=robotyka_id)
        self.assertGreaterEqual(len(payers), 7)

        student_names = {item["full_name"] for item in self.billing_service.list_students(organization_id=robotyka_id)}
        self.assertGreaterEqual(len(student_names), 11)
        self.assertIn("Lena Kruk", student_names)
        self.assertIn("Maja Kruk", student_names)
        self.assertIn("Igor Nowak", student_names)
        self.assertIn("Milosz Wisniewski", student_names)
        self.assertIn("Hanna Dabrowska", student_names)
        self.assertIn("Tymon Lewandowski", student_names)

        charges = self.billing_service.list_charges(organization_id=robotyka_id, limit=100)
        self.assertGreaterEqual(len(charges), 20)
        self.assertTrue(any(item["period_label"] == "Pazdziernik 2026" for item in charges))
        self.assertTrue(any(item["period_label"] == "Semestr zimowy 2026/2027" for item in charges))
        bank_accounts = self.billing_service.list_bank_accounts(organization_id=robotyka_id)
        self.assertGreaterEqual(len(bank_accounts), 2)
        transactions = self.billing_service.list_transactions(organization_id=robotyka_id, limit=100)
        self.assertGreaterEqual(len(transactions), 10)
        self.assertTrue(any(item["reference"] == "MR-DEMO-010" for item in transactions))
        balances = self.services["billing_ledger_service"].list_balances(organization_id=robotyka_id)
        balances_by_name = {item["display_name"]: item for item in balances}
        self.assertTrue(any(float(item.get("balance_due") or 0) < 0 for item in balances))
        self.assertTrue(any(float(item.get("balance_due") or 0) > 0 for item in balances))
        self.assertAlmostEqual(float(balances_by_name["Rodzina Kruk"].get("balance_due") or 0), -30.0)
        self.assertAlmostEqual(float(balances_by_name["Rodzina Zielinskich"].get("balance_due") or 0), 200.0)
        self.assertLess(abs(float(balances_by_name["Rodzina Kruk"].get("balance_due") or 0)), 1000)
        self.assertLess(abs(float(balances_by_name["Rodzina Zielinskich"].get("balance_due") or 0)), 1000)
        self.assertTrue(
            any(
                item.get("display_name") == "Rodzina Lewandowskich"
                and float(item.get("balance_due") or 0) > 0
                for item in balances
            )
        )

        users_by_login = {item["login"]: item for item in self.auth_service.list_users()}
        admin_calendars = self.calendar_service.list_user_calendars(users_by_login["admin"])
        self.assertGreaterEqual(len(admin_calendars), 3)
        self.assertTrue(any(item["display_name"] == "Kalendarz zarzadczy firmy" for item in admin_calendars))
        self.assertTrue(any(item["display_name"] == "Prezentacje produktu" for item in admin_calendars))
        self.assertTrue(any(item["display_name"] == "Sprawy prywatne i wyjazdy" for item in admin_calendars))
        casi_admin_calendars = self.calendar_service.list_user_calendars(users_by_login["casi_admin"])
        self.assertGreaterEqual(len(casi_admin_calendars), 2)
        self.assertTrue(any(item["display_name"] == "CASI - rekrutacje i eventy" for item in casi_admin_calendars))
        robotyka_calendars = self.calendar_service.list_user_calendars(users_by_login["robotyka_admin"])
        self.assertTrue(any(item["display_name"] == "Robotyka - grafik instruktorow" for item in robotyka_calendars))
        self.assertTrue(any(item["display_name"] == "Robotyka - archiwum" and not item["is_active"] for item in robotyka_calendars))
        alfa_admin_calendars = self.calendar_service.list_user_calendars(users_by_login["alfa_admin"])
        self.assertGreaterEqual(len(alfa_admin_calendars), 2)
        self.assertTrue(any(item["display_name"] == "Biuro Alfa - archiwum klientow" and not item["is_active"] for item in alfa_admin_calendars))

        default_org = self.organization_repository.ensure_default_organization()
        self.assertIsNotNone(default_org)
        self.assertEqual(default_org["slug"], "casi")
        self.assertEqual(default_org["name"], "CASI")
        self.assertEqual(default_org["email_inbox_address"], "faktury@casi24.com")
        self.assertIn("brak nowych", str(default_org["email_last_check_status"]).lower())
        default_invoices = self.invoice_service.list_invoices({}, organization_id=int(default_org["organization_id"]))
        self.assertGreaterEqual(len(default_invoices), 8)
        casi = default_org
        casi_invoices = self.invoice_service.list_invoices({}, organization_id=int(casi["organization_id"]))
        self.assertGreaterEqual(len(casi_invoices), 5)
        self.assertTrue(any(item["status"] == "odrzucona" for item in casi_invoices))
        self.assertTrue(any(item["status"] == "weryfikacja" for item in casi_invoices))
        self.assertTrue(any(item["status"] == "nowa" for item in casi_invoices))

        robotyka_invoices = self.invoice_service.list_invoices({}, organization_id=int(robotyka["organization_id"]))
        self.assertEqual(robotyka["email_integration_enabled"], 1)
        self.assertIn("zaimportowano", str(robotyka["email_last_check_status"]).lower())
        self.assertGreaterEqual(len(robotyka_invoices), 3)
        self.assertTrue(any(item["status"] == "zaksiegowana" for item in robotyka_invoices))

        alfa = self.organization_repository.get_by_slug("biuro-rachunkowe-alfa")
        self.assertIsNotNone(alfa)
        self.assertEqual(alfa["email_inbox_address"], "klienci@biuroalfa.pl")
        self.assertIn("imap", str(alfa["email_last_connection_status"]).lower())
        alfa_invoices = self.invoice_service.list_invoices({}, organization_id=int(alfa["organization_id"]))
        self.assertGreaterEqual(len(alfa_invoices), 4)
        self.assertTrue(any(item["status"] == "zaksiegowana" for item in alfa_invoices))

        archived = self.organization_repository.get_by_slug("klient-archiwalny-demo")
        self.assertIsNotNone(archived)
        self.assertEqual(int(archived["is_active"]), 0)
        self.assertEqual(int(archived["email_integration_enabled"]), 0)
        self.assertEqual(archived["email_inbox_address"], "archiwum@klient-demo.pl")

        default_contractors = self.invoice_service.list_contractors(organization_id=int(default_org["organization_id"]))
        self.assertTrue(any(int(item["invoice_count"] or 0) > 1 for item in default_contractors))
        self.assertTrue(any(int(item["is_new"] or 0) == 1 for item in default_contractors))
        casi_contractors = self.invoice_service.list_contractors(organization_id=int(casi["organization_id"]))
        self.assertTrue(any(int(item["invoice_count"] or 0) > 1 for item in casi_contractors))
        robotyka_contractors = self.invoice_service.list_contractors(organization_id=int(robotyka["organization_id"]))
        self.assertTrue(any(int(item["invoice_count"] or 0) > 1 for item in robotyka_contractors))
        alfa_contractors = self.invoice_service.list_contractors(organization_id=int(alfa["organization_id"]))
        self.assertTrue(any(int(item["invoice_count"] or 0) > 1 for item in alfa_contractors))
        alfa_docs = self.knowledge_service.list_documents(organization_id=int(alfa["organization_id"]))["documents"]
        self.assertTrue(alfa_docs)
        self.assertTrue(any(item["source_type"] == "folder_sync" for item in alfa_docs))
        self.assertTrue(any(item["library_path"] for item in alfa_docs))
        casi_docs = self.knowledge_service.list_documents(organization_id=int(casi["organization_id"]))["documents"]
        self.assertTrue(any(item["is_downloadable"] and not item["use_in_assistant"] for item in casi_docs))
        self.assertTrue(any(int(item["current_version_number"] or 0) >= 2 for item in casi_docs))
        alfa_answer = self.knowledge_service.answer_question(
            "Kto zatwierdza delegacje?",
            organization_id=int(alfa["organization_id"]),
        )
        self.assertIn("koordynator organizacji", alfa_answer["answer"])

        default_tasks = self.task_service.list_tasks(
            organization_id=int(default_org["organization_id"]),
            viewer_user=users_by_login["admin"],
        )
        self.assertGreaterEqual(len(default_tasks), 5)
        casi_tasks = self.task_service.list_tasks(
            organization_id=int(casi["organization_id"]),
            viewer_user=users_by_login["casi_admin"],
        )
        self.assertGreaterEqual(len(casi_tasks), 3)
        self.assertTrue(any(item["title"] == "Przejrzec delegacje krajowe CASI" for item in casi_tasks))
        self.assertTrue(any(item["title"] == "Spotkanie operacyjne zespolu CASI" for item in casi_tasks))
        self.assertTrue(any(item["title"] == "Zweryfikowac harmonogram rekrutacji CASI" for item in casi_tasks))
        casi_ola_tasks = self.task_service.list_tasks(
            organization_id=int(casi["organization_id"]),
            viewer_user=users_by_login["casi_ola"],
        )
        self.assertGreaterEqual(len(casi_ola_tasks), 4)
        robotyka_tasks = self.task_service.list_tasks(
            organization_id=int(robotyka["organization_id"]),
            viewer_user=users_by_login["robotyka_admin"],
        )
        self.assertGreaterEqual(len(robotyka_tasks), 4)
        self.assertTrue(any(item["status"] == "zakonczone" for item in robotyka_tasks))
        alfa_tasks = self.task_service.list_tasks(
            organization_id=int(alfa["organization_id"]),
            viewer_user=users_by_login["alfa_admin"],
        )
        self.assertGreaterEqual(len(alfa_tasks), 4)
        self.assertTrue(any(item["title"] == "Przygotowac zestawienie terminow VAT" for item in alfa_tasks))
        self.assertTrue(any(item["title"] == "Spotkanie statusowe z klientem premium" for item in alfa_tasks))

        casi_work_items = self.work_item_service.list_work_items(
            organization_id=int(casi["organization_id"]),
            limit=50,
        )
        self.assertGreaterEqual(len(casi_work_items), 2)
        self.assertTrue(
            any(item["title"] == "Uzupelnic opis faktury za hosting i monitoring" for item in casi_work_items)
        )
        self.assertTrue(any(item["title"] == "Sprawdzic aktualnosc procedury delegacji" for item in casi_work_items))
        casi_invoice_work_item = next(
            item for item in casi_work_items if item["title"] == "Uzupelnic opis faktury za hosting i monitoring"
        )
        casi_work_item_detail = self.work_item_service.get_work_item_detail(
            int(casi_invoice_work_item["work_item_id"]),
            organization_id=int(casi["organization_id"]),
        )
        self.assertIsNotNone(casi_work_item_detail)
        assert casi_work_item_detail is not None
        self.assertTrue(casi_work_item_detail["history"])
        casi_metadata = casi_work_item_detail["work_item"]["metadata"]
        self.assertTrue(casi_metadata.get("invoice_id"))
        self.assertTrue(casi_metadata.get("contractor_id"))
        self.assertTrue(casi_metadata.get("knowledge_document_ids"))

        robotyka_work_items = self.work_item_service.list_work_items(
            organization_id=int(robotyka["organization_id"]),
            limit=50,
        )
        self.assertGreaterEqual(len(robotyka_work_items), 2)
        self.assertTrue(any(item["title"] == "Wyjasnic platnosc za zajecia robotyki" for item in robotyka_work_items))
        self.assertTrue(
            any(item["title"] == "Potwierdzic zgody rodzicow na warsztaty sobotnie" for item in robotyka_work_items)
        )

        planner_snapshot = self.task_service.get_planner_snapshot(
            organization_id=int(default_org["organization_id"]),
            viewer_user=users_by_login["admin"],
        )
        self.assertGreater(planner_snapshot["counts"]["zalegle"], 0)
        self.assertGreater(planner_snapshot["counts"]["dzis"], 0)
        self.assertGreater(planner_snapshot["counts"]["jutro"], 0)
        self.assertGreater(planner_snapshot["counts"]["tydzien"], 0)

        dashboard_snapshot = self.dashboard_service.get_snapshot(
            organization_id=int(default_org["organization_id"]),
            viewer_user_id=int(users_by_login["admin"]["user_id"]),
        )
        self.assertGreater(dashboard_snapshot["cards"]["nowi_kontrahenci"], 0)
        self.assertGreater(dashboard_snapshot["cards"]["aktywne_przypomnienia"], 0)
        self.assertTrue(dashboard_snapshot["recent_events"])
        task_with_attachment = next(item for item in default_tasks if item["title"] == "Sprawdzic poranny przeglad operacyjny")
        detail = self.task_service.get_task_detail(
            int(task_with_attachment["task_id"]),
            organization_id=int(default_org["organization_id"]),
            viewer_user=users_by_login["admin"],
        )
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertTrue(detail["notes"])
        self.assertTrue(detail["attachments"])

        first_count = len(self.auth_service.list_users())
        first_student_count = len(self.billing_service.list_students(organization_id=robotyka_id))
        first_transaction_count = len(transactions)
        first_alfa_doc_count = len(alfa_docs)
        first_default_invoice_count = len(default_invoices)
        first_task_count = len(default_tasks)
        first_casi_work_item_count = len(casi_work_items)
        first_robotyka_work_item_count = len(robotyka_work_items)
        first_payment_match_count = len(
            self.services["billing_ledger_service"].list_payment_matches(
                organization_id=robotyka_id,
                limit=1000,
            )
        )
        first_balances_by_name = {
            item["display_name"]: item
            for item in self.services["billing_ledger_service"].list_balances(organization_id=robotyka_id)
        }
        seed_demo_data(
            self.invoice_service,
            self.invoice_repository,
            task_service=self.task_service,
            auth_service=self.auth_service,
            billing_service=self.billing_service,
            knowledge_service=self.knowledge_service,
            calendar_service=self.calendar_service,
            work_item_service=self.work_item_service,
        )
        self.assertEqual(len(self.auth_service.list_users()), first_count)
        self.assertEqual(len(self.billing_service.list_students(organization_id=robotyka_id)), first_student_count)
        self.assertEqual(
            len(self.billing_service.list_transactions(organization_id=robotyka_id, limit=100)),
            first_transaction_count,
        )
        alfa_docs_second = self.knowledge_service.list_documents(organization_id=int(alfa["organization_id"]))["documents"]
        self.assertEqual(len(alfa_docs_second), first_alfa_doc_count)
        self.assertEqual(
            len(self.invoice_service.list_invoices({}, organization_id=int(default_org["organization_id"]))),
            first_default_invoice_count,
        )
        self.assertEqual(
            len(
                self.task_service.list_tasks(
                    organization_id=int(default_org["organization_id"]),
                    viewer_user=users_by_login["admin"],
                )
            ),
            first_task_count,
        )
        self.assertEqual(
            len(self.work_item_service.list_work_items(organization_id=int(casi["organization_id"]), limit=50)),
            first_casi_work_item_count,
        )
        self.assertEqual(
            len(self.work_item_service.list_work_items(organization_id=int(robotyka["organization_id"]), limit=50)),
            first_robotyka_work_item_count,
        )
        self.assertEqual(
            len(
                self.services["billing_ledger_service"].list_payment_matches(
                    organization_id=robotyka_id,
                    limit=1000,
                )
            ),
            first_payment_match_count,
        )
        second_balances_by_name = {
            item["display_name"]: item
            for item in self.services["billing_ledger_service"].list_balances(organization_id=robotyka_id)
        }
        self.assertAlmostEqual(
            float(second_balances_by_name["Rodzina Kruk"].get("balance_due") or 0),
            float(first_balances_by_name["Rodzina Kruk"].get("balance_due") or 0),
        )
        self.assertAlmostEqual(
            float(second_balances_by_name["Rodzina Zielinskich"].get("balance_due") or 0),
            float(first_balances_by_name["Rodzina Zielinskich"].get("balance_due") or 0),
        )

    def test_seed_demo_data_adds_demo_users_even_when_invoices_already_exist(self) -> None:
        self.auth_service.ensure_default_admin()
        self.invoice_service.create_invoice(dict(SEED_INVOICES[0]), actor="unittest")

        seed_demo_data(
            self.invoice_service,
            self.invoice_repository,
            task_service=self.task_service,
            auth_service=self.auth_service,
            billing_service=self.billing_service,
            knowledge_service=self.knowledge_service,
            calendar_service=self.calendar_service,
            work_item_service=self.work_item_service,
        )

        self.assertGreater(self.invoice_repository.count_all(), 1)
        user_logins = {item["login"] for item in self.auth_service.list_users()}
        self.assertIn("casi_ola", user_logins)
        self.assertIn("alfa_admin", user_logins)

        robotyka = self.organization_repository.get_by_slug("misja-robotyka")
        self.assertIsNotNone(robotyka)
        charges = self.billing_service.list_charges(organization_id=int(robotyka["organization_id"]), limit=20)
        self.assertTrue(charges)
        knowledge_docs = self.knowledge_service.list_documents(organization_id=int(robotyka["organization_id"]))["documents"]
        self.assertTrue(knowledge_docs)
        robotyka_tasks = self.task_service.list_tasks(
            organization_id=int(robotyka["organization_id"]),
            viewer_user=next(item for item in self.auth_service.list_users() if item["login"] == "robotyka_admin"),
        )
        self.assertTrue(robotyka_tasks)
        robotyka_work_items = self.work_item_service.list_work_items(
            organization_id=int(robotyka["organization_id"]),
            limit=50,
        )
        self.assertTrue(robotyka_work_items)


if __name__ == "__main__":
    unittest.main()

