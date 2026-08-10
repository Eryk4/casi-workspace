from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Callable, Protocol

from app.repositories.email_import_repository import EmailImportRepository
from app.repositories.internal_notification_schedule_repository import InternalNotificationScheduleRepository
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.ksef_import_repository import KSeFImportRepository
from app.repositories.task_reminder_outbox_repository import TaskReminderOutboxRepository
from app.services.internal_notification_service import (
    INTERNAL_NOTIFICATION_SOURCE_BILLING_ATTENTION,
    InternalNotificationService,
)
from app.services.task_reminder_service import TaskReminderService


INTERNAL_NOTIFICATION_SCHEDULER_KEY = "internal_notification_scheduler"
TASK_REMINDERS_KEY = "task_reminders"
KNOWLEDGE_PROCESSING_KEY = "knowledge_processing"
EMAIL_IMPORT_KEY = "email_import"
KSEF_IMPORT_KEY = "ksef_import"
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
_ABSOLUTE_PATH_TEXT = re.compile(r"(?:[a-z]:\\|/(?:home|users|var|tmp|srv|opt)/)", re.IGNORECASE)


class AutomationOperationNotFoundError(ValueError):
    pass


class AutomationOperationsAdapter(Protocol):
    automation_key: str
    scope: str
    capabilities: frozenset[str]

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
        if any(not str(getattr(adapter, "scope", "")).strip() for adapter in adapters):
            raise ValueError("Każdy adapter Centrum Automatyzacji musi deklarować scope.")
        if any(not getattr(adapter, "capabilities", None) for adapter in adapters):
            raise ValueError("Każdy adapter Centrum Automatyzacji musi deklarować capabilities.")
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


def email_import_health(
    *,
    runtime_enabled: bool,
    organization_configured: bool,
    mailbox_configured: bool,
    last_terminal_status: str | None,
) -> tuple[str, str, str]:
    if not runtime_enabled:
        return "disabled", "disabled", "email_import_runtime_disabled"
    if not organization_configured:
        return "not_configured", "disabled", "organization_email_not_configured"
    if not mailbox_configured:
        return "not_configured", "disabled", "system_mailbox_not_configured"
    if last_terminal_status is None:
        return "enabled", "never_run", "no_terminal_email_import_run"
    if last_terminal_status in {"failed", "completed_with_issues"}:
        return "enabled", "attention", "last_email_import_run_requires_attention"
    if last_terminal_status in {"completed", "no_new_documents"}:
        return "enabled", "healthy", "last_email_import_run_succeeded"
    raise ValueError("Nieznany terminalny status importu e-mail.")


def ksef_import_health(
    *, integration_enabled: bool, organization_configured: bool, last_terminal_status: str | None
) -> tuple[str, str, str]:
    if not integration_enabled:
        return "disabled", "disabled", "ksef_import_disabled"
    if not organization_configured:
        return "not_configured", "disabled", "organization_ksef_not_configured"
    if last_terminal_status is None:
        return "enabled", "never_run", "no_terminal_ksef_import_run"
    if last_terminal_status in {"failed", "completed_with_issues"}:
        return "enabled", "attention", "last_ksef_import_run_requires_attention"
    if last_terminal_status in {"completed", "no_new_documents"}:
        return "enabled", "healthy", "last_ksef_import_run_succeeded"
    raise ValueError("Nieznany terminalny status importu KSeF.")


class InternalNotificationSchedulerOperationsAdapter:
    automation_key = INTERNAL_NOTIFICATION_SCHEDULER_KEY
    scope = "organization_recipient"
    capabilities = frozenset({"summary", "history", "settings"})

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


def task_reminder_health(*, enabled: bool, failed_count: int, latest_attempt_status: str | None, disabled_reason: str | None = None) -> tuple[str, str, str]:
    if not enabled:
        return "disabled", "disabled", disabled_reason or "runtime_disabled"
    if failed_count > 0:
        return "enabled", "attention", "failed_outbox_present"
    if latest_attempt_status in {"failed", "dead_letter", "retry"}:
        return "enabled", "attention", "last_attempt_failed"
    if latest_attempt_status == "sent":
        return "enabled", "healthy", "last_attempt_sent"
    return "enabled", "never_run", "no_delivery_attempt"


class TaskRemindersOperationsAdapter:
    automation_key = TASK_REMINDERS_KEY
    scope = "organization_task_visibility"
    capabilities = frozenset({"summary", "history", "queue", "heartbeat"})

    def __init__(self, repository: TaskReminderOutboxRepository, service: TaskReminderService) -> None:
        self.repository = repository
        self.service = service

    def get_operation(self, *, organization_id: int, recipient_user_id: int) -> dict[str, Any]:
        contract = self.service.runtime_contract(organization_id=organization_id)
        snapshot = self.repository.get_operations_snapshot(
            organization_id=organization_id,
            viewer_user_id=recipient_user_id,
        )
        counts = snapshot["counts"]
        attempt = snapshot["latest_attempt"]
        outbox = snapshot["latest_outbox"]
        attempt_status = str(attempt.get("outcome") or "") or None if attempt else None
        status, health, reason = task_reminder_health(
            enabled=bool(contract["enabled"]),
            failed_count=int(counts["failed"]),
            latest_attempt_status=attempt_status,
            disabled_reason=contract.get("disabled_reason"),
        )
        error_value = attempt.get("error_message") if attempt else None
        if not error_value and outbox:
            error_value = outbox.get("last_error")
        last_activity = None
        if attempt:
            last_activity = attempt.get("attempted_at")
        elif outbox:
            last_activity = outbox.get("last_attempt_at") or outbox.get("updated_at") or outbox.get("created_at")
        operation = {
            "automation_key": self.automation_key,
            "automation_type": "task_reminders",
            "title": "Przypomnienia zadań",
            "description": "Kolejka i historia dostarczania przypomnień Telegram dla widocznych zadań.",
            "status": status,
            "enabled": bool(contract["enabled"]),
            "disabled_reason": contract.get("disabled_reason"),
            "health": health,
            "health_reason_code": reason,
            "schedule_id": None,
            "run_id": None,
            "next_run_at": None,
            "last_run_at": last_activity,
            "last_activity_at": last_activity,
            "last_run_status": "succeeded" if attempt_status == "sent" else "failed" if attempt_status in {"failed", "dead_letter", "retry"} else None,
            "last_attempt_at": attempt.get("attempted_at") if attempt else None,
            "last_attempt_status": attempt_status,
            "last_attempt_count": int(attempt.get("attempt_no") or 0) if attempt else None,
            "last_run_duration_ms": None,
            "last_candidates_count": None,
            "last_created_count": None,
            "last_existing_count": None,
            "pending_count": int(counts["queued"]),
            "processing_count": int(counts["processing"]),
            "failed_count": int(counts["failed"]),
            "sent_count": int(counts["sent"]),
            "cancelled_count": int(counts["cancelled"]),
            "recent_failure_count": int(snapshot["recent_failure_count"]),
            "last_error_code": "task_reminder_delivery_failed" if error_value else None,
            "last_error_summary": _safe_error_summary(error_value),
            "last_heartbeat_at": snapshot["last_heartbeat_at"],
            "settings_url": None,
            "details_url": f"/automatyzacje/{self.automation_key}",
            "runtime_status": "unknown",
            "schedule": None,
            "updated_at": last_activity or snapshot["last_heartbeat_at"],
        }
        AutomationOperationsRegistry.validate_operation(operation)
        return operation

    def get_history(self, *, organization_id: int, recipient_user_id: int, limit: int) -> list[dict[str, Any]]:
        rows = self.repository.list_attempts_read_only(
            organization_id=organization_id,
            viewer_user_id=recipient_user_id,
            limit=limit,
        )
        return [{
            "history_type": "reminder_attempt",
            "attempt_id": int(row["task_reminder_outbox_attempt_id"]),
            "outbox_id": int(row["task_reminder_outbox_id"]),
            "channel": str(row["delivery_channel"]),
            "attempt_no": int(row["attempt_no"]),
            "status": str(row["outcome"]),
            "attempted_at": row["attempted_at"],
            "error_code": "task_reminder_delivery_failed" if row.get("error_message") else None,
            "error_summary": _safe_error_summary(row.get("error_message")),
        } for row in rows]

    def get_outbox(self, *, organization_id: int, recipient_user_id: int, limit: int) -> list[dict[str, Any]]:
        return self.repository.list_outbox_read_only(
            organization_id=organization_id,
            viewer_user_id=recipient_user_id,
            limit=limit,
        )


def knowledge_processing_health(
    *,
    latest_terminal_status: str | None,
    watcher_status: str | None,
) -> tuple[str, str, str]:
    if latest_terminal_status == "failed":
        return "enabled", "attention", "last_job_failed"
    if watcher_status in {"failed", "error"}:
        return "enabled", "attention", "last_folder_scan_failed"
    if latest_terminal_status == "completed":
        return "enabled", "healthy", "last_job_completed"
    return "enabled", "never_run", "no_terminal_job"


class KnowledgeProcessingOperationsAdapter:
    automation_key = KNOWLEDGE_PROCESSING_KEY
    scope = "organization"
    capabilities = frozenset({"summary", "history", "queue", "watcher_status"})

    def __init__(self, repository: KnowledgeRepository) -> None:
        self.repository = repository

    def get_operation(self, *, organization_id: int, recipient_user_id: int) -> dict[str, Any]:
        del recipient_user_id
        snapshot = self.repository.get_operations_snapshot(organization_id)
        counts = snapshot["counts"]
        latest_job = snapshot["latest_job"]
        terminal_job = snapshot["latest_terminal_job"]
        watcher = snapshot["watcher"]
        terminal_status = str(terminal_job.get("status") or "") or None if terminal_job else None
        watcher_status = str(watcher.get("last_scan_status") or "") or None if watcher else None
        status, health, reason = knowledge_processing_health(
            latest_terminal_status=terminal_status,
            watcher_status=watcher_status,
        )
        latest_status = str(latest_job.get("status") or "") or None if latest_job else None
        error_value = None
        error_code = None
        if terminal_job and terminal_status == "failed":
            error_value = terminal_job.get("error_message")
            error_code = "knowledge_processing_failed"
        elif watcher and watcher_status in {"failed", "error"}:
            error_value = watcher.get("last_error")
            error_code = "knowledge_folder_scan_failed"
        last_job_at = (
            latest_job.get("finished_at") or latest_job.get("started_at")
            or latest_job.get("updated_at") or latest_job.get("created_at")
            if latest_job else None
        )
        last_scan_at = (
            watcher.get("last_scan_completed_at") or watcher.get("last_scan_started_at") or watcher.get("updated_at")
            if watcher else None
        )
        last_activity = _latest_timestamp(last_job_at, last_scan_at)
        operation = {
            "automation_key": self.automation_key,
            "automation_type": "knowledge_processing",
            "title": "Przetwarzanie bazy wiedzy",
            "description": "Kolejka przetwarzania dokumentów i ostatni stan skanowania folderu organizacji.",
            "status": status,
            "enabled": True,
            "health": health,
            "health_reason_code": reason,
            "schedule_id": None,
            "run_id": int(latest_job["knowledge_processing_job_id"]) if latest_job else None,
            "next_run_at": None,
            "last_run_at": last_job_at,
            "last_activity_at": last_activity,
            "last_job_at": last_job_at,
            "last_run_status": _knowledge_run_status(latest_status),
            "last_job_status": latest_status,
            "last_run_duration_ms": _duration_ms(
                latest_job.get("started_at") if latest_job else None,
                latest_job.get("finished_at") if latest_job else None,
            ),
            "last_attempt_count": int(latest_job.get("attempts") or 0) if latest_job else None,
            "last_candidates_count": None,
            "last_created_count": None,
            "last_existing_count": None,
            "pending_count": int(counts.get("pending_count") or 0),
            "processing_count": int(counts.get("processing_count") or 0),
            "succeeded_count": int(counts.get("completed_count") or 0),
            "failed_count": int(counts.get("failed_count") or 0),
            "sent_count": 0,
            "cancelled_count": 0,
            "recent_failure_count": int(snapshot["recent_failure_count"]),
            "last_success_at": _snapshot_time(snapshot.get("latest_success")),
            "last_failure_at": _snapshot_time(snapshot.get("latest_failure")),
            "last_error_code": error_code,
            "last_error_summary": _safe_error_summary(error_value),
            "watcher_count": 1 if watcher else 0,
            "last_scan_at": last_scan_at,
            "last_scan_status": watcher_status,
            "settings_url": None,
            "details_url": f"/automatyzacje/{self.automation_key}",
            "runtime_status": "unknown",
            "schedule": None,
            "updated_at": last_activity,
        }
        AutomationOperationsRegistry.validate_operation(operation)
        return operation

    def get_history(self, *, organization_id: int, recipient_user_id: int, limit: int) -> list[dict[str, Any]]:
        del recipient_user_id
        return [_serialize_knowledge_job(row) for row in self.repository.list_jobs_read_only(
            organization_id=organization_id,
            limit=limit,
        )]

    def get_watchers(self, *, organization_id: int, recipient_user_id: int) -> list[dict[str, Any]]:
        del recipient_user_id
        watcher = self.repository.get_watch_status(organization_id)
        if not watcher:
            return []
        return [{
            "watcher_id": int(watcher["knowledge_folder_watcher_id"]),
            "watch_mode": str(watcher.get("watch_mode") or "polling"),
            "status": str(watcher.get("last_scan_status") or "idle"),
            "last_scan_started_at": watcher.get("last_scan_started_at"),
            "last_scan_completed_at": watcher.get("last_scan_completed_at"),
            "error_code": "knowledge_folder_scan_failed" if watcher.get("last_error") else None,
            "error_summary": _safe_error_summary(watcher.get("last_error")),
        }]


class EmailImportOperationsAdapter:
    automation_key = EMAIL_IMPORT_KEY
    scope = "organization"
    capabilities = frozenset({"summary", "history", "settings"})

    def __init__(
        self,
        repository: EmailImportRepository,
        configuration_status_provider: Callable[[], dict[str, Any]],
    ) -> None:
        self.repository = repository
        self.configuration_status_provider = configuration_status_provider

    def get_operation(self, *, organization_id: int, recipient_user_id: int) -> dict[str, Any]:
        del recipient_user_id
        snapshot = self.repository.get_operations_snapshot(organization_id)
        organization = snapshot["organization"] or {}
        latest_run = snapshot["latest_run"]
        terminal_run = snapshot["latest_terminal_run"]
        aggregates = snapshot["aggregates"]
        item_counts = snapshot["item_counts"]
        runtime = self.configuration_status_provider()
        organization_configured = bool(
            int(organization.get("is_active") or 0)
            and int(organization.get("email_integration_enabled") or 0)
            and int(organization.get("has_inbox") or 0)
        )
        runtime_enabled = bool(runtime.get("enabled"))
        mailbox_configured = bool(runtime.get("configured"))
        terminal_status = str(terminal_run.get("status") or "") or None if terminal_run else None
        status, health, reason = email_import_health(
            runtime_enabled=runtime_enabled,
            organization_configured=organization_configured,
            mailbox_configured=mailbox_configured,
            last_terminal_status=terminal_status,
        )
        latest_status = str(latest_run.get("status") or "") or None if latest_run else None
        last_error_code, last_error_summary = _email_import_error(terminal_status)
        operation = {
            "automation_key": self.automation_key,
            "automation_type": "email_import",
            "title": "Import e-maili",
            "description": "Monitoruje organizacyjny import faktur z centralnej skrzynki bez ujawniania treści wiadomości.",
            "status": status,
            "enabled": status == "enabled",
            "health": health,
            "health_reason_code": reason,
            "schedule_id": None,
            "run_id": int(latest_run["email_import_run_id"]) if latest_run else None,
            "next_run_at": None,
            "last_run_at": _email_import_run_time(latest_run),
            "last_activity_at": _email_import_run_time(latest_run),
            "last_run_status": _email_import_run_status(latest_status),
            "last_run_duration_ms": _duration_ms(
                latest_run.get("started_at") if latest_run else None,
                latest_run.get("finished_at") if latest_run else None,
            ),
            "last_attempt_count": None,
            "last_candidates_count": int(latest_run.get("matched_attachment_count") or 0) if latest_run else None,
            "last_created_count": int(latest_run.get("imported_invoice_count") or 0) if latest_run else None,
            "last_existing_count": int(latest_run.get("skipped_existing_count") or 0) if latest_run else None,
            "checked_message_count": int(latest_run.get("checked_message_count") or 0) if latest_run else 0,
            "matched_message_count": int(latest_run.get("matched_message_count") or 0) if latest_run else 0,
            "matched_attachment_count": int(latest_run.get("matched_attachment_count") or 0) if latest_run else 0,
            "imported_count": int(latest_run.get("imported_invoice_count") or 0) if latest_run else 0,
            "duplicate_count": int(latest_run.get("skipped_existing_count") or 0) if latest_run else 0,
            "failed_count": int(latest_run.get("skipped_error_count") or 0) if latest_run else 0,
            "total_imported_count": int(item_counts.get("imported_count") or 0),
            "total_duplicate_count": int(item_counts.get("duplicate_count") or 0),
            "total_failed_count": int(item_counts.get("failed_count") or 0),
            "runs_count": int(aggregates.get("runs_count") or 0),
            "recent_failure_count": int(aggregates.get("recent_failure_count") or 0),
            "last_success_at": aggregates.get("last_success_at"),
            "last_failure_at": aggregates.get("last_failure_at"),
            "last_error_code": last_error_code,
            "last_error_summary": last_error_summary,
            "configured_connections_count": 1 if organization_configured and mailbox_configured else 0,
            "enabled_connections_count": 1 if status == "enabled" else 0,
            "settings_url": "/ustawienia",
            "details_url": f"/automatyzacje/{self.automation_key}",
            "runtime_status": "unknown",
            "schedule": None,
            "updated_at": _email_import_run_time(latest_run),
        }
        AutomationOperationsRegistry.validate_operation(operation)
        return operation

    def get_history(self, *, organization_id: int, recipient_user_id: int, limit: int) -> list[dict[str, Any]]:
        del recipient_user_id
        return [
            _serialize_email_import_run(run)
            for run in self.repository.list_runs_read_only(organization_id=organization_id, limit=limit)
        ]


class KSeFImportOperationsAdapter:
    automation_key = KSEF_IMPORT_KEY
    scope = "organization"
    capabilities = frozenset({"summary", "history", "settings"})

    def __init__(self, repository: KSeFImportRepository) -> None:
        self.repository = repository

    def get_operation(self, *, organization_id: int, recipient_user_id: int) -> dict[str, Any]:
        del recipient_user_id
        snapshot = self.repository.get_operations_snapshot(organization_id)
        organization = snapshot["organization"] or {}
        latest_run = snapshot["latest_run"]
        terminal_run = snapshot["latest_terminal_run"]
        aggregates = snapshot["aggregates"]
        item_counts = snapshot["item_counts"]
        integration_enabled = bool(int(organization.get("ksef_integration_enabled") or 0))
        organization_configured = bool(
            int(organization.get("is_active") or 0)
            and int(organization.get("has_company_identifier") or 0)
        )
        terminal_status = str(terminal_run.get("status") or "") or None if terminal_run else None
        status, health, reason = ksef_import_health(
            integration_enabled=integration_enabled,
            organization_configured=organization_configured,
            last_terminal_status=terminal_status,
        )
        latest_status = str(latest_run.get("status") or "") or None if latest_run else None
        last_error_code, last_error_summary = _ksef_import_error(terminal_status)
        operation = {
            "automation_key": self.automation_key,
            "automation_type": "ksef_import",
            "title": "Import KSeF",
            "description": "Monitoruje organizacyjny import KSeF bez ujawniania danych faktur ani konfiguracji połączenia.",
            "status": status,
            "enabled": status == "enabled",
            "health": health,
            "health_reason_code": reason,
            "schedule_id": None,
            "run_id": int(latest_run["ksef_import_run_id"]) if latest_run else None,
            "next_run_at": None,
            "last_run_at": _ksef_import_run_time(latest_run),
            "last_activity_at": _ksef_import_run_time(latest_run),
            "last_run_status": _ksef_import_run_status(latest_status),
            "last_run_duration_ms": _duration_ms(
                latest_run.get("started_at") if latest_run else None,
                latest_run.get("finished_at") if latest_run else None,
            ),
            "last_attempt_count": None,
            "last_candidates_count": int(latest_run.get("checked_document_count") or 0) if latest_run else None,
            "last_created_count": int(latest_run.get("imported_invoice_count") or 0) if latest_run else None,
            "last_existing_count": int(latest_run.get("skipped_existing_count") or 0) if latest_run else None,
            "checked_document_count": int(latest_run.get("checked_document_count") or 0) if latest_run else 0,
            "imported_count": int(latest_run.get("imported_invoice_count") or 0) if latest_run else 0,
            "duplicate_count": int(latest_run.get("skipped_existing_count") or 0) if latest_run else 0,
            "failed_count": int(latest_run.get("skipped_error_count") or 0) if latest_run else 0,
            "total_imported_count": int(item_counts.get("imported_count") or 0),
            "total_duplicate_count": int(item_counts.get("duplicate_count") or 0),
            "total_failed_count": int(item_counts.get("failed_count") or 0),
            "runs_count": int(aggregates.get("runs_count") or 0),
            "recent_failure_count": int(aggregates.get("recent_failure_count") or 0),
            "last_success_at": aggregates.get("last_success_at"),
            "last_failure_at": aggregates.get("last_failure_at"),
            "last_error_code": last_error_code,
            "last_error_summary": last_error_summary,
            "configured_connections_count": 1 if organization_configured else 0,
            "enabled_connections_count": 1 if status == "enabled" else 0,
            "settings_url": "/ustawienia",
            "details_url": f"/automatyzacje/{self.automation_key}",
            "runtime_status": "unknown",
            "schedule": None,
            "updated_at": _ksef_import_run_time(latest_run),
        }
        AutomationOperationsRegistry.validate_operation(operation)
        return operation

    def get_history(self, *, organization_id: int, recipient_user_id: int, limit: int) -> list[dict[str, Any]]:
        del recipient_user_id
        return [
            _serialize_ksef_import_run(run)
            for run in self.repository.list_runs_read_only(organization_id=organization_id, limit=limit)
        ]


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
        result = {
            "item": operation,
            "history": history,
            "history_limit": normalized_limit,
        }
        get_outbox = getattr(adapter, "get_outbox", None)
        if callable(get_outbox):
            result["outbox"] = get_outbox(
                organization_id=organization_id,
                recipient_user_id=recipient_user_id,
                limit=normalized_limit,
            )
        get_watchers = getattr(adapter, "get_watchers", None)
        if callable(get_watchers):
            result["watchers"] = get_watchers(
                organization_id=organization_id,
                recipient_user_id=recipient_user_id,
            )
        return result

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
    if _SENSITIVE_ERROR_TEXT.search(normalized) or _ABSOLUTE_PATH_TEXT.search(normalized):
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


def _latest_timestamp(*values: Any) -> str | None:
    timestamps = [str(value) for value in values if value]
    return max(timestamps) if timestamps else None


def _snapshot_time(snapshot: dict[str, Any] | None) -> str | None:
    if not snapshot:
        return None
    return snapshot.get("finished_at") or snapshot.get("updated_at")


def _knowledge_run_status(status: str | None) -> str | None:
    return {
        "pending": "pending",
        "processing": "running",
        "completed": "succeeded",
        "failed": "failed",
    }.get(str(status or ""))


def _email_import_run_status(status: str | None) -> str | None:
    if status == "running":
        return "running"
    if status in {"completed", "no_new_documents"}:
        return "succeeded"
    if status in {"failed", "completed_with_issues"}:
        return "failed"
    return None


def _ksef_import_run_status(status: str | None) -> str | None:
    return _email_import_run_status(status)


def _email_import_run_time(run: dict[str, Any] | None) -> str | None:
    if not run:
        return None
    return run.get("finished_at") or run.get("started_at")


def _email_import_error(status: str | None) -> tuple[str | None, str | None]:
    if status == "failed":
        return "email_import_failed", "Import e-maili zakończył się błędem. Sprawdź konfigurację połączenia."
    if status == "completed_with_issues":
        return "email_import_completed_with_issues", "Część dokumentów z importu e-mail wymaga uwagi."
    return None, None


def _ksef_import_run_time(run: dict[str, Any] | None) -> str | None:
    return _email_import_run_time(run)


def _ksef_import_error(status: str | None) -> tuple[str | None, str | None]:
    if status == "failed":
        return "ksef_import_failed", "Import KSeF zakończył się błędem. Sprawdź konfigurację integracji."
    if status == "completed_with_issues":
        return "ksef_import_completed_with_issues", "Część dokumentów z importu KSeF wymaga uwagi."
    return None, None


def _serialize_email_import_run(run: dict[str, Any]) -> dict[str, Any]:
    status = str(run.get("status") or "")
    error_code, error_summary = _email_import_error(status)
    return {
        "history_type": "email_import_run",
        "run_id": int(run["email_import_run_id"]),
        "trigger_mode": str(run.get("trigger_mode") or "manual"),
        "result_status": status,
        "status": _email_import_run_status(status) or "running",
        "started_at": run.get("started_at"),
        "finished_at": run.get("finished_at"),
        "duration_ms": _duration_ms(run.get("started_at"), run.get("finished_at")),
        "checked_message_count": int(run.get("checked_message_count") or 0),
        "matched_message_count": int(run.get("matched_message_count") or 0),
        "matched_attachment_count": int(run.get("matched_attachment_count") or 0),
        "imported_count": int(run.get("imported_invoice_count") or 0),
        "duplicate_count": int(run.get("skipped_existing_count") or 0),
        "failed_count": int(run.get("skipped_error_count") or 0),
        "error_code": error_code,
        "error_summary": error_summary,
    }


def _serialize_ksef_import_run(run: dict[str, Any]) -> dict[str, Any]:
    status = str(run.get("status") or "")
    error_code, error_summary = _ksef_import_error(status)
    return {
        "history_type": "ksef_import_run",
        "run_id": int(run["ksef_import_run_id"]),
        "trigger_mode": str(run.get("trigger_mode") or "manual"),
        "result_status": status,
        "status": _ksef_import_run_status(status) or "running",
        "started_at": run.get("started_at"),
        "finished_at": run.get("finished_at"),
        "duration_ms": _duration_ms(run.get("started_at"), run.get("finished_at")),
        "checked_document_count": int(run.get("checked_document_count") or 0),
        "imported_count": int(run.get("imported_invoice_count") or 0),
        "duplicate_count": int(run.get("skipped_existing_count") or 0),
        "failed_count": int(run.get("skipped_error_count") or 0),
        "error_code": error_code,
        "error_summary": error_summary,
    }


def _serialize_knowledge_job(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "history_type": "knowledge_job",
        "job_id": int(job["knowledge_processing_job_id"]),
        "job_type": str(job.get("job_type") or "ingest"),
        "status": str(job["status"]),
        "attempt_count": int(job.get("attempts") or 0),
        "max_attempts": int(job.get("max_attempts") or 0),
        "created_at": job.get("created_at"),
        "started_at": job.get("started_at"),
        "finished_at": job.get("finished_at"),
        "duration_ms": _duration_ms(job.get("started_at"), job.get("finished_at")),
        "error_code": "knowledge_processing_failed" if job.get("error_message") else None,
        "error_summary": _safe_error_summary(job.get("error_message")),
    }


def _serialize_run(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "history_type": "scheduler_run",
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
