from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import secrets
from typing import Any

from app.config import (
    DEFAULT_ADMIN_LOGIN,
    DEFAULT_ADMIN_PASSWORD,
    SESSION_DURATION_HOURS,
    SESSION_MAX_ACTIVE_DEVICES_PER_ACCOUNT,
)
from app.domain.constants import (
    GUEST_ROLE,
    KNOWLEDGE_ASSISTANT_USE_CAPABILITY,
    KNOWLEDGE_CAPABILITIES,
    KNOWLEDGE_DOWNLOAD_CAPABILITY,
    KNOWLEDGE_MANAGE_CAPABILITY,
    KNOWLEDGE_READ_CAPABILITY,
    KNOWLEDGE_SYNC_CAPABILITY,
    KNOWLEDGE_UPLOAD_CAPABILITY,
    KNOWLEDGE_UPLOAD_DEFAULT_ROLES,
    OPERATOR_ROLE,
    SYSTEM_OWNER_ROLE,
    USER_MANAGEMENT_ROLES,
    USER_ROLES,
    default_capabilities_for_role,
)
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


MAX_ACTIVE_DEVICES_PER_ACCOUNT = SESSION_MAX_ACTIVE_DEVICES_PER_ACCOUNT


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
                "display_name": "Wlasciciel systemu",
                "password": DEFAULT_ADMIN_PASSWORD,
                "role": SYSTEM_OWNER_ROLE,
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
        capabilities_map = self.user_repository.list_capabilities_map([int(item["user_id"]) for item in users])
        memberships_map = self.user_repository.list_memberships_map([int(item["user_id"]) for item in users])
        modules_map = self.organization_repository.list_enabled_modules_map(
            [int(item["organization_id"]) for item in users if item.get("organization_id")]
        )
        return [
            self._sanitize_user(
                item,
                capabilities_map.get(int(item["user_id"]), []),
                memberships=memberships_map.get(int(item["user_id"]), []),
                organization_modules=(
                    modules_map.get(int(item["organization_id"]), []) if item.get("organization_id") else []
                ),
            )
            for item in users
        ]

    def list_capabilities(self, user: dict[str, Any] | None) -> tuple[str, ...]:
        if not user or not user.get("user_id"):
            return tuple()

        stored = self.user_repository.list_capabilities(int(user["user_id"]))
        if stored:
            return tuple(capability for capability in KNOWLEDGE_CAPABILITIES if capability in stored)

        can_upload = int(user.get("can_upload_knowledge") or 0)
        return self._resolve_capabilities(
            role=str(user.get("role") or ""),
            requested_capabilities=None,
            can_upload_knowledge=can_upload,
        )

    def has_capability(self, user: dict[str, Any] | None, capability_code: str) -> bool:
        return capability_code in self.list_capabilities(user)

    def create_user(
        self,
        payload: dict[str, Any],
        actor_login: str,
        actor_user_id: int | None,
        actor_user: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        login = (payload.get("login") or "").strip()
        password = str(payload.get("password") or "").strip()
        role = (payload.get("role") or OPERATOR_ROLE).strip()
        display_name = (payload.get("display_name") or "").strip() or login
        telegram_user_id = self._normalize_telegram_user_id(payload.get("telegram_user_id"))
        try:
            organization_id = self.organization_service.normalize_user_organization_id(actor_user, payload)
        except (OrganizationError, OrganizationPermissionError) as error:
            raise self._as_auth_error(error) from error
        self._ensure_user_management_permission(actor_user)

        is_active = 1 if payload.get("is_active", True) not in {False, 0, "0", "false"} else 0
        telegram_reminders_enabled = self._normalize_telegram_reminder_flag(
            payload.get("telegram_reminders_enabled"),
            default=1,
        )
        reminder_quiet_hours_start = self._normalize_optional_time(payload.get("reminder_quiet_hours_start"))
        reminder_quiet_hours_end = self._normalize_optional_time(payload.get("reminder_quiet_hours_end"))
        reminder_repeat_interval_minutes = self._normalize_repeat_interval_minutes(
            payload.get("reminder_repeat_interval_minutes"),
            default=0,
        )
        requested_capabilities = payload.get("capabilities")
        can_upload_knowledge = self._normalize_knowledge_upload_flag(
            payload.get("can_upload_knowledge"),
            default=1 if role in KNOWLEDGE_UPLOAD_DEFAULT_ROLES else 0,
        )

        if not login:
            raise AuthError("Login jest wymagany.")
        if not password:
            raise AuthError("Haslo jest wymagane.")
        if role not in USER_ROLES:
            raise AuthError("Nieprawidlowa rola uzytkownika.")

        self._validate_role_assignment(role=role, organization_id=organization_id, actor_user=actor_user)
        capabilities = self._resolve_capabilities(
            role=role,
            requested_capabilities=requested_capabilities,
            can_upload_knowledge=can_upload_knowledge,
        )
        can_upload_knowledge = 1 if self._capabilities_allow_upload(capabilities) else 0

        if self.user_repository.get_by_login(login):
            raise AuthError("Uzytkownik o takim loginie juz istnieje.")
        if telegram_user_id and self.user_repository.get_by_telegram_user_id(telegram_user_id):
            raise AuthError("To ID uzytkownika Telegram jest juz przypisane do innego konta.")

        password_salt = secrets.token_hex(16)
        password_hash = self._hash_password(password, password_salt)
        user_id = self.user_repository.create(
            {
                "login": login,
                "display_name": display_name,
                "telegram_user_id": telegram_user_id,
                "telegram_reminders_enabled": telegram_reminders_enabled,
                "reminder_quiet_hours_start": reminder_quiet_hours_start,
                "reminder_quiet_hours_end": reminder_quiet_hours_end,
                "reminder_repeat_interval_minutes": reminder_repeat_interval_minutes,
                "organization_id": organization_id,
                "password_hash": password_hash,
                "password_salt": password_salt,
                "role": role,
                "can_upload_knowledge": can_upload_knowledge,
                "is_active": is_active,
                "created_by_user_id": actor_user_id,
            }
        )
        self.user_repository.sync_primary_membership(user_id)
        self.user_repository.replace_capabilities(user_id, list(capabilities))
        created = self.user_repository.get_by_id(user_id)
        assert created is not None

        self.event_repository.log(
            event_type="user_created",
            invoice_id=None,
            organization_id=organization_id,
            source=None,
            status_before=None,
            status_after=None,
            decision_reason=f"Utworzono konto uzytkownika {login}.",
            actor=actor_login,
            details={
                "user_id": user_id,
                "login": login,
                "role": role,
                "telegram_user_id": telegram_user_id,
                "organization_id": organization_id,
                "telegram_reminders_enabled": telegram_reminders_enabled,
                "reminder_quiet_hours_start": reminder_quiet_hours_start,
                "reminder_quiet_hours_end": reminder_quiet_hours_end,
                "reminder_repeat_interval_minutes": reminder_repeat_interval_minutes,
                "can_upload_knowledge": can_upload_knowledge,
                "capabilities": list(capabilities),
            },
        )
        organization_modules = []
        organization_module_shortcuts = {}
        if created.get("organization_id"):
            organization_modules = self.organization_repository.list_enabled_modules(int(created["organization_id"]))
            organization_module_shortcuts = self._load_organization_module_shortcuts(int(created["organization_id"]))
        memberships = self.user_repository.list_memberships(int(created["user_id"]))
        return self._sanitize_user(
            created,
            list(capabilities),
            memberships=memberships,
            organization_modules=organization_modules,
            organization_module_shortcuts=organization_module_shortcuts,
        )

    def update_user(
        self,
        user_id: int,
        payload: dict[str, Any],
        actor_login: str,
        actor_user: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        current = self.user_repository.get_by_id(user_id)
        if not current:
            raise AuthError("Nie znaleziono uzytkownika.")
        current_capabilities = self.user_repository.list_capabilities(user_id)
        self._ensure_user_management_permission(actor_user)
        if actor_user and not actor_user.get("is_global_admin") and int(current.get("organization_id") or 0) != int(actor_user.get("organization_id") or 0):
            raise PermissionError("Nie mozna zmieniac uzytkownika z innej organizacji.")

        updates: dict[str, Any] = {}
        if "display_name" in payload:
            updates["display_name"] = (payload.get("display_name") or "").strip() or current["login"]
        if "telegram_user_id" in payload:
            telegram_user_id = self._normalize_telegram_user_id(payload.get("telegram_user_id"))
            existing = self.user_repository.get_by_telegram_user_id(telegram_user_id) if telegram_user_id else None
            if existing and int(existing["user_id"]) != int(user_id):
                raise AuthError("To ID uzytkownika Telegram jest juz przypisane do innego konta.")
            updates["telegram_user_id"] = telegram_user_id
        if "telegram_reminders_enabled" in payload:
            updates["telegram_reminders_enabled"] = self._normalize_telegram_reminder_flag(
                payload.get("telegram_reminders_enabled"),
                default=int(current.get("telegram_reminders_enabled") if current.get("telegram_reminders_enabled") is not None else 1),
            )
        if "reminder_quiet_hours_start" in payload:
            updates["reminder_quiet_hours_start"] = self._normalize_optional_time(payload.get("reminder_quiet_hours_start"))
        if "reminder_quiet_hours_end" in payload:
            updates["reminder_quiet_hours_end"] = self._normalize_optional_time(payload.get("reminder_quiet_hours_end"))
        if "reminder_repeat_interval_minutes" in payload:
            updates["reminder_repeat_interval_minutes"] = self._normalize_repeat_interval_minutes(
                payload.get("reminder_repeat_interval_minutes"),
                default=int(current.get("reminder_repeat_interval_minutes") or 0),
            )
        if "organization_id" in payload:
            try:
                updates["organization_id"] = self.organization_service.normalize_user_organization_id(actor_user, payload)
            except (OrganizationError, OrganizationPermissionError) as error:
                raise self._as_auth_error(error) from error
        if "role" in payload:
            role = (payload.get("role") or "").strip()
            if role not in USER_ROLES:
                raise AuthError("Nieprawidlowa rola uzytkownika.")
            updates["role"] = role
        if "is_active" in payload:
            updates["is_active"] = 1 if payload.get("is_active") not in {False, 0, "0", "false"} else 0
        if payload.get("password"):
            password_salt = secrets.token_hex(16)
            updates["password_salt"] = password_salt
            updates["password_hash"] = self._hash_password(str(payload["password"]).strip(), password_salt)
            self.session_repository.delete_for_user(user_id)

        next_role = updates.get("role", current["role"])
        next_organization_id = updates.get("organization_id", current.get("organization_id"))
        self._validate_role_assignment(
            role=next_role,
            organization_id=next_organization_id,
            actor_user=actor_user,
        )
        requested_upload = self._normalize_knowledge_upload_flag(
            payload.get("can_upload_knowledge"),
            default=1 if self._capabilities_allow_upload(current_capabilities) else 0,
        )
        requested_capabilities = payload.get("capabilities") if "capabilities" in payload else None
        capabilities = self._resolve_capabilities(
            role=next_role,
            requested_capabilities=requested_capabilities,
            can_upload_knowledge=requested_upload,
            existing_capabilities=current_capabilities,
        )
        updates["can_upload_knowledge"] = 1 if self._capabilities_allow_upload(capabilities) else 0

        self.user_repository.update(user_id, updates)
        self.user_repository.sync_primary_membership(user_id)
        self.user_repository.replace_capabilities(user_id, list(capabilities))
        refreshed = self.user_repository.get_by_id(user_id)
        assert refreshed is not None

        self.event_repository.log(
            event_type="user_updated",
            invoice_id=None,
            organization_id=refreshed.get("organization_id"),
            source=None,
            status_before=None,
            status_after=None,
            decision_reason=f"Zmieniono konto uzytkownika {refreshed['login']}.",
            actor=actor_login,
            details={"user_id": user_id, "updates": list(updates.keys()), "capabilities": list(capabilities)},
        )
        organization_modules = []
        organization_module_shortcuts = {}
        if refreshed.get("organization_id"):
            organization_modules = self.organization_repository.list_enabled_modules(int(refreshed["organization_id"]))
            organization_module_shortcuts = self._load_organization_module_shortcuts(int(refreshed["organization_id"]))
        memberships = self.user_repository.list_memberships(int(refreshed["user_id"]))
        return self._sanitize_user(
            refreshed,
            list(capabilities),
            memberships=memberships,
            organization_modules=organization_modules,
            organization_module_shortcuts=organization_module_shortcuts,
        )

    def login(
        self,
        login: str,
        password: str,
        ip_address: str | None,
        user_agent: str | None,
        device_id: str | None = None,
        device_label: str | None = None,
    ) -> tuple[dict[str, Any], str]:
        user = self.user_repository.get_by_login(login.strip())
        if not user or not user["is_active"]:
            raise AuthError("Nieprawidlowy login lub haslo.")
        expected_hash = self._hash_password(password, user["password_salt"])
        if not hmac.compare_digest(expected_hash, user["password_hash"]):
            raise AuthError("Nieprawidlowy login lub haslo.")

        self.session_repository.delete_expired()
        normalized_device_id = self._normalize_device_id(device_id)
        normalized_device_label = self._normalize_device_label(device_label)
        if normalized_device_id:
            self.session_repository.delete_for_user_and_device_id(int(user["user_id"]), normalized_device_id)
        active_device_count = self.session_repository.count_active_devices_for_user(
            int(user["user_id"]),
            exclude_device_id=normalized_device_id,
        )
        if MAX_ACTIVE_DEVICES_PER_ACCOUNT > 0 and active_device_count >= MAX_ACTIVE_DEVICES_PER_ACCOUNT:
            raise AuthError(
                "To konto moze byc zalogowane jednoczesnie maksymalnie "
                f"na {MAX_ACTIVE_DEVICES_PER_ACCOUNT} urzadzeniach."
            )
        session_token = secrets.token_urlsafe(32)
        expires_at = self._expires_at()
        self.session_repository.create(
            {
                "user_id": user["user_id"],
                "token_hash": self._hash_token(session_token),
                "device_id": normalized_device_id,
                "device_label": normalized_device_label,
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
            decision_reason=f"Zalogowano uzytkownika {refreshed['login']}.",
            actor=refreshed["login"],
            details={"user_id": refreshed["user_id"]},
        )
        organization_modules = []
        organization_module_shortcuts = {}
        if refreshed.get("organization_id"):
            organization_modules = self.organization_repository.list_enabled_modules(int(refreshed["organization_id"]))
            organization_module_shortcuts = self._load_organization_module_shortcuts(int(refreshed["organization_id"]))
        capabilities = self.user_repository.list_capabilities(int(refreshed["user_id"]))
        memberships = self.user_repository.list_memberships(int(refreshed["user_id"]))
        return self._build_session_user_payload(
            refreshed,
            capabilities,
            memberships=memberships,
            organization_modules=organization_modules,
            organization_module_shortcuts=organization_module_shortcuts,
            device_id=normalized_device_id,
        ), session_token

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
                decision_reason=f"Wylogowano uzytkownika {session['login']}.",
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
        capabilities = self.user_repository.list_capabilities(int(session["user_id"]))
        memberships = self.user_repository.list_memberships(int(session["user_id"]))
        organization_modules = []
        organization_module_shortcuts = {}
        if session.get("organization_id"):
            organization_modules = self.organization_repository.list_enabled_modules(int(session["organization_id"]))
            organization_module_shortcuts = self._load_organization_module_shortcuts(int(session["organization_id"]))
        return self._build_session_user_payload(
            session,
            capabilities,
            memberships=memberships,
            organization_modules=organization_modules,
            organization_module_shortcuts=organization_module_shortcuts,
            device_id=session.get("device_id"),
        )

    def update_workspace_state(
        self,
        user: dict[str, Any] | None,
        workspace_state: dict[str, Any],
        *,
        device_id: str | None = None,
    ) -> dict[str, Any]:
        if not user:
            raise PermissionError("Brak aktywnej sesji.")
        normalized_state = self._normalize_workspace_state(workspace_state)
        self.user_repository.update_workspace_state(
            int(user["user_id"]),
            json.dumps(normalized_state, ensure_ascii=True, separators=(",", ":")),
            device_id=self._normalize_device_id(device_id),
        )
        refreshed = self.user_repository.get_by_id(int(user["user_id"]))
        assert refreshed is not None
        capabilities = self.user_repository.list_capabilities(int(refreshed["user_id"]))
        memberships = self.user_repository.list_memberships(int(refreshed["user_id"]))
        organization_modules = []
        organization_module_shortcuts = {}
        if refreshed.get("organization_id"):
            organization_modules = self.organization_repository.list_enabled_modules(int(refreshed["organization_id"]))
            organization_module_shortcuts = self._load_organization_module_shortcuts(int(refreshed["organization_id"]))
        return self._build_session_user_payload(
            refreshed,
            capabilities,
            memberships=memberships,
            organization_modules=organization_modules,
            organization_module_shortcuts=organization_module_shortcuts,
            device_id=device_id,
        )

    def get_personal_note(self, user: dict[str, Any] | None) -> dict[str, Any]:
        if not user:
            raise PermissionError("Brak aktywnej sesji.")
        refreshed = self.user_repository.get_by_id(int(user["user_id"]))
        if not refreshed:
            raise PermissionError("Nie znaleziono uzytkownika.")
        return self._build_personal_note_payload(refreshed)

    def update_personal_note(
        self,
        user: dict[str, Any] | None,
        *,
        personal_note_text: Any,
        actor_login: str,
    ) -> dict[str, Any]:
        if not user:
            raise PermissionError("Brak aktywnej sesji.")
        normalized_text = self._normalize_personal_note_text(personal_note_text)
        timestamp = now_iso()
        self.user_repository.update(
            int(user["user_id"]),
            {
                "personal_note_text": normalized_text,
                "personal_note_updated_at": timestamp,
            },
        )
        refreshed = self.user_repository.get_by_id(int(user["user_id"]))
        if not refreshed:
            raise PermissionError("Nie znaleziono uzytkownika.")
        self.event_repository.log(
            event_type="user_personal_note_updated",
            invoice_id=None,
            organization_id=refreshed.get("organization_id"),
            source=None,
            status_before=None,
            status_after=None,
            decision_reason="Zaktualizowano notatke osobista uzytkownika.",
            actor=actor_login,
            details={"user_id": refreshed["user_id"]},
        )
        return self._build_personal_note_payload(refreshed)

    def require_role(self, user: dict[str, Any] | None, allowed_roles: tuple[str, ...]) -> None:
        if not user:
            raise PermissionError("Brak aktywnej sesji.")
        if user["role"] not in allowed_roles:
            raise PermissionError("Brak uprawnien do tej operacji.")

    def require_capability(self, user: dict[str, Any] | None, capability: str) -> None:
        if not user:
            raise PermissionError("Brak aktywnej sesji.")
        if capability not in set(user.get("capabilities") or []):
            raise PermissionError("To konto nie ma wymaganego uprawnienia do tego modułu.")

    def has_capability(self, user: dict[str, Any] | None, capability: str) -> bool:
        return bool(user and capability in set(user.get("capabilities") or []))

    def _sanitize_user(
        self,
        user: dict[str, Any],
        capabilities: list[str] | None = None,
        *,
        memberships: list[dict[str, Any]] | None = None,
        organization_modules: list[str] | None = None,
        organization_module_shortcuts: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        normalized_capabilities = sorted(
            set(capabilities if capabilities is not None else self.user_repository.list_capabilities(int(user["user_id"])))
        )
        normalized_memberships = self._serialize_memberships(
            memberships if memberships is not None else self.user_repository.list_memberships(int(user["user_id"]))
        )
        normalized_modules = sorted(set(organization_modules or []))
        return {
            "user_id": user["user_id"],
            "login": user["login"],
            "display_name": user.get("display_name") or user["login"],
            "telegram_user_id": user.get("telegram_user_id"),
            "telegram_reminders_enabled": int(user.get("telegram_reminders_enabled") if user.get("telegram_reminders_enabled") is not None else 1),
            "reminder_quiet_hours_start": user.get("reminder_quiet_hours_start"),
            "reminder_quiet_hours_end": user.get("reminder_quiet_hours_end"),
            "reminder_repeat_interval_minutes": int(user.get("reminder_repeat_interval_minutes") or 0),
            "role": user["role"],
            "can_upload_knowledge": 1 if self._capabilities_allow_upload(normalized_capabilities) else 0,
            "capabilities": normalized_capabilities,
            "is_active": user["is_active"],
            "organization_id": user.get("organization_id"),
            "organization_name": user.get("organization_name"),
            "organization_slug": user.get("organization_slug"),
            "organization_modules": normalized_modules,
            "organization_module_shortcuts": dict(organization_module_shortcuts or {}),
            "memberships": normalized_memberships,
            "primary_membership": normalized_memberships[0] if normalized_memberships else None,
            "is_global_admin": self._is_system_owner(user["role"], user.get("organization_id")),
            "last_login_at": user.get("last_login_at"),
            "created_at": user.get("created_at"),
            "updated_at": user.get("updated_at"),
            "created_by_login": user.get("created_by_login"),
        }

    def _build_session_user_payload(
        self,
        user: dict[str, Any],
        capabilities: list[str] | tuple[str, ...] | None = None,
        *,
        memberships: list[dict[str, Any]] | None = None,
        organization_modules: list[str] | None = None,
        organization_module_shortcuts: dict[str, str] | None = None,
        device_id: str | None = None,
    ) -> dict[str, Any]:
        payload = self._sanitize_user(
            user,
            list(capabilities or []),
            memberships=memberships,
            organization_modules=organization_modules,
            organization_module_shortcuts=organization_module_shortcuts,
        )
        payload["workspace_state"] = self._parse_workspace_state(user)
        payload["workspace_state_updated_at"] = user.get("workspace_state_updated_at")
        payload["workspace_state_device_id"] = user.get("workspace_state_device_id")
        payload["current_device_id"] = self._normalize_device_id(device_id)
        payload["max_active_devices"] = MAX_ACTIVE_DEVICES_PER_ACCOUNT
        return payload

    def _normalize_telegram_user_id(self, value: Any) -> str | None:
        normalized = str(value or "").strip()
        return normalized or None

    def _normalize_telegram_reminder_flag(self, value: Any, default: int) -> int:
        normalized = str(value).strip().lower() if value is not None else ""
        if normalized == "":
            return int(default)
        return 0 if normalized in {"0", "false", "nie", "no", "off"} else 1

    def _normalize_optional_time(self, value: Any) -> str | None:
        normalized = str(value or "").strip()
        if not normalized:
            return None
        if len(normalized) != 5 or normalized[2] != ":":
            raise AuthError("Godzina musi miec format HH:MM.")
        hours, minutes = normalized.split(":", 1)
        if not (hours.isdigit() and minutes.isdigit()):
            raise AuthError("Godzina musi miec format HH:MM.")
        hours_int = int(hours)
        minutes_int = int(minutes)
        if hours_int not in range(24) or minutes_int not in range(60):
            raise AuthError("Godzina musi miec poprawny zakres.")
        return f"{hours_int:02d}:{minutes_int:02d}"

    def _load_organization_module_shortcuts(self, organization_id: int) -> dict[str, str]:
        organization = self.organization_repository.get_by_id(int(organization_id))
        if not organization:
            return {}
        raw_value = organization.get("module_shortcuts_json")
        if not raw_value:
            return {}
        try:
            parsed = json.loads(str(raw_value))
        except json.JSONDecodeError:
            return {}
        if not isinstance(parsed, dict):
            return {}
        normalized: dict[str, str] = {}
        for key, value in parsed.items():
            normalized_key = str(key or "").strip()
            normalized_value = str(value or "").strip()
            if normalized_key and normalized_value:
                normalized[normalized_key] = normalized_value
        return normalized

    def _normalize_repeat_interval_minutes(self, value: Any, default: int) -> int:
        normalized = str(value or "").strip()
        if not normalized:
            return int(default)
        if not normalized.isdigit():
            raise AuthError("Interwal ponowienia przypomnienia musi byc liczba minut.")
        return min(int(normalized), 1440)

    def _normalize_device_id(self, value: Any) -> str | None:
        normalized = str(value or "").strip()
        if not normalized:
            return None
        return normalized[:120]

    def _normalize_device_label(self, value: Any) -> str | None:
        normalized = str(value or "").strip()
        if not normalized:
            return None
        return normalized[:160]

    def _normalize_workspace_state(self, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise AuthError("Stan workspace musi byc obiektem JSON.")
        return value

    def _normalize_personal_note_text(self, value: Any) -> str:
        normalized = str(value or "").replace("\r\n", "\n").strip()
        if len(normalized) > 20000:
            raise AuthError("Notatka osobista moze miec maksymalnie 20000 znakow.")
        return normalized

    def _parse_workspace_state(self, user: dict[str, Any]) -> dict[str, Any] | None:
        raw_value = user.get("workspace_state_json")
        if not raw_value:
            return None
        try:
            parsed = json.loads(str(raw_value))
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None

    def _build_personal_note_payload(self, user: dict[str, Any]) -> dict[str, Any]:
        return {
            "user_id": user.get("user_id"),
            "personal_note_text": str(user.get("personal_note_text") or ""),
            "personal_note_updated_at": user.get("personal_note_updated_at"),
        }

    def _normalize_knowledge_upload_flag(self, value: Any, default: int) -> int:
        normalized = str(value).strip().lower() if value is not None else ""
        if normalized == "":
            return int(default)
        return 0 if normalized in {"0", "false", "nie", "no", "off"} else 1

    def _normalize_capability_list(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            raw_values = [item.strip() for item in value.split(",")]
        else:
            raw_values = [str(item).strip() for item in list(value)]
        normalized = [item for item in raw_values if item in KNOWLEDGE_CAPABILITIES]
        return sorted(set(normalized))

    def _resolve_capabilities(
        self,
        *,
        role: str,
        requested_capabilities: Any,
        can_upload_knowledge: int,
        existing_capabilities: list[str] | None = None,
    ) -> tuple[str, ...]:
        if requested_capabilities is None:
            capabilities = set(existing_capabilities or default_capabilities_for_role(role))
            capabilities.update(default_capabilities_for_role(role))
        else:
            capabilities = set(self._normalize_capability_list(requested_capabilities))
            capabilities.add(KNOWLEDGE_READ_CAPABILITY)

        if can_upload_knowledge:
            capabilities.update({KNOWLEDGE_UPLOAD_CAPABILITY, KNOWLEDGE_SYNC_CAPABILITY})
        else:
            capabilities.discard(KNOWLEDGE_UPLOAD_CAPABILITY)
            capabilities.discard(KNOWLEDGE_SYNC_CAPABILITY)

        if role == GUEST_ROLE:
            capabilities = {KNOWLEDGE_READ_CAPABILITY, KNOWLEDGE_DOWNLOAD_CAPABILITY}

        capabilities.intersection_update(KNOWLEDGE_CAPABILITIES)
        capabilities.add(KNOWLEDGE_READ_CAPABILITY)
        return tuple(sorted(capabilities))

    def _capabilities_allow_upload(self, capabilities: list[str] | tuple[str, ...]) -> bool:
        return KNOWLEDGE_UPLOAD_CAPABILITY in set(capabilities)

    def _serialize_memberships(self, memberships: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for membership in memberships or []:
            normalized.append(
                {
                    "organization_membership_id": membership.get("organization_membership_id"),
                    "organization_id": membership.get("organization_id"),
                    "organization_name": membership.get("organization_name"),
                    "organization_slug": membership.get("organization_slug"),
                    "role": membership.get("role"),
                    "membership_status": membership.get("membership_status") or "active",
                    "is_primary": bool(membership.get("is_primary", 0)),
                    "granted_at": membership.get("granted_at"),
                    "updated_at": membership.get("updated_at"),
                }
            )
        normalized.sort(
            key=lambda item: (
                0 if item.get("is_primary") else 1,
                str(item.get("organization_name") or "").lower(),
                int(item.get("organization_id") or 0),
            )
        )
        return normalized

    def _ensure_user_management_permission(self, actor_user: dict[str, Any] | None) -> None:
        if actor_user is None:
            return
        if actor_user.get("role") not in USER_MANAGEMENT_ROLES:
            raise PermissionError("To konto nie moze zarzadzac uzytkownikami.")

    def _validate_role_assignment(
        self,
        *,
        role: str,
        organization_id: int | None,
        actor_user: dict[str, Any] | None,
    ) -> None:
        if role == SYSTEM_OWNER_ROLE:
            if organization_id is not None:
                raise AuthError("Wlasciciel systemu nie moze byc przypisany do organizacji.")
            if actor_user is not None and not actor_user.get("is_global_admin"):
                raise PermissionError("Tylko wlasciciel systemu moze nadawac ta role.")
            return

        if organization_id is None:
            raise AuthError("Ta rola wymaga przypisania do organizacji.")

    def _is_system_owner(self, role: Any, organization_id: Any) -> bool:
        return role == SYSTEM_OWNER_ROLE and not organization_id

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
