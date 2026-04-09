from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
from typing import Any

from app.config import DEFAULT_ADMIN_LOGIN, DEFAULT_ADMIN_PASSWORD, SESSION_DURATION_HOURS
from app.domain.constants import USER_ROLES
from app.repositories.event_repository import EventRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.services.organization_service import (
    OrganizationError,
    OrganizationPermissionError,
    OrganizationService,
)
from app.utils import now_iso


class AuthError(Exception):
    pass


class PermissionError(AuthError):
    pass


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        session_repository: SessionRepository,
        event_repository: EventRepository,
        organization_repository: OrganizationRepository,
        organization_service: OrganizationService,
    ) -> None:
        self.user_repository = user_repository
        self.session_repository = session_repository
        self.event_repository = event_repository
        self.organization_repository = organization_repository
        self.organization_service = organization_service

    def ensure_default_admin(self) -> dict[str, Any] | None:
        if self.user_repository.count_all() > 0:
            return None
        return self.create_user(
            {
                "login": DEFAULT_ADMIN_LOGIN,
                "display_name": "Administrator",
                "password": DEFAULT_ADMIN_PASSWORD,
                "role": "administrator",
                "is_active": 1,
                "organization_id": None,
            },
            actor_login="system",
            actor_user_id=None,
            actor_user=None,
        )

    def list_users(
        self,
        actor_user: dict[str, Any] | None = None,
        requested_organization_id: int | None = None,
    ) -> list[dict[str, Any]]:
        if actor_user is None:
            organization_id = None
        else:
            try:
                organization_id = self.organization_service.resolve_data_scope(actor_user, requested_organization_id)
            except (OrganizationError, OrganizationPermissionError) as error:
                raise self._as_auth_error(error) from error
        users = self.user_repository.list_users(organization_id=organization_id)
        return [self._sanitize_user(item) for item in users]

    def create_user(
        self,
        payload: dict[str, Any],
        actor_login: str,
        actor_user_id: int | None,
        actor_user: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        login = (payload.get("login") or "").strip()
        password = str(payload.get("password") or "").strip()
        role = (payload.get("role") or "operator").strip()
        display_name = (payload.get("display_name") or "").strip() or login
        telegram_user_id = self._normalize_telegram_user_id(payload.get("telegram_user_id"))
        try:
            organization_id = self.organization_service.normalize_user_organization_id(actor_user, payload)
        except (OrganizationError, OrganizationPermissionError) as error:
            raise self._as_auth_error(error) from error
        is_active = 1 if payload.get("is_active", True) not in {False, 0, "0", "false"} else 0

        if not login:
            raise AuthError("Login jest wymagany.")
        if not password:
            raise AuthError("Hasło jest wymagane.")
        if role not in USER_ROLES:
            raise AuthError("Nieprawidłowa rola użytkownika.")
        if self.user_repository.get_by_login(login):
            raise AuthError("Użytkownik o takim loginie już istnieje.")
        if telegram_user_id and self.user_repository.get_by_telegram_user_id(telegram_user_id):
            raise AuthError("To ID użytkownika Telegram jest już przypisane do innego konta.")

        password_salt = secrets.token_hex(16)
        password_hash = self._hash_password(password, password_salt)
        user_id = self.user_repository.create(
            {
                "login": login,
                "display_name": display_name,
                "telegram_user_id": telegram_user_id,
                "organization_id": organization_id,
                "password_hash": password_hash,
                "password_salt": password_salt,
                "role": role,
                "is_active": is_active,
                "created_by_user_id": actor_user_id,
            }
        )
        created = self.user_repository.get_by_id(user_id)
        assert created is not None

        self.event_repository.log(
            event_type="user_created",
            invoice_id=None,
            organization_id=organization_id,
            source=None,
            status_before=None,
            status_after=None,
            decision_reason=f"Utworzono konto użytkownika {login}.",
            actor=actor_login,
            details={
                "user_id": user_id,
                "login": login,
                "role": role,
                "telegram_user_id": telegram_user_id,
                "organization_id": organization_id,
            },
        )
        return self._sanitize_user(created)

    def update_user(
        self,
        user_id: int,
        payload: dict[str, Any],
        actor_login: str,
        actor_user: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        current = self.user_repository.get_by_id(user_id)
        if not current:
            raise AuthError("Nie znaleziono użytkownika.")
        if actor_user and not actor_user.get("is_global_admin") and int(current.get("organization_id") or 0) != int(actor_user.get("organization_id") or 0):
            raise PermissionError("Nie można zmieniać użytkownika z innej organizacji.")

        updates: dict[str, Any] = {}
        if "display_name" in payload:
            updates["display_name"] = (payload.get("display_name") or "").strip() or current["login"]
        if "telegram_user_id" in payload:
            telegram_user_id = self._normalize_telegram_user_id(payload.get("telegram_user_id"))
            existing = self.user_repository.get_by_telegram_user_id(telegram_user_id) if telegram_user_id else None
            if existing and int(existing["user_id"]) != int(user_id):
                raise AuthError("To ID użytkownika Telegram jest już przypisane do innego konta.")
            updates["telegram_user_id"] = telegram_user_id
        if "organization_id" in payload:
            try:
                updates["organization_id"] = self.organization_service.normalize_user_organization_id(actor_user, payload)
            except (OrganizationError, OrganizationPermissionError) as error:
                raise self._as_auth_error(error) from error
        if "role" in payload:
            role = (payload.get("role") or "").strip()
            if role not in USER_ROLES:
                raise AuthError("Nieprawidłowa rola użytkownika.")
            updates["role"] = role
        if "is_active" in payload:
            updates["is_active"] = 1 if payload.get("is_active") not in {False, 0, "0", "false"} else 0
        if payload.get("password"):
            password_salt = secrets.token_hex(16)
            updates["password_salt"] = password_salt
            updates["password_hash"] = self._hash_password(str(payload["password"]).strip(), password_salt)
            self.session_repository.delete_for_user(user_id)

        self.user_repository.update(user_id, updates)
        refreshed = self.user_repository.get_by_id(user_id)
        assert refreshed is not None

        self.event_repository.log(
            event_type="user_updated",
            invoice_id=None,
            organization_id=refreshed.get("organization_id"),
            source=None,
            status_before=None,
            status_after=None,
            decision_reason=f"Zmieniono konto użytkownika {refreshed['login']}.",
            actor=actor_login,
            details={"user_id": user_id, "updates": list(updates.keys())},
        )
        return self._sanitize_user(refreshed)

    def login(self, login: str, password: str, ip_address: str | None, user_agent: str | None) -> tuple[dict[str, Any], str]:
        user = self.user_repository.get_by_login(login.strip())
        if not user or not user["is_active"]:
            raise AuthError("Nieprawidłowy login lub hasło.")
        expected_hash = self._hash_password(password, user["password_salt"])
        if not hmac.compare_digest(expected_hash, user["password_hash"]):
            raise AuthError("Nieprawidłowy login lub hasło.")

        self.session_repository.delete_expired()
        session_token = secrets.token_urlsafe(32)
        expires_at = self._expires_at()
        self.session_repository.create(
            {
                "user_id": user["user_id"],
                "token_hash": self._hash_token(session_token),
                "ip_address": ip_address,
                "user_agent": user_agent,
                "created_at": now_iso(),
                "last_seen_at": now_iso(),
                "expires_at": expires_at,
            }
        )
        self.user_repository.set_last_login(int(user["user_id"]))
        refreshed = self.user_repository.get_by_id(int(user["user_id"]))
        assert refreshed is not None

        self.event_repository.log(
            event_type="user_login",
            invoice_id=None,
            organization_id=refreshed.get("organization_id"),
            source=None,
            status_before=None,
            status_after=None,
            decision_reason=f"Zalogowano użytkownika {refreshed['login']}.",
            actor=refreshed["login"],
            details={"user_id": refreshed["user_id"]},
        )
        return self._sanitize_user(refreshed), session_token

    def logout(self, session_token: str, actor_login: str | None = None) -> None:
        token_hash = self._hash_token(session_token)
        session = self.session_repository.get_active_by_token_hash(token_hash)
        self.session_repository.delete_by_token_hash(token_hash)
        if session:
            self.event_repository.log(
                event_type="user_logout",
                invoice_id=None,
                organization_id=session.get("organization_id"),
                source=None,
                status_before=None,
                status_after=None,
                decision_reason=f"Wylogowano użytkownika {session['login']}.",
                actor=actor_login or session["login"],
                details={"user_id": session["user_id"]},
            )

    def get_current_user(self, session_token: str | None) -> dict[str, Any] | None:
        if not session_token:
            return None
        token_hash = self._hash_token(session_token)
        session = self.session_repository.get_active_by_token_hash(token_hash)
        if not session or not session["is_active"]:
            return None
        self.session_repository.touch(int(session["session_id"]))
        return {
            "user_id": session["user_id"],
            "login": session["login"],
            "display_name": session.get("display_name") or session["login"],
            "role": session["role"],
            "is_active": session["is_active"],
            "organization_id": session.get("organization_id"),
            "organization_name": session.get("organization_name"),
            "organization_slug": session.get("organization_slug"),
            "is_global_admin": session["role"] == "administrator" and not session.get("organization_id"),
        }

    def require_role(self, user: dict[str, Any] | None, allowed_roles: tuple[str, ...]) -> None:
        if not user:
            raise PermissionError("Brak aktywnej sesji.")
        if user["role"] not in allowed_roles:
            raise PermissionError("Brak uprawnień do tej operacji.")

    def _sanitize_user(self, user: dict[str, Any]) -> dict[str, Any]:
        return {
            "user_id": user["user_id"],
            "login": user["login"],
            "display_name": user.get("display_name") or user["login"],
            "telegram_user_id": user.get("telegram_user_id"),
            "role": user["role"],
            "is_active": user["is_active"],
            "organization_id": user.get("organization_id"),
            "organization_name": user.get("organization_name"),
            "organization_slug": user.get("organization_slug"),
            "is_global_admin": user["role"] == "administrator" and not user.get("organization_id"),
            "last_login_at": user.get("last_login_at"),
            "created_at": user.get("created_at"),
            "updated_at": user.get("updated_at"),
            "created_by_login": user.get("created_by_login"),
        }

    def _normalize_telegram_user_id(self, value: Any) -> str | None:
        normalized = str(value or "").strip()
        return normalized or None

    def _hash_password(self, password: str, salt: str) -> str:
        raw = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000)
        return raw.hex()

    def _hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _expires_at(self) -> str:
        return (
            datetime.now(timezone.utc) + timedelta(hours=SESSION_DURATION_HOURS)
        ).replace(microsecond=0).isoformat()

    def _as_auth_error(self, error: Exception) -> AuthError:
        if isinstance(error, OrganizationPermissionError):
            return PermissionError(str(error))
        return AuthError(str(error))
