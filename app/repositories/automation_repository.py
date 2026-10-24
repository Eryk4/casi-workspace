from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from app.db import execute_insert_returning_id, get_connection, get_read_only_connection
from app.utils import now_iso


_ActivationResult = TypeVar("_ActivationResult")
AUTOMATION_ACTIVATION_SERIALIZATION_ATTEMPTS = 3


class AutomationRepository:
    def list_rules(self, organization_id: int | None = None, *, include_inactive: bool = False) -> list[dict[str, Any]]:
        params: list[Any] = []
        conditions = []
        if organization_id is not None:
            conditions.append("r.organization_id = ?")
            params.append(organization_id)
        if not include_inactive:
            conditions.append("COALESCE(r.is_active, 1) = 1")

        query = """
            SELECT
                r.*,
                COALESCE(u.display_name, u.login) AS created_by_user_name,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM automation_rules r
            LEFT JOIN users u ON u.user_id = r.created_by_user_id
            LEFT JOIN organizations o ON o.organization_id = r.organization_id
        """
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY r.is_active DESC, r.trigger_event_type ASC, r.rule_name ASC, r.automation_rule_id ASC"
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_by_id(self, automation_rule_id: int, organization_id: int | None = None) -> dict[str, Any] | None:
        params: list[Any] = [automation_rule_id]
        query = """
            SELECT
                r.*,
                COALESCE(u.display_name, u.login) AS created_by_user_name,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM automation_rules r
            LEFT JOIN users u ON u.user_id = r.created_by_user_id
            LEFT JOIN organizations o ON o.organization_id = r.organization_id
            WHERE r.automation_rule_id = ?
        """
        if organization_id is not None:
            query += " AND r.organization_id = ?"
            params.append(organization_id)
        with get_connection() as connection:
            row = connection.execute(query, params).fetchone()
        return dict(row) if row else None

    def get_by_slug(self, organization_id: int, rule_slug: str) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM automation_rules
                WHERE organization_id = ?
                  AND rule_slug = ?
                """,
                (organization_id, rule_slug),
            ).fetchone()
        return dict(row) if row else None

    def create(self, payload: dict[str, Any]) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return self._insert_rule(connection, payload, timestamp=timestamp)

    def create_active_from_now(self, payload: dict[str, Any], *, activated_at: str) -> int:
        """Create an active rule behind the current organization event watermark."""

        def operation(connection: Any) -> int:
            watermark = self._organization_event_watermark(
                connection,
                organization_id=int(payload["organization_id"]),
            )
            return self._insert_rule(
                connection,
                {**payload, "is_active": 1, "last_processed_event_log_id": watermark},
                timestamp=activated_at,
            )

        return self._run_activation_transaction(operation)

    def activate_rule_from_now(
        self,
        automation_rule_id: int,
        *,
        organization_id: int,
        fields: dict[str, Any],
        activated_at: str,
    ) -> dict[str, Any]:
        """Atomically persist requested fields and activate a rule from the current org watermark."""

        allowed = {
            "rule_slug",
            "rule_name",
            "description",
            "trigger_event_type",
            "conditions_json",
            "actions_json",
        }
        activation_fields = {key: value for key, value in fields.items() if key in allowed}

        def operation(connection: Any) -> dict[str, Any]:
            row = connection.execute(
                """
                SELECT automation_rule_id, is_active,
                       CASE
                           WHEN processing_claim_token IS NOT NULL
                            AND processing_lease_until IS NOT NULL
                            AND processing_lease_until > ?
                           THEN 1 ELSE 0
                       END AS has_active_lease
                FROM automation_rules
                WHERE automation_rule_id = ?
                  AND organization_id = ?
                """,
                (activated_at, automation_rule_id, organization_id),
            ).fetchone()
            if row is None:
                return {"status": "not_found", "watermark": None}
            if int(row["is_active"] or 0):
                return {"status": "already_active", "watermark": None}
            if int(row["has_active_lease"] or 0):
                return {"status": "busy", "watermark": None}

            watermark = self._organization_event_watermark(
                connection,
                organization_id=organization_id,
            )
            update_fields = {
                **activation_fields,
                "is_active": 1,
                "last_processed_event_log_id": watermark,
                "updated_at": activated_at,
            }
            assignments = ", ".join(f"{key} = ?" for key in update_fields)
            updated = connection.execute(
                f"""
                UPDATE automation_rules
                SET {assignments}
                WHERE automation_rule_id = ?
                  AND organization_id = ?
                  AND COALESCE(is_active, 0) = 0
                """,
                [*update_fields.values(), automation_rule_id, organization_id],
            )
            if not updated.rowcount:
                return {"status": "not_found", "watermark": None}
            return {"status": "activated", "watermark": watermark}

        return self._run_activation_transaction(operation)

    def _insert_rule(self, connection: Any, payload: dict[str, Any], *, timestamp: str) -> int:
        return execute_insert_returning_id(
            connection,
            """
                INSERT INTO automation_rules (
                    organization_id, rule_slug, rule_name, description, trigger_event_type, conditions_json,
                    actions_json, is_active, last_processed_event_log_id, last_run_at, last_result,
                    execution_count, created_by_user_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["organization_id"],
                payload["rule_slug"],
                payload["rule_name"],
                payload.get("description"),
                payload["trigger_event_type"],
                payload.get("conditions_json") or "{}",
                payload.get("actions_json") or "[]",
                int(payload.get("is_active", 1)),
                int(payload.get("last_processed_event_log_id") or 0),
                payload.get("last_run_at"),
                payload.get("last_result"),
                int(payload.get("execution_count") or 0),
                payload.get("created_by_user_id"),
                timestamp,
                timestamp,
            ),
            "automation_rule_id",
        )

    @staticmethod
    def _organization_event_watermark(connection: Any, *, organization_id: int) -> int:
        row = connection.execute(
            "SELECT COALESCE(MAX(id), 0) AS watermark FROM event_logs WHERE organization_id = ?",
            (organization_id,),
        ).fetchone()
        return int(row["watermark"] or 0)

    def _run_activation_transaction(
        self,
        operation: Callable[[Any], _ActivationResult],
    ) -> _ActivationResult:
        for attempt in range(AUTOMATION_ACTIVATION_SERIALIZATION_ATTEMPTS):
            try:
                with get_connection() as connection:
                    self._begin_activation_transaction(connection)
                    return operation(connection)
            except Exception as error:
                if (
                    attempt + 1 >= AUTOMATION_ACTIVATION_SERIALIZATION_ATTEMPTS
                    or not self._is_serialization_conflict(error)
                ):
                    raise
        raise RuntimeError("Activation transaction retry loop exhausted unexpectedly.")

    @staticmethod
    def _begin_activation_transaction(connection: Any) -> None:
        if connection.backend == "sqlite":
            connection.execute("BEGIN IMMEDIATE")
            return
        # Opening a PostgreSQL connection applies session settings in an initial transaction.
        # Commit those settings before starting the short serializable activation boundary.
        connection.commit()
        connection.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")

    @staticmethod
    def _is_serialization_conflict(error: Exception) -> bool:
        current: BaseException | None = error
        while current is not None:
            if getattr(current, "sqlstate", None) == "40001" or getattr(current, "pgcode", None) == "40001":
                return True
            current = current.__cause__ or current.__context__
        return "could not serialize access" in str(error).lower()

    def update(self, automation_rule_id: int, fields: dict[str, Any]) -> None:
        if not fields:
            return
        allowed = {
            "rule_slug",
            "rule_name",
            "description",
            "trigger_event_type",
            "conditions_json",
            "actions_json",
            "is_active",
            "last_processed_event_log_id",
            "last_run_at",
            "last_result",
            "execution_count",
        }
        update_fields = {key: value for key, value in fields.items() if key in allowed}
        if not update_fields:
            return
        update_fields["updated_at"] = now_iso()
        assignments = ", ".join(f"{key} = ?" for key in update_fields)
        values = list(update_fields.values()) + [automation_rule_id]
        with get_connection() as connection:
            connection.execute(
                f"UPDATE automation_rules SET {assignments} WHERE automation_rule_id = ?",
                values,
            )

    def list_executions(
        self,
        *,
        organization_id: int | None = None,
        automation_rule_id: int | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        params: list[Any] = []
        conditions = []
        conditions.append("e.execution_status IN ('success', 'failed')")
        if organization_id is not None:
            conditions.append("e.organization_id = ?")
            params.append(organization_id)
            conditions.append("r.organization_id = ?")
            params.append(organization_id)
        if automation_rule_id is not None:
            conditions.append("e.automation_rule_id = ?")
            params.append(automation_rule_id)
        query = """
            SELECT
                e.*,
                r.rule_name,
                r.rule_slug,
                r.trigger_event_type
            FROM automation_executions e
            JOIN automation_rules r ON r.automation_rule_id = e.automation_rule_id
        """
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY e.executed_at DESC, e.automation_execution_id DESC LIMIT ?"
        params.append(max(1, int(limit)))
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_operations_snapshot(self, organization_id: int) -> dict[str, Any]:
        """Return a payload-free, organization-scoped operational projection."""
        with get_connection() as connection:
            rule_counts = dict(connection.execute(
                """
                SELECT
                    COUNT(*) AS total_rules_count,
                    SUM(CASE WHEN COALESCE(is_active, 1) = 1 THEN 1 ELSE 0 END) AS enabled_rules_count,
                    SUM(CASE WHEN COALESCE(is_active, 1) = 0 THEN 1 ELSE 0 END) AS disabled_rules_count,
                    MAX(updated_at) AS last_rule_updated_at
                FROM automation_rules
                WHERE organization_id = ?
                """,
                (organization_id,),
            ).fetchone())
            latest = connection.execute(
                """
                SELECT
                    e.automation_execution_id,
                    e.automation_rule_id,
                    e.execution_status,
                    e.executed_at
                FROM automation_executions e
                JOIN automation_rules r ON r.automation_rule_id = e.automation_rule_id
                WHERE e.organization_id = ?
                  AND r.organization_id = ?
                  AND COALESCE(r.is_active, 1) = 1
                  AND e.execution_status IN ('success', 'failed')
                ORDER BY e.executed_at DESC, e.automation_execution_id DESC
                LIMIT 1
                """,
                (organization_id, organization_id),
            ).fetchone()
            aggregates = dict(connection.execute(
                """
                SELECT
                    COUNT(*) AS executions_count,
                    SUM(CASE WHEN e.execution_status = 'success' THEN 1 ELSE 0 END) AS succeeded_count,
                    SUM(CASE WHEN e.execution_status = 'failed' THEN 1 ELSE 0 END) AS failed_count,
                    MAX(CASE WHEN e.execution_status = 'success' THEN e.executed_at END) AS last_success_at,
                    MAX(CASE WHEN e.execution_status = 'failed' THEN e.executed_at END) AS last_failure_at
                FROM automation_executions e
                JOIN automation_rules r ON r.automation_rule_id = e.automation_rule_id
                WHERE e.organization_id = ?
                  AND r.organization_id = ?
                  AND COALESCE(r.is_active, 1) = 1
                  AND e.execution_status IN ('success', 'failed')
                """,
                (organization_id, organization_id),
            ).fetchone())
            recent_failure_count = int(connection.execute(
                """
                SELECT COUNT(*)
                FROM (
                    SELECT e.execution_status
                    FROM automation_executions e
                    JOIN automation_rules r ON r.automation_rule_id = e.automation_rule_id
                    WHERE e.organization_id = ?
                      AND r.organization_id = ?
                      AND COALESCE(r.is_active, 1) = 1
                      AND e.execution_status IN ('success', 'failed')
                    ORDER BY e.executed_at DESC, e.automation_execution_id DESC
                    LIMIT 50
                ) recent
                WHERE recent.execution_status = 'failed'
                """,
                (organization_id, organization_id),
            ).fetchone()[0])
        return {
            "rule_counts": rule_counts,
            "latest_execution": dict(latest) if latest else None,
            "aggregates": aggregates,
            "recent_failure_count": recent_failure_count,
        }

    def list_rules_read_only(self, *, organization_id: int, limit: int) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT automation_rule_id, is_active, execution_count, created_at, updated_at
                FROM automation_rules
                WHERE organization_id = ?
                ORDER BY updated_at DESC, automation_rule_id DESC
                LIMIT ?
                """,
                (organization_id, max(1, min(int(limit), 50))),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_executions_read_only(self, *, organization_id: int, limit: int) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    e.automation_execution_id,
                    e.automation_rule_id,
                    e.execution_status,
                    e.executed_at
                FROM automation_executions e
                JOIN automation_rules r ON r.automation_rule_id = e.automation_rule_id
                WHERE e.organization_id = ?
                  AND r.organization_id = ?
                  AND e.execution_status IN ('success', 'failed')
                ORDER BY e.executed_at DESC, e.automation_execution_id DESC
                LIMIT ?
                """,
                (organization_id, organization_id, max(1, min(int(limit), 50))),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_activity_executions_read_only(self, *, organization_id: int, limit: int) -> list[dict[str, Any]]:
        with get_read_only_connection() as connection:
            rows = connection.execute(
                """
                SELECT automation_execution_id, execution_status, executed_at
                FROM automation_executions
                WHERE organization_id = ? AND execution_status IN ('success', 'failed')
                ORDER BY executed_at DESC, automation_execution_id DESC LIMIT ?
                """,
                (organization_id, max(1, min(int(limit), 20))),
            ).fetchall()
        return [dict(row) for row in rows]

    def create_execution(self, payload: dict[str, Any]) -> int:
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO automation_executions (
                    automation_rule_id, organization_id, event_log_id, trigger_event_type, execution_status,
                    input_json, result_json, error_message, executed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["automation_rule_id"],
                    payload["organization_id"],
                    payload.get("event_log_id"),
                    payload["trigger_event_type"],
                    payload["execution_status"],
                    payload.get("input_json"),
                    payload.get("result_json"),
                    payload.get("error_message"),
                    payload.get("executed_at") or now_iso(),
                ),
                "automation_execution_id",
            )

    def try_claim_execution(self, payload: dict[str, Any]) -> dict[str, Any]:
        query = """
            INSERT INTO automation_executions (
                automation_rule_id, organization_id, event_log_id, trigger_event_type, execution_status,
                input_json, result_json, error_message, executed_at
            )
            SELECT
                r.automation_rule_id, r.organization_id, ?, ?, 'processing', ?, NULL, NULL, ?
            FROM automation_rules r
            WHERE r.automation_rule_id = ?
              AND r.organization_id = ?
        """
        params = (
            payload.get("event_log_id"),
            payload["trigger_event_type"],
            payload.get("input_json"),
            payload.get("executed_at") or now_iso(),
            payload["automation_rule_id"],
            payload["organization_id"],
        )
        with get_connection() as connection:
            try:
                if connection.backend == "sqlite":
                    cursor = connection.execute(query, params)
                    if not cursor.rowcount:
                        raise ValueError("Automation rule does not belong to the requested organization.")
                    execution_id = int(cursor.lastrowid)
                else:
                    cursor = connection.execute(
                        f"{query.rstrip().rstrip(';')} RETURNING automation_execution_id",
                        params,
                    )
                    row = cursor.fetchone()
                    if row is None:
                        raise ValueError("Automation rule does not belong to the requested organization.")
                    execution_id = int(row["automation_execution_id"])
            except Exception as error:
                if self._is_execution_identity_conflict(error):
                    return {"claimed": False, "reason": "already_claimed", "automation_execution_id": None}
                raise
        return {"claimed": True, "reason": "claimed", "automation_execution_id": execution_id}

    def complete_execution(
        self,
        automation_execution_id: int,
        *,
        execution_status: str,
        result_json: str | None = None,
        error_message: str | None = None,
        executed_at: str | None = None,
    ) -> bool:
        if execution_status not in {"success", "failed"}:
            raise ValueError("Execution can only be completed with a terminal status.")
        with get_connection() as connection:
            updated = connection.execute(
                """
                UPDATE automation_executions
                SET execution_status = ?,
                    result_json = ?,
                    error_message = ?,
                    executed_at = ?
                WHERE automation_execution_id = ?
                  AND execution_status = 'processing'
                """,
                (
                    execution_status,
                    result_json,
                    error_message,
                    executed_at or now_iso(),
                    automation_execution_id,
                ),
            )
            return bool(updated.rowcount)

    def get_execution_by_id(self, automation_execution_id: int) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT * FROM automation_executions WHERE automation_execution_id = ?",
                (automation_execution_id,),
            ).fetchone()
        return dict(row) if row else None

    def acquire_rule_claim(
        self,
        *,
        automation_rule_id: int,
        organization_id: int,
        claim_token: str,
        claimed_at: str,
        lease_until: str,
        require_active: bool = False,
    ) -> bool:
        active_guard = "AND COALESCE(is_active, 1) = 1" if require_active else ""
        with get_connection() as connection:
            updated = connection.execute(
                f"""
                UPDATE automation_rules
                SET processing_claim_token = ?,
                    processing_claimed_at = ?,
                    processing_lease_until = ?
                WHERE automation_rule_id = ?
                  AND organization_id = ?
                  AND (
                      processing_claim_token IS NULL
                      OR processing_lease_until IS NULL
                      OR processing_lease_until <= ?
                  )
                  {active_guard}
                """,
                (
                    claim_token,
                    claimed_at,
                    lease_until,
                    automation_rule_id,
                    organization_id,
                    claimed_at,
                ),
            )
            return bool(updated.rowcount)

    def renew_rule_claim(
        self,
        *,
        automation_rule_id: int,
        organization_id: int,
        claim_token: str,
        now: str,
        lease_until: str,
        require_active: bool = False,
    ) -> bool:
        active_guard = "AND COALESCE(is_active, 1) = 1" if require_active else ""
        with get_connection() as connection:
            updated = connection.execute(
                f"""
                UPDATE automation_rules
                SET processing_lease_until = ?
                WHERE automation_rule_id = ?
                  AND organization_id = ?
                  AND processing_claim_token = ?
                  AND processing_lease_until > ?
                  {active_guard}
                """,
                (lease_until, automation_rule_id, organization_id, claim_token, now),
            )
            return bool(updated.rowcount)

    def release_rule_claim(
        self,
        *,
        automation_rule_id: int,
        organization_id: int,
        claim_token: str,
    ) -> bool:
        with get_connection() as connection:
            updated = connection.execute(
                """
                UPDATE automation_rules
                SET processing_claim_token = NULL,
                    processing_claimed_at = NULL,
                    processing_lease_until = NULL
                WHERE automation_rule_id = ?
                  AND organization_id = ?
                  AND processing_claim_token = ?
                """,
                (automation_rule_id, organization_id, claim_token),
            )
            return bool(updated.rowcount)

    def update_rule_progress(
        self,
        *,
        automation_rule_id: int,
        organization_id: int,
        claim_token: str,
        now: str,
        last_processed_event_log_id: int,
        last_run_at: str,
        last_result: str,
        execution_count_increment: int,
        require_inactive: bool = False,
    ) -> bool:
        inactive_guard = "AND COALESCE(is_active, 0) = 0" if require_inactive else ""
        with get_connection() as connection:
            updated = connection.execute(
                f"""
                UPDATE automation_rules
                SET last_processed_event_log_id = CASE
                        WHEN last_processed_event_log_id < ? THEN ?
                        ELSE last_processed_event_log_id
                    END,
                    last_run_at = ?,
                    last_result = ?,
                    execution_count = execution_count + ?,
                    updated_at = ?
                WHERE automation_rule_id = ?
                  AND organization_id = ?
                  AND processing_claim_token = ?
                  AND processing_lease_until > ?
                  {inactive_guard}
                """,
                (
                    last_processed_event_log_id,
                    last_processed_event_log_id,
                    last_run_at,
                    last_result,
                    max(0, int(execution_count_increment)),
                    now,
                    automation_rule_id,
                    organization_id,
                    claim_token,
                    now,
                ),
            )
            return bool(updated.rowcount)

    @staticmethod
    def _is_execution_identity_conflict(error: Exception) -> bool:
        message = str(error).lower()
        return (
            "idx_automation_executions_rule_event_unique" in message
            or "automation_executions.automation_rule_id, automation_executions.event_log_id" in message
            or (
                "duplicate key value violates unique constraint" in message
                and "automation_executions" in message
            )
        )

