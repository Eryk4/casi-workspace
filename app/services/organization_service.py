from __future__ import annotations

import re
from typing import Any

from app.repositories.event_repository import EventRepository
from app.repositories.organization_repository import OrganizationRepository


class OrganizationError(ValueError):
    pass


class OrganizationPermissionError(PermissionError):
    pass


class OrganizationService:
    def __init__(
        self,
        organization_repository: OrganizationRepository,
        event_repository: EventRepository,
    ) -> None:
        self.organization_repository = organization_repository
        self.event_repository = event_repository

    def ensure_default_setup(self, default_admin_login: str) -> dict[str, Any]:
        organization = self.organization_repository.ensure_default_organization()
        self.organization_repository.assign_legacy_records_to_default(
            int(organization["organization_id"]),
            default_admin_login,
        )
        return organization

    def list_organizations(self, actor_user: dict[str, Any]) -> list[dict[str, Any]]:
        if actor_user.get("is_global_admin"):
            return self.organization_repository.list_organizations()

        organization_id = actor_user.get("organization_id")
        if not organization_id:
            return []
        organization = self.organization_repository.get_by_id(int(organization_id))
        return [organization] if organization else []

    def create_organization(self, payload: dict[str, Any], actor_user: dict[str, Any], actor_login: str) -> dict[str, Any]:
        self._require_global_admin(actor_user)
        normalized = self._normalize_payload(payload)

        if self.organization_repository.get_by_name(normalized["name"]):
            raise OrganizationError("Organizacja o takiej nazwie już istnieje.")
        if self.organization_repository.get_by_slug(normalized["slug"]):
            raise OrganizationError("Organizacja o takim identyfikatorze katalogu już istnieje.")

        if normalized.get("telegram_chat_id"):
            existing_by_chat = self.organization_repository.get_by_telegram_chat_id(normalized["telegram_chat_id"])
            if existing_by_chat:
                raise OrganizationError("Ten kanal Telegram jest juz przypisany do innej organizacji.")

        organization_id = self.organization_repository.create(normalized)
        created = self.organization_repository.get_by_id(organization_id)
        assert created is not None

        self.event_repository.log(
            event_type="organization_created",
            invoice_id=None,
            source=None,
            status_before=None,
            status_after=None,
            decision_reason=f"Utworzono organizację {created['name']}.",
            actor=actor_login,
            organization_id=created["organization_id"],
            details={"organization_id": created["organization_id"], "slug": created["slug"]},
        )
        return created

    def update_organization(
        self,
        organization_id: int,
        payload: dict[str, Any],
        actor_user: dict[str, Any],
        actor_login: str,
    ) -> dict[str, Any]:
        self._require_global_admin(actor_user)
        current = self.organization_repository.get_by_id(organization_id)
        if not current:
            raise OrganizationError("Nie znaleziono organizacji.")

        normalized = self._normalize_payload(payload, current=current)
        if normalized.get("name") and normalized["name"] != current["name"]:
            existing_by_name = self.organization_repository.get_by_name(normalized["name"])
            if existing_by_name and int(existing_by_name["organization_id"]) != organization_id:
                raise OrganizationError("Organizacja o takiej nazwie już istnieje.")
        if normalized.get("slug") and normalized["slug"] != current["slug"]:
            existing_by_slug = self.organization_repository.get_by_slug(normalized["slug"])
            if existing_by_slug and int(existing_by_slug["organization_id"]) != organization_id:
                raise OrganizationError("Organizacja o takim identyfikatorze katalogu już istnieje.")

        if "telegram_chat_id" in normalized and normalized["telegram_chat_id"] != (current.get("telegram_chat_id") or ""):
            if normalized["telegram_chat_id"]:
                existing_by_chat = self.organization_repository.get_by_telegram_chat_id(normalized["telegram_chat_id"])
                if existing_by_chat and int(existing_by_chat["organization_id"]) != organization_id:
                    raise OrganizationError("Ten kanal Telegram jest juz przypisany do innej organizacji.")

        self.organization_repository.update(organization_id, normalized)
        refreshed = self.organization_repository.get_by_id(organization_id)
        assert refreshed is not None

        self.event_repository.log(
            event_type="organization_updated",
            invoice_id=None,
            source=None,
            status_before=None,
            status_after=None,
            decision_reason=f"Zmieniono organizację {refreshed['name']}.",
            actor=actor_login,
            organization_id=refreshed["organization_id"],
            details={"organization_id": organization_id, "updates": list(normalized.keys())},
        )
        return refreshed

    def resolve_data_scope(self, actor_user: dict[str, Any], requested_organization_id: int | None) -> int | None:
        if actor_user.get("is_global_admin"):
            if requested_organization_id is None:
                return None
            organization = self.organization_repository.get_by_id(requested_organization_id)
            if not organization:
                raise OrganizationError("Wybrana organizacja nie istnieje.")
            return int(organization["organization_id"])

        organization_id = actor_user.get("organization_id")
        if not organization_id:
            raise OrganizationPermissionError("To konto nie ma przypisanej organizacji.")
        return int(organization_id)

    def resolve_write_scope(self, actor_user: dict[str, Any], requested_organization_id: int | None) -> int | None:
        scope = self.resolve_data_scope(actor_user, requested_organization_id)
        if actor_user.get("is_global_admin") and scope is None:
            raise OrganizationError("Wybierz organizację przed wykonaniem tej operacji.")
        if scope is not None:
            organization = self.organization_repository.get_by_id(scope)
            if not organization:
                raise OrganizationError("Wybrana organizacja nie istnieje.")
            if not organization.get("is_active"):
                raise OrganizationError("Nie można pracować na organizacji oznaczonej jako nieaktywna.")
        return scope

    def normalize_user_organization_id(self, actor_user: dict[str, Any] | None, payload: dict[str, Any]) -> int | None:
        raw_value = payload.get("organization_id")
        requested_organization_id = self._parse_optional_id(raw_value)

        if actor_user is None:
            return requested_organization_id

        if actor_user.get("is_global_admin"):
            if requested_organization_id is None:
                return None
            organization = self.organization_repository.get_by_id(requested_organization_id)
            if not organization:
                raise OrganizationError("Wybrana organizacja nie istnieje.")
            return int(organization["organization_id"])

        actor_organization_id = actor_user.get("organization_id")
        if not actor_organization_id:
            raise OrganizationPermissionError("To konto nie ma przypisanej organizacji.")
        if requested_organization_id not in {None, int(actor_organization_id)}:
            raise OrganizationPermissionError("Nie można przypisać użytkownika do innej organizacji.")
        return int(actor_organization_id)

    def _normalize_payload(self, payload: dict[str, Any], current: dict[str, Any] | None = None) -> dict[str, Any]:
        if current is None:
            name = (payload.get("name") or "").strip()
            slug_source = payload.get("slug")
            is_active = 1 if payload.get("is_active", True) not in {False, 0, "0", "false"} else 0
            if not name:
                raise OrganizationError("Nazwa organizacji jest wymagana.")
            slug = self._slugify(slug_source or name)
            if not slug:
                raise OrganizationError("Identyfikator katalogu organizacji jest wymagany.")
            return {
                "name": name,
                "slug": slug,
                "telegram_chat_id": self._normalize_telegram_chat_id(payload.get("telegram_chat_id")),
                "telegram_chat_name": self._normalize_optional_text(payload.get("telegram_chat_name")),
                "is_active": is_active,
            }

        updates: dict[str, Any] = {}
        if "name" in payload:
            name = (payload.get("name") or "").strip()
            if not name:
                raise OrganizationError("Nazwa organizacji jest wymagana.")
            updates["name"] = name
        if "slug" in payload:
            slug = self._slugify(payload.get("slug") or payload.get("name") or current["slug"])
            if not slug:
                raise OrganizationError("Identyfikator katalogu organizacji jest wymagany.")
            updates["slug"] = slug
        if "is_active" in payload:
            updates["is_active"] = 1 if payload.get("is_active") not in {False, 0, "0", "false"} else 0
        if "telegram_chat_id" in payload:
            updates["telegram_chat_id"] = self._normalize_telegram_chat_id(payload.get("telegram_chat_id"))
        if "telegram_chat_name" in payload:
            updates["telegram_chat_name"] = self._normalize_optional_text(payload.get("telegram_chat_name"))
        return updates

    def _slugify(self, value: Any) -> str:
        normalized = re.sub(r"[^A-Za-z0-9]+", "-", str(value or "").strip().lower())
        return normalized.strip("-")

    def _normalize_telegram_chat_id(self, value: Any) -> str | None:
        normalized = str(value or "").strip()
        if not normalized:
            return None
        if not re.fullmatch(r"-?\d+", normalized):
            raise OrganizationError("ID kanalu Telegram musi byc liczba, na przyklad -1001234567890.")
        return normalized

    def _normalize_optional_text(self, value: Any) -> str | None:
        normalized = str(value or "").strip()
        return normalized or None

    def _parse_optional_id(self, value: Any) -> int | None:
        normalized = str(value or "").strip()
        if not normalized:
            return None
        if not normalized.isdigit():
            raise OrganizationError("Nieprawidłowy identyfikator organizacji.")
        return int(normalized)

    def _require_global_admin(self, actor_user: dict[str, Any]) -> None:
        if not actor_user.get("is_global_admin"):
            raise OrganizationPermissionError("Tylko administrator globalny może zarządzać organizacjami.")
