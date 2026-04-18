from __future__ import annotations

import http.client
import json
import threading
import unittest
from urllib.parse import parse_qs, urlsplit

from app.api.http_server import create_server
from app.bootstrap import build_services
from app.db import reset_database
from app.domain.constants import MANAGER_ASSISTANT_MODULE


class FakeGoogleCalendarAdapter:
    def __init__(self) -> None:
        self.upserted_events: list[dict[str, object]] = []
        self.deleted_events: list[dict[str, str]] = []
        self.remote_events: dict[tuple[str, str], dict[str, object]] = {}

    def is_enabled(self) -> bool:
        return True

    def callback_url(self) -> str:
        return "https://panel.example.com/api/google-calendar/oauth/callback"

    def build_authorization_url(self, state_token: str) -> str:
        return f"https://accounts.example.com/oauth?state={state_token}"

    def exchange_code_for_tokens(self, code: str) -> dict[str, object]:
        return {
            "access_token": f"access-{code}",
            "refresh_token": f"refresh-{code}",
            "token_expires_at": "2099-01-01T10:00:00+00:00",
            "scope": "calendar openid email",
        }

    def refresh_tokens(self, refresh_token: str) -> dict[str, object]:
        return {
            "access_token": f"refreshed-{refresh_token}",
            "refresh_token": refresh_token,
            "token_expires_at": "2099-01-01T10:00:00+00:00",
            "scope": "calendar openid email",
        }

    def fetch_user_info(self, access_token: str) -> dict[str, str]:
        lowered = access_token.lower()
        if "admin" in lowered:
            return {"email": "admin.calendar@example.com"}
        return {"email": "ola.calendar@example.com"}

    def list_calendars(self, access_token: str) -> list[dict[str, object]]:
        return [
            {
                "external_calendar_id": "primary",
                "external_calendar_name": "Firma CASI",
                "external_calendar_timezone": "Europe/Warsaw",
                "is_primary": True,
                "access_role": "owner",
            },
            {
                "external_calendar_id": "family",
                "external_calendar_name": "Kalendarz rodzinny",
                "external_calendar_timezone": "Europe/Warsaw",
                "is_primary": False,
                "access_role": "owner",
            },
        ]

    def upsert_event(
        self,
        access_token: str,
        *,
        external_calendar_id: str,
        event_id: str | None,
        event_payload: dict[str, object],
    ) -> dict[str, str]:
        self.upserted_events.append(
            {
                "access_token": access_token,
                "external_calendar_id": external_calendar_id,
                "event_id": event_id,
                "summary": str(event_payload.get("summary") or ""),
            }
        )
        counter = len(self.upserted_events)
        resulting_id = event_id or f"evt-{counter}"
        response = {
            "id": resulting_id,
            "updated": "2099-01-01T12:00:00+00:00",
            "etag": f"etag-{counter}",
            "htmlLink": f"https://calendar.google.com/calendar/event?eid={resulting_id}",
        }
        self.remote_events[(external_calendar_id, resulting_id)] = {
            **response,
            "summary": str(event_payload.get("summary") or ""),
            "description": str(event_payload.get("description") or ""),
            "start": dict(event_payload.get("start") or {}),
            "end": dict(event_payload.get("end") or {}),
            "status": str(event_payload.get("status") or "confirmed"),
        }
        return response

    def get_event(self, access_token: str, *, external_calendar_id: str, event_id: str) -> dict[str, object] | None:
        event = self.remote_events.get((external_calendar_id, event_id))
        return dict(event) if event else None

    def delete_event(self, access_token: str, *, external_calendar_id: str, event_id: str) -> None:
        self.deleted_events.append(
            {
                "access_token": access_token,
                "external_calendar_id": external_calendar_id,
                "event_id": event_id,
            }
        )
        self.remote_events.pop((external_calendar_id, event_id), None)


class CalendarMvpTestCase(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        self.fake_google = FakeGoogleCalendarAdapter()
        self.services["calendar_service"].google_adapter = self.fake_google
        self.admin = self._ensure_admin()
        self.organization = self.services["organization_service"].create_organization(
            {"name": "Klient Kalendarzowy", "slug": "klient-kalendarzowy", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.services["organization_repository"].replace_enabled_modules(
            int(self.organization["organization_id"]),
            [MANAGER_ASSISTANT_MODULE],
            enabled_by_user_id=int(self.admin["user_id"]),
        )
        self.org_admin = self.services["auth_service"].create_user(
            {
                "login": "ania-admin",
                "display_name": "Ania Admin",
                "password": "1234",
                "role": "organization_admin",
                "is_active": 1,
                "organization_id": self.organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )
        self.user = self.services["auth_service"].create_user(
            {
                "login": "ola-kalendarz",
                "display_name": "Ola Kalendarz",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": self.organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )

    def _ensure_admin(self):
        existing = next(
            (user for user in self.services["auth_service"].list_users() if user.get("login") == "admin"),
            None,
        )
        if existing:
            return existing
        self.services["auth_service"].ensure_default_admin()
        admin = next(
            (user for user in self.services["auth_service"].list_users() if user.get("login") == "admin"),
            None,
        )
        assert admin is not None
        return admin

    def _begin_google_connection(self, user: dict[str, object], *, code: str) -> tuple[str, dict[str, object]]:
        auth_payload = self.services["calendar_service"].begin_google_calendar_connection(
            user,
            confirm_work_account_visibility=True,
        )
        parsed = urlsplit(auth_payload["authorization_url"])
        state_token = parse_qs(parsed.query)["state"][0]
        status = self.services["calendar_service"].finalize_google_calendar_connection(state_token, code)
        return state_token, status

    def _approve_google_connection(self, target_user: dict[str, object]) -> dict[str, object]:
        return self.services["calendar_service"].approve_google_calendar_connection(
            int(target_user["user_id"]),
            actor_user=self.org_admin,
            actor="Ania Admin",
        )

    def _request(self, method: str, path: str, body: str | None = None, headers: dict[str, str] | None = None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        payload = response.read()
        connection.close()
        return response, payload

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
        return cookie

    def start_http_server(self) -> None:
        self.server = create_server("127.0.0.1", 0, self.services)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop_http_server(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
