from __future__ import annotations

from typing import Any

from app.domain.constants import TASK_PRIORITIES, TASK_STATUSES, TASK_TYPES
from app.repositories.event_repository import EventRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.utils import json_dumps, now_iso, now_local_datetime_value


class TaskService:
    def __init__(
        self,
        task_repository: TaskRepository,
        event_repository: EventRepository,
        user_repository: UserRepository,
        organization_repository: OrganizationRepository,
    ) -> None:
        self.task_repository = task_repository
        self.event_repository = event_repository
        self.user_repository = user_repository
        self.organization_repository = organization_repository

    def list_tasks(self, filters: dict[str, Any] | None = None, organization_id: int | None = None) -> list[dict[str, Any]]:
        tasks = self.task_repository.list_tasks(filters, organization_id=organization_id)
        return [self._decorate_task(task) for task in tasks]

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
                    "organization_id": user.get("organization_id"),
                    "organization_name": user.get("organization_name"),
                }
            )
        return result

    def get_task_detail(self, task_id: int, organization_id: int | None = None) -> dict[str, Any] | None:
        task = self.task_repository.get_by_id(task_id, organization_id=organization_id)
        if not task:
            return None
        return {
            "task": self._decorate_task(task),
            "notes": self.task_repository.list_notes(task_id),
            "history": self.task_repository.list_history(task_id),
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

        task_type = self._normalize_choice(payload.get("task_type"), TASK_TYPES, "zadanie", "Nieprawidlowy typ wpisu.")
        status = self._normalize_choice(payload.get("status"), TASK_STATUSES, "nowe", "Nieprawidlowy status zadania.")
        priority = self._normalize_choice(payload.get("priority"), TASK_PRIORITIES, "normalny", "Nieprawidlowy priorytet.")
        title = str(payload.get("title") or "").strip()
        description = str(payload.get("description") or "").strip() or None
        due_at = self._normalize_optional_text(payload.get("due_at"))
        remind_at = self._normalize_optional_text(payload.get("remind_at"))
        assigned_user_id = self._normalize_optional_id(payload.get("assigned_user_id"))

        if not title:
            raise ValueError("Tytul zadania jest wymagany.")
        if task_type == "przypomnienie" and not due_at and not remind_at:
            raise ValueError("Przypomnienie musi miec termin albo godzine przypomnienia.")
        if not remind_at and task_type == "przypomnienie" and due_at:
            remind_at = due_at
        self._validate_reminder(due_at=due_at, remind_at=remind_at)

        assigned_user = self._validate_assigned_user(assigned_user_id, organization_id)
        completed_at = now_iso() if status == "zakonczone" else None

        task_id = self.task_repository.create(
            {
                "organization_id": organization_id,
                "task_type": task_type,
                "title": title,
                "description": description,
                "status": status,
                "priority": priority,
                "due_at": due_at,
                "remind_at": remind_at,
                "assigned_user_id": assigned_user_id,
                "created_by_user_id": int(actor_user["user_id"]),
                "completed_at": completed_at,
            }
        )
        task = self.task_repository.get_by_id(task_id, organization_id=organization_id)
        assert task is not None

        history_message = f"Dodano nowe {task_type}: {title}."
        if assigned_user:
            history_message += f" Przypisano do: {assigned_user.get('display_name') or assigned_user.get('login')}."
        if remind_at:
            history_message += f" Ustawiono przypomnienie na: {remind_at}."

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
                "remind_at": remind_at,
                "assigned_user_id": assigned_user_id,
            },
        )
        self.event_repository.log(
            event_type="task_created",
            invoice_id=None,
            organization_id=organization_id,
            source=None,
            status_before=None,
            status_after=status,
            decision_reason=f"Dodano zadanie {title}.",
            actor=actor,
            details={"task_id": task_id, "title": title, "task_type": task_type, "remind_at": remind_at},
        )
        return self._decorate_task(task)

    def update_task(
        self,
        task_id: int,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any] | None:
        current = self.task_repository.get_by_id(task_id, organization_id=organization_id)
        if not current:
            return None

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
        if "assigned_user_id" in payload:
            assigned_user_id = self._normalize_optional_id(payload.get("assigned_user_id"))
            self._validate_assigned_user(assigned_user_id, int(current["organization_id"]))
            if assigned_user_id != current.get("assigned_user_id"):
                updates["assigned_user_id"] = assigned_user_id
                changes.append("osoba_przypisana")

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

        next_status = updates.get("status", current["status"])
        if next_status == "zakonczone" and not current.get("completed_at"):
            updates["completed_at"] = now_iso()
        if next_status != "zakonczone" and current.get("completed_at"):
            updates["completed_at"] = None

        self.task_repository.update(task_id, updates)
        refreshed = self.task_repository.get_by_id(task_id, organization_id=organization_id)
        assert refreshed is not None

        if changes:
            self._log_task_history(
                task_id=task_id,
                organization_id=int(refreshed["organization_id"]),
                action_type="task_updated",
                actor=actor,
                message=f"Zmieniono pola: {', '.join(changes)}.",
                details={"task_id": task_id, "changes": changes, "remind_at": refreshed.get("remind_at")},
            )
            self.event_repository.log(
                event_type="task_updated",
                invoice_id=None,
                organization_id=refreshed["organization_id"],
                source=None,
                status_before=current.get("status"),
                status_after=refreshed.get("status"),
                decision_reason=f"Zmieniono zadanie {refreshed['title']}.",
                actor=actor,
                details={"task_id": task_id, "changes": changes, "remind_at": refreshed.get("remind_at")},
            )
        return self._decorate_task(refreshed)

    def add_task_note(
        self,
        task_id: int,
        note_text: str,
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any] | None:
        task = self.task_repository.get_by_id(task_id, organization_id=organization_id)
        if not task:
            return None
        normalized_note = str(note_text or "").strip()
        if not normalized_note:
            raise ValueError("Tresc notatki jest wymagana.")

        self.task_repository.create_note(
            {
                "task_id": task_id,
                "organization_id": int(task["organization_id"]),
                "note_text": normalized_note,
                "created_by_user_id": int(actor_user["user_id"]),
            }
        )
        self._log_task_history(
            task_id=task_id,
            organization_id=int(task["organization_id"]),
            action_type="task_note_added",
            actor=actor,
            message="Dodano notatke do zadania.",
            details={"task_id": task_id, "note_preview": normalized_note[:160]},
        )
        self.event_repository.log(
            event_type="task_note_added",
            invoice_id=None,
            organization_id=task["organization_id"],
            source=None,
            status_before=None,
            status_after=task["status"],
            decision_reason=f"Dodano notatke do zadania {task['title']}.",
            actor=actor,
            details={"task_id": task_id},
        )
        return self.get_task_detail(task_id, organization_id=organization_id)

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

    def _validate_assigned_user(self, user_id: int | None, organization_id: int) -> dict[str, Any] | None:
        if user_id is None:
            return None
        user = self.user_repository.get_by_id(user_id)
        if not user or not user.get("is_active"):
            raise ValueError("Nie mozna przypisac zadania do nieistniejacego lub nieaktywnego uzytkownika.")
        if int(user.get("organization_id") or 0) != int(organization_id):
            raise ValueError("Mozna przypisac zadanie tylko do uzytkownika z tej samej organizacji.")
        return user

    def _validate_reminder(self, *, due_at: str | None, remind_at: str | None) -> None:
        if due_at and remind_at and remind_at > due_at:
            raise ValueError("Godzina przypomnienia nie moze byc pozniejsza niz termin zadania.")

    def _decorate_task(self, task: dict[str, Any]) -> dict[str, Any]:
        result = dict(task)
        remind_at = result.get("remind_at")
        status = str(result.get("status") or "")
        if not remind_at:
            result["has_reminder"] = False
            result["reminder_state"] = "brak"
            return result
        result["has_reminder"] = True
        if status in {"zakonczone", "anulowane"}:
            result["reminder_state"] = "zamkniete"
        elif remind_at <= now_local_datetime_value():
            result["reminder_state"] = "aktywne"
        else:
            result["reminder_state"] = "zaplanowane"
        return result
