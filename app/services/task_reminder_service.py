from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.integrations.telegram_bot import TelegramBotAdapter, TelegramBotError
from app.repositories.event_repository import EventRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.task_reminder_outbox_repository import TaskReminderOutboxRepository
from app.repositories.task_repository import TaskRepository
from app.utils import json_dumps, now_local_datetime_value


class TaskReminderService:
    def __init__(
        self,
        task_repository: TaskRepository,
        event_repository: EventRepository,
        outbox_repository: TaskReminderOutboxRepository,
        organization_repository: OrganizationRepository,
        telegram_adapter: TelegramBotAdapter,
        *,
        retry_minutes: int = 15,
        processing_timeout_minutes: int = 10,
        max_attempts: int = 5,
    ) -> None:
        self.task_repository = task_repository
        self.event_repository = event_repository
        self.outbox_repository = outbox_repository
        self.organization_repository = organization_repository
        self.telegram_adapter = telegram_adapter
        self.retry_minutes = max(1, int(retry_minutes))
        self.processing_timeout_minutes = max(1, int(processing_timeout_minutes))
        self.max_attempts = max(1, int(max_attempts))

    def is_enabled(self, *, organization_id: int | None = None) -> bool:
        if not self.telegram_adapter.can_send_messages():
            return False
        if organization_id is None:
            return True
        return self._organization_uses_telegram(organization_id)

    def integration_status(self, *, organization_id: int | None = None) -> dict[str, Any]:
        enabled = self.is_enabled(organization_id=organization_id)
        return {
            "enabled": enabled,
            "mode": "aktywny" if enabled else "wylaczony",
            "delivery_channel": "telegram" if enabled else None,
            "retry_minutes": self.retry_minutes,
            "processing_timeout_minutes": self.processing_timeout_minutes,
            "max_attempts": self.max_attempts,
            "queue": self.outbox_repository.count_statuses(organization_id=organization_id),
            "workers": self.outbox_repository.list_worker_heartbeats(),
        }

    def list_outbox_deliveries(
        self,
        *,
        limit: int = 25,
        organization_id: int | None = None,
        viewer_user_id: int | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        return self.outbox_repository.list_deliveries(
            limit=limit,
            organization_id=organization_id,
            viewer_user_id=viewer_user_id,
            status=status,
        )

    def retry_outbox_delivery(
        self,
        outbox_id: int,
        *,
        organization_id: int | None,
        viewer_user_id: int | None,
        actor: str,
    ) -> dict[str, Any] | None:
        requeued = self.outbox_repository.requeue_delivery(
            outbox_id,
            available_at=now_local_datetime_value(),
            reason="Reczne ponowienie przez operatora.",
            organization_id=organization_id,
            viewer_user_id=viewer_user_id,
        )
        if not requeued:
            return None

        task = self.task_repository.get_by_id(
            int(requeued["task_id"]),
            organization_id=organization_id,
            viewer_user_id=viewer_user_id,
        )
        if not task:
            return None

        task_id = int(task["task_id"])
        self.task_repository.create_history(
            {
                "task_id": task_id,
                "organization_id": int(task["organization_id"]),
                "action_type": "task_reminder_outbox_requeued",
                "actor": actor,
                "message": "Ponowiono wpis outboxa przypomnien.",
                "details": json_dumps(
                    {
                        "task_id": task_id,
                        "outbox_id": int(requeued["task_reminder_outbox_id"]),
                    }
                ),
            }
        )
        self.event_repository.log(
            event_type="task_reminder_outbox_requeued",
            invoice_id=None,
            organization_id=int(task["organization_id"]),
            source="TELEGRAM",
            status_before=str(requeued.get("status") or ""),
            status_after="queued",
            decision_reason="Reczne ponowienie wpisu outboxa przypomnien.",
            actor=actor,
            details={
                "task_id": task_id,
                "outbox_id": int(requeued["task_reminder_outbox_id"]),
            },
        )
        return requeued

    def record_worker_heartbeat(
        self,
        *,
        worker_name: str,
        worker_role: str,
        state: str,
        process_id: int | None = None,
        summary: dict[str, int] | None = None,
        error_message: str | None = None,
    ) -> None:
        summary = summary or {}
        queue = summary.get("queue") if isinstance(summary.get("queue"), dict) else {}
        self.outbox_repository.upsert_worker_heartbeat(
            worker_name=worker_name,
            worker_role=worker_role,
            state=state,
            process_id=process_id,
            processed_total=int(summary.get("processed") or 0),
            sent_total=int(summary.get("sent") or 0),
            failed_total=int(summary.get("failed") or 0),
            deferred_total=int(summary.get("deferred") or 0),
            retrying_total=int(summary.get("retrying") or 0),
            skipped_total=int(summary.get("skipped") or 0),
            queue_total=int(queue.get("total") or 0),
            queue_due=int(queue.get("due") or 0),
            queue_failed=int(queue.get("failed") or 0),
            error_message=error_message,
        )

    def dispatch_due_reminders(
        self,
        *,
        limit: int = 20,
        organization_id: int | None = None,
        viewer_user_id: int | None = None,
    ) -> dict[str, int]:
        enqueue_result = self.enqueue_due_reminders(
            limit=limit,
            organization_id=organization_id,
            viewer_user_id=viewer_user_id,
            force_requeue=True,
            worker_name="manual-dispatch",
        )
        process_result = self.process_due_reminders(
            limit=limit,
            organization_id=organization_id,
            viewer_user_id=viewer_user_id,
            worker_name="manual-dispatch",
        )
        return {
            "processed": process_result["processed"],
            "sent": process_result["sent"],
            "failed": process_result["failed"] + enqueue_result["failed"],
            "deferred": process_result["deferred"] + enqueue_result["deferred"],
            "queued": enqueue_result["queued"],
            "skipped": process_result["skipped"] + enqueue_result["skipped"],
            "retrying": process_result["retrying"],
        }

    def enqueue_due_reminders(
        self,
        *,
        limit: int = 20,
        organization_id: int | None = None,
        viewer_user_id: int | None = None,
        force_requeue: bool = False,
        worker_name: str = "scheduler",
    ) -> dict[str, int]:
        if not self.is_enabled(organization_id=organization_id):
            return {"evaluated": 0, "queued": 0, "deferred": 0, "failed": 0, "skipped": 0}

        tasks = self.task_repository.list_due_reminders_for_dispatch(
            due_before=now_local_datetime_value(),
            retry_before=self._retry_before_value(),
            limit=limit,
            organization_id=organization_id,
            viewer_user_id=viewer_user_id,
        )
        result = {"evaluated": 0, "queued": 0, "deferred": 0, "failed": 0, "skipped": 0}

        for task in tasks:
            result["evaluated"] += 1
            if not self._task_uses_telegram(task):
                result["skipped"] += 1
                continue
            recipient = self._resolve_recipient(task)
            if not recipient:
                recipient = self._fallback_recipient(task)
                delivery_key = self._delivery_key(task, recipient)
                existing = self.outbox_repository.find_delivery_by_key(
                    int(task["task_id"]),
                    "telegram",
                    delivery_key,
                )
                if existing and str(existing.get("status") or "") == "failed" and int(existing.get("retryable") or 0) == 0:
                    result["skipped"] += 1
                    continue
                self._mark_failed(task, now_local_datetime_value(), "Brak odbiorcy przypomnienia Telegram.", actor=worker_name)
                self.outbox_repository.upsert_delivery(
                    {
                        "organization_id": int(task["organization_id"]),
                        "task_id": int(task["task_id"]),
                        "delivery_channel": "telegram",
                        "delivery_key": delivery_key,
                        "delivery_anchor_at": self._delivery_anchor_value(task),
                        "recipient_user_id": int(recipient["user_id"]),
                        "recipient_telegram_user_id": "",
                        "available_at": now_local_datetime_value(),
                        "status": "failed",
                        "retryable": 0,
                        "payload": json_dumps(
                            {
                                "task_id": int(task["task_id"]),
                                "task_title": task.get("title") or "",
                                "delivery_channel": "telegram",
                                "delivery_anchor_at": self._delivery_anchor_value(task),
                                "recipient_user_id": int(recipient["user_id"]),
                                "recipient_name": recipient["display_name"],
                                "available_at": now_local_datetime_value(),
                                "error": "Brak odbiorcy przypomnienia Telegram.",
                            }
                        ),
                    },
                    force_requeue=force_requeue,
                )
                result["failed"] += 1
                continue
            if not self._is_automatic_reminder_cycle_due(task, recipient):
                result["skipped"] += 1
                continue

            available_at = self._next_delivery_at(task, recipient)
            payload = self._build_outbox_payload(task, recipient, available_at=available_at)
            upserted = self.outbox_repository.upsert_delivery(payload, force_requeue=force_requeue)
            if str(upserted.get("status") or "") == "failed" and int(upserted.get("retryable") or 0) == 0 and not force_requeue:
                result["skipped"] += 1
                continue
            result["queued"] += 1
            if str(upserted.get("available_at") or "") > now_local_datetime_value():
                result["deferred"] += 1

        return result

    def process_due_reminders(
        self,
        *,
        limit: int = 20,
        organization_id: int | None = None,
        viewer_user_id: int | None = None,
        worker_name: str = "worker",
    ) -> dict[str, int]:
        if not self.is_enabled(organization_id=organization_id):
            return {"processed": 0, "sent": 0, "failed": 0, "deferred": 0, "skipped": 0, "retrying": 0}

        deliveries = self.outbox_repository.claim_due_deliveries(
            limit=limit,
            worker_name=worker_name,
            processing_timeout_minutes=self.processing_timeout_minutes,
            organization_id=organization_id,
            viewer_user_id=viewer_user_id,
        )
        result = {"processed": 0, "sent": 0, "failed": 0, "deferred": 0, "skipped": 0, "retrying": 0}

        for delivery in deliveries:
            result["processed"] += 1
            outcome = self._process_outbox_delivery(delivery, worker_name=worker_name)
            result[outcome] += 1

        return result

    def send_reminder_now(
        self,
        task_id: int,
        *,
        organization_id: int | None,
        viewer_user_id: int | None,
        actor: str,
    ) -> dict[str, Any] | None:
        if not self.is_enabled(organization_id=organization_id):
            raise ValueError("Wysylka przypomnien Telegram jest obecnie wylaczona.")

        task = self.task_repository.get_by_id(
            task_id,
            organization_id=organization_id,
            viewer_user_id=viewer_user_id,
        )
        if not task:
            return None
        if not self._task_uses_telegram(task):
            raise ValueError("Ta organizacja ma aktywny inny komunikator niz Telegram.")
        if not str(task.get("remind_at") or "").strip():
            raise ValueError("Ten wpis nie ma ustawionego przypomnienia.")
        if str(task.get("status") or "") in {"zakonczone", "anulowane"}:
            raise ValueError("Nie mozna wyslac przypomnienia dla zamknietego wpisu.")

        self._send_task_reminder(task, actor=actor, manual=True, raise_on_error=True)
        refreshed = self.task_repository.get_by_id(
            task_id,
            organization_id=organization_id,
            viewer_user_id=viewer_user_id,
        )
        return dict(refreshed) if refreshed else None

    def _retry_before_value(self) -> str:
        return (
            datetime.strptime(now_local_datetime_value(), "%Y-%m-%dT%H:%M") - timedelta(minutes=self.retry_minutes)
        ).strftime("%Y-%m-%dT%H:%M")

    def _retry_delay_minutes(self, attempt_count: int) -> int:
        attempt_count = max(1, int(attempt_count))
        delay = self.retry_minutes * (2 ** max(0, attempt_count - 1))
        return min(delay, self.retry_minutes * 8)

    def _delivery_anchor_value(self, task: dict[str, Any]) -> str:
        reminder_sent_at = str(task.get("reminder_sent_at") or "").strip()
        if reminder_sent_at:
            return reminder_sent_at
        return str(task.get("remind_at") or "").strip()

    def _delivery_key(self, task: dict[str, Any], recipient: dict[str, Any]) -> str:
        return f"telegram:{int(task['task_id'])}:{self._delivery_anchor_value(task)}:{int(recipient['user_id'])}"

    def _next_delivery_at(self, task: dict[str, Any], recipient: dict[str, Any]) -> str:
        if self._is_in_quiet_hours(recipient):
            return self._quiet_hours_resume_value(recipient)
        return now_local_datetime_value()

    def _quiet_hours_resume_value(self, recipient: dict[str, Any]) -> str:
        quiet_start = self._parse_clock(recipient.get("quiet_hours_start"))
        quiet_end = self._parse_clock(recipient.get("quiet_hours_end"))
        if quiet_start is None or quiet_end is None or quiet_start == quiet_end:
            return now_local_datetime_value()

        now_dt = datetime.now().replace(second=0, microsecond=0)
        now_clock = now_dt.strftime("%H:%M")
        if quiet_start < quiet_end:
            resume_dt = now_dt.replace(hour=int(quiet_end[:2]), minute=int(quiet_end[3:5]))
            return resume_dt.strftime("%Y-%m-%dT%H:%M")

        resume_dt = now_dt.replace(hour=int(quiet_end[:2]), minute=int(quiet_end[3:5]))
        if now_clock >= quiet_start:
            resume_dt += timedelta(days=1)
        return resume_dt.strftime("%Y-%m-%dT%H:%M")

    def _build_outbox_payload(
        self,
        task: dict[str, Any],
        recipient: dict[str, Any],
        *,
        available_at: str,
    ) -> dict[str, Any]:
        anchor_at = self._delivery_anchor_value(task)
        return {
            "organization_id": int(task["organization_id"]),
            "task_id": int(task["task_id"]),
            "delivery_channel": "telegram",
            "delivery_key": self._delivery_key(task, recipient),
            "delivery_anchor_at": anchor_at,
            "recipient_user_id": int(recipient["user_id"]),
            "recipient_telegram_user_id": str(recipient.get("telegram_user_id") or "").strip(),
            "available_at": available_at,
            "status": "queued",
            "retryable": 1,
            "payload": json_dumps(
                {
                    "task_id": int(task["task_id"]),
                    "task_title": task.get("title") or "",
                    "delivery_channel": "telegram",
                    "delivery_anchor_at": anchor_at,
                    "recipient_user_id": int(recipient["user_id"]),
                    "recipient_name": recipient["display_name"],
                    "available_at": available_at,
                }
            ),
        }

    def _fallback_recipient(self, task: dict[str, Any]) -> dict[str, Any]:
        recipient_user_id = int(task.get("assigned_user_id") or task.get("owner_user_id") or 0)
        if recipient_user_id <= 0:
            raise ValueError("Brak odbiorcy przypomnienia Telegram.")
        display_name = task.get("assigned_user_name") or task.get("owner_user_name") or f"Uzytkownik {recipient_user_id}"
        return {
            "user_id": recipient_user_id,
            "display_name": display_name,
            "telegram_user_id": str(task.get("assigned_telegram_user_id") or task.get("owner_telegram_user_id") or "").strip(),
            "quiet_hours_start": task.get("assigned_reminder_quiet_hours_start") or task.get("owner_reminder_quiet_hours_start"),
            "quiet_hours_end": task.get("assigned_reminder_quiet_hours_end") or task.get("owner_reminder_quiet_hours_end"),
            "repeat_interval_minutes": int(
                task.get("assigned_reminder_repeat_interval_minutes")
                or task.get("owner_reminder_repeat_interval_minutes")
                or 0
            ),
        }

    def _is_automatic_reminder_cycle_due(self, task: dict[str, Any], recipient: dict[str, Any]) -> bool:
        reminder_sent_at = self._parse_local_datetime(task.get("reminder_sent_at"))
        if reminder_sent_at is None:
            return True

        repeat_interval = int(recipient.get("repeat_interval_minutes") or 0)
        if repeat_interval <= 0:
            return False
        return datetime.now().replace(second=0, microsecond=0) >= reminder_sent_at + timedelta(minutes=repeat_interval)

    def _process_outbox_delivery(self, delivery: dict[str, Any], *, worker_name: str) -> str:
        attempted_at = now_local_datetime_value()
        task = self.task_repository.get_by_id(int(delivery["task_id"]), organization_id=int(delivery["organization_id"]))
        if not task:
            self.outbox_repository.mark_cancelled(
                int(delivery["task_reminder_outbox_id"]),
                cancelled_at=attempted_at,
                reason="Zadanie nie istnieje.",
                worker_name=worker_name,
            )
            self.outbox_repository.create_attempt(
                outbox_id=int(delivery["task_reminder_outbox_id"]),
                organization_id=int(delivery["organization_id"]),
                task_id=int(delivery["task_id"]),
                delivery_channel=str(delivery["delivery_channel"]),
                attempt_no=int(delivery["attempt_count"] or 0),
                outcome="skipped",
                attempted_at=attempted_at,
                worker_name=worker_name,
                error_message="Zadanie nie istnieje.",
            )
            return "skipped"

        if not self._task_uses_telegram(task):
            error_message = "Organizacja korzysta z innego komunikatora niz Telegram."
            self.outbox_repository.mark_cancelled(
                int(delivery["task_reminder_outbox_id"]),
                cancelled_at=attempted_at,
                reason=error_message,
                worker_name=worker_name,
            )
            self.outbox_repository.create_attempt(
                outbox_id=int(delivery["task_reminder_outbox_id"]),
                organization_id=int(delivery["organization_id"]),
                task_id=int(delivery["task_id"]),
                delivery_channel=str(delivery["delivery_channel"]),
                attempt_no=int(delivery["attempt_count"] or 0),
                outcome="skipped",
                attempted_at=attempted_at,
                worker_name=worker_name,
                error_message=error_message,
            )
            return "skipped"

        recipient = self._resolve_recipient(task)
        if not recipient:
            error_message = "Brak odbiorcy przypomnienia Telegram."
            self._mark_failed(task, attempted_at, error_message, actor=worker_name)
            self.outbox_repository.mark_failed(
                int(delivery["task_reminder_outbox_id"]),
                failed_at=attempted_at,
                error_message=error_message,
                worker_name=worker_name,
                retryable=False,
            )
            self.outbox_repository.create_attempt(
                outbox_id=int(delivery["task_reminder_outbox_id"]),
                organization_id=int(delivery["organization_id"]),
                task_id=int(delivery["task_id"]),
                delivery_channel=str(delivery["delivery_channel"]),
                attempt_no=int(delivery["attempt_count"] or 0),
                outcome="failed",
                attempted_at=attempted_at,
                worker_name=worker_name,
                error_message=error_message,
            )
            return "failed"

        if not self._is_automatic_reminder_cycle_due(task, recipient):
            self.outbox_repository.mark_cancelled(
                int(delivery["task_reminder_outbox_id"]),
                cancelled_at=attempted_at,
                reason="Cykl przypomnienia nie jest jeszcze gotowy.",
                worker_name=worker_name,
            )
            self.outbox_repository.create_attempt(
                outbox_id=int(delivery["task_reminder_outbox_id"]),
                organization_id=int(delivery["organization_id"]),
                task_id=int(delivery["task_id"]),
                delivery_channel=str(delivery["delivery_channel"]),
                attempt_no=int(delivery["attempt_count"] or 0),
                outcome="skipped",
                attempted_at=attempted_at,
                worker_name=worker_name,
                error_message="Cykl przypomnienia nie jest jeszcze gotowy.",
            )
            return "skipped"

        if self._is_in_quiet_hours(recipient):
            retry_at = self._quiet_hours_resume_value(recipient)
            self.task_repository.mark_reminder_deferred(int(task["task_id"]), attempted_at)
            self.outbox_repository.mark_retry(
                int(delivery["task_reminder_outbox_id"]),
                retry_at=retry_at,
                error_message="Cisza nocna odbiorcy.",
                worker_name=worker_name,
            )
            self.outbox_repository.create_attempt(
                outbox_id=int(delivery["task_reminder_outbox_id"]),
                organization_id=int(delivery["organization_id"]),
                task_id=int(delivery["task_id"]),
                delivery_channel=str(delivery["delivery_channel"]),
                attempt_no=int(delivery["attempt_count"] or 0),
                outcome="deferred",
                attempted_at=attempted_at,
                worker_name=worker_name,
                error_message="Cisza nocna odbiorcy.",
                details={"retry_at": retry_at},
            )
            return "deferred"

        try:
            self._send_task_reminder(task, actor=worker_name, manual=False, raise_on_error=True)
        except ValueError as error:
            error_message = str(error).strip() or "Nieznany blad wysylki Telegram."
            retryable = not self._is_permanent_delivery_error(error_message)
            self.task_repository.update(
                int(task["task_id"]),
                {
                    "reminder_last_attempt_at": attempted_at,
                    "reminder_last_error": error_message,
                },
            )
            if retryable and int(delivery["attempt_count"] or 0) < self.max_attempts:
                retry_delay = self._retry_delay_minutes(int(delivery["attempt_count"] or 0))
                retry_at = (
                    datetime.strptime(now_local_datetime_value(), "%Y-%m-%dT%H:%M") + timedelta(minutes=retry_delay)
                ).strftime("%Y-%m-%dT%H:%M")
                self.outbox_repository.mark_retry(
                    int(delivery["task_reminder_outbox_id"]),
                    retry_at=retry_at,
                    error_message=error_message,
                    worker_name=worker_name,
                )
                self.outbox_repository.create_attempt(
                    outbox_id=int(delivery["task_reminder_outbox_id"]),
                    organization_id=int(delivery["organization_id"]),
                    task_id=int(delivery["task_id"]),
                    delivery_channel=str(delivery["delivery_channel"]),
                    attempt_no=int(delivery["attempt_count"] or 0),
                    outcome="retry",
                    attempted_at=attempted_at,
                    worker_name=worker_name,
                    error_message=error_message,
                    details={"retry_at": retry_at},
                )
                return "retrying"

            if retryable and int(delivery["attempt_count"] or 0) >= self.max_attempts:
                error_message = f"Osiagnieto limit prob ponowienia ({self.max_attempts}). {error_message}"
            self.outbox_repository.mark_failed(
                int(delivery["task_reminder_outbox_id"]),
                failed_at=attempted_at,
                error_message=error_message,
                worker_name=worker_name,
                retryable=False,
            )
            self.outbox_repository.create_attempt(
                outbox_id=int(delivery["task_reminder_outbox_id"]),
                organization_id=int(delivery["organization_id"]),
                task_id=int(delivery["task_id"]),
                delivery_channel=str(delivery["delivery_channel"]),
                attempt_no=int(delivery["attempt_count"] or 0),
                outcome="dead_letter" if retryable else "failed",
                attempted_at=attempted_at,
                worker_name=worker_name,
                error_message=error_message,
            )
            return "failed"

        self.outbox_repository.mark_sent(
            int(delivery["task_reminder_outbox_id"]),
            sent_at=attempted_at,
            worker_name=worker_name,
        )
        self.outbox_repository.create_attempt(
            outbox_id=int(delivery["task_reminder_outbox_id"]),
            organization_id=int(delivery["organization_id"]),
            task_id=int(delivery["task_id"]),
            delivery_channel=str(delivery["delivery_channel"]),
            attempt_no=int(delivery["attempt_count"] or 0),
            outcome="sent",
            attempted_at=attempted_at,
            worker_name=worker_name,
        )
        return "sent"

    def _is_permanent_delivery_error(self, error_message: str) -> bool:
        normalized = error_message.lower()
        permanent_signals = (
            "chat not found",
            "bot was blocked",
            "user is deactivated",
            "forbidden",
            "not enough rights",
            "can't initiate conversation",
            "cannot initiate conversation",
            "brak identyfikatora czatu",
            "brak odbiorcy",
        )
        return any(signal in normalized for signal in permanent_signals)

    def _send_task_reminder(
        self,
        task: dict[str, Any],
        *,
        actor: str,
        manual: bool,
        raise_on_error: bool = False,
    ) -> bool:
        attempted_at = now_local_datetime_value()
        if not self._task_uses_telegram(task):
            error_message = "Ta organizacja ma aktywny inny komunikator niz Telegram."
            self._mark_failed(task, attempted_at, error_message, actor=actor)
            if raise_on_error:
                raise ValueError(error_message)
            return False
        recipient = self._resolve_recipient(task)
        if not recipient:
            error_message = "Brak odbiorcy przypomnienia Telegram."
            self._mark_failed(task, attempted_at, error_message, actor=actor)
            if raise_on_error:
                raise ValueError(error_message)
            return False

        chat_id = str(recipient.get("telegram_user_id") or "").strip()
        if not chat_id:
            error_message = f"Uzytkownik {recipient['display_name']} nie ma przypisanego ID uzytkownika Telegram."
            self._mark_failed(task, attempted_at, error_message, actor=actor)
            if raise_on_error:
                raise ValueError(error_message)
            return False

        try:
            self.telegram_adapter.send_text_message(chat_id, self._build_message(task, recipient, manual=manual))
        except TelegramBotError as error:
            self._mark_failed(task, attempted_at, str(error), actor=actor)
            if raise_on_error:
                raise ValueError(str(error))
            return False

        task_id = int(task["task_id"])
        organization_id = int(task["organization_id"])
        self.task_repository.mark_reminder_sent(task_id, attempted_at)
        self.task_repository.create_history(
            {
                "task_id": task_id,
                "organization_id": organization_id,
                "action_type": "task_reminder_sent_manual" if manual else "task_reminder_sent",
                "actor": actor,
                "message": (
                    f"Wyslano przypomnienie Telegram recznie do uzytkownika {recipient['display_name']}."
                    if manual
                    else f"Wyslano przypomnienie Telegram do uzytkownika {recipient['display_name']}."
                ),
                "details": json_dumps(
                    {
                        "task_id": task_id,
                        "recipient_user_id": int(recipient["user_id"]),
                        "recipient_name": recipient["display_name"],
                        "chat_id": chat_id,
                        "manual": manual,
                    }
                ),
            }
        )
        self.event_repository.log(
            event_type="task_reminder_sent_manual" if manual else "task_reminder_sent",
            invoice_id=None,
            organization_id=organization_id,
            source="TELEGRAM",
            status_before=None,
            status_after=str(task.get("status") or ""),
            decision_reason=(
                f"Recznie wyslano przypomnienie dla wpisu: {task.get('title')}."
                if manual
                else f"Wyslano przypomnienie dla wpisu: {task.get('title')}."
            ),
            actor=actor,
            details={
                "task_id": task_id,
                "recipient_user_id": int(recipient["user_id"]),
                "recipient_name": recipient["display_name"],
                "manual": manual,
            },
        )
        return True

    def _organization_uses_telegram(self, organization_id: int | None) -> bool:
        if not organization_id:
            return True
        organization = self.organization_repository.get_by_id(int(organization_id))
        if not organization:
            return False
        return str(organization.get("communication_provider") or "telegram").strip().lower() == "telegram"

    def _task_uses_telegram(self, task: dict[str, Any]) -> bool:
        return self._organization_uses_telegram(int(task.get("organization_id") or 0))

    def _resolve_recipient(self, task: dict[str, Any]) -> dict[str, Any] | None:
        assigned = self._build_recipient_candidate(task, actor_type="assigned")
        if assigned is not None:
            return assigned

        owner = self._build_recipient_candidate(task, actor_type="owner")
        if owner is not None:
            return owner
        return None

    def _build_recipient_candidate(self, task: dict[str, Any], *, actor_type: str) -> dict[str, Any] | None:
        if actor_type == "assigned":
            user_id = task.get("assigned_user_id")
            reminders_enabled = task.get("assigned_telegram_reminders_enabled")
            display_name = task.get("assigned_user_name")
            telegram_user_id = task.get("assigned_telegram_user_id")
            quiet_hours_start = task.get("assigned_reminder_quiet_hours_start")
            quiet_hours_end = task.get("assigned_reminder_quiet_hours_end")
            repeat_interval_minutes = task.get("assigned_reminder_repeat_interval_minutes")
        else:
            user_id = task.get("owner_user_id")
            reminders_enabled = task.get("owner_telegram_reminders_enabled")
            display_name = task.get("owner_user_name")
            telegram_user_id = task.get("owner_telegram_user_id")
            quiet_hours_start = task.get("owner_reminder_quiet_hours_start")
            quiet_hours_end = task.get("owner_reminder_quiet_hours_end")
            repeat_interval_minutes = task.get("owner_reminder_repeat_interval_minutes")

        if not user_id or not self._reminders_enabled(reminders_enabled, default=1):
            return None

        normalized_telegram_user_id = str(telegram_user_id or "").strip()
        if not normalized_telegram_user_id:
            return None

        return {
            "user_id": int(user_id),
            "display_name": display_name or f"Uzytkownik {user_id}",
            "telegram_user_id": normalized_telegram_user_id,
            "quiet_hours_start": quiet_hours_start,
            "quiet_hours_end": quiet_hours_end,
            "repeat_interval_minutes": int(repeat_interval_minutes or 0),
        }

    def _should_send_automatic_reminder(self, task: dict[str, Any], recipient: dict[str, Any]) -> bool:
        if self._is_in_quiet_hours(recipient):
            return False

        reminder_sent_at = self._parse_local_datetime(task.get("reminder_sent_at"))
        if reminder_sent_at is None:
            return True

        repeat_interval = int(recipient.get("repeat_interval_minutes") or 0)
        if repeat_interval <= 0:
            return False
        return datetime.now().replace(second=0, microsecond=0) >= reminder_sent_at + timedelta(minutes=repeat_interval)

    def _is_in_quiet_hours(self, recipient: dict[str, Any]) -> bool:
        quiet_start = self._parse_clock(recipient.get("quiet_hours_start"))
        quiet_end = self._parse_clock(recipient.get("quiet_hours_end"))
        if quiet_start is None or quiet_end is None or quiet_start == quiet_end:
            return False
        now_clock = datetime.now().strftime("%H:%M")
        if quiet_start < quiet_end:
            return quiet_start <= now_clock < quiet_end
        return now_clock >= quiet_start or now_clock < quiet_end

    def _parse_clock(self, value: Any) -> str | None:
        normalized = str(value or "").strip()
        if len(normalized) == 5 and normalized[2] == ":":
            hours, minutes = normalized.split(":", 1)
            if hours.isdigit() and minutes.isdigit():
                return normalized
        return None

    def _parse_local_datetime(self, value: Any) -> datetime | None:
        normalized = str(value or "").strip()
        if not normalized:
            return None
        try:
            return datetime.strptime(normalized, "%Y-%m-%dT%H:%M")
        except ValueError:
            return None

    def _build_message(self, task: dict[str, Any], recipient: dict[str, Any], *, manual: bool) -> str:
        type_label = {
            "zadanie": "Zadanie",
            "wydarzenie": "Wydarzenie",
            "przypomnienie": "Przypomnienie",
            "notatka": "Notatka",
        }.get(str(task.get("task_type") or ""), "Wpis")
        priority_label = {
            "niski": "Niski",
            "normalny": "Normalny",
            "wysoki": "Wysoki",
            "krytyczny": "Krytyczny",
        }.get(str(task.get("priority") or ""), str(task.get("priority") or "-"))

        lines = [
            "Reczne przypomnienie" if manual else f"Przypomnienie: {type_label}",
            f"Tytul: {task.get('title') or '-'}",
            f"Dla: {recipient['display_name']}",
        ]
        if manual:
            lines.append(f"Typ: {type_label}")
        if task.get("organization_name"):
            lines.append(f"Organizacja: {task['organization_name']}")
        if task.get("due_at"):
            lines.append(f"Termin: {task['due_at']}")
        if task.get("remind_at"):
            lines.append(f"Godzina przypomnienia: {task['remind_at']}")
        lines.append(f"Priorytet: {priority_label}")

        description = str(task.get("description") or "").strip()
        if description:
            if len(description) > 220:
                description = description[:217].rstrip() + "..."
            lines.append(f"Opis: {description}")
        return "\n".join(lines)

    def _mark_failed(self, task: dict[str, Any], attempted_at: str, error_message: str, *, actor: str) -> None:
        normalized_error = (str(error_message or "").strip() or "Nieznany blad wysylki.")[:300]
        task_id = int(task["task_id"])
        organization_id = int(task["organization_id"])

        self.task_repository.mark_reminder_failed(task_id, attempted_at, normalized_error)
        self.task_repository.create_history(
            {
                "task_id": task_id,
                "organization_id": organization_id,
                "action_type": "task_reminder_failed",
                "actor": actor,
                "message": f"Nie udalo sie wyslac przypomnienia Telegram: {normalized_error}",
                "details": json_dumps(
                    {
                        "task_id": task_id,
                        "error": normalized_error,
                    }
                ),
            }
        )
        self.event_repository.log(
            event_type="task_reminder_failed",
            invoice_id=None,
            organization_id=organization_id,
            source="TELEGRAM",
            status_before=None,
            status_after=str(task.get("status") or ""),
            decision_reason=normalized_error,
            actor=actor,
            details={
                "task_id": task_id,
                "error": normalized_error,
            },
        )

    def _reminders_enabled(self, value: Any, *, default: int) -> bool:
        if value is None:
            return bool(default)
        return bool(int(value))
