from __future__ import annotations

from typing import Any

from app.db import execute_insert_returning_id, get_connection
from app.utils import future_local_datetime_value, now_iso, now_local_datetime_value


class TaskRepository:
    def list_tasks(self, filters: dict[str, Any] | None = None, organization_id: int | None = None) -> list[dict[str, Any]]:
        filters = filters or {}
        params: list[Any] = []
        conditions = ["COALESCE(o.is_active, 1) = 1"]

        if organization_id is not None:
            conditions.append("t.organization_id = ?")
            params.append(organization_id)

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
                COALESCE(assignee.display_name, assignee.login) AS assigned_user_name,
                COALESCE(creator.display_name, creator.login) AS created_by_user_name
            FROM tasks t
            JOIN organizations o ON o.organization_id = t.organization_id
            LEFT JOIN users assignee ON assignee.user_id = t.assigned_user_id
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

    def get_by_id(self, task_id: int, organization_id: int | None = None) -> dict[str, Any] | None:
        params: list[Any] = [task_id]
        query = """
            SELECT
                t.*,
                o.name AS organization_name,
                o.slug AS organization_slug,
                COALESCE(assignee.display_name, assignee.login) AS assigned_user_name,
                COALESCE(creator.display_name, creator.login) AS created_by_user_name
            FROM tasks t
            JOIN organizations o ON o.organization_id = t.organization_id
            LEFT JOIN users assignee ON assignee.user_id = t.assigned_user_id
            LEFT JOIN users creator ON creator.user_id = t.created_by_user_id
            WHERE t.task_id = ?
              AND COALESCE(o.is_active, 1) = 1
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
                INSERT INTO tasks (
                    organization_id, task_type, title, description, status, priority, due_at,
                    remind_at, assigned_user_id, created_by_user_id, completed_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["organization_id"],
                    payload["task_type"],
                    payload["title"],
                    payload.get("description"),
                    payload["status"],
                    payload["priority"],
                    payload.get("due_at"),
                    payload.get("remind_at"),
                    payload.get("assigned_user_id"),
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
            "title",
            "description",
            "status",
            "priority",
            "due_at",
            "remind_at",
            "assigned_user_id",
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

    def create_note(self, payload: dict[str, Any]) -> int:
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO task_notes (
                    task_id, organization_id, note_text, created_by_user_id, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    payload["task_id"],
                    payload["organization_id"],
                    payload["note_text"],
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
                ORDER BY n.created_at DESC, n.task_note_id DESC
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

    def count_due_reminders(self, organization_id: int | None = None) -> int:
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
        with get_connection() as connection:
            row = connection.execute(query, params).fetchone()
        return int(row["reminder_count"]) if row else 0

    def list_active_reminders(self, organization_id: int | None = None, limit: int = 6) -> list[dict[str, Any]]:
        now_value = now_local_datetime_value()
        upcoming_limit = future_local_datetime_value(24)
        params: list[Any] = [now_value, now_value, upcoming_limit]
        query = """
            SELECT
                t.*,
                o.name AS organization_name,
                o.slug AS organization_slug,
                COALESCE(assignee.display_name, assignee.login) AS assigned_user_name,
                COALESCE(creator.display_name, creator.login) AS created_by_user_name
            FROM tasks t
            JOIN organizations o ON o.organization_id = t.organization_id
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
