from __future__ import annotations

from typing import Any

from app.db import execute_insert_returning_id, get_connection
from app.utils import now_iso


class ApprovalRepository:
    def list_requests(
        self,
        *,
        organization_id: int | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        params: list[Any] = []
        conditions = []
        if organization_id is not None:
            conditions.append("a.organization_id = ?")
            params.append(organization_id)
        if entity_type:
            conditions.append("a.entity_type = ?")
            params.append(entity_type)
        if entity_id is not None:
            conditions.append("a.entity_id = ?")
            params.append(entity_id)
        if status:
            conditions.append("a.status = ?")
            params.append(status)

        query = """
            SELECT
                a.*,
                COALESCE(requested_by.display_name, requested_by.login) AS requested_by_user_name,
                COALESCE(requested_user.display_name, requested_user.login) AS requested_user_name,
                COALESCE(decided_by.display_name, decided_by.login) AS decided_by_user_name
            FROM approval_requests a
            LEFT JOIN users requested_by ON requested_by.user_id = a.requested_by_user_id
            LEFT JOIN users requested_user ON requested_user.user_id = a.requested_user_id
            LEFT JOIN users decided_by ON decided_by.user_id = a.decided_by_user_id
        """
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY a.updated_at DESC, a.approval_request_id DESC LIMIT ?"
        params.append(limit)

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_by_id(self, approval_request_id: int, organization_id: int | None = None) -> dict[str, Any] | None:
        params: list[Any] = [approval_request_id]
        query = """
            SELECT
                a.*,
                COALESCE(requested_by.display_name, requested_by.login) AS requested_by_user_name,
                COALESCE(requested_user.display_name, requested_user.login) AS requested_user_name,
                COALESCE(decided_by.display_name, decided_by.login) AS decided_by_user_name
            FROM approval_requests a
            LEFT JOIN users requested_by ON requested_by.user_id = a.requested_by_user_id
            LEFT JOIN users requested_user ON requested_user.user_id = a.requested_user_id
            LEFT JOIN users decided_by ON decided_by.user_id = a.decided_by_user_id
            WHERE a.approval_request_id = ?
        """
        if organization_id is not None:
            query += " AND a.organization_id = ?"
            params.append(organization_id)
        with get_connection() as connection:
            row = connection.execute(query, params).fetchone()
        return dict(row) if row else None

    def list_for_entity(self, entity_type: str, entity_id: int, *, organization_id: int | None = None) -> list[dict[str, Any]]:
        return self.list_requests(
            organization_id=organization_id,
            entity_type=entity_type,
            entity_id=entity_id,
            limit=100,
        )

    def create(self, payload: dict[str, Any]) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO approval_requests (
                    organization_id, entity_type, entity_id, title, description, status, requested_by_user_id,
                    requested_user_id, approve_status, reject_status, metadata_json, requested_at, decided_by_user_id,
                    decided_at, decision_reason, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["organization_id"],
                    payload["entity_type"],
                    payload["entity_id"],
                    payload["title"],
                    payload.get("description"),
                    payload.get("status") or "pending",
                    payload["requested_by_user_id"],
                    payload.get("requested_user_id"),
                    payload.get("approve_status"),
                    payload.get("reject_status"),
                    payload.get("metadata_json"),
                    payload.get("requested_at") or timestamp,
                    payload.get("decided_by_user_id"),
                    payload.get("decided_at"),
                    payload.get("decision_reason"),
                    timestamp,
                    timestamp,
                ),
                "approval_request_id",
            )

    def update(self, approval_request_id: int, fields: dict[str, Any]) -> None:
        if not fields:
            return
        allowed = {
            "title",
            "description",
            "status",
            "requested_user_id",
            "approve_status",
            "reject_status",
            "metadata_json",
            "requested_at",
            "decided_by_user_id",
            "decided_at",
            "decision_reason",
        }
        update_fields = {key: value for key, value in fields.items() if key in allowed}
        if not update_fields:
            return
        update_fields["updated_at"] = now_iso()
        assignments = ", ".join(f"{key} = ?" for key in update_fields)
        values = list(update_fields.values()) + [approval_request_id]
        with get_connection() as connection:
            connection.execute(
                f"UPDATE approval_requests SET {assignments} WHERE approval_request_id = ?",
                values,
            )
