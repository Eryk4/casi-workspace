from __future__ import annotations

from typing import Any

from app.db import execute_insert_returning_id, get_connection
from app.utils import now_iso


class UserRepository:
    def count_all(self) -> int:
        with get_connection() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM users").fetchone()
        return int(row["total"]) if row else 0

    def list_users(self, organization_id: int | None = None) -> list[dict[str, Any]]:
        params: list[Any] = []
        conditions = []
        if organization_id is not None:
            conditions.append("u.organization_id = ?")
            params.append(organization_id)

        query = """
            SELECT
                u.*,
                creator.login AS created_by_login,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM users u
            LEFT JOIN users creator ON creator.user_id = u.created_by_user_id
            LEFT JOIN organizations o ON o.organization_id = u.organization_id
        """
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY u.is_active DESC, u.role ASC, u.login ASC"

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_by_id(self, user_id: int) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT
                    u.*,
                    creator.login AS created_by_login,
                    o.name AS organization_name,
                    o.slug AS organization_slug
                FROM users u
                LEFT JOIN users creator ON creator.user_id = u.created_by_user_id
                LEFT JOIN organizations o ON o.organization_id = u.organization_id
                WHERE u.user_id = ?
                """,
                (user_id,),
            ).fetchone()
        return dict(row) if row else None

    def get_by_login(self, login: str) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT
                    u.*,
                    creator.login AS created_by_login,
                    o.name AS organization_name,
                    o.slug AS organization_slug
                FROM users u
                LEFT JOIN users creator ON creator.user_id = u.created_by_user_id
                LEFT JOIN organizations o ON o.organization_id = u.organization_id
                WHERE u.login = ?
                """,
                (login,),
            ).fetchone()
        return dict(row) if row else None

    def get_by_telegram_user_id(self, telegram_user_id: str) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT
                    u.*,
                    creator.login AS created_by_login,
                    o.name AS organization_name,
                    o.slug AS organization_slug
                FROM users u
                LEFT JOIN users creator ON creator.user_id = u.created_by_user_id
                LEFT JOIN organizations o ON o.organization_id = u.organization_id
                WHERE u.telegram_user_id = ?
                """,
                (telegram_user_id,),
            ).fetchone()
        return dict(row) if row else None

    def create(self, payload: dict[str, Any]) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO users (
                    login, display_name, telegram_user_id, telegram_reminders_enabled, reminder_quiet_hours_start,
                    reminder_quiet_hours_end, reminder_repeat_interval_minutes, organization_id, password_hash,
                    password_salt, role, can_upload_knowledge, personal_note_text, personal_note_updated_at,
                    workspace_state_json, workspace_state_updated_at, workspace_state_device_id, is_active,
                    last_login_at, created_by_user_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["login"],
                    payload.get("display_name"),
                    payload.get("telegram_user_id"),
                    int(payload.get("telegram_reminders_enabled", 1)),
                    payload.get("reminder_quiet_hours_start"),
                    payload.get("reminder_quiet_hours_end"),
                    int(payload.get("reminder_repeat_interval_minutes", 0)),
                    payload.get("organization_id"),
                    payload["password_hash"],
                    payload["password_salt"],
                    payload["role"],
                    int(payload.get("can_upload_knowledge", 0)),
                    payload.get("personal_note_text", ""),
                    payload.get("personal_note_updated_at"),
                    payload.get("workspace_state_json"),
                    payload.get("workspace_state_updated_at"),
                    payload.get("workspace_state_device_id"),
                    int(payload.get("is_active", 1)),
                    payload.get("last_login_at"),
                    payload.get("created_by_user_id"),
                    timestamp,
                    timestamp,
                ),
                "user_id",
            )

    def update(self, user_id: int, fields: dict[str, Any]) -> None:
        if not fields:
            return
        allowed = {
            "login",
            "display_name",
            "telegram_user_id",
            "telegram_reminders_enabled",
            "browser_notifications_enabled",
            "reminder_quiet_hours_start",
            "reminder_quiet_hours_end",
            "reminder_repeat_interval_minutes",
            "organization_id",
            "password_hash",
            "password_salt",
            "role",
            "can_upload_knowledge",
            "personal_note_text",
            "personal_note_updated_at",
            "workspace_state_json",
            "workspace_state_updated_at",
            "workspace_state_device_id",
            "is_active",
            "last_login_at",
        }
        update_fields = {key: value for key, value in fields.items() if key in allowed}
        if not update_fields:
            return
        update_fields["updated_at"] = now_iso()
        assignments = ", ".join(f"{key} = ?" for key in update_fields)
        values = list(update_fields.values()) + [user_id]
        with get_connection() as connection:
            connection.execute(
                f"UPDATE users SET {assignments} WHERE user_id = ?",
                values,
            )

    def set_last_login(self, user_id: int) -> None:
        with get_connection() as connection:
            connection.execute(
                "UPDATE users SET last_login_at = ?, updated_at = ? WHERE user_id = ?",
                (now_iso(), now_iso(), user_id),
            )

    def update_workspace_state(self, user_id: int, workspace_state_json: str, *, device_id: str | None = None) -> None:
        timestamp = now_iso()
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE users
                SET workspace_state_json = ?,
                    workspace_state_updated_at = ?,
                    workspace_state_device_id = ?,
                    updated_at = ?
                WHERE user_id = ?
                """,
                (workspace_state_json, timestamp, device_id, timestamp, user_id),
            )

    def list_capabilities(self, user_id: int) -> list[str]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT capability_code
                FROM user_capabilities
                WHERE user_id = ?
                ORDER BY capability_code ASC
                """,
                (user_id,),
            ).fetchall()
        return [str(row["capability_code"]) for row in rows]

    def list_capabilities_map(self, user_ids: list[int]) -> dict[int, list[str]]:
        normalized_ids = [int(user_id) for user_id in user_ids if user_id is not None]
        if not normalized_ids:
            return {}
        placeholders = ", ".join("?" for _ in normalized_ids)
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT user_id, capability_code
                FROM user_capabilities
                WHERE user_id IN ({placeholders})
                ORDER BY user_id ASC, capability_code ASC
                """,
                normalized_ids,
            ).fetchall()
        result: dict[int, list[str]] = {user_id: [] for user_id in normalized_ids}
        for row in rows:
            result.setdefault(int(row["user_id"]), []).append(str(row["capability_code"]))
        return result

    def list_memberships(self, user_id: int) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    om.*,
                    o.name AS organization_name,
                    o.slug AS organization_slug
                FROM organization_memberships om
                JOIN organizations o ON o.organization_id = om.organization_id
                WHERE om.user_id = ?
                ORDER BY om.is_primary DESC, o.name ASC, om.organization_membership_id ASC
                """,
                (user_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_memberships_map(self, user_ids: list[int]) -> dict[int, list[dict[str, Any]]]:
        normalized_ids = [int(user_id) for user_id in user_ids if user_id is not None]
        if not normalized_ids:
            return {}
        placeholders = ", ".join("?" for _ in normalized_ids)
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    om.*,
                    o.name AS organization_name,
                    o.slug AS organization_slug
                FROM organization_memberships om
                JOIN organizations o ON o.organization_id = om.organization_id
                WHERE om.user_id IN ({placeholders})
                ORDER BY om.user_id ASC, om.is_primary DESC, o.name ASC, om.organization_membership_id ASC
                """,
                normalized_ids,
            ).fetchall()
        result: dict[int, list[dict[str, Any]]] = {user_id: [] for user_id in normalized_ids}
        for row in rows:
            result.setdefault(int(row["user_id"]), []).append(dict(row))
        return result

    def list_active_organization_members(self, organization_id: int) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    u.*,
                    o.name AS organization_name,
                    o.slug AS organization_slug,
                    om.role AS membership_role,
                    om.membership_status,
                    om.is_primary
                FROM organization_memberships om
                JOIN users u ON u.user_id = om.user_id
                JOIN organizations o ON o.organization_id = om.organization_id
                WHERE om.organization_id = ?
                  AND COALESCE(om.membership_status, 'active') = 'active'
                  AND COALESCE(u.is_active, 1) = 1
                ORDER BY om.is_primary DESC, COALESCE(u.display_name, u.login) ASC, u.login ASC
                """,
                (organization_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def sync_primary_membership(self, user_id: int) -> None:
        timestamp = now_iso()
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT organization_id, role, is_active
                FROM users
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()
            connection.execute(
                "DELETE FROM organization_memberships WHERE user_id = ? AND is_primary = 1",
                (user_id,),
            )
            if not row or row["organization_id"] is None:
                return
            membership_status = "active" if int(row["is_active"] or 0) else "inactive"
            connection.execute(
                """
                INSERT INTO organization_memberships (
                    user_id,
                    organization_id,
                    role,
                    membership_status,
                    is_primary,
                    granted_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    user_id,
                    int(row["organization_id"]),
                    str(row["role"] or ""),
                    membership_status,
                    timestamp,
                    timestamp,
                ),
            )

    def search_users(
        self,
        query_text: str,
        *,
        organization_id: int | None = None,
        limit: int = 6,
    ) -> list[dict[str, Any]]:
        normalized_query = str(query_text or "").strip().lower()
        if not normalized_query:
            return []

        value = f"%{normalized_query}%"
        params: list[Any] = [value, value, value, value, value]
        query = """
            SELECT
                u.*,
                creator.login AS created_by_login,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM users u
            LEFT JOIN users creator ON creator.user_id = u.created_by_user_id
            LEFT JOIN organizations o ON o.organization_id = u.organization_id
            WHERE (
                CAST(u.user_id AS TEXT) LIKE ?
                OR LOWER(COALESCE(u.login, '')) LIKE ?
                OR LOWER(COALESCE(u.display_name, '')) LIKE ?
                OR LOWER(COALESCE(u.telegram_user_id, '')) LIKE ?
                OR LOWER(COALESCE(o.name, '')) LIKE ?
            )
        """
        if organization_id is not None:
            query += " AND u.organization_id = ?"
            params.append(organization_id)
        query += """
            ORDER BY u.is_active DESC, u.login ASC, u.user_id ASC
            LIMIT ?
        """
        params.append(limit)

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def replace_capabilities(self, user_id: int, capabilities: list[str]) -> None:
        normalized = sorted({str(capability).strip() for capability in capabilities if str(capability).strip()})
        timestamp = now_iso()
        with get_connection() as connection:
            connection.execute("DELETE FROM user_capabilities WHERE user_id = ?", (user_id,))
            for capability in normalized:
                connection.execute(
                    """
                    INSERT INTO user_capabilities (user_id, capability_code, granted_at)
                    VALUES (?, ?, ?)
                    """,
                    (user_id, capability, timestamp),
                )
