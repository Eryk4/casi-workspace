from __future__ import annotations

import json
import unittest

from tests.http_server_support import HttpServerTestCase


class SupportCenterHttpTests(HttpServerTestCase):
    def _create_organization_with_users(self) -> tuple[dict, str, str, str]:
        admin = self.services["auth_service"].list_users()[0]
        organization = self.services["organization_service"].create_organization(
            {"name": "Support Org", "slug": "support-org", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        self.services["auth_service"].create_user(
            {
                "login": "support-gosc-1",
                "display_name": "Support Gosc 1",
                "password": "1234",
                "role": "guest",
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        self.services["auth_service"].create_user(
            {
                "login": "support-gosc-2",
                "display_name": "Support Gosc 2",
                "password": "1234",
                "role": "guest",
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        self.services["auth_service"].create_user(
            {
                "login": "support-operator",
                "display_name": "Support Operator",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        return organization, self._login("support-gosc-1", "1234"), self._login("support-gosc-2", "1234"), self._login("support-operator", "1234")

    def test_guest_can_create_comment_and_attach_only_to_own_support_request(self) -> None:
        _organization, guest_cookie, other_guest_cookie, _operator_cookie = self._create_organization_with_users()

        response, payload = self._request(
            "POST",
            "/api/support/requests",
            body=json.dumps(
                {
                    "title": "Nie dziala zmiana organizacji",
                    "description": "Lista zamyka sie od razu po kliknieciu.",
                    "support_category": "problem_techniczny",
                    "priority": "wysoki",
                }
            ),
            headers={"Cookie": guest_cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))
        created = json.loads(payload.decode("utf-8"))
        request_id = int(created["intake_item_id"])
        self.assertEqual(created["source_kind"], "support")

        response, payload = self._request("GET", "/api/support/requests", headers={"Cookie": guest_cookie})
        self.assertEqual(response.status, 200)
        items = json.loads(payload.decode("utf-8"))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["intake_item_id"], request_id)

        response, payload = self._request(
            "POST",
            f"/api/support/requests/{request_id}/comments",
            body=json.dumps({"note_text": "Dodaje jeszcze nagranie i screen."}),
            headers={"Cookie": guest_cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))

        response, payload = self._request(
            "POST",
            f"/api/support/requests/{request_id}/attachments",
            body=json.dumps(
                {
                    "attachment_kind": "link",
                    "file_name": "Screen z bledu",
                    "attachment_url": "https://example.com/screen",
                    "content_type": "text/uri-list",
                }
            ),
            headers={"Cookie": guest_cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))

        response, payload = self._request(
            "GET",
            f"/api/support/requests/{request_id}",
            headers={"Cookie": guest_cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        detail = json.loads(payload.decode("utf-8"))
        self.assertEqual(detail["item"]["source_kind"], "support")
        self.assertEqual(len(detail["comments"]), 1)
        self.assertEqual(len(detail["attachments"]), 1)

        response, payload = self._request("GET", "/api/support/requests", headers={"Cookie": other_guest_cookie})
        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(payload.decode("utf-8")), [])

        response, payload = self._request(
            "GET",
            f"/api/support/requests/{request_id}",
            headers={"Cookie": other_guest_cookie},
        )
        self.assertEqual(response.status, 404)

    def test_guest_cannot_open_operational_intake_endpoints(self) -> None:
        _organization, guest_cookie, _other_guest_cookie, _operator_cookie = self._create_organization_with_users()

        response, payload = self._request("GET", "/api/intake/items", headers={"Cookie": guest_cookie})
        self.assertEqual(response.status, 403, payload.decode("utf-8"))

        response, payload = self._request(
            "POST",
            "/api/intake/items",
            body=json.dumps({"title": "Nie powinno przejsc", "source_kind": "manual"}),
            headers={"Cookie": guest_cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 403, payload.decode("utf-8"))

    def test_operator_keeps_access_to_operational_intake(self) -> None:
        _organization, _guest_cookie, _other_guest_cookie, operator_cookie = self._create_organization_with_users()

        response, payload = self._request(
            "POST",
            "/api/intake/items",
            body=json.dumps(
                {
                    "title": "Sprawa operacyjna",
                    "description": "To jest wewnetrzny inbox dla operatora.",
                    "source_kind": "manual",
                    "priority": "normalny",
                }
            ),
            headers={"Cookie": operator_cookie, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 201, payload.decode("utf-8"))

        response, payload = self._request("GET", "/api/intake/items", headers={"Cookie": operator_cookie})
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        items = json.loads(payload.decode("utf-8"))
        self.assertGreaterEqual(len(items), 1)
        self.assertTrue(any(item["title"] == "Sprawa operacyjna" for item in items))


if __name__ == "__main__":
    unittest.main()
