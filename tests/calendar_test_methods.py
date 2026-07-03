from __future__ import annotations

import http.client
import json
import threading
import unittest
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

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


class CalendarMvpTests(unittest.TestCase):
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

    def test_user_can_create_named_google_calendars_and_assign_task(self) -> None:
        calendar = self.services["calendar_service"].create_user_calendar(
            {
                "display_name": "Sluzbowy klient A",
                "description": "Wlasny kalendarz sluzbowy do pracy z klientem A",
                "calendar_kind": "inne",
                "default_duration_minutes": 90,
                "is_active": 1,
            },
            actor_user=self.user,
            actor="Ola",
            base_url="https://panel.example.com",
        )
        self.assertEqual(calendar["display_name"], "Sluzbowy klient A")
        self.assertEqual(calendar["calendar_kind"], "inne")
        self.assertIsNone(calendar["linked_organization_id"])
        self.assertEqual(calendar["default_duration_minutes"], 90)
        self.assertIn("/api/calendar-feeds/", calendar["feed_url"])

        created_task = self.services["task_service"].create_task(
            {
                "title": "Spotkanie z firma A",
                "task_type": "wydarzenie",
                "status": "nowe",
                "priority": "wysoki",
                "due_at": "2099-05-10T10:00",
                "remind_at": "2099-05-10T09:30",
                "calendar_id": calendar["user_calendar_id"],
            },
            actor_user=self.user,
            actor="Ola",
            organization_id=self.organization["organization_id"],
        )

        self.assertEqual(created_task["calendar_name"], "Sluzbowy klient A")
        self.assertEqual(created_task["calendar_kind"], "inne")
        self.assertEqual(created_task["calendar_duration_minutes"], 90)

        built_feed = self.services["calendar_service"].build_calendar_feed(calendar["sync_token"])
        self.assertIsNotNone(built_feed)
        assert built_feed is not None
        content, display_name = built_feed
        self.assertEqual(display_name, "Sluzbowy klient A")
        self.assertIn("SUMMARY:Spotkanie z firma A", content)
        self.assertIn("DTSTART;TZID=Europe/Warsaw:20990510T100000", content)
        self.assertIn("DTEND;TZID=Europe/Warsaw:20990510T113000", content)

    def test_operator_cannot_create_private_family_or_organization_calendar(self) -> None:
        restricted_payloads = [
            {"display_name": "Prywatny operatora", "calendar_kind": "prywatny"},
            {"display_name": "Rodzinny operatora", "calendar_kind": "rodzinny"},
            {
                "display_name": "Kalendarz organizacji operatora",
                "calendar_kind": "organizacja",
                "linked_organization_id": self.organization["organization_id"],
            },
        ]
        for payload in restricted_payloads:
            with self.assertRaisesRegex(ValueError, "Wlasciciel systemu albo Administrator organizacji"):
                self.services["calendar_service"].create_user_calendar(
                    {
                        **payload,
                        "default_duration_minutes": 60,
                        "is_active": 1,
                    },
                    actor_user=self.user,
                    actor="Ola",
                    base_url="https://panel.example.com",
                )

    def test_org_admin_can_create_private_and_family_calendar(self) -> None:
        private_calendar = self.services["calendar_service"].create_user_calendar(
            {
                "display_name": "Admin prywatny",
                "calendar_kind": "prywatny",
                "default_duration_minutes": 45,
                "is_active": 1,
            },
            actor_user=self.org_admin,
            actor="Ania Admin",
            base_url="https://panel.example.com",
        )
        family_calendar = self.services["calendar_service"].create_user_calendar(
            {
                "display_name": "Admin rodzinny",
                "calendar_kind": "rodzinny",
                "default_duration_minutes": 120,
                "is_active": 1,
            },
            actor_user=self.org_admin,
            actor="Ania Admin",
            base_url="https://panel.example.com",
        )

        self.assertEqual(private_calendar["calendar_kind"], "prywatny")
        self.assertEqual(family_calendar["calendar_kind"], "rodzinny")

    def test_user_can_store_own_reminder_preferences(self) -> None:
        updated = self.services["calendar_service"].update_reminder_preferences(
            {
                "telegram_reminders_enabled": True,
                "quiet_hours_start": "22:00",
                "quiet_hours_end": "06:30",
                "repeat_interval_minutes": 45,
            },
            actor_user=self.user,
            actor="Ola",
        )

        self.assertEqual(updated["quiet_hours_start"], "22:00")
        self.assertEqual(updated["quiet_hours_end"], "06:30")
        self.assertEqual(updated["repeat_interval_minutes"], 45)

    def test_google_connection_status_exposes_setup_diagnostics(self) -> None:
        with patch("app.services.calendar_service.google_calendar_direct_enabled", return_value=True), patch(
            "app.services.calendar_service.GOOGLE_CLIENT_ID",
            "client-id",
        ), patch(
            "app.services.calendar_service.GOOGLE_CLIENT_SECRET",
            "client-secret",
        ), patch(
            "app.services.calendar_service.PUBLIC_BASE_URL",
            "https://panel.example.com",
        ):
            status = self.services["calendar_service"].get_google_connection_status(self.user)
            self.assertTrue(status["configured"])
            self.assertTrue(status["client_id_ready"])
            self.assertTrue(status["client_secret_ready"])
            self.assertTrue(status["public_base_url_ready"])
            self.assertFalse(status["ready_for_direct_sync"])
            self.assertTrue(any(item["code"] == "oauth_ready" and item["ok"] for item in status["setup_checks"]))

    def test_google_connection_requires_visibility_confirmation(self) -> None:
        with patch("app.services.calendar_service.google_calendar_direct_enabled", return_value=True):
            with self.assertRaisesRegex(ValueError, "Potwierdz"):
                self.services["calendar_service"].begin_google_calendar_connection(
                    self.user,
                    confirm_work_account_visibility=False,
                )

    def test_user_google_connection_waits_for_admin_approval_before_sync(self) -> None:
        with patch("app.services.calendar_service.google_calendar_direct_enabled", return_value=True):
            _, status = self._begin_google_connection(self.user, code="kod-operatora")
            self.assertFalse(status["connected"])
            self.assertTrue(status["approval_pending"])
            self.assertEqual(status["approval_status"], "pending_approval")
            self.assertEqual(status["google_email"], "ola.calendar@example.com")
            self.assertTrue(status["employee_visibility_confirmed"])

            with self.assertRaisesRegex(ValueError, "czeka jeszcze na zatwierdzenie"):
                self.services["calendar_service"].list_external_google_calendars(self.user)

            approved = self._approve_google_connection(self.user)
            self.assertTrue(approved["connected"])
            self.assertEqual(approved["approval_status"], "approved")
            self.assertEqual(approved["approved_by_login"], "ania-admin")

            external_calendars = self.services["calendar_service"].list_external_google_calendars(self.user)
            self.assertEqual(len(external_calendars), 2)
            self.assertEqual(external_calendars[0]["external_calendar_id"], "primary")

            calendar = self.services["calendar_service"].create_user_calendar(
                {
                    "display_name": "Sluzbowy Google Oli",
                    "provider": "google_api",
                    "external_calendar_id": "primary",
                    "calendar_kind": "inne",
                    "default_duration_minutes": 45,
                    "is_active": 1,
                },
                actor_user=self.user,
                actor="Ola",
                base_url="https://panel.example.com",
            )

            created_task = self.services["task_service"].create_task(
                {
                    "title": "Spotkanie z klientem w Google",
                    "task_type": "wydarzenie",
                    "status": "nowe",
                    "priority": "wysoki",
                    "due_at": "2099-05-10T10:00",
                    "remind_at": "2099-05-10T09:30",
                    "calendar_id": calendar["user_calendar_id"],
                },
                actor_user=self.user,
                actor="Ola",
                organization_id=self.organization["organization_id"],
            )

            self.assertEqual(created_task["calendar_provider"], "google_api")
            self.assertEqual(created_task["external_calendar_event_id"], "evt-1")
            self.assertEqual(self.fake_google.upserted_events[-1]["access_token"], "access-kod-operatora")

    def test_assigned_organization_calendar_uses_organization_admin_connection(self) -> None:
        with patch("app.services.calendar_service.google_calendar_direct_enabled", return_value=True):
            _, admin_status = self._begin_google_connection(self.org_admin, code="kod-admina")
            self.assertTrue(admin_status["connected"])
            self.assertEqual(admin_status["approval_status"], "approved")

            organization_calendar = self.services["calendar_service"].create_user_calendar(
                {
                    "display_name": "Kalendarz firmy",
                    "provider": "google_api",
                    "external_calendar_id": "family",
                    "calendar_kind": "organizacja",
                    "linked_organization_id": self.organization["organization_id"],
                    "default_duration_minutes": 50,
                    "is_active": 1,
                },
                actor_user=self.org_admin,
                actor="Ania Admin",
                base_url="https://panel.example.com",
            )

            assigned = self.services["calendar_service"].assign_organization_calendar_to_user(
                int(self.user["user_id"]),
                int(organization_calendar["user_calendar_id"]),
                actor_user=self.org_admin,
                actor="Ania Admin",
                base_url="https://panel.example.com",
            )
            self.assertEqual(assigned["access_mode"], "assigned")
            self.assertEqual(assigned["access_mode_label"], "Przypisany kalendarz organizacji")

            visible_calendars = self.services["calendar_service"].list_user_calendars(
                self.user,
                base_url="https://panel.example.com",
            )
            self.assertEqual(len(visible_calendars), 1)
            self.assertEqual(visible_calendars[0]["access_mode"], "assigned")
            self.assertEqual(visible_calendars[0]["display_name"], "Kalendarz firmy")

            created_task = self.services["task_service"].create_task(
                {
                    "title": "Spotkanie z przypisanego kalendarza",
                    "task_type": "wydarzenie",
                    "status": "nowe",
                    "priority": "normalny",
                    "due_at": "2099-05-10T10:00",
                    "calendar_id": organization_calendar["user_calendar_id"],
                },
                actor_user=self.user,
                actor="Ola",
                organization_id=self.organization["organization_id"],
            )

            self.assertEqual(created_task["calendar_access_mode"], "assigned")
            self.assertEqual(created_task["external_calendar_event_id"], "evt-1")
            self.assertEqual(self.fake_google.upserted_events[-1]["access_token"], "access-kod-admina")
            self.assertEqual(self.fake_google.upserted_events[-1]["external_calendar_id"], "family")

    def test_google_sync_check_detects_difference_and_missing_event(self) -> None:
        with patch("app.services.calendar_service.google_calendar_direct_enabled", return_value=True):
            self._begin_google_connection(self.user, code="kod-operatora")
            self._approve_google_connection(self.user)

            calendar = self.services["calendar_service"].create_user_calendar(
                {
                    "display_name": "Sluzbowy Google - sprawdzenie",
                    "provider": "google_api",
                    "external_calendar_id": "primary",
                    "calendar_kind": "inne",
                    "default_duration_minutes": 30,
                    "is_active": 1,
                },
                actor_user=self.user,
                actor="Ola",
                base_url="https://panel.example.com",
            )

            created_task = self.services["task_service"].create_task(
                {
                    "title": "Status Google",
                    "task_type": "wydarzenie",
                    "status": "nowe",
                    "priority": "normalny",
                    "due_at": "2099-05-10T10:00",
                    "calendar_id": calendar["user_calendar_id"],
                },
                actor_user=self.user,
                actor="Ola",
                organization_id=self.organization["organization_id"],
            )

            remote_key = ("primary", "evt-1")
            self.fake_google.remote_events[remote_key]["summary"] = "Status Google - zmiana z Google"
            detail = self.services["task_service"].check_task_calendar_sync(
                int(created_task["task_id"]),
                actor_user=self.user,
                actor="Ola",
                organization_id=self.organization["organization_id"],
            )
            assert detail is not None
            self.assertEqual(detail["task"]["external_calendar_sync_state"], "wymaga_uwagi")
            self.assertIn("tytul", detail["task"]["external_calendar_sync_message"])
            self.assertEqual(detail["task"]["external_calendar_last_sync_source"], "google")

            del self.fake_google.remote_events[remote_key]
            detail = self.services["task_service"].check_task_calendar_sync(
                int(created_task["task_id"]),
                actor_user=self.user,
                actor="Ola",
                organization_id=self.organization["organization_id"],
            )
            assert detail is not None
            self.assertEqual(detail["task"]["external_calendar_sync_state"], "brak_w_google")
            self.assertIsNone(detail["task"]["external_calendar_event_id"])

            detail = self.services["task_service"].sync_task_calendar(
                int(created_task["task_id"]),
                actor_user=self.user,
                actor="Ola",
                organization_id=self.organization["organization_id"],
            )
            assert detail is not None
            self.assertEqual(detail["task"]["external_calendar_sync_state"], "zsynchronizowano")
            self.assertEqual(detail["task"]["external_calendar_event_id"], "evt-2")


class CalendarHttpTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        self.fake_google = FakeGoogleCalendarAdapter()
        self.services["calendar_service"].google_adapter = self.fake_google
        self.admin = self._ensure_admin()
        self.organization = self.services["organization_service"].create_organization(
            {"name": "Klient HTTP", "slug": "klient-http", "is_active": 1},
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
                "login": "ewa-admin",
                "display_name": "Ewa Admin",
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
                "login": "ewa-http",
                "display_name": "Ewa HTTP",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": self.organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )
        self.server = create_server("127.0.0.1", 0, self.services)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

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

    def test_calendar_endpoints_and_public_ics_feed_work(self) -> None:
        cookie = self._login("ewa-http", "1234")

        response, payload = self._request(
            "POST",
            "/api/user-calendars",
            body=json.dumps(
                {
                    "display_name": "Sluzbowy plan dnia",
                    "description": "Wlasny kalendarz sluzbowy pracownika",
                    "calendar_kind": "inne",
                    "default_duration_minutes": 120,
                    "is_active": True,
                }
            ),
            headers={"Content-Type": "application/json", "Cookie": cookie},
        )
        self.assertEqual(response.status, 201)
        created_calendar = json.loads(payload.decode("utf-8"))
        self.assertEqual(created_calendar["display_name"], "Sluzbowy plan dnia")
        self.assertEqual(created_calendar["calendar_kind"], "inne")
        self.assertEqual(created_calendar["default_duration_minutes"], 120)
        self.assertIn("/api/calendar-feeds/", created_calendar["feed_url"])

        response, payload = self._request(
            "POST",
            "/api/user-calendars",
            body=json.dumps(
                {
                    "display_name": "Nie powinien powstac",
                    "description": "Nadmiarowy payload nie moze utworzyc kalendarza.",
                    "calendar_kind": "inne",
                    "default_duration_minutes": 30,
                    "user_id": 999,
                    "organization_id": 999,
                    "calendar_id": 999,
                    "actor_user_id": 999,
                    "role": "admin",
                    "created_at": "2099-01-01T00:00:00",
                    "updated_at": "2099-01-01T00:00:00",
                    "google_access_token": "secret-access-token",
                    "google_refresh_token": "secret-refresh-token",
                    "oauth_state": "secret-state",
                    "is_admin": True,
                    "owner_user_id": 999,
                }
            ),
            headers={"Content-Type": "application/json", "Cookie": cookie},
        )
        self.assertEqual(response.status, 400, payload.decode("utf-8"))
        error_payload = json.loads(payload.decode("utf-8"))
        self.assertIn("display_name", error_payload["error"])
        self.assertIn("external_calendar_id", error_payload["error"])

        response, payload = self._request("GET", "/api/user-calendars", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        calendars_after_rejected_create = json.loads(payload.decode("utf-8"))
        self.assertEqual(len(calendars_after_rejected_create), 1)
        self.assertFalse(any(item["display_name"] == "Nie powinien powstac" for item in calendars_after_rejected_create))

        response, payload = self._request(
            "POST",
            f"/api/tasks?organization_id={self.organization['organization_id']}",
            body=json.dumps(
                {
                    "title": "Obiad rodzinny",
                    "task_type": "wydarzenie",
                    "status": "nowe",
                    "priority": "normalny",
                    "due_at": "2099-07-01T18:00",
                    "calendar_id": created_calendar["user_calendar_id"],
                }
            ),
            headers={"Content-Type": "application/json", "Cookie": cookie},
        )
        self.assertEqual(response.status, 201)
        created_task = json.loads(payload.decode("utf-8"))
        self.assertEqual(created_task["calendar_name"], "Sluzbowy plan dnia")
        self.assertEqual(created_task["calendar_duration_minutes"], 120)

        response, payload = self._request(
            "GET",
            f"/api/calendar-feeds/{created_calendar['sync_token']}.ics",
        )
        self.assertEqual(response.status, 200)
        self.assertIn("text/calendar", response.getheader("Content-Type", ""))
        ics_body = payload.decode("utf-8")
        self.assertIn("SUMMARY:Obiad rodzinny", ics_body)
        self.assertIn("X-WR-CALNAME:Sluzbowy plan dnia", ics_body)

        response, payload = self._request(
            "PATCH",
            f"/api/user-calendars/{created_calendar['user_calendar_id']}",
            body=json.dumps({"display_name": "Sluzbowy plan dnia po korekcie", "default_duration_minutes": 90}),
            headers={"Content-Type": "application/json", "Cookie": cookie},
        )
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        updated_calendar = json.loads(payload.decode("utf-8"))
        self.assertEqual(updated_calendar["display_name"], "Sluzbowy plan dnia po korekcie")
        self.assertEqual(updated_calendar["default_duration_minutes"], 90)

        response, payload = self._request(
            "PATCH",
            f"/api/user-calendars/{created_calendar['user_calendar_id']}",
            body=json.dumps(
                {
                    "display_name": "Nie powinno zmienic kalendarza",
                    "default_duration_minutes": 15,
                    "user_id": 999,
                    "organization_id": 999,
                    "calendar_id": 999,
                    "actor_user_id": 999,
                    "role": "admin",
                    "created_at": "2099-01-01T00:00:00",
                    "updated_at": "2099-01-01T00:00:00",
                    "google_access_token": "secret-access-token",
                    "google_refresh_token": "secret-refresh-token",
                    "oauth_state": "secret-state",
                    "is_admin": True,
                    "owner_user_id": 999,
                }
            ),
            headers={"Content-Type": "application/json", "Cookie": cookie},
        )
        self.assertEqual(response.status, 400, payload.decode("utf-8"))
        error_payload = json.loads(payload.decode("utf-8"))
        self.assertIn("display_name", error_payload["error"])
        self.assertIn("external_calendar_id", error_payload["error"])

        response, payload = self._request("GET", "/api/user-calendars", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        calendars_after_rejected_update = json.loads(payload.decode("utf-8"))
        self.assertEqual(len(calendars_after_rejected_update), 1)
        self.assertEqual(calendars_after_rejected_update[0]["display_name"], "Sluzbowy plan dnia po korekcie")
        self.assertEqual(calendars_after_rejected_update[0]["default_duration_minutes"], 90)

        admin_cookie = self._login("ewa-admin", "1234")
        response, payload = self._request(
            "PATCH",
            f"/api/user-calendars/{created_calendar['user_calendar_id']}",
            body=json.dumps({"display_name": "Nie powinno zmienic cudzego kalendarza"}),
            headers={"Content-Type": "application/json", "Cookie": admin_cookie},
        )
        self.assertEqual(response.status, 404, payload.decode("utf-8"))

        response, payload = self._request("GET", "/api/user-calendars", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200, payload.decode("utf-8"))
        calendars_after_cross_user_update = json.loads(payload.decode("utf-8"))
        self.assertEqual(calendars_after_cross_user_update[0]["display_name"], "Sluzbowy plan dnia po korekcie")

    def test_http_operator_cannot_create_family_calendar(self) -> None:
        cookie = self._login("ewa-http", "1234")

        response, payload = self._request(
            "POST",
            "/api/user-calendars",
            body=json.dumps(
                {
                    "display_name": "Rodzinny",
                    "calendar_kind": "rodzinny",
                    "default_duration_minutes": 120,
                    "is_active": True,
                }
            ),
            headers={"Content-Type": "application/json", "Cookie": cookie},
        )

        self.assertEqual(response.status, 400)
        self.assertIn("Administrator organizacji", payload.decode("utf-8"))

    def test_http_google_calendar_connection_requires_approval_and_exposes_admin_snapshot(self) -> None:
        with patch("app.api.http_server.google_calendar_direct_enabled", return_value=True), patch(
            "app.services.calendar_service.google_calendar_direct_enabled",
            return_value=True,
        ):
            operator_cookie = self._login("ewa-http", "1234")

            response, payload = self._request(
                "POST",
                "/api/google-calendar/connect",
                body=json.dumps({}),
                headers={"Content-Type": "application/json", "Cookie": operator_cookie},
            )
            self.assertEqual(response.status, 400)
            self.assertIn("Potwierdz", payload.decode("utf-8"))

            response, payload = self._request(
                "POST",
                "/api/google-calendar/connect",
                body=json.dumps({"confirm_work_account_visibility": True}),
                headers={"Content-Type": "application/json", "Cookie": operator_cookie},
            )
            self.assertEqual(response.status, 200)
            connection_payload = json.loads(payload.decode("utf-8"))
            parsed = urlsplit(connection_payload["authorization_url"])
            state_token = parse_qs(parsed.query)["state"][0]

            finalized = self.services["calendar_service"].finalize_google_calendar_connection(state_token, "kod-http")
            self.assertFalse(finalized["connected"])
            self.assertTrue(finalized["approval_pending"])

            response, payload = self._request(
                "GET",
                "/api/google-calendar/status",
                headers={"Cookie": operator_cookie},
            )
            self.assertEqual(response.status, 200)
            status = json.loads(payload.decode("utf-8"))
            self.assertTrue(status["approval_pending"])
            self.assertEqual(status["google_email"], "ola.calendar@example.com")

            response, payload = self._request(
                "GET",
                "/api/google-calendar/external-calendars",
                headers={"Cookie": operator_cookie},
            )
            self.assertEqual(response.status, 400)
            self.assertIn("czeka jeszcze na zatwierdzenie", payload.decode("utf-8"))

            admin_cookie = self._login("ewa-admin", "1234")
            response, payload = self._request(
                "GET",
                f"/api/google-calendar/admin-users?organization_id={self.organization['organization_id']}",
                headers={"Cookie": admin_cookie},
            )
            self.assertEqual(response.status, 200)
            snapshot = json.loads(payload.decode("utf-8"))
            operator_snapshot = next(item for item in snapshot if int(item["user_id"]) == int(self.user["user_id"]))
            self.assertEqual(operator_snapshot["google_connection_status"], "pending_approval")
            self.assertEqual(operator_snapshot["google_connection_email"], "ola.calendar@example.com")
            self.assertTrue(operator_snapshot["google_connection_employee_visibility_confirmed"])

            response, payload = self._request(
                "POST",
                f"/api/google-calendar/connections/{self.user['user_id']}/approve",
                headers={"Cookie": admin_cookie},
            )
            self.assertEqual(response.status, 200)
            approved = json.loads(payload.decode("utf-8"))
            self.assertTrue(approved["connected"])
            self.assertEqual(approved["approved_by_login"], "ewa-admin")

            response, payload = self._request(
                "GET",
                "/api/google-calendar/external-calendars",
                headers={"Cookie": operator_cookie},
            )
            self.assertEqual(response.status, 200)
            external_calendars = json.loads(payload.decode("utf-8"))
            self.assertEqual(len(external_calendars), 2)

    def test_http_assignment_of_organization_calendar_to_user_allows_sync_without_own_google_account(self) -> None:
        with patch("app.api.http_server.google_calendar_direct_enabled", return_value=True), patch(
            "app.services.calendar_service.google_calendar_direct_enabled",
            return_value=True,
        ):
            admin_cookie = self._login("ewa-admin", "1234")
            operator_cookie = self._login("ewa-http", "1234")

            response, payload = self._request(
                "POST",
                "/api/google-calendar/connect",
                body=json.dumps({"confirm_work_account_visibility": True}),
                headers={"Content-Type": "application/json", "Cookie": admin_cookie},
            )
            self.assertEqual(response.status, 200)
            connection_payload = json.loads(payload.decode("utf-8"))
            parsed = urlsplit(connection_payload["authorization_url"])
            state_token = parse_qs(parsed.query)["state"][0]
            finalized = self.services["calendar_service"].finalize_google_calendar_connection(state_token, "kod-admin-http")
            self.assertTrue(finalized["connected"])

            response, payload = self._request(
                "POST",
                "/api/user-calendars",
                body=json.dumps(
                    {
                        "display_name": "Kalendarz organizacji HTTP",
                        "provider": "google_api",
                        "external_calendar_id": "family",
                        "description": "Kalendarz firmowy przypisywany pracownikom",
                        "calendar_kind": "organizacja",
                        "linked_organization_id": self.organization["organization_id"],
                        "default_duration_minutes": 50,
                        "is_active": True,
                    }
                ),
                headers={"Content-Type": "application/json", "Cookie": admin_cookie},
            )
            self.assertEqual(response.status, 201)
            created_calendar = json.loads(payload.decode("utf-8"))
            self.assertEqual(created_calendar["provider"], "google_api")

            response, payload = self._request(
                "POST",
                "/api/google-calendar/assignments",
                body=json.dumps(
                    {
                        "user_id": self.user["user_id"],
                        "user_calendar_id": created_calendar["user_calendar_id"],
                    }
                ),
                headers={"Content-Type": "application/json", "Cookie": admin_cookie},
            )
            self.assertEqual(response.status, 200)
            assigned = json.loads(payload.decode("utf-8"))
            self.assertEqual(assigned["access_mode"], "assigned")

            response, payload = self._request(
                "GET",
                "/api/user-calendars",
                headers={"Cookie": operator_cookie},
            )
            self.assertEqual(response.status, 200)
            visible_calendars = json.loads(payload.decode("utf-8"))
            self.assertEqual(len(visible_calendars), 1)
            self.assertEqual(visible_calendars[0]["access_mode"], "assigned")
            self.assertEqual(visible_calendars[0]["display_name"], "Kalendarz organizacji HTTP")

            response, payload = self._request(
                "POST",
                f"/api/tasks?organization_id={self.organization['organization_id']}",
                body=json.dumps(
                    {
                        "title": "Wpis z przypisanego kalendarza",
                        "task_type": "wydarzenie",
                        "status": "nowe",
                        "priority": "normalny",
                        "due_at": "2099-07-01T18:00",
                        "calendar_id": created_calendar["user_calendar_id"],
                    }
                ),
                headers={"Content-Type": "application/json", "Cookie": operator_cookie},
            )
            self.assertEqual(response.status, 201)
            created_task = json.loads(payload.decode("utf-8"))
            self.assertEqual(created_task["calendar_access_mode"], "assigned")
            self.assertEqual(created_task["external_calendar_event_id"], "evt-1")
            self.assertEqual(self.fake_google.upserted_events[-1]["access_token"], "access-kod-admin-http")

            response, _ = self._request(
                "DELETE",
                f"/api/google-calendar/assignments/{self.user['user_id']}",
                headers={"Cookie": admin_cookie},
            )
            self.assertEqual(response.status, 200)


if __name__ == "__main__":
    unittest.main()
