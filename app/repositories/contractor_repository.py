from __future__ import annotations

from typing import Any

from app.db import execute_insert_returning_id, get_connection
from app.utils import now_iso


class ContractorRepository:
    def list_contractors(self, search: str = "", only_new: bool = False, organization_id: int | None = None) -> list[dict[str, Any]]:
        search_value = f"%{search.strip()}%"
        conditions = []
        params: list[Any] = []

        if organization_id is not None:
            conditions.append("c.organization_id = ?")
            params.append(organization_id)
        if search.strip():
            conditions.append("(c.name LIKE ? OR c.nip LIKE ? OR COALESCE(c.email, '') LIKE ?)")
            params.extend([search_value, search_value, search_value])
        if only_new:
            conditions.append("c.is_new = 1")

        query = """
            SELECT
                c.*,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM contractors c
            LEFT JOIN organizations o ON o.organization_id = c.organization_id
        """
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY c.is_new DESC, c.updated_at DESC, c.name ASC"

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_by_id(self, contractor_id: int, organization_id: int | None = None) -> dict[str, Any] | None:
        params: list[Any] = [contractor_id]
        query = """
            SELECT
                c.*,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM contractors c
            LEFT JOIN organizations o ON o.organization_id = c.organization_id
            WHERE c.contractor_id = ?
        """
        if organization_id is not None:
            query += " AND c.organization_id = ?"
            params.append(organization_id)
        with get_connection() as connection:
            row = connection.execute(query, params).fetchone()
        return dict(row) if row else None

    def get_by_nip(self, nip: str, organization_id: int | None = None) -> dict[str, Any] | None:
        params: list[Any] = [nip]
        query = """
            SELECT
                c.*,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM contractors c
            LEFT JOIN organizations o ON o.organization_id = c.organization_id
            WHERE c.nip = ?
        """
        if organization_id is not None:
            query += " AND c.organization_id = ?"
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
                INSERT INTO contractors (
                    organization_id, name, nip, email, phone, is_new, last_invoice_date,
                    last_invoice_number, invoice_count, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.get("organization_id"),
                    payload["name"],
                    payload["nip"],
                    payload.get("email"),
                    payload.get("phone"),
                    int(payload.get("is_new", 1)),
                    payload.get("last_invoice_date"),
                    payload.get("last_invoice_number"),
                    int(payload.get("invoice_count", 0)),
                    payload.get("notes"),
                    timestamp,
                    timestamp,
                ),
                "contractor_id",
            )

    def update(self, contractor_id: int, fields: dict[str, Any]) -> None:
        if not fields:
            return
        allowed = {
            "organization_id",
            "name",
            "nip",
            "email",
            "phone",
            "is_new",
            "last_invoice_date",
            "last_invoice_number",
            "invoice_count",
            "notes",
        }
        update_fields = {key: value for key, value in fields.items() if key in allowed}
        if not update_fields:
            return
        update_fields["updated_at"] = now_iso()
        assignments = ", ".join(f"{key} = ?" for key in update_fields)
        values = list(update_fields.values()) + [contractor_id]
        with get_connection() as connection:
            connection.execute(
                f"UPDATE contractors SET {assignments} WHERE contractor_id = ?",
                values,
            )

    def add_note(self, payload: dict[str, Any]) -> int:
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO contractor_notes (
                    organization_id, contractor_id, author_user_id, note_text, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    payload["organization_id"],
                    payload["contractor_id"],
                    payload["author_user_id"],
                    payload["note_text"],
                    now_iso(),
                ),
                "contractor_note_id",
            )

    def list_notes(self, contractor_id: int, organization_id: int | None = None) -> list[dict[str, Any]]:
        params: list[Any] = [contractor_id]
        query = """
            SELECT
                n.*,
                COALESCE(u.display_name, u.login) AS author_user_name,
                u.role AS author_user_role
            FROM contractor_notes n
            LEFT JOIN users u ON u.user_id = n.author_user_id
            WHERE n.contractor_id = ?
        """
        if organization_id is not None:
            query += " AND n.organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY n.created_at ASC, n.contractor_note_id ASC"
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def refresh_invoice_stats(self, contractor_id: int) -> None:
        with get_connection() as connection:
            stats = connection.execute(
                """
                SELECT
                    COUNT(*) AS invoice_count,
                    MAX(issue_date) AS last_invoice_date
                FROM invoices
                WHERE contractor_id = ?
                """,
                (contractor_id,),
            ).fetchone()
            last_number_row = connection.execute(
                """
                SELECT invoice_number
                FROM invoices
                WHERE contractor_id = ?
                ORDER BY issue_date DESC, created_at DESC
                LIMIT 1
                """,
                (contractor_id,),
            ).fetchone()
            connection.execute(
                """
                UPDATE contractors
                SET invoice_count = ?,
                    last_invoice_date = ?,
                    last_invoice_number = ?,
                    is_new = CASE WHEN ? > 1 THEN 0 ELSE is_new END,
                    updated_at = ?
                WHERE contractor_id = ?
                """,
                (
                    int(stats["invoice_count"]) if stats else 0,
                    stats["last_invoice_date"] if stats else None,
                    last_number_row["invoice_number"] if last_number_row else None,
                    int(stats["invoice_count"]) if stats else 0,
                    now_iso(),
                    contractor_id,
                ),
            )

    def search_contractors(
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
        params: list[Any] = [value, value, value, value, value, value, value]
        query = """
            SELECT
                c.*,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM contractors c
            LEFT JOIN organizations o ON o.organization_id = c.organization_id
            WHERE (
                LOWER(COALESCE(c.name, '')) LIKE ?
                OR LOWER(COALESCE(c.nip, '')) LIKE ?
                OR LOWER(COALESCE(c.email, '')) LIKE ?
                OR LOWER(COALESCE(c.phone, '')) LIKE ?
                OR LOWER(COALESCE(c.notes, '')) LIKE ?
                OR LOWER(COALESCE(c.last_invoice_number, '')) LIKE ?
                OR LOWER(COALESCE(o.name, '')) LIKE ?
            )
              AND COALESCE(o.is_active, 1) = 1
        """
        if organization_id is not None:
            query += " AND c.organization_id = ?"
            params.append(organization_id)
        query += """
            ORDER BY c.is_new DESC, c.updated_at DESC, c.contractor_id DESC
            LIMIT ?
        """
        params.append(limit)

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]
