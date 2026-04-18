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

    def list_logs_after(
        self,
        last_event_id: int,
        *,
        organization_id: int | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        params: list[Any] = [last_event_id]
        query = """
            SELECT
                e.*,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM event_logs e
            LEFT JOIN organizations o ON o.organization_id = e.organization_id
            WHERE e.id > ?
        """
        if organization_id is not None:
            query += " AND e.organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY e.id ASC LIMIT ?"
        params.append(max(1, int(limit)))
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

    def list_knowledge_document_logs(
        self,
        knowledge_document_id: int,
        *,
        organization_id: int | None = None,
        limit: int = 25,
    ) -> list[dict[str, Any]]:
        document_id = int(knowledge_document_id)
        params: list[Any] = [
            f'%"knowledge_document_id": {document_id},%',
            f'%"knowledge_document_id": {document_id}\n%',
            f'%"knowledge_document_id": {document_id}\r\n%',
        ]
        query = """
            SELECT
                e.*,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM event_logs e
            LEFT JOIN organizations o ON o.organization_id = e.organization_id
            WHERE COALESCE(e.source, '') = 'WIEDZA'
              AND (
                COALESCE(e.details, '') LIKE ?
                OR COALESCE(e.details, '') LIKE ?
                OR COALESCE(e.details, '') LIKE ?
              )
        """
        if organization_id is not None:
            query += " AND e.organization_id = ?"
            params.append(organization_id)
        query += """
            ORDER BY e.event_time DESC, e.id DESC
            LIMIT ?
        """
        params.append(max(1, int(limit)))

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def list_knowledge_activity(
        self,
        *,
        organization_id: int,
        event_types: list[str],
        limit: int = 12,
    ) -> list[dict[str, Any]]:
        normalized_types = [str(item or "").strip() for item in event_types if str(item or "").strip()]
        if not normalized_types:
            return []
        placeholders = ", ".join("?" for _ in normalized_types)
        params: list[Any] = [organization_id, *normalized_types, max(1, int(limit))]
        query = f"""
            SELECT
                e.*,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM event_logs e
            LEFT JOIN organizations o ON o.organization_id = e.organization_id
            WHERE e.organization_id = ?
              AND COALESCE(e.source, '') = 'WIEDZA'
              AND e.event_type IN ({placeholders})
            ORDER BY e.event_time DESC, e.id DESC
            LIMIT ?
        """
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_module_inbox_state(
        self,
        *,
        user_id: int,
        organization_id: int,
        module_key: str,
    ) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM user_module_inbox_state
                WHERE user_id = ?
                  AND organization_id = ?
                  AND module_key = ?
                LIMIT 1
                """,
                (user_id, organization_id, str(module_key or "").strip()),
            ).fetchone()
        return dict(row) if row else None

    def mark_module_inbox_seen(
        self,
        *,
        user_id: int,
        organization_id: int,
        module_key: str,
        last_seen_event_id: int | None,
    ) -> dict[str, Any]:
        normalized_module_key = str(module_key or "").strip()
        timestamp = now_iso()
        existing = self.get_module_inbox_state(
            user_id=int(user_id),
            organization_id=int(organization_id),
            module_key=normalized_module_key,
        )
        with get_connection() as connection:
            if existing:
                connection.execute(
                    """
                    UPDATE user_module_inbox_state
                    SET last_seen_event_id = ?,
                        last_seen_at = ?,
                        updated_at = ?
                    WHERE user_module_inbox_state_id = ?
                    """,
                    (
                        last_seen_event_id,
                        timestamp,
                        timestamp,
                        existing["user_module_inbox_state_id"],
                    ),
                )
            else:
                execute_insert_returning_id(
                    connection,
                    """
                    INSERT INTO user_module_inbox_state (
                        user_id,
                        organization_id,
                        module_key,
                        last_seen_event_id,
                        last_seen_at,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        int(user_id),
                        int(organization_id),
                        normalized_module_key,
                        last_seen_event_id,
                        timestamp,
                        timestamp,
                    ),
                    "user_module_inbox_state_id",
                )
        state = self.get_module_inbox_state(
            user_id=int(user_id),
            organization_id=int(organization_id),
            module_key=normalized_module_key,
        )
        return state or {
            "user_id": int(user_id),
            "organization_id": int(organization_id),
            "module_key": normalized_module_key,
            "last_seen_event_id": last_seen_event_id,
            "last_seen_at": timestamp,
            "updated_at": timestamp,
        }

    def search_logs(
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
                e.*,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM event_logs e
            LEFT JOIN organizations o ON o.organization_id = e.organization_id
            WHERE (
                CAST(e.id AS TEXT) LIKE ?
                OR CAST(COALESCE(e.invoice_id, '') AS TEXT) LIKE ?
                OR LOWER(COALESCE(e.event_type, '')) LIKE ?
                OR LOWER(COALESCE(e.actor, '')) LIKE ?
                OR LOWER(COALESCE(e.decision_reason, '')) LIKE ?
                OR LOWER(COALESCE(e.details, '')) LIKE ?
                OR LOWER(COALESCE(o.name, '')) LIKE ?
            )
        """
        if organization_id is not None:
            query += " AND e.organization_id = ?"
            params.append(organization_id)
        query += """
            ORDER BY e.event_time DESC, e.id DESC
            LIMIT ?
        """
        params.append(limit)

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]
