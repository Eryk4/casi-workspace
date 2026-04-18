from __future__ import annotations

from typing import Any

from app.db import execute_insert_returning_id, get_connection
from app.utils import json_dumps, now_iso


class InvoiceHandoffRepository:
    def create_batch(
        self,
        *,
        organization_id: int,
        batch_number: str,
        handoff_target: str | None,
        note: str | None,
        created_by_user_id: int | None,
        invoice_count: int = 0,
        status: str = "utworzona",
    ) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO invoice_handoff_batches (
                    organization_id,
                    batch_number,
                    status,
                    handoff_target,
                    note,
                    invoice_count,
                    exported_at,
                    exported_by_user_id,
                    export_format,
                    export_metadata,
                    created_by_user_id,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    organization_id,
                    batch_number,
                    status,
                    handoff_target,
                    note,
                    int(invoice_count),
                    None,
                    None,
                    None,
                    None,
                    created_by_user_id,
                    timestamp,
                    timestamp,
                ),
                "invoice_handoff_batch_id",
            )

    def add_batch_item(
        self,
        *,
        invoice_handoff_batch_id: int,
        invoice_id: int,
        organization_id: int,
        workflow_state_snapshot: str | None,
        status_snapshot: str | None,
        source_snapshot: str | None,
    ) -> int:
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO invoice_handoff_batch_items (
                    invoice_handoff_batch_id,
                    invoice_id,
                    organization_id,
                    workflow_state_snapshot,
                    status_snapshot,
                    source_snapshot,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    invoice_handoff_batch_id,
                    invoice_id,
                    organization_id,
                    workflow_state_snapshot,
                    status_snapshot,
                    source_snapshot,
                    now_iso(),
                ),
                "invoice_handoff_batch_item_id",
            )

    def update_batch(
        self,
        invoice_handoff_batch_id: int,
        fields: dict[str, Any],
    ) -> None:
        if not fields:
            return
        allowed = {
            "status",
            "handoff_target",
            "note",
            "invoice_count",
            "exported_at",
            "exported_by_user_id",
            "export_format",
            "export_metadata",
        }
        update_fields = {key: value for key, value in fields.items() if key in allowed}
        if not update_fields:
            return
        update_fields["updated_at"] = now_iso()
        assignments = ", ".join(f"{key} = ?" for key in update_fields)
        values = list(update_fields.values()) + [invoice_handoff_batch_id]
        with get_connection() as connection:
            connection.execute(
                f"UPDATE invoice_handoff_batches SET {assignments} WHERE invoice_handoff_batch_id = ?",
                values,
            )

    def mark_exported(
        self,
        invoice_handoff_batch_id: int,
        *,
        exported_by_user_id: int | None,
        export_format: str,
        export_metadata: dict[str, Any] | None = None,
    ) -> None:
        self.update_batch(
            invoice_handoff_batch_id,
            {
                "status": "wyeksportowana",
                "exported_at": now_iso(),
                "exported_by_user_id": exported_by_user_id,
                "export_format": export_format,
                "export_metadata": json_dumps(export_metadata or {}),
            },
        )

    def list_batches(
        self,
        *,
        organization_id: int | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        params: list[Any] = []
        query = """
            SELECT
                b.*,
                o.name AS organization_name,
                o.slug AS organization_slug,
                COALESCE(created_by.display_name, created_by.login) AS created_by_user_name,
                COALESCE(exported_by.display_name, exported_by.login) AS exported_by_user_name
            FROM invoice_handoff_batches b
            LEFT JOIN organizations o ON o.organization_id = b.organization_id
            LEFT JOIN users created_by ON created_by.user_id = b.created_by_user_id
            LEFT JOIN users exported_by ON exported_by.user_id = b.exported_by_user_id
        """
        if organization_id is not None:
            query += " WHERE b.organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY COALESCE(b.exported_at, b.created_at) DESC, b.invoice_handoff_batch_id DESC LIMIT ?"
        params.append(max(int(limit), 1))
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._deserialize_batch(dict(row)) for row in rows]

    def get_batch_detail(
        self,
        invoice_handoff_batch_id: int,
        *,
        organization_id: int | None = None,
    ) -> dict[str, Any] | None:
        params: list[Any] = [invoice_handoff_batch_id]
        query = """
            SELECT
                b.*,
                o.name AS organization_name,
                o.slug AS organization_slug,
                COALESCE(created_by.display_name, created_by.login) AS created_by_user_name,
                COALESCE(exported_by.display_name, exported_by.login) AS exported_by_user_name
            FROM invoice_handoff_batches b
            LEFT JOIN organizations o ON o.organization_id = b.organization_id
            LEFT JOIN users created_by ON created_by.user_id = b.created_by_user_id
            LEFT JOIN users exported_by ON exported_by.user_id = b.exported_by_user_id
            WHERE b.invoice_handoff_batch_id = ?
        """
        if organization_id is not None:
            query += " AND b.organization_id = ?"
            params.append(organization_id)
        with get_connection() as connection:
            row = connection.execute(query, params).fetchone()
        return self._deserialize_batch(dict(row)) if row else None

    def list_batch_items(
        self,
        invoice_handoff_batch_id: int,
        *,
        organization_id: int | None = None,
    ) -> list[dict[str, Any]]:
        params: list[Any] = [invoice_handoff_batch_id]
        query = """
            SELECT
                bi.*,
                i.file_name,
                i.invoice_number,
                i.ksef_number,
                i.issuer_nip,
                i.issuer_name,
                i.issue_date,
                i.sale_date,
                i.gross_amount,
                i.currency,
                i.status AS current_status,
                i.workflow_state AS current_workflow_state,
                i.handoff_target AS current_handoff_target,
                i.handed_off_at,
                i.closed_at,
                i.assigned_user_id,
                COALESCE(assignee.display_name, assignee.login) AS assigned_user_name
            FROM invoice_handoff_batch_items bi
            JOIN invoices i ON i.id = bi.invoice_id
            LEFT JOIN users assignee ON assignee.user_id = i.assigned_user_id
            WHERE bi.invoice_handoff_batch_id = ?
        """
        if organization_id is not None:
            query += " AND bi.organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY bi.invoice_handoff_batch_item_id ASC"
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def list_batches_for_invoice(
        self,
        invoice_id: int,
        *,
        organization_id: int | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        params: list[Any] = [invoice_id]
        query = """
            SELECT
                b.*,
                bi.invoice_handoff_batch_item_id,
                bi.workflow_state_snapshot,
                bi.status_snapshot,
                bi.source_snapshot,
                o.name AS organization_name,
                o.slug AS organization_slug,
                COALESCE(created_by.display_name, created_by.login) AS created_by_user_name,
                COALESCE(exported_by.display_name, exported_by.login) AS exported_by_user_name
            FROM invoice_handoff_batch_items bi
            JOIN invoice_handoff_batches b ON b.invoice_handoff_batch_id = bi.invoice_handoff_batch_id
            LEFT JOIN organizations o ON o.organization_id = b.organization_id
            LEFT JOIN users created_by ON created_by.user_id = b.created_by_user_id
            LEFT JOIN users exported_by ON exported_by.user_id = b.exported_by_user_id
            WHERE bi.invoice_id = ?
        """
        if organization_id is not None:
            query += " AND bi.organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY b.created_at DESC, b.invoice_handoff_batch_id DESC LIMIT ?"
        params.append(max(int(limit), 1))
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._deserialize_batch(dict(row)) for row in rows]

    def _deserialize_batch(self, row: dict[str, Any]) -> dict[str, Any]:
        export_metadata = row.get("export_metadata")
        if export_metadata:
            try:
                import json

                row["export_metadata"] = json.loads(str(export_metadata))
            except (TypeError, ValueError):
                row["export_metadata"] = {}
        else:
            row["export_metadata"] = {}
        return row
