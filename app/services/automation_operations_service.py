from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Protocol

from app.repositories.internal_notification_schedule_repository import InternalNotificationScheduleRepository
from app.services.internal_notification_service import (
    INTERNAL_NOTIFICATION_SOURCE_BILLING_ATTENTION,
    InternalNotificationService,
)


INTERNAL_NOTIFICATION_SCHEDULER_KEY = "internal_notification_scheduler"
AUTOMATION_CONFIGURATION_STATUSES = {"enabled", "disabled", "not_configured"}
AUTOMATION_HEALTH_STATUSES = {"healthy", "attention", "never_run", "disabled"}
REQUIRED_OPERATION_FIELDS = {
    "automation_key",
    "automation_type",
    "title",
    "description",
    "status",
    "enabled",
    "health",
    "health_reason_code",
    "next_run_at",
    "last_run_at",
    "last_run_status",
    "recent_failure_count",
    "settings_url",
    "details_url",
    "updated_at",
}
_SAFE_ERROR_CODE = re.compile(r"^[a-z0-9_]{1,80}$")
_SENSITIVE_ERROR_TEXT = re.compile(
    r"(?:traceback|stack trace|password|passwd|secret|token|authorization|connection string|database_url|dsn)",
    re.IGNORECASE,
)


class AutomationOperationNotFoundError(ValueError):
    pass


class AutomationOperationsAdapter(Protocol):
    automation_key: str

    def get_operation(self, *, organization_id: int, recipient_user_id: int) -> dict[str, Any]: ...

    def get_history(
        self,
        *,
        organization_id: int,
        recipient_user_id: int,
        limit: int,
    ) -> list[dict[str, Any]]: ...


class AutomationOperationsRegistry:
    def __init__(self, adapters: tuple[AutomationOperationsAdapter, ...]) -> None:
        keys = [str(adapter.automation_key or "").strip() for adapter in adapters]
        if any(not key for key in keys):
            raise ValueError("Każdy adapter Centrum Automatyzacji musi mieć automation_key.")
        if len(keys) != len(set(keys)):
            raise ValueError("automation_key adapterów Centrum Automatyzacji muszą być unikalne.")
        self._adapters = adapters
        self._by_key = dict(zip(keys, adapters, strict=True))

    @property
    def adapters(self) -> tuple[AutomationOperationsAdapter, ...]:
        return self._adapters

    def get(self, automation_key: str) -> AutomationOperationsAdapter | None:
        return self._by_key.get(str(automation_key or "").strip())

    @staticmethod
    def validate_operation(operation: dict[str, Any]) -> None:
        missing = sorted(REQUIRED_OPERATION_FIELDS - set(operation))
        if missing:
            raise ValueError(f"Adapter Centrum Automatyzacji nie zwrócił pól: {', '.join(missing)}.")
        if operation["status"] not in AUTOMATION_CONFIGURATION_STATUSES:
            raise ValueError("Adapter zwrócił nieprawidłowy status konfiguracji.")
        if operation["health"] not in AUTOMATION_HEALTH_STATUSES:
            raise ValueError("Adapter zwrócił nieprawidłowy health.")


def scheduler_health(
    *,
    schedule_exists: bool,
    enabled: bool,
    last_terminal_status: str | None,
) -> tuple[str, str, str]:
    if not schedule_exists:
        return "not_configured", "disabled", "schedule_not_configured"
    if not enabled:
        return "disabled", "disabled", "schedule_disabled"
    if last_terminal_status is None:
        return "enabled", "never_run", "no_terminal_run"
    if last_terminal_status == "failed":
        return "enabled", "attention", "last_run_failed"
    if last_terminal_status == "succeeded":
        return "enabled", "healthy", "last_run_succeeded"
    raise ValueError("Nieznany terminalny status runu schedulera.")


class InternalNotificationSchedulerOperationsAdapter:
    automation_key = INTERNAL_NOTIFICATION_SCHEDULER_KEY

    def __init__(self, repository: InternalNotificationScheduleRepository) -> None:
        self.repository = repository

    def get_operation(self, *, organization_id: int, recipient_user_id: int) -> dict[str, Any]:
        snapshot = self.repository.get_operations_snapshot(
            organization_id=organization_id,
            recipient_user_id=recipient_user_id,
            source_type=INTERNAL_NOTIFICATION_SOURCE_BILLING_ATTENTION,
        )
        exists = snapshot is not None
        enabled = bool(int(snapshot.get("enabled") or 0)) if snapshot else False
        terminal_status = str(snapshot.get("terminal_run_status") or "") or None if snapshot else None
        status, health, reason = scheduler_health(
            schedule_exists=exists,
            enabled=enabled,
            last_terminal_status=terminal_status,
        )
        latest_status = str(snapshot.get("latest_run_status") or "") or None if snapshot else None
        latest_error_code = snapshot.get("terminal_error_code") if snapshot else None
        latest_error_summary = snapshot.get("terminal_error_summary") if snapshot else None
        if snapshot and latest_status == "failed":
            latest_error_code = snapshot.get("latest_error_code")
            latest_error_summary = snapshot.get("latest_error_summary")
        schedule_id = int(snapshot["internal_notification_schedule_id"]) if snapshot else None
        run_id = int(snapshot["latest_run_id"]) if snapshot and snapshot.get("latest_run_id") is not None else None
        operation = {
            "automation_key": self.automation_key,
            "automation_type": "scheduler",
            "title": "Automatyczne sprawdzanie powiadomień",
            "description": "Codziennie materializuje brakujące wewnętrzne powiadomienia z billing attention.",
            "status": status,
            "enabled": enabled,
            "health": health,
            "health_reason_code": reason,
            "schedule_id": schedule_id,
            "run_id": run_id,
            "next_run_at": snapshot.get("next_run_at_utc") if snapshot else None,
            "last_run_at": (
                snapshot.get("latest_started_at") or snapshot.get("latest_created_at")
                if snapshot
                else None
            ),
            "last_run_status": latest_status,
            "last_run_duration_ms": _duration_ms(
                snapshot.get("latest_started_at") if snapshot else None,
                snapshot.get("latest_finished_at") if snapshot else None,
            ),
            "last_attempt_count": int(snapshot.get("latest_attempt_count") or 0) if snapshot and run_id else None,
            "last_candidates_count": _optional_non_negative_int(snapshot.get("latest_candidates_count") if snapshot else None),
            "last_created_count": _optional_non_negative_int(snapshot.get("latest_created_count") if snapshot else None),
            "last_existing_count": _optional_non_negative_int(snapshot.get("latest_existing_count") if snapshot else None),
            "recent_failure_count": int(snapshot.get("recent_failure_count") or 0) if snapshot else 0,
            "last_error_code": _safe_error_code(latest_error_code),
            "last_error_summary": _safe_error_summary(latest_error_summary),
            "settings_url": "/powiadomienia",
            "details_url": f"/automatyzacje/{self.automation_key}",
            "runtime_status": "unknown",
            "schedule": {
                "cadence": str(snapshot.get("cadence") or "daily") if snapshot else "daily",
                "timezone_name": str(snapshot.get("timezone_name") or "Europe/Warsaw") if snapshot else "Europe/Warsaw",
                "local_time": str(snapshot.get("local_time") or "08:00") if snapshot else "08:00",
            },
            "updated_at": (
                snapshot.get("latest_created_at") or snapshot.get("updated_at")
                if snapshot
                else None
            ),
        }
        AutomationOperationsRegistry.validate_operation(operation)
        return operation

    def get_history(
        self,
        *,
        organization_id: int,
        recipient_user_id: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        snapshot = self.repository.get_operations_snapshot(
            organization_id=organization_id,
            recipient_user_id=recipient_user_id,
            source_type=INTERNAL_NOTIFICATION_SOURCE_BILLING_ATTENTION,
        )
        if not snapshot:
            return []
        schedule_id = int(snapshot["internal_notification_schedule_id"])
        rows = self.repository.list_runs_read_only(schedule_id=schedule_id, limit=limit)
        return [_serialize_run(row) for row in rows]


class AutomationOperationsService:
    def __init__(
        self,
        *,
        registry: AutomationOperationsRegistry,
        notification_service: InternalNotificationService,
    ) -> None:
        self.registry = registry
        self.notification_service = notification_service

    def dashboard(
        self,
        *,
        organization_id: int,
        recipient_user_id: int,
        actor_user: dict[str, Any],
    ) -> dict[str, Any]:
        self._validate_scope(
            organization_id=organization_id,
            recipient_user_id=recipient_user_id,
            actor_user=actor_user,
        )
        items = [
            adapter.get_operation(
                organization_id=organization_id,
                recipient_user_id=recipient_user_id,
            )
            for adapter in self.registry.adapters
        ]
        for item in items:
            AutomationOperationsRegistry.validate_operation(item)
        return {
            "summary": {
                "active_count": sum(1 for item in items if item["status"] == "enabled"),
                "disabled_count": sum(1 for item in items if item["status"] != "enabled"),
                "attention_count": sum(1 for item in items if item["health"] == "attention"),
                "recent_failure_count": sum(int(item["recent_failure_count"]) for item in items),
            },
            "items": items,
        }

    def detail(
        self,
        automation_key: str,
        *,
        organization_id: int,
        recipient_user_id: int,
        actor_user: dict[str, Any],
        history_limit: int = 20,
    ) -> dict[str, Any]:
        self._validate_scope(
            organization_id=organization_id,
            recipient_user_id=recipient_user_id,
            actor_user=actor_user,
        )
        adapter = self.registry.get(automation_key)
        if not adapter:
            raise AutomationOperationNotFoundError("Nie znaleziono automatyzacji.")
        normalized_limit = max(1, min(int(history_limit), 50))
        operation = adapter.get_operation(
            organization_id=organization_id,
            recipient_user_id=recipient_user_id,
        )
        AutomationOperationsRegistry.validate_operation(operation)
        history = adapter.get_history(
            organization_id=organization_id,
            recipient_user_id=recipient_user_id,
            limit=normalized_limit,
        )
        return {
            "item": operation,
            "history": history,
            "history_limit": normalized_limit,
        }

    def _validate_scope(
        self,
        *,
        organization_id: int,
        recipient_user_id: int,
        actor_user: dict[str, Any],
    ) -> None:
        self.notification_service.validate_recipient_scope(
            organization_id=organization_id,
            recipient_user_id=recipient_user_id,
            actor_user=actor_user,
            require_write=False,
        )


def _optional_non_negative_int(value: Any) -> int | None:
    if value is None:
        return None
    normalized = int(value)
    return normalized if normalized >= 0 else None


def _safe_error_code(value: Any) -> str | None:
    normalized = str(value or "").strip().lower()
    return normalized if _SAFE_ERROR_CODE.fullmatch(normalized) else None


def _safe_error_summary(value: Any) -> str | None:
    normalized = " ".join(str(value or "").split())
    if not normalized:
        return None
    if _SENSITIVE_ERROR_TEXT.search(normalized):
        return "Błąd wykonania. Szczegóły techniczne zostały ukryte."
    return normalized[:240]


def _duration_ms(started_at: Any, finished_at: Any) -> int | None:
    if not started_at or not finished_at:
        return None
    try:
        started = datetime.fromisoformat(str(started_at).replace("Z", "+00:00"))
        finished = datetime.fromisoformat(str(finished_at).replace("Z", "+00:00"))
    except ValueError:
        return None
    return max(0, int((finished - started).total_seconds() * 1000))


def _serialize_run(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": int(run["internal_notification_schedule_run_id"]),
        "schedule_id": int(run["schedule_id"]),
        "scheduled_local_date": str(run["scheduled_local_date"]),
        "as_of_date": str(run["as_of_date"]),
        "scheduled_for_utc": str(run["scheduled_for_utc"]),
        "status": str(run["status"]),
        "attempt_count": int(run["attempt_count"]),
        "candidates_count": _optional_non_negative_int(run.get("candidates_count")),
        "created_count": _optional_non_negative_int(run.get("created_count")),
        "existing_count": _optional_non_negative_int(run.get("existing_count")),
        "error_code": _safe_error_code(run.get("error_code")),
        "error_summary": _safe_error_summary(run.get("error_summary")),
        "started_at": run.get("started_at"),
        "finished_at": run.get("finished_at"),
        "duration_ms": _duration_ms(run.get("started_at"), run.get("finished_at")),
    }
