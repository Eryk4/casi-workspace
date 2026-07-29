from __future__ import annotations

from typing import Any

from app.db import get_connection
from app.utils import now_iso


class InternalNotificationRepository:
    def create_notification(self, payload: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        with get_connection() as connection:
            row = connection.execute(
                """
                INSERT INTO internal_notifications (
                    organization_id, recipient_user_id, source_type, source_event_id,
                    reason_code, detected_on, planned_for, title_snapshot, target_type,
                    target_id, related_issue_key, target_label_snapshot,
                    internal_link_snapshot, dedupe_key, created_by_user_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT DO NOTHING
                RETURNING internal_notification_id
                """,
                (
                    payload["organization_id"],
                    payload["recipient_user_id"],
                    payload["source_type"],
                    payload["source_event_id"],
                    payload["reason_code"],
                    payload["detected_on"],
                    payload.get("planned_for"),
                    payload["title_snapshot"],
                    payload["target_type"],
                    payload.get("target_id"),
                    payload.get("related_issue_key"),
                    payload["target_label_snapshot"],
                    payload.get("internal_link_snapshot"),
                    payload["dedupe_key"],
                    payload.get("created_by_user_id"),
                    payload.get("created_at") or now_iso(),
                ),
            ).fetchone()
            created = row is not None
            if created:
                notification_id = int(row["internal_notification_id"])
                stored = connection.execute(
                    "SELECT * FROM internal_notifications WHERE internal_notification_id = ?",
                    (notification_id,),
                ).fetchone()
            else:
                stored = connection.execute(
                    "SELECT * FROM internal_notifications WHERE dedupe_key = ?",
                    (payload["dedupe_key"],),
                ).fetchone()
            if not stored:
                raise RuntimeError("Nie udalo sie odczytac zmaterializowanego powiadomienia.")
            return dict(stored), created

    def list_notifications(
        self,
        *,
        organization_id: int,
        recipient_user_id: int,
        filter_name: str,
        limit: int,
        cursor_created_at: str | None = None,
        cursor_notification_id: int | None = None,
    ) -> list[dict[str, Any]]:
        state_expression = """
            (
                SELECT state.action
                FROM internal_notification_state_events state
                WHERE state.notification_id = notification.internal_notification_id
                  AND state.organization_id = notification.organization_id
                  AND state.recipient_user_id = notification.recipient_user_id
                ORDER BY state.created_at DESC, state.internal_notification_state_event_id DESC
                LIMIT 1
            )
        """
        params: list[Any] = [organization_id, recipient_user_id]
        query = f"""
            SELECT
                notification.*,
                {state_expression} AS state_action,
                (
                    SELECT state.created_at
                    FROM internal_notification_state_events state
                    WHERE state.notification_id = notification.internal_notification_id
                      AND state.organization_id = notification.organization_id
                      AND state.recipient_user_id = notification.recipient_user_id
                    ORDER BY state.created_at DESC, state.internal_notification_state_event_id DESC
                    LIMIT 1
                ) AS state_changed_at
            FROM internal_notifications notification
            WHERE notification.organization_id = ?
              AND notification.recipient_user_id = ?
        """
        if filter_name == "inbox":
            query += f" AND COALESCE({state_expression}, 'unread') <> 'archived'"
        elif filter_name == "unread":
            query += f" AND COALESCE({state_expression}, 'unread') = 'unread'"
        elif filter_name == "archived":
            query += f" AND {state_expression} = 'archived'"
        if cursor_created_at is not None and cursor_notification_id is not None:
            query += """
              AND (
                  notification.created_at < ?
                  OR (
                      notification.created_at = ?
                      AND notification.internal_notification_id < ?
                  )
              )
            """
            params.extend([cursor_created_at, cursor_created_at, cursor_notification_id])
        query += " ORDER BY notification.created_at DESC, notification.internal_notification_id DESC LIMIT ?"
        params.append(limit)
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def count_unread(self, *, organization_id: int, recipient_user_id: int) -> int:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM internal_notifications notification
                WHERE notification.organization_id = ?
                  AND notification.recipient_user_id = ?
                  AND COALESCE(
                      (
                          SELECT state.action
                          FROM internal_notification_state_events state
                          WHERE state.notification_id = notification.internal_notification_id
                            AND state.organization_id = notification.organization_id
                            AND state.recipient_user_id = notification.recipient_user_id
                          ORDER BY state.created_at DESC, state.internal_notification_state_event_id DESC
                          LIMIT 1
                      ),
                      'unread'
                  ) = 'unread'
                """,
                (organization_id, recipient_user_id),
            ).fetchone()
        return int(row["count"] if row else 0)

    def get_notification(
        self,
        notification_id: int,
        *,
        organization_id: int,
        recipient_user_id: int,
    ) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT
                    notification.*,
                    (
                        SELECT state.action
                        FROM internal_notification_state_events state
                        WHERE state.notification_id = notification.internal_notification_id
                          AND state.organization_id = notification.organization_id
                          AND state.recipient_user_id = notification.recipient_user_id
                        ORDER BY state.created_at DESC, state.internal_notification_state_event_id DESC
                        LIMIT 1
                    ) AS state_action
                FROM internal_notifications notification
                WHERE notification.internal_notification_id = ?
                  AND notification.organization_id = ?
                  AND notification.recipient_user_id = ?
                """,
                (notification_id, organization_id, recipient_user_id),
            ).fetchone()
        return dict(row) if row else None

    def add_state_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        timestamp = payload.get("created_at") or now_iso()
        with get_connection() as connection:
            row = connection.execute(
                """
                INSERT INTO internal_notification_state_events (
                    notification_id, organization_id, recipient_user_id,
                    action, actor_user_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                RETURNING internal_notification_state_event_id
                """,
                (
                    payload["notification_id"],
                    payload["organization_id"],
                    payload["recipient_user_id"],
                    payload["action"],
                    payload["actor_user_id"],
                    timestamp,
                ),
            ).fetchone()
            event_id = int(row["internal_notification_state_event_id"])
            stored = connection.execute(
                """
                SELECT * FROM internal_notification_state_events
                WHERE internal_notification_state_event_id = ?
                """,
                (event_id,),
            ).fetchone()
        return dict(stored)

    def list_state_events(self, notification_id: int) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM internal_notification_state_events
                WHERE notification_id = ?
                ORDER BY created_at ASC, internal_notification_state_event_id ASC
                """,
                (notification_id,),
            ).fetchall()
        return [dict(row) for row in rows]
