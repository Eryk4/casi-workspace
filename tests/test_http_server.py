from __future__ import annotations

import http.client
import json
import threading
import unittest
from pathlib import Path

from app.api.http_server import create_server
from app.bootstrap import build_services
from app.config import DOCUMENTS_DIR
from app.db import reset_database
from app.demo_seed import seed_demo_data


class HttpServerTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        self.services["auth_service"].ensure_default_admin()
        seed_demo_data(self.services["invoice_service"], self.services["invoice_repository"])
        self.server = create_server("127.0.0.1", 0, self.services)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def _request(self, method: str, path: str, body: str | None = None, headers: dict[str, str] | None = None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        payload = response.read()
        connection.close()
        return response, payload

    def test_root_is_public_and_serves_html(self) -> None:
        response, payload = self._request("GET", "/")
        self.assertEqual(response.status, 200)
        self.assertIn("text/html", response.getheader("Content-Type", ""))
        body = payload.decode("utf-8")
        self.assertIn("Panel Faktur", body)
        self.assertIn("login-form", body)

    def test_meta_exposes_storage_backend(self) -> None:
        response, payload = self._request("GET", "/api/meta")
        self.assertEqual(response.status, 200)
        meta = json.loads(payload.decode("utf-8"))
        self.assertEqual(meta["storage_backend"], "lokalny")

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
        self.assertEqual(current["role"], "administrator")

    def test_org_user_sees_only_own_invoices_and_cannot_open_other_org_files(self) -> None:
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
        self.assertFalse(any(item["organization_slug"] == "organizacja-domyslna" for item in invoices))

        response, payload = self._request("GET", "/pliki/dokumenty/organizacje/organizacja-domyslna/KSeF/2026-04-01/ksef_fv_biuroserwis_2026_04_01_dokument.txt", headers={"Cookie": cookie})
        self.assertEqual(response.status, 403)
        self.assertIn("Brak dostępu do plików innej organizacji.", payload.decode("utf-8"))

    def test_public_telegram_webhook_creates_invoice_and_stores_real_file(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {"name": "Telegram Klient", "slug": "telegram-klient", "is_active": 1},
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
            "content": b"%PDF-1.4 test telegram",
            "telegram_file_path": "documents/test/faktura_telegram.pdf",
        }

        webhook_payload = {
            "update_id": 101,
            "message": {
                "message_id": 77,
                "date": 1775671200,
                "caption": "Nowa faktura do systemu",
                "chat": {"id": -100123, "type": "private"},
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
        self.assertTrue(invoice["file_storage_key"].startswith("organizacje/telegram-klient/TELEGRAM/"))
        self.assertTrue(invoice["file_link"].endswith(".pdf"))
        self.assertEqual(detail["source_trace"]["linked_user"]["login"], "olga")
        self.assertTrue(any(item["event_type"] == "invoice_created" and item["actor"] == "Olga" for item in detail["history"]))

        file_relative = invoice["file_storage_key"]
        stored_file = DOCUMENTS_DIR / Path(file_relative)
        self.assertTrue(stored_file.exists())
        self.assertEqual(stored_file.read_bytes(), b"%PDF-1.4 test telegram")


if __name__ == "__main__":
    unittest.main()
