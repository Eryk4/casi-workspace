from __future__ import annotations

from typing import Any

from app.db import execute_insert_returning_id, get_connection
from app.utils import now_iso


class EntityAttachmentRepository:
    def create_attachment(self, payload: dict[str, Any]) -> int:
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO entity_attachments (
                    organization_id, entity_type, entity_id, file_name, mime_type, file_size, file_link,
                    file_storage_key, storage_backend, uploaded_by_user_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["organization_id"],
                    payload["entity_type"],
                    payload["entity_id"],
                    payload["file_name"],
                    payload.get("mime_type"),
                    int(payload.get("file_size") or 0),
                    payload["file_link"],
                    payload["file_storage_key"],
                    payload.get("storage_backend") or "lokalny",
                    payload.get("uploaded_by_user_id"),
                    now_iso(),
                ),
                "entity_attachment_id",
            )

    def list_attachments(
        self,
        entity_type: str,
        entity_id: int,
        *,
        organization_id: int | None = None,
    ) -> list[dict[str, Any]]:
        params: list[Any] = [entity_type, entity_id]
        query = """
            SELECT
                a.*,
                COALESCE(u.display_name, u.login) AS uploaded_by_user_name
            FROM entity_attachments a
            LEFT JOIN users u ON u.user_id = a.uploaded_by_user_id
            WHERE a.entity_type = ?
              AND a.entity_id = ?
        """
        if organization_id is not None:
            query += " AND a.organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY a.created_at DESC, a.entity_attachment_id DESC"
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

