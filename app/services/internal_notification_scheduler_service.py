from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

from app.domain.internal_notification_schedule import (
    DEFAULT_LOCAL_TIME,
    DEFAULT_TIMEZONE_NAME,
    SCHEDULE_CADENCE_DAILY,
    UTC,
    calculate_next_run_at_utc,
    next_run_after_local_date,
    normalize_now_utc,
    occurrence_for_due_schedule,
    utc_iso,
    validate_local_time,
    validate_timezone_name,
)
from app.repositories.event_repository import EventRepository
from app.repositories.internal_notification_schedule_repository import InternalNotificationScheduleRepository
from app.services.internal_notification_service import (
    INTERNAL_NOTIFICATION_SOURCE_BILLING_ATTENTION,
    InternalNotificationService,
)


class InternalNotificationSchedulerService:
    def __init__(
        self,
        *,
        repository: InternalNotificationScheduleRepository,
        notification_service: InternalNotificationService,
        event_repository: EventRepository,
        lease_minutes: int = 10,
        retry_minutes: int = 15,
        max_attempts: int = 3,
    ) -> None:
        self.repository = repository
        self.notification_service = notification_service
        self.event_repository = event_repository
        self.lease_minutes = max(1, int(lease_minutes))
        self.retry_minutes = max(1, int(retry_minutes))
        self.max_attempts = max(1, int(max_attempts))

    def get_settings(
        self,
        *,
        organization_id: int,
        recipient_user_id: int,
        actor_user: dict[str, Any],
    ) -> dict[str, Any]:
        self.notification_service.validate_recipient_scope(
            organization_id=organization_id,
            recipient_user_id=recipient_user_id,
            actor_user=actor_user,
            require_write=False,
        )
        schedule = self.repository.get_schedule(
            organization_id=organization_id,
            recipient_user_id=recipient_user_id,
            source_type=INTERNAL_NOTIFICATION_SOURCE_BILLING_ATTENTION,
        )
        return self._serialize_schedule(schedule, organization_id=organization_id, recipient_user_id=recipient_user_id)

    def save_settings(
        self,
        *,
        organization_id: int,
        recipient_user_id: int,
        actor_user: dict[str, Any],
        actor: str,
        enabled: bool,
        local_time: str,
        timezone_name: str,
        cadence: str = SCHEDULE_CADENCE_DAILY,
        now_utc: datetime | None = None,
    ) -> dict[str, Any]:
        self.notification_service.validate_recipient_scope(
            organization_id=organization_id,
            recipient_user_id=recipient_user_id,
            actor_user=actor_user,
            require_write=True,
        )
        if str(cadence or "").strip() != SCHEDULE_CADENCE_DAILY:
            raise ValueError("Scheduler v1 obsluguje wylacznie cadence daily.")
        normalized_time = validate_local_time(local_time)
        normalized_timezone = validate_timezone_name(timezone_name)
        current = normalize_now_utc(now_utc)
        existing = self.repository.get_schedule(
            organization_id=organization_id,
            recipient_user_id=recipient_user_id,
            source_type=INTERNAL_NOTIFICATION_SOURCE_BILLING_ATTENTION,
        )
        last_succeeded = (
            self.repository.last_succeeded_local_date(int(existing["internal_notification_schedule_id"]))
            if existing
            else None
        )
        next_run_at_utc = calculate_next_run_at_utc(
            enabled=bool(enabled),
            local_time=normalized_time,
            timezone_name=normalized_timezone,
            now_utc=current,
            last_succeeded_local_date=last_succeeded,
        )
        timestamp = utc_iso(current)
        stored = self.repository.upsert_schedule(
            {
                "organization_id": organization_id,
                "recipient_user_id": recipient_user_id,
                "source_type": INTERNAL_NOTIFICATION_SOURCE_BILLING_ATTENTION,
                "enabled": bool(enabled),
                "cadence": SCHEDULE_CADENCE_DAILY,
                "timezone_name": normalized_timezone,
                "local_time": normalized_time,
                "next_run_at_utc": next_run_at_utc,
                "created_by_user_id": int(actor_user["user_id"]),
                "updated_by_user_id": int(actor_user["user_id"]),
                "created_at": timestamp,
                "updated_at": timestamp,
            }
        )
        before = self._audit_snapshot(existing)
        after = self._audit_snapshot(stored)
        if before != after:
            self.event_repository.log(
                event_type="internal_notification_schedule_changed",
                invoice_id=None,
                organization_id=organization_id,
                source="INTERNAL_NOTIFICATION_SCHEDULER",
                status_before="enabled" if existing and int(existing.get("enabled") or 0) else "disabled",
                status_after="enabled" if enabled else "disabled",
                decision_reason="Jawnie zapisano ustawienia automatycznego sprawdzania powiadomien.",
                actor=actor,
                details={
                    "schedule_id": int(stored["internal_notification_schedule_id"]),
                    "recipient_user_id": recipient_user_id,
                    "source_type": INTERNAL_NOTIFICATION_SOURCE_BILLING_ATTENTION,
                    "before": before,
                    "after": after,
                },
            )
        return self._serialize_schedule(stored, organization_id=organization_id, recipient_user_id=recipient_user_id)

    def list_runs(
        self,
        *,
        organization_id: int,
        recipient_user_id: int,
        actor_user: dict[str, Any],
        limit: int = 20,
    ) -> dict[str, Any]:
        self.notification_service.validate_recipient_scope(
            organization_id=organization_id,
            recipient_user_id=recipient_user_id,
            actor_user=actor_user,
            require_write=False,
        )
        schedule = self.repository.get_schedule(
            organization_id=organization_id,
            recipient_user_id=recipient_user_id,
            source_type=INTERNAL_NOTIFICATION_SOURCE_BILLING_ATTENTION,
        )
        items = [] if not schedule else self.repository.list_runs(
            schedule_id=int(schedule["internal_notification_schedule_id"]),
            limit=limit,
        )
        return {
            "organization_id": organization_id,
            "recipient_user_id": recipient_user_id,
            "items": [self._serialize_run(item) for item in items],
        }

    def run_once(self, *, now_utc: datetime | None = None, limit: int = 100) -> dict[str, Any]:
        current = normalize_now_utc(now_utc)
        now_value = utc_iso(current)
        schedules = self.repository.list_due_schedules(now_utc=now_value, limit=limit)
        report: dict[str, Any] = {
            "status": "completed",
            "checked_schedules": len(schedules),
            "claimed_runs": 0,
            "succeeded_runs": 0,
            "failed_runs": 0,
            "skipped_runs": 0,
            "runs": [],
        }
        for schedule in schedules:
            outcome = self._run_schedule(schedule, now_utc=current)
            report["runs"].append(outcome)
            if outcome["status"] == "succeeded":
                report["claimed_runs"] += 1
                report["succeeded_runs"] += 1
            elif outcome["status"] == "failed":
                report["claimed_runs"] += 1
                report["failed_runs"] += 1
            else:
                report["skipped_runs"] += 1
        return report

    def _run_schedule(self, schedule: dict[str, Any], *, now_utc: datetime) -> dict[str, Any]:
        schedule_id = int(schedule["internal_notification_schedule_id"])
        occurrence = occurrence_for_due_schedule(
            local_time=str(schedule["local_time"]),
            timezone_name=str(schedule["timezone_name"]),
            now_utc=now_utc,
        )
        run, _ = self.repository.ensure_run(
            {
                "schedule_id": schedule_id,
                "organization_id": int(schedule["organization_id"]),
                "recipient_user_id": int(schedule["recipient_user_id"]),
                "source_type": str(schedule["source_type"]),
                "scheduled_local_date": occurrence.scheduled_local_date,
                "as_of_date": occurrence.as_of_date,
                "scheduled_for_utc": occurrence.scheduled_for_utc,
                "created_at": utc_iso(now_utc),
            }
        )
        run_id = int(run["internal_notification_schedule_run_id"])
        if str(run.get("status")) == "succeeded":
            self.repository.advance_schedule(
                schedule_id=schedule_id,
                next_run_at_utc=next_run_after_local_date(
                    completed_local_date=occurrence.scheduled_local_date,
                    local_time=str(schedule["local_time"]),
                    timezone_name=str(schedule["timezone_name"]),
                ),
                updated_at=utc_iso(now_utc),
            )
            return {"schedule_id": schedule_id, "run_id": run_id, "status": "skipped", "reason": "already_succeeded"}

        lease_token = uuid.uuid4().hex
        claimed = self.repository.claim_run(
            run_id=run_id,
            lease_token=lease_token,
            now_utc=utc_iso(now_utc),
            lease_expires_at_utc=utc_iso(now_utc + timedelta(minutes=self.lease_minutes)),
            max_attempts=self.max_attempts,
        )
        if not claimed:
            return {"schedule_id": schedule_id, "run_id": run_id, "status": "skipped", "reason": "not_claimable"}

        attempt_count = int(claimed["attempt_count"])
        try:
            self.notification_service.validate_recipient_scope(
                organization_id=int(schedule["organization_id"]),
                recipient_user_id=int(schedule["recipient_user_id"]),
                actor_user=None,
                require_write=True,
            )
            result = self.notification_service.materialize_billing_attention(
                organization_id=int(schedule["organization_id"]),
                recipient_user_id=int(schedule["recipient_user_id"]),
                trigger_actor_user=None,
                trigger_actor="internal-notification-scheduler",
                as_of_date=occurrence.as_of_date,
            )
            counts = {
                "candidates_count": int(result["candidates_count"]),
                "created_count": int(result["created_count"]),
                "existing_count": int(result["existing_count"]),
            }
            next_run = next_run_after_local_date(
                completed_local_date=occurrence.scheduled_local_date,
                local_time=str(schedule["local_time"]),
                timezone_name=str(schedule["timezone_name"]),
            )
            if not self.repository.mark_succeeded(
                run_id=run_id,
                lease_token=lease_token,
                counts=counts,
                finished_at=utc_iso(now_utc),
                next_run_at_utc=next_run,
            ):
                raise RuntimeError("Utracono lease runu przed zapisem sukcesu.")
            try:
                self.event_repository.log(
                    event_type="internal_notification_schedule_run_succeeded",
                    invoice_id=None,
                    organization_id=int(schedule["organization_id"]),
                    source="INTERNAL_NOTIFICATION_SCHEDULER",
                    status_before="running",
                    status_after="succeeded",
                    decision_reason="Scheduler utworzyl brakujace wewnetrzne powiadomienia przez centralny materializer.",
                    actor="internal-notification-scheduler",
                    details={
                        "schedule_id": schedule_id,
                        "run_id": run_id,
                        "recipient_user_id": int(schedule["recipient_user_id"]),
                        "source_type": str(schedule["source_type"]),
                        "as_of_date": occurrence.as_of_date,
                        **counts,
                    },
                )
            except Exception:
                # Run i materializacja sa juz trwale zakonczone. Opcjonalny audit
                # podsumowujacy nie moze zmienic sukcesu w falszywy retry.
                pass
            return {"schedule_id": schedule_id, "run_id": run_id, "status": "succeeded", "attempt_count": attempt_count, **counts}
        except Exception:
            terminal = attempt_count >= self.max_attempts
            next_attempt = None if terminal else utc_iso(now_utc + timedelta(minutes=self.retry_minutes))
            next_run = (
                next_run_after_local_date(
                    completed_local_date=occurrence.scheduled_local_date,
                    local_time=str(schedule["local_time"]),
                    timezone_name=str(schedule["timezone_name"]),
                )
                if terminal
                else None
            )
            self.repository.mark_failed(
                run_id=run_id,
                lease_token=lease_token,
                error_code="materialization_failed",
                error_summary="Nie udalo sie zmaterializowac wewnetrznych powiadomien.",
                finished_at=utc_iso(now_utc),
                next_attempt_at_utc=next_attempt,
                next_run_at_utc=next_run,
            )
            return {
                "schedule_id": schedule_id,
                "run_id": run_id,
                "status": "failed",
                "attempt_count": attempt_count,
                "will_retry": not terminal,
                "error_code": "materialization_failed",
            }

    @staticmethod
    def _audit_snapshot(schedule: dict[str, Any] | None) -> dict[str, Any] | None:
        if not schedule:
            return None
        return {
            "enabled": bool(int(schedule.get("enabled") or 0)),
            "cadence": str(schedule.get("cadence") or ""),
            "timezone_name": str(schedule.get("timezone_name") or ""),
            "local_time": str(schedule.get("local_time") or ""),
        }

    @staticmethod
    def _serialize_schedule(
        schedule: dict[str, Any] | None,
        *,
        organization_id: int,
        recipient_user_id: int,
    ) -> dict[str, Any]:
        if not schedule:
            return {
                "exists": False,
                "organization_id": organization_id,
                "recipient_user_id": recipient_user_id,
                "source_type": INTERNAL_NOTIFICATION_SOURCE_BILLING_ATTENTION,
                "enabled": False,
                "cadence": SCHEDULE_CADENCE_DAILY,
                "timezone_name": DEFAULT_TIMEZONE_NAME,
                "local_time": DEFAULT_LOCAL_TIME,
                "next_run_at_utc": None,
            }
        return {
            "exists": True,
            "internal_notification_schedule_id": int(schedule["internal_notification_schedule_id"]),
            "organization_id": int(schedule["organization_id"]),
            "recipient_user_id": int(schedule["recipient_user_id"]),
            "source_type": str(schedule["source_type"]),
            "enabled": bool(int(schedule["enabled"])),
            "cadence": str(schedule["cadence"]),
            "timezone_name": str(schedule["timezone_name"]),
            "local_time": str(schedule["local_time"]),
            "next_run_at_utc": schedule.get("next_run_at_utc"),
            "created_at": schedule.get("created_at"),
            "updated_at": schedule.get("updated_at"),
        }

    @staticmethod
    def _serialize_run(run: dict[str, Any]) -> dict[str, Any]:
        return {
            "internal_notification_schedule_run_id": int(run["internal_notification_schedule_run_id"]),
            "schedule_id": int(run["schedule_id"]),
            "organization_id": int(run["organization_id"]),
            "recipient_user_id": int(run["recipient_user_id"]),
            "source_type": str(run["source_type"]),
            "scheduled_local_date": str(run["scheduled_local_date"]),
            "as_of_date": str(run["as_of_date"]),
            "scheduled_for_utc": str(run["scheduled_for_utc"]),
            "status": str(run["status"]),
            "attempt_count": int(run["attempt_count"]),
            "candidates_count": run.get("candidates_count"),
            "created_count": run.get("created_count"),
            "existing_count": run.get("existing_count"),
            "error_code": run.get("error_code"),
            "error_summary": run.get("error_summary"),
            "started_at": run.get("started_at"),
            "finished_at": run.get("finished_at"),
            "created_at": run.get("created_at"),
        }
