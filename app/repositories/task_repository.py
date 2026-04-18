from __future__ import annotations

import json
from typing import Any

from app.db import execute_insert_returning_id, get_connection
from app.utils import future_local_datetime_value, now_iso, now_local_datetime_value


class TaskRepository:
    def _build_visibility_condition(self) -> str:
        return """
            (
                (
                    t.visibility_scope = 'organizacja'
                    AND EXISTS (
                        SELECT 1
                        FROM users viewer
                        WHERE viewer.user_id = ?
                          AND viewer.organization_id = t.organization_id
                    )
                )
                OR t.owner_user_id = ?
                OR t.assigned_user_id = ?
                OR EXISTS (
                    SELECT 1
                    FROM task_visibility_users tvu
                    WHERE tvu.task_id = t.task_id
                      AND tvu.user_id = ?
                )
            )
        """

    def list_tasks(
        self,
        filters: dict[str, Any] | None = None,
        organization_id: int | None = None,
        viewer_user_id: int | None = None,
    ) -> list[dict[str, Any]]:
        filters = filters or {}
        params: list[Any] = []
        conditions = ["COALESCE(o.is_active, 1) = 1"]

        if organization_id is not None:
            conditions.append("t.organization_id = ?")
            params.append(organization_id)
        if viewer_user_id is not None:
            conditions.append(self._build_visibility_condition())
            params.extend([viewer_user_id, viewer_user_id, viewer_user_id, viewer_user_id])

        search = str(filters.get("search") or "").strip()
        if search:
            search_like = f"%{search}%"
            conditions.append(
                """
                (
                    CAST(t.task_id AS TEXT) LIKE ?
                    OR COALESCE(t.title, '') LIKE ?
                    OR COALESCE(t.description, '') LIKE ?
                    OR COALESCE(assignee.display_name, assignee.login, '') LIKE ?
                    OR COALESCE(creator.display_name, creator.login, '') LIKE ?
                )
                """
            )
            params.extend([search_like] * 5)

        for key, column in {
            "task_type": "t.task_type",
            "status": "t.status",
            "priority": "t.priority",
            "assigned_user_id": "t.assigned_user_id",
            "recurrence_pattern": "t.recurrence_pattern",
        }.items():
            value = filters.get(key)
            normalized = str(value).strip() if isinstance(value, str) else value
            if normalized not in (None, ""):
                conditions.append(f"{column} = ?")
                params.append(normalized)

        due_from = str(filters.get("due_from") or "").strip()
        if due_from:
            conditions.append("COALESCE(t.due_at, '') >= ?")
            params.append(due_from)

        due_to = str(filters.get("due_to") or "").strip()
        if due_to:
            conditions.append("COALESCE(t.due_at, '') <= ?")
            params.append(due_to)

        remind_from = str(filters.get("remind_from") or "").strip()
        if remind_from:
            conditions.append("COALESCE(t.remind_at, '') >= ?")
            params.append(remind_from)

        remind_to = str(filters.get("remind_to") or "").strip()
        if remind_to:
            conditions.append("COALESCE(t.remind_at, '') <= ?")
            params.append(remind_to)

        due_reminders_only = str(filters.get("due_reminders_only") or "").strip().lower()
        if due_reminders_only in {"1", "true", "tak"}:
            conditions.append("COALESCE(t.remind_at, '') <> ''")
            conditions.append("COALESCE(t.remind_at, '') <= ?")
            conditions.append("t.status NOT IN ('zakonczone', 'anulowane')")
            params.append(now_local_datetime_value())

        query = """
            SELECT
                t.*,
                o.name AS organization_name,
                o.slug AS organization_slug,
                COALESCE(owner.display_name, owner.login) AS owner_user_name,
                owner.telegram_user_id AS owner_telegram_user_id,
                owner.telegram_reminders_enabled AS owner_telegram_reminders_enabled,
                owner.reminder_quiet_hours_start AS owner_reminder_quiet_hours_start,
                owner.reminder_quiet_hours_end AS owner_reminder_quiet_hours_end,
                owner.reminder_repeat_interval_minutes AS owner_reminder_repeat_interval_minutes,
                COALESCE(assignee.display_name, assignee.login) AS assigned_user_name,
                assignee.telegram_user_id AS assigned_telegram_user_id,
                assignee.telegram_reminders_enabled AS assigned_telegram_reminders_enabled,
                assignee.reminder_quiet_hours_start AS assigned_reminder_quiet_hours_start,
                assignee.reminder_quiet_hours_end AS assigned_reminder_quiet_hours_end,
                assignee.reminder_repeat_interval_minutes AS assigned_reminder_repeat_interval_minutes,
                calendar.display_name AS calendar_name,
                calendar.owner_user_id AS calendar_owner_user_id,
                calendar.provider AS calendar_provider,
                calendar.calendar_kind AS calendar_kind,
                calendar.external_calendar_id AS calendar_external_calendar_id,
                calendar.external_calendar_name AS calendar_external_calendar_name,
                calendar.external_calendar_timezone AS calendar_external_calendar_timezone,
                calendar.linked_organization_id AS calendar_linked_organization_id,
                linked_calendar_org.name AS calendar_linked_organization_name,
                calendar.default_duration_minutes AS calendar_default_duration_minutes,
                COALESCE(creator.display_name, creator.login) AS created_by_user_name
            FROM tasks t
            JOIN organizations o ON o.organization_id = t.organization_id
            LEFT JOIN users owner ON owner.user_id = t.owner_user_id
            LEFT JOIN users assignee ON assignee.user_id = t.assigned_user_id
            LEFT JOIN user_calendars calendar ON calendar.user_calendar_id = t.calendar_id
            LEFT JOIN organizations linked_calendar_org ON linked_calendar_org.organization_id = calendar.linked_organization_id
            LEFT JOIN users creator ON creator.user_id = t.created_by_user_id
        """
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += """
            ORDER BY
                CASE WHEN t.status = 'zakonczone' THEN 1 ELSE 0 END,
                CASE WHEN t.status = 'anulowane' THEN 1 ELSE 0 END,
                CASE WHEN t.due_at IS NULL OR t.due_at = '' THEN 1 ELSE 0 END,
                t.due_at ASC,
                t.updated_at DESC,
                t.task_id DESC
        """

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_by_id(
        self,
        task_id: int,
        organization_id: int | None = None,
        viewer_user_id: int | None = None,
    ) -> dict[str, Any] | None:
        params: list[Any] = [task_id]
        query = """
            SELECT
                t.*,
                o.name AS organization_name,
                o.slug AS organization_slug,
                COALESCE(owner.display_name, owner.login) AS owner_user_name,
                owner.telegram_user_id AS owner_telegram_user_id,
                owner.telegram_reminders_enabled AS owner_telegram_reminders_enabled,
                owner.reminder_quiet_hours_start AS owner_reminder_quiet_hours_start,
                owner.reminder_quiet_hours_end AS owner_reminder_quiet_hours_end,
                owner.reminder_repeat_interval_minutes AS owner_reminder_repeat_interval_minutes,
                COALESCE(assignee.display_name, assignee.login) AS assigned_user_name,
                assignee.telegram_user_id AS assigned_telegram_user_id,
                assignee.telegram_reminders_enabled AS assigned_telegram_reminders_enabled,
                assignee.reminder_quiet_hours_start AS assigned_reminder_quiet_hours_start,
                assignee.reminder_quiet_hours_end AS assigned_reminder_quiet_hours_end,
                assignee.reminder_repeat_interval_minutes AS assigned_reminder_repeat_interval_minutes,
                calendar.display_name AS calendar_name,
                calendar.owner_user_id AS calendar_owner_user_id,
                calendar.provider AS calendar_provider,
                calendar.calendar_kind AS calendar_kind,
                calendar.external_calendar_id AS calendar_external_calendar_id,
                calendar.external_calendar_name AS calendar_external_calendar_name,
                calendar.external_calendar_timezone AS calendar_external_calendar_timezone,
                calendar.linked_organization_id AS calendar_linked_organization_id,
                linked_calendar_org.name AS calendar_linked_organization_name,
                calendar.default_duration_minutes AS calendar_default_duration_minutes,
                COALESCE(creator.display_name, creator.login) AS created_by_user_name
            FROM tasks t
            JOIN organizations o ON o.organization_id = t.organization_id
            LEFT JOIN users owner ON owner.user_id = t.owner_user_id
            LEFT JOIN users assignee ON assignee.user_id = t.assigned_user_id
            LEFT JOIN user_calendars calendar ON calendar.user_calendar_id = t.calendar_id
            LEFT JOIN organizations linked_calendar_org ON linked_calendar_org.organization_id = calendar.linked_organization_id
            LEFT JOIN users creator ON creator.user_id = t.created_by_user_id
            WHERE t.task_id = ?
              AND COALESCE(o.is_active, 1) = 1
        """
        if organization_id is not None:
            query += " AND t.organization_id = ?"
            params.append(organization_id)
        if viewer_user_id is not None:
            query += f" AND {self._build_visibility_condition()}"
            params.extend([viewer_user_id, viewer_user_id, viewer_user_id, viewer_user_id])
        with get_connection() as connection:
            row = connection.execute(query, params).fetchone()
        return dict(row) if row else None

    def create(self, payload: dict[str, Any]) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO tasks (
                    organization_id, task_type, visibility_scope, owner_user_id, title, description, status, priority, due_at,
                    remind_at, recurrence_pattern, recurrence_interval, recurrence_weekdays, recurrence_end_at,
                    recurrence_series_id, recurrence_parent_task_id, assigned_user_id, calendar_id, calendar_duration_minutes, external_calendar_event_id,
                    external_calendar_event_url,
                    external_calendar_synced_at, external_calendar_sync_error, external_calendar_sync_state,
                    external_calendar_sync_message, external_calendar_last_checked_at, external_calendar_last_check_error,
                    external_calendar_remote_updated_at,
                    external_calendar_remote_etag, external_calendar_last_sync_source, created_by_user_id, completed_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["organization_id"],
                    payload["task_type"],
                    payload["visibility_scope"],
                    payload["owner_user_id"],
                    payload["title"],
                    payload.get("description"),
                    payload["status"],
                    payload["priority"],
                    payload.get("due_at"),
                    payload.get("remind_at"),
                    payload.get("recurrence_pattern", "brak"),
                    int(payload.get("recurrence_interval") or 1),
                    payload.get("recurrence_weekdays"),
                    payload.get("recurrence_end_at"),
                    payload.get("recurrence_series_id"),
                    payload.get("recurrence_parent_task_id"),
                    payload.get("assigned_user_id"),
                    payload.get("calendar_id"),
                    int(payload.get("calendar_duration_minutes", 60)),
                    payload.get("external_calendar_event_id"),
                    payload.get("external_calendar_event_url"),
                    payload.get("external_calendar_synced_at"),
                    payload.get("external_calendar_sync_error"),
                    payload.get("external_calendar_sync_state"),
                    payload.get("external_calendar_sync_message"),
                    payload.get("external_calendar_last_checked_at"),
                    payload.get("external_calendar_last_check_error"),
                    payload.get("external_calendar_remote_updated_at"),
                    payload.get("external_calendar_remote_etag"),
                    payload.get("external_calendar_last_sync_source"),
                    payload["created_by_user_id"],
                    payload.get("completed_at"),
                    timestamp,
                    timestamp,
                ),
                "task_id",
            )

    def update(self, task_id: int, fields: dict[str, Any]) -> None:
        if not fields:
            return
        allowed = {
            "task_type",
            "visibility_scope",
            "title",
            "description",
            "status",
            "priority",
            "due_at",
            "remind_at",
            "recurrence_pattern",
            "recurrence_interval",
            "recurrence_weekdays",
            "recurrence_end_at",
            "recurrence_series_id",
            "recurrence_parent_task_id",
            "reminder_sent_at",
            "reminder_last_attempt_at",
            "reminder_last_error",
            "assigned_user_id",
            "calendar_id",
            "calendar_duration_minutes",
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
            "completed_at",
        }
        update_fields = {key: value for key, value in fields.items() if key in allowed}
        if not update_fields:
            return
        update_fields["updated_at"] = now_iso()
        assignments = ", ".join(f"{key} = ?" for key in update_fields)
        values = list(update_fields.values()) + [task_id]
        with get_connection() as connection:
            connection.execute(f"UPDATE tasks SET {assignments} WHERE task_id = ?", values)

    def find_recurring_successor(
        self,
        recurrence_series_id: str,
        *,
        due_after: str | None = None,
        remind_after: str | None = None,
        organization_id: int | None = None,
    ) -> dict[str, Any] | None:
        params: list[Any] = [recurrence_series_id]
        conditions = ["recurrence_series_id = ?"]
        if organization_id is not None:
            conditions.append("organization_id = ?")
            params.append(organization_id)
        if due_after:
            conditions.append("COALESCE(due_at, '') >= ?")
            params.append(due_after)
        elif remind_after:
            conditions.append("COALESCE(remind_at, '') >= ?")
            params.append(remind_after)
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT *
                FROM tasks
                WHERE {' AND '.join(conditions)}
                ORDER BY
                    CASE WHEN due_at IS NULL OR due_at = '' THEN 1 ELSE 0 END,
                    due_at ASC,
                    remind_at ASC,
                    task_id ASC
                LIMIT 1
                """,
                params,
            ).fetchone()
        return dict(row) if row else None

    def list_series_task_ids(
        self,
        recurrence_series_id: str,
        *,
        organization_id: int | None = None,
        exclude_task_id: int | None = None,
        from_anchor: str | None = None,
        include_closed: bool = False,
    ) -> list[int]:
        if not str(recurrence_series_id or "").strip():
            return []
        params: list[Any] = [recurrence_series_id]
        conditions = ["recurrence_series_id = ?"]
        if organization_id is not None:
            conditions.append("organization_id = ?")
            params.append(organization_id)
        if exclude_task_id is not None:
            conditions.append("task_id <> ?")
            params.append(exclude_task_id)
        if not include_closed:
            conditions.append("status NOT IN ('zakonczone', 'anulowane')")
        if from_anchor:
            conditions.append("COALESCE(due_at, remind_at, '') >= ?")
            params.append(from_anchor)

        query = f"""
            SELECT task_id
            FROM tasks
            WHERE {' AND '.join(conditions)}
            ORDER BY
                CASE WHEN due_at IS NULL OR due_at = '' THEN 1 ELSE 0 END,
                due_at ASC,
                remind_at ASC,
                task_id ASC
        """
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [int(row["task_id"]) for row in rows]

    def create_note(self, payload: dict[str, Any]) -> int:
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO task_notes (
                    task_id, organization_id, parent_note_id, note_kind, note_text, mentioned_user_ids,
                    mentioned_user_names, created_by_user_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["task_id"],
                    payload["organization_id"],
                    payload.get("parent_note_id"),
                    payload.get("note_kind") or "comment",
                    payload["note_text"],
                    payload.get("mentioned_user_ids"),
                    payload.get("mentioned_user_names"),
                    payload["created_by_user_id"],
                    now_iso(),
                ),
                "task_note_id",
            )

    def list_notes(self, task_id: int) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    n.*,
                    COALESCE(u.display_name, u.login) AS created_by_user_name
                FROM task_notes n
                LEFT JOIN users u ON u.user_id = n.created_by_user_id
                WHERE n.task_id = ?
                ORDER BY COALESCE(n.parent_note_id, n.task_note_id) ASC, n.created_at ASC, n.task_note_id ASC
                """,
                (task_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_note_by_id(self, note_id: int, *, task_id: int | None = None) -> dict[str, Any] | None:
        params: list[Any] = [note_id]
        query = "SELECT * FROM task_notes WHERE task_note_id = ?"
        if task_id is not None:
            query += " AND task_id = ?"
            params.append(task_id)
        with get_connection() as connection:
            row = connection.execute(query, params).fetchone()
        return dict(row) if row else None

    def create_checklist_item(self, payload: dict[str, Any]) -> int:
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO task_checklist_items (
                    task_id, organization_id, item_text, item_order, is_completed, completed_at,
                    completed_by_user_id, created_by_user_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["task_id"],
                    payload["organization_id"],
                    payload["item_text"],
                    int(payload.get("item_order") or 0),
                    int(payload.get("is_completed") or 0),
                    payload.get("completed_at"),
                    payload.get("completed_by_user_id"),
                    payload["created_by_user_id"],
                    now_iso(),
                    now_iso(),
                ),
                "task_checklist_item_id",
            )

    def list_checklist_items(self, task_id: int) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    item.*,
                    COALESCE(created_by.display_name, created_by.login) AS created_by_user_name,
                    COALESCE(completed_by.display_name, completed_by.login) AS completed_by_user_name
                FROM task_checklist_items item
                LEFT JOIN users created_by ON created_by.user_id = item.created_by_user_id
                LEFT JOIN users completed_by ON completed_by.user_id = item.completed_by_user_id
                WHERE item.task_id = ?
                ORDER BY item.item_order ASC, item.task_checklist_item_id ASC
                """,
                (task_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def update_checklist_item(self, item_id: int, fields: dict[str, Any]) -> None:
        if not fields:
            return
        allowed = {
            "item_text",
            "item_order",
            "is_completed",
            "completed_at",
            "completed_by_user_id",
        }
        update_fields = {key: value for key, value in fields.items() if key in allowed}
        if not update_fields:
            return
        update_fields["updated_at"] = now_iso()
        assignments = ", ".join(f"{key} = ?" for key in update_fields)
        values = list(update_fields.values()) + [item_id]
        with get_connection() as connection:
            connection.execute(
                f"UPDATE task_checklist_items SET {assignments} WHERE task_checklist_item_id = ?",
                values,
            )

    def get_checklist_item(self, item_id: int, *, task_id: int | None = None) -> dict[str, Any] | None:
        params: list[Any] = [item_id]
        query = """
            SELECT *
            FROM task_checklist_items
            WHERE task_checklist_item_id = ?
        """
        if task_id is not None:
            query += " AND task_id = ?"
            params.append(task_id)
        with get_connection() as connection:
            row = connection.execute(query, params).fetchone()
        return dict(row) if row else None

    def count_checklist_items(self, task_id: int) -> dict[str, int]:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) AS completed
                FROM task_checklist_items
                WHERE task_id = ?
                """,
                (task_id,),
            ).fetchone()
        total = int(row["total"]) if row else 0
        completed = int(row["completed"] or 0) if row else 0
        return {"total": total, "completed": completed}

    def create_attachment(self, payload: dict[str, Any]) -> int:
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO task_attachments (
                    task_id, organization_id, file_name, mime_type, file_size, file_link, file_storage_key,
                    storage_backend, uploaded_by_user_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["task_id"],
                    payload["organization_id"],
                    payload["file_name"],
                    payload.get("mime_type"),
                    int(payload.get("file_size") or 0),
                    payload["file_link"],
                    payload["file_storage_key"],
                    payload.get("storage_backend") or "lokalny",
                    payload["uploaded_by_user_id"],
                    now_iso(),
                ),
                "task_attachment_id",
            )

    def list_attachments(self, task_id: int) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    a.*,
                    COALESCE(u.display_name, u.login) AS uploaded_by_user_name
                FROM task_attachments a
                LEFT JOIN users u ON u.user_id = a.uploaded_by_user_id
                WHERE a.task_id = ?
                ORDER BY a.created_at DESC, a.task_attachment_id DESC
                """,
                (task_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def create_history(self, payload: dict[str, Any]) -> int:
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO task_history (
                    task_id, organization_id, action_type, actor, message, details, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["task_id"],
                    payload["organization_id"],
                    payload["action_type"],
                    payload["actor"],
                    payload["message"],
                    payload.get("details"),
                    now_iso(),
                ),
                "task_history_id",
            )

    def list_history(self, task_id: int) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM task_history
                WHERE task_id = ?
                ORDER BY created_at DESC, task_history_id DESC
                """,
                (task_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def replace_visibility_users(self, task_id: int, organization_id: int, user_ids: list[int]) -> None:
        with get_connection() as connection:
            connection.execute("DELETE FROM task_visibility_users WHERE task_id = ?", (task_id,))
            for user_id in user_ids:
                execute_insert_returning_id(
                    connection,
                    """
                    INSERT INTO task_visibility_users (
                        task_id, organization_id, user_id, created_at
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (
                        task_id,
                        organization_id,
                        user_id,
                        now_iso(),
                    ),
                    "task_visibility_user_id",
                )

    def list_visibility_users(self, task_id: int) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    tvu.*,
                    COALESCE(u.display_name, u.login) AS user_name
                FROM task_visibility_users tvu
                JOIN users u ON u.user_id = tvu.user_id
                WHERE tvu.task_id = ?
                ORDER BY user_name ASC, tvu.user_id ASC
                """,
                (task_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def replace_links(
        self,
        task_id: int,
        organization_id: int,
        links: list[dict[str, Any]],
        *,
        created_by_user_id: int | None = None,
    ) -> None:
        with get_connection() as connection:
            connection.execute("DELETE FROM task_links WHERE task_id = ?", (task_id,))
            for link in links:
                execute_insert_returning_id(
                    connection,
                    """
                    INSERT INTO task_links (
                        task_id, organization_id, entity_type, entity_id, created_by_user_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task_id,
                        organization_id,
                        link["entity_type"],
                        int(link["entity_id"]),
                        created_by_user_id,
                        now_iso(),
                    ),
                    "task_link_id",
                )

    def list_links(self, task_id: int) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    tl.*,
                    invoice.invoice_number AS invoice_number,
                    invoice.issuer_name AS invoice_issuer_name,
                    invoice.gross_amount AS invoice_gross_amount,
                    invoice.currency AS invoice_currency,
                    invoice.status AS invoice_status,
                    invoice.duplicate_type AS invoice_duplicate_type,
                    contractor.name AS contractor_name,
                    contractor.nip AS contractor_nip,
                    knowledge.title AS knowledge_document_title,
                    knowledge.file_name AS knowledge_document_file_name,
                    knowledge.business_status AS knowledge_document_business_status,
                    COALESCE(linked_org.name, invoice_org.name, contractor_org.name, knowledge_org.name) AS linked_organization_name
                FROM task_links tl
                LEFT JOIN invoices invoice
                    ON tl.entity_type = 'invoice'
                   AND invoice.id = tl.entity_id
                LEFT JOIN organizations invoice_org
                    ON invoice_org.organization_id = invoice.organization_id
                LEFT JOIN contractors contractor
                    ON tl.entity_type = 'contractor'
                   AND contractor.contractor_id = tl.entity_id
                LEFT JOIN organizations contractor_org
                    ON contractor_org.organization_id = contractor.organization_id
                LEFT JOIN knowledge_documents knowledge
                    ON tl.entity_type = 'knowledge_document'
                   AND knowledge.knowledge_document_id = tl.entity_id
                LEFT JOIN organizations knowledge_org
                    ON knowledge_org.organization_id = knowledge.organization_id
                LEFT JOIN organizations linked_org
                    ON linked_org.organization_id = tl.organization_id
                WHERE tl.task_id = ?
                ORDER BY
                    CASE tl.entity_type WHEN 'invoice' THEN 0 WHEN 'knowledge_document' THEN 1 ELSE 2 END,
                    tl.entity_id ASC
                """,
                (task_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_linked_tasks(
        self,
        entity_type: str,
        entity_id: int,
        *,
        organization_id: int | None = None,
        viewer_user_id: int | None = None,
        include_completed: bool = False,
        limit: int = 12,
    ) -> list[dict[str, Any]]:
        params: list[Any] = [entity_type, int(entity_id)]
        conditions = [
            "tl.entity_type = ?",
            "tl.entity_id = ?",
            "COALESCE(o.is_active, 1) = 1",
        ]
        if organization_id is not None:
            conditions.append("t.organization_id = ?")
            params.append(organization_id)
        if viewer_user_id is not None:
            conditions.append(self._build_visibility_condition())
            params.extend([viewer_user_id, viewer_user_id, viewer_user_id, viewer_user_id])
        if not include_completed:
            conditions.append("t.status NOT IN ('zakonczone', 'anulowane')")

        query = f"""
            SELECT
                t.*,
                o.name AS organization_name,
                o.slug AS organization_slug,
                COALESCE(owner.display_name, owner.login) AS owner_user_name,
                COALESCE(assignee.display_name, assignee.login) AS assigned_user_name,
                COALESCE(creator.display_name, creator.login) AS created_by_user_name,
                calendar.display_name AS calendar_name,
                calendar.provider AS calendar_provider,
                calendar.calendar_kind AS calendar_kind
            FROM task_links tl
            JOIN tasks t ON t.task_id = tl.task_id
            JOIN organizations o ON o.organization_id = t.organization_id
            LEFT JOIN users owner ON owner.user_id = t.owner_user_id
            LEFT JOIN users assignee ON assignee.user_id = t.assigned_user_id
            LEFT JOIN users creator ON creator.user_id = t.created_by_user_id
            LEFT JOIN user_calendars calendar ON calendar.user_calendar_id = t.calendar_id
            WHERE {' AND '.join(conditions)}
            ORDER BY
                CASE WHEN t.due_at IS NULL OR t.due_at = '' THEN 1 ELSE 0 END,
                t.due_at ASC,
                t.updated_at DESC,
                t.task_id DESC
            LIMIT ?
        """
        params.append(limit)
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def list_due_reminders_for_dispatch(
        self,
        *,
        due_before: str,
        retry_before: str,
        limit: int = 20,
        organization_id: int | None = None,
        viewer_user_id: int | None = None,
    ) -> list[dict[str, Any]]:
        params: list[Any] = []
        conditions = [
            "COALESCE(o.is_active, 1) = 1",
            "COALESCE(t.remind_at, '') <> ''",
            "COALESCE(t.remind_at, '') <= ?",
            "t.status NOT IN ('zakonczone', 'anulowane')",
            "(COALESCE(t.reminder_last_attempt_at, '') = '' OR COALESCE(t.reminder_last_attempt_at, '') <= ?)",
        ]
        params.extend([due_before, retry_before])
        if organization_id is not None:
            conditions.append("t.organization_id = ?")
            params.append(organization_id)
        if viewer_user_id is not None:
            conditions.append(self._build_visibility_condition())
            params.extend([viewer_user_id, viewer_user_id, viewer_user_id, viewer_user_id])

        where_clause = " AND ".join(conditions)
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    t.*,
                    o.name AS organization_name,
                    o.slug AS organization_slug,
                    COALESCE(owner.display_name, owner.login) AS owner_user_name,
                    owner.telegram_user_id AS owner_telegram_user_id,
                    owner.telegram_reminders_enabled AS owner_telegram_reminders_enabled,
                    owner.reminder_quiet_hours_start AS owner_reminder_quiet_hours_start,
                    owner.reminder_quiet_hours_end AS owner_reminder_quiet_hours_end,
                    owner.reminder_repeat_interval_minutes AS owner_reminder_repeat_interval_minutes,
                    COALESCE(assignee.display_name, assignee.login) AS assigned_user_name,
                    assignee.telegram_user_id AS assigned_telegram_user_id,
                    assignee.telegram_reminders_enabled AS assigned_telegram_reminders_enabled,
                    assignee.reminder_quiet_hours_start AS assigned_reminder_quiet_hours_start,
                    assignee.reminder_quiet_hours_end AS assigned_reminder_quiet_hours_end,
                    assignee.reminder_repeat_interval_minutes AS assigned_reminder_repeat_interval_minutes,
                    COALESCE(creator.display_name, creator.login) AS created_by_user_name
                FROM tasks t
                JOIN organizations o ON o.organization_id = t.organization_id
                LEFT JOIN users owner ON owner.user_id = t.owner_user_id
                LEFT JOIN users assignee ON assignee.user_id = t.assigned_user_id
                LEFT JOIN users creator ON creator.user_id = t.created_by_user_id
                WHERE {where_clause}
                ORDER BY
                    t.remind_at ASC,
                    t.priority DESC,
                    t.task_id ASC
                LIMIT ?
                """,
                (*params, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def mark_reminder_sent(self, task_id: int, sent_at: str) -> None:
        self.update(
            task_id,
            {
                "reminder_sent_at": sent_at,
                "reminder_last_attempt_at": sent_at,
                "reminder_last_error": None,
            },
        )

    def mark_reminder_failed(self, task_id: int, attempted_at: str, error_message: str) -> None:
        self.update(
            task_id,
            {
                "reminder_last_attempt_at": attempted_at,
                "reminder_last_error": error_message,
            },
        )

    def mark_reminder_deferred(self, task_id: int, attempted_at: str) -> None:
        self.update(
            task_id,
            {
                "reminder_last_attempt_at": attempted_at,
            },
        )

    def reset_reminder_delivery(self, task_id: int) -> None:
        self.update(
            task_id,
            {
                "reminder_sent_at": None,
                "reminder_last_attempt_at": None,
                "reminder_last_error": None,
            },
        )

    def can_user_view_task(self, task_id: int, viewer_user_id: int | None) -> bool:
        if viewer_user_id is None:
            return False
        return self.get_by_id(task_id, viewer_user_id=viewer_user_id) is not None

    def search_tasks(
        self,
        query_text: str,
        *,
        organization_id: int | None = None,
        viewer_user_id: int | None = None,
        limit: int = 6,
    ) -> list[dict[str, Any]]:
        normalized_query = str(query_text or "").strip().lower()
        if not normalized_query:
            return []

        params: list[Any] = []
        conditions = ["COALESCE(o.is_active, 1) = 1"]

        if organization_id is not None:
            conditions.append("t.organization_id = ?")
            params.append(organization_id)
        if viewer_user_id is not None:
            conditions.append(self._build_visibility_condition())
            params.extend([viewer_user_id, viewer_user_id, viewer_user_id, viewer_user_id])

        search_like = f"%{normalized_query}%"
        conditions.append(
            """
            (
                CAST(t.task_id AS TEXT) LIKE ?
                OR LOWER(COALESCE(t.title, '')) LIKE ?
                OR LOWER(COALESCE(t.description, '')) LIKE ?
                OR LOWER(COALESCE(t.task_type, '')) LIKE ?
                OR LOWER(COALESCE(t.status, '')) LIKE ?
                OR LOWER(COALESCE(t.priority, '')) LIKE ?
                OR COALESCE(t.due_at, '') LIKE ?
                OR COALESCE(t.remind_at, '') LIKE ?
                OR LOWER(COALESCE(assignee.display_name, assignee.login, '')) LIKE ?
                OR LOWER(COALESCE(creator.display_name, creator.login, '')) LIKE ?
                OR LOWER(COALESCE(calendar.display_name, '')) LIKE ?
                OR LOWER(COALESCE(o.name, '')) LIKE ?
            )
            """
        )
        params.extend([search_like] * 12)

        query = """
            SELECT
                t.*,
                o.name AS organization_name,
                o.slug AS organization_slug,
                COALESCE(owner.display_name, owner.login) AS owner_user_name,
                COALESCE(assignee.display_name, assignee.login) AS assigned_user_name,
                COALESCE(creator.display_name, creator.login) AS created_by_user_name,
                calendar.display_name AS calendar_name
            FROM tasks t
            JOIN organizations o ON o.organization_id = t.organization_id
            LEFT JOIN users owner ON owner.user_id = t.owner_user_id
            LEFT JOIN users assignee ON assignee.user_id = t.assigned_user_id
            LEFT JOIN users creator ON creator.user_id = t.created_by_user_id
            LEFT JOIN user_calendars calendar ON calendar.user_calendar_id = t.calendar_id
        """
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += """
            ORDER BY
                CASE WHEN t.status IN ('nowe', 'w_toku', 'oczekuje') THEN 0 ELSE 1 END,
                COALESCE(t.due_at, '') ASC,
                t.updated_at DESC,
                t.task_id DESC
            LIMIT ?
        """
        params.append(limit)

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def count_due_reminders(self, organization_id: int | None = None, viewer_user_id: int | None = None) -> int:
        params: list[Any] = [now_local_datetime_value()]
        query = """
            SELECT COUNT(*) AS reminder_count
            FROM tasks t
            JOIN organizations o ON o.organization_id = t.organization_id
            WHERE COALESCE(o.is_active, 1) = 1
              AND COALESCE(t.remind_at, '') <> ''
              AND COALESCE(t.remind_at, '') <= ?
              AND t.status NOT IN ('zakonczone', 'anulowane')
        """
        if organization_id is not None:
            query += " AND t.organization_id = ?"
            params.append(organization_id)
        if viewer_user_id is not None:
            query += f" AND {self._build_visibility_condition()}"
            params.extend([viewer_user_id, viewer_user_id, viewer_user_id, viewer_user_id])
        with get_connection() as connection:
            row = connection.execute(query, params).fetchone()
        return int(row["reminder_count"]) if row else 0

    def list_active_reminders(
        self,
        organization_id: int | None = None,
        viewer_user_id: int | None = None,
        limit: int = 6,
    ) -> list[dict[str, Any]]:
        now_value = now_local_datetime_value()
        upcoming_limit = future_local_datetime_value(24)
        params: list[Any] = [now_value, now_value, upcoming_limit]
        query = """
            SELECT
                t.*,
                o.name AS organization_name,
                o.slug AS organization_slug,
                COALESCE(owner.display_name, owner.login) AS owner_user_name,
                COALESCE(assignee.display_name, assignee.login) AS assigned_user_name,
                COALESCE(creator.display_name, creator.login) AS created_by_user_name
            FROM tasks t
            JOIN organizations o ON o.organization_id = t.organization_id
            LEFT JOIN users owner ON owner.user_id = t.owner_user_id
            LEFT JOIN users assignee ON assignee.user_id = t.assigned_user_id
            LEFT JOIN users creator ON creator.user_id = t.created_by_user_id
            WHERE COALESCE(o.is_active, 1) = 1
              AND COALESCE(t.remind_at, '') <> ''
              AND t.status NOT IN ('zakonczone', 'anulowane')
              AND (
                COALESCE(t.remind_at, '') <= ?
                OR (COALESCE(t.remind_at, '') > ? AND COALESCE(t.remind_at, '') <= ?)
              )
        """
        if organization_id is not None:
            query += " AND t.organization_id = ?"
            params.append(organization_id)
        if viewer_user_id is not None:
            query += f" AND {self._build_visibility_condition()}"
            params.extend([viewer_user_id, viewer_user_id, viewer_user_id, viewer_user_id])
        query += """
            ORDER BY
                CASE WHEN COALESCE(t.remind_at, '') <= ? THEN 0 ELSE 1 END,
                t.remind_at ASC,
                t.priority DESC,
                t.task_id DESC
            LIMIT ?
        """
        params.extend([now_value, limit])
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]
