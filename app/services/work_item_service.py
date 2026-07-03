from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

from app.domain.constants import (
    WORK_ITEM_PRIORITY_LEVELS,
    WORK_ITEM_SOURCE_TYPES,
    WORK_ITEM_STATUSES,
)
from app.repositories.event_repository import EventRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository
from app.repositories.work_item_repository import WorkItemRepository
from app.utils import json_dumps, now_iso, now_local_datetime_value, parse_datetime_flexible

_LOCAL_DATETIME_FORMAT = "%Y-%m-%dT%H:%M"
_DEFAULT_WORK_ITEM_SLA_WARNING_MINUTES = 120
_DEFAULT_WORK_ITEM_SLA_PRIORITY_TARGETS_MINUTES = {
    "niski": 72 * 60,
    "normalny": 24 * 60,
    "wysoki": 8 * 60,
    "krytyczny": 2 * 60,
}


class WorkItemService:
    def __init__(
        self,
        *,
        work_item_repository: WorkItemRepository,
        event_repository: EventRepository,
        user_repository: UserRepository,
        organization_repository: OrganizationRepository,
    ) -> None:
        self.work_item_repository = work_item_repository
        self.event_repository = event_repository
        self.user_repository = user_repository
        self.organization_repository = organization_repository

    def list_work_items(
        self,
        filters: dict[str, Any] | None = None,
        *,
        organization_id: int | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        normalized_filters = dict(filters or {})
        normalized_filters.setdefault("now_value", now_local_datetime_value())
        rows = self.work_item_repository.list_work_items(
            normalized_filters,
            organization_id=organization_id,
            limit=limit,
        )
        return [self._decorate_work_item(row) for row in rows]

    def get_work_item_detail(
        self,
        work_item_id: int,
        *,
        organization_id: int | None = None,
    ) -> dict[str, Any] | None:
        row = self.work_item_repository.get_by_id(work_item_id, organization_id=organization_id)
        if not row:
            return None
        return {
            "work_item": self._decorate_work_item(row),
            "history": self.work_item_repository.list_history(int(row["work_item_id"])),
        }

    def get_summary(
        self,
        *,
        organization_id: int | None = None,
    ) -> dict[str, Any]:
        summary = self.work_item_repository.summary(
            organization_id=organization_id,
            now_value=now_local_datetime_value(),
        )
        return {
            "generated_at": now_iso(),
            "counts": summary.get("counts") or {},
            "top_risk": [self._decorate_work_item(item) for item in list(summary.get("top_risk") or [])],
        }

    def get_sla_policy(
        self,
        *,
        organization_id: int | None,
    ) -> dict[str, Any]:
        if organization_id is None:
            raise ValueError("Wybierz organizacje, aby sprawdzic polityke SLA.")
        organization = self.organization_repository.get_by_id(int(organization_id))
        if not organization:
            raise ValueError("Wybrana organizacja nie istnieje.")
        policy = self._load_sla_policy_for_org(organization)
        return {
            "generated_at": now_iso(),
            "organization_id": int(organization["organization_id"]),
            "organization_name": organization.get("name"),
            "policy": policy,
        }

    def update_sla_policy(
        self,
        payload: dict[str, Any] | None,
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any]:
        if organization_id is None:
            raise ValueError("Wybierz organizacje, aby zapisac polityke SLA.")
        organization = self.organization_repository.get_by_id(int(organization_id))
        if not organization or not int(organization.get("is_active") or 0):
            raise ValueError("Wybrana organizacja nie istnieje albo jest nieaktywna.")
        payload = payload or {}
        if not isinstance(payload, dict):
            raise ValueError("Polityka SLA musi byc obiektem JSON.")
        current_policy = self._load_sla_policy_for_org(organization)
        next_policy = self._normalize_sla_policy_update(payload, current_policy=current_policy)

        self.organization_repository.update(
            int(organization_id),
            {
                "work_item_sla_policy_json": json_dumps(next_policy),
            },
        )
        self.event_repository.log(
            event_type="work_item_updated",
            invoice_id=None,
            organization_id=int(organization_id),
            source="WORK_ITEM",
            status_before=None,
            status_after=None,
            decision_reason="Zmieniono polityke SLA dla pozycji pracy.",
            actor=actor,
            details={
                "updated_by_user_id": int(actor_user["user_id"]),
                "policy": next_policy,
            },
        )
        refreshed = self.organization_repository.get_by_id(int(organization_id))
        assert refreshed is not None
        return {
            "saved_at": now_iso(),
            "organization_id": int(organization_id),
            "organization_name": refreshed.get("name"),
            "policy": self._load_sla_policy_for_org(refreshed),
        }

    def get_workload(
        self,
        *,
        organization_id: int | None,
        limit: int = 20,
    ) -> dict[str, Any]:
        rows = self.work_item_repository.assignee_workload(
            organization_id=organization_id,
            now_value=now_local_datetime_value(),
            limit=min(max(int(limit), 1), 200),
        )
        serialized_rows = [
            {
                "assigned_user_id": int(row.get("assigned_user_id") or 0) or None,
                "assigned_user_name": row.get("assigned_user_name") or "Nieprzypisane",
                "open_items": int(row.get("open_items") or 0),
                "escalated_items": int(row.get("escalated_items") or 0),
                "warning_items": int(row.get("warning_items") or 0),
                "overdue_sla_items": int(row.get("overdue_sla_items") or 0),
                "overdue_due_items": int(row.get("overdue_due_items") or 0),
                "avg_priority_score": round(float(row.get("avg_priority_score") or 0), 2),
                "max_priority_score": round(float(row.get("max_priority_score") or 0), 2),
            }
            for row in rows
        ]
        return {
            "generated_at": now_iso(),
            "items": serialized_rows,
            "summary": {
                "assignees": len(serialized_rows),
                "open_items": sum(int(item["open_items"]) for item in serialized_rows),
                "escalated_items": sum(int(item["escalated_items"]) for item in serialized_rows),
                "warning_items": sum(int(item["warning_items"]) for item in serialized_rows),
                "overdue_sla_items": sum(int(item["overdue_sla_items"]) for item in serialized_rows),
                "overdue_due_items": sum(int(item["overdue_due_items"]) for item in serialized_rows),
            },
        }

    def create_work_item(
        self,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any]:
        if organization_id is None:
            raise ValueError("Wybierz organizacje przed dodaniem pozycji pracy.")
        organization = self.organization_repository.get_by_id(int(organization_id))
        if not organization or not int(organization.get("is_active") or 0):
            raise ValueError("Wybrana organizacja nie istnieje albo jest nieaktywna.")
        sla_policy = self._load_sla_policy_for_org(organization)

        source_type = self._normalize_choice(
            payload.get("source_type"),
            WORK_ITEM_SOURCE_TYPES,
            "manual",
            "Nieprawidlowe zrodlo pozycji pracy.",
        )
        source_id = self._normalize_optional_id(payload.get("source_id"))
        title = str(payload.get("title") or "").strip()
        if not title:
            raise ValueError("Tytul pozycji pracy jest wymagany.")
        description = self._normalize_optional_text(payload.get("description"))
        status = self._normalize_choice(
            payload.get("status"),
            WORK_ITEM_STATUSES,
            "nowe",
            "Nieprawidlowy status pozycji pracy.",
        )
        requested_priority = self._normalize_choice(
            payload.get("priority_level"),
            WORK_ITEM_PRIORITY_LEVELS,
            "normalny",
            "Nieprawidlowy poziom priorytetu.",
        )
        assigned_user_id = self._validate_assigned_user(
            self._normalize_optional_id(payload.get("assigned_user_id")),
            organization_id=organization_id,
        )
        due_at = self._normalize_optional_local_datetime(payload.get("due_at"), "Termin ma nieprawidlowy format.")
        sla_deadline_at = self._normalize_optional_local_datetime(
            payload.get("sla_deadline_at"),
            "Termin SLA ma nieprawidlowy format.",
        )
        if sla_deadline_at is None and bool(sla_policy.get("auto_deadline_enabled")):
            sla_deadline_at = self._derive_sla_deadline_from_policy(
                priority_level=requested_priority,
                due_at=due_at,
                policy=sla_policy,
            )
        sla_warning_minutes = self._normalize_sla_warning_minutes(
            payload.get("sla_warning_minutes"),
            default_minutes=int(sla_policy.get("default_warning_minutes") or _DEFAULT_WORK_ITEM_SLA_WARNING_MINUTES),
        )
        sla_warning_at = self._build_sla_warning_at(
            sla_deadline_at=sla_deadline_at,
            sla_warning_minutes=sla_warning_minutes,
            explicit_warning_at=payload.get("sla_warning_at"),
        )
        metadata = self._normalize_metadata(payload.get("metadata"))
        metadata_json = json_dumps(metadata)

        working_item = {
            "source_type": source_type,
            "source_id": source_id,
            "title": title,
            "description": description,
            "status": status,
            "priority_level": requested_priority,
            "assigned_user_id": assigned_user_id,
            "due_at": due_at,
            "sla_deadline_at": sla_deadline_at,
            "sla_warning_minutes": sla_warning_minutes,
            "sla_warning_at": sla_warning_at,
            "metadata_json": metadata_json,
            "created_at": now_iso(),
            "sla_stage": self._derive_sla_stage(
                status=status,
                warning_at=sla_warning_at,
                deadline_at=sla_deadline_at,
                current_stage="on_track",
            ),
        }
        score = self._calculate_priority_score(working_item)
        priority_level = self._priority_level_from_score(score, minimum_level=requested_priority)

        work_item_id = self.work_item_repository.create(
            {
                "organization_id": int(organization_id),
                "source_type": source_type,
                "source_id": source_id,
                "title": title,
                "description": description,
                "status": status,
                "priority_level": priority_level,
                "priority_score": score,
                "assigned_user_id": assigned_user_id,
                "created_by_user_id": int(actor_user["user_id"]),
                "updated_by_user_id": int(actor_user["user_id"]),
                "due_at": due_at,
                "sla_deadline_at": sla_deadline_at,
                "sla_warning_minutes": sla_warning_minutes,
                "sla_warning_at": sla_warning_at,
                "sla_stage": working_item["sla_stage"],
                "resolved_at": now_iso() if status in {"zamkniete", "anulowane"} else None,
                "last_sla_transition_at": now_local_datetime_value()
                if working_item["sla_stage"] in {"warning", "breached", "escalated", "resolved"}
                else None,
                "metadata_json": metadata_json,
            }
        )
        self.work_item_repository.create_history(
            {
                "work_item_id": work_item_id,
                "organization_id": int(organization_id),
                "action_type": "work_item_created",
                "actor": actor,
                "message": f"Dodano pozycje pracy: {title}.",
                "details": json_dumps(
                    {
                        "work_item_id": work_item_id,
                        "status": status,
                        "priority_level": priority_level,
                        "priority_score": score,
                        "source_type": source_type,
                        "source_id": source_id,
                        "assigned_user_id": assigned_user_id,
                        "sla_deadline_at": sla_deadline_at,
                        "sla_warning_at": sla_warning_at,
                    }
                ),
            }
        )
        self.event_repository.log(
            event_type="work_item_created",
            invoice_id=None,
            organization_id=int(organization_id),
            source="WORK_ITEM",
            status_before=None,
            status_after=status,
            decision_reason=f"Dodano pozycje pracy: {title}.",
            actor=actor,
            details={
                "work_item_id": work_item_id,
                "priority_level": priority_level,
                "priority_score": score,
                "sla_stage": working_item["sla_stage"],
            },
        )
        detail = self.get_work_item_detail(work_item_id, organization_id=organization_id)
        assert detail is not None
        return detail["work_item"]

    def update_work_item(
        self,
        work_item_id: int,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any] | None:
        current = self.work_item_repository.get_by_id(work_item_id, organization_id=organization_id)
        if not current:
            return None

        updated_data: dict[str, Any] = {}
        changed_keys: list[str] = []
        if "source_type" in payload:
            updated_data["source_type"] = self._normalize_choice(
                payload.get("source_type"),
                WORK_ITEM_SOURCE_TYPES,
                str(current.get("source_type") or "manual"),
                "Nieprawidlowe zrodlo pozycji pracy.",
            )
            changed_keys.append("source_type")
        if "source_id" in payload:
            updated_data["source_id"] = self._normalize_optional_id(payload.get("source_id"))
            changed_keys.append("source_id")
        if "title" in payload:
            title = str(payload.get("title") or "").strip()
            if not title:
                raise ValueError("Tytul pozycji pracy jest wymagany.")
            updated_data["title"] = title
            changed_keys.append("title")
        if "description" in payload:
            updated_data["description"] = self._normalize_optional_text(payload.get("description"))
            changed_keys.append("description")
        if "status" in payload:
            updated_data["status"] = self._normalize_choice(
                payload.get("status"),
                WORK_ITEM_STATUSES,
                str(current.get("status") or "nowe"),
                "Nieprawidlowy status pozycji pracy.",
            )
            changed_keys.append("status")
        if "priority_level" in payload:
            changed_keys.append("priority_level")
        if "assigned_user_id" in payload:
            updated_data["assigned_user_id"] = self._validate_assigned_user(
                self._normalize_optional_id(payload.get("assigned_user_id")),
                organization_id=int(current["organization_id"]),
            )
            changed_keys.append("assigned_user_id")
        if "due_at" in payload:
            updated_data["due_at"] = self._normalize_optional_local_datetime(
                payload.get("due_at"),
                "Termin ma nieprawidlowy format.",
            )
            changed_keys.append("due_at")
        if "sla_deadline_at" in payload:
            updated_data["sla_deadline_at"] = self._normalize_optional_local_datetime(
                payload.get("sla_deadline_at"),
                "Termin SLA ma nieprawidlowy format.",
            )
            changed_keys.append("sla_deadline_at")
        if "sla_warning_minutes" in payload:
            updated_data["sla_warning_minutes"] = self._normalize_sla_warning_minutes(payload.get("sla_warning_minutes"))
            changed_keys.append("sla_warning_minutes")
        if "metadata" in payload:
            metadata = self._normalize_metadata(payload.get("metadata"))
            updated_data["metadata_json"] = json_dumps(metadata)
            changed_keys.append("metadata")

        if not updated_data:
            return self._decorate_work_item(current)

        merged = dict(current)
        merged.update(updated_data)
        warning_input: Any
        if "sla_warning_at" in payload:
            warning_input = payload.get("sla_warning_at")
            changed_keys.append("sla_warning_at")
        elif "sla_deadline_at" in payload or "sla_warning_minutes" in payload:
            warning_input = None
        else:
            warning_input = merged.get("sla_warning_at")
        merged["sla_warning_at"] = self._build_sla_warning_at(
            sla_deadline_at=str(merged.get("sla_deadline_at") or "").strip() or None,
            sla_warning_minutes=int(merged.get("sla_warning_minutes") or 120),
            explicit_warning_at=warning_input,
        )
        merged["priority_level"] = self._normalize_choice(
            payload.get("priority_level"),
            WORK_ITEM_PRIORITY_LEVELS,
            str(merged.get("priority_level") or "normalny"),
            "Nieprawidlowy poziom priorytetu.",
        )
        merged["sla_stage"] = self._derive_sla_stage(
            status=str(merged.get("status") or "nowe"),
            warning_at=str(merged.get("sla_warning_at") or "").strip() or None,
            deadline_at=str(merged.get("sla_deadline_at") or "").strip() or None,
            current_stage=str(current.get("sla_stage") or "on_track"),
        )
        merged["priority_score"] = self._calculate_priority_score(merged)
        merged["priority_level"] = self._priority_level_from_score(
            float(merged["priority_score"]),
            minimum_level=str(merged["priority_level"]),
        )
        merged["updated_by_user_id"] = int(actor_user["user_id"])

        if str(current.get("status") or "") not in {"zamkniete", "anulowane"} and str(merged.get("status") or "") in {
            "zamkniete",
            "anulowane",
        }:
            merged["resolved_at"] = now_iso()
            merged["sla_stage"] = "resolved"
            merged["last_sla_transition_at"] = now_local_datetime_value()
        elif str(current.get("status") or "") in {"zamkniete", "anulowane"} and str(merged.get("status") or "") not in {
            "zamkniete",
            "anulowane",
        }:
            merged["resolved_at"] = None
            if merged["sla_stage"] == "resolved":
                merged["sla_stage"] = "on_track"

        self.work_item_repository.update(
            work_item_id,
            {
                "source_type": merged.get("source_type"),
                "source_id": merged.get("source_id"),
                "title": merged.get("title"),
                "description": merged.get("description"),
                "status": merged.get("status"),
                "priority_level": merged.get("priority_level"),
                "priority_score": merged.get("priority_score"),
                "assigned_user_id": merged.get("assigned_user_id"),
                "updated_by_user_id": merged.get("updated_by_user_id"),
                "due_at": merged.get("due_at"),
                "sla_deadline_at": merged.get("sla_deadline_at"),
                "sla_warning_minutes": merged.get("sla_warning_minutes"),
                "sla_warning_at": merged.get("sla_warning_at"),
                "sla_stage": merged.get("sla_stage"),
                "resolved_at": merged.get("resolved_at"),
                "last_sla_transition_at": merged.get("last_sla_transition_at"),
                "metadata_json": merged.get("metadata_json"),
            },
        )
        self.work_item_repository.create_history(
            {
                "work_item_id": work_item_id,
                "organization_id": int(current["organization_id"]),
                "action_type": "work_item_updated",
                "actor": actor,
                "message": f"Zaktualizowano pozycje pracy: {merged.get('title') or current.get('title')}.",
                "details": json_dumps({"changed_keys": changed_keys}),
            }
        )
        self.event_repository.log(
            event_type="work_item_updated",
            invoice_id=None,
            organization_id=int(current["organization_id"]),
            source="WORK_ITEM",
            status_before=str(current.get("status") or ""),
            status_after=str(merged.get("status") or ""),
            decision_reason="Aktualizacja pozycji pracy.",
            actor=actor,
            details={
                "work_item_id": int(work_item_id),
                "changed_keys": changed_keys,
                "priority_score": float(merged.get("priority_score") or 0),
                "priority_level": merged.get("priority_level"),
                "sla_stage": merged.get("sla_stage"),
            },
        )
        refreshed = self.work_item_repository.get_by_id(work_item_id, organization_id=organization_id)
        return self._decorate_work_item(refreshed) if refreshed else None

    def assign_work_item(
        self,
        work_item_id: int,
        assigned_user_id: int | None,
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any] | None:
        current = self.work_item_repository.get_by_id(work_item_id, organization_id=organization_id)
        if not current:
            return None
        normalized_assignee = self._validate_assigned_user(
            assigned_user_id,
            organization_id=int(current["organization_id"]),
        )
        merged = dict(current)
        merged["assigned_user_id"] = normalized_assignee
        merged["priority_score"] = self._calculate_priority_score(merged)
        merged["priority_level"] = self._priority_level_from_score(
            float(merged["priority_score"]),
            minimum_level=str(merged.get("priority_level") or "normalny"),
        )
        self.work_item_repository.update(
            work_item_id,
            {
                "assigned_user_id": normalized_assignee,
                "priority_level": merged["priority_level"],
                "priority_score": merged["priority_score"],
                "updated_by_user_id": int(actor_user["user_id"]),
            },
        )
        assigned_user_label = "nieprzypisano"
        if normalized_assignee:
            assigned_user = self.user_repository.get_by_id(normalized_assignee)
            assigned_user_label = str(assigned_user.get("display_name") or assigned_user.get("login")) if assigned_user else str(
                normalized_assignee
            )
        self.work_item_repository.create_history(
            {
                "work_item_id": work_item_id,
                "organization_id": int(current["organization_id"]),
                "action_type": "work_item_assigned",
                "actor": actor,
                "message": f"Zmieniono przypisanie pozycji pracy na: {assigned_user_label}.",
                "details": json_dumps({"assigned_user_id": normalized_assignee}),
            }
        )
        self.event_repository.log(
            event_type="work_item_assigned",
            invoice_id=None,
            organization_id=int(current["organization_id"]),
            source="WORK_ITEM",
            status_before=str(current.get("status") or ""),
            status_after=str(current.get("status") or ""),
            decision_reason="Zmiana przypisania pozycji pracy.",
            actor=actor,
            details={"work_item_id": work_item_id, "assigned_user_id": normalized_assignee},
        )
        refreshed = self.work_item_repository.get_by_id(work_item_id, organization_id=organization_id)
        return self._decorate_work_item(refreshed) if refreshed else None

    def snooze_work_item(
        self,
        work_item_id: int,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any] | None:
        current = self.work_item_repository.get_by_id(work_item_id, organization_id=organization_id)
        if not current:
            return None
        if str(current.get("status") or "") in {"zamkniete", "anulowane"}:
            raise ValueError("Nie mozna odroczyc zamknietej pozycji pracy.")

        mode = str(payload.get("mode") or "").strip().lower()
        explicit_due_at = self._normalize_optional_local_datetime(
            payload.get("due_at"),
            "Termin ma nieprawidlowy format.",
        )
        explicit_sla_deadline = self._normalize_optional_local_datetime(
            payload.get("sla_deadline_at"),
            "Termin SLA ma nieprawidlowy format.",
        )
        minutes_delta = self._parse_snooze_mode_minutes(mode) if mode else None
        if minutes_delta is None and explicit_due_at is None and explicit_sla_deadline is None:
            raise ValueError("Podaj tryb odroczenia (np. 30m, 2h, 1d) albo nowe terminy.")

        due_at = explicit_due_at
        sla_deadline_at = explicit_sla_deadline
        if minutes_delta is not None:
            due_at = self._shift_local_datetime(current.get("due_at"), minutes_delta)
            sla_deadline_at = self._shift_local_datetime(current.get("sla_deadline_at"), minutes_delta)

        sla_warning_minutes = int(current.get("sla_warning_minutes") or 120)
        sla_warning_at = self._build_sla_warning_at(
            sla_deadline_at=sla_deadline_at,
            sla_warning_minutes=sla_warning_minutes,
            explicit_warning_at=None,
        )
        merged = dict(current)
        merged["due_at"] = due_at
        merged["sla_deadline_at"] = sla_deadline_at
        merged["sla_warning_at"] = sla_warning_at
        merged["sla_stage"] = "on_track"
        merged["priority_score"] = self._calculate_priority_score(merged)
        merged["priority_level"] = self._priority_level_from_score(
            float(merged["priority_score"]),
            minimum_level=str(current.get("priority_level") or "normalny"),
        )

        self.work_item_repository.update(
            work_item_id,
            {
                "due_at": due_at,
                "sla_deadline_at": sla_deadline_at,
                "sla_warning_at": sla_warning_at,
                "sla_stage": "on_track",
                "priority_level": merged["priority_level"],
                "priority_score": merged["priority_score"],
                "updated_by_user_id": int(actor_user["user_id"]),
            },
        )
        self.work_item_repository.create_history(
            {
                "work_item_id": work_item_id,
                "organization_id": int(current["organization_id"]),
                "action_type": "work_item_snoozed",
                "actor": actor,
                "message": "Odroczono pozycje pracy.",
                "details": json_dumps(
                    {
                        "mode": mode,
                        "due_at": due_at,
                        "sla_deadline_at": sla_deadline_at,
                    }
                ),
            }
        )
        self.event_repository.log(
            event_type="work_item_snoozed",
            invoice_id=None,
            organization_id=int(current["organization_id"]),
            source="WORK_ITEM",
            status_before=str(current.get("status") or ""),
            status_after=str(current.get("status") or ""),
            decision_reason="Odroczono pozycje pracy.",
            actor=actor,
            details={
                "work_item_id": work_item_id,
                "mode": mode,
                "due_at": due_at,
                "sla_deadline_at": sla_deadline_at,
            },
        )
        refreshed = self.work_item_repository.get_by_id(work_item_id, organization_id=organization_id)
        return self._decorate_work_item(refreshed) if refreshed else None

    def escalate_work_item(
        self,
        work_item_id: int,
        payload: dict[str, Any] | None,
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any] | None:
        current = self.work_item_repository.get_by_id(work_item_id, organization_id=organization_id)
        if not current:
            return None
        payload = payload or {}
        assigned_user_id = payload.get("assigned_user_id", current.get("assigned_user_id"))
        normalized_assignee = self._validate_assigned_user(
            self._normalize_optional_id(assigned_user_id),
            organization_id=int(current["organization_id"]),
        )
        merged = dict(current)
        merged["assigned_user_id"] = normalized_assignee
        merged["sla_stage"] = "escalated"
        merged["last_sla_transition_at"] = now_local_datetime_value()
        merged["escalation_sent_at"] = now_local_datetime_value()
        merged["priority_score"] = max(90.0, self._calculate_priority_score(merged))
        merged["priority_level"] = self._priority_level_from_score(
            float(merged["priority_score"]),
            minimum_level="krytyczny",
        )

        self.work_item_repository.update(
            work_item_id,
            {
                "assigned_user_id": normalized_assignee,
                "sla_stage": "escalated",
                "last_sla_transition_at": merged["last_sla_transition_at"],
                "escalation_sent_at": merged["escalation_sent_at"],
                "priority_level": merged["priority_level"],
                "priority_score": merged["priority_score"],
                "updated_by_user_id": int(actor_user["user_id"]),
            },
        )
        self.work_item_repository.create_history(
            {
                "work_item_id": work_item_id,
                "organization_id": int(current["organization_id"]),
                "action_type": "work_item_escalated",
                "actor": actor,
                "message": "Pozycja pracy zostala eskalowana.",
                "details": json_dumps({"assigned_user_id": normalized_assignee}),
            }
        )
        self.event_repository.log(
            event_type="work_item_escalated",
            invoice_id=None,
            organization_id=int(current["organization_id"]),
            source="WORK_ITEM",
            status_before=str(current.get("status") or ""),
            status_after=str(current.get("status") or ""),
            decision_reason="Reczna eskalacja pozycji pracy.",
            actor=actor,
            details={
                "work_item_id": work_item_id,
                "assigned_user_id": normalized_assignee,
                "priority_level": merged["priority_level"],
                "priority_score": merged["priority_score"],
            },
        )
        refreshed = self.work_item_repository.get_by_id(work_item_id, organization_id=organization_id)
        return self._decorate_work_item(refreshed) if refreshed else None

    def close_work_item(
        self,
        work_item_id: int,
        payload: dict[str, Any] | None,
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any] | None:
        current = self.work_item_repository.get_by_id(work_item_id, organization_id=organization_id)
        if not current:
            return None
        payload = payload or {}
        close_status = self._normalize_choice(
            payload.get("status"),
            ("zamkniete", "anulowane"),
            "zamkniete",
            "Dla zamkniecia mozna uzyc tylko statusu zamkniete albo anulowane.",
        )
        reason = str(payload.get("reason") or "").strip() or "Pozycja pracy zostala zamknieta."
        resolved_at = now_iso()
        self.work_item_repository.update(
            work_item_id,
            {
                "status": close_status,
                "sla_stage": "resolved",
                "resolved_at": resolved_at,
                "last_sla_transition_at": now_local_datetime_value(),
                "priority_score": 0,
                "updated_by_user_id": int(actor_user["user_id"]),
            },
        )
        self.work_item_repository.create_history(
            {
                "work_item_id": work_item_id,
                "organization_id": int(current["organization_id"]),
                "action_type": "work_item_closed",
                "actor": actor,
                "message": reason,
                "details": json_dumps({"status": close_status}),
            }
        )
        self.event_repository.log(
            event_type="work_item_closed",
            invoice_id=None,
            organization_id=int(current["organization_id"]),
            source="WORK_ITEM",
            status_before=str(current.get("status") or ""),
            status_after=close_status,
            decision_reason=reason,
            actor=actor,
            details={"work_item_id": work_item_id},
        )
        refreshed = self.work_item_repository.get_by_id(work_item_id, organization_id=organization_id)
        return self._decorate_work_item(refreshed) if refreshed else None

    def reopen_work_item(
        self,
        work_item_id: int,
        payload: dict[str, Any] | None,
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any] | None:
        current = self.work_item_repository.get_by_id(work_item_id, organization_id=organization_id)
        if not current:
            return None
        if str(current.get("status") or "") not in {"zamkniete", "anulowane"}:
            raise ValueError("Mozna ponownie otworzyc tylko zamknieta albo anulowana pozycje pracy.")
        payload = payload or {}
        reopen_status = self._normalize_choice(
            payload.get("status"),
            ("nowe", "w_toku", "oczekuje"),
            "w_toku",
            "Dla ponownego otwarcia mozna uzyc tylko statusu nowe, w_toku albo oczekuje.",
        )
        reason = str(payload.get("reason") or "").strip() or "Pozycja pracy zostala ponownie otwarta."
        organization = self.organization_repository.get_by_id(int(current["organization_id"]))
        sla_policy = self._load_sla_policy_for_org(organization or {})
        due_at = (
            self._normalize_optional_local_datetime(
                payload.get("due_at"),
                "Termin ma nieprawidlowy format.",
            )
            if "due_at" in payload
            else (str(current.get("due_at") or "").strip() or None)
        )
        sla_deadline_at = (
            self._normalize_optional_local_datetime(
                payload.get("sla_deadline_at"),
                "Termin SLA ma nieprawidlowy format.",
            )
            if "sla_deadline_at" in payload
            else (str(current.get("sla_deadline_at") or "").strip() or None)
        )
        if sla_deadline_at is None and bool(sla_policy.get("auto_deadline_enabled")):
            sla_deadline_at = self._derive_sla_deadline_from_policy(
                priority_level=str(current.get("priority_level") or "normalny"),
                due_at=due_at,
                policy=sla_policy,
            )
        default_warning_minutes = int(current.get("sla_warning_minutes") or 0) or int(
            sla_policy.get("default_warning_minutes") or _DEFAULT_WORK_ITEM_SLA_WARNING_MINUTES
        )
        sla_warning_minutes = self._normalize_sla_warning_minutes(
            payload.get("sla_warning_minutes"),
            default_minutes=default_warning_minutes,
        )
        warning_input: Any
        if "sla_warning_at" in payload:
            warning_input = payload.get("sla_warning_at")
        elif "sla_deadline_at" in payload or "sla_warning_minutes" in payload or "due_at" in payload:
            warning_input = None
        else:
            warning_input = str(current.get("sla_warning_at") or "").strip() or None
        sla_warning_at = self._build_sla_warning_at(
            sla_deadline_at=sla_deadline_at,
            sla_warning_minutes=sla_warning_minutes,
            explicit_warning_at=warning_input,
        )
        merged = dict(current)
        merged["status"] = reopen_status
        merged["resolved_at"] = None
        merged["due_at"] = due_at
        merged["sla_deadline_at"] = sla_deadline_at
        merged["sla_warning_minutes"] = sla_warning_minutes
        merged["sla_warning_at"] = sla_warning_at
        merged["sla_stage"] = self._derive_sla_stage(
            status=reopen_status,
            warning_at=sla_warning_at,
            deadline_at=sla_deadline_at,
            current_stage="on_track",
        )
        merged["priority_score"] = self._calculate_priority_score(merged)
        merged["priority_level"] = self._priority_level_from_score(
            float(merged["priority_score"]),
            minimum_level=str(current.get("priority_level") or "normalny"),
        )
        self.work_item_repository.update(
            work_item_id,
            {
                "status": reopen_status,
                "resolved_at": None,
                "due_at": due_at,
                "sla_deadline_at": sla_deadline_at,
                "sla_warning_minutes": sla_warning_minutes,
                "sla_warning_at": sla_warning_at,
                "sla_stage": merged["sla_stage"],
                "last_sla_transition_at": now_local_datetime_value(),
                "priority_level": merged["priority_level"],
                "priority_score": merged["priority_score"],
                "updated_by_user_id": int(actor_user["user_id"]),
            },
        )
        self.work_item_repository.create_history(
            {
                "work_item_id": work_item_id,
                "organization_id": int(current["organization_id"]),
                "action_type": "work_item_reopened",
                "actor": actor,
                "message": reason,
                "details": json_dumps({"status": reopen_status}),
            }
        )
        self.event_repository.log(
            event_type="work_item_reopened",
            invoice_id=None,
            organization_id=int(current["organization_id"]),
            source="WORK_ITEM",
            status_before=str(current.get("status") or ""),
            status_after=reopen_status,
            decision_reason=reason,
            actor=actor,
            details={"work_item_id": work_item_id},
        )
        refreshed = self.work_item_repository.get_by_id(work_item_id, organization_id=organization_id)
        return self._decorate_work_item(refreshed) if refreshed else None

    def bulk_apply(
        self,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any]:
        action = str(payload.get("action") or "").strip().lower()
        allowed_actions = {"assign", "snooze", "escalate", "close", "reopen"}
        if action not in allowed_actions:
            raise ValueError("Nieprawidlowa akcja bulk. Dostepne: assign, snooze, escalate, close, reopen.")
        work_item_ids = self._normalize_id_list(payload.get("work_item_ids"))
        if not work_item_ids:
            raise ValueError("Podaj liste work_item_ids dla operacji bulk.")

        succeeded: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []
        not_found_ids: list[int] = []
        for work_item_id in work_item_ids:
            try:
                if action == "assign":
                    assigned_user_id = self._normalize_optional_id(payload.get("assigned_user_id"))
                    result = self.assign_work_item(
                        work_item_id,
                        assigned_user_id,
                        actor_user=actor_user,
                        actor=actor,
                        organization_id=organization_id,
                    )
                elif action == "snooze":
                    result = self.snooze_work_item(
                        work_item_id,
                        payload,
                        actor_user=actor_user,
                        actor=actor,
                        organization_id=organization_id,
                    )
                elif action == "escalate":
                    result = self.escalate_work_item(
                        work_item_id,
                        payload,
                        actor_user=actor_user,
                        actor=actor,
                        organization_id=organization_id,
                    )
                elif action == "close":
                    result = self.close_work_item(
                        work_item_id,
                        payload,
                        actor_user=actor_user,
                        actor=actor,
                        organization_id=organization_id,
                    )
                else:
                    result = self.reopen_work_item(
                        work_item_id,
                        payload,
                        actor_user=actor_user,
                        actor=actor,
                        organization_id=organization_id,
                    )

                if result is None:
                    not_found_ids.append(int(work_item_id))
                    continue
                succeeded.append(
                    {
                        "work_item_id": int(work_item_id),
                        "status": result.get("status"),
                        "sla_stage": result.get("sla_stage"),
                        "priority_level": result.get("priority_level"),
                        "priority_score": result.get("priority_score"),
                    }
                )
            except ValueError as error:
                failed.append({"work_item_id": int(work_item_id), "error": str(error)})

        return {
            "action": action,
            "requested": len(work_item_ids),
            "updated": len(succeeded),
            "failed": len(failed),
            "not_found": len(not_found_ids),
            "updated_items": succeeded,
            "errors": failed,
            "not_found_ids": not_found_ids,
        }

    def run_sla_sweep(
        self,
        *,
        organization_id: int | None = None,
        actor: str = "sla-worker",
        limit: int = 50,
    ) -> dict[str, int]:
        now_value = now_local_datetime_value()
        candidates = self.work_item_repository.list_due_sla_candidates(
            now_value=now_value,
            organization_id=organization_id,
            limit=limit,
        )
        result = {"evaluated": 0, "warnings": 0, "escalated": 0}
        for item in candidates:
            result["evaluated"] += 1
            item_id = int(item["work_item_id"])
            current_stage = str(item.get("sla_stage") or "on_track")
            deadline_at = str(item.get("sla_deadline_at") or "").strip()
            warning_at = str(item.get("sla_warning_at") or "").strip()
            status = str(item.get("status") or "")

            if status in {"zamkniete", "anulowane"}:
                continue

            if deadline_at and deadline_at <= now_value and current_stage in {"on_track", "warning", "breached"}:
                merged = dict(item)
                merged["sla_stage"] = "escalated"
                merged["priority_score"] = max(90.0, self._calculate_priority_score(merged))
                merged["priority_level"] = self._priority_level_from_score(
                    float(merged["priority_score"]),
                    minimum_level="krytyczny",
                )
                transition_time = now_local_datetime_value()
                self.work_item_repository.update(
                    item_id,
                    {
                        "sla_stage": "escalated",
                        "priority_level": merged["priority_level"],
                        "priority_score": merged["priority_score"],
                        "escalation_sent_at": transition_time,
                        "last_sla_transition_at": transition_time,
                    },
                )
                self.work_item_repository.create_history(
                    {
                        "work_item_id": item_id,
                        "organization_id": int(item["organization_id"]),
                        "action_type": "work_item_sla_escalated",
                        "actor": actor,
                        "message": "Automatyczna eskalacja po przekroczeniu SLA.",
                        "details": json_dumps(
                            {
                                "sla_deadline_at": deadline_at,
                                "priority_level": merged["priority_level"],
                                "priority_score": merged["priority_score"],
                            }
                        ),
                    }
                )
                self.event_repository.log(
                    event_type="work_item_sla_escalated",
                    invoice_id=None,
                    organization_id=int(item["organization_id"]),
                    source="WORK_ITEM",
                    status_before=status,
                    status_after=status,
                    decision_reason="Przekroczono SLA pozycji pracy.",
                    actor=actor,
                    details={
                        "work_item_id": item_id,
                        "sla_deadline_at": deadline_at,
                        "priority_level": merged["priority_level"],
                        "priority_score": merged["priority_score"],
                    },
                )
                result["escalated"] += 1
                continue

            if warning_at and warning_at <= now_value and current_stage == "on_track":
                transition_time = now_local_datetime_value()
                merged = dict(item)
                merged["sla_stage"] = "warning"
                merged["priority_score"] = self._calculate_priority_score(merged)
                merged["priority_level"] = self._priority_level_from_score(
                    float(merged["priority_score"]),
                    minimum_level=str(item.get("priority_level") or "normalny"),
                )
                self.work_item_repository.update(
                    item_id,
                    {
                        "sla_stage": "warning",
                        "priority_level": merged["priority_level"],
                        "priority_score": merged["priority_score"],
                        "reminder_sent_at": transition_time,
                        "last_sla_transition_at": transition_time,
                    },
                )
                self.work_item_repository.create_history(
                    {
                        "work_item_id": item_id,
                        "organization_id": int(item["organization_id"]),
                        "action_type": "work_item_sla_warning",
                        "actor": actor,
                        "message": "Automatyczne ostrzezenie SLA.",
                        "details": json_dumps({"sla_warning_at": warning_at, "sla_deadline_at": deadline_at}),
                    }
                )
                self.event_repository.log(
                    event_type="work_item_sla_warning",
                    invoice_id=None,
                    organization_id=int(item["organization_id"]),
                    source="WORK_ITEM",
                    status_before=status,
                    status_after=status,
                    decision_reason="Pozycja pracy zbliza sie do przekroczenia SLA.",
                    actor=actor,
                    details={
                        "work_item_id": item_id,
                        "sla_warning_at": warning_at,
                        "sla_deadline_at": deadline_at,
                    },
                )
                result["warnings"] += 1

        return result

    def _decorate_work_item(self, row: dict[str, Any]) -> dict[str, Any]:
        result = dict(row)
        metadata = self._normalize_metadata(result.get("metadata_json"))
        result["metadata"] = metadata
        result["priority_score"] = round(float(result.get("priority_score") or 0), 2)
        result["is_closed"] = str(result.get("status") or "") in {"zamkniete", "anulowane"}
        now_value = now_local_datetime_value()
        sla_deadline = str(result.get("sla_deadline_at") or "").strip()
        due_at = str(result.get("due_at") or "").strip()
        result["is_due_overdue"] = bool(due_at and due_at <= now_value and not result["is_closed"])
        result["is_sla_overdue"] = bool(sla_deadline and sla_deadline <= now_value and not result["is_closed"])
        result["sla_stage"] = str(result.get("sla_stage") or "on_track")
        if result["is_closed"]:
            result["sla_state_label"] = "Zamkniete"
        elif result["sla_stage"] == "escalated":
            result["sla_state_label"] = "Eskalowane"
        elif result["sla_stage"] == "breached" or result["is_sla_overdue"]:
            result["sla_state_label"] = "Po SLA"
        elif result["sla_stage"] == "warning":
            result["sla_state_label"] = "Ostrzezenie SLA"
        else:
            result["sla_state_label"] = "W normie SLA"
        return result

    def _load_sla_policy_for_org(self, organization: dict[str, Any]) -> dict[str, Any]:
        raw_policy = None
        if isinstance(organization, dict):
            raw_policy = organization.get("work_item_sla_policy_json")
        return self._normalize_sla_policy(raw_policy)

    def _normalize_sla_policy(self, value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            parsed = dict(value)
        elif isinstance(value, str):
            trimmed = value.strip()
            if not trimmed:
                parsed = {}
            else:
                try:
                    parsed_json = json.loads(trimmed)
                except json.JSONDecodeError:
                    parsed_json = {}
                parsed = dict(parsed_json) if isinstance(parsed_json, dict) else {}
        else:
            parsed = {}

        default_targets = dict(_DEFAULT_WORK_ITEM_SLA_PRIORITY_TARGETS_MINUTES)
        source_targets = parsed.get("priority_targets_minutes")
        if isinstance(source_targets, dict):
            for level in WORK_ITEM_PRIORITY_LEVELS:
                if level in source_targets:
                    default_targets[level] = self._normalize_sla_target_minutes(
                        source_targets.get(level),
                        priority_level=level,
                    )

        return {
            "auto_deadline_enabled": self._parse_policy_bool(parsed.get("auto_deadline_enabled"), default=True),
            "default_warning_minutes": self._normalize_sla_warning_minutes(
                parsed.get("default_warning_minutes"),
                default_minutes=_DEFAULT_WORK_ITEM_SLA_WARNING_MINUTES,
            ),
            "priority_targets_minutes": default_targets,
        }

    def _normalize_sla_policy_update(
        self,
        payload: dict[str, Any],
        *,
        current_policy: dict[str, Any],
    ) -> dict[str, Any]:
        candidate = self._normalize_sla_policy(current_policy)

        if "auto_deadline_enabled" in payload:
            candidate["auto_deadline_enabled"] = self._parse_policy_bool(
                payload.get("auto_deadline_enabled"),
                default=bool(candidate.get("auto_deadline_enabled")),
            )

        if "default_warning_minutes" in payload:
            candidate["default_warning_minutes"] = self._normalize_sla_warning_minutes(
                payload.get("default_warning_minutes"),
                default_minutes=int(candidate.get("default_warning_minutes") or _DEFAULT_WORK_ITEM_SLA_WARNING_MINUTES),
            )

        if "priority_targets_minutes" in payload:
            updates = payload.get("priority_targets_minutes")
            if not isinstance(updates, dict):
                raise ValueError("priority_targets_minutes musi byc obiektem z kluczami: niski, normalny, wysoki, krytyczny.")
            merged_targets = dict(candidate.get("priority_targets_minutes") or {})
            for raw_key, raw_value in updates.items():
                key = str(raw_key or "").strip()
                if key not in WORK_ITEM_PRIORITY_LEVELS:
                    raise ValueError("Dozwolone klucze priority_targets_minutes to: niski, normalny, wysoki, krytyczny.")
                merged_targets[key] = self._normalize_sla_target_minutes(raw_value, priority_level=key)
            candidate["priority_targets_minutes"] = merged_targets

        return self._normalize_sla_policy(candidate)

    def _normalize_sla_target_minutes(self, value: Any, *, priority_level: str) -> int:
        try:
            normalized = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"Docelowy czas SLA dla priorytetu {priority_level} musi byc liczba minut.")
        if normalized < 15 or normalized > 60 * 24 * 365:
            raise ValueError(f"Docelowy czas SLA dla priorytetu {priority_level} musi byc w zakresie 15-525600 minut.")
        return normalized

    def _parse_policy_bool(self, value: Any, *, default: bool) -> bool:
        if value is None:
            return bool(default)
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "tak", "yes", "on"}:
            return True
        if normalized in {"0", "false", "nie", "no", "off"}:
            return False
        return bool(default)

    def _derive_sla_deadline_from_policy(
        self,
        *,
        priority_level: str,
        due_at: str | None,
        policy: dict[str, Any],
    ) -> str:
        targets = policy.get("priority_targets_minutes") if isinstance(policy, dict) else {}
        if not isinstance(targets, dict):
            targets = {}
        normalized_priority = str(priority_level or "").strip().lower()
        fallback_minutes = int(targets.get("normalny") or _DEFAULT_WORK_ITEM_SLA_PRIORITY_TARGETS_MINUTES["normalny"])
        target_minutes = int(targets.get(normalized_priority) or fallback_minutes)
        target_minutes = max(15, min(target_minutes, 60 * 24 * 365))

        base_dt = datetime.now().replace(second=0, microsecond=0)
        derived_deadline = base_dt + timedelta(minutes=target_minutes)
        due_dt = self._parse_local_datetime(due_at)
        if due_dt is not None and due_dt < derived_deadline:
            derived_deadline = due_dt
        return derived_deadline.strftime(_LOCAL_DATETIME_FORMAT)

    def _normalize_optional_text(self, value: Any) -> str | None:
        normalized = str(value or "").strip()
        return normalized or None

    def _normalize_optional_id(self, value: Any) -> int | None:
        if value in (None, "", 0, "0"):
            return None
        try:
            normalized = int(value)
        except (TypeError, ValueError):
            raise ValueError("Nieprawidlowy identyfikator.")
        if normalized <= 0:
            return None
        return normalized

    def _normalize_choice(self, value: Any, allowed: tuple[str, ...], default: str, error_message: str) -> str:
        normalized = str(value or "").strip() or default
        if normalized not in allowed:
            raise ValueError(error_message)
        return normalized

    def _normalize_id_list(self, value: Any) -> list[int]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("Lista identyfikatorow musi byc tablica.")
        normalized: list[int] = []
        for item in value:
            try:
                item_id = int(item)
            except (TypeError, ValueError):
                continue
            if item_id <= 0:
                continue
            if item_id not in normalized:
                normalized.append(item_id)
        return normalized

    def _normalize_optional_local_datetime(self, value: Any, error_message: str) -> str | None:
        normalized = str(value or "").strip()
        if not normalized:
            return None
        try:
            datetime.strptime(normalized, _LOCAL_DATETIME_FORMAT)
        except ValueError:
            raise ValueError(error_message)
        return normalized

    def _normalize_sla_warning_minutes(
        self,
        value: Any,
        *,
        default_minutes: int = _DEFAULT_WORK_ITEM_SLA_WARNING_MINUTES,
    ) -> int:
        if value in (None, ""):
            return max(5, int(default_minutes))
        try:
            normalized = int(value)
        except (TypeError, ValueError):
            raise ValueError("Okno ostrzezenia SLA musi byc liczba minut.")
        if normalized < 5 or normalized > 60 * 24 * 14:
            raise ValueError("Okno ostrzezenia SLA musi miescic sie w zakresie 5-20160 minut.")
        return normalized

    def _build_sla_warning_at(
        self,
        *,
        sla_deadline_at: str | None,
        sla_warning_minutes: int,
        explicit_warning_at: Any,
    ) -> str | None:
        deadline = str(sla_deadline_at or "").strip()
        if not deadline:
            return None
        if explicit_warning_at not in (None, ""):
            explicit = self._normalize_optional_local_datetime(
                explicit_warning_at,
                "Termin ostrzezenia SLA ma nieprawidlowy format.",
            )
            if explicit and explicit > deadline:
                raise ValueError("Termin ostrzezenia SLA nie moze byc pozniejszy niz termin SLA.")
            return explicit

        deadline_dt = datetime.strptime(deadline, _LOCAL_DATETIME_FORMAT)
        warning_dt = deadline_dt - timedelta(minutes=max(5, int(sla_warning_minutes)))
        return warning_dt.strftime(_LOCAL_DATETIME_FORMAT)

    def _normalize_metadata(self, value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return dict(value)
        if isinstance(value, str):
            trimmed = value.strip()
            if not trimmed:
                return {}
            try:
                parsed = json.loads(trimmed)
            except Exception:
                return {}
            return parsed if isinstance(parsed, dict) else {}
        return {}

    def _validate_assigned_user(self, assigned_user_id: int | None, *, organization_id: int) -> int | None:
        if assigned_user_id is None:
            return None
        user = self.user_repository.get_by_id(int(assigned_user_id))
        if not user or not int(user.get("is_active") or 0):
            raise ValueError("Wybrany wykonawca nie istnieje albo jest nieaktywny.")
        if int(user.get("organization_id") or 0) != int(organization_id):
            raise ValueError("Wykonawca musi nalezec do tej samej organizacji.")
        return int(assigned_user_id)

    def _priority_rank(self, priority_level: str) -> int:
        ranking = {
            "niski": 0,
            "normalny": 1,
            "wysoki": 2,
            "krytyczny": 3,
        }
        return ranking.get(priority_level, 1)

    def _priority_level_from_score(self, score: float, *, minimum_level: str | None = None) -> str:
        if score >= 85:
            level = "krytyczny"
        elif score >= 60:
            level = "wysoki"
        elif score >= 35:
            level = "normalny"
        else:
            level = "niski"
        if minimum_level and self._priority_rank(minimum_level) > self._priority_rank(level):
            return minimum_level
        return level

    def _calculate_priority_score(self, item: dict[str, Any]) -> float:
        base_score = {
            "niski": 10.0,
            "normalny": 30.0,
            "wysoki": 55.0,
            "krytyczny": 80.0,
        }.get(str(item.get("priority_level") or "normalny"), 30.0)
        source_bonus = {
            "manual": 0.0,
            "invoice": 8.0,
            "task": 6.0,
            "support": 12.0,
            "knowledge": 4.0,
            "automation": 5.0,
        }.get(str(item.get("source_type") or "manual"), 0.0)
        score = base_score + source_bonus

        now_local = datetime.now().replace(second=0, microsecond=0)
        created_at = parse_datetime_flexible(item.get("created_at"))
        if created_at is not None:
            age_hours = max(0.0, (datetime.now(created_at.tzinfo) - created_at).total_seconds() / 3600)
            score += min(20.0, age_hours / 6.0)

        due_at = self._parse_local_datetime(item.get("due_at"))
        if due_at is not None:
            delta_minutes = (due_at - now_local).total_seconds() / 60
            if delta_minutes <= 0:
                score += 18.0
            elif delta_minutes <= 24 * 60:
                score += 12.0
            elif delta_minutes <= 72 * 60:
                score += 6.0

        sla_deadline = self._parse_local_datetime(item.get("sla_deadline_at"))
        if sla_deadline is not None:
            sla_delta_minutes = (sla_deadline - now_local).total_seconds() / 60
            if sla_delta_minutes <= 0:
                score += 25.0
            elif sla_delta_minutes <= 4 * 60:
                score += 18.0
            elif sla_delta_minutes <= 24 * 60:
                score += 10.0
            elif sla_delta_minutes <= 72 * 60:
                score += 5.0

        metadata = self._normalize_metadata(item.get("metadata_json"))
        if bool(metadata.get("is_blocker")):
            score += 15.0
        if bool(metadata.get("waiting_for_external")):
            score -= 3.0
        if str(item.get("status") or "") in {"zamkniete", "anulowane"}:
            return 0.0
        return round(max(0.0, min(100.0, score)), 2)

    def _derive_sla_stage(
        self,
        *,
        status: str,
        warning_at: str | None,
        deadline_at: str | None,
        current_stage: str,
    ) -> str:
        if status in {"zamkniete", "anulowane"}:
            return "resolved"

        now_value = now_local_datetime_value()
        if deadline_at and deadline_at <= now_value:
            return "breached" if current_stage != "escalated" else "escalated"
        if warning_at and warning_at <= now_value:
            return "warning" if current_stage not in {"breached", "escalated"} else current_stage
        if current_stage == "escalated":
            return "escalated"
        return "on_track"

    def _parse_local_datetime(self, value: Any) -> datetime | None:
        normalized = str(value or "").strip()
        if not normalized:
            return None
        try:
            return datetime.strptime(normalized, _LOCAL_DATETIME_FORMAT)
        except ValueError:
            return None

    def _parse_snooze_mode_minutes(self, mode: str) -> int | None:
        normalized = str(mode or "").strip().lower()
        if not normalized:
            return None
        if normalized.endswith("m") and normalized[:-1].isdigit():
            return int(normalized[:-1])
        if normalized.endswith("h") and normalized[:-1].isdigit():
            return int(normalized[:-1]) * 60
        if normalized.endswith("d") and normalized[:-1].isdigit():
            return int(normalized[:-1]) * 60 * 24
        aliases = {
            "30m": 30,
            "1h": 60,
            "2h": 120,
            "4h": 240,
            "1d": 60 * 24,
        }
        return aliases.get(normalized)

    def _shift_local_datetime(self, value: Any, minutes_delta: int) -> str | None:
        current = self._parse_local_datetime(value)
        if current is None:
            return None
        shifted = current + timedelta(minutes=max(1, int(minutes_delta)))
        return shifted.strftime(_LOCAL_DATETIME_FORMAT)
