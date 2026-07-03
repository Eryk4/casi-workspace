from __future__ import annotations

import base64
import binascii
import hashlib
import json
import mimetypes
import re
import secrets
import unicodedata
from calendar import monthrange
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.domain.constants import (
    MANAGER_ASSISTANT_MANAGER_ROLES,
    MANAGER_TASK_FOCUS_VIEWS,
    TASK_ASSIGNMENT_ROLES,
    TASK_FOCUS_VIEWS,
    TASK_FOCUS_VIEW_LABELS,
    TASK_PRIORITIES,
    TASK_NOTE_KINDS,
    TASK_RECURRENCE_EDIT_SCOPES,
    TASK_RECURRENCE_PATTERNS,
    TASK_STATUSES,
    TASK_TYPES,
    TASK_VISIBILITY_SCOPES,
    WORKER_TASK_FOCUS_VIEWS,
)
from app.repositories.event_repository import EventRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.contractor_repository import ContractorRepository
from app.repositories.task_template_repository import TaskTemplateRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.services.calendar_service import CalendarService
from app.services.storage_service import StorageService
from app.utils import json_dumps, now_iso, now_local_datetime_value

TASK_ATTACHMENT_MAX_BYTES = 8 * 1024 * 1024


class TaskService:
    def __init__(
        self,
        task_repository: TaskRepository,
        event_repository: EventRepository,
        user_repository: UserRepository,
        organization_repository: OrganizationRepository,
        invoice_repository: InvoiceRepository,
        contractor_repository: ContractorRepository,
        knowledge_repository: KnowledgeRepository | None,
        calendar_service: CalendarService,
        storage_service: StorageService,
        task_template_repository: TaskTemplateRepository | None = None,
        approval_repository: ApprovalRepository | None = None,
    ) -> None:
        self.task_repository = task_repository
        self.event_repository = event_repository
        self.user_repository = user_repository
        self.organization_repository = organization_repository
        self.invoice_repository = invoice_repository
        self.contractor_repository = contractor_repository
        self.knowledge_repository = knowledge_repository
        self.calendar_service = calendar_service
        self.storage_service = storage_service
        self.task_template_repository = task_template_repository
        self.approval_repository = approval_repository

    def list_tasks(
        self,
        filters: dict[str, Any] | None = None,
        organization_id: int | None = None,
        viewer_user: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        filters = filters or {}
        viewer_user_id = int(viewer_user["user_id"]) if viewer_user else None
        focus_view = str(filters.get("focus_view") or "").strip()
        repository_filters = dict(filters)
        repository_filters.pop("focus_view", None)
        tasks = self.task_repository.list_tasks(
            repository_filters,
            organization_id=organization_id,
            viewer_user_id=viewer_user_id,
        )
        decorated = [self._decorate_task(task, viewer_user_id=viewer_user_id) for task in tasks]
        if focus_view:
            allowed_focus_views = set(self._focus_view_codes_for_user(viewer_user))
            if focus_view not in allowed_focus_views:
                return []
            decorated = [task for task in decorated if self._matches_focus_view(task, focus_view, viewer_user_id)]
        return decorated

    def list_assignable_users(self, organization_id: int | None = None) -> list[dict[str, Any]]:
        users = self.user_repository.list_users(organization_id=organization_id)
        result = []
        for user in users:
            if not user.get("is_active"):
                continue
            if not user.get("organization_id"):
                continue
            result.append(
                {
                    "user_id": user["user_id"],
                    "login": user["login"],
                    "display_name": user.get("display_name") or user["login"],
                    "telegram_user_id": user.get("telegram_user_id"),
                    "telegram_reminders_enabled": int(
                        user.get("telegram_reminders_enabled") if user.get("telegram_reminders_enabled") is not None else 1
                    ),
                    "organization_id": user.get("organization_id"),
                    "organization_name": user.get("organization_name"),
                }
            )
        return result

    def get_planner_snapshot(
        self,
        *,
        organization_id: int | None = None,
        viewer_user: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        viewer_user_id = int(viewer_user["user_id"]) if viewer_user else None
        tasks = self.list_tasks({}, organization_id=organization_id, viewer_user=viewer_user)
        now_dt = datetime.now().replace(second=0, microsecond=0)
        today_start = now_dt.replace(hour=0, minute=0)
        tomorrow_start = today_start + timedelta(days=1)
        day_after_tomorrow = today_start + timedelta(days=2)
        week_end = today_start + timedelta(days=7)

        buckets = {
            "zalegle": self._build_planner_bucket(tasks, "zalegle", viewer_user_id, today_start, today_start),
            "dzis": self._build_planner_bucket(tasks, "dzis", viewer_user_id, today_start, tomorrow_start),
            "jutro": self._build_planner_bucket(tasks, "jutro", viewer_user_id, tomorrow_start, day_after_tomorrow),
            "tydzien": self._build_planner_bucket(tasks, "tydzien", viewer_user_id, day_after_tomorrow, week_end),
        }
        return {
            "generated_at": now_dt.strftime("%Y-%m-%dT%H:%M"),
            "counts": {key: bucket["count"] for key, bucket in buckets.items()},
            "buckets": buckets,
        }

    def get_focus_snapshot(
        self,
        *,
        organization_id: int | None = None,
        viewer_user: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        viewer_user_id = int(viewer_user["user_id"]) if viewer_user else None
        tasks = self.list_tasks({}, organization_id=organization_id, viewer_user=viewer_user)
        now_dt = datetime.now().replace(second=0, microsecond=0)
        view_codes = self._focus_view_codes_for_user(viewer_user)
        views = []
        for code in view_codes:
            items = [task for task in tasks if self._matches_focus_view(task, code, viewer_user_id)]
            items.sort(key=self._focus_sort_key)
            views.append(
                {
                    "code": code,
                    "label": TASK_FOCUS_VIEW_LABELS.get(code, code),
                    "count": len(items),
                    "items": items[:12],
                }
            )
        return {
            "generated_at": now_dt.strftime("%Y-%m-%dT%H:%M"),
            "available_views": list(view_codes),
            "views": views,
        }

    def get_task_detail(
        self,
        task_id: int,
        organization_id: int | None = None,
        viewer_user: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        viewer_user_id = int(viewer_user["user_id"]) if viewer_user else None
        task = self.task_repository.get_by_id(
            task_id,
            organization_id=organization_id,
            viewer_user_id=viewer_user_id,
        )
        if not task:
            return None

        visible_users = self.task_repository.list_visibility_users(task_id)
        linked_entities = self.task_repository.list_links(task_id)
        decorated_task = self._decorate_task(
            task,
            visible_users=visible_users,
            linked_entities=linked_entities,
            viewer_user_id=viewer_user_id,
        )
        notes = [self._decorate_note(note) for note in self.task_repository.list_notes(task_id)]
        checklist_items = self.task_repository.list_checklist_items(task_id)
        return {
            "task": decorated_task,
            "notes": notes,
            "attachments": self.task_repository.list_attachments(task_id),
            "history": self.task_repository.list_history(task_id),
            "checklist_items": checklist_items,
            "checklist_summary": self.task_repository.count_checklist_items(task_id),
            "approval_requests": self.approval_repository.list_for_entity("task", task_id, organization_id=organization_id)
            if self.approval_repository
            else [],
            "visible_users": visible_users,
        }

    def create_task(
        self,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any]:
        if organization_id is None:
            raise ValueError("Wybierz organizacje przed dodaniem zadania.")

        owner_user_id = int(actor_user["user_id"])
        task_type = self._normalize_choice(payload.get("task_type"), TASK_TYPES, "zadanie", "Nieprawidlowy typ wpisu.")
        status = self._normalize_choice(payload.get("status"), TASK_STATUSES, "nowe", "Nieprawidlowy status zadania.")
        priority = self._normalize_choice(payload.get("priority"), TASK_PRIORITIES, "normalny", "Nieprawidlowy priorytet.")
        visibility_scope = self._normalize_choice(
            payload.get("visibility_scope"),
            TASK_VISIBILITY_SCOPES,
            "prywatne",
            "Nieprawidlowy zakres widocznosci.",
        )
        title = str(payload.get("title") or "").strip()
        description = str(payload.get("description") or "").strip() or None
        due_at = self._normalize_optional_text(payload.get("due_at"))
        remind_at = self._normalize_optional_text(payload.get("remind_at"))
        recurrence_pattern = self._normalize_choice(
            payload.get("recurrence_pattern"),
            TASK_RECURRENCE_PATTERNS,
            "brak",
            "Nieprawidlowy wzorzec cyklicznosci.",
        )
        recurrence_interval = self._normalize_recurrence_interval(payload.get("recurrence_interval"))
        recurrence_weekdays = self._normalize_recurrence_weekdays(payload.get("recurrence_weekdays"))
        recurrence_end_at = self._normalize_optional_text(payload.get("recurrence_end_at"))
        assigned_user_id = self._normalize_optional_id(payload.get("assigned_user_id"))
        visible_user_ids = self._normalize_optional_id_list(payload.get("visible_user_ids"))
        linked_entities = self._validate_linked_entities(
            self._normalize_linked_entities(payload.get("linked_entities")),
            organization_id=organization_id,
        )
        calendar_id = self._normalize_optional_id(payload.get("calendar_id"))
        calendar_duration_minutes = self._normalize_optional_minutes(payload.get("calendar_duration_minutes"), default=60)

        if not title:
            raise ValueError("Tytul zadania jest wymagany.")
        if task_type == "przypomnienie" and not due_at and not remind_at:
            raise ValueError("Przypomnienie musi miec termin albo godzine przypomnienia.")
        if not remind_at and task_type == "przypomnienie" and due_at:
            remind_at = due_at
        self._validate_reminder(due_at=due_at, remind_at=remind_at)
        recurrence_payload = self._prepare_recurrence_payload(
            recurrence_pattern=recurrence_pattern,
            recurrence_interval=recurrence_interval,
            recurrence_weekdays=recurrence_weekdays,
            recurrence_end_at=recurrence_end_at,
            due_at=due_at,
            remind_at=remind_at,
            existing_series_id=None,
        )
        self._validate_task_distribution_permissions(
            actor_user=actor_user,
            visibility_scope=visibility_scope,
            visible_user_ids=visible_user_ids,
            assigned_user_id=assigned_user_id,
            owner_user_id=owner_user_id,
        )

        assigned_user = self._validate_assigned_user(assigned_user_id, organization_id)
        calendar = self.calendar_service.validate_calendar_for_user(calendar_id, actor_user)
        calendar_duration_minutes = self._normalize_optional_minutes(
            payload.get("calendar_duration_minutes"),
            default=int(calendar.get("default_duration_minutes") or 60) if calendar else 60,
        )
        visible_user_ids = self._resolve_visibility_users(
            visibility_scope=visibility_scope,
            requested_user_ids=visible_user_ids,
            owner_user_id=owner_user_id,
            assigned_user_id=assigned_user_id,
            organization_id=organization_id,
        )
        completed_at = now_iso() if status == "zakonczone" else None

        task_id = self.task_repository.create(
            {
                "organization_id": organization_id,
                "task_type": task_type,
                "visibility_scope": visibility_scope,
                "owner_user_id": owner_user_id,
                "title": title,
                "description": description,
                "status": status,
                "priority": priority,
                "due_at": due_at,
                "remind_at": remind_at,
                "recurrence_pattern": recurrence_payload["recurrence_pattern"],
                "recurrence_interval": recurrence_payload["recurrence_interval"],
                "recurrence_weekdays": recurrence_payload["recurrence_weekdays"],
                "recurrence_end_at": recurrence_payload["recurrence_end_at"],
                "recurrence_series_id": recurrence_payload["recurrence_series_id"],
                "recurrence_parent_task_id": None,
                "assigned_user_id": assigned_user_id,
                "calendar_id": int(calendar["user_calendar_id"]) if calendar else None,
                "calendar_duration_minutes": calendar_duration_minutes,
                "created_by_user_id": owner_user_id,
                "completed_at": completed_at,
            }
        )
        self.task_repository.replace_visibility_users(task_id, organization_id, visible_user_ids)
        self.task_repository.replace_links(
            task_id,
            organization_id,
            linked_entities,
            created_by_user_id=owner_user_id,
        )

        task = self.task_repository.get_by_id(
            task_id,
            organization_id=organization_id,
            viewer_user_id=owner_user_id,
        )
        assert task is not None
        visible_users = self.task_repository.list_visibility_users(task_id)
        persisted_links = self.task_repository.list_links(task_id)
        checklist_items = self._normalize_checklist_payload(payload.get("checklist_items"))
        for index, item_text in enumerate(checklist_items):
            self.task_repository.create_checklist_item(
                {
                    "task_id": task_id,
                    "organization_id": organization_id,
                    "item_text": item_text,
                    "item_order": index,
                    "created_by_user_id": owner_user_id,
                }
            )
        task = self._synchronize_google_calendar(task, organization_id=organization_id)
        visible_users = self.task_repository.list_visibility_users(task_id)

        history_message = f"Dodano nowy wpis typu {self._task_type_label(task_type)}: {title}."
        history_message += f" Widocznosc: {self._visibility_label(visibility_scope)}."
        if assigned_user:
            history_message += f" Przypisano do: {assigned_user.get('display_name') or assigned_user.get('login')}."
        if remind_at:
            history_message += f" Ustawiono przypomnienie na: {remind_at}."
        if calendar:
            history_message += f" Dodano do kalendarza: {calendar['display_name']}."
        if recurrence_payload["recurrence_pattern"] != "brak":
            history_message += f" Cyklicznosc: {self._recurrence_label(recurrence_payload['recurrence_pattern'], recurrence_payload.get('recurrence_interval') or 1)}."
        if persisted_links:
            history_message += f" Powiazania: {self._linked_entities_summary(persisted_links)}."

        self._log_task_history(
            task_id=task_id,
            organization_id=organization_id,
            action_type="task_created",
            actor=actor,
            message=history_message,
            details={
                "task_id": task_id,
                "title": title,
                "task_type": task_type,
                "status": status,
                "priority": priority,
                "visibility_scope": visibility_scope,
                "visible_user_ids": visible_user_ids,
                "remind_at": remind_at,
                "recurrence_pattern": recurrence_payload["recurrence_pattern"],
                "recurrence_interval": recurrence_payload["recurrence_interval"],
                "recurrence_end_at": recurrence_payload["recurrence_end_at"],
                "assigned_user_id": assigned_user_id,
                "linked_entities": [
                    {"entity_type": item["entity_type"], "entity_id": int(item["entity_id"])}
                    for item in persisted_links
                ],
                "calendar_id": int(calendar["user_calendar_id"]) if calendar else None,
                "calendar_duration_minutes": calendar_duration_minutes,
            },
        )
        self.event_repository.log(
            event_type="task_created",
            invoice_id=None,
            organization_id=organization_id,
            source=None,
            status_before=None,
            status_after=status,
            decision_reason=f"Dodano wpis: {title}.",
            actor=actor,
            details={
                "task_id": task_id,
                "title": title,
                "task_type": task_type,
                "visibility_scope": visibility_scope,
                "visible_user_ids": visible_user_ids,
                "linked_entities": [
                    {"entity_type": item["entity_type"], "entity_id": int(item["entity_id"])}
                    for item in persisted_links
                ],
                "remind_at": remind_at,
                "recurrence_pattern": recurrence_payload["recurrence_pattern"],
                "calendar_id": int(calendar["user_calendar_id"]) if calendar else None,
            },
        )
        return self._decorate_task(
            task,
            visible_users=visible_users,
            linked_entities=persisted_links,
            viewer_user_id=int(actor_user["user_id"]),
        )

    def update_task(
        self,
        task_id: int,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any] | None:
        viewer_user_id = int(actor_user["user_id"])
        current = self.task_repository.get_by_id(
            task_id,
            organization_id=organization_id,
            viewer_user_id=viewer_user_id,
        )
        if not current:
            return None

        current_visible_users = self.task_repository.list_visibility_users(task_id)
        current_visible_user_ids = [int(item["user_id"]) for item in current_visible_users]
        current_linked_entities = self.task_repository.list_links(task_id)
        current_linked_entity_refs = [
            {"entity_type": str(item["entity_type"]), "entity_id": int(item["entity_id"])}
            for item in current_linked_entities
        ]
        current_calendar_id = self._normalize_optional_id(current.get("calendar_id"))
        recurrence_apply_scope = self._normalize_recurrence_edit_scope(
            payload.get("recurrence_apply_scope"),
            default="tylko_ten",
        )

        updates: dict[str, Any] = {}
        changes: list[str] = []

        if "task_type" in payload:
            task_type = self._normalize_choice(payload.get("task_type"), TASK_TYPES, current["task_type"], "Nieprawidlowy typ wpisu.")
            if task_type != current["task_type"]:
                updates["task_type"] = task_type
                changes.append("typ")
        if "title" in payload:
            title = str(payload.get("title") or "").strip()
            if not title:
                raise ValueError("Tytul zadania jest wymagany.")
            if title != current["title"]:
                updates["title"] = title
                changes.append("tytul")
        if "description" in payload:
            description = str(payload.get("description") or "").strip() or None
            if description != current.get("description"):
                updates["description"] = description
                changes.append("opis")
        if "status" in payload:
            status = self._normalize_choice(payload.get("status"), TASK_STATUSES, current["status"], "Nieprawidlowy status zadania.")
            if status != current["status"]:
                updates["status"] = status
                changes.append("status")
        if "priority" in payload:
            priority = self._normalize_choice(payload.get("priority"), TASK_PRIORITIES, current["priority"], "Nieprawidlowy priorytet.")
            if priority != current["priority"]:
                updates["priority"] = priority
                changes.append("priorytet")
        if "due_at" in payload:
            due_at = self._normalize_optional_text(payload.get("due_at"))
            if due_at != current.get("due_at"):
                updates["due_at"] = due_at
                changes.append("termin")
        if "remind_at" in payload:
            remind_at = self._normalize_optional_text(payload.get("remind_at"))
            if remind_at != current.get("remind_at"):
                updates["remind_at"] = remind_at
                changes.append("przypomnienie")
        if "recurrence_pattern" in payload:
            recurrence_pattern = self._normalize_choice(
                payload.get("recurrence_pattern"),
                TASK_RECURRENCE_PATTERNS,
                current.get("recurrence_pattern") or "brak",
                "Nieprawidlowy wzorzec cyklicznosci.",
            )
            if recurrence_pattern != (current.get("recurrence_pattern") or "brak"):
                updates["recurrence_pattern"] = recurrence_pattern
                changes.append("cyklicznosc")
        if "recurrence_interval" in payload:
            recurrence_interval = self._normalize_recurrence_interval(payload.get("recurrence_interval"))
            if recurrence_interval != int(current.get("recurrence_interval") or 1):
                updates["recurrence_interval"] = recurrence_interval
                changes.append("interwal_cyklu")
        if "recurrence_weekdays" in payload:
            recurrence_weekdays = self._normalize_recurrence_weekdays(payload.get("recurrence_weekdays"))
            if recurrence_weekdays != self._normalize_recurrence_weekdays(current.get("recurrence_weekdays")):
                updates["recurrence_weekdays"] = recurrence_weekdays
                changes.append("dni_cyklu")
        if "recurrence_end_at" in payload:
            recurrence_end_at = self._normalize_optional_text(payload.get("recurrence_end_at"))
            if recurrence_end_at != current.get("recurrence_end_at"):
                updates["recurrence_end_at"] = recurrence_end_at
                changes.append("koniec_cyklu")
        if "assigned_user_id" in payload:
            assigned_user_id = self._normalize_optional_id(payload.get("assigned_user_id"))
            self._validate_assigned_user(assigned_user_id, int(current["organization_id"]))
            if assigned_user_id != current.get("assigned_user_id"):
                updates["assigned_user_id"] = assigned_user_id
                changes.append("osoba_przypisana")
        if "calendar_id" in payload:
            calendar_id = self._normalize_optional_id(payload.get("calendar_id"))
            calendar = self.calendar_service.validate_calendar_for_user(calendar_id, actor_user)
            next_calendar_id = int(calendar["user_calendar_id"]) if calendar else None
            if next_calendar_id != current_calendar_id:
                updates["calendar_id"] = next_calendar_id
                changes.append("kalendarz")
        if "calendar_duration_minutes" in payload:
            calendar_duration_minutes = self._normalize_optional_minutes(
                payload.get("calendar_duration_minutes"),
                default=(
                    int(calendar.get("default_duration_minutes") or 60)
                    if "calendar_id" in payload and calendar
                    else int(current.get("calendar_default_duration_minutes") or current.get("calendar_duration_minutes") or 60)
                ),
            )
            if int(current.get("calendar_duration_minutes") or 60) != calendar_duration_minutes:
                updates["calendar_duration_minutes"] = calendar_duration_minutes
                changes.append("czas_w_kalendarzu")
        if "visibility_scope" in payload:
            visibility_scope = self._normalize_choice(
                payload.get("visibility_scope"),
                TASK_VISIBILITY_SCOPES,
                current.get("visibility_scope") or "prywatne",
                "Nieprawidlowy zakres widocznosci.",
            )
            if visibility_scope != (current.get("visibility_scope") or "prywatne"):
                updates["visibility_scope"] = visibility_scope
                changes.append("widocznosc")

        next_task_type = updates.get("task_type", current["task_type"])
        next_due_at = updates.get("due_at", current.get("due_at"))
        next_remind_at = updates.get("remind_at", current.get("remind_at"))
        if next_task_type == "przypomnienie" and not next_due_at and not next_remind_at:
            raise ValueError("Przypomnienie musi miec termin albo godzine przypomnienia.")
        if next_task_type == "przypomnienie" and not next_remind_at and next_due_at:
            updates["remind_at"] = next_due_at
            next_remind_at = next_due_at
            if "przypomnienie" not in changes:
                changes.append("przypomnienie")
        self._validate_reminder(due_at=next_due_at, remind_at=next_remind_at)
        next_recurrence_payload = self._prepare_recurrence_payload(
            recurrence_pattern=updates.get("recurrence_pattern", current.get("recurrence_pattern") or "brak"),
            recurrence_interval=updates.get("recurrence_interval", int(current.get("recurrence_interval") or 1)),
            recurrence_weekdays=updates.get("recurrence_weekdays", current.get("recurrence_weekdays")),
            recurrence_end_at=updates.get("recurrence_end_at", current.get("recurrence_end_at")),
            due_at=next_due_at,
            remind_at=next_remind_at,
            existing_series_id=current.get("recurrence_series_id"),
        )
        updates["recurrence_pattern"] = next_recurrence_payload["recurrence_pattern"]
        updates["recurrence_interval"] = next_recurrence_payload["recurrence_interval"]
        updates["recurrence_weekdays"] = next_recurrence_payload["recurrence_weekdays"]
        updates["recurrence_end_at"] = next_recurrence_payload["recurrence_end_at"]
        updates["recurrence_series_id"] = next_recurrence_payload["recurrence_series_id"]

        next_status = updates.get("status", current["status"])
        if next_status == "zakonczone" and not current.get("completed_at"):
            updates["completed_at"] = now_iso()
        if next_status != "zakonczone" and current.get("completed_at"):
            updates["completed_at"] = None

        next_visibility_scope = updates.get("visibility_scope", current.get("visibility_scope") or "prywatne")
        next_assigned_user_id = updates.get("assigned_user_id", current.get("assigned_user_id"))
        requested_visible_user_ids = current_visible_user_ids
        if "visible_user_ids" in payload:
            requested_visible_user_ids = self._normalize_optional_id_list(payload.get("visible_user_ids"))
        next_linked_entities = current_linked_entity_refs
        if "linked_entities" in payload:
            next_linked_entities = self._validate_linked_entities(
                self._normalize_linked_entities(payload.get("linked_entities")),
                organization_id=int(current["organization_id"]),
            )
        self._validate_task_distribution_permissions(
            actor_user=actor_user,
            visibility_scope=next_visibility_scope,
            visible_user_ids=requested_visible_user_ids,
            assigned_user_id=next_assigned_user_id,
            owner_user_id=int(current["owner_user_id"]),
        )
        next_visible_user_ids = self._resolve_visibility_users(
            visibility_scope=next_visibility_scope,
            requested_user_ids=requested_visible_user_ids,
            owner_user_id=int(current["owner_user_id"]),
            assigned_user_id=next_assigned_user_id,
            organization_id=int(current["organization_id"]),
        )
        if next_visible_user_ids != current_visible_user_ids and "udostepnione_osoby" not in changes:
            changes.append("udostepnione_osoby")
        if self._linked_entities_changed(current_linked_entity_refs, next_linked_entities) and "powiazania" not in changes:
            changes.append("powiazania")

        self.task_repository.update(task_id, updates)
        if any(
            key in updates
            for key in ("task_type", "title", "status", "due_at", "remind_at", "assigned_user_id")
        ):
            self.task_repository.reset_reminder_delivery(task_id)
        self.task_repository.replace_visibility_users(task_id, int(current["organization_id"]), next_visible_user_ids)
        self.task_repository.replace_links(
            task_id,
            int(current["organization_id"]),
            next_linked_entities,
            created_by_user_id=int(actor_user["user_id"]),
        )

        refreshed = self.task_repository.get_by_id(
            task_id,
            organization_id=organization_id,
            viewer_user_id=viewer_user_id,
        )
        assert refreshed is not None
        series_update_summary = self._apply_recurrence_scope_updates(
            current_task=current,
            refreshed_task=refreshed,
            actor=actor,
            organization_id=organization_id,
            recurrence_apply_scope=recurrence_apply_scope,
            updates=updates,
            current_visible_user_ids=current_visible_user_ids,
            next_visible_user_ids=next_visible_user_ids,
        )
        refreshed = self._synchronize_google_calendar(
            refreshed,
            organization_id=organization_id,
            previous_task=current,
        )
        refreshed_visible_users = self.task_repository.list_visibility_users(task_id)
        refreshed_links = self.task_repository.list_links(task_id)

        if changes:
            self._log_task_history(
                task_id=task_id,
                organization_id=int(refreshed["organization_id"]),
                action_type="task_updated",
                actor=actor,
                message=f"Zmieniono pola: {', '.join(changes)}.",
                details={
                    "task_id": task_id,
                    "changes": changes,
                    "visibility_scope": refreshed.get("visibility_scope"),
                    "visible_user_ids": next_visible_user_ids,
                    "linked_entities": [
                        {"entity_type": item["entity_type"], "entity_id": int(item["entity_id"])}
                        for item in refreshed_links
                    ],
                    "remind_at": refreshed.get("remind_at"),
                    "recurrence_pattern": refreshed.get("recurrence_pattern"),
                    "recurrence_interval": refreshed.get("recurrence_interval"),
                    "calendar_id": refreshed.get("calendar_id"),
                    "calendar_duration_minutes": refreshed.get("calendar_duration_minutes"),
                    "recurrence_apply_scope": recurrence_apply_scope,
                    "series_update_summary": series_update_summary,
                },
            )
            self.event_repository.log(
                event_type="task_updated",
                invoice_id=None,
                organization_id=refreshed["organization_id"],
                source=None,
                status_before=current.get("status"),
                status_after=refreshed.get("status"),
                decision_reason=f"Zmieniono wpis: {refreshed['title']}.",
                actor=actor,
                details={
                    "task_id": task_id,
                    "changes": changes,
                    "visibility_scope": refreshed.get("visibility_scope"),
                    "visible_user_ids": next_visible_user_ids,
                    "linked_entities": [
                        {"entity_type": item["entity_type"], "entity_id": int(item["entity_id"])}
                        for item in refreshed_links
                    ],
                    "remind_at": refreshed.get("remind_at"),
                    "recurrence_pattern": refreshed.get("recurrence_pattern"),
                    "calendar_id": refreshed.get("calendar_id"),
                    "calendar_duration_minutes": refreshed.get("calendar_duration_minutes"),
                    "recurrence_apply_scope": recurrence_apply_scope,
                    "series_update_summary": series_update_summary,
                },
            )
        self._create_next_recurrence_occurrence(
            refreshed,
            previous_task=current,
            visible_user_ids=next_visible_user_ids,
            actor=actor,
        )
        return self._decorate_task(
            refreshed,
            visible_users=refreshed_visible_users,
            linked_entities=refreshed_links,
            viewer_user_id=int(actor_user["user_id"]),
        )

    def add_task_note(
        self,
        task_id: int,
        note_text: str,
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
        parent_note_id: int | None = None,
        note_kind: str = "comment",
    ) -> dict[str, Any] | None:
        task = self.task_repository.get_by_id(
            task_id,
            organization_id=organization_id,
            viewer_user_id=int(actor_user["user_id"]),
        )
        if not task:
            return None
        normalized_note = str(note_text or "").strip()
        if not normalized_note:
            raise ValueError("Tresc notatki jest wymagana.")
        normalized_note_kind = str(note_kind or "comment").strip().lower() or "comment"
        if normalized_note_kind not in TASK_NOTE_KINDS:
            normalized_note_kind = "comment"
        if parent_note_id is not None:
            normalized_note_kind = "reply"
        mentioned_users = self._resolve_note_mentions(normalized_note, int(task["organization_id"]))
        mention_user_ids = [int(user["user_id"]) for user in mentioned_users]
        mention_user_names = [str(user.get("display_name") or user.get("login") or user["user_id"]) for user in mentioned_users]
        if parent_note_id is not None:
            parent_note = self.task_repository.get_note_by_id(int(parent_note_id), task_id=task_id)
            if not parent_note:
                raise ValueError("Nie znaleziono komentarza nadrzednego.")

        self.task_repository.create_note(
            {
                "task_id": task_id,
                "organization_id": int(task["organization_id"]),
                "note_text": normalized_note,
                "created_by_user_id": int(actor_user["user_id"]),
                "parent_note_id": parent_note_id,
                "note_kind": normalized_note_kind,
                "mentioned_user_ids": json_dumps(mention_user_ids) if mention_user_ids else None,
                "mentioned_user_names": json_dumps(mention_user_names) if mention_user_names else None,
            }
        )
        if mention_user_names:
            self._log_task_history(
                task_id=task_id,
                organization_id=int(task["organization_id"]),
                action_type="task_comment_mentioned",
                actor=actor,
                message=f"W komentarzu wspomniano: {', '.join(mention_user_names)}.",
                details={
                    "task_id": task_id,
                    "mentioned_user_ids": mention_user_ids,
                    "mentioned_user_names": mention_user_names,
                    "parent_note_id": parent_note_id,
                },
            )
        self._log_task_history(
            task_id=task_id,
            organization_id=int(task["organization_id"]),
            action_type="task_note_added",
            actor=actor,
            message="Dodano komentarz do wpisu.",
            details={
                "task_id": task_id,
                "note_preview": normalized_note[:160],
                "note_kind": normalized_note_kind,
                "parent_note_id": parent_note_id,
                "mentioned_user_ids": mention_user_ids,
            },
        )
        self.event_repository.log(
            event_type="task_comment_added" if normalized_note_kind == "comment" else "task_note_added",
            invoice_id=None,
            organization_id=task["organization_id"],
            source=None,
            status_before=None,
            status_after=task["status"],
            decision_reason=f"Dodano komentarz do wpisu: {task['title']}.",
            actor=actor,
            details={
                "task_id": task_id,
                "mentioned_user_ids": mention_user_ids,
                "parent_note_id": parent_note_id,
            },
        )
        return self.get_task_detail(
            task_id,
            organization_id=organization_id,
            viewer_user=actor_user,
        )

    def add_task_checklist_item(
        self,
        task_id: int,
        item_text: str,
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any] | None:
        task = self.task_repository.get_by_id(
            task_id,
            organization_id=organization_id,
            viewer_user_id=int(actor_user["user_id"]),
        )
        if not task:
            return None
        normalized_item = str(item_text or "").strip()
        if not normalized_item:
            raise ValueError("Tresc elementu checklisty jest wymagana.")
        current_items = self.task_repository.list_checklist_items(task_id)
        next_order = (max((int(item.get("item_order") or 0) for item in current_items), default=-1) + 1)
        self.task_repository.create_checklist_item(
            {
                "task_id": task_id,
                "organization_id": int(task["organization_id"]),
                "item_text": normalized_item,
                "item_order": next_order,
                "created_by_user_id": int(actor_user["user_id"]),
            }
        )
        self._log_task_history(
            task_id=task_id,
            organization_id=int(task["organization_id"]),
            action_type="task_checklist_item_added",
            actor=actor,
            message=f"Dodano element checklisty: {normalized_item}.",
            details={"task_id": task_id, "item_text": normalized_item, "item_order": next_order},
        )
        return self.get_task_detail(task_id, organization_id=organization_id, viewer_user=actor_user)

    def toggle_task_checklist_item(
        self,
        task_id: int,
        item_id: int,
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any] | None:
        task = self.task_repository.get_by_id(
            task_id,
            organization_id=organization_id,
            viewer_user_id=int(actor_user["user_id"]),
        )
        if not task:
            return None
        item = self.task_repository.get_checklist_item(item_id, task_id=task_id)
        if not item:
            raise ValueError("Nie znaleziono elementu checklisty.")
        next_completed = 0 if int(item.get("is_completed") or 0) else 1
        next_fields: dict[str, Any] = {"is_completed": next_completed}
        if next_completed:
            next_fields["completed_at"] = now_iso()
            next_fields["completed_by_user_id"] = int(actor_user["user_id"])
        else:
            next_fields["completed_at"] = None
            next_fields["completed_by_user_id"] = None
        self.task_repository.update_checklist_item(item_id, next_fields)
        self._log_task_history(
            task_id=task_id,
            organization_id=int(task["organization_id"]),
            action_type="task_checklist_item_toggled",
            actor=actor,
            message=(
                f"Odznaczono element checklisty: {item['item_text']}."
                if next_completed
                else f"Oznaczono element checklisty jako do zrobienia: {item['item_text']}."
            ),
            details={"task_id": task_id, "task_checklist_item_id": item_id, "is_completed": next_completed},
        )
        return self.get_task_detail(task_id, organization_id=organization_id, viewer_user=actor_user)

    def list_task_templates(self, organization_id: int | None = None) -> list[dict[str, Any]]:
        if not self.task_template_repository:
            return []
        templates = self.task_template_repository.list_templates(organization_id=organization_id)
        return [self._decorate_template(template) for template in templates]

    def create_task_template(
        self,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any]:
        if not self.task_template_repository:
            raise ValueError("Szablony zadan nie sa jeszcze skonfigurowane.")
        if organization_id is None:
            raise ValueError("Wybierz organizacje przed dodaniem szablonu.")
        template_name = str(payload.get("template_name") or "").strip()
        if not template_name:
            raise ValueError("Nazwa szablonu jest wymagana.")
        checklist_items = self._normalize_checklist_payload(payload.get("checklist_items"))
        template_id = self.task_template_repository.create(
            {
                "organization_id": int(organization_id),
                "template_name": template_name,
                "template_description": self._normalize_optional_text(payload.get("template_description")),
                "task_type": self._normalize_choice(payload.get("task_type"), TASK_TYPES, "zadanie", "Nieprawidlowy typ wpisu."),
                "priority": self._normalize_choice(payload.get("priority"), TASK_PRIORITIES, "normalny", "Nieprawidlowy priorytet."),
                "visibility_scope": self._normalize_choice(
                    payload.get("visibility_scope"),
                    TASK_VISIBILITY_SCOPES,
                    "prywatne",
                    "Nieprawidlowy zakres widocznosci.",
                ),
                "due_offset_minutes": self._normalize_optional_int(payload.get("due_offset_minutes")),
                "reminder_offset_minutes": self._normalize_optional_int(payload.get("reminder_offset_minutes")),
                "recurrence_pattern": self._normalize_choice(
                    payload.get("recurrence_pattern"),
                    TASK_RECURRENCE_PATTERNS,
                    "brak",
                    "Nieprawidlowy wzorzec cyklicznosci.",
                ),
                "recurrence_interval": self._normalize_recurrence_interval(payload.get("recurrence_interval")),
                "recurrence_weekdays": self._normalize_recurrence_weekdays(payload.get("recurrence_weekdays")),
                "recurrence_end_offset_minutes": self._normalize_optional_int(payload.get("recurrence_end_offset_minutes")),
                "calendar_duration_minutes": self._normalize_optional_minutes(payload.get("calendar_duration_minutes"), default=60),
                "checklist_json": json_dumps(checklist_items) if checklist_items else None,
                "is_active": self._normalize_optional_bool(payload.get("is_active"), default=True),
                "created_by_user_id": int(actor_user["user_id"]),
            }
        )
        template = self.task_template_repository.get_by_id(template_id, organization_id=int(organization_id))
        assert template is not None
        self.event_repository.log(
            event_type="task_template_created",
            invoice_id=None,
            organization_id=int(organization_id),
            source=None,
            status_before=None,
            status_after="active" if int(template.get("is_active") or 0) else "inactive",
            decision_reason=f"Utworzono szablon zadania: {template_name}.",
            actor=actor,
            details={"task_template_id": template_id, "template_name": template_name},
        )
        return self._decorate_template(template)

    def update_task_template(
        self,
        template_id: int,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any] | None:
        if not self.task_template_repository:
            return None
        template = self.task_template_repository.get_by_id(template_id, organization_id=organization_id)
        if not template:
            return None
        updates: dict[str, Any] = {}
        if "template_name" in payload:
            value = str(payload.get("template_name") or "").strip()
            if not value:
                raise ValueError("Nazwa szablonu jest wymagana.")
            updates["template_name"] = value
        if "template_description" in payload:
            updates["template_description"] = self._normalize_optional_text(payload.get("template_description"))
        if "task_type" in payload:
            updates["task_type"] = self._normalize_choice(payload.get("task_type"), TASK_TYPES, template.get("task_type") or "zadanie", "Nieprawidlowy typ wpisu.")
        if "priority" in payload:
            updates["priority"] = self._normalize_choice(payload.get("priority"), TASK_PRIORITIES, template.get("priority") or "normalny", "Nieprawidlowy priorytet.")
        if "visibility_scope" in payload:
            updates["visibility_scope"] = self._normalize_choice(
                payload.get("visibility_scope"),
                TASK_VISIBILITY_SCOPES,
                template.get("visibility_scope") or "prywatne",
                "Nieprawidlowy zakres widocznosci.",
            )
        if "due_offset_minutes" in payload:
            updates["due_offset_minutes"] = self._normalize_optional_int(payload.get("due_offset_minutes"))
        if "reminder_offset_minutes" in payload:
            updates["reminder_offset_minutes"] = self._normalize_optional_int(payload.get("reminder_offset_minutes"))
        if "recurrence_pattern" in payload:
            updates["recurrence_pattern"] = self._normalize_choice(
                payload.get("recurrence_pattern"),
                TASK_RECURRENCE_PATTERNS,
                template.get("recurrence_pattern") or "brak",
                "Nieprawidlowy wzorzec cyklicznosci.",
            )
        if "recurrence_interval" in payload:
            updates["recurrence_interval"] = self._normalize_recurrence_interval(payload.get("recurrence_interval"))
        if "recurrence_weekdays" in payload:
            updates["recurrence_weekdays"] = self._normalize_recurrence_weekdays(payload.get("recurrence_weekdays"))
        if "recurrence_end_offset_minutes" in payload:
            updates["recurrence_end_offset_minutes"] = self._normalize_optional_int(payload.get("recurrence_end_offset_minutes"))
        if "calendar_duration_minutes" in payload:
            updates["calendar_duration_minutes"] = self._normalize_optional_minutes(
                payload.get("calendar_duration_minutes"),
                default=int(template.get("calendar_duration_minutes") or 60),
            )
        if "is_active" in payload:
            updates["is_active"] = self._normalize_optional_bool(payload.get("is_active"), default=bool(int(template.get("is_active") or 1)))
        if "checklist_items" in payload:
            checklist_items = self._normalize_checklist_payload(payload.get("checklist_items"))
            updates["checklist_json"] = json_dumps(checklist_items) if checklist_items else None
        self.task_template_repository.update(template_id, updates)
        refreshed = self.task_template_repository.get_by_id(template_id, organization_id=organization_id)
        if refreshed:
            self.event_repository.log(
                event_type="task_template_updated",
                invoice_id=None,
                organization_id=int(template["organization_id"]),
                source=None,
                status_before=None,
                status_after="active" if int(refreshed.get("is_active") or 0) else "inactive",
                decision_reason=f"Zaktualizowano szablon zadania: {refreshed['template_name']}.",
                actor=actor,
                details={"task_template_id": template_id, "changes": list(updates.keys())},
            )
        return self._decorate_template(refreshed) if refreshed else None

    def apply_task_template(
        self,
        template_id: int,
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
        anchor_at: str | None = None,
        overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        template = self.task_template_repository.get_by_id(template_id, organization_id=organization_id) if self.task_template_repository else None
        if not template:
            return None
        payload = {
            "title": (overrides or {}).get("title") or template["template_name"],
            "task_type": (overrides or {}).get("task_type") or template.get("task_type") or "zadanie",
            "status": (overrides or {}).get("status") or "nowe",
            "priority": (overrides or {}).get("priority") or template.get("priority") or "normalny",
            "visibility_scope": (overrides or {}).get("visibility_scope") or template.get("visibility_scope") or "prywatne",
            "description": (overrides or {}).get("description") or template.get("template_description"),
        }
        override_due_at = (overrides or {}).get("due_at")
        override_remind_at = (overrides or {}).get("remind_at")
        base_due = self._parse_local_datetime(anchor_at) if anchor_at else None
        if override_due_at:
            payload["due_at"] = override_due_at
        elif template.get("due_offset_minutes") is not None:
            due_dt = (base_due or datetime.now()).replace(second=0, microsecond=0) + timedelta(minutes=int(template["due_offset_minutes"]))
            payload["due_at"] = due_dt.strftime("%Y-%m-%dT%H:%M")
        if override_remind_at:
            payload["remind_at"] = override_remind_at
        elif template.get("reminder_offset_minutes") is not None:
            base_due_at = payload.get("due_at")
            due_reference = self._parse_local_datetime(base_due_at) if base_due_at else (base_due or datetime.now()).replace(second=0, microsecond=0)
            remind_dt = due_reference - timedelta(minutes=int(template["reminder_offset_minutes"]))
            payload["remind_at"] = remind_dt.strftime("%Y-%m-%dT%H:%M")
        payload["recurrence_pattern"] = template.get("recurrence_pattern") or "brak"
        payload["recurrence_interval"] = template.get("recurrence_interval") or 1
        payload["recurrence_weekdays"] = template.get("recurrence_weekdays")
        payload["recurrence_end_at"] = (overrides or {}).get("recurrence_end_at") or None
        if template.get("calendar_duration_minutes"):
            payload["calendar_duration_minutes"] = int(template["calendar_duration_minutes"])
        checklist_items = self._normalize_checklist_payload(template.get("checklist_json"))
        if checklist_items:
            payload["checklist_items"] = checklist_items
        created = self.create_task(
            payload,
            actor_user=actor_user,
            actor=actor,
            organization_id=organization_id,
        )
        self._log_task_history(
            task_id=int(created["task_id"]),
            organization_id=int(created["organization_id"]),
            action_type="task_template_applied",
            actor=actor,
            message=f"Utworzono wpis z szablonu: {template['template_name']}.",
            details={"task_template_id": template_id, "task_id": int(created["task_id"])},
        )
        return self.get_task_detail(int(created["task_id"]), organization_id=organization_id, viewer_user=actor_user)

    def add_task_attachment(
        self,
        task_id: int,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any] | None:
        task = self.task_repository.get_by_id(
            task_id,
            organization_id=organization_id,
            viewer_user_id=int(actor_user["user_id"]),
        )
        if not task:
            return None

        attachment_kind = str(payload.get("attachment_kind") or "file").strip().lower()
        file_name = str(payload.get("file_name") or "").strip()
        content_base64 = str(payload.get("content_base64") or "").strip()
        attachment_url = str(payload.get("attachment_url") or "").strip()
        mime_type = self._normalize_optional_text(payload.get("content_type"))

        if attachment_kind == "link" or attachment_url:
            if not attachment_url:
                raise ValueError("Wybierz link do dodania.")
            parsed_url = urlparse(attachment_url)
            if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
                raise ValueError("Link musi zaczynac sie od http:// albo https://.")
            safe_name = self._sanitize_attachment_name(file_name or self._attachment_name_from_url(attachment_url))
            file_size = len(attachment_url.encode("utf-8"))
            stored = {
                "storage_backend": "external_link",
                "storage_key": f"link/{task_id}/{hashlib.sha256(attachment_url.encode('utf-8')).hexdigest()[:24]}",
                "public_link": attachment_url,
            }
            if not mime_type:
                mime_type = "text/uri-list"
        else:
            if not file_name or not content_base64:
                raise ValueError("Wybierz plik do dodania albo podaj link.")
            safe_name = self._sanitize_attachment_name(file_name)
            try:
                content = base64.b64decode(content_base64, validate=True)
            except (ValueError, binascii.Error):
                raise ValueError("Nie udalo sie odczytac tresci pliku.") from None

            if not content:
                raise ValueError("Plik jest pusty.")
            if len(content) > TASK_ATTACHMENT_MAX_BYTES:
                max_mb = TASK_ATTACHMENT_MAX_BYTES // (1024 * 1024)
                raise ValueError(f"Plik jest zbyt duzy. Maksymalny rozmiar to {max_mb} MB.")

            organization = self.organization_repository.get_by_id(int(task["organization_id"]))
            organization_slug = str(organization.get("slug") if organization else task.get("organization_slug") or "").strip()
            if not organization_slug:
                raise ValueError("Nie mozna ustalic organizacji dla zalacznika.")

            relative_path = (
                Path("organizacje")
                / organization_slug
                / "taski"
                / str(task_id)
                / f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{safe_name}"
            )
            stored = self.storage_service.save_binary("document", relative_path, content)
            file_size = len(content)
            if not mime_type:
                mime_type = mimetypes.guess_type(safe_name)[0] or "application/octet-stream"

        storage_key = stored["storage_key"] if isinstance(stored, dict) else stored.storage_key
        public_link = stored["public_link"] if isinstance(stored, dict) else stored.public_link
        storage_backend = stored["storage_backend"] if isinstance(stored, dict) else stored.storage_backend

        self.task_repository.create_attachment(
            {
                "task_id": task_id,
                "organization_id": int(task["organization_id"]),
                "file_name": safe_name,
                "mime_type": mime_type,
                "file_size": file_size,
                "file_link": public_link,
                "file_storage_key": storage_key,
                "storage_backend": storage_backend,
                "uploaded_by_user_id": int(actor_user["user_id"]),
            }
        )
        self._log_task_history(
            task_id=task_id,
            organization_id=int(task["organization_id"]),
            action_type="task_attachment_added",
            actor=actor,
            message=f"Dodano zalacznik: {safe_name}.",
            details={
                "task_id": task_id,
                "file_name": safe_name,
                "file_size": file_size,
                "storage_key": storage_key,
            },
        )
        self.event_repository.log(
            event_type="task_attachment_added",
            invoice_id=None,
            organization_id=task["organization_id"],
            source=None,
            status_before=None,
            status_after=task["status"],
            decision_reason=f"Dodano zalacznik do wpisu: {task['title']}.",
            actor=actor,
            details={"task_id": task_id, "file_name": safe_name},
        )
        return self.get_task_detail(
            task_id,
            organization_id=organization_id,
            viewer_user=actor_user,
        )

    def snooze_task_reminder(
        self,
        task_id: int,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any] | None:
        task = self.task_repository.get_by_id(
            task_id,
            organization_id=organization_id,
            viewer_user_id=int(actor_user["user_id"]),
        )
        if not task:
            return None
        if not str(task.get("remind_at") or "").strip():
            raise ValueError("Ten wpis nie ma ustawionego przypomnienia.")
        if str(task.get("status") or "") in {"zakonczone", "anulowane"}:
            raise ValueError("Nie mozna odkladac przypomnienia dla zamknietego wpisu.")

        mode = str(payload.get("mode") or "").strip().lower()
        new_remind_at = self._calculate_snooze_target(task, mode)
        due_dt = self._parse_local_datetime(task.get("due_at"))
        new_remind_dt = self._parse_local_datetime(new_remind_at)
        if due_dt and new_remind_dt and new_remind_dt > due_dt:
            raise ValueError("Nowa godzina przypomnienia wykracza poza termin wpisu. Zmien termin albo wybierz wczesniejszy wariant.")

        self.task_repository.update(task_id, {"remind_at": new_remind_at})
        self.task_repository.reset_reminder_delivery(task_id)
        self._log_task_history(
            task_id=task_id,
            organization_id=int(task["organization_id"]),
            action_type="task_reminder_snoozed",
            actor=actor,
            message=f"Odlozono przypomnienie na {new_remind_at}.",
            details={"task_id": task_id, "mode": mode, "remind_at": new_remind_at},
        )
        self.event_repository.log(
            event_type="task_reminder_snoozed",
            invoice_id=None,
            organization_id=task["organization_id"],
            source=None,
            status_before=task.get("status"),
            status_after=task.get("status"),
            decision_reason=f"Odlozono przypomnienie dla wpisu: {task['title']}.",
            actor=actor,
            details={"task_id": task_id, "mode": mode, "remind_at": new_remind_at},
        )
        return self.get_task_detail(
            task_id,
            organization_id=organization_id,
            viewer_user=actor_user,
        )

    def sync_task_calendar(
        self,
        task_id: int,
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any] | None:
        viewer_user_id = int(actor_user["user_id"])
        task = self.task_repository.get_by_id(
            task_id,
            organization_id=organization_id,
            viewer_user_id=viewer_user_id,
        )
        if not task:
            return None
        if not task.get("calendar_id"):
            raise ValueError("Ten wpis nie ma przypisanego kalendarza.")
        if str(task.get("calendar_provider") or "google_ics") != "google_api":
            raise ValueError("Reczna synchronizacja jest dostepna tylko dla bezposredniego polaczenia z Google Calendar.")

        synchronized = self._synchronize_google_calendar(task, organization_id=organization_id, previous_task=task)
        self._log_task_history(
            task_id=task_id,
            organization_id=int(task["organization_id"]),
            action_type="task_calendar_resynced",
            actor=actor,
            message="Uruchomiono reczna synchronizacje z Google Calendar.",
            details={
                "task_id": task_id,
                "calendar_id": task.get("calendar_id"),
                "external_calendar_event_id": synchronized.get("external_calendar_event_id"),
                "external_calendar_sync_error": synchronized.get("external_calendar_sync_error"),
            },
        )
        self.event_repository.log(
            event_type="task_calendar_resynced",
            invoice_id=None,
            organization_id=task["organization_id"],
            source="GOOGLE_CALENDAR",
            status_before=task.get("status"),
            status_after=synchronized.get("status"),
            decision_reason=f"Uruchomiono reczna synchronizacje wpisu: {task['title']}.",
            actor=actor,
            details={
                "task_id": task_id,
                "calendar_id": task.get("calendar_id"),
                "external_calendar_event_id": synchronized.get("external_calendar_event_id"),
                "external_calendar_sync_error": synchronized.get("external_calendar_sync_error"),
            },
        )
        return self.get_task_detail(
            task_id,
            organization_id=organization_id,
            viewer_user=actor_user,
        )

    def check_task_calendar_sync(
        self,
        task_id: int,
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any] | None:
        viewer_user_id = int(actor_user["user_id"])
        task = self.task_repository.get_by_id(
            task_id,
            organization_id=organization_id,
            viewer_user_id=viewer_user_id,
        )
        if not task:
            return None
        if not task.get("calendar_id"):
            raise ValueError("Ten wpis nie ma przypisanego kalendarza.")
        if str(task.get("calendar_provider") or "google_ics") != "google_api":
            raise ValueError("Sprawdzenie stanu jest dostepne tylko dla bezposredniego polaczenia z Google Calendar.")

        try:
            inspection_payload = self.calendar_service.inspect_task_google_sync(task)
        except ValueError as error:
            inspection_payload = {
                "external_calendar_sync_state": "blad_sprawdzenia",
                "external_calendar_sync_message": "Nie udalo sie sprawdzic stanu wpisu w Google Calendar.",
                "external_calendar_last_checked_at": now_iso(),
                "external_calendar_last_check_error": str(error),
                "external_calendar_last_sync_source": task.get("external_calendar_last_sync_source"),
            }

        self.task_repository.update(task_id, inspection_payload)
        refreshed = self.task_repository.get_by_id(
            task_id,
            organization_id=organization_id,
            viewer_user_id=viewer_user_id,
        )
        assert refreshed is not None
        self._log_task_history(
            task_id=task_id,
            organization_id=int(task["organization_id"]),
            action_type="task_calendar_checked",
            actor=actor,
            message="Sprawdzono stan wpisu w Google Calendar.",
            details={
                "task_id": task_id,
                "calendar_id": task.get("calendar_id"),
                "external_calendar_sync_state": refreshed.get("external_calendar_sync_state"),
                "external_calendar_sync_message": refreshed.get("external_calendar_sync_message"),
            },
        )
        self.event_repository.log(
            event_type="task_calendar_checked",
            invoice_id=None,
            organization_id=task["organization_id"],
            source="GOOGLE_CALENDAR",
            status_before=task.get("status"),
            status_after=refreshed.get("status"),
            decision_reason=f"Sprawdzono stan wpisu: {task['title']}.",
            actor=actor,
            details={
                "task_id": task_id,
                "calendar_id": task.get("calendar_id"),
                "external_calendar_sync_state": refreshed.get("external_calendar_sync_state"),
            },
        )
        return self.get_task_detail(
            task_id,
            organization_id=organization_id,
            viewer_user=actor_user,
        )

    def _build_planner_bucket(
        self,
        tasks: list[dict[str, Any]],
        bucket_key: str,
        viewer_user_id: int | None,
        range_start: datetime,
        range_end: datetime,
    ) -> dict[str, Any]:
        grouped: dict[str, list[dict[str, Any]]] = {
            "moje_prywatne": [],
            "przypisane_do_mnie": [],
            "organizacyjne": [],
            "inne": [],
        }
        for task in tasks:
            if str(task.get("status") or "") in {"zakonczone", "anulowane"}:
                continue
            if not self._task_matches_planner_bucket(task, bucket_key, range_start, range_end):
                continue
            cloned = dict(task)
            cloned["planner_anchor_at"] = self._task_planner_anchor(task, bucket_key, range_start, range_end)
            group_key = self._classify_planner_task(task, viewer_user_id)
            grouped[group_key].append(cloned)

        for items in grouped.values():
            items.sort(key=self._planner_sort_key)

        groups = [
            {"key": "moje_prywatne", "label": "Moje prywatne", "items": grouped["moje_prywatne"]},
            {"key": "przypisane_do_mnie", "label": "Przypisane do mnie", "items": grouped["przypisane_do_mnie"]},
            {"key": "organizacyjne", "label": "Organizacyjne", "items": grouped["organizacyjne"]},
            {"key": "inne", "label": "Inne wspoldzielone", "items": grouped["inne"]},
        ]
        return {
            "key": bucket_key,
            "label": {
                "zalegle": "Zalegle",
                "dzis": "Dzis",
                "jutro": "Jutro",
                "tydzien": "Ten tydzien",
            }.get(bucket_key, bucket_key),
            "count": sum(len(group["items"]) for group in groups),
            "groups": groups,
        }

    def _task_matches_planner_bucket(
        self,
        task: dict[str, Any],
        bucket_key: str,
        range_start: datetime,
        range_end: datetime,
    ) -> bool:
        due_dt = self._parse_local_datetime(task.get("due_at"))
        remind_dt = self._parse_local_datetime(task.get("remind_at"))
        candidates = [value for value in (remind_dt, due_dt) if value is not None]
        if not candidates:
            return False
        if bucket_key == "zalegle":
            return any(value < range_end for value in candidates)
        return any(range_start <= value < range_end for value in candidates)

    def _task_planner_anchor(
        self,
        task: dict[str, Any],
        bucket_key: str,
        range_start: datetime,
        range_end: datetime,
    ) -> str | None:
        due_dt = self._parse_local_datetime(task.get("due_at"))
        remind_dt = self._parse_local_datetime(task.get("remind_at"))
        candidates = []
        for label, value in (("przypomnienie", remind_dt), ("termin", due_dt)):
            if value is None:
                continue
            if bucket_key == "zalegle":
                if value < range_end:
                    candidates.append((label, value))
            elif range_start <= value < range_end:
                candidates.append((label, value))
        if not candidates:
            return None
        candidates.sort(key=lambda item: item[1])
        return candidates[0][1].strftime("%Y-%m-%dT%H:%M")

    def _classify_planner_task(self, task: dict[str, Any], viewer_user_id: int | None) -> str:
        if viewer_user_id is None:
            return "inne"
        owner_user_id = int(task.get("owner_user_id") or 0)
        assigned_user_id = int(task.get("assigned_user_id") or 0) if task.get("assigned_user_id") else None
        visibility_scope = str(task.get("visibility_scope") or "prywatne")
        if owner_user_id == viewer_user_id and visibility_scope == "prywatne":
            return "moje_prywatne"
        if assigned_user_id == viewer_user_id and owner_user_id != viewer_user_id:
            return "przypisane_do_mnie"
        if visibility_scope == "organizacja":
            return "organizacyjne"
        return "inne"

    def _planner_sort_key(self, task: dict[str, Any]) -> tuple[str, int, int]:
        anchor = str(task.get("planner_anchor_at") or task.get("due_at") or task.get("remind_at") or "9999-12-31T23:59")
        priority_order = {"krytyczny": 0, "wysoki": 1, "normalny": 2, "niski": 3}
        priority_rank = priority_order.get(str(task.get("priority") or "normalny"), 4)
        return (anchor, priority_rank, -int(task.get("task_id") or 0))

    def _calculate_snooze_target(self, task: dict[str, Any], mode: str) -> str:
        current_remind_dt = self._parse_local_datetime(task.get("remind_at"))
        now_dt = datetime.now().replace(second=0, microsecond=0)
        base_dt = max(now_dt, current_remind_dt or now_dt)
        if mode == "10m":
            target = base_dt + timedelta(minutes=10)
        elif mode == "1h":
            target = base_dt + timedelta(hours=1)
        elif mode == "jutro_rano":
            tomorrow = now_dt + timedelta(days=1)
            target = tomorrow.replace(hour=9, minute=0)
        else:
            raise ValueError("Nieprawidlowy wariant odlozenia przypomnienia.")
        return target.strftime("%Y-%m-%dT%H:%M")

    def _normalize_recurrence_interval(self, value: Any) -> int:
        normalized = str(value or "").strip()
        if not normalized:
            return 1
        if not normalized.isdigit():
            raise ValueError("Interwal cyklicznosci musi byc liczba dodatnia.")
        return min(max(1, int(normalized)), 365)

    def _normalize_recurrence_weekdays(self, value: Any) -> str | None:
        if value in (None, "", []):
            return None
        raw_values = value if isinstance(value, (list, tuple, set)) else str(value).split(",")
        weekdays: list[int] = []
        for item in raw_values:
            normalized = str(item or "").strip()
            if not normalized:
                continue
            if not normalized.isdigit():
                raise ValueError("Dni cyklicznosci musza byc zapisane jako numery od 0 do 6.")
            weekday = int(normalized)
            if weekday < 0 or weekday > 6:
                raise ValueError("Dni cyklicznosci musza miescic sie w zakresie 0-6.")
            weekdays.append(weekday)
        if not weekdays:
            return None
        return ",".join(str(item) for item in sorted(set(weekdays)))

    def _prepare_recurrence_payload(
        self,
        *,
        recurrence_pattern: str,
        recurrence_interval: int,
        recurrence_weekdays: str | None,
        recurrence_end_at: str | None,
        due_at: str | None,
        remind_at: str | None,
        existing_series_id: str | None,
    ) -> dict[str, Any]:
        if recurrence_pattern == "brak":
            return {
                "recurrence_pattern": "brak",
                "recurrence_interval": 1,
                "recurrence_weekdays": None,
                "recurrence_end_at": None,
                "recurrence_series_id": None,
            }
        if not due_at and not remind_at:
            raise ValueError("Wpis cykliczny musi miec termin albo przypomnienie.")
        weekdays = recurrence_weekdays
        if recurrence_pattern == "dni_robocze":
            weekdays = "0,1,2,3,4"
        elif recurrence_pattern == "co_tydzien" and not weekdays:
            anchor_dt = self._parse_local_datetime(due_at) or self._parse_local_datetime(remind_at)
            if anchor_dt is not None:
                weekdays = str(anchor_dt.weekday())
        elif recurrence_pattern != "co_tydzien":
            weekdays = None
        end_dt = self._parse_local_datetime(recurrence_end_at)
        anchor_dt = self._parse_local_datetime(due_at) or self._parse_local_datetime(remind_at)
        if end_dt and anchor_dt and end_dt < anchor_dt:
            raise ValueError("Koniec cyklu nie moze byc wczesniejszy niz pierwszy termin wpisu.")
        return {
            "recurrence_pattern": recurrence_pattern,
            "recurrence_interval": recurrence_interval,
            "recurrence_weekdays": weekdays,
            "recurrence_end_at": recurrence_end_at,
            "recurrence_series_id": existing_series_id or self._generate_recurrence_series_id(),
        }

    def _generate_recurrence_series_id(self) -> str:
        return f"series-{secrets.token_hex(6)}"

    def _recurrence_label(self, pattern: str, interval: int) -> str:
        if pattern == "codziennie":
            return "Codziennie" if interval == 1 else f"Co {interval} dni"
        if pattern == "co_tydzien":
            return "Co tydzien" if interval == 1 else f"Co {interval} tygodnie"
        if pattern == "dni_robocze":
            return "W dni robocze"
        if pattern == "co_miesiac":
            return "Co miesiac" if interval == 1 else f"Co {interval} miesiace"
        return "Brak"

    def _recurrence_weekdays_label(self, value: str | None) -> str | None:
        if not value:
            return None
        names = {
            0: "pon.",
            1: "wt.",
            2: "sr.",
            3: "czw.",
            4: "pt.",
            5: "sob.",
            6: "niedz.",
        }
        result = []
        for item in str(value).split(","):
            if item.strip().isdigit():
                result.append(names.get(int(item.strip()), item.strip()))
        return ", ".join(result) or None

    def _normalize_recurrence_edit_scope(self, value: Any, *, default: str = "tylko_ten") -> str:
        normalized = str(value or "").strip().lower() or default
        if normalized not in TASK_RECURRENCE_EDIT_SCOPES:
            raise ValueError("Nieprawidlowy zakres edycji serii cyklicznej.")
        return normalized

    def _task_anchor_value(self, task: dict[str, Any]) -> str:
        return str(task.get("due_at") or task.get("remind_at") or "").strip()

    def _build_series_schedule_updates(
        self,
        *,
        source_task: dict[str, Any],
        target_task: dict[str, Any],
        include_due: bool,
        include_remind: bool,
    ) -> dict[str, Any]:
        updates: dict[str, Any] = {}
        source_due = self._parse_local_datetime(source_task.get("due_at"))
        source_remind = self._parse_local_datetime(source_task.get("remind_at"))
        target_due = self._parse_local_datetime(target_task.get("due_at"))
        target_remind = self._parse_local_datetime(target_task.get("remind_at"))

        new_due: datetime | None = target_due
        if include_due:
            if source_due is None:
                new_due = None
            elif target_due is not None:
                new_due = target_due.replace(hour=source_due.hour, minute=source_due.minute)
            elif target_remind is not None:
                new_due = target_remind.replace(hour=source_due.hour, minute=source_due.minute)
            else:
                new_due = source_due

            next_due_value = new_due.strftime("%Y-%m-%dT%H:%M") if new_due else None
            if next_due_value != target_task.get("due_at"):
                updates["due_at"] = next_due_value

        if include_remind:
            new_remind: datetime | None
            if source_remind is None:
                new_remind = None
            elif source_due is not None and source_remind is not None and new_due is not None:
                reminder_delta = source_due - source_remind
                new_remind = new_due - reminder_delta
            elif target_remind is not None:
                new_remind = target_remind.replace(hour=source_remind.hour, minute=source_remind.minute)
            elif new_due is not None:
                new_remind = new_due.replace(hour=source_remind.hour, minute=source_remind.minute)
            else:
                new_remind = source_remind

            next_remind_value = new_remind.strftime("%Y-%m-%dT%H:%M") if new_remind else None
            if next_remind_value != target_task.get("remind_at"):
                updates["remind_at"] = next_remind_value

        return updates

    def _apply_recurrence_scope_updates(
        self,
        *,
        current_task: dict[str, Any],
        refreshed_task: dict[str, Any],
        actor: str,
        organization_id: int | None,
        recurrence_apply_scope: str,
        updates: dict[str, Any],
        current_visible_user_ids: list[int],
        next_visible_user_ids: list[int],
    ) -> dict[str, Any] | None:
        series_id = str(refreshed_task.get("recurrence_series_id") or current_task.get("recurrence_series_id") or "").strip()
        if recurrence_apply_scope == "tylko_ten" or not series_id:
            return None

        series_field_names = {
            "task_type",
            "title",
            "description",
            "priority",
            "assigned_user_id",
            "calendar_id",
            "calendar_duration_minutes",
            "visibility_scope",
            "recurrence_pattern",
            "recurrence_interval",
            "recurrence_weekdays",
            "recurrence_end_at",
        }
        propagated_fields = {
            key: refreshed_task.get(key)
            for key in series_field_names
            if key in updates
        }
        schedule_changes = {
            "include_due": "due_at" in updates,
            "include_remind": "remind_at" in updates,
        }
        propagate_visibility = (
            "visibility_scope" in updates or current_visible_user_ids != next_visible_user_ids
        )
        if not propagated_fields and not any(schedule_changes.values()) and not propagate_visibility:
            return None

        from_anchor = self._task_anchor_value(refreshed_task) if recurrence_apply_scope == "ten_i_nastepne" else None
        target_ids = self.task_repository.list_series_task_ids(
            series_id,
            organization_id=organization_id or int(refreshed_task["organization_id"]),
            exclude_task_id=int(refreshed_task["task_id"]),
            from_anchor=from_anchor,
            include_closed=False,
        )
        if not target_ids:
            return {
                "scope": recurrence_apply_scope,
                "updated_count": 0,
                "updated_task_ids": [],
                "historical_tasks_untouched": True,
            }

        should_reset_reminders = any(
            key in updates for key in ("task_type", "assigned_user_id", "due_at", "remind_at")
        )
        should_resync_calendar = any(
            key in updates
            for key in ("task_type", "title", "description", "calendar_id", "calendar_duration_minutes", "due_at", "remind_at")
        )
        updated_ids: list[int] = []

        for target_task_id in target_ids:
            target_before = self.task_repository.get_by_id(target_task_id, organization_id=int(refreshed_task["organization_id"]))
            if not target_before:
                continue

            target_updates = dict(propagated_fields)
            target_updates.update(
                self._build_series_schedule_updates(
                    source_task=refreshed_task,
                    target_task=target_before,
                    include_due=schedule_changes["include_due"],
                    include_remind=schedule_changes["include_remind"],
                )
            )
            if target_updates:
                self.task_repository.update(target_task_id, target_updates)
            if should_reset_reminders and (target_updates or propagate_visibility):
                self.task_repository.reset_reminder_delivery(target_task_id)
            if propagate_visibility:
                self.task_repository.replace_visibility_users(
                    target_task_id,
                    int(refreshed_task["organization_id"]),
                    next_visible_user_ids,
                )

            target_after = self.task_repository.get_by_id(
                target_task_id,
                organization_id=int(refreshed_task["organization_id"]),
                viewer_user_id=int(target_before["owner_user_id"]),
            )
            if target_after and should_resync_calendar:
                self._synchronize_google_calendar(
                    target_after,
                    organization_id=int(refreshed_task["organization_id"]),
                    previous_task=target_before,
                )

            self._log_task_history(
                task_id=target_task_id,
                organization_id=int(refreshed_task["organization_id"]),
                action_type="task_series_updated",
                actor=actor,
                message=(
                    "Zaktualizowano wpis w ramach serii cyklicznej."
                    if recurrence_apply_scope == "cala_seria"
                    else "Zaktualizowano ten i kolejne wpisy serii cyklicznej."
                ),
                details={
                    "task_id": target_task_id,
                    "series_scope": recurrence_apply_scope,
                    "source_task_id": int(refreshed_task["task_id"]),
                    "changes": sorted(target_updates.keys()),
                    "visible_user_ids": next_visible_user_ids if propagate_visibility else None,
                },
            )
            updated_ids.append(target_task_id)

        return {
            "scope": recurrence_apply_scope,
            "updated_count": len(updated_ids),
            "updated_task_ids": updated_ids[:25],
            "historical_tasks_untouched": True,
        }

    def _build_reminder_target_summary(self, task: dict[str, Any]) -> dict[str, Any]:
        def candidate(prefix: str) -> dict[str, Any] | None:
            user_id = task.get(f"{prefix}_user_id")
            if not user_id:
                return None
            reminders_enabled = task.get(f"{prefix}_telegram_reminders_enabled")
            if reminders_enabled is not None and not bool(int(reminders_enabled)):
                return {
                    "user_id": int(user_id),
                    "name": task.get(f"{prefix}_user_name") or f"Uzytkownik {user_id}",
                    "telegram_user_id": None,
                    "enabled": False,
                }
            telegram_user_id = str(task.get(f"{prefix}_telegram_user_id") or "").strip() or None
            return {
                "user_id": int(user_id),
                "name": task.get(f"{prefix}_user_name") or f"Uzytkownik {user_id}",
                "telegram_user_id": telegram_user_id,
                "enabled": True,
            }

        assigned = candidate("assigned")
        owner = candidate("owner")
        if assigned and assigned["enabled"] and assigned["telegram_user_id"]:
            return {
                "reminder_target_user_id": assigned["user_id"],
                "reminder_target_name": assigned["name"],
                "reminder_target_ready": True,
                "reminder_target_reason": "assigned_user",
                "reminder_target_label": f"Przypisana osoba: {assigned['name']}",
            }
        if owner and owner["enabled"] and owner["telegram_user_id"]:
            return {
                "reminder_target_user_id": owner["user_id"],
                "reminder_target_name": owner["name"],
                "reminder_target_ready": True,
                "reminder_target_reason": "owner_fallback" if assigned else "owner_user",
                "reminder_target_label": (
                    f"Wlasciciel wpisu: {owner['name']} (fallback)"
                    if assigned
                    else f"Wlasciciel wpisu: {owner['name']}"
                ),
            }
        if assigned and assigned["enabled"] and not assigned["telegram_user_id"]:
            return {
                "reminder_target_user_id": assigned["user_id"],
                "reminder_target_name": assigned["name"],
                "reminder_target_ready": False,
                "reminder_target_reason": "assigned_missing_telegram",
                "reminder_target_label": f"Przypisana osoba nie ma ID Telegram: {assigned['name']}",
            }
        if owner and owner["enabled"] and not owner["telegram_user_id"]:
            return {
                "reminder_target_user_id": owner["user_id"],
                "reminder_target_name": owner["name"],
                "reminder_target_ready": False,
                "reminder_target_reason": "owner_missing_telegram",
                "reminder_target_label": f"Wlasciciel wpisu nie ma ID Telegram: {owner['name']}",
            }
        if assigned and not assigned["enabled"]:
            return {
                "reminder_target_user_id": assigned["user_id"],
                "reminder_target_name": assigned["name"],
                "reminder_target_ready": False,
                "reminder_target_reason": "assigned_disabled",
                "reminder_target_label": f"Przypisana osoba ma wylaczone przypomnienia: {assigned['name']}",
            }
        if owner and not owner["enabled"]:
            return {
                "reminder_target_user_id": owner["user_id"],
                "reminder_target_name": owner["name"],
                "reminder_target_ready": False,
                "reminder_target_reason": "owner_disabled",
                "reminder_target_label": f"Wlasciciel ma wylaczone przypomnienia: {owner['name']}",
            }
        return {
            "reminder_target_user_id": None,
            "reminder_target_name": None,
            "reminder_target_ready": False,
            "reminder_target_reason": "missing",
            "reminder_target_label": "Brak gotowego odbiorcy przypomnienia Telegram",
        }

    def _matches_focus_view(self, task: dict[str, Any], focus_view: str, viewer_user_id: int | None) -> bool:
        if focus_view not in TASK_FOCUS_VIEWS:
            return True
        if str(task.get("status") or "") in {"zakonczone", "anulowane"}:
            return False
        due_dt = self._parse_local_datetime(task.get("due_at"))
        remind_dt = self._parse_local_datetime(task.get("remind_at"))
        now_dt = datetime.now().replace(second=0, microsecond=0)
        today_start = now_dt.replace(hour=0, minute=0)
        tomorrow_start = today_start + timedelta(days=1)
        owner_user_id = int(task.get("owner_user_id") or 0)
        assigned_user_id = int(task.get("assigned_user_id") or 0) if task.get("assigned_user_id") else None
        visibility_scope = str(task.get("visibility_scope") or "prywatne")

        if focus_view == "moj_dzien":
            if viewer_user_id is None or viewer_user_id not in {owner_user_id, assigned_user_id}:
                return False
            anchors = [value for value in (remind_dt, due_dt) if value is not None]
            return any(value < tomorrow_start for value in anchors)
        if focus_view == "do_decyzji":
            return bool(
                visibility_scope != "prywatne"
                and str(task.get("priority") or "normalny") in {"wysoki", "krytyczny"}
                and str(task.get("status") or "") in {"nowe", "oczekuje"}
            )
        if focus_view == "przypisane_do_mnie":
            return viewer_user_id is not None and assigned_user_id == viewer_user_id
        if focus_view == "po_terminie":
            return any(value < now_dt for value in (remind_dt, due_dt) if value is not None)
        if focus_view == "czeka_na_kogos":
            return str(task.get("status") or "") == "oczekuje" or (
                assigned_user_id is not None and viewer_user_id is not None and assigned_user_id != viewer_user_id
            )
        if focus_view == "prywatne":
            return visibility_scope == "prywatne" and owner_user_id == viewer_user_id
        if focus_view == "organizacyjne":
            return visibility_scope == "organizacja"
        return True

    def _focus_view_codes_for_user(self, viewer_user: dict[str, Any] | None) -> tuple[str, ...]:
        role = str((viewer_user or {}).get("role") or "")
        if role in MANAGER_ASSISTANT_MANAGER_ROLES:
            return MANAGER_TASK_FOCUS_VIEWS
        return WORKER_TASK_FOCUS_VIEWS

    def _focus_sort_key(self, task: dict[str, Any]) -> tuple[str, int, int]:
        anchor = str(task.get("remind_at") or task.get("due_at") or "9999-12-31T23:59")
        priority_order = {"krytyczny": 0, "wysoki": 1, "normalny": 2, "niski": 3}
        priority_rank = priority_order.get(str(task.get("priority") or "normalny"), 4)
        return (anchor, priority_rank, -int(task.get("task_id") or 0))

    def _calculate_next_recurrence(self, task: dict[str, Any]) -> tuple[str | None, str | None]:
        pattern = str(task.get("recurrence_pattern") or "brak")
        if pattern == "brak":
            return None, None
        interval = int(task.get("recurrence_interval") or 1)
        due_dt = self._parse_local_datetime(task.get("due_at"))
        remind_dt = self._parse_local_datetime(task.get("remind_at"))
        anchor_dt = due_dt or remind_dt
        if anchor_dt is None:
            return None, None
        if pattern == "codziennie":
            next_anchor = anchor_dt + timedelta(days=interval)
        elif pattern == "co_tydzien":
            weekdays = self._normalize_recurrence_weekdays(task.get("recurrence_weekdays"))
            if weekdays:
                next_anchor = self._advance_to_next_weekday(anchor_dt, weekdays, interval)
            else:
                next_anchor = anchor_dt + timedelta(days=7 * interval)
        elif pattern == "dni_robocze":
            next_anchor = self._advance_to_next_business_day(anchor_dt)
        elif pattern == "co_miesiac":
            next_anchor = self._shift_month(anchor_dt, interval)
        else:
            return None, None

        if due_dt and remind_dt:
            reminder_delta = due_dt - remind_dt
            next_due = next_anchor
            next_remind = next_due - reminder_delta
        elif due_dt:
            next_due = next_anchor
            next_remind = None
        else:
            next_due = None
            next_remind = next_anchor

        recurrence_end_dt = self._parse_local_datetime(task.get("recurrence_end_at"))
        reference_dt = next_due or next_remind
        if recurrence_end_dt and reference_dt and reference_dt > recurrence_end_dt:
            return None, None
        return (
            next_due.strftime("%Y-%m-%dT%H:%M") if next_due else None,
            next_remind.strftime("%Y-%m-%dT%H:%M") if next_remind else None,
        )

    def _advance_to_next_business_day(self, value: datetime) -> datetime:
        candidate = value + timedelta(days=1)
        while candidate.weekday() > 4:
            candidate += timedelta(days=1)
        return candidate

    def _advance_to_next_weekday(self, value: datetime, weekdays: str, interval: int) -> datetime:
        allowed = sorted(int(item) for item in weekdays.split(",") if item.strip().isdigit())
        if not allowed:
            return value + timedelta(days=7 * interval)
        candidate = value + timedelta(days=1)
        max_iterations = 366
        while max_iterations > 0:
            week_difference = max(0, ((candidate.date() - value.date()).days) // 7)
            if candidate.weekday() in allowed and week_difference % max(1, interval) == 0:
                return candidate
            candidate += timedelta(days=1)
            max_iterations -= 1
        return value + timedelta(days=7 * max(1, interval))

    def _shift_month(self, value: datetime, months: int) -> datetime:
        total_months = (value.month - 1) + months
        year = value.year + total_months // 12
        month = total_months % 12 + 1
        day = min(value.day, monthrange(year, month)[1])
        return value.replace(year=year, month=month, day=day)

    def _create_next_recurrence_occurrence(
        self,
        task: dict[str, Any],
        *,
        previous_task: dict[str, Any],
        visible_user_ids: list[int],
        actor: str,
    ) -> None:
        if str(task.get("status") or "") != "zakonczone":
            return
        if str(previous_task.get("status") or "") == "zakonczone":
            return
        if str(task.get("recurrence_pattern") or "brak") == "brak":
            return

        next_due_at, next_remind_at = self._calculate_next_recurrence(task)
        if not next_due_at and not next_remind_at:
            return

        existing = self.task_repository.find_recurring_successor(
            str(task.get("recurrence_series_id") or ""),
            due_after=next_due_at,
            remind_after=next_remind_at,
            organization_id=int(task["organization_id"]),
        )
        if existing:
            return

        next_task_id = self.task_repository.create(
            {
                "organization_id": int(task["organization_id"]),
                "task_type": task["task_type"],
                "visibility_scope": task.get("visibility_scope") or "prywatne",
                "owner_user_id": int(task["owner_user_id"]),
                "title": task["title"],
                "description": task.get("description"),
                "status": "nowe",
                "priority": task.get("priority") or "normalny",
                "due_at": next_due_at,
                "remind_at": next_remind_at,
                "recurrence_pattern": task.get("recurrence_pattern") or "brak",
                "recurrence_interval": int(task.get("recurrence_interval") or 1),
                "recurrence_weekdays": task.get("recurrence_weekdays"),
                "recurrence_end_at": task.get("recurrence_end_at"),
                "recurrence_series_id": task.get("recurrence_series_id"),
                "recurrence_parent_task_id": int(task["task_id"]),
                "assigned_user_id": task.get("assigned_user_id"),
                "calendar_id": task.get("calendar_id"),
                "calendar_duration_minutes": int(task.get("calendar_duration_minutes") or 60),
                "created_by_user_id": int(task["owner_user_id"]),
                "completed_at": None,
            }
        )
        self.task_repository.replace_visibility_users(next_task_id, int(task["organization_id"]), visible_user_ids)
        created_task = self.task_repository.get_by_id(
            next_task_id,
            organization_id=int(task["organization_id"]),
            viewer_user_id=int(task["owner_user_id"]),
        )
        if created_task:
            self._synchronize_google_calendar(created_task, organization_id=int(task["organization_id"]))
        self._log_task_history(
            task_id=int(task["task_id"]),
            organization_id=int(task["organization_id"]),
            action_type="task_recurrence_generated",
            actor=actor,
            message=f"Utworzono kolejne wystapienie cykliczne na {next_due_at or next_remind_at}.",
            details={
                "task_id": int(task["task_id"]),
                "next_task_id": next_task_id,
                "next_due_at": next_due_at,
                "next_remind_at": next_remind_at,
            },
        )
        self.event_repository.log(
            event_type="task_created",
            invoice_id=None,
            organization_id=int(task["organization_id"]),
            source=None,
            status_before=None,
            status_after="nowe",
            decision_reason=f"Automatycznie utworzono kolejne wystapienie wpisu: {task['title']}.",
            actor=actor,
            details={"task_id": next_task_id, "recurrence_series_id": task.get("recurrence_series_id")},
        )

    def _log_task_history(
        self,
        *,
        task_id: int,
        organization_id: int,
        action_type: str,
        actor: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.task_repository.create_history(
            {
                "task_id": task_id,
                "organization_id": organization_id,
                "action_type": action_type,
                "actor": actor,
                "message": message,
                "details": json_dumps(details or {}),
            }
        )

    def _normalize_choice(self, value: Any, allowed: tuple[str, ...], default: str, error_message: str) -> str:
        normalized = str(value or "").strip() or default
        if normalized not in allowed:
            raise ValueError(error_message)
        return normalized

    def _normalize_optional_text(self, value: Any) -> str | None:
        normalized = str(value or "").strip()
        return normalized or None

    def _normalize_optional_id(self, value: Any) -> int | None:
        normalized = str(value or "").strip()
        if not normalized:
            return None
        if not normalized.isdigit():
            raise ValueError("Nieprawidlowy identyfikator uzytkownika.")
        return int(normalized)

    def _normalize_optional_id_list(self, values: Any) -> list[int]:
        if values in (None, ""):
            return []
        if isinstance(values, (list, tuple, set)):
            raw_values = values
        else:
            raw_values = [values]

        result: list[int] = []
        for value in raw_values:
            normalized = str(value or "").strip()
            if not normalized:
                continue
            if not normalized.isdigit():
                raise ValueError("Nieprawidlowy identyfikator uzytkownika na liscie widocznosci.")
            result.append(int(normalized))
        return sorted(set(result))

    def _normalize_linked_entities(self, value: Any) -> list[dict[str, int | str]]:
        if value in (None, ""):
            return []
        if not isinstance(value, (list, tuple)):
            raise ValueError("Powiazania wpisu musza byc lista obiektow.")

        normalized_entities: list[dict[str, int | str]] = []
        seen: set[tuple[str, int]] = set()
        for item in value:
            if not isinstance(item, dict):
                raise ValueError("Kazde powiazanie wpisu musi miec typ i identyfikator.")
            entity_type = str(item.get("entity_type") or "").strip().lower()
            entity_id_raw = str(item.get("entity_id") or "").strip()
            if entity_type not in {"invoice", "contractor", "knowledge_document"}:
                raise ValueError("Mozna powiazac wpis tylko z faktura, kontrahentem albo dokumentem firmowym.")
            if not entity_id_raw.isdigit():
                raise ValueError("Powiazanie wpisu ma nieprawidlowy identyfikator.")
            entity_id = int(entity_id_raw)
            key = (entity_type, entity_id)
            if key in seen:
                continue
            seen.add(key)
            normalized_entities.append({"entity_type": entity_type, "entity_id": entity_id})
        return sorted(normalized_entities, key=lambda item: (str(item["entity_type"]), int(item["entity_id"])))

    def _normalize_optional_minutes(self, value: Any, *, default: int) -> int:
        normalized = str(value or "").strip()
        if not normalized:
            return max(1, int(default))
        if not normalized.isdigit():
            raise ValueError("Czas wpisu w kalendarzu musi byc liczba minut.")
        return min(max(1, int(normalized)), 1440)

    def _normalize_optional_int(self, value: Any) -> int | None:
        normalized = str(value or "").strip()
        if not normalized:
            return None
        if not re.fullmatch(r"-?\d+", normalized):
            raise ValueError("Wartosc musi byc liczba calkowita.")
        return int(normalized)

    def _validate_linked_entities(
        self,
        linked_entities: list[dict[str, int | str]],
        *,
        organization_id: int,
    ) -> list[dict[str, int | str]]:
        validated: list[dict[str, int | str]] = []
        for item in linked_entities:
            entity_type = str(item["entity_type"])
            entity_id = int(item["entity_id"])
            if entity_type == "invoice":
                invoice = self.invoice_repository.get_by_id(entity_id, organization_id=organization_id)
                if not invoice:
                    raise ValueError("Nie znaleziono wskazanej faktury do powiazania.")
            elif entity_type == "contractor":
                contractor = self.contractor_repository.get_by_id(entity_id, organization_id=organization_id)
                if not contractor:
                    raise ValueError("Nie znaleziono wskazanego kontrahenta do powiazania.")
            elif entity_type == "knowledge_document":
                if not self.knowledge_repository:
                    raise ValueError("Powiazania z dokumentami firmowymi nie sa teraz dostepne.")
                knowledge_document = self.knowledge_repository.get_by_id(entity_id, organization_id=organization_id)
                if not knowledge_document:
                    raise ValueError("Nie znaleziono wskazanego dokumentu firmowego do powiazania.")
            validated.append({"entity_type": entity_type, "entity_id": entity_id})
        return validated

    def _linked_entities_changed(
        self,
        current_items: list[dict[str, int | str]],
        next_items: list[dict[str, int | str]],
    ) -> bool:
        current_keys = {(str(item["entity_type"]), int(item["entity_id"])) for item in current_items}
        next_keys = {(str(item["entity_type"]), int(item["entity_id"])) for item in next_items}
        return current_keys != next_keys

    def _normalize_optional_bool(self, value: Any, *, default: bool = False) -> int:
        if value in (None, ""):
            return 1 if default else 0
        if isinstance(value, bool):
            return 1 if value else 0
        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "tak", "on"}:
            return 1
        if normalized in {"0", "false", "no", "nie", "off"}:
            return 0
        raise ValueError("Wartosc logiczna jest nieprawidlowa.")

    def _normalize_checklist_payload(self, value: Any) -> list[str]:
        if value in (None, ""):
            return []
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                parsed = [part.strip() for part in value.split("\n")]
        else:
            parsed = value
        if not isinstance(parsed, (list, tuple)):
            raise ValueError("Checklista musi byc lista elementow.")
        result: list[str] = []
        for item in parsed:
            normalized = str(item or "").strip()
            if normalized:
                result.append(normalized)
        return result

    def _validate_assigned_user(self, user_id: int | None, organization_id: int) -> dict[str, Any] | None:
        if user_id is None:
            return None
        user = self.user_repository.get_by_id(user_id)
        if not user or not user.get("is_active"):
            raise ValueError("Nie mozna przypisac wpisu do nieistniejacego lub nieaktywnego uzytkownika.")
        if int(user.get("organization_id") or 0) != int(organization_id):
            raise ValueError("Mozna przypisac wpis tylko do uzytkownika z tej samej organizacji.")
        return user

    def _resolve_visibility_users(
        self,
        *,
        visibility_scope: str,
        requested_user_ids: list[int],
        owner_user_id: int,
        assigned_user_id: int | None,
        organization_id: int,
    ) -> list[int]:
        if visibility_scope == "prywatne":
            if assigned_user_id not in (None, owner_user_id):
                raise ValueError("Prywatny wpis mozna przypisac tylko sobie.")
            return []

        normalized_user_ids: list[int] = []
        for user_id in requested_user_ids:
            if user_id == owner_user_id:
                continue
            user = self.user_repository.get_by_id(user_id)
            if not user or not user.get("is_active"):
                raise ValueError("Na liscie widocznosci znajduje sie nieistniejacy lub nieaktywny uzytkownik.")
            if int(user.get("organization_id") or 0) != int(organization_id):
                raise ValueError("Mozna udostepniac wpis tylko uzytkownikom z tej samej organizacji.")
            normalized_user_ids.append(user_id)

        if visibility_scope == "wybrane_osoby":
            if assigned_user_id not in (None, owner_user_id) and assigned_user_id not in normalized_user_ids:
                normalized_user_ids.append(int(assigned_user_id))
            normalized_user_ids = sorted(set(normalized_user_ids))
            if not normalized_user_ids:
                raise ValueError("Dla zakresu 'Wybrane osoby' wybierz przynajmniej jedna osobe.")
            return normalized_user_ids

        return []

    def _validate_reminder(self, *, due_at: str | None, remind_at: str | None) -> None:
        if due_at and remind_at and remind_at > due_at:
            raise ValueError("Godzina przypomnienia nie moze byc pozniejsza niz termin zadania.")

    def _parse_local_datetime(self, value: Any) -> datetime | None:
        normalized = str(value or "").strip()
        if not normalized:
            return None
        try:
            return datetime.strptime(normalized, "%Y-%m-%dT%H:%M")
        except ValueError:
            return None

    def _sanitize_attachment_name(self, value: str) -> str:
        base_name = Path(str(value or "").strip()).name or "zalacznik.bin"
        sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", base_name).strip("._")
        return sanitized or "zalacznik.bin"

    def _attachment_name_from_url(self, value: str) -> str:
        parsed = urlparse(str(value or "").strip())
        candidate = Path(parsed.path or "").name
        if candidate:
            return candidate
        host = parsed.netloc.replace(":", "_").strip()
        return f"{host or 'link'}.url"

    def _validate_task_distribution_permissions(
        self,
        *,
        actor_user: dict[str, Any],
        visibility_scope: str,
        visible_user_ids: list[int],
        assigned_user_id: int | None,
        owner_user_id: int,
    ) -> None:
        if actor_user.get("role") in TASK_ASSIGNMENT_ROLES:
            return
        if visibility_scope != "prywatne":
            raise ValueError("Ta rola nie moze udostepniac zadan innym osobom.")
        if visible_user_ids:
            raise ValueError("Ta rola nie moze wybierac dodatkowych odbiorcow zadania.")
        if assigned_user_id not in {None, owner_user_id}:
            raise ValueError("Ta rola nie moze przypisywac zadania innym osobom.")

    def _visibility_label(self, visibility_scope: str) -> str:
        labels = {
            "prywatne": "Prywatne",
            "wybrane_osoby": "Wybrane osoby",
            "organizacja": "Cala organizacja",
        }
        return labels.get(visibility_scope, visibility_scope)

    def _resolve_note_mentions(self, note_text: str, organization_id: int) -> list[dict[str, Any]]:
        users = self.user_repository.list_users(organization_id=organization_id)
        normalized_text = str(note_text or "").lower()
        mention_candidates: dict[str, dict[str, Any]] = {}
        for user in users:
            if not user.get("is_active"):
                continue
            aliases = {
                str(user.get("login") or "").strip().lower(),
                str(user.get("display_name") or "").strip().lower(),
            }
            aliases = {alias for alias in aliases if alias}
            for alias in aliases:
                mention_candidates[self._normalize_mention_key(alias)] = user
        matches: list[dict[str, Any]] = []
        for raw_match in re.findall(r"@([A-Za-z0-9._-]+(?:\s+[A-Za-z0-9._-]+)*)", normalized_text):
            normalized_match = self._normalize_mention_key(raw_match)
            matched_user = mention_candidates.get(normalized_match)
            if matched_user and matched_user not in matches:
                matches.append(matched_user)
        return matches

    def _normalize_mention_key(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", str(value or "").strip().lower())
        ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
        return re.sub(r"[^a-z0-9]+", "", ascii_only)

    def _decorate_template(self, template: dict[str, Any]) -> dict[str, Any]:
        result = dict(template)
        result["checklist_items"] = self._normalize_checklist_payload(result.get("checklist_json"))
        result["is_active"] = bool(int(result.get("is_active") or 0))
        return result

    def _decorate_note(self, note: dict[str, Any]) -> dict[str, Any]:
        result = dict(note)
        for key in ("mentioned_user_ids", "mentioned_user_names"):
            value = result.get(key)
            if isinstance(value, str) and value.strip():
                try:
                    result[key] = json.loads(value)
                except json.JSONDecodeError:
                    result[key] = [value]
            elif value in (None, ""):
                result[key] = []
        return result

    def _linked_entity_label(self, item: dict[str, Any]) -> str:
        entity_type = str(item.get("entity_type") or "")
        if entity_type == "invoice":
            invoice_number = str(item.get("invoice_number") or "").strip()
            if invoice_number:
                return f"Faktura {invoice_number}"
            return f"Faktura #{int(item.get('entity_id') or 0)}"
        if entity_type == "contractor":
            return str(item.get("contractor_name") or f"Kontrahent #{int(item.get('entity_id') or 0)}")
        if entity_type == "knowledge_document":
            title = str(item.get("knowledge_document_title") or "").strip()
            if title:
                return f"Dokument {title}"
            return f"Dokument #{int(item.get('entity_id') or 0)}"
        return str(item.get("entity_type") or "Powiazanie")

    def _linked_entity_subtitle(self, item: dict[str, Any]) -> str:
        entity_type = str(item.get("entity_type") or "")
        if entity_type == "invoice":
            parts = []
            if item.get("invoice_issuer_name"):
                parts.append(str(item["invoice_issuer_name"]))
            if item.get("invoice_gross_amount") not in (None, ""):
                parts.append(f"{item['invoice_gross_amount']} {item.get('invoice_currency') or 'PLN'}")
            return " | ".join(parts)
        if entity_type == "contractor":
            nip = str(item.get("contractor_nip") or "").strip()
            return f"NIP: {nip}" if nip else ""
        if entity_type == "knowledge_document":
            parts = []
            file_name = str(item.get("knowledge_document_file_name") or "").strip()
            business_status = str(item.get("knowledge_document_business_status") or "").strip()
            if file_name:
                parts.append(file_name)
            if business_status:
                parts.append(business_status.replace("_", " "))
            return " | ".join(parts)
        return ""

    def _decorate_linked_entity(self, item: dict[str, Any]) -> dict[str, Any]:
        result = dict(item)
        result["entity_type"] = str(result.get("entity_type") or "")
        result["entity_id"] = int(result.get("entity_id") or 0)
        result["label"] = self._linked_entity_label(result)
        result["subtitle"] = self._linked_entity_subtitle(result)
        result["organization_name"] = result.get("linked_organization_name")
        return result

    def _linked_entities_summary(self, items: list[dict[str, Any]]) -> str:
        if not items:
            return "brak"
        return ", ".join(self._linked_entity_label(item) for item in items)

    def _task_type_label(self, task_type: str) -> str:
        labels = {
            "zadanie": "Zadanie",
            "wydarzenie": "Wydarzenie",
            "przypomnienie": "Przypomnienie",
            "notatka": "Notatka",
        }
        return labels.get(task_type, task_type)

    def _decorate_task(
        self,
        task: dict[str, Any],
        *,
        visible_users: list[dict[str, Any]] | None = None,
        linked_entities: list[dict[str, Any]] | None = None,
        viewer_user_id: int | None = None,
    ) -> dict[str, Any]:
        result = dict(task)
        visibility_scope = str(result.get("visibility_scope") or "organizacja")
        result["visibility_scope"] = visibility_scope
        result["visibility_label"] = self._visibility_label(visibility_scope)
        result["owner_user_name"] = result.get("owner_user_name") or result.get("created_by_user_name")

        selected_visible_users = visible_users or []
        result["visible_users"] = [
            {
                "user_id": int(item["user_id"]),
                "user_name": item.get("user_name") or str(item["user_id"]),
            }
            for item in selected_visible_users
        ]
        result["visible_user_ids"] = [item["user_id"] for item in result["visible_users"]]
        result["visible_user_names"] = [item["user_name"] for item in result["visible_users"]]
        selected_linked_entities = linked_entities or []
        result["linked_entities"] = [self._decorate_linked_entity(item) for item in selected_linked_entities]
        result["linked_entity_count"] = len(result["linked_entities"])
        result["linked_invoice_ids"] = [
            int(item["entity_id"])
            for item in result["linked_entities"]
            if str(item.get("entity_type") or "") == "invoice"
        ]
        result["linked_contractor_ids"] = [
            int(item["entity_id"])
            for item in result["linked_entities"]
            if str(item.get("entity_type") or "") == "contractor"
        ]
        result["linked_knowledge_document_ids"] = [
            int(item["entity_id"])
            for item in result["linked_entities"]
            if str(item.get("entity_type") or "") == "knowledge_document"
        ]
        result["calendar_name"] = result.get("calendar_name")
        result["calendar_provider"] = result.get("calendar_provider") or "google_ics"
        result["calendar_provider_label"] = self.calendar_service._provider_label(result["calendar_provider"])
        result["calendar_kind"] = result.get("calendar_kind") or "inne"
        result["calendar_kind_label"] = self.calendar_service._calendar_kind_label(result["calendar_kind"])
        result["calendar_external_calendar_id"] = result.get("calendar_external_calendar_id")
        result["calendar_external_calendar_name"] = result.get("calendar_external_calendar_name")
        result["calendar_external_calendar_timezone"] = result.get("calendar_external_calendar_timezone")
        result["calendar_linked_organization_id"] = result.get("calendar_linked_organization_id")
        result["calendar_linked_organization_name"] = result.get("calendar_linked_organization_name")
        calendar_owner_user_id = int(result.get("calendar_owner_user_id") or 0) if result.get("calendar_owner_user_id") else None
        calendar_access_mode = (
            "assigned"
            if viewer_user_id is not None
            and calendar_owner_user_id is not None
            and calendar_owner_user_id != int(viewer_user_id)
            and result.get("calendar_id")
            else "owner"
        )
        result["calendar_access_mode"] = calendar_access_mode
        result["calendar_access_mode_label"] = (
            "Przypisany kalendarz organizacji" if calendar_access_mode == "assigned" else "Wlasny kalendarz"
        )
        result["calendar_default_duration_minutes"] = int(result.get("calendar_default_duration_minutes") or 60)
        result["calendar_duration_minutes"] = int(result.get("calendar_duration_minutes") or 60)
        result["external_calendar_event_id"] = result.get("external_calendar_event_id")
        result["external_calendar_event_url"] = result.get("external_calendar_event_url")
        result["external_calendar_synced_at"] = result.get("external_calendar_synced_at")
        result["external_calendar_sync_error"] = result.get("external_calendar_sync_error")
        result["external_calendar_sync_state"] = result.get("external_calendar_sync_state")
        result["external_calendar_sync_message"] = result.get("external_calendar_sync_message")
        result["external_calendar_last_checked_at"] = result.get("external_calendar_last_checked_at")
        result["external_calendar_last_check_error"] = result.get("external_calendar_last_check_error")
        result["external_calendar_remote_updated_at"] = result.get("external_calendar_remote_updated_at")
        result["external_calendar_remote_etag"] = result.get("external_calendar_remote_etag")
        result["external_calendar_last_sync_source"] = result.get("external_calendar_last_sync_source")
        result["recurrence_pattern"] = result.get("recurrence_pattern") or "brak"
        result["recurrence_interval"] = int(result.get("recurrence_interval") or 1)
        result["recurrence_weekdays"] = self._normalize_recurrence_weekdays(result.get("recurrence_weekdays"))
        result["recurrence_end_at"] = result.get("recurrence_end_at")
        result["recurrence_series_id"] = result.get("recurrence_series_id")
        result["recurrence_parent_task_id"] = result.get("recurrence_parent_task_id")
        result["recurrence_enabled"] = result["recurrence_pattern"] != "brak"
        result["recurrence_label"] = self._recurrence_label(result["recurrence_pattern"], result["recurrence_interval"])
        result["recurrence_weekdays_label"] = self._recurrence_weekdays_label(result["recurrence_weekdays"])
        result["recurrence_summary"] = (
            f"{result['recurrence_label']}"
            + (
                f" | {result['recurrence_weekdays_label']}"
                if result["recurrence_weekdays_label"] and result["recurrence_pattern"] == "co_tydzien"
                else ""
            )
            + (f" | do {result['recurrence_end_at']}" if result.get("recurrence_end_at") else "")
            if result["recurrence_enabled"]
            else "Brak cyklicznosci"
        )
        result.update(self._build_reminder_target_summary(result))

        remind_at = result.get("remind_at")
        status = str(result.get("status") or "")
        reminder_sent_at = result.get("reminder_sent_at")
        reminder_last_error = str(result.get("reminder_last_error") or "").strip()
        if not remind_at:
            result["has_reminder"] = False
            result["reminder_state"] = "brak"
            result["reminder_delivery_state"] = "brak"
            return result
        result["has_reminder"] = True
        if reminder_sent_at:
            result["reminder_state"] = "wyslane"
            result["reminder_delivery_state"] = "wyslane"
        elif reminder_last_error:
            result["reminder_state"] = "blad"
            result["reminder_delivery_state"] = "blad"
        elif status in {"zakonczone", "anulowane"}:
            result["reminder_state"] = "zamkniete"
            result["reminder_delivery_state"] = "zamkniete"
        elif remind_at <= now_local_datetime_value():
            result["reminder_state"] = "aktywne"
            result["reminder_delivery_state"] = "oczekuje_wysylki"
        else:
            result["reminder_state"] = "zaplanowane"
            result["reminder_delivery_state"] = "zaplanowane"
        return result

    def _synchronize_google_calendar(
        self,
        task: dict[str, Any],
        *,
        organization_id: int | None,
        previous_task: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        task_id = int(task["task_id"])
        current_provider = str(task.get("calendar_provider") or "google_ics")
        previous_provider = str(previous_task.get("calendar_provider") or "") if previous_task else ""

        should_remove_previous = bool(
            previous_task
            and previous_provider == "google_api"
            and str(previous_task.get("external_calendar_event_id") or "").strip()
            and (
                int(previous_task.get("calendar_id") or 0) != int(task.get("calendar_id") or 0)
                or str(previous_task.get("calendar_external_calendar_id") or "") != str(task.get("calendar_external_calendar_id") or "")
                or current_provider != "google_api"
            )
        )
        if should_remove_previous:
            self.calendar_service.remove_task_from_google(previous_task)

        if current_provider != "google_api":
            if any(
                task.get(key)
                for key in (
                    "external_calendar_event_id",
                    "external_calendar_event_url",
                    "external_calendar_synced_at",
                    "external_calendar_sync_error",
                    "external_calendar_sync_state",
                    "external_calendar_sync_message",
                    "external_calendar_last_checked_at",
                    "external_calendar_last_check_error",
                    "external_calendar_remote_updated_at",
                    "external_calendar_remote_etag",
                    "external_calendar_last_sync_source",
                )
            ):
                self.task_repository.update(
                    task_id,
                    {
                        "external_calendar_event_id": None,
                        "external_calendar_event_url": None,
                        "external_calendar_synced_at": None,
                        "external_calendar_sync_error": None,
                        "external_calendar_sync_state": None,
                        "external_calendar_sync_message": None,
                        "external_calendar_last_checked_at": None,
                        "external_calendar_last_check_error": None,
                        "external_calendar_remote_updated_at": None,
                        "external_calendar_remote_etag": None,
                        "external_calendar_last_sync_source": None,
                    },
                )
                refreshed = self.task_repository.get_by_id(
                    task_id,
                    organization_id=organization_id,
                    viewer_user_id=int(task["owner_user_id"]),
                )
                assert refreshed is not None
                return refreshed
            return task

        try:
            sync_payload = self.calendar_service.sync_task_to_google(task)
        except ValueError as error:
            self.task_repository.update(
                task_id,
                {
                    "external_calendar_sync_error": str(error),
                    "external_calendar_sync_state": "blad_zapisu",
                    "external_calendar_sync_message": "Nie udalo sie zapisac wpisu do Google Calendar.",
                    "external_calendar_last_checked_at": now_iso(),
                    "external_calendar_last_check_error": None,
                    "external_calendar_last_sync_source": "app",
                },
            )
            refreshed = self.task_repository.get_by_id(
                task_id,
                organization_id=organization_id,
                viewer_user_id=int(task["owner_user_id"]),
            )
            assert refreshed is not None
            return refreshed

        if sync_payload:
            self.task_repository.update(task_id, sync_payload)
            refreshed = self.task_repository.get_by_id(
                task_id,
                organization_id=organization_id,
                viewer_user_id=int(task["owner_user_id"]),
            )
            assert refreshed is not None
            return refreshed
        return task
