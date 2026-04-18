from __future__ import annotations

from typing import Any

from app.db import execute_insert_returning_id, get_connection


class WhiteboardRepository:
    def get_event_by_id(self, organization_id: int, whiteboard_event_id: int) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM organization_whiteboard_events
                WHERE organization_id = ?
                  AND whiteboard_event_id = ?
                LIMIT 1
                """,
                (organization_id, whiteboard_event_id),
            ).fetchone()
        return dict(row) if row else None

    def list_events(
        self,
        organization_id: int,
        *,
        after_event_id: int | None = None,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT *
            FROM organization_whiteboard_events
            WHERE organization_id = ?
        """
        params: list[Any] = [organization_id]
        if after_event_id is not None:
            query += " AND whiteboard_event_id > ?"
            params.append(after_event_id)
        query += " ORDER BY whiteboard_event_id ASC"

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_latest_event(self, organization_id: int) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM organization_whiteboard_events
                WHERE organization_id = ?
                ORDER BY whiteboard_event_id DESC
                LIMIT 1
                """,
                (organization_id,),
            ).fetchone()
        return dict(row) if row else None

    def get_latest_clear_event(self, organization_id: int) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM organization_whiteboard_events
                WHERE organization_id = ?
                  AND event_type = 'clear'
                ORDER BY whiteboard_event_id DESC
                LIMIT 1
                """,
                (organization_id,),
            ).fetchone()
        return dict(row) if row else None

    def create_event(
        self,
        *,
        organization_id: int,
        event_type: str,
        payload_json: str,
        actor_label: str,
        created_at: str,
        created_by_user_id: int | None = None,
    ) -> int:
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO organization_whiteboard_events (
                    organization_id,
                    event_type,
                    payload_json,
                    created_by_user_id,
                    actor_label,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    organization_id,
                    event_type,
                    payload_json,
                    created_by_user_id,
                    actor_label,
                    created_at,
                ),
                "whiteboard_event_id",
            )
