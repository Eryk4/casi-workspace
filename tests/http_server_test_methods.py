from __future__ import annotations

import json
import uuid
from pathlib import Path
from unittest.mock import patch

from app.config import DOCUMENTS_DIR, KNOWLEDGE_DIR
from app.domain.constants import MANAGER_ASSISTANT_MODULE
from app.integrations.email_ingestion import EmailIngestionError

from tests.http_server_support import HttpServerTestCase


class HttpServerTestMethods(HttpServerTestCase):
    def test_root_is_public_and_serves_html(self) -> None:
        response, payload = self._request("GET", "/")
        self.assertEqual(response.status, 200)
        self.assertIn("text/html", response.getheader("Content-Type", ""))
        body = payload.decode("utf-8")
        self.assertIn("CASI Workspace", body)
        self.assertIn("login-form", body)
        self.assertIn("default-login-hint", body)
        self.assertIn("subtle-note hidden", body)

    def test_meta_exposes_storage_backend(self) -> None:
        response, payload = self._request("GET", "/api/meta")
        self.assertEqual(response.status, 200)
        meta = json.loads(payload.decode("utf-8"))
        self.assertEqual(meta["storage_backend"], "lokalny")
        self.assertIn("email_enabled", meta)
        self.assertIn(meta["email_mode"], {"imap", "not_configured"})
        self.assertEqual(meta["email_routing_mode"], "central_mailbox")
        self.assertIn("email_scheduler_status", meta)
        self.assertIn(meta["email_scheduler_status"]["mode"], {"automatic_interval", "manual_only"})
        self.assertIn("email_google_oauth_enabled", meta)
        self.assertIn("email_google_connection", meta)
        self.assertIn("ksef_enabled", meta)
        self.assertIn(meta["ksef_mode"], {"mvp_stub", "disabled"})
        self.assertIn("ksef_provider", meta)
        self.assertGreaterEqual(int(meta["ksef_fetch_limit"]), 1)
        self.assertIn(meta["ocr_mode"], {"tesseract", "fallback"})
        self.assertIn("ocr_enabled", meta)
        self.assertIn("workflow_states", meta)
        self.assertEqual(
            meta["workflow_states"],
            ["w_pracy", "gotowa_do_przekazania", "przekazana", "zamknieta"],
        )
        self.assertEqual(
            meta["knowledge_capabilities"],
            [
                "knowledge.read",
                "knowledge.download",
                "knowledge.upload",
                "knowledge.sync",
                "knowledge.manage",
                "knowledge.assistant_use",
            ],
        )
        self.assertIn("codziennie", meta["task_recurrence_patterns"])
        self.assertIn("moj_dzien", meta["task_focus_views"])
        self.assertIn("tylko_ten", meta["task_recurrence_edit_scopes"])

    def test_meta_exposes_environment_flags(self) -> None:
        with patch("app.api.http_server.test_imports_enabled", return_value=False), patch(
            "app.api.http_server.default_login_hint_enabled",
            return_value=False,
        ):
            response, payload = self._request("GET", "/api/meta")

        self.assertEqual(response.status, 200)
        meta = json.loads(payload.decode("utf-8"))
        self.assertFalse(meta["test_imports_enabled"])
        self.assertFalse(meta["default_login_hint_enabled"])

    def test_system_owner_can_save_system_communication_settings(self) -> None:
        cookie = self._login_default_admin()

        response, payload = self._request(
            "PATCH",
            "/api/system/communication-settings",
            body=json.dumps(
                {
                    "telegram": {
                        "bot_token": "telegram-token-1234",
                        "webhook_secret": "telegram-secret-5678",
                    },
                    "slack": {
                        "bot_token": "xoxb-slack-token-1234",
                        "signing_secret": "slack-signing-secret-5678",
                    },
                }
            ),
            headers={
                "Cookie": cookie,
                "Content-Type": "application/json",
                "Host": "workspace.local",
            },
        )

        self.assertEqual(response.status, 201, payload.decode("utf-8"))
        snapshot = json.loads(payload.decode("utf-8"))
        self.assertTrue(snapshot["telegram"]["enabled"])
        self.assertTrue(snapshot["slack"]["enabled"])
        self.assertEqual(snapshot["telegram"]["bot_token"]["source"], "panel")
        self.assertEqual(snapshot["slack"]["signing_secret"]["source"], "panel")
        self.assertIn("/api/telegram/webhook/telegram-secret-5678", snapshot["telegram"]["webhook_url"])
        self.assertEqual(snapshot["slack"]["webhook_url"], "http://workspace.local/api/slack/events")
        self.assertEqual(self.services["invoice_service"].telegram_adapter.bot_token, "telegram-token-1234")
        self.assertEqual(self.services["invoice_service"].slack_adapter.signing_secret, "slack-signing-secret-5678")

        response, payload = self._request("GET", "/api/meta", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        meta = json.loads(payload.decode("utf-8"))
        self.assertTrue(meta["telegram_enabled"])
        self.assertTrue(meta["slack_enabled"])

    def test_system_communication_settings_require_system_owner(self) -> None:
        owner = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {"name": "Klient Sekrety", "slug": "klient-sekrety", "is_active": 1},
            actor_user=owner,
            actor_login="admin",
        )
        self.services["auth_service"].create_user(
            {
                "login": "org_admin_settings",
                "display_name": "Org Admin Settings",
                "password": "OrgAdmin1234",
                "role": "organization_admin",
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=owner["user_id"],
            actor_user=owner,
        )
        cookie = self._login("org_admin_settings", "OrgAdmin1234")

        response, payload = self._request(
            "GET",
            "/api/system/communication-settings",
            headers={"Cookie": cookie},
        )

        self.assertEqual(response.status, 403)
        self.assertIn("Tylko Wlasciciel systemu", payload.decode("utf-8"))

    def test_email_center_requires_session(self) -> None:
        response, payload = self._request("GET", "/api/email-center")
        self.assertEqual(response.status, 401)
        self.assertIn("Brak aktywnej sesji.", payload.decode("utf-8"))

    def test_email_center_returns_snapshot_for_owner(self) -> None:
        cookie = self._login_default_admin()

        response, payload = self._request("GET", "/api/email-center?limit=5", headers={"Cookie": cookie})

        self.assertEqual(response.status, 200)
        snapshot = json.loads(payload.decode("utf-8"))
        self.assertIn("integration", snapshot)
        self.assertIn("scheduler", snapshot)
        self.assertIn("summary", snapshot)
        self.assertIn("runs", snapshot)
        self.assertIn("scope", snapshot)

    def test_integration_center_returns_nested_snapshot_for_owner(self) -> None:
        cookie = self._login_default_admin()

        response, payload = self._request("GET", "/api/integration-center?limit=5", headers={"Cookie": cookie})

        self.assertEqual(response.status, 200)
        snapshot = json.loads(payload.decode("utf-8"))
        self.assertIn("scope", snapshot)
        self.assertIn("email", snapshot)
        self.assertIn("ksef", snapshot)
        self.assertIn("telegram", snapshot)
        self.assertIn("ocr", snapshot)
        self.assertIn("storage", snapshot)
        self.assertIn("scheduler", snapshot)
        self.assertIn("integration", snapshot["email"])
        self.assertIn("runs", snapshot["email"])
        self.assertIn("integration", snapshot["ksef"])
        self.assertIn("runs", snapshot["ksef"])

    def test_email_google_connect_endpoint_returns_authorization_url(self) -> None:
        cookie = self._login_default_admin()

        with patch.object(
            self.services["invoice_service"],
            "begin_email_google_connection",
            return_value={
                "authorization_url": "https://accounts.google.com/o/oauth2/auth?state=abc",
                "callback_url": "https://app.example.com/api/email/oauth/callback",
                "expires_at": "2026-04-13T10:00:00+00:00",
            },
        ) as mocked:
            response, payload = self._request(
                "POST",
                "/api/email/google/connect",
                body=json.dumps({"login_hint": "biuro@casi24.com"}),
                headers={"Cookie": cookie, "Content-Type": "application/json"},
            )

        self.assertEqual(response.status, 200)
        data = json.loads(payload.decode("utf-8"))
        self.assertIn("authorization_url", data)
        self.assertIn("callback_url", data)
        self.assertIn("expires_at", data)
        mocked.assert_called_once()

    def test_email_google_disconnect_endpoint_returns_status(self) -> None:
        cookie = self._login_default_admin()

        with patch.object(
            self.services["invoice_service"],
            "disconnect_email_google_connection",
            return_value={"status": "disconnected", "google_email": "centralna@casi24.com"},
        ) as mocked:
            response, payload = self._request(
                "POST",
                "/api/email/google/disconnect",
                headers={"Cookie": cookie, "Content-Type": "application/json"},
            )

        self.assertEqual(response.status, 200)
        data = json.loads(payload.decode("utf-8"))
        self.assertEqual(data["status"], "disconnected")
        self.assertEqual(data["google_email"], "centralna@casi24.com")
        mocked.assert_called_once()

    def test_email_oauth_callback_returns_success_html(self) -> None:
        with patch.object(
            self.services["invoice_service"],
            "finalize_email_google_connection",
            return_value={
                "status": "connected",
                "google_email": "centralna@casi24.com",
                "connection": {"google_email": "centralna@casi24.com"},
            },
        ) as mocked:
            response, payload = self._request("GET", "/api/email/oauth/callback?state=abc&code=good-code")

        self.assertEqual(response.status, 200)
        self.assertIn("text/html", response.getheader("Content-Type", ""))
        html = payload.decode("utf-8")
        self.assertIn("Centralna skrzynka Google Workspace zostala polaczona", html)
        self.assertIn("email-google-connected", html)
        mocked.assert_called_once()

    def test_dashboard_requires_session_but_login_works(self) -> None:
        response, payload = self._request("GET", "/api/dashboard")
        self.assertEqual(response.status, 401)
        self.assertIn("Brak aktywnej sesji.", payload.decode("utf-8"))

        headers = {"Content-Type": "application/json"}
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "admin", "password": "Admin1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)
        user = json.loads(payload.decode("utf-8"))
        self.assertEqual(user["login"], "admin")

        response, payload = self._request("GET", "/api/session/current", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        current = json.loads(payload.decode("utf-8"))
        self.assertEqual(current["role"], "system_owner")
        self.assertEqual(current["can_upload_knowledge"], 1)

    def test_session_current_exposes_workspace_state_and_device_context(self) -> None:
        headers = {
            "Content-Type": "application/json",
            "X-CASI-Device-Id": "desktop-a",
            "X-CASI-Device-Label": "Desktop",
        }
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "admin", "password": "Admin1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)
        current_user = json.loads(payload.decode("utf-8"))
        self.assertEqual(current_user["current_device_id"], "desktop-a")
        self.assertEqual(current_user["max_active_devices"], 3)
        self.assertIsNone(current_user["workspace_state"])

        response, payload = self._request(
            "PATCH",
            "/api/session/workspace-state",
            body=json.dumps(
                {
                    "workspace_state": {
                        "active_slot_id": "slot-knowledge",
                        "slots": [{"slot_id": "slot-knowledge", "module_key": "knowledge"}],
                    }
                }
            ),
            headers={
                "Content-Type": "application/json",
                "Cookie": cookie,
                "X-CASI-Device-Id": "desktop-a",
            },
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        updated = json.loads(payload.decode("utf-8"))
        self.assertEqual(updated["workspace_state"]["active_slot_id"], "slot-knowledge")
        self.assertEqual(updated["workspace_state_device_id"], "desktop-a")

        response, payload = self._request(
            "GET",
            "/api/session/current",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200)
        current = json.loads(payload.decode("utf-8"))
        self.assertEqual(current["workspace_state"]["slots"][0]["module_key"], "knowledge")

    def test_session_login_blocks_fourth_active_device(self) -> None:
        for device_id in ("desktop-a", "tablet-b", "phone-c"):
            response, payload = self._request(
                "POST",
                "/api/session/login",
                body=json.dumps({"login": "admin", "password": "Admin1234"}),
                headers={
                    "Content-Type": "application/json",
                    "X-CASI-Device-Id": device_id,
                    "X-CASI-Device-Label": device_id,
                },
            )
            self.assertEqual(response.status, 200, payload.decode("utf-8"))

        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "admin", "password": "Admin1234"}),
            headers={
                "Content-Type": "application/json",
                "X-CASI-Device-Id": "watch-d",
                "X-CASI-Device-Label": "watch-d",
            },
        )
        self.assertEqual(response.status, 401)
        self.assertIn("maksymalnie na 3 urzadzeniach", payload.decode("utf-8"))

    def test_dashboard_snapshot_contains_operational_alerts(self) -> None:
        cookie = self._login_default_admin()

        response, payload = self._request("GET", "/api/dashboard", headers={"Cookie": cookie})

        self.assertEqual(response.status, 200)
        snapshot = json.loads(payload.decode("utf-8"))
        self.assertIn("cards", snapshot)
        self.assertIn("recent_events", snapshot)
        self.assertIn("active_reminders", snapshot)
        self.assertIn("operational_alerts", snapshot)
        self.assertIsInstance(snapshot["operational_alerts"], list)
        invoice_alerts = [item for item in snapshot["operational_alerts"] if item.get("category") == "invoices"]
        self.assertTrue(invoice_alerts)
        self.assertTrue(
            all(item.get("action_view") == "invoices" and item.get("action_bucket") for item in invoice_alerts)
        )

    def test_dashboard_snapshot_shows_knowledge_alerts_for_document_queue(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {"name": "Klient Dashboard Wiedza", "slug": "klient-dashboard-wiedza", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        reviewer = self.services["auth_service"].create_user(
            {
                "login": "dashboard_reviewer",
                "display_name": "Dashboard Reviewer",
                "password": "Dash1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
                "capabilities": ["knowledge.read", "knowledge.manage"],
                "can_upload_knowledge": 0,
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        document = self.services["knowledge_service"].add_document(
            organization_id=int(organization["organization_id"]),
            title="Procedura do sprawdzenia",
            actor_user=admin,
            actor="admin",
            file_name="procedura_do_sprawdzenia.txt",
            content_text="Wersja pierwsza. Dokument musi przejsc review.",
            library_path="Procedury/Operacje",
            is_downloadable=True,
            use_in_assistant=True,
        )
        self.services["knowledge_service"].process_pending_jobs(limit=2)
        self.services["knowledge_service"].update_document_metadata(
            organization_id=int(organization["organization_id"]),
            knowledge_document_id=int(document["knowledge_document_id"]),
            actor_user=admin,
            actor="admin",
            business_status="do_sprawdzenia",
            reviewer_user_id=int(reviewer["user_id"]),
        )

        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "dashboard_reviewer", "password": "Dash1234"}),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)

        response, payload = self._request("GET", "/api/dashboard", headers={"Cookie": cookie})

        self.assertEqual(response.status, 200)
        snapshot = json.loads(payload.decode("utf-8"))
        knowledge_alerts = [item for item in snapshot["operational_alerts"] if item.get("action_view") == "knowledge"]
        titles = [item.get("title") for item in knowledge_alerts]
        self.assertIn("Dokumenty czekaja na sprawdzenie", titles)
        self.assertIn("Na Ciebie czekaja dokumenty firmowe", titles)
        self.assertTrue(any(item.get("action_bucket") == "knowledge_review" for item in knowledge_alerts))
        self.assertTrue(any(item.get("action_bucket") == "knowledge_my_queue" for item in knowledge_alerts))

    def test_dashboard_snapshot_exposes_knowledge_queue_with_decision_actions(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {"name": "Klient Dashboard Kolejka", "slug": "klient-dashboard-kolejka", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        reviewer = self.services["auth_service"].create_user(
            {
                "login": "dashboard_queue_reviewer",
                "display_name": "Queue Reviewer",
                "password": "DashQ1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
                "capabilities": ["knowledge.read"],
                "can_upload_knowledge": 0,
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        document = self.services["knowledge_service"].add_document(
            organization_id=int(organization["organization_id"]),
            title="Polityka decyzji dashboard",
            actor_user=admin,
            actor="admin",
            file_name="polityka_dashboard.txt",
            content_text="Dokument czeka na review i kolejne etapy decyzji.",
            library_path="Procedury/Dashboard",
            is_downloadable=True,
            use_in_assistant=True,
        )
        self.services["knowledge_service"].process_pending_jobs(limit=2)
        self.services["knowledge_service"].update_document_metadata(
            organization_id=int(organization["organization_id"]),
            knowledge_document_id=int(document["knowledge_document_id"]),
            actor_user=admin,
            actor="admin",
            business_status="do_sprawdzenia",
            reviewer_user_id=int(reviewer["user_id"]),
        )

        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "dashboard_queue_reviewer", "password": "DashQ1234"}),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)

        response, payload = self._request("GET", "/api/dashboard", headers={"Cookie": cookie})

        self.assertEqual(response.status, 200)
        snapshot = json.loads(payload.decode("utf-8"))
        self.assertIn("knowledge_queue", snapshot)
        self.assertTrue(snapshot["knowledge_queue"])
        queue_item = snapshot["knowledge_queue"][0]
        self.assertEqual(queue_item["title"], "Polityka decyzji dashboard")
        self.assertEqual(queue_item["business_status"], "do_sprawdzenia")
        self.assertEqual(queue_item["reviewer_user_id"], int(reviewer["user_id"]))
        action_codes = [item["code"] for item in queue_item["decision_actions"]]
        self.assertIn("send_for_approval", action_codes)
        self.assertIn("return_for_changes", action_codes)

    def _create_manager_assistant_org_for_http(self) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {
                "name": "Klient Powiazan HTTP",
                "slug": "klient-powiazan-http",
                "is_active": 1,
                "enabled_modules": [MANAGER_ASSISTANT_MODULE],
            },
            actor_user=admin,
            actor_login="admin",
        )
        self.services["organization_repository"].replace_enabled_modules(
            int(organization["organization_id"]),
            [MANAGER_ASSISTANT_MODULE],
            enabled_by_user_id=int(admin["user_id"]),
        )
        owner = self.services["auth_service"].create_user(
            {
                "login": "powiazania-olga",
                "display_name": "Olga Powiazania",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        other = self.services["auth_service"].create_user(
            {
                "login": "powiazania-ania",
                "display_name": "Ania Powiazania",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        return organization, owner, other

    def test_invoice_and_contractor_details_hide_private_linked_tasks_for_other_user(self) -> None:
        organization, owner, other = self._create_manager_assistant_org_for_http()
        invoice = self.services["invoice_service"].create_invoice(
            {
                "source": "MANUAL",
                "file_name": "powiazanie-http.pdf",
                "invoice_number": "FV/HTTP/1",
                "issuer_name": "HTTP Test",
                "issuer_nip": "1234567890",
                "gross_amount": 321.0,
                "currency": "PLN",
                "issue_date": "2099-04-10",
                "sale_date": "2099-04-10",
            },
            actor="Olga Powiazania",
            organization_id=organization["organization_id"],
        )
        task = self.services["task_service"].create_task(
            {
                "title": "Prywatna sprawa do faktury",
                "task_type": "zadanie",
                "status": "nowe",
                "priority": "normalny",
                "linked_entities": [
                    {"entity_type": "invoice", "entity_id": invoice["id"]},
                    {"entity_type": "contractor", "entity_id": invoice["contractor_id"]},
                ],
            },
            actor_user=owner,
            actor="Olga Powiazania",
            organization_id=organization["organization_id"],
        )

        owner_cookie = self._login("powiazania-olga", "1234")
        other_cookie = self._login("powiazania-ania", "1234")

        response, payload = self._request("GET", f"/api/invoices/{invoice['id']}", headers={"Cookie": owner_cookie})
        self.assertEqual(response.status, 200)
        invoice_detail_owner = json.loads(payload.decode("utf-8"))
        self.assertTrue(any(item["task_id"] == task["task_id"] for item in invoice_detail_owner["linked_tasks"]))

        response, payload = self._request("GET", f"/api/invoices/{invoice['id']}", headers={"Cookie": other_cookie})
        self.assertEqual(response.status, 200)
        invoice_detail_other = json.loads(payload.decode("utf-8"))
        self.assertFalse(any(item["task_id"] == task["task_id"] for item in invoice_detail_other["linked_tasks"]))

        response, payload = self._request(
            "GET",
            f"/api/contractors/{invoice['contractor_id']}",
            headers={"Cookie": owner_cookie},
        )
        self.assertEqual(response.status, 200)
        contractor_detail_owner = json.loads(payload.decode("utf-8"))
        self.assertTrue(any(item["task_id"] == task["task_id"] for item in contractor_detail_owner["linked_tasks"]))

        response, payload = self._request(
            "GET",
            f"/api/contractors/{invoice['contractor_id']}",
            headers={"Cookie": other_cookie},
        )
        self.assertEqual(response.status, 200)
        contractor_detail_other = json.loads(payload.decode("utf-8"))
        self.assertFalse(any(item["task_id"] == task["task_id"] for item in contractor_detail_other["linked_tasks"]))

    def test_task_detail_http_returns_linked_entities(self) -> None:
        organization, owner, _other = self._create_manager_assistant_org_for_http()
        invoice = self.services["invoice_service"].create_invoice(
            {
                "source": "MANUAL",
                "file_name": "powiazanie-http-2.pdf",
                "invoice_number": "FV/HTTP/2",
                "issuer_name": "HTTP Test 2",
                "issuer_nip": "9988776655",
                "gross_amount": 654.0,
                "currency": "PLN",
                "issue_date": "2099-04-11",
                "sale_date": "2099-04-11",
            },
            actor="Olga Powiazania",
            organization_id=organization["organization_id"],
        )
        task = self.services["task_service"].create_task(
            {
                "title": "Wyjasnic status klienta",
                "task_type": "zadanie",
                "status": "nowe",
                "priority": "wysoki",
                "linked_entities": [
                    {"entity_type": "invoice", "entity_id": invoice["id"]},
                    {"entity_type": "contractor", "entity_id": invoice["contractor_id"]},
                ],
            },
            actor_user=owner,
            actor="Olga Powiazania",
            organization_id=organization["organization_id"],
        )

        owner_cookie = self._login("powiazania-olga", "1234")
        response, payload = self._request("GET", f"/api/tasks/{task['task_id']}", headers={"Cookie": owner_cookie})
        self.assertEqual(response.status, 200)
        detail = json.loads(payload.decode("utf-8"))
        self.assertEqual(detail["task"]["linked_entity_count"], 2)
        self.assertTrue(any(item["entity_type"] == "invoice" for item in detail["task"]["linked_entities"]))
        self.assertTrue(any(item["entity_type"] == "contractor" for item in detail["task"]["linked_entities"]))

    def test_test_import_endpoint_can_be_disabled(self) -> None:
        headers = {"Content-Type": "application/json"}
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "admin", "password": "Admin1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)

        with patch("app.api.http_server.test_imports_enabled", return_value=False):
            response, payload = self._request("POST", "/api/import/EMAIL", headers={"Cookie": cookie})

        self.assertEqual(response.status, 403)
        self.assertIn("Import testowy jest wyłączony w tym środowisku.", payload.decode("utf-8"))

    def test_org_admin_can_check_email_and_second_check_returns_no_new_documents(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {
                "name": "Klient Email",
                "slug": "klient-email",
                "email_inbox_address": "faktury@klient-email.pl",
                "email_allowed_sender": "dokumenty@dostawca.pl",
                "email_subject_keyword": "Faktura",
                "email_integration_enabled": 1,
                "is_active": 1,
            },
            actor_user=admin,
            actor_login="admin",
        )
        self.services["auth_service"].create_user(
            {
                "login": "email-admin",
                "display_name": "Email Admin",
                "password": "1234",
                "role": "organization_admin",
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )

        headers = {"Content-Type": "application/json"}
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "email-admin", "password": "1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)

        with patch.object(
            self.services["invoice_service"].email_adapter,
            "fetch_invoice_candidates",
            return_value={
                "candidates": [
                    {
                        "incoming_date": "2026-04-11",
                        "source": "EMAIL",
                        "file_name": "mail_faktura.pdf",
                        "document_type": "pdf",
                        "invoice_number": "FV/EMAIL/44/04/2026",
                        "ksef_number": "",
                        "issuer_nip": "1234567890",
                        "issuer_name": "Email Dostawca Sp. z o.o.",
                        "issue_date": "2026-04-11",
                        "sale_date": "2026-04-11",
                        "gross_amount": 120.50,
                        "currency": "PLN",
                        "source_external_id": "email-test-44",
                        "source_sender_name": "dokumenty@dostawca.pl",
                        "source_metadata": {
                            "temat": "Faktura FV/EMAIL/44/04/2026",
                            "skrzynka": "faktury@klient-email.pl",
                            "tryb": "manual-check-imap",
                            "message_id": "<mail-44@example.com>",
                            "imap_uid": "44",
                            "nadawca_email": "dokumenty@dostawca.pl",
                            "odbiorcy": ["faktury@klient-email.pl"],
                            "dopasowany_odbiorca": "faktury@klient-email.pl",
                            "zalacznik_typ": "application/pdf",
                            "zalacznik_index": 1,
                        },
                        "notes": "Import z e-maila.",
                    },
                    {
                        "incoming_date": "2026-04-11",
                        "source": "EMAIL",
                        "file_name": "mail_faktura_2.pdf",
                        "document_type": "pdf",
                        "invoice_number": "FV/EMAIL/45/04/2026",
                        "ksef_number": "",
                        "issuer_nip": "0987654321",
                        "issuer_name": "Drugi Dostawca Sp. z o.o.",
                        "issue_date": "2026-04-11",
                        "sale_date": "2026-04-11",
                        "gross_amount": 221.00,
                        "currency": "PLN",
                        "source_external_id": "email-test-45",
                        "source_sender_name": "dokumenty@dostawca.pl",
                        "source_metadata": {
                            "temat": "Faktura FV/EMAIL/45/04/2026",
                            "skrzynka": "faktury@klient-email.pl",
                            "tryb": "manual-check-imap",
                            "message_id": "<mail-45@example.com>",
                            "imap_uid": "45",
                            "nadawca_email": "dokumenty@dostawca.pl",
                            "odbiorcy": ["faktury@klient-email.pl"],
                            "dopasowany_odbiorca": "faktury@klient-email.pl",
                            "zalacznik_typ": "application/pdf",
                            "zalacznik_index": 1,
                        },
                        "notes": "Import z e-maila.",
                    },
                ],
                "checked_message_count": 2,
                "matched_message_count": 2,
                "matched_attachment_count": 2,
                "routing_mode": "central_mailbox",
            },
        ):
            response, payload = self._request(
                "POST",
                f"/api/organizations/{organization['organization_id']}/actions/check-email",
                headers={"Cookie": cookie},
            )
            self.assertEqual(response.status, 200)
            result = json.loads(payload.decode("utf-8"))
            self.assertEqual(result["status"], "invoices_imported")
            self.assertEqual(result["imported_count"], 2)
            self.assertEqual(result["checked_message_count"], 2)
            self.assertEqual(result["matched_message_count"], 2)
            self.assertEqual(result["matched_attachment_count"], 2)
            self.assertEqual(len(result["invoices"]), 2)
            self.assertEqual(result["invoice"]["source"], "EMAIL")
            self.assertIn("run", result)
            self.assertEqual(result["run"]["imported_invoice_count"], 2)
            self.assertEqual(result["run"]["trigger_mode"], "manual")

            response, payload = self._request(
                "POST",
                f"/api/organizations/{organization['organization_id']}/actions/check-email",
                headers={"Cookie": cookie},
            )
            self.assertEqual(response.status, 200)
            result = json.loads(payload.decode("utf-8"))
            self.assertEqual(result["status"], "no_new_documents")
            self.assertEqual(result["imported_count"], 0)

        response, payload = self._request(
            "GET",
            f"/api/organizations/{organization['organization_id']}/email-import-runs",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200)
        runs = json.loads(payload.decode("utf-8"))
        self.assertTrue(runs)
        self.assertEqual(runs[0]["organization_id"], organization["organization_id"])
        self.assertIn("items_preview", runs[0])
        self.assertGreaterEqual(len(runs[0]["items_preview"]), 1)

    def test_test_email_connection_endpoint_reports_success_before_enabling_integration(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {
                "name": "Klient Email Test",
                "slug": "klient-email-test",
                "email_inbox_address": "faktury@klient-email-test.pl",
                "email_integration_enabled": 0,
                "is_active": 1,
            },
            actor_user=admin,
            actor_login="admin",
        )

        headers = {"Content-Type": "application/json"}
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "admin", "password": "Admin1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)

        with patch.object(
            self.services["invoice_service"].email_adapter,
            "test_connection",
            return_value={
                "connected": True,
                "host": "imap.gmail.com",
                "port": 993,
                "folder": "INBOX",
                "use_ssl": True,
                "username_masked": "fa***@casi24.com",
                "message_count": 12,
                "preview_uids": ["101", "100"],
            },
        ):
            response, payload = self._request(
                "POST",
                f"/api/organizations/{organization['organization_id']}/actions/test-email-connection",
                headers={"Cookie": cookie},
            )

        self.assertEqual(response.status, 200)
        result = json.loads(payload.decode("utf-8"))
        self.assertEqual(result["status"], "connection_ok")
        self.assertEqual(result["message_count"], 12)
        self.assertIn("Folder: INBOX", result["message"])

        updated_organization = self.services["organization_repository"].get_by_id(organization["organization_id"])
        self.assertIsNotNone(updated_organization)
        assert updated_organization is not None
        self.assertTrue(updated_organization["email_last_connection_tested_at"])
        self.assertIn("Polaczenie IMAP dziala", updated_organization["email_last_connection_status"])

    def test_check_email_endpoint_returns_friendly_error_when_system_imap_is_missing(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {
                "name": "Klient Email Blad",
                "slug": "klient-email-blad",
                "email_inbox_address": "faktury@klient-email-blad.pl",
                "email_integration_enabled": 1,
                "is_active": 1,
            },
            actor_user=admin,
            actor_login="admin",
        )

        headers = {"Content-Type": "application/json"}
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "admin", "password": "Admin1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)

        with patch.object(
            self.services["invoice_service"].email_adapter,
            "fetch_invoice_candidates",
            side_effect=EmailIngestionError(
                "Integracja e-mail nie jest jeszcze skonfigurowana na poziomie systemu. Uzupelnij ustawienia IMAP."
            ),
        ):
            response, payload = self._request(
                "POST",
                f"/api/organizations/{organization['organization_id']}/actions/check-email",
                headers={"Cookie": cookie},
            )

        self.assertEqual(response.status, 400)
        self.assertIn("Uzupelnij ustawienia IMAP", payload.decode("utf-8"))

    def test_check_email_endpoint_rejects_disabled_integration(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {
                "name": "Klient Bez Emaila",
                "slug": "klient-bez-emaila",
                "email_inbox_address": "faktury@klient-bez-emaila.pl",
                "email_integration_enabled": 0,
                "is_active": 1,
            },
            actor_user=admin,
            actor_login="admin",
        )

        headers = {"Content-Type": "application/json"}
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "admin", "password": "Admin1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)

        response, payload = self._request(
            "POST",
            f"/api/organizations/{organization['organization_id']}/actions/check-email",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 400)
        self.assertIn("Integracja e-mail jest wylaczona", payload.decode("utf-8"))

    def test_test_ksef_connection_endpoint_reports_success(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {
                "name": "Klient KSeF Test",
                "slug": "klient-ksef-test",
                "ksef_company_identifier": "1234567890",
                "ksef_environment": "demo",
                "ksef_integration_enabled": 1,
                "is_active": 1,
            },
            actor_user=admin,
            actor_login="admin",
        )

        cookie = self._login_default_admin()

        response, payload = self._request(
            "POST",
            f"/api/organizations/{organization['organization_id']}/actions/test-ksef-connection",
            headers={"Cookie": cookie},
        )

        self.assertEqual(response.status, 200)
        result = json.loads(payload.decode("utf-8"))
        self.assertEqual(result["status"], "connection_ok")
        self.assertEqual(result["company_identifier"], "1234567890")
        self.assertIn("KSeF", result["message"])

    def test_org_admin_can_check_ksef_and_second_check_returns_no_new_documents(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {
                "name": "Klient KSeF",
                "slug": "klient-ksef",
                "ksef_company_identifier": "9988877766",
                "ksef_environment": "demo",
                "ksef_integration_enabled": 1,
                "is_active": 1,
            },
            actor_user=admin,
            actor_login="admin",
        )
        self.services["auth_service"].create_user(
            {
                "login": "ksef-admin",
                "display_name": "KSeF Admin",
                "password": "1234",
                "role": "organization_admin",
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )

        headers = {"Content-Type": "application/json"}
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "ksef-admin", "password": "1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)

        response, payload = self._request(
            "POST",
            f"/api/organizations/{organization['organization_id']}/actions/check-ksef",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200)
        result = json.loads(payload.decode("utf-8"))
        self.assertEqual(result["status"], "invoices_imported")
        self.assertEqual(result["imported_count"], 2)
        self.assertEqual(result["checked_document_count"], 2)
        self.assertEqual(len(result["invoices"]), 2)
        self.assertIn("run", result)
        self.assertEqual(result["run"]["imported_invoice_count"], 2)
        self.assertEqual(result["run"]["trigger_mode"], "manual")

        response, payload = self._request(
            "POST",
            f"/api/organizations/{organization['organization_id']}/actions/check-ksef",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200)
        result = json.loads(payload.decode("utf-8"))
        self.assertEqual(result["status"], "no_new_documents")
        self.assertEqual(result["imported_count"], 0)

        response, payload = self._request(
            "GET",
            f"/api/organizations/{organization['organization_id']}/ksef-import-runs",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200)
        runs = json.loads(payload.decode("utf-8"))
        self.assertTrue(runs)
        self.assertEqual(runs[0]["organization_id"], organization["organization_id"])
        self.assertIn("items_preview", runs[0])
        self.assertGreaterEqual(len(runs[0]["items_preview"]), 1)

    def test_invoice_batch_action_endpoint_updates_multiple_invoices(self) -> None:
        headers = {"Content-Type": "application/json"}
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "admin", "password": "Admin1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)

        response, payload = self._request(
            "POST",
            "/api/invoices/actions/batch",
            body=json.dumps({"action": "mark-verification", "invoice_ids": [1, 5]}),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200)
        result = json.loads(payload.decode("utf-8"))
        self.assertEqual(result["updated_count"], 2)

        response, payload = self._request("GET", "/api/invoices/1", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        detail = json.loads(payload.decode("utf-8"))
        self.assertEqual(detail["invoice"]["status"], "weryfikacja")

    def test_invoice_verification_inbox_endpoint_returns_operational_sections(self) -> None:
        cookie = self._login_default_admin()

        response, payload = self._request("GET", "/api/invoices/verification-inbox", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        snapshot = json.loads(payload.decode("utf-8"))

        self.assertIn("summary", snapshot)
        self.assertIn("sections", snapshot)
        self.assertEqual(
            set(snapshot["sections"].keys()),
            {"verification", "duplicates", "ksef_corrections", "ocr_attention"},
        )
        self.assertGreaterEqual(snapshot["summary"]["total_open_count"], 1)

    def test_invoice_verification_workspace_endpoint_returns_sections_and_sla_summary(self) -> None:
        cookie = self._login_default_admin()

        response, payload = self._request(
            "GET",
            "/api/invoices/verification-workspace?limit=10&bucket=duplicates",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200)
        snapshot = json.loads(payload.decode("utf-8"))

        self.assertIn("summary", snapshot)
        self.assertIn("bucket_order", snapshot)
        self.assertIn("sections", snapshot)
        self.assertEqual(snapshot["summary"]["active_bucket"], "duplicates")
        self.assertEqual(
            snapshot["bucket_order"],
            ["verification", "duplicates", "ksef_corrections", "ocr_attention"],
        )
        self.assertIn("duplicates", snapshot["sections"])
        self.assertIn("sla_days", snapshot["sections"]["duplicates"])
        self.assertIn("sla_breached_count", snapshot["sections"]["duplicates"])
        self.assertIsInstance(snapshot["sections"]["duplicates"]["items"], list)

    def test_invoice_compare_endpoint_returns_side_by_side_rows(self) -> None:
        invoice_left = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-05-04",
                "source": "KSeF",
                "file_name": "http_compare_left.xml",
                "document_type": "xml",
                "invoice_number": "FV/HTTP/04/05/2026",
                "ksef_number": "KSEF-HTTP-04",
                "issuer_nip": "9019029034",
                "issuer_name": "HTTP Compare Left",
                "issue_date": "2026-05-04",
                "sale_date": "2026-05-04",
                "gross_amount": 610.0,
                "currency": "PLN",
                "status": "nowa",
                "source_external_id": "http-compare-left",
            },
            actor="test",
        )
        invoice_right = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-05-05",
                "source": "EMAIL",
                "file_name": "http_compare_right.pdf",
                "document_type": "pdf",
                "invoice_number": "FV/HTTP/04/05/2026",
                "issuer_nip": "9019029034",
                "issuer_name": "HTTP Compare Right",
                "issue_date": "2026-05-05",
                "sale_date": "2026-05-04",
                "gross_amount": 611.0,
                "currency": "PLN",
                "status": "weryfikacja",
                "source_external_id": "http-compare-right",
            },
            actor="test",
        )
        cookie = self._login_default_admin()

        response, payload = self._request(
            "GET",
            f"/api/invoices/compare?left_id={invoice_left['id']}&right_id={invoice_right['id']}",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200)
        comparison = json.loads(payload.decode("utf-8"))

        self.assertEqual(comparison["left_invoice"]["id"], int(invoice_left["id"]))
        self.assertEqual(comparison["right_invoice"]["id"], int(invoice_right["id"]))
        self.assertEqual(len(comparison["rows"]), 8)
        self.assertTrue(comparison["summary"]["same_invoice_number_and_nip"])
        self.assertFalse(comparison["summary"]["same_ksef_number"])
        gross_amount_row = next(row for row in comparison["rows"] if row["field_name"] == "gross_amount")
        self.assertFalse(gross_amount_row["matches"])
        self.assertTrue(gross_amount_row["left_is_ksef_protected"])

    def test_invoice_detail_endpoint_returns_field_provenance_and_duplicate_center(self) -> None:
        cookie = self._login_default_admin()

        response, payload = self._request("GET", "/api/invoices/2", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        detail = json.loads(payload.decode("utf-8"))

        self.assertIn("field_provenance", detail)
        self.assertIn("duplicate_center", detail)
        self.assertTrue(any(item["field_name"] == "invoice_number" for item in detail["field_provenance"]))
        self.assertGreaterEqual(detail["duplicate_center"]["candidate_count"], 1)

    def test_invoice_approval_workflow_updates_invoice_and_exposes_request(self) -> None:
        cookie = self._login_default_admin()
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {
                "name": "Klient Akceptacje",
                "slug": "klient-akceptacje",
                "is_active": 1,
                "enabled_modules": ["manager_assistant"],
            },
            actor_user=admin,
            actor_login="admin",
        )
        self.services["organization_repository"].replace_enabled_modules(
            int(organization["organization_id"]),
            [MANAGER_ASSISTANT_MODULE],
            enabled_by_user_id=int(admin["user_id"]),
        )
        invoice = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-04-14",
                "source": "EMAIL",
                "file_name": "akceptacja_test.pdf",
                "document_type": "pdf",
                "invoice_number": "AKC/1/04/2026",
                "issuer_nip": "1234567890",
                "issuer_name": "Akceptacje Sp. z o.o.",
                "issue_date": "2026-04-14",
                "sale_date": "2026-04-14",
                "gross_amount": 123.45,
                "currency": "PLN",
                "status": "nowa",
            },
            actor="admin",
            organization_id=int(organization["organization_id"]),
        )
        invoice_id = invoice["id"]
        organization_id = int(organization["organization_id"])

        response, payload = self._request(
            "POST",
            f"/api/approvals?organization_id={organization_id}",
            body=json.dumps(
                {
                    "entity_type": "invoice",
                    "entity_id": invoice_id,
                    "title": "Akceptacja faktury",
                    "description": "Sprawdzenie faktury przed zaksięgowaniem.",
                }
            ),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))
        approval = json.loads(payload.decode("utf-8"))
        approval_id = approval["approval_request_id"]

        response, payload = self._request(
            "POST",
            f"/api/approvals/{approval_id}/approve?organization_id={organization_id}",
            body=json.dumps({"reason": "Zatwierdzona po kontroli."}),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        approved = json.loads(payload.decode("utf-8"))
        self.assertEqual(approved["status"], "approved")

        response, payload = self._request("GET", f"/api/invoices/{invoice_id}", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        detail = json.loads(payload.decode("utf-8"))
        self.assertEqual(detail["invoice"]["status"], "poprawna")
        self.assertTrue(
            any(item["approval_request_id"] == approval_id and item["status"] == "approved" for item in detail["approval_requests"])
        )

    def test_organization_patch_can_store_ksef_delegate_fields(self) -> None:
        cookie = self._login_default_admin()
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {
                "name": "Klient Delegacja",
                "slug": "klient-delegacja",
                "is_active": 1,
            },
            actor_user=admin,
            actor_login="admin",
        )
        delegate = self.services["auth_service"].create_user(
            {
                "login": "delegat-ksef-http",
                "display_name": "Delegat KSeF HTTP",
                "password": "1234",
                "role": "coordinator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=int(admin["user_id"]),
            actor_user=admin,
        )

        response, payload = self._request(
            "PATCH",
            f"/api/organizations/{organization['organization_id']}",
            body=json.dumps(
                {
                    "ksef_correction_delegate_user_id": delegate["user_id"],
                    "ksef_correction_delegate_expires_at": "2026-06-30T17:00",
                }
            ),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        updated = json.loads(payload.decode("utf-8"))
        self.assertEqual(updated["ksef_correction_delegate_user_id"], delegate["user_id"])
        self.assertEqual(updated["ksef_correction_delegate_expires_at"], "2026-06-30T17:00")
        self.assertTrue(updated["ksef_correction_delegate_assigned_at"])
        self.assertEqual(updated["ksef_correction_delegate_user"]["login"], "delegat-ksef-http")
        self.assertEqual(updated["ksef_correction_delegate_user"]["role"], "coordinator")

    def test_operator_save_on_ksef_invoice_returns_request_and_delegate_can_approve_via_http(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {
                "name": "Klient KSeF HTTP",
                "slug": "klient-ksef-http",
                "is_active": 1,
            },
            actor_user=admin,
            actor_login="admin",
        )
        delegate = self.services["auth_service"].create_user(
            {
                "login": "delegate-http",
                "display_name": "Delegate HTTP",
                "password": "1234",
                "role": "coordinator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=int(admin["user_id"]),
            actor_user=admin,
        )
        self.services["auth_service"].create_user(
            {
                "login": "operator-http",
                "display_name": "Operator HTTP",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=int(admin["user_id"]),
            actor_user=admin,
        )
        self.services["organization_service"].update_organization(
            int(organization["organization_id"]),
            {
                "ksef_correction_delegate_user_id": delegate["user_id"],
                "ksef_correction_delegate_expires_at": "2026-12-31T23:59",
            },
            actor_user=admin,
            actor_login="admin",
        )
        invoice = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-06-01",
                "source": "KSeF",
                "file_name": "ksef_http_01_06_2026.xml",
                "document_type": "xml",
                "invoice_number": "FV/KSEF/HTTP/01",
                "ksef_number": "KSEF-HTTP-0001",
                "issuer_nip": "7778889990",
                "issuer_name": "HTTP KSeF Sp. z o.o.",
                "issue_date": "2026-06-01",
                "sale_date": "2026-06-01",
                "gross_amount": 180.0,
                "currency": "PLN",
                "status": "nowa",
                "source_external_id": "ksef-http-0001",
            },
            actor="admin",
            organization_id=int(organization["organization_id"]),
        )

        operator_cookie = self._login("operator-http", "1234")
        response, payload = self._request(
            "PATCH",
            f"/api/invoices/{invoice['id']}?organization_id={organization['organization_id']}",
            body=json.dumps({"gross_amount": "199.99", "notes": "Prosba po zapisie."}),
            headers={"Cookie": operator_cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        update_result = json.loads(payload.decode("utf-8"))
        self.assertEqual(update_result["invoice"]["gross_amount"], 180.0)
        self.assertEqual(update_result["invoice"]["notes"], "Prosba po zapisie.")
        self.assertEqual(update_result["ksef_correction"]["mode"], "request_created")
        approval_request_id = int(update_result["ksef_correction"]["request_id"])
        self.assertEqual(update_result["ksef_correction"]["requested_user_id"], delegate["user_id"])

        delegate_cookie = self._login("delegate-http", "1234")
        response, payload = self._request(
            "GET",
            f"/api/invoices/{invoice['id']}?organization_id={organization['organization_id']}",
            headers={"Cookie": delegate_cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        detail_before = json.loads(payload.decode("utf-8"))
        self.assertEqual(len(detail_before["approval_requests"]), 1)
        self.assertTrue(detail_before["approval_requests"][0]["can_decide"])
        self.assertEqual(detail_before["ksef_corrections"]["pending"][0]["source_value"], "180.00")
        self.assertEqual(detail_before["ksef_corrections"]["pending"][0]["local_value"], "199.99")

        response, payload = self._request(
            "POST",
            f"/api/approvals/{approval_request_id}/approve?organization_id={organization['organization_id']}",
            body=json.dumps({"reason": "Delegat zaakceptowal korekte."}),
            headers={"Cookie": delegate_cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        approved = json.loads(payload.decode("utf-8"))
        self.assertEqual(approved["status"], "approved")

        response, payload = self._request(
            "GET",
            f"/api/invoices/{invoice['id']}?organization_id={organization['organization_id']}",
            headers={"Cookie": delegate_cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        detail_after = json.loads(payload.decode("utf-8"))
        self.assertEqual(detail_after["invoice"]["gross_amount"], 199.99)
        self.assertEqual(detail_after["ksef_corrections"]["authoritative_values"]["gross_amount"], "180.00")
        self.assertEqual(detail_after["ksef_corrections"]["active_local_values"]["gross_amount"], 199.99)
        self.assertEqual(detail_after["approval_requests"][0]["status"], "approved")
        self.assertTrue(
            any(
                item["status"] == "approved" and item["local_value"] == "199.99"
                for item in detail_after["ksef_corrections"]["approved"]
            )
        )

    def test_org_user_sees_only_own_invoices_and_cannot_open_other_org_files(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        default_org = self.services["organization_repository"].ensure_default_organization()
        default_slug = str(default_org["slug"])
        organization = self.services["organization_service"].create_organization(
            {"name": "Klient Beta", "slug": "klient-beta", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        self.services["auth_service"].create_user(
            {
                "login": "beta",
                "display_name": "Beta Operator",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        beta_invoice = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-04-08",
                "source": "EMAIL",
                "file_name": "beta_1.pdf",
                "document_type": "pdf",
                "invoice_number": "BETA/1/04/2026",
                "issuer_nip": "2223334445",
                "issuer_name": "Klient Beta Dostawca",
                "issue_date": "2026-04-08",
                "sale_date": "2026-04-08",
                "gross_amount": 321.0,
                "currency": "PLN",
                "status": "nowa",
            },
            actor="test",
            organization_id=int(organization["organization_id"]),
        )

        headers = {"Content-Type": "application/json"}
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "beta", "password": "1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)

        response, payload = self._request("GET", "/api/invoices", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        invoices = json.loads(payload.decode("utf-8"))
        self.assertTrue(all(item["organization_slug"] == "klient-beta" for item in invoices))
        self.assertTrue(any(item["id"] == beta_invoice["id"] for item in invoices))
        self.assertFalse(any(item["organization_slug"] == default_slug for item in invoices))

        response, payload = self._request("GET", f"/pliki/dokumenty/organizacje/{default_slug}/KSeF/2026-04-01/ksef_fv_biuroserwis_2026_04_01_dokument.txt", headers={"Cookie": cookie})
        self.assertEqual(response.status, 403)
        self.assertIn("Brak dostępu do plików innej organizacji.", payload.decode("utf-8"))

    def test_org_user_sees_only_own_knowledge_base_and_cannot_open_other_org_knowledge_files(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {"name": "Klient Beta", "slug": "klient-beta", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        self.services["auth_service"].create_user(
            {
                "login": "beta",
                "display_name": "Beta Operator",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        default_org = self.services["organization_repository"].ensure_default_organization()
        default_slug = str(default_org["slug"])
        self.services["knowledge_service"].add_document(
            organization_id=int(default_org["organization_id"]),
            title="Regulamin domyslny",
            actor_user=admin,
            actor="admin",
            file_name="regulamin_domyslny.txt",
            content_text="W organizacji domyslnej zatwierdzenie delegacji nalezy do zarzadu.",
        )
        beta_doc = self.services["knowledge_service"].add_document(
            organization_id=int(organization["organization_id"]),
            title="Procedury Beta",
            actor_user=admin,
            actor="admin",
            file_name="procedury_beta.txt",
            content_text="W organizacji Beta delegacje zatwierdza dyrektor operacyjny.",
        )

        headers = {"Content-Type": "application/json"}
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "beta", "password": "1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)

        response, payload = self._request("GET", "/api/knowledge/documents", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        knowledge_payload = json.loads(payload.decode("utf-8"))
        self.assertEqual(len(knowledge_payload["documents"]), 1)
        self.assertEqual(knowledge_payload["documents"][0]["title"], "Procedury Beta")
        self.assertIn("klient-beta", knowledge_payload["folder_path"])

        response, payload = self._request(
            "POST",
            "/api/knowledge/ask",
            body=json.dumps({"question": "Kto zatwierdza delegacje?"}),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200)
        answer_payload = json.loads(payload.decode("utf-8"))
        self.assertIn("dyrektor operacyjny", answer_payload["answer"])

        default_path = KNOWLEDGE_DIR / "organizacje" / default_slug
        default_file = next(default_path.rglob("*.txt"))
        relative_default = default_file.relative_to(KNOWLEDGE_DIR).as_posix()
        response, payload = self._request(
            "GET",
            f"/pliki/wiedza/{relative_default}",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 403)
        self.assertIn("Brak dost", payload.decode("utf-8"))

        response, payload = self._request(
            "GET",
            f"/pliki/wiedza/{beta_doc['file_storage_key']}",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200)
        self.assertIn("delegacje", payload.decode("utf-8").lower())

    def test_knowledge_upload_permission_is_controlled_per_user(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {"name": "Klient Gamma", "slug": "klient-gamma", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        self.services["auth_service"].create_user(
            {
                "login": "gamma-gosc",
                "display_name": "Gamma Gosc",
                "password": "1234",
                "role": "guest",
                "can_upload_knowledge": 1,
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        self.services["auth_service"].create_user(
            {
                "login": "gamma-koordynator",
                "display_name": "Gamma Koordynator",
                "password": "1234",
                "role": "coordinator",
                "can_upload_knowledge": 1,
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        self.services["auth_service"].create_user(
            {
                "login": "gamma-operator",
                "display_name": "Gamma Operator",
                "password": "1234",
                "role": "operator",
                "can_upload_knowledge": 0,
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )

        headers = {"Content-Type": "application/json"}
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "gamma-koordynator", "password": "1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        allowed_cookie = response.getheader("Set-Cookie")
        self.assertTrue(allowed_cookie)

        response, payload = self._request("GET", "/api/session/current", headers={"Cookie": allowed_cookie})
        self.assertEqual(response.status, 200)
        allowed_current = json.loads(payload.decode("utf-8"))
        self.assertEqual(allowed_current["can_upload_knowledge"], 1)

        response, payload = self._request(
            "POST",
            "/api/knowledge/documents",
            body=json.dumps(
                {
                    "title": "Instrukcja Gamma",
                    "file_name": "instrukcja_gamma.txt",
                    "content_text": "W organizacji Gamma dokumenty zatwierdza kierownik operacyjny.",
                }
            ),
            headers={"Cookie": allowed_cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 201)
        created_payload = json.loads(payload.decode("utf-8"))
        self.assertEqual(created_payload["title"], "Instrukcja Gamma")

        response, payload = self._request("GET", "/api/knowledge/documents", headers={"Cookie": allowed_cookie})
        self.assertEqual(response.status, 200)
        knowledge_payload = json.loads(payload.decode("utf-8"))
        self.assertEqual(len(knowledge_payload["documents"]), 1)
        self.assertEqual(knowledge_payload["documents"][0]["title"], "Instrukcja Gamma")

        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "gamma-gosc", "password": "1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        guest_cookie = response.getheader("Set-Cookie")
        self.assertTrue(guest_cookie)

        response, payload = self._request("GET", "/api/session/current", headers={"Cookie": guest_cookie})
        self.assertEqual(response.status, 200)
        guest_current = json.loads(payload.decode("utf-8"))
        self.assertEqual(guest_current["can_upload_knowledge"], 0)

        response, payload = self._request(
            "POST",
            "/api/knowledge/documents",
            body=json.dumps(
                {
                    "title": "Instrukcja Goscia",
                    "file_name": "instrukcja_goscia.txt",
                    "content_text": "Gosc nie powinien dodawac dokumentow.",
                }
            ),
            headers={"Cookie": guest_cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 403)
        self.assertIn("Brak uprawnien do tej operacji.", payload.decode("utf-8"))

        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "gamma-operator", "password": "1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        blocked_cookie = response.getheader("Set-Cookie")
        self.assertTrue(blocked_cookie)

        response, payload = self._request("GET", "/api/session/current", headers={"Cookie": blocked_cookie})
        self.assertEqual(response.status, 200)
        blocked_current = json.loads(payload.decode("utf-8"))
        self.assertEqual(blocked_current["can_upload_knowledge"], 0)

        response, payload = self._request(
            "POST",
            "/api/knowledge/documents",
            body=json.dumps(
                {
                    "title": "Zablokowany dokument",
                    "file_name": "zablokowany.txt",
                    "content_text": "To konto nie powinno dodac dokumentu.",
                }
            ),
            headers={"Cookie": blocked_cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 403)
        self.assertIn("uprawnienia do dodawania plików do bazy wiedzy", payload.decode("utf-8"))

        response, payload = self._request(
            "POST",
            "/api/knowledge/sync",
            headers={"Cookie": blocked_cookie},
        )
        self.assertEqual(response.status, 403)
        self.assertIn("uprawnienia do dodawania plików do bazy wiedzy", payload.decode("utf-8"))

    def test_knowledge_reprocess_requires_manage_capability(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {"name": "Klient Reprocess", "slug": "klient-reprocess", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        self.services["auth_service"].create_user(
            {
                "login": "reprocess-operator",
                "display_name": "Reprocess Operator",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        self.services["auth_service"].create_user(
            {
                "login": "reprocess-koordynator",
                "display_name": "Reprocess Koordynator",
                "password": "1234",
                "role": "coordinator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )

        document = self.services["knowledge_service"].add_document(
            organization_id=int(organization["organization_id"]),
            title="Polityka delegacji",
            actor_user=admin,
            actor="admin",
            file_name="polityka_delegacji.txt",
            content_text="Delegacje zatwierdza dyrektor operacyjny.",
        )
        self.services["knowledge_service"].process_pending_jobs(limit=2)

        headers = {"Content-Type": "application/json"}
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "reprocess-operator", "password": "1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        operator_cookie = response.getheader("Set-Cookie")
        self.assertTrue(operator_cookie)

        response, payload = self._request(
            "POST",
            f"/api/knowledge/documents/{document['knowledge_document_id']}/reprocess",
            headers={"Cookie": operator_cookie},
        )
        self.assertEqual(response.status, 403)
        self.assertIn("zarz", payload.decode("utf-8").lower())

        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "reprocess-koordynator", "password": "1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        coordinator_cookie = response.getheader("Set-Cookie")
        self.assertTrue(coordinator_cookie)

        response, payload = self._request(
            "POST",
            f"/api/knowledge/documents/{document['knowledge_document_id']}/reprocess",
            headers={"Cookie": coordinator_cookie},
        )
        self.assertEqual(response.status, 202)
        reprocess_payload = json.loads(payload.decode("utf-8"))
        self.assertEqual(reprocess_payload["processing_status"], "queued")

    def test_knowledge_document_metadata_can_be_updated_and_is_searchable(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {"name": "Klient Dokumenty", "slug": "klient-dokumenty", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        reviewer = self.services["auth_service"].create_user(
            {
                "login": "metadata-reviewer",
                "display_name": "Metadata Reviewer",
                "password": "Meta1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
                "capabilities": ["knowledge.read"],
                "can_upload_knowledge": 0,
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        approver = self.services["auth_service"].create_user(
            {
                "login": "metadata-approver",
                "display_name": "Metadata Approver",
                "password": "Meta1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
                "capabilities": ["knowledge.read"],
                "can_upload_knowledge": 0,
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        document = self.services["knowledge_service"].add_document(
            organization_id=int(organization["organization_id"]),
            title="Aneks roboczy",
            actor_user=admin,
            actor="admin",
            file_name="aneks_roboczy.txt",
            content_text="Wzor aneksu do umowy dla klientow strategicznych.",
            library_path="Robocze",
            is_downloadable=True,
            use_in_assistant=False,
        )
        self.services["knowledge_service"].process_pending_jobs(limit=4)

        headers = {"Content-Type": "application/json"}
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "admin", "password": "Admin1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)

        response, payload = self._request(
            "PATCH",
            f"/api/knowledge/documents/{document['knowledge_document_id']}?organization_id={organization['organization_id']}",
            body=json.dumps(
                {
                    "title": "Wzor aneksu handlowego",
                    "library_path": "Wzory/Umowy",
                    "is_downloadable": True,
                    "use_in_assistant": False,
                    "business_status": "do_akceptacji",
                    "reviewer_user_id": int(reviewer["user_id"]),
                    "approver_user_id": int(approver["user_id"]),
                }
            ),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200)
        updated_payload = json.loads(payload.decode("utf-8"))
        self.assertEqual(updated_payload["title"], "Wzor aneksu handlowego")
        self.assertEqual(updated_payload["library_path"], "Wzory/Umowy")
        self.assertEqual(updated_payload["business_status"], "do_akceptacji")
        self.assertEqual(updated_payload["reviewer_user_id"], int(reviewer["user_id"]))
        self.assertEqual(updated_payload["approver_user_id"], int(approver["user_id"]))
        self.assertEqual(updated_payload["reviewer_user_label"], "Metadata Reviewer")
        self.assertEqual(updated_payload["approver_user_label"], "Metadata Approver")

        response, payload = self._request(
            "GET",
            f"/api/knowledge/documents?organization_id={organization['organization_id']}",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200)
        knowledge_payload = json.loads(payload.decode("utf-8"))
        self.assertTrue(any(item["library_path"] == "Wzory/Umowy" for item in knowledge_payload["documents"]))
        self.assertTrue(any(item["business_status"] == "do_akceptacji" for item in knowledge_payload["documents"]))

        response, payload = self._request(
            "GET",
            f"/api/search?q=aneks&organization_id={organization['organization_id']}",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200)
        search_payload = json.loads(payload.decode("utf-8"))
        titles = [
            item["title"]
            for group in search_payload["groups"]
            for item in group["items"]
            if group["key"] == "knowledge_documents"
        ]
        self.assertIn("Wzor aneksu handlowego", titles)

    def test_knowledge_assignment_candidates_endpoint_returns_active_org_members(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {"name": "Klient Kandydaci", "slug": "klient-kandydaci", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        active_member = self.services["auth_service"].create_user(
            {
                "login": "aktywny-kandydat",
                "display_name": "Aktywny Kandydat",
                "password": "Cand1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
                "capabilities": ["knowledge.read"],
                "can_upload_knowledge": 0,
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        inactive_member = self.services["auth_service"].create_user(
            {
                "login": "nieaktywny-kandydat",
                "display_name": "Nieaktywny Kandydat",
                "password": "Cand1234",
                "role": "operator",
                "is_active": 0,
                "organization_id": organization["organization_id"],
                "capabilities": ["knowledge.read"],
                "can_upload_knowledge": 0,
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        cookie = self._login_default_admin()

        response, payload = self._request(
            "GET",
            f"/api/knowledge/assignment-candidates?organization_id={organization['organization_id']}",
            headers={"Cookie": cookie},
        )

        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        candidates = json.loads(payload.decode("utf-8"))
        candidate_ids = {int(item["user_id"]) for item in candidates}
        self.assertIn(int(active_member["user_id"]), candidate_ids)
        self.assertNotIn(int(inactive_member["user_id"]), candidate_ids)

    def test_knowledge_document_detail_exposes_audit_after_download(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {"name": "Klient Audyt", "slug": "klient-audyt", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        document = self.services["knowledge_service"].add_document(
            organization_id=int(organization["organization_id"]),
            title="Wzor umowy ramowej",
            actor_user=admin,
            actor="admin",
            file_name="wzor_umowy_ramowej.txt",
            content_text="Wzor umowy ramowej dla klientow enterprise.",
            library_path="Wzory/Umowy",
            is_downloadable=True,
            use_in_assistant=False,
        )
        self.services["knowledge_service"].process_pending_jobs(limit=4)

        headers = {"Content-Type": "application/json"}
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "admin", "password": "Admin1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)

        response, payload = self._request(
            "GET",
            f"/api/knowledge/documents/{document['knowledge_document_id']}/download?organization_id={organization['organization_id']}",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200)
        self.assertIn("Wzor umowy ramowej", payload.decode("utf-8"))

        response, payload = self._request(
            "GET",
            f"/api/knowledge/documents/{document['knowledge_document_id']}?organization_id={organization['organization_id']}",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200)
        detail_payload = json.loads(payload.decode("utf-8"))
        self.assertIn("audit_events", detail_payload)
        self.assertEqual(detail_payload["audit_summary"]["download_count"], 1)
        self.assertTrue(any(item["event_type"] == "knowledge_document_downloaded" for item in detail_payload["audit_events"]))
        self.assertTrue(any(item["action_label"] == "Pobranie pliku" for item in detail_payload["audit_events"]))

    def test_knowledge_document_comment_and_official_version_endpoints_update_detail(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {"name": "Klient Workflow", "slug": "klient-workflow", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        document = self.services["knowledge_service"].add_document(
            organization_id=int(organization["organization_id"]),
            title="Procedura obiegu",
            actor_user=admin,
            actor="admin",
            file_name="procedura_obiegu.txt",
            content_text="Wersja pierwsza. Akceptuje kierownik operacyjny.",
            library_path="Procedury/HR",
            is_downloadable=True,
            use_in_assistant=True,
        )
        self.services["knowledge_service"].process_pending_jobs(limit=2)
        self.services["knowledge_service"].replace_document_file(
            organization_id=int(organization["organization_id"]),
            knowledge_document_id=int(document["knowledge_document_id"]),
            actor_user=admin,
            actor="admin",
            file_name="procedura_obiegu_v2.txt",
            file_bytes=b"Wersja druga. Akceptuje dyrektor finansowy.",
            mime_type="text/plain",
        )
        self.services["knowledge_service"].process_pending_jobs(limit=2)
        cookie = self._login_default_admin()

        response, payload = self._request(
            "POST",
            f"/api/knowledge/documents/{document['knowledge_document_id']}/mark-official-version?organization_id={organization['organization_id']}",
            body=json.dumps({"version_number": 2}),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        official_payload = json.loads(payload.decode("utf-8"))
        self.assertEqual(official_payload["official_version_number"], 2)

        response, payload = self._request(
            "POST",
            f"/api/knowledge/documents/{document['knowledge_document_id']}/comments?organization_id={organization['organization_id']}",
            body=json.dumps(
                {
                    "note_text": "Ta wersja wchodzi do obiegu od poniedzialku.",
                    "version_number": 2,
                    "annotation_kind": "annotation",
                    "anchor_label": "sekcja akceptacji",
                }
            ),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))
        comment_payload = json.loads(payload.decode("utf-8"))
        self.assertEqual(comment_payload["comment_summary"]["comment_count"], 1)
        self.assertEqual(comment_payload["comments"][0]["version_number"], 2)
        self.assertEqual(comment_payload["comments"][0]["annotation_kind"], "annotation")

        response, payload = self._request(
            "GET",
            f"/api/knowledge/documents/{document['knowledge_document_id']}?organization_id={organization['organization_id']}",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        detail_payload = json.loads(payload.decode("utf-8"))
        self.assertEqual(detail_payload["official_version_number"], 2)
        self.assertTrue(detail_payload["versions"][0]["is_official"])
        self.assertEqual(detail_payload["comment_summary"]["comment_count"], 1)
        self.assertTrue(any(item["event_type"] == "knowledge_document_official_version_marked" for item in detail_payload["audit_events"]))
        self.assertTrue(any(item["event_type"] == "knowledge_document_comment_added" for item in detail_payload["audit_events"]))

    def test_knowledge_document_compare_endpoint_returns_diff(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {"name": "Klient Compare", "slug": "klient-compare", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        document = self.services["knowledge_service"].add_document(
            organization_id=int(organization["organization_id"]),
            title="Procedura zawarcia umowy",
            actor_user=admin,
            actor="admin",
            file_name="procedura_umowy.txt",
            content_text=(
                "Etap 1: przygotuj brief.\n"
                "Etap 2: potwierdz budzet.\n"
                "Etap 3: wyslij projekt."
            ),
            library_path="Procedury/Umowy",
            is_downloadable=True,
            use_in_assistant=True,
        )
        self.services["knowledge_service"].process_pending_jobs(limit=4)
        self.services["knowledge_service"].replace_document_file(
            organization_id=int(organization["organization_id"]),
            knowledge_document_id=int(document["knowledge_document_id"]),
            actor_user=admin,
            actor="admin",
            file_name="procedura_umowy_v2.txt",
            file_bytes=(
                "Etap 1: przygotuj brief.\n"
                "Etap 2: potwierdz budzet i termin platnosci.\n"
                "Etap 3: wyslij projekt.\n"
                "Etap 4: zapisz ustalenia w CRM."
            ).encode("utf-8"),
            mime_type="text/plain",
        )
        self.services["knowledge_service"].process_pending_jobs(limit=4)

        headers = {"Content-Type": "application/json"}
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "admin", "password": "Admin1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)

        response, payload = self._request(
            "GET",
            (
                f"/api/knowledge/documents/{document['knowledge_document_id']}/compare"
                f"?organization_id={organization['organization_id']}&left_version=2&right_version=1"
            ),
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200)
        compare_payload = json.loads(payload.decode("utf-8"))
        self.assertEqual(compare_payload["left_version"]["version_number"], 2)
        self.assertEqual(compare_payload["right_version"]["version_number"], 1)
        self.assertEqual(compare_payload["target_version"]["version_number"], 2)
        self.assertEqual(compare_payload["base_version"]["version_number"], 1)
        self.assertGreaterEqual(compare_payload["summary"]["changed_block_count"], 1)
        self.assertEqual(compare_payload["summary"]["comparison_basis"], "older_to_newer")
        self.assertIn("overview", compare_payload["change_summary"])
        self.assertTrue(compare_payload["side_by_side_rows"])
        self.assertTrue(any(item["type"] == "changed" for item in compare_payload["side_by_side_rows"]))
        self.assertTrue(any(item["type"] == "added" for item in compare_payload["blocks"]))
        self.assertTrue(any(item["type"] == "removed" for item in compare_payload["blocks"]))

    def test_knowledge_document_preview_file_endpoint_returns_inline_content(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {"name": "Klient Preview", "slug": "klient-preview", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        document = self.services["knowledge_service"].add_document(
            organization_id=int(organization["organization_id"]),
            title="Instrukcja zespolu",
            actor_user=admin,
            actor="admin",
            file_name="instrukcja_zespolu.txt",
            content_text="Krok 1: zapisz ustalenia.\nKrok 2: potwierdz odbior.",
            library_path="Procedury/Zespol",
            is_downloadable=True,
            use_in_assistant=True,
        )
        self.services["knowledge_service"].process_pending_jobs(limit=2)

        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "admin", "password": "Admin1234"}),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)

        response, payload = self._request(
            "GET",
            f"/api/knowledge/documents/{document['knowledge_document_id']}/preview-file?organization_id={organization['organization_id']}",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200)
        self.assertIn("text/plain", response.getheader("Content-Type") or "")
        self.assertIn("Krok 1", payload.decode("utf-8"))
        self.assertIsNone(response.getheader("Content-Disposition"))

    def test_knowledge_comment_endpoint_allows_reader_but_mark_official_requires_manage(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {"name": "Klient Komentarze ACL", "slug": "klient-komentarze-acl", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        self.services["auth_service"].create_user(
            {
                "login": "knowledge_reader",
                "display_name": "Knowledge Reader",
                "password": "Reader1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
                "capabilities": ["knowledge.read"],
                "can_upload_knowledge": 0,
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        document = self.services["knowledge_service"].add_document(
            organization_id=int(organization["organization_id"]),
            title="Instrukcja czytelnika",
            actor_user=admin,
            actor="admin",
            file_name="instrukcja_czytelnika.txt",
            content_text="Wersja pierwsza instrukcji dla zespolu.",
            library_path="Procedury/Czytelnicy",
            is_downloadable=True,
            use_in_assistant=True,
        )
        self.services["knowledge_service"].process_pending_jobs(limit=2)

        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "knowledge_reader", "password": "Reader1234"}),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)

        response, payload = self._request(
            "POST",
            f"/api/knowledge/documents/{document['knowledge_document_id']}/comments?organization_id={organization['organization_id']}",
            body=json.dumps({"note_text": "Potwierdzam, ze dokument jest czytelny."}),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))
        comment_payload = json.loads(payload.decode("utf-8"))
        self.assertEqual(comment_payload["comment_summary"]["comment_count"], 1)
        self.assertEqual(comment_payload["comments"][0]["author_label"], "Knowledge Reader")

        response, payload = self._request(
            "POST",
            f"/api/knowledge/documents/{document['knowledge_document_id']}/mark-official-version?organization_id={organization['organization_id']}",
            body=json.dumps({"version_number": 1}),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 403)
        error_payload = json.loads(payload.decode("utf-8"))
        self.assertIn("zarz", error_payload["error"].lower())

    def test_knowledge_documents_endpoint_exposes_activity_feed_and_mark_seen(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {"name": "Klient Activity", "slug": "klient-activity", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        document = self.services["knowledge_service"].add_document(
            organization_id=int(organization["organization_id"]),
            title="Instrukcja obiegu zmian",
            actor_user=admin,
            actor="admin",
            file_name="instrukcja_zmian.txt",
            content_text="Wersja pierwsza. Zmiany akceptuje kierownik operacyjny.",
            library_path="Procedury/Operacje",
            is_downloadable=True,
            use_in_assistant=True,
        )
        self.services["knowledge_service"].process_pending_jobs(limit=2)
        self.services["knowledge_service"].replace_document_file(
            organization_id=int(organization["organization_id"]),
            knowledge_document_id=int(document["knowledge_document_id"]),
            actor_user=admin,
            actor="admin",
            file_name="instrukcja_zmian_v2.txt",
            file_bytes=b"Wersja druga. Zmiany akceptuje dyrektor finansowy.",
            mime_type="text/plain",
        )
        self.services["knowledge_service"].process_pending_jobs(limit=2)
        self.services["knowledge_service"].add_document_comment(
            organization_id=int(organization["organization_id"]),
            knowledge_document_id=int(document["knowledge_document_id"]),
            note_text="Prosze oznaczyc wersje obowiazujaca po akceptacji zarzadu.",
            actor_user=admin,
            actor="admin",
            version_number=2,
            annotation_kind="annotation",
        )

        cookie = self._login_default_admin()
        response, payload = self._request(
            "GET",
            f"/api/knowledge/documents?organization_id={organization['organization_id']}",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        list_payload = json.loads(payload.decode("utf-8"))
        self.assertIn("activity_feed", list_payload)
        self.assertIn("activity_summary", list_payload)
        self.assertEqual(list_payload["documents"][0]["workflow_status"], "official_missing")
        self.assertEqual(list_payload["documents"][0]["business_status"], "roboczy")
        self.assertEqual(list_payload["activity_summary"]["pending_review_count"], 1)
        self.assertGreaterEqual(list_payload["activity_summary"]["unread_count"], 1)
        self.assertTrue(
            any(item["event_type"] == "knowledge_document_comment_added" for item in list_payload["activity_feed"])
        )
        self.assertTrue(any(item["is_unread"] for item in list_payload["activity_feed"]))

        response, payload = self._request(
            "POST",
            f"/api/knowledge/activity/mark-seen?organization_id={organization['organization_id']}",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        seen_payload = json.loads(payload.decode("utf-8"))
        self.assertEqual(seen_payload["module_key"], "knowledge")
        self.assertEqual(seen_payload["unread_count"], 0)

        response, payload = self._request(
            "GET",
            f"/api/knowledge/documents?organization_id={organization['organization_id']}",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        list_after_seen = json.loads(payload.decode("utf-8"))
        self.assertEqual(list_after_seen["activity_summary"]["unread_count"], 0)
        self.assertFalse(any(item["is_unread"] for item in list_after_seen["activity_feed"]))

    def test_knowledge_document_decision_endpoint_updates_workflow_and_requires_reason(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {"name": "Klient HTTP Decyzje", "slug": "klient-http-decyzje", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        owner = self.services["auth_service"].create_user(
            {
                "login": "http_owner",
                "display_name": "HTTP Owner",
                "password": "Http1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
                "capabilities": ["knowledge.read"],
                "can_upload_knowledge": 0,
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        reviewer = self.services["auth_service"].create_user(
            {
                "login": "http_reviewer",
                "display_name": "HTTP Reviewer",
                "password": "Http1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
                "capabilities": ["knowledge.read"],
                "can_upload_knowledge": 0,
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        approver = self.services["auth_service"].create_user(
            {
                "login": "http_approver",
                "display_name": "HTTP Approver",
                "password": "Http1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
                "capabilities": ["knowledge.read"],
                "can_upload_knowledge": 0,
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        document = self.services["knowledge_service"].add_document(
            organization_id=int(organization["organization_id"]),
            title="Dokument HTTP decyzji",
            actor_user=admin,
            actor="admin",
            file_name="dokument_http_decyzji.txt",
            content_text="Dokument przechodzi przez review i akceptacje.",
            library_path="Procedury/HTTP",
            is_downloadable=True,
            use_in_assistant=True,
        )
        self.services["knowledge_service"].process_pending_jobs(limit=2)
        self.services["knowledge_service"].update_document_metadata(
            organization_id=int(organization["organization_id"]),
            knowledge_document_id=int(document["knowledge_document_id"]),
            actor_user=admin,
            actor="admin",
            owner_user_id=int(owner["user_id"]),
            reviewer_user_id=int(reviewer["user_id"]),
            approver_user_id=int(approver["user_id"]),
        )
        owner_cookie = self._login("http_owner", "Http1234")

        response, payload = self._request(
            "POST",
            f"/api/knowledge/documents/{document['knowledge_document_id']}/decision?organization_id={organization['organization_id']}",
            body=json.dumps({"action": "send_for_review", "reason": "   "}),
            headers={"Cookie": owner_cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 400)
        self.assertIn("powod tej decyzji", payload.decode("utf-8").lower())

        response, payload = self._request(
            "POST",
            f"/api/knowledge/documents/{document['knowledge_document_id']}/decision?organization_id={organization['organization_id']}",
            body=json.dumps({"action": "send_for_review", "reason": "Dokument jest gotowy do review."}),
            headers={"Cookie": owner_cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        decision_payload = json.loads(payload.decode("utf-8"))
        self.assertEqual(decision_payload["business_status"], "do_sprawdzenia")
        self.assertTrue(
            any(item["event_type"] == "knowledge_document_decision_taken" for item in decision_payload["audit_events"])
        )
        self.assertTrue(
            any(item["event_type"] == "knowledge_document_comment_added" for item in decision_payload["audit_events"])
        )

        reviewer_cookie = self._login("http_reviewer", "Http1234")
        response, payload = self._request(
            "POST",
            f"/api/knowledge/documents/{document['knowledge_document_id']}/decision?organization_id={organization['organization_id']}",
            body=json.dumps({"action": "send_for_approval", "reason": "Review zakonczony, przekazuje dalej."}),
            headers={"Cookie": reviewer_cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        approval_payload = json.loads(payload.decode("utf-8"))
        self.assertEqual(approval_payload["business_status"], "do_akceptacji")

    def test_knowledge_document_tasks_endpoint_creates_linked_task_and_audit(self) -> None:
        organization, owner, other = self._create_manager_assistant_org_for_http()
        admin = self.services["auth_service"].list_users()[0]
        document = self.services["knowledge_service"].add_document(
            organization_id=int(organization["organization_id"]),
            title="Dokument do zadania",
            actor_user=admin,
            actor="admin",
            file_name="dokument_do_zadania.txt",
            content_text="Ten dokument wymaga dalszej pracy operacyjnej.",
            library_path="Operacje/Zadania",
            is_downloadable=True,
            use_in_assistant=True,
        )
        self.services["knowledge_service"].process_pending_jobs(limit=2)
        self.services["knowledge_service"].update_document_metadata(
            organization_id=int(organization["organization_id"]),
            knowledge_document_id=int(document["knowledge_document_id"]),
            actor_user=admin,
            actor="admin",
            owner_user_id=int(owner["user_id"]),
        )
        owner_cookie = self._login("powiazania-olga", "1234")

        response, payload = self._request(
            "POST",
            f"/api/knowledge/documents/{document['knowledge_document_id']}/tasks?organization_id={organization['organization_id']}",
            body=json.dumps(
                {
                    "title": "Przygotuj poprawki do dokumentu",
                    "description": "Sprawdz uwagi i przygotuj nastepna wersje do review.",
                    "priority": "wysoki",
                    "visibility_scope": "organizacja",
                    "assigned_user_id": int(other["user_id"]),
                }
            ),
            headers={"Cookie": owner_cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))
        task_payload = json.loads(payload.decode("utf-8"))
        self.assertEqual(task_payload["task"]["title"], "Przygotuj poprawki do dokumentu")
        self.assertIn(int(document["knowledge_document_id"]), task_payload["task"]["linked_knowledge_document_ids"])
        self.assertTrue(
            any(item["event_type"] == "knowledge_document_task_created" for item in task_payload["document"]["audit_events"])
        )

    def test_knowledge_preview_file_requires_download_capability(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {"name": "Klient Preview ACL", "slug": "klient-preview-acl", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        self.services["auth_service"].create_user(
            {
                "login": "preview_reader",
                "display_name": "Preview Reader",
                "password": "Preview1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
                "capabilities": ["knowledge.read"],
                "can_upload_knowledge": 0,
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        document = self.services["knowledge_service"].add_document(
            organization_id=int(organization["organization_id"]),
            title="Instrukcja do podgladu",
            actor_user=admin,
            actor="admin",
            file_name="instrukcja_podglad.txt",
            content_text="Linia 1.\nLinia 2.",
            library_path="Procedury/Preview",
            is_downloadable=True,
            use_in_assistant=False,
        )
        self.services["knowledge_service"].process_pending_jobs(limit=2)

        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "preview_reader", "password": "Preview1234"}),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)

        response, payload = self._request(
            "GET",
            f"/api/knowledge/documents/{document['knowledge_document_id']}/preview-file?organization_id={organization['organization_id']}",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 403)
        error_payload = json.loads(payload.decode("utf-8"))
        self.assertIn("podgladu", error_payload["error"].lower())

    def test_knowledge_document_bulk_endpoint_updates_selected_records(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {"name": "Klient Bulk", "slug": "klient-bulk", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        document_one = self.services["knowledge_service"].add_document(
            organization_id=int(organization["organization_id"]),
            title="Wzor oferty",
            actor_user=admin,
            actor="admin",
            file_name="wzor_oferty.txt",
            content_text="Sekcja 1: dane klienta.\nSekcja 2: zakres uslugi.",
            library_path="Sprzedaz/Robocze",
            is_downloadable=True,
            use_in_assistant=True,
        )
        document_two = self.services["knowledge_service"].add_document(
            organization_id=int(organization["organization_id"]),
            title="Wzor zamowienia",
            actor_user=admin,
            actor="admin",
            file_name="wzor_zamowienia.txt",
            content_text="Sekcja 1: projekt.\nSekcja 2: akceptacja budzetu.",
            library_path="Sprzedaz/Robocze",
            is_downloadable=True,
            use_in_assistant=False,
        )
        self.services["knowledge_service"].process_pending_jobs(limit=4)

        headers = {"Content-Type": "application/json"}
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "admin", "password": "Admin1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)

        response, payload = self._request(
            "POST",
            f"/api/knowledge/documents/bulk?organization_id={organization['organization_id']}",
            body=json.dumps(
                {
                    "action": "move_folder",
                    "knowledge_document_ids": [
                        int(document_one["knowledge_document_id"]),
                        int(document_two["knowledge_document_id"]),
                    ],
                    "library_path": "Sprzedaz/Aktualne",
                }
            ),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200)
        bulk_payload = json.loads(payload.decode("utf-8"))
        self.assertEqual(bulk_payload["action"], "move_folder")
        self.assertEqual(bulk_payload["succeeded_count"], 2)
        self.assertEqual(bulk_payload["failed_count"], 0)
        self.assertEqual(bulk_payload["target_library_path"], "Sprzedaz/Aktualne")

        response, payload = self._request(
            "GET",
            f"/api/knowledge/documents?organization_id={organization['organization_id']}",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200)
        list_payload = json.loads(payload.decode("utf-8"))
        updated_documents = {
            int(item["knowledge_document_id"]): item["library_path"]
            for item in list_payload["documents"]
            if int(item["knowledge_document_id"])
            in {int(document_one["knowledge_document_id"]), int(document_two["knowledge_document_id"])}
        }
        self.assertEqual(updated_documents[int(document_one["knowledge_document_id"])], "Sprzedaz/Aktualne")
        self.assertEqual(updated_documents[int(document_two["knowledge_document_id"])], "Sprzedaz/Aktualne")

    def test_knowledge_bulk_endpoint_requires_manage_capability(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {"name": "Klient Bulk ACL", "slug": "klient-bulk-acl", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        self.services["auth_service"].create_user(
            {
                "login": "bulk_operator",
                "display_name": "Bulk Operator",
                "password": "Bulk1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
                "capabilities": [
                    "knowledge.read",
                    "knowledge.download",
                    "knowledge.upload",
                ],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        document = self.services["knowledge_service"].add_document(
            organization_id=int(organization["organization_id"]),
            title="Wzor operacyjny",
            actor_user=admin,
            actor="admin",
            file_name="wzor_operacyjny.txt",
            content_text="Punkt 1: przygotowanie.\nPunkt 2: realizacja.",
            library_path="Operacje/Robocze",
            is_downloadable=True,
            use_in_assistant=True,
        )
        self.services["knowledge_service"].process_pending_jobs(limit=2)

        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "bulk_operator", "password": "Bulk1234"}),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)

        response, payload = self._request(
            "POST",
            f"/api/knowledge/documents/bulk?organization_id={organization['organization_id']}",
            body=json.dumps(
                {
                    "action": "archive",
                    "knowledge_document_ids": [int(document["knowledge_document_id"])],
                }
            ),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 403)
        error_payload = json.loads(payload.decode("utf-8"))
        self.assertIn("nie ma uprawnienia", error_payload["error"].lower())

    def test_public_telegram_webhook_creates_invoice_and_stores_real_file(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {
                "name": "Telegram Klient",
                "slug": "telegram-klient",
                "telegram_chat_id": "-100123",
                "telegram_chat_name": "Telegram Klient - dokumenty",
                "is_active": 1,
            },
            actor_user=admin,
            actor_login="admin",
        )
        self.services["auth_service"].create_user(
            {
                "login": "olga",
                "display_name": "Olga",
                "telegram_user_id": "900100",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )

        adapter = self.services["invoice_service"].telegram_adapter
        adapter.bot_token = "telegram-token"
        adapter.webhook_secret = "sekret-webhooka"
        adapter._download_file = lambda file_id, suggested_file_name: {
            "file_name": "faktura_telegram.pdf",
            "content": (
                "%PDF-1.4\n"
                "Numer faktury: FV/TG/77/04/2026\n"
                "NIP wystawcy: 9988877766\n"
                "Data wystawienia: 08.04.2026\n"
                "Data sprzedaży: 08.04.2026\n"
                "Kwota brutto: 442,80 PLN\n"
                "Wystawca: Telegram Dostawca Sp. z o.o.\n"
            ).encode("utf-8"),
            "telegram_file_path": "documents/test/faktura_telegram.pdf",
        }

        webhook_payload = {
            "update_id": 101,
            "message": {
                "message_id": 77,
                "date": 1775671200,
                "caption": "Nowa faktura do systemu",
                "chat": {"id": -100123, "type": "supergroup", "title": "Telegram Klient - dokumenty"},
                "from": {"id": 900100, "username": "olga_telegram", "first_name": "Olga"},
                "document": {
                    "file_id": "plik-telegram-1",
                    "file_unique_id": "unikat-1",
                    "file_name": "faktura_telegram.pdf",
                    "mime_type": "application/pdf",
                },
            },
        }

        response, payload = self._request(
            "POST",
            "/api/telegram/webhook/sekret-webhooka",
            body=json.dumps(webhook_payload),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200)
        webhook_result = json.loads(payload.decode("utf-8"))
        self.assertTrue(webhook_result["ok"])

        detail = self.services["invoice_service"].get_invoice_detail(webhook_result["invoice_id"])
        self.assertIsNotNone(detail)
        assert detail is not None

        invoice = detail["invoice"]
        self.assertEqual(invoice["source"], "TELEGRAM")
        self.assertEqual(invoice["organization_slug"], "telegram-klient")
        self.assertEqual(invoice["storage_backend"], "lokalny")
        self.assertEqual(invoice["invoice_number"], "FV/TG/77/04/2026")
        self.assertEqual(invoice["issuer_nip"], "9988877766")
        self.assertEqual(invoice["issue_date"], "2026-04-08")
        self.assertEqual(invoice["sale_date"], "2026-04-08")
        self.assertEqual(invoice["gross_amount"], 442.8)
        self.assertEqual(invoice["currency"], "PLN")
        self.assertTrue(invoice["file_storage_key"].startswith("organizacje/telegram-klient/TELEGRAM/"))
        self.assertTrue(invoice["file_link"].endswith(".pdf"))
        self.assertIn("Numer faktury: FV/TG/77/04/2026", invoice["ocr_raw_text"])
        self.assertEqual(detail["source_trace"]["linked_user"]["login"], "olga")
        self.assertTrue(any(item["event_type"] == "invoice_created" and item["actor"] == "Olga" for item in detail["history"]))

        file_relative = invoice["file_storage_key"]
        stored_file = DOCUMENTS_DIR / Path(file_relative)
        self.assertTrue(stored_file.exists())
        self.assertIn(b"FV/TG/77/04/2026", stored_file.read_bytes())

    def test_public_telegram_webhook_can_resolve_organization_by_chat_id(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {
                "name": "Chat Klienta",
                "slug": "chat-klienta",
                "telegram_chat_id": "-100555",
                "telegram_chat_name": "Chat Klienta - faktury",
                "is_active": 1,
            },
            actor_user=admin,
            actor_login="admin",
        )

        adapter = self.services["invoice_service"].telegram_adapter
        adapter.bot_token = "telegram-token"
        adapter.webhook_secret = "sekret-webhooka"
        adapter._download_file = lambda file_id, suggested_file_name: {
            "file_name": "chat_klienta.pdf",
            "content": (
                "%PDF-1.4\n"
                "Numer faktury: CK/88/04/2026\n"
                "NIP wystawcy: 1122334455\n"
                "Kwota brutto: 912,30 PLN\n"
            ).encode("utf-8"),
            "telegram_file_path": "documents/test/chat_klienta.pdf",
        }

        webhook_payload = {
            "update_id": 202,
            "message": {
                "message_id": 88,
                "date": 1775671800,
                "caption": "Faktura z czatu klienta",
                "chat": {"id": -100555, "type": "supergroup", "title": "Chat Klienta - faktury"},
                "from": {"id": 777000, "username": "niepowiazany_uzytkownik", "first_name": "Marta"},
                "document": {
                    "file_id": "plik-telegram-2",
                    "file_unique_id": "unikat-2",
                    "file_name": "chat_klienta.pdf",
                    "mime_type": "application/pdf",
                },
            },
        }

        response, payload = self._request(
            "POST",
            "/api/telegram/webhook/sekret-webhooka",
            body=json.dumps(webhook_payload),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200)
        webhook_result = json.loads(payload.decode("utf-8"))

        detail = self.services["invoice_service"].get_invoice_detail(webhook_result["invoice_id"])
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail["invoice"]["organization_id"], organization["organization_id"])
        self.assertEqual(detail["invoice"]["organization_slug"], "chat-klienta")
        self.assertEqual(detail["invoice"]["invoice_number"], "CK/88/04/2026")
        self.assertEqual(detail["invoice"]["issuer_nip"], "1122334455")
        self.assertEqual(detail["invoice"]["gross_amount"], 912.3)
        self.assertIsNone(detail["source_trace"]["linked_user"])

    def test_public_telegram_webhook_rejects_organization_with_non_telegram_provider(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {
                "name": "Slack Chat Klienta",
                "slug": "slack-chat-klienta",
                "communication_provider": "slack",
                "communication_config": {
                    "telegram": {
                        "chat_id": "-100556",
                        "chat_name": "Slack Chat Klienta - dokumenty",
                    },
                    "slack": {
                        "workspace_name": "Casi Ops",
                        "channel_id": "C0222222222",
                        "channel_name": "#slack-chat-klienta",
                    },
                },
                "is_active": 1,
            },
            actor_user=admin,
            actor_login="admin",
        )
        self.services["auth_service"].create_user(
            {
                "login": "slack_olga",
                "display_name": "Slack Olga",
                "telegram_user_id": "900556",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )

        adapter = self.services["invoice_service"].telegram_adapter
        adapter.bot_token = "telegram-token"
        adapter.webhook_secret = "sekret-webhooka"
        adapter._download_file = lambda file_id, suggested_file_name: {
            "file_name": "slack_chat_klienta.pdf",
            "content": b"%PDF-1.4\nNumer faktury: CK/89/04/2026\n",
            "telegram_file_path": "documents/test/slack_chat_klienta.pdf",
        }

        webhook_payload = {
            "update_id": 203,
            "message": {
                "message_id": 89,
                "date": 1775671800,
                "chat": {"id": -100556, "type": "supergroup", "title": "Slack Chat Klienta - dokumenty"},
                "from": {"id": 900556, "username": "slack_olga", "first_name": "Olga"},
                "document": {
                    "file_id": "plik-telegram-3",
                    "file_unique_id": "unikat-3",
                    "file_name": "slack_chat_klienta.pdf",
                    "mime_type": "application/pdf",
                },
            },
        }

        response, payload = self._request(
            "POST",
            "/api/telegram/webhook/sekret-webhooka",
            body=json.dumps(webhook_payload),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 400)
        error_payload = json.loads(payload.decode("utf-8"))
        self.assertIn("inny komunikator", error_payload["error"].lower())

    def test_public_telegram_webhook_marks_invoice_for_verification_when_ocr_fails(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {
                "name": "Skan Telegram",
                "slug": "skan-telegram",
                "telegram_chat_id": "-100777",
                "telegram_chat_name": "Skan Telegram - dokumenty",
                "is_active": 1,
            },
            actor_user=admin,
            actor_login="admin",
        )
        self.services["auth_service"].create_user(
            {
                "login": "maria",
                "display_name": "Maria",
                "telegram_user_id": "901200",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )

        adapter = self.services["invoice_service"].telegram_adapter
        adapter.bot_token = "telegram-token"
        adapter.webhook_secret = "sekret-webhooka"
        adapter._download_file = lambda file_id, suggested_file_name: {
            "file_name": "skan_faktury.jpg",
            "content": b"\x00\x01\x02\x03\x04\x05",
            "telegram_file_path": "documents/test/skan_faktury.jpg",
        }

        webhook_payload = {
            "update_id": 303,
            "message": {
                "message_id": 99,
                "date": 1775672400,
                "caption": "Papierowa faktura do sprawdzenia",
                "chat": {"id": -100777, "type": "supergroup", "title": "Skan Telegram - dokumenty"},
                "from": {"id": 901200, "username": "maria_telegram", "first_name": "Maria"},
                "photo": [
                    {"file_id": "photo-small", "file_unique_id": "foto-1", "file_size": 1280},
                    {"file_id": "photo-big", "file_unique_id": "foto-2", "file_size": 4096},
                ],
            },
        }

        response, payload = self._request(
            "POST",
            "/api/telegram/webhook/sekret-webhooka",
            body=json.dumps(webhook_payload),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200)
        webhook_result = json.loads(payload.decode("utf-8"))

        detail = self.services["invoice_service"].get_invoice_detail(webhook_result["invoice_id"])
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail["invoice"]["organization_id"], organization["organization_id"])
        self.assertEqual(detail["invoice"]["status"], "weryfikacja")
        self.assertEqual(detail["invoice"]["duplicate_type"], "brak")
        self.assertEqual(
            detail["invoice"]["flag_reason"],
            "Dokument z Telegrama wymaga weryfikacji, ponieważ OCR nie odczytał kluczowych pól faktury.",
        )
        self.assertIn("Nie udało się odczytać treści dokumentu lokalnym OCR.", detail["invoice"]["ocr_raw_text"])


    def test_public_slack_webhook_creates_invoice_and_stores_real_file(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {
                "name": "Slack Klient",
                "slug": "slack-klient",
                "communication_provider": "slack",
                "communication_config": {
                    "slack": {
                        "workspace_name": "Casi Ops",
                        "channel_id": "C0222222222",
                        "channel_name": "#faktury-slack-klient",
                    }
                },
                "is_active": 1,
            },
            actor_user=admin,
            actor_login="admin",
        )

        adapter = self.services["invoice_service"].slack_adapter
        adapter.bot_token = "xoxb-test"
        adapter.signing_secret = "slack-signing-secret"
        adapter.verify_request = lambda headers, raw_body: True
        adapter._fetch_file_info = lambda file_id: {
            "id": file_id,
            "name": "faktura_slack.pdf",
            "mimetype": "application/pdf",
            "url_private_download": "https://files.slack.test/faktura_slack.pdf",
            "permalink": "https://slack.test/files/F111",
            "created": 1775673000,
            "user": "U123456",
        }
        adapter._download_private_file = lambda download_url, suggested_file_name: {
            "file_name": suggested_file_name,
            "content": (
                "%PDF-1.4\n"
                "Numer faktury: FV/SL/77/04/2026\n"
                "NIP wystawcy: 6655443322\n"
                "Data wystawienia: 08.04.2026\n"
                "Data sprzedazy: 08.04.2026\n"
                "Kwota brutto: 712,40 PLN\n"
                "Wystawca: Slack Dostawca Sp. z o.o.\n"
            ).encode("utf-8"),
        }

        webhook_payload = {
            "type": "event_callback",
            "team_id": "T024BE7LD",
            "api_app_id": "A024BE7LH",
            "event_id": "Ev04M00AAA",
            "event": {
                "type": "message",
                "subtype": "file_share",
                "channel": "C0222222222",
                "user": "U123456",
                "ts": "1775673000.000200",
                "files": [{"id": "F111"}],
            },
        }

        response, payload = self._request(
            "POST",
            "/api/slack/events",
            body=json.dumps(webhook_payload),
            headers={
                "Content-Type": "application/json",
                "X-Slack-Signature": "v0=test",
                "X-Slack-Request-Timestamp": "1775673000",
            },
        )
        self.assertEqual(response.status, 200)
        webhook_result = json.loads(payload.decode("utf-8"))
        self.assertTrue(webhook_result["ok"])

        detail = self.services["invoice_service"].get_invoice_detail(webhook_result["invoice_id"])
        self.assertIsNotNone(detail)
        assert detail is not None

        invoice = detail["invoice"]
        self.assertEqual(invoice["source"], "SLACK")
        self.assertEqual(invoice["organization_id"], organization["organization_id"])
        self.assertEqual(invoice["organization_slug"], "slack-klient")
        self.assertEqual(invoice["storage_backend"], "lokalny")
        self.assertEqual(invoice["invoice_number"], "FV/SL/77/04/2026")
        self.assertEqual(invoice["issuer_nip"], "6655443322")
        self.assertEqual(invoice["issue_date"], "2026-04-08")
        self.assertEqual(invoice["sale_date"], "2026-04-08")
        self.assertEqual(invoice["gross_amount"], 712.4)
        self.assertEqual(invoice["currency"], "PLN")
        self.assertTrue(invoice["file_storage_key"].startswith("organizacje/slack-klient/SLACK/"))
        self.assertIn("Numer faktury: FV/SL/77/04/2026", invoice["ocr_raw_text"])
        self.assertIsNone(detail["source_trace"]["linked_user"])

        file_relative = invoice["file_storage_key"]
        stored_file = DOCUMENTS_DIR / Path(file_relative)
        self.assertTrue(stored_file.exists())
        self.assertIn(b"FV/SL/77/04/2026", stored_file.read_bytes())

    def test_public_slack_webhook_handles_url_verification(self) -> None:
        adapter = self.services["invoice_service"].slack_adapter
        adapter.bot_token = "xoxb-test"
        adapter.signing_secret = "slack-signing-secret"
        adapter.verify_request = lambda headers, raw_body: True

        response, payload = self._request(
            "POST",
            "/api/slack/events",
            body=json.dumps({"type": "url_verification", "challenge": "challenge-token-123"}),
            headers={
                "Content-Type": "application/json",
                "X-Slack-Signature": "v0=test",
                "X-Slack-Request-Timestamp": "1775673000",
            },
        )
        self.assertEqual(response.status, 200)
        self.assertEqual(payload.decode("utf-8"), "challenge-token-123")
        self.assertIn("text/plain", response.getheader("Content-Type", ""))

    def test_organization_admin_can_edit_own_organization_but_cannot_create_new_one(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {
                "name": "Klient Delta",
                "slug": "klient-delta",
                "telegram_chat_name": "Delta - dokumenty",
                "is_active": 1,
            },
            actor_user=admin,
            actor_login="admin",
        )
        self.services["auth_service"].create_user(
            {
                "login": "delta-admin",
                "display_name": "Delta Admin",
                "password": "1234",
                "role": "organization_admin",
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )

        headers = {"Content-Type": "application/json"}
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "delta-admin", "password": "1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)

        response, payload = self._request("GET", "/api/organizations", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        organizations = json.loads(payload.decode("utf-8"))
        self.assertEqual(len(organizations), 1)
        self.assertEqual(organizations[0]["slug"], "klient-delta")

        response, payload = self._request(
            "PATCH",
            f"/api/organizations/{organization['organization_id']}",
            body=json.dumps(
                {
                    "telegram_chat_name": "Delta - nowy kanal",
                    "module_shortcuts": {
                        "knowledge": "Ctrl+2",
                        "tasks": "Alt+3",
                    },
                }
            ),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200)
        updated = json.loads(payload.decode("utf-8"))
        self.assertEqual(updated["telegram_chat_name"], "Delta - nowy kanal")
        self.assertEqual(
            updated["module_shortcuts"],
            {
                "knowledge": "Ctrl+2",
                "tasks": "Alt+3",
            },
        )

        response, payload = self._request(
            "POST",
            "/api/organizations",
            body=json.dumps({"name": "Nie wolno", "slug": "nie-wolno", "is_active": 1}),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 403)
        self.assertIn("Wlasciciel systemu", payload.decode("utf-8"))

    def test_same_organization_users_share_one_note(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization_alpha = self.services["organization_service"].create_organization(
            {"name": "Klient Alpha", "slug": "klient-alpha", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        organization_beta = self.services["organization_service"].create_organization(
            {"name": "Klient Beta", "slug": "klient-beta", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        self.services["auth_service"].create_user(
            {
                "login": "alpha-jeden",
                "display_name": "Alpha Jeden",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization_alpha["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        self.services["auth_service"].create_user(
            {
                "login": "alpha-dwa",
                "display_name": "Alpha Dwa",
                "password": "1234",
                "role": "guest",
                "is_active": 1,
                "organization_id": organization_alpha["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        self.services["auth_service"].create_user(
            {
                "login": "beta-jeden",
                "display_name": "Beta Jeden",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization_beta["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )

        headers = {"Content-Type": "application/json"}
        response, _ = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "alpha-jeden", "password": "1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        alpha_cookie = response.getheader("Set-Cookie")
        self.assertTrue(alpha_cookie)

        response, payload = self._request("GET", "/api/organization-shared-note", headers={"Cookie": alpha_cookie})
        self.assertEqual(response.status, 200)
        note = json.loads(payload.decode("utf-8"))
        self.assertEqual(note["shared_note_text"], "")

        response, payload = self._request(
            "PATCH",
            "/api/organization-shared-note",
            body=json.dumps({"shared_note_text": "Sprawdzamy dzis korekty od dostawcy Alfa."}),
            headers={"Cookie": alpha_cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200)
        updated = json.loads(payload.decode("utf-8"))
        self.assertEqual(updated["organization_id"], organization_alpha["organization_id"])
        self.assertEqual(updated["shared_note_text"], "Sprawdzamy dzis korekty od dostawcy Alfa.")
        self.assertEqual(updated["shared_note_updated_by_name"], "Alpha Jeden")

        response, _ = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "alpha-dwa", "password": "1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        alpha_second_cookie = response.getheader("Set-Cookie")
        self.assertTrue(alpha_second_cookie)

        response, payload = self._request(
            "GET",
            f"/api/organization-shared-note?organization_id={organization_beta['organization_id']}",
            headers={"Cookie": alpha_second_cookie},
        )
        self.assertEqual(response.status, 200)
        alpha_shared = json.loads(payload.decode("utf-8"))
        self.assertEqual(alpha_shared["organization_id"], organization_alpha["organization_id"])
        self.assertEqual(alpha_shared["shared_note_text"], "Sprawdzamy dzis korekty od dostawcy Alfa.")

        response, _ = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "beta-jeden", "password": "1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        beta_cookie = response.getheader("Set-Cookie")
        self.assertTrue(beta_cookie)

        response, payload = self._request("GET", "/api/organization-shared-note", headers={"Cookie": beta_cookie})
        self.assertEqual(response.status, 200)
        beta_note = json.loads(payload.decode("utf-8"))
        self.assertEqual(beta_note["organization_id"], organization_beta["organization_id"])
        self.assertEqual(beta_note["shared_note_text"], "")

    def test_personal_note_is_private_per_user(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {"name": "Klient Personal", "slug": "klient-personal", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        self.services["auth_service"].create_user(
            {
                "login": "personal-jeden",
                "display_name": "Personal Jeden",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        self.services["auth_service"].create_user(
            {
                "login": "personal-dwa",
                "display_name": "Personal Dwa",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )

        headers = {"Content-Type": "application/json"}
        response, _ = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "personal-jeden", "password": "1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        first_cookie = response.getheader("Set-Cookie")
        self.assertTrue(first_cookie)

        response, payload = self._request(
            "PATCH",
            "/api/user-personal-note",
            body=json.dumps({"personal_note_text": "Moja prywatna lista spraw."}),
            headers={"Cookie": first_cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200)
        first_note = json.loads(payload.decode("utf-8"))
        self.assertEqual(first_note["personal_note_text"], "Moja prywatna lista spraw.")
        self.assertIsNotNone(first_note["personal_note_updated_at"])

        response, payload = self._request("GET", "/api/user-personal-note", headers={"Cookie": first_cookie})
        self.assertEqual(response.status, 200)
        same_user_note = json.loads(payload.decode("utf-8"))
        self.assertEqual(same_user_note["personal_note_text"], "Moja prywatna lista spraw.")

        response, _ = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "personal-dwa", "password": "1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        second_cookie = response.getheader("Set-Cookie")
        self.assertTrue(second_cookie)

        response, payload = self._request("GET", "/api/user-personal-note", headers={"Cookie": second_cookie})
        self.assertEqual(response.status, 200)
        second_note = json.loads(payload.decode("utf-8"))
        self.assertEqual(second_note["personal_note_text"], "")

    def test_only_decision_roles_can_confirm_duplicate(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {"name": "Klient Duplikat", "slug": "klient-duplikat", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        self.services["auth_service"].create_user(
            {
                "login": "duplikat-operator",
                "display_name": "Duplikat Operator",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        self.services["auth_service"].create_user(
            {
                "login": "duplikat-koordynator",
                "display_name": "Duplikat Koordynator",
                "password": "1234",
                "role": "coordinator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )

        self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-04-08",
                "source": "EMAIL",
                "file_name": "duplikat_1.pdf",
                "document_type": "pdf",
                "invoice_number": "DUP/1/04/2026",
                "issuer_nip": "9988776655",
                "issuer_name": "Duplikat Sp. z o.o.",
                "issue_date": "2026-04-08",
                "sale_date": "2026-04-08",
                "gross_amount": 123.0,
                "currency": "PLN",
                "status": "nowa",
            },
            actor="test",
            organization_id=int(organization["organization_id"]),
        )
        duplicate = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-04-09",
                "source": "EMAIL",
                "file_name": "duplikat_2.pdf",
                "document_type": "pdf",
                "invoice_number": "DUP/1/04/2026",
                "issuer_nip": "9988776655",
                "issuer_name": "Duplikat Sp. z o.o.",
                "issue_date": "2026-04-09",
                "sale_date": "2026-04-09",
                "gross_amount": 123.0,
                "currency": "PLN",
                "status": "podejrzenie_duplikatu",
            },
            actor="test",
            organization_id=int(organization["organization_id"]),
        )

        headers = {"Content-Type": "application/json"}
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "duplikat-operator", "password": "1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        operator_cookie = response.getheader("Set-Cookie")
        self.assertTrue(operator_cookie)

        response, payload = self._request(
            "POST",
            f"/api/invoices/{duplicate['id']}/actions/confirm-duplicate?organization_id={organization['organization_id']}",
            headers={"Cookie": operator_cookie},
        )
        self.assertEqual(response.status, 403)
        self.assertIn("nie moze potwierdzac duplikatow", payload.decode("utf-8"))

        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "duplikat-koordynator", "password": "1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        coordinator_cookie = response.getheader("Set-Cookie")
        self.assertTrue(coordinator_cookie)

        response, payload = self._request(
            "POST",
            f"/api/invoices/{duplicate['id']}/actions/confirm-duplicate?organization_id={organization['organization_id']}",
            headers={"Cookie": coordinator_cookie},
        )
        self.assertEqual(response.status, 200)
        confirmed = json.loads(payload.decode("utf-8"))
        self.assertEqual(confirmed["status"], "pewny_duplikat")

    def test_search_endpoint_returns_modules_and_visible_records(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {"name": "Klient Search", "slug": "klient-search", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-04-12",
                "source": "EMAIL",
                "file_name": "faktury_test_search.pdf",
                "document_type": "pdf",
                "invoice_number": "SEARCH/2026/001",
                "issuer_nip": "1231231231",
                "issuer_name": "Faktury Search Sp. z o.o.",
                "issue_date": "2026-04-12",
                "sale_date": "2026-04-12",
                "gross_amount": 199.99,
                "currency": "PLN",
                "status": "nowa",
            },
            actor="test",
            organization_id=int(organization["organization_id"]),
        )

        headers = {"Content-Type": "application/json"}
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": "admin", "password": "Admin1234"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200)
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)

        response, payload = self._request(
            "GET",
            f"/api/search?q=faktury&organization_id={organization['organization_id']}",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200)
        result = json.loads(payload.decode("utf-8"))
        self.assertIn("modules", result)
        self.assertIn("groups", result)
        self.assertTrue(any(item["view"] == "invoices" and item["category"] == "Modul" for item in result["modules"]))
        invoice_items = [
            item
            for group in result["groups"]
            if group["key"] == "invoices"
            for item in group["items"]
        ]
        self.assertTrue(invoice_items)
        self.assertTrue(any("SEARCH/2026/001" in item["title"] for item in invoice_items))
        self.assertTrue(all(item["category"] == "Faktury" for item in invoice_items))

    def test_invoice_assignable_users_endpoint_returns_users_in_scope(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        default_organization = self.services["organization_repository"].ensure_default_organization()
        created_user = self.services["auth_service"].create_user(
            {
                "login": "invoice-http-owner",
                "display_name": "Invoice HTTP Owner",
                "password": "1234",
                "role": "coordinator",
                "is_active": 1,
                "organization_id": int(default_organization["organization_id"]),
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )

        cookie = self._login_default_admin()
        response, payload = self._request(
            "GET",
            f"/api/invoices/assignable-users?organization_id={default_organization['organization_id']}",
            headers={"Cookie": cookie},
        )

        self.assertEqual(response.status, 200)
        users = json.loads(payload.decode("utf-8"))
        self.assertTrue(any(int(item["user_id"]) == int(created_user["user_id"]) for item in users))
        self.assertTrue(all(int(item["organization_id"]) == int(default_organization["organization_id"]) for item in users))

    def test_invoice_patch_can_assign_user_and_detail_exposes_assignee(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        default_organization = self.services["organization_repository"].ensure_default_organization()
        created_user = self.services["auth_service"].create_user(
            {
                "login": "invoice-http-assignee",
                "display_name": "Invoice HTTP Assignee",
                "password": "1234",
                "role": "coordinator",
                "is_active": 1,
                "organization_id": int(default_organization["organization_id"]),
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )

        cookie = self._login_default_admin()
        response, payload = self._request(
            "PATCH",
            f"/api/invoices/1?organization_id={default_organization['organization_id']}",
            body=json.dumps({"assigned_user_id": created_user["user_id"]}),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        updated = json.loads(payload.decode("utf-8"))
        self.assertEqual(updated["invoice"]["assigned_user_id"], created_user["user_id"])

        response, payload = self._request(
            "GET",
            f"/api/invoices/1?organization_id={default_organization['organization_id']}",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200)
        detail = json.loads(payload.decode("utf-8"))
        self.assertEqual(detail["invoice"]["assigned_user_name"], "Invoice HTTP Assignee")

    def test_invoice_list_can_filter_by_assigned_user(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        default_organization = self.services["organization_repository"].ensure_default_organization()
        created_user = self.services["auth_service"].create_user(
            {
                "login": "invoice-http-filter",
                "display_name": "Invoice HTTP Filter",
                "password": "1234",
                "role": "coordinator",
                "is_active": 1,
                "organization_id": int(default_organization["organization_id"]),
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        self.services["invoice_service"].update_invoice(
            1,
            {"assigned_user_id": created_user["user_id"]},
            actor="Admin",
            organization_id=int(default_organization["organization_id"]),
            actor_user=admin,
        )

        cookie = self._login_default_admin()
        response, payload = self._request(
            "GET",
            f"/api/invoices?organization_id={default_organization['organization_id']}&assigned_user_id={created_user['user_id']}",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200)
        invoices = json.loads(payload.decode("utf-8"))
        self.assertTrue(invoices)
        self.assertTrue(all(int(item["assigned_user_id"] or 0) == int(created_user["user_id"]) for item in invoices))
        self.assertTrue(any(int(item["id"]) == 1 for item in invoices))

    def test_invoice_comment_endpoint_adds_comment_and_detail_contains_it(self) -> None:
        default_organization = self.services["organization_repository"].ensure_default_organization()
        cookie = self._login_default_admin()

        response, payload = self._request(
            "POST",
            f"/api/invoices/1/comments?organization_id={default_organization['organization_id']}",
            body=json.dumps({"note_text": "Komentarz HTTP do faktury."}),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))
        comment = json.loads(payload.decode("utf-8"))
        self.assertEqual(comment["note_text"], "Komentarz HTTP do faktury.")

        response, payload = self._request(
            "GET",
            f"/api/invoices/1?organization_id={default_organization['organization_id']}",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200)
        detail = json.loads(payload.decode("utf-8"))
        self.assertTrue(any(item["note_text"] == "Komentarz HTTP do faktury." for item in detail["comments"]))

    def test_invoice_preview_endpoint_returns_preview_payload(self) -> None:
        default_organization = self.services["organization_repository"].ensure_default_organization()
        created = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-06-03",
                "source": "EMAIL",
                "file_name": "http_preview_invoice.pdf",
                "document_type": "pdf",
                "invoice_number": "HTTP/PREVIEW/06/2026",
                "issuer_nip": "9988776655",
                "issuer_name": "HTTP Preview Sp. z o.o.",
                "issue_date": "2026-06-03",
                "sale_date": "2026-06-03",
                "gross_amount": 88.40,
                "currency": "PLN",
                "status": "nowa",
                "source_external_id": "http-preview-2026-06-03",
                "ocr_raw_text": "HTTP preview OCR invoice HTTP/PREVIEW/06/2026",
            },
            actor="test",
            organization_id=int(default_organization["organization_id"]),
        )
        cookie = self._login_default_admin()

        response, payload = self._request(
            "GET",
            f"/api/invoices/{created['id']}/preview?organization_id={default_organization['organization_id']}",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        preview = json.loads(payload.decode("utf-8"))
        self.assertEqual(int(preview["invoice"]["id"]), int(created["id"]))
        self.assertEqual(preview["document_trace"]["preview_kind"], "pdf")
        self.assertIn("ocr_excerpt", preview)
        self.assertIn("field_provenance", preview)

    def test_dashboard_views_accept_invoice_module_key(self) -> None:
        default_organization = self.services["organization_repository"].ensure_default_organization()
        cookie = self._login_default_admin()
        view_slug = f"moje-faktury-do-decyzji-http-{uuid.uuid4().hex[:8]}"

        response, payload = self._request(
            "POST",
            f"/api/dashboard/views?organization_id={default_organization['organization_id']}",
            body=json.dumps(
                {
                    "module_key": "invoices",
                    "view_name": "Moje faktury do decyzji",
                    "view_slug": view_slug,
                    "description": "Widok testowy dla faktur.",
                    "view_state": {
                        "filters": {"status": "weryfikacja", "assigned_user_id": 1},
                    },
                    "is_shared": True,
                    "is_default": False,
                }
            ),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))
        created = json.loads(payload.decode("utf-8"))
        self.assertEqual(created["module_key"], "invoices")

        response, payload = self._request(
            "GET",
            f"/api/dashboard/views?organization_id={default_organization['organization_id']}&module_key=invoices&include_hidden=1",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        views = json.loads(payload.decode("utf-8"))
        self.assertTrue(any(int(item["saved_view_id"]) == int(created["saved_view_id"]) for item in views))

    def test_invoice_list_can_filter_by_workflow_state(self) -> None:
        default_organization = self.services["organization_repository"].ensure_default_organization()
        self.services["invoice_service"].mark_invoice_ready_for_handoff(
            1,
            actor_user=self.services["auth_service"].list_users()[0],
            actor="Administrator",
            organization_id=int(default_organization["organization_id"]),
            handoff_target="Ksiegowosc",
        )

        cookie = self._login_default_admin()
        response, payload = self._request(
            "GET",
            f"/api/invoices?organization_id={default_organization['organization_id']}&workflow_state=gotowa_do_przekazania",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200)
        invoices = json.loads(payload.decode("utf-8"))
        self.assertTrue(invoices)
        self.assertTrue(all(item["workflow_state"] == "gotowa_do_przekazania" for item in invoices))
        self.assertTrue(any(int(item["id"]) == 1 for item in invoices))

    def test_invoice_mark_ready_action_updates_workflow(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        default_organization = self.services["organization_repository"].ensure_default_organization()
        operator = self.services["auth_service"].create_user(
            {
                "login": "invoice-workflow-operator-http",
                "display_name": "Invoice Workflow Operator HTTP",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": int(default_organization["organization_id"]),
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        cookie = self._login("invoice-workflow-operator-http", "1234")

        response, payload = self._request(
            "POST",
            f"/api/invoices/1/actions/mark-ready?organization_id={default_organization['organization_id']}",
            body=json.dumps({"handoff_target": "Ksiegowosc", "handoff_note": "Gotowe do przekazania."}),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        invoice = json.loads(payload.decode("utf-8"))
        self.assertEqual(invoice["workflow_state"], "gotowa_do_przekazania")
        self.assertEqual(invoice["handoff_target"], "Ksiegowosc")
        self.assertEqual(int(invoice["ready_for_handoff_by_user_id"]), int(operator["user_id"]))

    def test_invoice_undo_last_action_endpoint_reverts_workflow(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        default_organization = self.services["organization_repository"].ensure_default_organization()
        operator = self.services["auth_service"].create_user(
            {
                "login": "invoice-workflow-undo-http",
                "display_name": "Invoice Workflow Undo HTTP",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": int(default_organization["organization_id"]),
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        cookie = self._login("invoice-workflow-undo-http", "1234")

        response, payload = self._request(
            "POST",
            f"/api/invoices/1/actions/mark-ready?organization_id={default_organization['organization_id']}",
            body=json.dumps({"handoff_target": "Ksiegowosc", "handoff_note": "Do cofniecia."}),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))

        response, payload = self._request(
            "POST",
            f"/api/invoices/1/actions/undo-last?organization_id={default_organization['organization_id']}",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        invoice = json.loads(payload.decode("utf-8"))
        self.assertEqual(invoice["workflow_state"], "w_pracy")
        self.assertIsNone(invoice["ready_for_handoff_at"])

        response, payload = self._request(
            "GET",
            f"/api/invoices/1?organization_id={default_organization['organization_id']}",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        detail = json.loads(payload.decode("utf-8"))
        self.assertTrue(any(item["event_type"] == "invoice_workflow_undone" for item in detail["history"]))

    def test_invoice_handoff_action_requires_decision_role(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        default_organization = self.services["organization_repository"].ensure_default_organization()
        operator = self.services["auth_service"].create_user(
            {
                "login": "invoice-workflow-no-decision-http",
                "display_name": "Invoice Workflow No Decision HTTP",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": int(default_organization["organization_id"]),
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        cookie = self._login("invoice-workflow-no-decision-http", "1234")

        response, payload = self._request(
            "POST",
            f"/api/invoices/1/actions/handoff?organization_id={default_organization['organization_id']}",
            body=json.dumps({"handoff_target": "Ksiegowosc"}),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 403)
        self.assertIn("nie moze przekazac faktury dalej", payload.decode("utf-8").lower())

    def test_invoice_handoff_and_reopen_actions_change_workflow(self) -> None:
        default_organization = self.services["organization_repository"].ensure_default_organization()
        cookie = self._login_default_admin()

        response, payload = self._request(
            "POST",
            f"/api/invoices/1/actions/handoff?organization_id={default_organization['organization_id']}",
            body=json.dumps({"handoff_target": "Ksiegowosc", "handoff_note": "Przekazano do dalszej obslugi."}),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        invoice = json.loads(payload.decode("utf-8"))
        self.assertEqual(invoice["workflow_state"], "przekazana")
        self.assertEqual(invoice["handoff_target"], "Ksiegowosc")

        response, payload = self._request(
            "POST",
            f"/api/invoices/1/actions/reopen?organization_id={default_organization['organization_id']}",
            body=json.dumps({"reason": "Wymagana korekta po przekazaniu."}),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        reopened = json.loads(payload.decode("utf-8"))
        self.assertEqual(reopened["workflow_state"], "w_pracy")
        self.assertEqual(reopened["reopen_reason"], "Wymagana korekta po przekazaniu.")

        response, payload = self._request(
            "GET",
            f"/api/invoices/1?organization_id={default_organization['organization_id']}",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200)
        detail = json.loads(payload.decode("utf-8"))
        self.assertEqual(detail["workflow"]["state"], "w_pracy")
        self.assertEqual(detail["workflow"]["handoff_target"], "Ksiegowosc")
        self.assertEqual(detail["workflow"]["reopen_reason"], "Wymagana korekta po przekazaniu.")

    def test_invoice_document_intake_endpoint_returns_snapshot(self) -> None:
        default_organization = self.services["organization_repository"].ensure_default_organization()
        created = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-04-14",
                "source": "EMAIL",
                "file_name": "intake_http_snapshot.pdf",
                "document_type": "pdf",
                "invoice_number": "INTAKE/HTTP/14/04/2026",
                "issuer_nip": "1231239900",
                "issuer_name": "Intake HTTP Sp. z o.o.",
                "issue_date": "2026-04-14",
                "sale_date": "2026-04-14",
                "gross_amount": 189.55,
                "currency": "PLN",
                "status": "nowa",
                "source_external_id": "intake-http-2026-04-14",
            },
            actor="test",
            organization_id=int(default_organization["organization_id"]),
        )
        cookie = self._login_default_admin()
        response, payload = self._request(
            "GET",
            f"/api/invoices/document-intake?organization_id={default_organization['organization_id']}&limit=10",
            headers={"Cookie": cookie},
        )

        self.assertEqual(response.status, 200)
        snapshot = json.loads(payload.decode("utf-8"))
        self.assertIn("summary", snapshot)
        self.assertIn("items", snapshot)
        self.assertGreaterEqual(int(snapshot["summary"]["count"]), 1)
        intake_item = next(
            item for item in snapshot["items"] if int(item.get("linked_invoice_id") or 0) == int(created["id"])
        )
        self.assertEqual(intake_item["source_kind"], "invoice_document")
        self.assertEqual(intake_item["linked_invoice"]["invoice_number"], "INTAKE/HTTP/14/04/2026")
        self.assertEqual(intake_item["status"], "nowe")

    def test_invoice_exception_center_endpoint_returns_snapshot(self) -> None:
        default_organization = self.services["organization_repository"].ensure_default_organization()
        created = self.services["invoice_service"].create_invoice(
            {
                "incoming_date": "2026-04-15",
                "source": "EMAIL",
                "file_name": "exception_http_snapshot.jpg",
                "document_type": "zdjecie",
                "invoice_number": "EXC/HTTP/15/04/2026",
                "issuer_nip": "4445556667",
                "issuer_name": "Exception HTTP Sp. z o.o.",
                "issue_date": "2026-04-15",
                "sale_date": "2026-04-15",
                "gross_amount": 88.0,
                "currency": "PLN",
                "status": "weryfikacja",
                "flag_reason": "Dokument z e-maila wymaga weryfikacji, poniewaz OCR nie odczytal kluczowych pol faktury.",
                "source_external_id": "exception-http-2026-04-15",
            },
            actor="test",
            organization_id=int(default_organization["organization_id"]),
        )
        self.services["intake_repository"].create_item(
            {
                "organization_id": int(default_organization["organization_id"]),
                "source_kind": "invoice_exception",
                "source_reference": "missing_contractor",
                "title": "Brak kontrahenta",
                "description": "Faktura nie ma jeszcze przypisanego kontrahenta i wymaga uzupelnienia kartoteki.",
                "priority": "wysoki",
                "status": "w_toku",
                "linked_invoice_id": int(created["id"]),
                "metadata_json": json.dumps(
                    {
                        "invoice_id": int(created["id"]),
                        "exception_code": "missing_contractor",
                    }
                ),
            }
        )

        cookie = self._login_default_admin()
        response, payload = self._request(
            "GET",
            f"/api/invoices/exceptions?organization_id={default_organization['organization_id']}&limit=20",
            headers={"Cookie": cookie},
        )

        self.assertEqual(response.status, 200)
        snapshot = json.loads(payload.decode("utf-8"))
        self.assertIn("summary", snapshot)
        self.assertIn("items", snapshot)
        self.assertGreaterEqual(int(snapshot["summary"]["count"]), 1)
        self.assertIn("missing_contractor", snapshot["summary"]["counts_by_code"])
        self.assertIn("weak_ocr", snapshot["summary"]["counts_by_code"])
        related_items = [
            item for item in snapshot["items"] if int(item.get("linked_invoice_id") or 0) == int(created["id"])
        ]
        self.assertTrue(any(item["source_reference"] == "missing_contractor" for item in related_items))
        self.assertTrue(any(item["source_reference"] == "weak_ocr" for item in related_items))

    def test_invoice_handoff_batch_endpoints_create_detail_and_export(self) -> None:
        default_organization = self.services["organization_repository"].ensure_default_organization()
        cookie = self._login_default_admin()

        response, payload = self._request(
            "POST",
            f"/api/invoice-handoff-batches?organization_id={default_organization['organization_id']}",
            body=json.dumps(
                {
                    "invoice_ids": [1, 5],
                    "handoff_target": "Biuro rachunkowe",
                    "note": "Tygodniowa paczka dokumentow",
                }
            ),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))
        created = json.loads(payload.decode("utf-8"))
        batch_id = int(created["batch"]["invoice_handoff_batch_id"])
        self.assertEqual(created["batch"]["handoff_target"], "Biuro rachunkowe")
        self.assertEqual(len(created["items"]), 2)

        response, payload = self._request(
            "GET",
            f"/api/invoice-handoff-batches/{batch_id}?organization_id={default_organization['organization_id']}",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200)
        detail = json.loads(payload.decode("utf-8"))
        self.assertEqual(int(detail["batch"]["invoice_handoff_batch_id"]), batch_id)
        self.assertEqual(len(detail["items"]), 2)
        self.assertTrue(all(item["current_workflow_state"] == "przekazana" for item in detail["items"]))

        response, payload = self._request(
            "GET",
            f"/api/invoice-handoff-batches/{batch_id}/export?organization_id={default_organization['organization_id']}",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200)
        exported = json.loads(payload.decode("utf-8"))
        self.assertIn("csv_content", exported)
        self.assertIn("BatchNumber;InvoiceId;InvoiceNumber", exported["csv_content"])
        self.assertEqual(exported["batch"]["status"], "wyeksportowana")

    def test_invoice_close_action_updates_workflow(self) -> None:
        default_organization = self.services["organization_repository"].ensure_default_organization()
        cookie = self._login_default_admin()

        response, payload = self._request(
            "POST",
            f"/api/invoices/1/actions/handoff?organization_id={default_organization['organization_id']}",
            body=json.dumps({"handoff_target": "Ksiegowosc", "handoff_note": "Do finalnej akceptacji."}),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))

        response, payload = self._request(
            "POST",
            f"/api/invoices/1/actions/close?organization_id={default_organization['organization_id']}",
            body=json.dumps({"reason": "Dokument rozliczony i zamkniety."}),
            headers={"Cookie": cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        closed = json.loads(payload.decode("utf-8"))
        self.assertEqual(closed["workflow_state"], "zamknieta")
        self.assertEqual(closed["closed_reason"], "Dokument rozliczony i zamkniety.")
        self.assertIsNotNone(closed["closed_at"])

        response, payload = self._request(
            "GET",
            f"/api/invoices/1?organization_id={default_organization['organization_id']}",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200)
        detail = json.loads(payload.decode("utf-8"))
        self.assertEqual(detail["workflow"]["state"], "zamknieta")
        self.assertEqual(detail["workflow"]["closed_reason"], "Dokument rozliczony i zamkniety.")
        self.assertTrue(any(item["event_type"] == "invoice_closed" for item in detail["history"]))
