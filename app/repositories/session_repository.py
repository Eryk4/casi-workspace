from __future__ import annotations

from typing import Any

from app.db import execute_insert_returning_id, get_connection
from app.utils import now_iso


class SessionRepository:
    def create(self, payload: dict[str, Any]) -> int:
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO user_sessions (
                    user_id, token_hash, device_id, device_label, ip_address, user_agent, created_at, last_seen_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["user_id"],
                    payload["token_hash"],
                    payload.get("device_id"),
                    payload.get("device_label"),
                    payload.get("ip_address"),
                    payload.get("user_agent"),
                    payload["created_at"],
                    payload["last_seen_at"],
                    payload["expires_at"],
                ),
                "session_id",
            )

    def get_active_by_token_hash(self, token_hash: str) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT
                    s.*,
                    u.login,
                    u.display_name,
                    u.role,
                    u.is_active,
                    u.telegram_reminders_enabled,
                    u.reminder_quiet_hours_start,
                    u.reminder_quiet_hours_end,
                    u.reminder_repeat_interval_minutes,
                    u.can_upload_knowledge,
                    u.workspace_state_json,
                    u.workspace_state_updated_at,
                    u.workspace_state_device_id,
                    u.organization_id,
                    o.name AS organization_name,
                    o.slug AS organization_slug
                FROM user_sessions s
                JOIN users u ON u.user_id = s.user_id
                LEFT JOIN organizations o ON o.organization_id = u.organization_id
                WHERE s.token_hash = ?
                  AND s.expires_at > ?
                """,
                (token_hash, now_iso()),
            ).fetchone()
        return dict(row) if row else None

    def touch(self, session_id: int) -> None:
        with get_connection() as connection:
            connection.execute(
                "UPDATE user_sessions SET last_seen_at = ? WHERE session_id = ?",
                (now_iso(), session_id),
            )

    def delete_by_token_hash(self, token_hash: str) -> None:
        with get_connection() as connection:
            connection.execute(
                "DELETE FROM user_sessions WHERE token_hash = ?",
                (token_hash,),
            )

    def delete_expired(self) -> None:
        with get_connection() as connection:
            connection.execute(
                "DELETE FROM user_sessions WHERE expires_at <= ?",
                (now_iso(),),
            )

    def delete_for_user(self, user_id: int) -> None:
        with get_connection() as connection:
            connection.execute(
                "DELETE FROM user_sessions WHERE user_id = ?",
                (user_id,),
            )

    def delete_for_user_and_device_id(self, user_id: int, device_id: str) -> None:
        with get_connection() as connection:
            connection.execute(
                "DELETE FROM user_sessions WHERE user_id = ? AND device_id = ?",
                (user_id, device_id),
            )

    def count_active_devices_for_user(self, user_id: int, exclude_device_id: str | None = None) -> int:
        query = """
            SELECT COUNT(*)
            FROM (
                SELECT COALESCE(NULLIF(TRIM(COALESCE(device_id, '')), ''), 'session:' || CAST(session_id AS TEXT)) AS device_key
                FROM user_sessions
                WHERE user_id = ?
                  AND expires_at > ?
        """
        params: list[Any] = [user_id, now_iso()]
        if exclude_device_id:
            query += """
                  AND COALESCE(NULLIF(TRIM(COALESCE(device_id, '')), ''), '') <> ?
            """
            params.append(exclude_device_id)
        query += """
                GROUP BY COALESCE(NULLIF(TRIM(COALESCE(device_id, '')), ''), 'session:' || CAST(session_id AS TEXT))
            ) active_devices
        """
        with get_connection() as connection:
            row = connection.execute(query, tuple(params)).fetchone()
        return int(row[0] if row else 0)
