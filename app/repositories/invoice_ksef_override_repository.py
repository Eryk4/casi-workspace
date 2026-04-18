from __future__ import annotations

from typing import Any

from app.db import execute_insert_returning_id, get_connection
from app.utils import now_iso


class InvoiceKSeFOverrideRepository:
    def create(self, payload: dict[str, Any]) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO invoice_ksef_field_overrides (
                    organization_id,
                    invoice_id,
                    approval_request_id,
                    field_name,
                    source_value,
                    local_value,
                    status,
                    requested_by_user_id,
                    approved_by_user_id,
                    rejected_by_user_id,
                    request_reason,
                    decision_reason,
                    created_at,
                    updated_at,
                    approved_at,
                    rejected_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["organization_id"],
                    payload["invoice_id"],
                    payload.get("approval_request_id"),
                    payload["field_name"],
                    payload.get("source_value"),
                    payload.get("local_value"),
                    payload.get("status") or "pending",
                    payload.get("requested_by_user_id"),
                    payload.get("approved_by_user_id"),
                    payload.get("rejected_by_user_id"),
                    payload.get("request_reason"),
                    payload.get("decision_reason"),
                    payload.get("created_at") or timestamp,
                    timestamp,
                    payload.get("approved_at"),
                    payload.get("rejected_at"),
                ),
                "invoice_ksef_field_override_id",
            )

    def update(self, override_id: int, fields: dict[str, Any]) -> None:
        if not fields:
            return
        allowed = {
            "approval_request_id",
            "source_value",
            "local_value",
            "status",
            "approved_by_user_id",
            "rejected_by_user_id",
            "request_reason",
            "decision_reason",
            "approved_at",
            "rejected_at",
        }
        update_fields = {key: value for key, value in fields.items() if key in allowed}
        if not update_fields:
            return
        update_fields["updated_at"] = now_iso()
        assignments = ", ".join(f"{key} = ?" for key in update_fields)
        values = list(update_fields.values()) + [override_id]
        with get_connection() as connection:
            connection.execute(
                f"""
                UPDATE invoice_ksef_field_overrides
                SET {assignments}
                WHERE invoice_ksef_field_override_id = ?
                """,
                values,
            )

    def list_for_invoice(
        self,
        invoice_id: int,
        *,
        organization_id: int | None = None,
        statuses: list[str] | tuple[str, ...] | None = None,
    ) -> list[dict[str, Any]]:
        params: list[Any] = [invoice_id]
        query = """
            SELECT
                o.*,
                COALESCE(requested_by.display_name, requested_by.login) AS requested_by_user_name,
                COALESCE(approved_by.display_name, approved_by.login) AS approved_by_user_name,
                COALESCE(rejected_by.display_name, rejected_by.login) AS rejected_by_user_name
            FROM invoice_ksef_field_overrides o
            LEFT JOIN users requested_by ON requested_by.user_id = o.requested_by_user_id
            LEFT JOIN users approved_by ON approved_by.user_id = o.approved_by_user_id
            LEFT JOIN users rejected_by ON rejected_by.user_id = o.rejected_by_user_id
            WHERE o.invoice_id = ?
        """
        if organization_id is not None:
            query += " AND o.organization_id = ?"
            params.append(organization_id)
        if statuses:
            placeholders = ", ".join("?" for _ in statuses)
            query += f" AND o.status IN ({placeholders})"
            params.extend(list(statuses))
        query += """
            ORDER BY o.created_at DESC, o.invoice_ksef_field_override_id DESC
        """
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def list_for_approval_request(
        self,
        approval_request_id: int,
        *,
        organization_id: int | None = None,
    ) -> list[dict[str, Any]]:
        params: list[Any] = [approval_request_id]
        query = """
            SELECT *
            FROM invoice_ksef_field_overrides
            WHERE approval_request_id = ?
        """
        if organization_id is not None:
            query += " AND organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY field_name ASC, invoice_ksef_field_override_id ASC"
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]
