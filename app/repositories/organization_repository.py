from __future__ import annotations

from typing import Any

from app.db import execute_insert_returning_id, get_connection
from app.utils import now_iso


class OrganizationRepository:
    DEFAULT_ORGANIZATION_NAME = "Organizacja domyślna"
    DEFAULT_ORGANIZATION_SLUG = "organizacja-domyslna"

    def list_organizations(self, only_active: bool = False) -> list[dict[str, Any]]:
        query = """
            SELECT
                o.*,
                (
                    SELECT COUNT(*)
                    FROM users u
                    WHERE u.organization_id = o.organization_id
                ) AS user_count,
                (
                    SELECT COUNT(*)
                    FROM invoices i
                    WHERE i.organization_id = o.organization_id
                ) AS invoice_count,
                (
                    SELECT COUNT(*)
                    FROM contractors c
                    WHERE c.organization_id = o.organization_id
                ) AS contractor_count
            FROM organizations o
        """
        params: list[Any] = []
        if only_active:
            query += " WHERE o.is_active = ?"
            params.append(1)
        query += " ORDER BY o.is_active DESC, o.name ASC"

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_by_id(self, organization_id: int) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM organizations
                WHERE organization_id = ?
                """,
                (organization_id,),
            ).fetchone()
        return dict(row) if row else None

    def get_by_name(self, name: str) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM organizations
                WHERE name = ?
                """,
                (name,),
            ).fetchone()
        return dict(row) if row else None

    def get_by_slug(self, slug: str) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM organizations
                WHERE slug = ?
                """,
                (slug,),
            ).fetchone()
        return dict(row) if row else None

    def get_by_telegram_chat_id(self, telegram_chat_id: str) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM organizations
                WHERE telegram_chat_id = ?
                """,
                (telegram_chat_id,),
            ).fetchone()
        return dict(row) if row else None

    def create(self, payload: dict[str, Any]) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO organizations (
                    name, slug, telegram_chat_id, telegram_chat_name, is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["name"],
                    payload["slug"],
                    payload.get("telegram_chat_id"),
                    payload.get("telegram_chat_name"),
                    int(payload.get("is_active", 1)),
                    timestamp,
                    timestamp,
                ),
                "organization_id",
            )

    def update(self, organization_id: int, fields: dict[str, Any]) -> None:
        if not fields:
            return
        allowed = {"name", "slug", "telegram_chat_id", "telegram_chat_name", "is_active"}
        update_fields = {key: value for key, value in fields.items() if key in allowed}
        if not update_fields:
            return
        update_fields["updated_at"] = now_iso()
        assignments = ", ".join(f"{key} = ?" for key in update_fields)
        values = list(update_fields.values()) + [organization_id]
        with get_connection() as connection:
            connection.execute(
                f"UPDATE organizations SET {assignments} WHERE organization_id = ?",
                values,
            )

    def ensure_default_organization(self) -> dict[str, Any]:
        existing = self.get_by_slug(self.DEFAULT_ORGANIZATION_SLUG)
        if existing:
            return existing

        organization_id = self.create(
            {
                "name": self.DEFAULT_ORGANIZATION_NAME,
                "slug": self.DEFAULT_ORGANIZATION_SLUG,
                "is_active": 1,
            }
        )
        created = self.get_by_id(organization_id)
        assert created is not None
        return created

    def assign_legacy_records_to_default(
        self,
        default_organization_id: int,
        default_admin_login: str,
    ) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE contractors
                SET organization_id = ?
                WHERE organization_id IS NULL
                """,
                (default_organization_id,),
            )
            connection.execute(
                """
                UPDATE invoices
                SET organization_id = ?
                WHERE organization_id IS NULL
                """,
                (default_organization_id,),
            )
            connection.execute(
                """
                UPDATE event_logs
                SET organization_id = (
                    SELECT i.organization_id
                    FROM invoices i
                    WHERE i.id = event_logs.invoice_id
                )
                WHERE organization_id IS NULL
                  AND invoice_id IS NOT NULL
                """
            )
            connection.execute(
                """
                UPDATE event_logs
                SET organization_id = ?
                WHERE organization_id IS NULL
                """,
                (default_organization_id,),
            )
            connection.execute(
                """
                UPDATE users
                SET organization_id = ?
                WHERE organization_id IS NULL
                  AND login <> ?
                """,
                (default_organization_id, default_admin_login),
            )
