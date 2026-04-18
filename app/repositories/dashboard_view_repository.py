from __future__ import annotations

from typing import Any

from app.db import execute_insert_returning_id, get_connection
from app.utils import now_iso


class DashboardViewRepository:
    def list_views(
        self,
        *,
        module_key: str,
        organization_id: int | None = None,
        include_hidden: bool = False,
    ) -> list[dict[str, Any]]:
        params: list[Any] = []
        conditions = ["v.module_key = ?"]
        params.append(module_key)
        if organization_id is not None:
            conditions.append("v.organization_id = ?")
            params.append(organization_id)
        if not include_hidden:
            conditions.append("COALESCE(v.is_shared, 0) = 1")

        query = """
            SELECT
                v.*,
                COALESCE(u.display_name, u.login) AS created_by_user_name,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM saved_views v
            LEFT JOIN users u ON u.user_id = v.created_by_user_id
            LEFT JOIN organizations o ON o.organization_id = v.organization_id
        """
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY v.is_default DESC, v.view_name ASC, v.saved_view_id ASC"
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_by_id(self, saved_view_id: int, organization_id: int | None = None) -> dict[str, Any] | None:
        params: list[Any] = [saved_view_id]
        query = """
            SELECT
                v.*,
                COALESCE(u.display_name, u.login) AS created_by_user_name,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM saved_views v
            LEFT JOIN users u ON u.user_id = v.created_by_user_id
            LEFT JOIN organizations o ON o.organization_id = v.organization_id
            WHERE v.saved_view_id = ?
        """
        if organization_id is not None:
            query += " AND v.organization_id = ?"
            params.append(organization_id)
        with get_connection() as connection:
            row = connection.execute(query, params).fetchone()
        return dict(row) if row else None

    def get_by_slug(
        self,
        *,
        module_key: str,
        view_slug: str,
        organization_id: int,
    ) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM saved_views
                WHERE organization_id = ?
                  AND module_key = ?
                  AND view_slug = ?
                """,
                (organization_id, module_key, view_slug),
            ).fetchone()
        return dict(row) if row else None

    def create(self, payload: dict[str, Any]) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO saved_views (
                    organization_id, module_key, view_slug, view_name, description, view_state_json, is_shared,
                    is_default, created_by_user_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["organization_id"],
                    payload["module_key"],
                    payload["view_slug"],
                    payload["view_name"],
                    payload.get("description"),
                    payload.get("view_state_json") or "{}",
                    int(payload.get("is_shared", 0)),
                    int(payload.get("is_default", 0)),
                    payload.get("created_by_user_id"),
                    timestamp,
                    timestamp,
                ),
                "saved_view_id",
            )

    def update(self, saved_view_id: int, fields: dict[str, Any]) -> None:
        if not fields:
            return
        allowed = {
            "view_slug",
            "view_name",
            "description",
            "view_state_json",
            "is_shared",
            "is_default",
        }
        update_fields = {key: value for key, value in fields.items() if key in allowed}
        if not update_fields:
            return
        update_fields["updated_at"] = now_iso()
        assignments = ", ".join(f"{key} = ?" for key in update_fields)
        values = list(update_fields.values()) + [saved_view_id]
        with get_connection() as connection:
            connection.execute(
                f"UPDATE saved_views SET {assignments} WHERE saved_view_id = ?",
                values,
            )

    def delete(self, saved_view_id: int, organization_id: int | None = None) -> None:
        params: list[Any] = [saved_view_id]
        query = "DELETE FROM saved_views WHERE saved_view_id = ?"
        if organization_id is not None:
            query += " AND organization_id = ?"
            params.append(organization_id)
        with get_connection() as connection:
            connection.execute(query, params)

