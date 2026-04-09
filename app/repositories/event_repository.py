from __future__ import annotations

from typing import Any

from app.db import execute_insert_returning_id, get_connection
from app.utils import json_dumps, now_iso


class EventRepository:
    def log(
        self,
        *,
        event_type: str,
        invoice_id: int | None,
        organization_id: int | None,
        source: str | None,
        status_before: str | None,
        status_after: str | None,
        decision_reason: str | None,
        actor: str,
        details: dict[str, Any] | str | None = None,
    ) -> int:
        serialized_details = details if isinstance(details, str) else json_dumps(details or {})
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO event_logs (
                    event_time, event_type, invoice_id, organization_id, source, status_before, status_after,
                    decision_reason, actor, details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now_iso(),
                    event_type,
                    invoice_id,
                    organization_id,
                    source,
                    status_before,
                    status_after,
                    decision_reason,
                    actor,
                    serialized_details,
                ),
                "id",
            )

    def list_logs(self, limit: int = 200, organization_id: int | None = None) -> list[dict[str, Any]]:
        params: list[Any] = []
        query = """
            SELECT
                e.*,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM event_logs e
            LEFT JOIN organizations o ON o.organization_id = e.organization_id
        """
        if organization_id is not None:
            query += " WHERE e.organization_id = ?"
            params.append(organization_id)
        query += """
            ORDER BY e.event_time DESC, e.id DESC
            LIMIT ?
        """
        params.append(limit)
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def list_by_invoice(self, invoice_id: int, organization_id: int | None = None) -> list[dict[str, Any]]:
        params: list[Any] = [invoice_id]
        query = """
            SELECT
                e.*,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM event_logs e
            LEFT JOIN organizations o ON o.organization_id = e.organization_id
            WHERE e.invoice_id = ?
        """
        if organization_id is not None:
            query += " AND e.organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY e.event_time DESC, e.id DESC"
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]
