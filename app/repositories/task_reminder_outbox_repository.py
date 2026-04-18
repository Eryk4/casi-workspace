from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.db import execute_insert_returning_id, get_connection
from app.utils import json_dumps, now_iso, now_local_datetime_value


class TaskReminderOutboxRepository:
    def upsert_delivery(self, payload: dict[str, Any], *, force_requeue: bool = False) -> dict[str, Any]:
        timestamp = now_iso()
        force_flag = 1 if force_requeue else 0
        values = (
            payload["organization_id"],
            payload["task_id"],
            payload["delivery_channel"],
            payload["delivery_key"],
            payload["delivery_anchor_at"],
            payload["recipient_user_id"],
            payload["recipient_telegram_user_id"],
            payload["available_at"],
            payload.get("status") or "queued",
            int(payload.get("retryable", 1) or 0),
            int(payload.get("attempt_count", 0) or 0),
            payload.get("claimed_at"),
            payload.get("claimed_by"),
            payload.get("last_attempt_at"),
            payload.get("last_error"),
            payload.get("sent_at"),
            payload.get("payload") or "{}",
            timestamp,
            timestamp,
        )
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO task_reminder_outbox (
                    organization_id, task_id, delivery_channel, delivery_key, delivery_anchor_at, recipient_user_id,
                    recipient_telegram_user_id, available_at, status, retryable, attempt_count, claimed_at, claimed_by,
                    last_attempt_at, last_error, sent_at, payload, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(task_id, delivery_channel, delivery_key) DO UPDATE SET
                    organization_id = excluded.organization_id,
                    task_id = excluded.task_id,
                    recipient_user_id = excluded.recipient_user_id,
                    recipient_telegram_user_id = excluded.recipient_telegram_user_id,
                    delivery_anchor_at = excluded.delivery_anchor_at,
                    available_at = CASE
                        WHEN task_reminder_outbox.status IN ('processing', 'sent') THEN task_reminder_outbox.available_at
                        WHEN task_reminder_outbox.status = 'failed' AND task_reminder_outbox.retryable = 0 AND ? = 0
                            THEN task_reminder_outbox.available_at
                        WHEN excluded.available_at < task_reminder_outbox.available_at THEN excluded.available_at
                        ELSE task_reminder_outbox.available_at
                    END,
                    retryable = CASE
                        WHEN task_reminder_outbox.status = 'failed' AND task_reminder_outbox.retryable = 0 AND ? = 0
                            THEN task_reminder_outbox.retryable
                        ELSE excluded.retryable
                    END,
                    status = CASE
                        WHEN task_reminder_outbox.status IN ('processing', 'sent') THEN task_reminder_outbox.status
                        WHEN task_reminder_outbox.status = 'failed' AND task_reminder_outbox.retryable = 0 AND ? = 0
                            THEN task_reminder_outbox.status
                        ELSE 'queued'
                    END,
                    payload = excluded.payload,
                    updated_at = excluded.updated_at
                """,
                (*values, force_flag, force_flag, force_flag),
            )
            row = connection.execute(
                """
                SELECT *
                FROM task_reminder_outbox
                WHERE task_id = ? AND delivery_channel = ? AND delivery_key = ?
                """,
                (
                    payload["task_id"],
                    payload["delivery_channel"],
                    payload["delivery_key"],
                ),
            ).fetchone()
        return dict(row) if row else dict(payload)

    def find_delivery_by_key(self, task_id: int, delivery_channel: str, delivery_key: str) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM task_reminder_outbox
                WHERE task_id = ? AND delivery_channel = ? AND delivery_key = ?
                """,
                (task_id, delivery_channel, delivery_key),
            ).fetchone()
        return dict(row) if row else None

    def claim_due_deliveries(
        self,
        *,
        limit: int,
        worker_name: str,
        processing_timeout_minutes: int,
        organization_id: int | None = None,
        viewer_user_id: int | None = None,
    ) -> list[dict[str, Any]]:
        now_value = now_local_datetime_value()
        stale_before = (
            datetime.strptime(now_value, "%Y-%m-%dT%H:%M") - timedelta(minutes=max(1, int(processing_timeout_minutes)))
        ).strftime("%Y-%m-%dT%H:%M")
        params: list[Any] = [now_value, stale_before]
        conditions = [
            """
            (
                (status = 'queued' AND COALESCE(available_at, '') <= ?)
                OR (status = 'processing' AND COALESCE(claimed_at, '') <= ?)
            )
            """
        ]
        if organization_id is not None:
            conditions.append("organization_id = ?")
            params.append(organization_id)
        if viewer_user_id is not None:
            conditions.append(
                """
                (
                    EXISTS (
                        SELECT 1
                        FROM tasks t
                        WHERE t.task_id = task_reminder_outbox.task_id
                          AND (
                              t.owner_user_id = ?
                              OR t.assigned_user_id = ?
                              OR EXISTS (
                                  SELECT 1
                                  FROM task_visibility_users tvu
                                  WHERE tvu.task_id = t.task_id
                                    AND tvu.user_id = ?
                              )
                          )
                    )
                )
                """
            )
            params.extend([viewer_user_id, viewer_user_id, viewer_user_id])

        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT *
                FROM task_reminder_outbox
                WHERE {' AND '.join(conditions)}
                ORDER BY
                    COALESCE(available_at, '') ASC,
                    attempt_count ASC,
                    task_reminder_outbox_id ASC
                LIMIT ?
                """,
                (*params, max(1, int(limit))),
            ).fetchall()
            claimed: list[dict[str, Any]] = []
            for row in rows:
                claim_time = now_value
                updated = connection.execute(
                    """
                    UPDATE task_reminder_outbox
                    SET status = 'processing',
                        claimed_at = ?,
                        claimed_by = ?,
                        attempt_count = attempt_count + 1,
                        last_attempt_at = ?,
                        updated_at = ?
                    WHERE task_reminder_outbox_id = ?
                      AND (
                          (status = 'queued' AND COALESCE(available_at, '') <= ?)
                          OR (status = 'processing' AND COALESCE(claimed_at, '') <= ?)
                      )
                    """,
                    (
                        claim_time,
                        worker_name,
                        claim_time,
                        claim_time,
                        row["task_reminder_outbox_id"],
                        now_value,
                        stale_before,
                    ),
                )
                if updated.rowcount:
                    refreshed = connection.execute(
                        """
                        SELECT *
                        FROM task_reminder_outbox
                        WHERE task_reminder_outbox_id = ?
                        """,
                        (row["task_reminder_outbox_id"],),
                    ).fetchone()
                    if refreshed:
                        claimed.append(dict(refreshed))
            return claimed

    def mark_sent(self, outbox_id: int, *, sent_at: str, worker_name: str) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE task_reminder_outbox
                SET status = 'sent',
                    sent_at = ?,
                    claimed_by = ?,
                    last_error = NULL,
                    updated_at = ?
                WHERE task_reminder_outbox_id = ?
                """,
                (sent_at, worker_name, sent_at, outbox_id),
            )

    def mark_retry(
        self,
        outbox_id: int,
        *,
        retry_at: str,
        error_message: str,
        worker_name: str,
    ) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE task_reminder_outbox
                SET status = 'queued',
                    available_at = ?,
                    last_error = ?,
                    claimed_at = NULL,
                    claimed_by = ?,
                    updated_at = ?
                WHERE task_reminder_outbox_id = ?
                """,
                (retry_at, error_message, worker_name, retry_at, outbox_id),
            )

    def mark_failed(
        self,
        outbox_id: int,
        *,
        failed_at: str,
        error_message: str,
        worker_name: str,
        retryable: bool,
    ) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE task_reminder_outbox
                SET status = 'failed',
                    retryable = ?,
                    last_error = ?,
                    claimed_at = NULL,
                    claimed_by = ?,
                    updated_at = ?
                WHERE task_reminder_outbox_id = ?
                """,
                (1 if retryable else 0, error_message, worker_name, failed_at, outbox_id),
            )

    def mark_cancelled(self, outbox_id: int, *, cancelled_at: str, reason: str, worker_name: str) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE task_reminder_outbox
                SET status = 'cancelled',
                    last_error = ?,
                    claimed_at = NULL,
                    claimed_by = ?,
                    updated_at = ?
                WHERE task_reminder_outbox_id = ?
                """,
                (reason, worker_name, cancelled_at, outbox_id),
            )

    def create_attempt(
        self,
        *,
        outbox_id: int,
        organization_id: int,
        task_id: int,
        delivery_channel: str,
        attempt_no: int,
        outcome: str,
        attempted_at: str,
        worker_name: str,
        error_message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> int:
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO task_reminder_outbox_attempts (
                    task_reminder_outbox_id, organization_id, task_id, delivery_channel, attempt_no, outcome,
                    attempted_at, worker_name, error_message, details, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    outbox_id,
                    organization_id,
                    task_id,
                    delivery_channel,
                    int(attempt_no),
                    outcome,
                    attempted_at,
                    worker_name,
                    error_message,
                    json_dumps(details or {}),
                    attempted_at,
                ),
                "task_reminder_outbox_attempt_id",
            )

    def count_statuses(self, *, organization_id: int | None = None) -> dict[str, int]:
        now_value = now_local_datetime_value()
        params: list[Any] = []
        conditions = []
        if organization_id is not None:
            conditions.append("organization_id = ?")
            params.append(organization_id)
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN status = 'queued' AND COALESCE(available_at, '') <= ? THEN 1 ELSE 0 END) AS due,
                    SUM(CASE WHEN status = 'queued' AND COALESCE(available_at, '') > ? THEN 1 ELSE 0 END) AS scheduled,
                    SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) AS processing,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed,
                    SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) AS sent,
                    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled
                FROM task_reminder_outbox
                {where_clause}
                """,
                (now_value, now_value, *params),
            ).fetchone()
        if not row:
            return {"total": 0, "due": 0, "scheduled": 0, "processing": 0, "failed": 0, "sent": 0, "cancelled": 0}
        return {
            "total": int(row["total"] or 0),
            "due": int(row["due"] or 0),
            "scheduled": int(row["scheduled"] or 0),
            "processing": int(row["processing"] or 0),
            "failed": int(row["failed"] or 0),
            "sent": int(row["sent"] or 0),
            "cancelled": int(row["cancelled"] or 0),
        }

    def list_deliveries(
        self,
        *,
        limit: int = 25,
        organization_id: int | None = None,
        viewer_user_id: int | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        params: list[Any] = []
        conditions = []
        if organization_id is not None:
            conditions.append("o.organization_id = ?")
            params.append(organization_id)
        if status:
            conditions.append("o.status = ?")
            params.append(status)
        if viewer_user_id is not None:
            conditions.append(
                """
                EXISTS (
                    SELECT 1
                    FROM tasks t
                    WHERE t.task_id = o.task_id
                      AND (
                          t.owner_user_id = ?
                          OR t.assigned_user_id = ?
                          OR EXISTS (
                              SELECT 1
                              FROM task_visibility_users tvu
                              WHERE tvu.task_id = t.task_id
                                AND tvu.user_id = ?
                          )
                      )
                )
                """
            )
            params.extend([viewer_user_id, viewer_user_id, viewer_user_id])

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    o.*,
                    t.title AS task_title,
                    t.task_type AS task_type,
                    t.status AS task_status,
                    t.priority AS task_priority,
                    t.due_at AS task_due_at,
                    t.remind_at AS task_remind_at,
                    COALESCE(owner.display_name, owner.login) AS owner_user_name,
                    COALESCE(assignee.display_name, assignee.login) AS assigned_user_name,
                    COALESCE(recipient.display_name, recipient.login) AS recipient_user_name
                FROM task_reminder_outbox o
                LEFT JOIN tasks t ON t.task_id = o.task_id
                LEFT JOIN users owner ON owner.user_id = t.owner_user_id
                LEFT JOIN users assignee ON assignee.user_id = t.assigned_user_id
                LEFT JOIN users recipient ON recipient.user_id = o.recipient_user_id
                {where_clause}
                ORDER BY
                    CASE o.status
                        WHEN 'processing' THEN 0
                        WHEN 'failed' THEN 1
                        WHEN 'queued' THEN 2
                        WHEN 'sent' THEN 3
                        ELSE 4
                    END,
                    COALESCE(o.available_at, '') ASC,
                    o.attempt_count DESC,
                    o.task_reminder_outbox_id DESC
                LIMIT ?
                """,
                (*params, max(1, int(limit))),
            ).fetchall()
        return [dict(row) for row in rows]

    def requeue_delivery(
        self,
        outbox_id: int,
        *,
        available_at: str,
        reason: str | None = None,
        organization_id: int | None = None,
        viewer_user_id: int | None = None,
    ) -> dict[str, Any] | None:
        params: list[Any] = [available_at, reason, available_at, outbox_id]
        conditions = ["task_reminder_outbox_id = ?", "status IN ('failed', 'cancelled', 'queued')"]
        if organization_id is not None:
            conditions.append("organization_id = ?")
            params.append(organization_id)
        if viewer_user_id is not None:
            conditions.append(
                """
                EXISTS (
                    SELECT 1
                    FROM tasks t
                    WHERE t.task_id = task_reminder_outbox.task_id
                      AND (
                          t.owner_user_id = ?
                          OR t.assigned_user_id = ?
                          OR EXISTS (
                              SELECT 1
                              FROM task_visibility_users tvu
                              WHERE tvu.task_id = t.task_id
                                AND tvu.user_id = ?
                          )
                      )
                )
                """
            )
            params.extend([viewer_user_id, viewer_user_id, viewer_user_id])
        with get_connection() as connection:
            connection.execute(
                f"""
                UPDATE task_reminder_outbox
                SET status = 'queued',
                    retryable = 1,
                    available_at = ?,
                    last_error = ?,
                    claimed_at = NULL,
                    claimed_by = NULL,
                    updated_at = ?
                WHERE {' AND '.join(conditions)}
                """,
                params,
            )
            row = connection.execute(
                """
                SELECT *
                FROM task_reminder_outbox
                WHERE task_reminder_outbox_id = ?
                """,
                (outbox_id,),
            ).fetchone()
        return dict(row) if row else None

    def upsert_worker_heartbeat(
        self,
        *,
        worker_name: str,
        worker_role: str,
        state: str,
        process_id: int | None = None,
        processed_total: int = 0,
        sent_total: int = 0,
        failed_total: int = 0,
        deferred_total: int = 0,
        retrying_total: int = 0,
        skipped_total: int = 0,
        queue_total: int = 0,
        queue_due: int = 0,
        queue_failed: int = 0,
        error_message: str | None = None,
    ) -> None:
        timestamp = now_local_datetime_value()
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO task_reminder_worker_heartbeats (
                    worker_name, worker_role, process_id, state, last_heartbeat_at, last_success_at, last_error_at,
                    last_error_message, cycles_completed, processed_total, sent_total, failed_total, deferred_total,
                    retrying_total, skipped_total, queue_total, queue_due, queue_failed, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(worker_name) DO UPDATE SET
                    worker_role = excluded.worker_role,
                    process_id = excluded.process_id,
                    state = excluded.state,
                    last_heartbeat_at = excluded.last_heartbeat_at,
                    last_success_at = CASE WHEN excluded.state = 'error' THEN task_reminder_worker_heartbeats.last_success_at ELSE excluded.last_heartbeat_at END,
                    last_error_at = CASE WHEN excluded.state = 'error' THEN excluded.last_heartbeat_at ELSE task_reminder_worker_heartbeats.last_error_at END,
                    last_error_message = CASE WHEN excluded.state = 'error' THEN excluded.last_error_message ELSE NULL END,
                    cycles_completed = task_reminder_worker_heartbeats.cycles_completed + 1,
                    processed_total = task_reminder_worker_heartbeats.processed_total + excluded.processed_total,
                    sent_total = task_reminder_worker_heartbeats.sent_total + excluded.sent_total,
                    failed_total = task_reminder_worker_heartbeats.failed_total + excluded.failed_total,
                    deferred_total = task_reminder_worker_heartbeats.deferred_total + excluded.deferred_total,
                    retrying_total = task_reminder_worker_heartbeats.retrying_total + excluded.retrying_total,
                    skipped_total = task_reminder_worker_heartbeats.skipped_total + excluded.skipped_total,
                    queue_total = excluded.queue_total,
                    queue_due = excluded.queue_due,
                    queue_failed = excluded.queue_failed,
                    updated_at = excluded.updated_at
                """,
                (
                    worker_name,
                    worker_role,
                    process_id,
                    state,
                    timestamp,
                    timestamp if state != "error" else None,
                    timestamp if state == "error" else None,
                    error_message,
                    1,
                    int(processed_total),
                    int(sent_total),
                    int(failed_total),
                    int(deferred_total),
                    int(retrying_total),
                    int(skipped_total),
                    int(queue_total),
                    int(queue_due),
                    int(queue_failed),
                    timestamp,
                    timestamp,
                ),
            )

    def list_worker_heartbeats(self) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM task_reminder_worker_heartbeats
                ORDER BY worker_role ASC, worker_name ASC
                """
            ).fetchall()
        return [dict(row) for row in rows]
