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
                    login, display_name, telegram_user_id, organization_id, password_hash, password_salt, role,
                    is_active, last_login_at, created_by_user_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["login"],
                    payload.get("display_name"),
                    payload.get("telegram_user_id"),
                    payload.get("organization_id"),
                    payload["password_hash"],
                    payload["password_salt"],
                    payload["role"],
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
            "organization_id",
            "password_hash",
            "password_salt",
            "role",
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
