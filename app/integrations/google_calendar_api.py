from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from app.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_OAUTH_CALLBACK_PATH,
    GOOGLE_OAUTH_SCOPES,
    PUBLIC_BASE_URL,
)


class GoogleCalendarIntegrationError(RuntimeError):
    pass


class GoogleCalendarApiAdapter:
    auth_base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    token_url = "https://oauth2.googleapis.com/token"
    calendar_list_url = "https://www.googleapis.com/calendar/v3/users/me/calendarList"
    user_info_url = "https://openidconnect.googleapis.com/v1/userinfo"

    def is_enabled(self) -> bool:
        return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET and PUBLIC_BASE_URL)

    def callback_url(self) -> str:
        if not PUBLIC_BASE_URL:
            raise GoogleCalendarIntegrationError("Brakuje publicznego adresu aplikacji do integracji Google Calendar.")
        return f"{PUBLIC_BASE_URL}{GOOGLE_OAUTH_CALLBACK_PATH}"

    def build_authorization_url(self, state_token: str) -> str:
        if not self.is_enabled():
            raise GoogleCalendarIntegrationError(
                "Integracja Google Calendar nie jest skonfigurowana. Uzupelnij dane OAuth i publiczny adres aplikacji."
            )
        params = {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": self.callback_url(),
            "response_type": "code",
            "scope": " ".join(GOOGLE_OAUTH_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
            "state": state_token,
        }
        return f"{self.auth_base_url}?{urlencode(params)}"

    def exchange_code_for_tokens(self, code: str) -> dict[str, Any]:
        response = self._post_form(
            self.token_url,
            {
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": self.callback_url(),
                "grant_type": "authorization_code",
            },
        )
        return self._normalize_token_response(response)

    def refresh_tokens(self, refresh_token: str) -> dict[str, Any]:
        response = self._post_form(
            self.token_url,
            {
                "refresh_token": refresh_token,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "grant_type": "refresh_token",
            },
        )
        normalized = self._normalize_token_response(response)
        if not normalized.get("refresh_token"):
            normalized["refresh_token"] = refresh_token
        return normalized

    def fetch_user_info(self, access_token: str) -> dict[str, Any]:
        return self._request_json(
            "GET",
            self.user_info_url,
            access_token=access_token,
        )

    def list_calendars(self, access_token: str) -> list[dict[str, Any]]:
        payload = self._request_json(
            "GET",
            self.calendar_list_url,
            access_token=access_token,
        )
        items = payload.get("items") or []
        result: list[dict[str, Any]] = []
        for item in items:
            result.append(
                {
                    "external_calendar_id": item.get("id"),
                    "external_calendar_name": item.get("summaryOverride") or item.get("summary") or item.get("id"),
                    "external_calendar_timezone": item.get("timeZone") or "Europe/Warsaw",
                    "is_primary": bool(item.get("primary")),
                    "access_role": item.get("accessRole"),
                }
            )
        result.sort(key=lambda entry: (not entry["is_primary"], str(entry["external_calendar_name"]).lower()))
        return result

    def upsert_event(
        self,
        access_token: str,
        *,
        external_calendar_id: str,
        event_id: str | None,
        event_payload: dict[str, Any],
    ) -> dict[str, Any]:
        encoded_calendar_id = quote(external_calendar_id, safe="")
        if event_id:
            encoded_event_id = quote(event_id, safe="")
            url = f"https://www.googleapis.com/calendar/v3/calendars/{encoded_calendar_id}/events/{encoded_event_id}"
            return self._request_json("PATCH", url, access_token=access_token, json_body=event_payload)
        url = f"https://www.googleapis.com/calendar/v3/calendars/{encoded_calendar_id}/events"
        return self._request_json("POST", url, access_token=access_token, json_body=event_payload)

    def delete_event(self, access_token: str, *, external_calendar_id: str, event_id: str) -> None:
        encoded_calendar_id = quote(external_calendar_id, safe="")
        encoded_event_id = quote(event_id, safe="")
        url = f"https://www.googleapis.com/calendar/v3/calendars/{encoded_calendar_id}/events/{encoded_event_id}"
        self._request_json("DELETE", url, access_token=access_token, allow_empty=True)

    def get_event(
        self,
        access_token: str,
        *,
        external_calendar_id: str,
        event_id: str,
    ) -> dict[str, Any] | None:
        encoded_calendar_id = quote(external_calendar_id, safe="")
        encoded_event_id = quote(event_id, safe="")
        url = f"https://www.googleapis.com/calendar/v3/calendars/{encoded_calendar_id}/events/{encoded_event_id}"
        final_headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        request = Request(url, headers=final_headers, method="GET")
        try:
            with urlopen(request, timeout=20) as response:
                body = response.read()
        except HTTPError as error:
            if error.code == 404:
                return None
            details = error.read().decode("utf-8", errors="ignore")
            raise GoogleCalendarIntegrationError(
                f"Google Calendar zwrocil blad HTTP {error.code}. {details[:300]}".strip()
            ) from error
        except URLError as error:
            raise GoogleCalendarIntegrationError("Nie udalo sie polaczyc z Google Calendar API.") from error

        if not body:
            return {}
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as error:
            raise GoogleCalendarIntegrationError("Google Calendar zwrocil nieprawidlowy format odpowiedzi.") from error

    def _post_form(self, url: str, form_payload: dict[str, Any]) -> dict[str, Any]:
        return self._request_json(
            "POST",
            url,
            data=urlencode(form_payload).encode("utf-8"),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    def _request_json(
        self,
        method: str,
        url: str,
        *,
        access_token: str | None = None,
        data: bytes | None = None,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        allow_empty: bool = False,
    ) -> dict[str, Any]:
        final_headers = {"Accept": "application/json"}
        if headers:
            final_headers.update(headers)
        if access_token:
            final_headers["Authorization"] = f"Bearer {access_token}"
        if json_body is not None:
            data = json.dumps(json_body).encode("utf-8")
            final_headers["Content-Type"] = "application/json; charset=utf-8"

        request = Request(url, data=data, headers=final_headers, method=method)
        try:
            with urlopen(request, timeout=20) as response:
                body = response.read()
        except HTTPError as error:
            details = error.read().decode("utf-8", errors="ignore")
            raise GoogleCalendarIntegrationError(
                f"Google Calendar zwrocil blad HTTP {error.code}. {details[:300]}".strip()
            ) from error
        except URLError as error:
            raise GoogleCalendarIntegrationError("Nie udalo sie polaczyc z Google Calendar API.") from error

        if not body:
            return {} if allow_empty else {}
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as error:
            if allow_empty:
                return {}
            raise GoogleCalendarIntegrationError("Google Calendar zwrocil nieprawidlowy format odpowiedzi.") from error

    def _normalize_token_response(self, payload: dict[str, Any]) -> dict[str, Any]:
        access_token = str(payload.get("access_token") or "").strip()
        if not access_token:
            raise GoogleCalendarIntegrationError("Google nie zwrocil tokenu dostepowego.")
        refresh_token = str(payload.get("refresh_token") or "").strip() or None
        expires_in_raw = payload.get("expires_in")
        try:
            expires_in = int(expires_in_raw)
        except (TypeError, ValueError):
            expires_in = 3600
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=max(60, expires_in - 30))
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_expires_at": expires_at.replace(microsecond=0).isoformat(),
            "scope": str(payload.get("scope") or "").strip(),
            "token_type": str(payload.get("token_type") or "").strip() or "Bearer",
        }
