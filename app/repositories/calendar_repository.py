from __future__ import annotations

from typing import Any

from app.db import execute_insert_returning_id, get_connection
from app.utils import now_iso


class CalendarRepository:
    _calendar_select = """
        SELECT
            c.*,
            COALESCE(u.display_name, u.login) AS owner_user_name,
            o.name AS linked_organization_name,
            o.slug AS linked_organization_slug
        FROM user_calendars c
        JOIN users u ON u.user_id = c.owner_user_id
        LEFT JOIN organizations o ON o.organization_id = c.linked_organization_id
    """

    _google_connection_select = """
        SELECT
            conn.*,
            u.organization_id,
            org.name AS organization_name,
            org.slug AS organization_slug,
            approver.login AS approved_by_login,
            approver.display_name AS approved_by_display_name
        FROM user_google_calendar_connections conn
        JOIN users u ON u.user_id = conn.user_id
        LEFT JOIN organizations org ON org.organization_id = u.organization_id
        LEFT JOIN users approver ON approver.user_id = conn.approved_by_user_id
    """

    _assignment_select = """
        SELECT
            assignment.*,
            calendar.display_name AS assigned_calendar_name,
            calendar.provider AS assigned_calendar_provider,
            calendar.calendar_kind AS assigned_calendar_kind,
            calendar.linked_organization_id AS assigned_calendar_organization_id,
            org.name AS assigned_calendar_organization_name,
            assigner.login AS assigned_by_login,
            assigner.display_name AS assigned_by_display_name
        FROM user_calendar_assignments assignment
        JOIN user_calendars calendar ON calendar.user_calendar_id = assignment.user_calendar_id
        LEFT JOIN organizations org ON org.organization_id = calendar.linked_organization_id
        LEFT JOIN users assigner ON assigner.user_id = assignment.assigned_by_user_id
    """

    def list_user_calendars(self, owner_user_id: int) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                {self._calendar_select}
                WHERE c.owner_user_id = ?
                ORDER BY c.is_active DESC, c.display_name ASC, c.user_calendar_id ASC
                """,
                (owner_user_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_visible_user_calendars(self, user_id: int) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM (
                    SELECT
                        c.*,
                        COALESCE(u.display_name, u.login) AS owner_user_name,
                        o.name AS linked_organization_name,
                        o.slug AS linked_organization_slug,
                        'owner' AS access_mode,
                        NULL AS assignment_user_calendar_assignment_id,
                        NULL AS assigned_by_user_id,
                        NULL AS assigned_by_login,
                        NULL AS assigned_by_display_name,
                        NULL AS assignment_created_at,
                        NULL AS assignment_updated_at
                    FROM user_calendars c
                    JOIN users u ON u.user_id = c.owner_user_id
                    LEFT JOIN organizations o ON o.organization_id = c.linked_organization_id
                    WHERE c.owner_user_id = ?
                    UNION ALL
                    SELECT
                        c.*,
                        COALESCE(u.display_name, u.login) AS owner_user_name,
                        o.name AS linked_organization_name,
                        o.slug AS linked_organization_slug,
                        'assigned' AS access_mode,
                        assignment.user_calendar_assignment_id AS assignment_user_calendar_assignment_id,
                        assignment.assigned_by_user_id,
                        assigner.login AS assigned_by_login,
                        assigner.display_name AS assigned_by_display_name,
                        assignment.created_at AS assignment_created_at,
                        assignment.updated_at AS assignment_updated_at
                    FROM user_calendar_assignments assignment
                    JOIN user_calendars c ON c.user_calendar_id = assignment.user_calendar_id
                    JOIN users u ON u.user_id = c.owner_user_id
                    LEFT JOIN organizations o ON o.organization_id = c.linked_organization_id
                    LEFT JOIN users assigner ON assigner.user_id = assignment.assigned_by_user_id
                    WHERE assignment.user_id = ?
                      AND c.owner_user_id <> ?
                ) visible
                ORDER BY visible.is_active DESC, visible.access_mode ASC, visible.display_name ASC, visible.user_calendar_id ASC
                """,
                (user_id, user_id, user_id),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_by_id(self, user_calendar_id: int) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""
                {self._calendar_select}
                WHERE c.user_calendar_id = ?
                """,
                (user_calendar_id,),
            ).fetchone()
        return dict(row) if row else None

    def get_by_id_for_owner(self, user_calendar_id: int, owner_user_id: int) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""
                {self._calendar_select}
                WHERE c.user_calendar_id = ?
                  AND c.owner_user_id = ?
                """,
                (user_calendar_id, owner_user_id),
            ).fetchone()
        return dict(row) if row else None

    def get_by_id_for_user(self, user_calendar_id: int, user_id: int) -> dict[str, Any] | None:
        owned = self.get_by_id_for_owner(user_calendar_id, user_id)
        if owned:
            owned["access_mode"] = "owner"
            owned["assignment_user_calendar_assignment_id"] = None
            owned["assigned_by_user_id"] = None
            owned["assigned_by_login"] = None
            owned["assigned_by_display_name"] = None
            owned["assignment_created_at"] = None
            owned["assignment_updated_at"] = None
            return owned
        assignment = self.get_assignment_for_user(user_id)
        if assignment and int(assignment["user_calendar_id"]) == int(user_calendar_id):
            calendar = self.get_by_id(user_calendar_id)
            if not calendar:
                return None
            calendar["access_mode"] = "assigned"
            calendar["assignment_user_calendar_assignment_id"] = assignment["user_calendar_assignment_id"]
            calendar["assigned_by_user_id"] = assignment.get("assigned_by_user_id")
            calendar["assigned_by_login"] = assignment.get("assigned_by_login")
            calendar["assigned_by_display_name"] = assignment.get("assigned_by_display_name")
            calendar["assignment_created_at"] = assignment.get("created_at")
            calendar["assignment_updated_at"] = assignment.get("updated_at")
            return calendar
        return None

    def get_by_sync_token(self, sync_token: str) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""
                {self._calendar_select}
                WHERE c.sync_token = ?
                  AND c.is_active = 1
                """,
                (sync_token,),
            ).fetchone()
        return dict(row) if row else None

    def create(self, payload: dict[str, Any]) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO user_calendars (
                    owner_user_id, provider, display_name, calendar_kind, linked_organization_id, default_duration_minutes,
                    description, sync_token, external_calendar_id, external_calendar_name, external_calendar_timezone,
                    is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["owner_user_id"],
                    payload.get("provider") or "google_ics",
                    payload["display_name"],
                    payload.get("calendar_kind") or "inne",
                    payload.get("linked_organization_id"),
                    int(payload.get("default_duration_minutes", 60)),
                    payload.get("description"),
                    payload["sync_token"],
                    payload.get("external_calendar_id"),
                    payload.get("external_calendar_name"),
                    payload.get("external_calendar_timezone"),
                    int(payload.get("is_active", 1)),
                    timestamp,
                    timestamp,
                ),
                "user_calendar_id",
            )

    def update(self, user_calendar_id: int, fields: dict[str, Any]) -> None:
        if not fields:
            return
        allowed = {
            "provider",
            "display_name",
            "calendar_kind",
            "linked_organization_id",
            "default_duration_minutes",
            "description",
            "sync_token",
            "external_calendar_id",
            "external_calendar_name",
            "external_calendar_timezone",
            "is_active",
        }
        update_fields = {key: value for key, value in fields.items() if key in allowed}
        if not update_fields:
            return
        update_fields["updated_at"] = now_iso()
        assignments = ", ".join(f"{key} = ?" for key in update_fields)
        values = list(update_fields.values()) + [user_calendar_id]
        with get_connection() as connection:
            connection.execute(
                f"UPDATE user_calendars SET {assignments} WHERE user_calendar_id = ?",
                values,
            )

    def delete(self, user_calendar_id: int) -> None:
        with get_connection() as connection:
            connection.execute("UPDATE tasks SET calendar_id = NULL WHERE calendar_id = ?", (user_calendar_id,))
            connection.execute("DELETE FROM user_calendars WHERE user_calendar_id = ?", (user_calendar_id,))

    def list_tasks_for_calendar(self, user_calendar_id: int) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    t.*,
                    o.name AS organization_name,
                    o.slug AS organization_slug,
                    COALESCE(owner.display_name, owner.login) AS owner_user_name,
                    COALESCE(assignee.display_name, assignee.login) AS assigned_user_name,
                    calendar.provider AS calendar_provider,
                    calendar.calendar_kind AS calendar_kind,
                    calendar.external_calendar_id AS calendar_external_calendar_id,
                    calendar.external_calendar_name AS calendar_external_calendar_name,
                    calendar.external_calendar_timezone AS calendar_external_calendar_timezone,
                    calendar.linked_organization_id AS calendar_linked_organization_id,
                    linked_org.name AS calendar_linked_organization_name,
                    calendar.default_duration_minutes AS calendar_default_duration_minutes
                FROM tasks t
                JOIN organizations o ON o.organization_id = t.organization_id
                LEFT JOIN users owner ON owner.user_id = t.owner_user_id
                LEFT JOIN users assignee ON assignee.user_id = t.assigned_user_id
                LEFT JOIN user_calendars calendar ON calendar.user_calendar_id = t.calendar_id
                LEFT JOIN organizations linked_org ON linked_org.organization_id = calendar.linked_organization_id
                WHERE t.calendar_id = ?
                  AND COALESCE(o.is_active, 1) = 1
                ORDER BY
                    CASE WHEN COALESCE(t.due_at, '') = '' THEN 1 ELSE 0 END,
                    t.due_at ASC,
                    t.updated_at DESC,
                    t.task_id DESC
                """,
                (user_calendar_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_google_connection(self, user_id: int) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM (
                    """ + self._google_connection_select + """
                )
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()
        return dict(row) if row else None

    def list_google_connections(
        self,
        *,
        organization_id: int | None = None,
        user_ids: list[int] | None = None,
    ) -> list[dict[str, Any]]:
        conditions: list[str] = []
        params: list[Any] = []
        if organization_id is not None:
            conditions.append("organization_id = ?")
            params.append(organization_id)
        normalized_ids = [int(item) for item in (user_ids or []) if item is not None]
        if normalized_ids:
            placeholders = ", ".join("?" for _ in normalized_ids)
            conditions.append(f"user_id IN ({placeholders})")
            params.extend(normalized_ids)
        query = self._google_connection_select
        if conditions:
            query = f"SELECT * FROM ({query}) connections WHERE " + " AND ".join(conditions)
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def upsert_google_connection(self, user_id: int, payload: dict[str, Any]) -> int:
        existing = self.get_google_connection(user_id)
        timestamp = now_iso()
        with get_connection() as connection:
            if existing:
                connection.execute(
                    """
                    UPDATE user_google_calendar_connections
                    SET google_email = ?, access_token = ?, refresh_token = ?, token_expires_at = ?, scope = ?,
                        employee_visibility_confirmed = ?, employee_confirmation_at = ?, approval_status = ?,
                        approved_by_user_id = ?, approved_at = ?, updated_at = ?
                    WHERE user_id = ?
                    """,
                    (
                        payload.get("google_email"),
                        payload["access_token"],
                        payload.get("refresh_token"),
                        payload["token_expires_at"],
                        payload.get("scope"),
                        int(payload.get("employee_visibility_confirmed", 0)),
                        payload.get("employee_confirmation_at"),
                        payload.get("approval_status") or "pending_approval",
                        payload.get("approved_by_user_id"),
                        payload.get("approved_at"),
                        timestamp,
                        user_id,
                    ),
                )
                return int(existing["user_google_calendar_connection_id"])
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO user_google_calendar_connections (
                    user_id, google_email, access_token, refresh_token, token_expires_at, scope,
                    employee_visibility_confirmed, employee_confirmation_at, approval_status,
                    approved_by_user_id, approved_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    payload.get("google_email"),
                    payload["access_token"],
                    payload.get("refresh_token"),
                    payload["token_expires_at"],
                    payload.get("scope"),
                    int(payload.get("employee_visibility_confirmed", 0)),
                    payload.get("employee_confirmation_at"),
                    payload.get("approval_status") or "pending_approval",
                    payload.get("approved_by_user_id"),
                    payload.get("approved_at"),
                    timestamp,
                    timestamp,
                ),
                "user_google_calendar_connection_id",
            )

    def approve_google_connection(self, user_id: int, approved_by_user_id: int) -> dict[str, Any] | None:
        timestamp = now_iso()
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE user_google_calendar_connections
                SET approval_status = 'approved',
                    approved_by_user_id = ?,
                    approved_at = ?,
                    updated_at = ?
                WHERE user_id = ?
                """,
                (approved_by_user_id, timestamp, timestamp, user_id),
            )
        return self.get_google_connection(user_id)

    def delete_google_connection(self, user_id: int) -> None:
        with get_connection() as connection:
            connection.execute(
                "DELETE FROM user_google_calendar_connections WHERE user_id = ?",
                (user_id,),
            )

    def get_assignment_for_user(self, user_id: int) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""
                {self._assignment_select}
                WHERE assignment.user_id = ?
                """,
                (user_id,),
            ).fetchone()
        return dict(row) if row else None

    def list_assignments(self, *, user_ids: list[int] | None = None, organization_id: int | None = None) -> list[dict[str, Any]]:
        conditions: list[str] = []
        params: list[Any] = []
        normalized_ids = [int(item) for item in (user_ids or []) if item is not None]
        if normalized_ids:
            placeholders = ", ".join("?" for _ in normalized_ids)
            conditions.append(f"assignment.user_id IN ({placeholders})")
            params.extend(normalized_ids)
        if organization_id is not None:
            conditions.append("calendar.linked_organization_id = ?")
            params.append(organization_id)
        query = self._assignment_select
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def assign_calendar_to_user(self, *, user_id: int, user_calendar_id: int, assigned_by_user_id: int) -> int:
        existing = self.get_assignment_for_user(user_id)
        timestamp = now_iso()
        with get_connection() as connection:
            if existing:
                connection.execute(
                    """
                    UPDATE user_calendar_assignments
                    SET user_calendar_id = ?, assigned_by_user_id = ?, updated_at = ?
                    WHERE user_id = ?
                    """,
                    (user_calendar_id, assigned_by_user_id, timestamp, user_id),
                )
                return int(existing["user_calendar_assignment_id"])
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO user_calendar_assignments (
                    user_id, user_calendar_id, assigned_by_user_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, user_calendar_id, assigned_by_user_id, timestamp, timestamp),
                "user_calendar_assignment_id",
            )

    def delete_assignment_for_user(self, user_id: int) -> None:
        with get_connection() as connection:
            connection.execute("DELETE FROM user_calendar_assignments WHERE user_id = ?", (user_id,))

    def list_organization_calendars(self, organization_id: int) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                {self._calendar_select}
                WHERE c.linked_organization_id = ?
                  AND c.calendar_kind = 'organizacja'
                  AND c.is_active = 1
                ORDER BY c.display_name ASC, c.user_calendar_id ASC
                """,
                (organization_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def create_google_oauth_state(self, user_id: int, state_token: str, expires_at: str) -> int:
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO google_calendar_oauth_states (user_id, state_token, expires_at, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, state_token, expires_at, now_iso()),
                "google_calendar_oauth_state_id",
            )

    def consume_google_oauth_state(self, state_token: str) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM google_calendar_oauth_states
                WHERE state_token = ?
                """,
                (state_token,),
            ).fetchone()
            if not row:
                return None
            connection.execute(
                "DELETE FROM google_calendar_oauth_states WHERE google_calendar_oauth_state_id = ?",
                (row["google_calendar_oauth_state_id"],),
            )
        return dict(row)

    def clear_expired_google_oauth_states(self, expires_before: str) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                DELETE FROM google_calendar_oauth_states
                WHERE expires_at <= ?
                """,
                (expires_before,),
            )
