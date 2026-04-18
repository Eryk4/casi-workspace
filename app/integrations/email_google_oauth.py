from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.config import (
    EMAIL_GOOGLE_CLIENT_ID,
    EMAIL_GOOGLE_CLIENT_SECRET,
    EMAIL_GOOGLE_OAUTH_CALLBACK_PATH,
    EMAIL_GOOGLE_OAUTH_SCOPES,
    PUBLIC_BASE_URL,
)


class EmailGoogleOAuthError(RuntimeError):
    pass


class EmailGoogleOAuthAdapter:
    auth_base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    token_url = "https://oauth2.googleapis.com/token"
    user_info_url = "https://openidconnect.googleapis.com/v1/userinfo"

    def is_enabled(self, public_base_url: str | None = None) -> bool:
        return bool(EMAIL_GOOGLE_CLIENT_ID and EMAIL_GOOGLE_CLIENT_SECRET and self._resolved_public_base_url(public_base_url))

    def callback_url(self, public_base_url: str | None = None) -> str:
        resolved_public_base_url = self._resolved_public_base_url(public_base_url)
        if not resolved_public_base_url:
            raise EmailGoogleOAuthError("Brakuje publicznego adresu aplikacji do integracji Google Workspace.")
        return f"{resolved_public_base_url}{EMAIL_GOOGLE_OAUTH_CALLBACK_PATH}"

    def build_authorization_url(
        self,
        state_token: str,
        *,
        login_hint: str | None = None,
        public_base_url: str | None = None,
    ) -> str:
        if not self.is_enabled(public_base_url):
            raise EmailGoogleOAuthError(
                "Integracja Google Workspace dla e-mail nie jest skonfigurowana. "
                "Uzupelnij dane OAuth i publiczny adres aplikacji."
            )
        params = {
            "client_id": EMAIL_GOOGLE_CLIENT_ID,
            "redirect_uri": self.callback_url(public_base_url),
            "response_type": "code",
            "scope": " ".join(EMAIL_GOOGLE_OAUTH_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
            "state": state_token,
        }
        if login_hint:
            params["login_hint"] = login_hint
        return f"{self.auth_base_url}?{urlencode(params)}"

    def exchange_code_for_tokens(self, code: str, *, public_base_url: str | None = None) -> dict[str, Any]:
        response = self._post_form(
            self.token_url,
            {
                "code": code,
                "client_id": EMAIL_GOOGLE_CLIENT_ID,
                "client_secret": EMAIL_GOOGLE_CLIENT_SECRET,
                "redirect_uri": self.callback_url(public_base_url),
                "grant_type": "authorization_code",
            },
        )
        return self._normalize_token_response(response)

    def refresh_tokens(self, refresh_token: str) -> dict[str, Any]:
        response = self._post_form(
            self.token_url,
            {
                "refresh_token": refresh_token,
                "client_id": EMAIL_GOOGLE_CLIENT_ID,
                "client_secret": EMAIL_GOOGLE_CLIENT_SECRET,
                "grant_type": "refresh_token",
            },
        )
        normalized = self._normalize_token_response(response)
        if not normalized.get("refresh_token"):
            normalized["refresh_token"] = refresh_token
        return normalized

    def fetch_user_info(self, access_token: str) -> dict[str, Any]:
        return self._request_json("GET", self.user_info_url, access_token=access_token)

    def build_xoauth2_string(self, username: str, access_token: str) -> bytes:
        raw = f"user={username}\x01auth=Bearer {access_token}\x01\x01"
        return base64.b64encode(raw.encode("utf-8"))

    def _resolved_public_base_url(self, public_base_url: str | None = None) -> str:
        return str(public_base_url or PUBLIC_BASE_URL or "").strip().rstrip("/")

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
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        final_headers = {"Accept": "application/json"}
        if headers:
            final_headers.update(headers)
        if access_token:
            final_headers["Authorization"] = f"Bearer {access_token}"

        request = Request(url, data=data, headers=final_headers, method=method)
        try:
            with urlopen(request, timeout=20) as response:
                body = response.read()
        except HTTPError as error:
            details = error.read().decode("utf-8", errors="ignore")
            raise EmailGoogleOAuthError(
                f"Google Workspace zwrocil blad HTTP {error.code}. {details[:300]}".strip()
            ) from error
        except URLError as error:
            raise EmailGoogleOAuthError("Nie udalo sie polaczyc z Google Workspace OAuth.") from error

        if not body:
            return {}
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as error:
            raise EmailGoogleOAuthError("Google Workspace zwrocil nieprawidlowy format odpowiedzi.") from error

    def _normalize_token_response(self, payload: dict[str, Any]) -> dict[str, Any]:
        access_token = str(payload.get("access_token") or "").strip()
        if not access_token:
            raise EmailGoogleOAuthError("Google nie zwrocil tokenu dostepowego dla skrzynki e-mail.")
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
