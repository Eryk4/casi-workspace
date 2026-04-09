from __future__ import annotations

from typing import Any

from app.db import execute_insert_returning_id, get_connection
from app.utils import now_iso


SORTABLE_COLUMNS = {
    "id": "i.id",
    "incoming_date": "i.incoming_date",
    "source": "i.source",
    "invoice_number": "i.invoice_number",
    "ksef_number": "i.ksef_number",
    "issuer_nip": "i.issuer_nip",
    "issuer_name": "i.issuer_name",
    "issue_date": "i.issue_date",
    "gross_amount": "i.gross_amount",
    "status": "i.status",
    "duplicate_type": "i.duplicate_type",
    "created_at": "i.created_at",
    "updated_at": "i.updated_at",
}


class InvoiceRepository:
    def list_invoices(self, filters: dict[str, Any] | None = None, organization_id: int | None = None) -> list[dict[str, Any]]:
        filters = filters or {}
        params: list[Any] = []
        conditions = []

        if organization_id is not None:
            conditions.append("i.organization_id = ?")
            params.append(organization_id)

        search = (filters.get("search") or "").strip()
        if search:
            search_value = f"%{search}%"
            conditions.append(
                """
                (
                    CAST(i.id AS TEXT) LIKE ?
                    OR COALESCE(i.file_name, '') LIKE ?
                    OR COALESCE(i.invoice_number, '') LIKE ?
                    OR COALESCE(i.ksef_number, '') LIKE ?
                    OR COALESCE(i.issuer_nip, '') LIKE ?
                    OR COALESCE(i.issuer_name, '') LIKE ?
                    OR COALESCE(c.name, '') LIKE ?
                )
                """
            )
            params.extend([search_value] * 7)

        for key, column in {
            "source": "i.source",
            "status": "i.status",
            "duplicate_type": "i.duplicate_type",
            "contractor_id": "i.contractor_id",
            "nip": "i.issuer_nip",
            "invoice_number": "i.invoice_number",
            "ksef_number": "i.ksef_number",
        }.items():
            value = (filters.get(key) or "").strip() if isinstance(filters.get(key), str) else filters.get(key)
            if value not in (None, ""):
                conditions.append(f"{column} = ?")
                params.append(value)

        date_from = (filters.get("date_from") or "").strip()
        if date_from:
            conditions.append("i.incoming_date >= ?")
            params.append(date_from)

        date_to = (filters.get("date_to") or "").strip()
        if date_to:
            conditions.append("i.incoming_date <= ?")
            params.append(date_to)

        query = """
            SELECT
                i.*,
                c.name AS contractor_name,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM invoices i
            LEFT JOIN contractors c ON c.contractor_id = i.contractor_id
            LEFT JOIN organizations o ON o.organization_id = i.organization_id
        """
        conditions.append("COALESCE(o.is_active, 1) = 1")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        sort_by = SORTABLE_COLUMNS.get(filters.get("sort_by"), "i.incoming_date")
        sort_order = "ASC" if str(filters.get("sort_order", "desc")).lower() == "asc" else "DESC"
        query += f" ORDER BY {sort_by} {sort_order}, i.id DESC"

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_by_id(self, invoice_id: int, organization_id: int | None = None) -> dict[str, Any] | None:
        params: list[Any] = [invoice_id]
        query = """
            SELECT
                i.*,
                c.name AS contractor_name,
                c.nip AS contractor_nip,
                c.email AS contractor_email,
                c.phone AS contractor_phone,
                c.is_new AS contractor_is_new,
                c.notes AS contractor_notes,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM invoices i
            LEFT JOIN contractors c ON c.contractor_id = i.contractor_id
            LEFT JOIN organizations o ON o.organization_id = i.organization_id
            WHERE i.id = ?
              AND COALESCE(o.is_active, 1) = 1
        """
        if organization_id is not None:
            query += " AND i.organization_id = ?"
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
                INSERT INTO invoices (
                    organization_id, incoming_date, source, file_name, document_type, invoice_number, ksef_number,
                    issuer_nip, issuer_name, issue_date, sale_date, gross_amount,
                    currency, status, duplicate_type, flag_reason, contractor_id,
                    file_link, file_storage_key, ocr_link, ocr_storage_key, storage_backend, source_external_id,
                    source_sender_name, source_sender_id, source_metadata, invoice_hash, ocr_raw_text, ocr_confidence,
                    notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.get("organization_id"),
                    payload["incoming_date"],
                    payload["source"],
                    payload["file_name"],
                    payload.get("document_type"),
                    payload.get("invoice_number"),
                    payload.get("ksef_number"),
                    payload.get("issuer_nip"),
                    payload.get("issuer_name"),
                    payload.get("issue_date"),
                    payload.get("sale_date"),
                    payload.get("gross_amount"),
                    payload.get("currency", "PLN"),
                    payload["status"],
                    payload.get("duplicate_type", "brak"),
                    payload.get("flag_reason"),
                    payload.get("contractor_id"),
                    payload.get("file_link"),
                    payload.get("file_storage_key"),
                    payload.get("ocr_link"),
                    payload.get("ocr_storage_key"),
                    payload.get("storage_backend"),
                    payload.get("source_external_id"),
                    payload.get("source_sender_name"),
                    payload.get("source_sender_id"),
                    payload.get("source_metadata"),
                    payload["invoice_hash"],
                    payload.get("ocr_raw_text"),
                    payload.get("ocr_confidence"),
                    payload.get("notes"),
                    timestamp,
                    timestamp,
                ),
                "id",
            )

    def update(self, invoice_id: int, fields: dict[str, Any]) -> None:
        if not fields:
            return
        allowed = {
            "organization_id",
            "incoming_date",
            "source",
            "file_name",
            "document_type",
            "invoice_number",
            "ksef_number",
            "issuer_nip",
            "issuer_name",
            "issue_date",
            "sale_date",
            "gross_amount",
            "currency",
            "status",
            "duplicate_type",
            "flag_reason",
            "contractor_id",
            "file_link",
            "file_storage_key",
            "ocr_link",
            "ocr_storage_key",
            "storage_backend",
            "source_external_id",
            "source_sender_name",
            "source_sender_id",
            "source_metadata",
            "invoice_hash",
            "ocr_raw_text",
            "ocr_confidence",
            "notes",
        }
        update_fields = {key: value for key, value in fields.items() if key in allowed}
        if not update_fields:
            return
        update_fields["updated_at"] = now_iso()
        assignments = ", ".join(f"{key} = ?" for key in update_fields)
        values = list(update_fields.values()) + [invoice_id]
        with get_connection() as connection:
            connection.execute(
                f"UPDATE invoices SET {assignments} WHERE id = ?",
                values,
            )

    def delete_relations(self, invoice_id: int) -> None:
        with get_connection() as connection:
            connection.execute(
                "DELETE FROM invoice_relations WHERE invoice_id = ?",
                (invoice_id,),
            )

    def add_relation(self, invoice_id: int, related_invoice_id: int, relation_type: str, reason: str) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO invoice_relations (invoice_id, related_invoice_id, relation_type, reason, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (invoice_id, related_invoice_id, relation_type, reason, now_iso()),
            )

    def list_relations(self, invoice_id: int) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    r.*,
                    i2.invoice_number,
                    i2.ksef_number,
                    i2.issuer_nip,
                    i2.issue_date,
                    i2.gross_amount,
                    i2.status,
                    i2.source,
                    i2.file_name
                FROM invoice_relations r
                JOIN invoices i2 ON i2.id = r.related_invoice_id
                WHERE r.invoice_id = ?
                ORDER BY r.id ASC
                """,
                (invoice_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def find_exact_ksef_duplicates(
        self,
        ksef_number: str,
        exclude_invoice_id: int | None = None,
        organization_id: int | None = None,
    ) -> list[dict[str, Any]]:
        if not ksef_number:
            return []
        query = """
            SELECT i.*
            FROM invoices i
            LEFT JOIN organizations o ON o.organization_id = i.organization_id
            WHERE i.ksef_number = ?
              AND COALESCE(o.is_active, 1) = 1
        """
        params: list[Any] = [ksef_number]
        if organization_id is not None:
            query += " AND i.organization_id = ?"
            params.append(organization_id)
        if exclude_invoice_id:
            query += " AND i.id <> ?"
            params.append(exclude_invoice_id)
        query += " ORDER BY i.id ASC"
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def find_suspected_duplicates(
        self,
        invoice_number: str | None,
        issuer_nip: str | None,
        exclude_invoice_id: int | None = None,
        organization_id: int | None = None,
    ) -> list[dict[str, Any]]:
        if not invoice_number or not issuer_nip:
            return []
        query = """
            SELECT i.*
            FROM invoices i
            LEFT JOIN organizations o ON o.organization_id = i.organization_id
            WHERE i.invoice_number = ?
              AND i.issuer_nip = ?
              AND COALESCE(o.is_active, 1) = 1
        """
        params: list[Any] = [invoice_number, issuer_nip]
        if organization_id is not None:
            query += " AND i.organization_id = ?"
            params.append(organization_id)
        if exclude_invoice_id:
            query += " AND i.id <> ?"
            params.append(exclude_invoice_id)
        query += " ORDER BY i.id ASC"
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def count_all(self, organization_id: int | None = None) -> int:
        params: list[Any] = []
        query = """
            SELECT COUNT(*) AS total
            FROM invoices i
            LEFT JOIN organizations o ON o.organization_id = i.organization_id
            WHERE COALESCE(o.is_active, 1) = 1
        """
        if organization_id is not None:
            query += " AND i.organization_id = ?"
            params.append(organization_id)
        with get_connection() as connection:
            row = connection.execute(query, params).fetchone()
        return int(row["total"]) if row else 0

    def search_global(self, query_text: str, organization_id: int | None = None) -> dict[str, list[dict[str, Any]]]:
        value = f"%{query_text.strip()}%"
        invoice_params: list[Any] = [value, value, value, value, value]
        contractor_params: list[Any] = [value, value, value]
        invoice_query = """
            SELECT
                i.id,
                i.invoice_number,
                i.issuer_name,
                i.issuer_nip,
                i.status,
                i.source,
                o.name AS organization_name
            FROM invoices i
            LEFT JOIN organizations o ON o.organization_id = i.organization_id
            WHERE (
                CAST(i.id AS TEXT) LIKE ?
                OR COALESCE(i.invoice_number, '') LIKE ?
                OR COALESCE(i.ksef_number, '') LIKE ?
                OR COALESCE(i.issuer_name, '') LIKE ?
                OR COALESCE(i.issuer_nip, '') LIKE ?
            )
              AND COALESCE(o.is_active, 1) = 1
        """
        contractor_query = """
            SELECT
                c.contractor_id,
                c.name,
                c.nip,
                c.email,
                c.is_new,
                o.name AS organization_name
            FROM contractors c
            LEFT JOIN organizations o ON o.organization_id = c.organization_id
            WHERE (
                c.name LIKE ?
                OR c.nip LIKE ?
                OR COALESCE(c.email, '') LIKE ?
            )
        """
        if organization_id is not None:
            invoice_query += " AND i.organization_id = ?"
            invoice_params.append(organization_id)
            contractor_query += " AND c.organization_id = ?"
            contractor_params.append(organization_id)
        invoice_query += " ORDER BY i.updated_at DESC LIMIT 10"
        contractor_query += " ORDER BY c.updated_at DESC LIMIT 10"
        with get_connection() as connection:
            invoice_rows = connection.execute(invoice_query, invoice_params).fetchall()
            contractor_rows = connection.execute(contractor_query, contractor_params).fetchall()
        return {
            "invoices": [dict(row) for row in invoice_rows],
            "contractors": [dict(row) for row in contractor_rows],
        }
