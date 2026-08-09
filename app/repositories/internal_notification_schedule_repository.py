from __future__ import annotations

from typing import Any

from app.db import get_connection, get_read_only_connection


class InternalNotificationScheduleRepository:
    def get_operations_snapshot(
        self,
        *,
        organization_id: int,
        recipient_user_id: int,
        source_type: str,
    ) -> dict[str, Any] | None:
        """Return one bounded, read-only operational snapshot without loading run history."""
        with get_read_only_connection() as connection:
            row = connection.execute(
                """
                WITH scoped_schedule AS (
                    SELECT *
                    FROM internal_notification_schedules
                    WHERE organization_id = ?
                      AND recipient_user_id = ?
                      AND source_type = ?
                ),
                latest_run AS (
                    SELECT run.*
                    FROM internal_notification_schedule_runs run
                    WHERE run.schedule_id = (
                        SELECT internal_notification_schedule_id FROM scoped_schedule
                    )
                    ORDER BY run.created_at DESC, run.internal_notification_schedule_run_id DESC
                    LIMIT 1
                ),
                latest_terminal_run AS (
                    SELECT run.*
                    FROM internal_notification_schedule_runs run
                    WHERE run.schedule_id = (
                        SELECT internal_notification_schedule_id FROM scoped_schedule
                    )
                      AND run.status IN ('succeeded', 'failed')
                    ORDER BY run.created_at DESC, run.internal_notification_schedule_run_id DESC
                    LIMIT 1
                ),
                recent_runs AS (
                    SELECT run.status
                    FROM internal_notification_schedule_runs run
                    WHERE run.schedule_id = (
                        SELECT internal_notification_schedule_id FROM scoped_schedule
                    )
                    ORDER BY run.created_at DESC, run.internal_notification_schedule_run_id DESC
                    LIMIT 20
                )
                SELECT
                    schedule.*,
                    latest.internal_notification_schedule_run_id AS latest_run_id,
                    latest.status AS latest_run_status,
                    latest.attempt_count AS latest_attempt_count,
                    latest.candidates_count AS latest_candidates_count,
                    latest.created_count AS latest_created_count,
                    latest.existing_count AS latest_existing_count,
                    latest.error_code AS latest_error_code,
                    latest.error_summary AS latest_error_summary,
                    latest.scheduled_for_utc AS latest_scheduled_for_utc,
                    latest.started_at AS latest_started_at,
                    latest.finished_at AS latest_finished_at,
                    latest.created_at AS latest_created_at,
                    terminal.internal_notification_schedule_run_id AS terminal_run_id,
                    terminal.status AS terminal_run_status,
                    terminal.error_code AS terminal_error_code,
                    terminal.error_summary AS terminal_error_summary,
                    terminal.finished_at AS terminal_finished_at,
                    (SELECT COUNT(*) FROM recent_runs WHERE status = 'failed') AS recent_failure_count
                FROM scoped_schedule schedule
                LEFT JOIN latest_run latest ON 1 = 1
                LEFT JOIN latest_terminal_run terminal ON 1 = 1
                """,
                (organization_id, recipient_user_id, source_type),
            ).fetchone()
        return dict(row) if row else None

    def get_schedule(
        self,
        *,
        organization_id: int,
        recipient_user_id: int,
        source_type: str,
    ) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM internal_notification_schedules
                WHERE organization_id = ?
                  AND recipient_user_id = ?
                  AND source_type = ?
                """,
                (organization_id, recipient_user_id, source_type),
            ).fetchone()
        return dict(row) if row else None

    def get_schedule_by_id(self, schedule_id: int) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT * FROM internal_notification_schedules WHERE internal_notification_schedule_id = ?",
                (schedule_id,),
            ).fetchone()
        return dict(row) if row else None

    def upsert_schedule(self, payload: dict[str, Any]) -> dict[str, Any]:
        with get_connection() as connection:
            row = connection.execute(
                """
                INSERT INTO internal_notification_schedules (
                    organization_id, recipient_user_id, source_type, enabled, cadence,
                    timezone_name, local_time, next_run_at_utc, created_by_user_id,
                    updated_by_user_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(organization_id, recipient_user_id, source_type) DO UPDATE SET
                    enabled = excluded.enabled,
                    cadence = excluded.cadence,
                    timezone_name = excluded.timezone_name,
                    local_time = excluded.local_time,
                    next_run_at_utc = excluded.next_run_at_utc,
                    updated_by_user_id = excluded.updated_by_user_id,
                    updated_at = excluded.updated_at
                RETURNING *
                """,
                (
                    payload["organization_id"],
                    payload["recipient_user_id"],
                    payload["source_type"],
                    1 if payload["enabled"] else 0,
                    payload["cadence"],
                    payload["timezone_name"],
                    payload["local_time"],
                    payload.get("next_run_at_utc"),
                    payload["created_by_user_id"],
                    payload["updated_by_user_id"],
                    payload["created_at"],
                    payload["updated_at"],
                ),
            ).fetchone()
        if not row:
            raise RuntimeError("Nie udalo sie zapisac harmonogramu powiadomien.")
        return dict(row)

    def last_succeeded_local_date(self, schedule_id: int) -> str | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT scheduled_local_date
                FROM internal_notification_schedule_runs
                WHERE schedule_id = ? AND status = 'succeeded'
                ORDER BY scheduled_local_date DESC
                LIMIT 1
                """,
                (schedule_id,),
            ).fetchone()
        return str(row["scheduled_local_date"]) if row else None

    def list_due_schedules(self, *, now_utc: str, limit: int = 100) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM internal_notification_schedules
                WHERE enabled = 1
                  AND next_run_at_utc IS NOT NULL
                  AND next_run_at_utc <= ?
                ORDER BY next_run_at_utc ASC, internal_notification_schedule_id ASC
                LIMIT ?
                """,
                (now_utc, max(1, min(int(limit), 500))),
            ).fetchall()
        return [dict(row) for row in rows]

    def count_due_schedules_read_only(self, *, now_utc: str) -> int:
        with get_read_only_connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM internal_notification_schedules
                WHERE enabled = 1
                  AND next_run_at_utc IS NOT NULL
                  AND next_run_at_utc <= ?
                """,
                (now_utc,),
            ).fetchone()
        return int(row["count"])

    def ensure_run(self, payload: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        with get_connection() as connection:
            inserted = connection.execute(
                """
                INSERT INTO internal_notification_schedule_runs (
                    schedule_id, organization_id, recipient_user_id, source_type,
                    scheduled_local_date, as_of_date, scheduled_for_utc, status,
                    attempt_count, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', 0, ?)
                ON CONFLICT(schedule_id, scheduled_local_date) DO NOTHING
                RETURNING *
                """,
                (
                    payload["schedule_id"],
                    payload["organization_id"],
                    payload["recipient_user_id"],
                    payload["source_type"],
                    payload["scheduled_local_date"],
                    payload["as_of_date"],
                    payload["scheduled_for_utc"],
                    payload["created_at"],
                ),
            ).fetchone()
            if inserted:
                return dict(inserted), True
            existing = connection.execute(
                """
                SELECT * FROM internal_notification_schedule_runs
                WHERE schedule_id = ? AND scheduled_local_date = ?
                """,
                (payload["schedule_id"], payload["scheduled_local_date"]),
            ).fetchone()
        if not existing:
            raise RuntimeError("Nie udalo sie odczytac logicznego runu harmonogramu.")
        return dict(existing), False

    def claim_run(
        self,
        *,
        run_id: int,
        lease_token: str,
        now_utc: str,
        lease_expires_at_utc: str,
        max_attempts: int,
    ) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                UPDATE internal_notification_schedule_runs
                SET status = 'running',
                    attempt_count = attempt_count + 1,
                    lease_token = ?,
                    lease_expires_at_utc = ?,
                    next_attempt_at_utc = NULL,
                    started_at = ?,
                    finished_at = NULL,
                    error_code = NULL,
                    error_summary = NULL
                WHERE internal_notification_schedule_run_id = ?
                  AND attempt_count < ?
                  AND EXISTS (
                      SELECT 1
                      FROM internal_notification_schedules schedule
                      WHERE schedule.internal_notification_schedule_id = internal_notification_schedule_runs.schedule_id
                        AND schedule.enabled = 1
                        AND schedule.next_run_at_utc IS NOT NULL
                        AND schedule.next_run_at_utc <= ?
                  )
                  AND (
                      status = 'pending'
                      OR (status = 'failed' AND next_attempt_at_utc IS NOT NULL AND next_attempt_at_utc <= ?)
                      OR (status = 'running' AND lease_expires_at_utc IS NOT NULL AND lease_expires_at_utc <= ?)
                  )
                RETURNING *
                """,
                (
                    lease_token,
                    lease_expires_at_utc,
                    now_utc,
                    run_id,
                    max_attempts,
                    now_utc,
                    now_utc,
                    now_utc,
                ),
            ).fetchone()
        return dict(row) if row else None

    def mark_succeeded(
        self,
        *,
        run_id: int,
        lease_token: str,
        counts: dict[str, int],
        finished_at: str,
        next_run_at_utc: str,
    ) -> bool:
        with get_connection() as connection:
            updated = connection.execute(
                """
                UPDATE internal_notification_schedule_runs
                SET status = 'succeeded',
                    candidates_count = ?,
                    created_count = ?,
                    existing_count = ?,
                    lease_token = NULL,
                    lease_expires_at_utc = NULL,
                    next_attempt_at_utc = NULL,
                    error_code = NULL,
                    error_summary = NULL,
                    finished_at = ?
                WHERE internal_notification_schedule_run_id = ?
                  AND status = 'running'
                  AND lease_token = ?
                """,
                (
                    counts["candidates_count"],
                    counts["created_count"],
                    counts["existing_count"],
                    finished_at,
                    run_id,
                    lease_token,
                ),
            )
            if not updated.rowcount:
                return False
            connection.execute(
                """
                UPDATE internal_notification_schedules
                SET next_run_at_utc = CASE WHEN enabled = 1 THEN ? ELSE NULL END,
                    updated_at = ?
                WHERE internal_notification_schedule_id = (
                    SELECT schedule_id FROM internal_notification_schedule_runs
                    WHERE internal_notification_schedule_run_id = ?
                )
                """,
                (next_run_at_utc, finished_at, run_id),
            )
            return True

    def mark_failed(
        self,
        *,
        run_id: int,
        lease_token: str,
        error_code: str,
        error_summary: str,
        finished_at: str,
        next_attempt_at_utc: str | None,
        next_run_at_utc: str | None,
    ) -> bool:
        with get_connection() as connection:
            updated = connection.execute(
                """
                UPDATE internal_notification_schedule_runs
                SET status = 'failed',
                    lease_token = NULL,
                    lease_expires_at_utc = NULL,
                    next_attempt_at_utc = ?,
                    error_code = ?,
                    error_summary = ?,
                    finished_at = ?
                WHERE internal_notification_schedule_run_id = ?
                  AND status = 'running'
                  AND lease_token = ?
                """,
                (next_attempt_at_utc, error_code, error_summary, finished_at, run_id, lease_token),
            )
            if not updated.rowcount:
                return False
            if next_run_at_utc is not None:
                connection.execute(
                    """
                    UPDATE internal_notification_schedules
                    SET next_run_at_utc = CASE WHEN enabled = 1 THEN ? ELSE NULL END,
                        updated_at = ?
                    WHERE internal_notification_schedule_id = (
                        SELECT schedule_id FROM internal_notification_schedule_runs
                        WHERE internal_notification_schedule_run_id = ?
                    )
                    """,
                    (next_run_at_utc, finished_at, run_id),
                )
            return True

    def advance_schedule(self, *, schedule_id: int, next_run_at_utc: str, updated_at: str) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE internal_notification_schedules
                SET next_run_at_utc = CASE WHEN enabled = 1 THEN ? ELSE NULL END,
                    updated_at = ?
                WHERE internal_notification_schedule_id = ?
                """,
                (next_run_at_utc, updated_at, schedule_id),
            )

    def list_runs(self, *, schedule_id: int, limit: int = 20) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM internal_notification_schedule_runs
                WHERE schedule_id = ?
                ORDER BY created_at DESC, internal_notification_schedule_run_id DESC
                LIMIT ?
                """,
                (schedule_id, max(1, min(int(limit), 50))),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_runs_read_only(self, *, schedule_id: int, limit: int = 20) -> list[dict[str, Any]]:
        with get_read_only_connection() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM internal_notification_schedule_runs
                WHERE schedule_id = ?
                ORDER BY created_at DESC, internal_notification_schedule_run_id DESC
                LIMIT ?
                """,
                (schedule_id, max(1, min(int(limit), 50))),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_run(self, run_id: int) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT * FROM internal_notification_schedule_runs WHERE internal_notification_schedule_run_id = ?",
                (run_id,),
            ).fetchone()
        return dict(row) if row else None
