from __future__ import annotations

from typing import Any

from app.db import execute_insert_returning_id, get_connection
from app.utils import now_iso


class TaskTemplateRepository:
    def list_templates(self, organization_id: int | None = None, *, include_inactive: bool = False) -> list[dict[str, Any]]:
        params: list[Any] = []
        conditions = []
        if organization_id is not None:
            conditions.append("t.organization_id = ?")
            params.append(organization_id)
        if not include_inactive:
            conditions.append("COALESCE(t.is_active, 1) = 1")

        query = """
            SELECT
                t.*,
                COALESCE(u.display_name, u.login) AS created_by_user_name
            FROM task_templates t
            LEFT JOIN users u ON u.user_id = t.created_by_user_id
        """
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY t.is_active DESC, t.template_name ASC, t.task_template_id ASC"

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_by_id(self, template_id: int, organization_id: int | None = None) -> dict[str, Any] | None:
        params: list[Any] = [template_id]
        query = """
            SELECT
                t.*,
                COALESCE(u.display_name, u.login) AS created_by_user_name
            FROM task_templates t
            LEFT JOIN users u ON u.user_id = t.created_by_user_id
            WHERE t.task_template_id = ?
        """
        if organization_id is not None:
            query += " AND t.organization_id = ?"
            params.append(organization_id)
        with get_connection() as connection:
            row = connection.execute(query, params).fetchone()
        return dict(row) if row else None

    def create(self, payload: dict[str, Any]) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO task_templates (
                    organization_id, template_name, template_description, task_type, priority, visibility_scope,
                    due_offset_minutes, reminder_offset_minutes, recurrence_pattern, recurrence_interval,
                    recurrence_weekdays, recurrence_end_offset_minutes, calendar_duration_minutes, checklist_json,
                    is_active, created_by_user_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["organization_id"],
                    payload["template_name"],
                    payload.get("template_description"),
                    payload.get("task_type") or "zadanie",
                    payload.get("priority") or "normalny",
                    payload.get("visibility_scope") or "prywatne",
                    payload.get("due_offset_minutes"),
                    payload.get("reminder_offset_minutes"),
                    payload.get("recurrence_pattern") or "brak",
                    int(payload.get("recurrence_interval") or 1),
                    payload.get("recurrence_weekdays"),
                    payload.get("recurrence_end_offset_minutes"),
                    int(payload.get("calendar_duration_minutes") or 60),
                    payload.get("checklist_json"),
                    int(payload.get("is_active") if payload.get("is_active") is not None else 1),
                    payload["created_by_user_id"],
                    timestamp,
                    timestamp,
                ),
                "task_template_id",
            )

    def update(self, template_id: int, fields: dict[str, Any]) -> None:
        if not fields:
            return
        allowed = {
            "template_name",
            "template_description",
            "task_type",
            "priority",
            "visibility_scope",
            "due_offset_minutes",
            "reminder_offset_minutes",
            "recurrence_pattern",
            "recurrence_interval",
            "recurrence_weekdays",
            "recurrence_end_offset_minutes",
            "calendar_duration_minutes",
            "checklist_json",
            "is_active",
        }
        update_fields = {key: value for key, value in fields.items() if key in allowed}
        if not update_fields:
            return
        update_fields["updated_at"] = now_iso()
        assignments = ", ".join(f"{key} = ?" for key in update_fields)
        values = list(update_fields.values()) + [template_id]
        with get_connection() as connection:
            connection.execute(
                f"UPDATE task_templates SET {assignments} WHERE task_template_id = ?",
                values,
            )

