from __future__ import annotations

import json
import re
from typing import Any

from app.repositories.dashboard_view_repository import DashboardViewRepository
from app.repositories.event_repository import EventRepository
from app.repositories.organization_repository import OrganizationRepository
from app.utils import json_dumps


class DashboardViewService:
    def __init__(
        self,
        dashboard_view_repository: DashboardViewRepository,
        event_repository: EventRepository,
        organization_repository: OrganizationRepository,
    ) -> None:
        self.dashboard_view_repository = dashboard_view_repository
        self.event_repository = event_repository
        self.organization_repository = organization_repository

    def list_views(
        self,
        module_key: str,
        *,
        organization_id: int | None = None,
        include_hidden: bool = False,
    ) -> list[dict[str, Any]]:
        return self.dashboard_view_repository.list_views(
            module_key=module_key,
            organization_id=organization_id,
            include_hidden=include_hidden,
        )

    def create_view(
        self,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any]:
        if organization_id is None:
            raise ValueError("Wybierz organizacje przed dodaniem widoku.")
        organization = self.organization_repository.get_by_id(organization_id)
        if not organization or not organization.get("is_active"):
            raise ValueError("Wybrana organizacja nie istnieje albo jest nieaktywna.")

        module_key = self._normalize_module_key(payload.get("module_key") or "dashboard")
        view_name = self._normalize_required_text(payload.get("view_name"), "Nazwa widoku")
        view_slug = self._normalize_slug(payload.get("view_slug") or view_name)
        existing = self.dashboard_view_repository.get_by_slug(
            module_key=module_key,
            view_slug=view_slug,
            organization_id=organization_id,
        )
        if existing:
            raise ValueError("Widok o tym identyfikatorze juz istnieje.")
        view_id = self.dashboard_view_repository.create(
            {
                "organization_id": organization_id,
                "module_key": module_key,
                "view_slug": view_slug,
                "view_name": view_name,
                "description": self._normalize_optional_text(payload.get("description")),
                "view_state_json": self._normalize_json_text(payload.get("view_state_json") or payload.get("view_state") or {}),
                "is_shared": 1 if payload.get("is_shared", True) not in {False, 0, "0", "false"} else 0,
                "is_default": 1 if payload.get("is_default", False) in {True, 1, "1", "true"} else 0,
                "created_by_user_id": int(actor_user["user_id"]),
            }
        )
        created = self.dashboard_view_repository.get_by_id(view_id, organization_id=organization_id)
        assert created is not None
        self.event_repository.log(
            event_type="saved_view_created",
            invoice_id=None,
            organization_id=organization_id,
            source="VIEW",
            status_before=None,
            status_after=None,
            decision_reason=f"Dodano widok {created['view_name']}.",
            actor=actor,
            details={
                "saved_view_id": view_id,
                "module_key": module_key,
                "view_slug": view_slug,
                "created_by_user_id": actor_user.get("user_id"),
            },
        )
        return self._decorate_view(created)

    def update_view(
        self,
        saved_view_id: int,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any] | None:
        current = self.dashboard_view_repository.get_by_id(saved_view_id, organization_id=organization_id)
        if not current:
            return None
        updates: dict[str, Any] = {}
        for key in ("view_slug", "view_name", "description"):
            if key in payload:
                updates[key] = self._normalize_optional_text(payload.get(key)) if key == "description" else self._normalize_required_text(payload.get(key), "Nazwa widoku" if key == "view_name" else "Identyfikator")
        if "view_state_json" in payload or "view_state" in payload:
            updates["view_state_json"] = self._normalize_json_text(payload.get("view_state_json") or payload.get("view_state") or {})
        if "is_shared" in payload:
            updates["is_shared"] = 1 if payload.get("is_shared") not in {False, 0, "0", "false"} else 0
        if "is_default" in payload:
            updates["is_default"] = 1 if payload.get("is_default") in {True, 1, "1", "true"} else 0
        if updates:
            self.dashboard_view_repository.update(saved_view_id, updates)
            refreshed = self.dashboard_view_repository.get_by_id(saved_view_id, organization_id=organization_id)
            assert refreshed is not None
            self.event_repository.log(
                event_type="saved_view_updated",
                invoice_id=None,
                organization_id=organization_id,
                source="VIEW",
                status_before=None,
                status_after=None,
                decision_reason=f"Zmieniono widok {refreshed['view_name']}.",
                actor=actor,
                details={"saved_view_id": saved_view_id, "updated_fields": sorted(updates.keys())},
            )
            return self._decorate_view(refreshed)
        return self._decorate_view(current)

    def delete_view(self, saved_view_id: int, *, organization_id: int | None, actor: str) -> None:
        current = self.dashboard_view_repository.get_by_id(saved_view_id, organization_id=organization_id)
        if not current:
            return None
        self.dashboard_view_repository.delete(saved_view_id, organization_id=organization_id)
        self.event_repository.log(
            event_type="saved_view_deleted",
            invoice_id=None,
            organization_id=organization_id,
            source="VIEW",
            status_before=None,
            status_after=None,
            decision_reason=f"Usunieto widok {current['view_name']}.",
            actor=actor,
            details={"saved_view_id": saved_view_id},
        )
        return self._decorate_view(current)

    def apply_view(
        self,
        saved_view_id: int,
        *,
        organization_id: int | None,
    ) -> dict[str, Any] | None:
        current = self.dashboard_view_repository.get_by_id(saved_view_id, organization_id=organization_id)
        if not current:
            return None
        return self._decorate_view(current)

    def _decorate_view(self, view: dict[str, Any]) -> dict[str, Any]:
        result = dict(view)
        raw = result.get("view_state_json")
        if isinstance(raw, str) and raw.strip():
            try:
                result["view_state_json"] = json.loads(raw)
            except json.JSONDecodeError:
                result["view_state_json"] = raw
        return result

    def _normalize_required_text(self, value: Any, field_label: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError(f"{field_label} jest wymagana.")
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized

    def _normalize_optional_text(self, value: Any) -> str | None:
        normalized = str(value or "").strip()
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized or None

    def _normalize_slug(self, value: Any) -> str:
        normalized = self._normalize_required_text(value, "Identyfikator")
        normalized = normalized.lower()
        normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
        normalized = re.sub(r"-+", "-", normalized).strip("-")
        if not normalized:
            raise ValueError("Identyfikator widoku jest nieprawidlowy.")
        return normalized

    def _normalize_module_key(self, value: Any) -> str:
        normalized = self._normalize_required_text(value, "Moduł")
        normalized = normalized.lower()
        if normalized not in {"dashboard", "tasks", "billing", "inbox", "health", "invoices"}:
            raise ValueError("Nieprawidlowy modul widoku.")
        return normalized

    def _normalize_json_text(self, value: Any) -> str:
        if isinstance(value, str):
            candidate = value.strip()
            if not candidate:
                return "{}"
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError as error:
                raise ValueError("Nieprawidlowy format danych JSON.") from error
            return json_dumps(parsed)
        return json_dumps(value if value is not None else {})
