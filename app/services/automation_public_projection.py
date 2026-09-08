from __future__ import annotations

from typing import Any


def automation_execution_error_projection(
    status: Any,
    *,
    latest: bool = False,
) -> tuple[str | None, str | None]:
    if str(status or "").strip().lower() != "failed":
        return None, None
    return (
        "automation_execution_failed",
        (
            "Ostatnie wykonanie reguły automatyzacji zakończyło się błędem."
            if latest
            else "Wykonanie reguły automatyzacji zakończyło się błędem."
        ),
    )


def project_public_automation_rule(rule: dict[str, Any]) -> dict[str, Any]:
    """Return the allowlisted rule summary safe for user-facing APIs."""
    return {
        "automation_rule_id": int(rule["automation_rule_id"]),
        "rule_name": rule.get("rule_name"),
        "rule_slug": rule.get("rule_slug"),
        "description": rule.get("description"),
        "trigger_event_type": rule.get("trigger_event_type"),
        "is_active": bool(rule.get("is_active")),
        "last_run_at": rule.get("last_run_at"),
        "execution_count": int(rule.get("execution_count") or 0),
        "created_at": rule.get("created_at"),
        "updated_at": rule.get("updated_at"),
    }


def project_public_automation_execution(execution: dict[str, Any]) -> dict[str, Any]:
    """Return operational execution metadata without input, output, or raw errors."""
    status = str(execution.get("execution_status") or "")
    error_code, error_summary = automation_execution_error_projection(status)
    return {
        "automation_execution_id": int(execution["automation_execution_id"]),
        "automation_rule_id": int(execution["automation_rule_id"]),
        "execution_status": status,
        "trigger_event_type": execution.get("trigger_event_type"),
        "executed_at": execution.get("executed_at"),
        "error_code": error_code,
        "error_summary": error_summary,
    }
