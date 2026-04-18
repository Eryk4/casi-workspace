from __future__ import annotations

from typing import Any

from app.db import execute_insert_returning_id, get_connection
from app.utils import now_iso


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
        if organization_id is not None:
            conditions.append("e.organization_id = ?")
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

