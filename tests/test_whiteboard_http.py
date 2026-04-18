from __future__ import annotations

import base64
import http.client
import json
import threading
import unittest

from app.api.http_server import create_server
from app.bootstrap import build_services
from app.db import reset_database
from app.demo_seed import seed_demo_data


class WhiteboardHttpTests(unittest.TestCase):
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

    def _request(
        self,
        method: str,
        path: str,
        body: str | bytes | None = None,
        headers: dict[str, str] | None = None,
    ):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        payload = response.read()
        connection.close()
        return response, payload

    def _build_multipart_payload(
        self,
        *,
        fields: dict[str, str],
        files: dict[str, tuple[str, str, bytes]],
    ) -> tuple[bytes, str]:
        boundary = "----CodexWhiteboardBoundary"
        body = bytearray()

        for field_name, value in fields.items():
            body.extend(f"--{boundary}\r\n".encode("utf-8"))
            body.extend(f'Content-Disposition: form-data; name="{field_name}"\r\n\r\n'.encode("utf-8"))
            body.extend(str(value).encode("utf-8"))
            body.extend(b"\r\n")

        for field_name, (file_name, content_type, content) in files.items():
            body.extend(f"--{boundary}\r\n".encode("utf-8"))
            body.extend(
                f'Content-Disposition: form-data; name="{field_name}"; filename="{file_name}"\r\n'.encode("utf-8")
            )
            body.extend(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
            body.extend(content)
            body.extend(b"\r\n")

        body.extend(f"--{boundary}--\r\n".encode("utf-8"))
        return bytes(body), f"multipart/form-data; boundary={boundary}"

    def _login(self, login: str, password: str) -> str:
        response, payload = self._request(
            "POST",
            "/api/session/login",
            body=json.dumps({"login": login, "password": password}),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        cookie = response.getheader("Set-Cookie")
        self.assertTrue(cookie)
        return str(cookie)

    def test_guest_can_draw_on_whiteboard_and_admin_can_clear_it(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {"name": "Tablica Org", "slug": "tablica-org", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        self.services["auth_service"].create_user(
            {
                "login": "tablica-gosc",
                "display_name": "Tablica Gosc",
                "password": "1234",
                "role": "guest",
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )

        guest_cookie = self._login("tablica-gosc", "1234")

        response, payload = self._request("GET", "/api/whiteboard", headers={"Cookie": guest_cookie})
        self.assertEqual(response.status, 200)
        board = json.loads(payload.decode("utf-8"))
        self.assertEqual(board["mode"], "full")
        self.assertEqual(board["events"], [])
        self.assertEqual(board["latest_event_id"], 0)

        response, payload = self._request(
            "POST",
            "/api/whiteboard/events",
            body=json.dumps(
                {
                    "strokes": [
                        {
                            "tool": "pen",
                            "color": "#0f5c90",
                            "width": 4,
                            "points": [
                                {"x": 0.12, "y": 0.21},
                                {"x": 0.28, "y": 0.34},
                            ],
                        }
                    ]
                }
            ),
            headers={"Cookie": guest_cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))
        created = json.loads(payload.decode("utf-8"))
        self.assertEqual(created["mode"], "patch")
        self.assertEqual(created["latest_event_id"], 1)
        self.assertEqual(created["events"][0]["event_type"], "stroke")
        self.assertEqual(created["events"][0]["actor_label"], "Tablica Gosc")

        response, payload = self._request(
            "GET",
            "/api/whiteboard?since_event_id=1",
            headers={"Cookie": guest_cookie},
        )
        self.assertEqual(response.status, 200)
        patch_payload = json.loads(payload.decode("utf-8"))
        self.assertEqual(patch_payload["mode"], "patch")
        self.assertEqual(patch_payload["events"], [])

        response, payload = self._request(
            "POST",
            "/api/whiteboard/actions/clear",
            headers={"Cookie": guest_cookie},
        )
        self.assertEqual(response.status, 403)

        admin_cookie = self._login("admin", "Admin1234")
        response, payload = self._request(
            "POST",
            f"/api/whiteboard/actions/clear?organization_id={organization['organization_id']}",
            headers={"Cookie": admin_cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        cleared = json.loads(payload.decode("utf-8"))
        self.assertEqual(cleared["events"][0]["event_type"], "clear")
        self.assertEqual(cleared["last_cleared_event_id"], 2)

        response, payload = self._request(
            "GET",
            "/api/whiteboard?since_event_id=1",
            headers={"Cookie": guest_cookie},
        )
        self.assertEqual(response.status, 200)
        refreshed = json.loads(payload.decode("utf-8"))
        self.assertEqual(refreshed["mode"], "full")
        self.assertEqual(len(refreshed["events"]), 1)
        self.assertEqual(refreshed["events"][0]["event_type"], "clear")
        self.assertEqual(refreshed["last_cleared_event_id"], 2)

    def test_global_admin_whiteboard_requires_specific_organization_scope(self) -> None:
        admin_cookie = self._login("admin", "Admin1234")
        response, payload = self._request("GET", "/api/whiteboard", headers={"Cookie": admin_cookie})
        self.assertEqual(response.status, 400)
        self.assertIn("Wybierz konkretna organizacje", payload.decode("utf-8"))

    def test_guest_can_upload_image_to_whiteboard(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {"name": "Tablica Obrazki", "slug": "tablica-obrazki", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        self.services["auth_service"].create_user(
            {
                "login": "obrazki-gosc",
                "display_name": "Obrazki Gosc",
                "password": "1234",
                "role": "guest",
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        guest_cookie = self._login("obrazki-gosc", "1234")

        image_bytes = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO2NT4cAAAAASUVORK5CYII="
        )
        body, content_type = self._build_multipart_payload(
            fields={"x": "0.2", "y": "0.25", "width": "0.3", "height": "0.18"},
            files={"file": ("zabawa.png", "image/png", image_bytes)},
        )

        response, payload = self._request(
            "POST",
            "/api/whiteboard/images",
            body=body,
            headers={"Cookie": guest_cookie, "Content-Type": content_type},
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))
        created = json.loads(payload.decode("utf-8"))
        self.assertEqual(created["events"][0]["event_type"], "image")
        self.assertEqual(created["events"][0]["payload"]["file_name"], "zabawa.png")
        self.assertEqual(created["events"][0]["payload"]["mime_type"], "image/png")
        self.assertTrue(created["events"][0]["payload"]["image_link"].startswith("/pliki/tablica/"))

        response, payload = self._request("GET", "/api/whiteboard", headers={"Cookie": guest_cookie})
        self.assertEqual(response.status, 200)
        board = json.loads(payload.decode("utf-8"))
        self.assertEqual(len(board["events"]), 1)
        self.assertEqual(board["events"][0]["event_type"], "image")

        response, payload = self._request(
            "GET",
            created["events"][0]["payload"]["image_link"],
            headers={"Cookie": guest_cookie},
        )
        self.assertEqual(response.status, 200)
        self.assertEqual(response.getheader("Content-Type"), "image/png")
        self.assertEqual(payload, image_bytes)

    def test_guest_can_transform_whiteboard_image(self) -> None:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {"name": "Tablica Transform", "slug": "tablica-transform", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        self.services["auth_service"].create_user(
            {
                "login": "transform-gosc",
                "display_name": "Transform Gosc",
                "password": "1234",
                "role": "guest",
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        guest_cookie = self._login("transform-gosc", "1234")

        image_bytes = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO2NT4cAAAAASUVORK5CYII="
        )
        body, content_type = self._build_multipart_payload(
            fields={"x": "0.2", "y": "0.25", "width": "0.3", "height": "0.18"},
            files={"file": ("obracany.png", "image/png", image_bytes)},
        )

        response, payload = self._request(
            "POST",
            "/api/whiteboard/images",
            body=body,
            headers={"Cookie": guest_cookie, "Content-Type": content_type},
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))
        created = json.loads(payload.decode("utf-8"))
        image_event_id = int(created["events"][0]["whiteboard_event_id"])

        response, payload = self._request(
            "PATCH",
            f"/api/whiteboard/images/{image_event_id}",
            body=json.dumps(
                {
                    "x": 0.18,
                    "y": 0.22,
                    "width": 0.36,
                    "height": 0.24,
                    "rotation_deg": 18,
                }
            ),
            headers={"Cookie": guest_cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        transformed = json.loads(payload.decode("utf-8"))
        self.assertEqual(transformed["events"][0]["event_type"], "image_transform")
        self.assertEqual(transformed["events"][0]["payload"]["image_event_id"], image_event_id)
        self.assertEqual(transformed["events"][0]["payload"]["rotation_deg"], 18)

        response, payload = self._request("GET", "/api/whiteboard", headers={"Cookie": guest_cookie})
        self.assertEqual(response.status, 200)
        board = json.loads(payload.decode("utf-8"))
        self.assertEqual(len(board["events"]), 2)
        self.assertEqual(board["events"][0]["event_type"], "image")
        self.assertEqual(board["events"][1]["event_type"], "image_transform")
        self.assertEqual(board["events"][1]["payload"]["width"], 0.36)


if __name__ == "__main__":
    unittest.main()
