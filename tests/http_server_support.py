from __future__ import annotations

import http.client
import json
import shutil
import threading
import unittest

from app.api.http_server import create_server
from app.bootstrap import build_services
from app.config import KNOWLEDGE_DIR
from app.db import reset_database
from app.demo_seed import seed_demo_data


class HttpServerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        shutil.rmtree(KNOWLEDGE_DIR, ignore_errors=True)
        KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
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

    def _login(self, login: str, password: str, headers: dict[str, str] | None = None) -> str:
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": login, "password": password}),
            headers=request_headers,
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)
        return cookie

    def _login_default_admin(self) -> str:
        return self._login("admin", "Admin1234")
