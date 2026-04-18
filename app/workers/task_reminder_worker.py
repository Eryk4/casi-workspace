from __future__ import annotations

import os
import threading


class TaskReminderSchedulerLoop:
    def __init__(self, reminder_service, interval_seconds: int) -> None:
        self.reminder_service = reminder_service
        self.interval_seconds = max(15, int(interval_seconds))
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> bool:
        if not self.reminder_service or not self.reminder_service.is_enabled():
            return False
        self._thread = threading.Thread(target=self._run, name="task-reminder-scheduler-loop", daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                result = self.reminder_service.enqueue_due_reminders(worker_name="scheduler-loop")
                self.reminder_service.record_worker_heartbeat(
                    worker_name="scheduler-loop",
                    worker_role="scheduler",
                    state="ok",
                    process_id=os.getpid(),
                    summary={**result, "queue": self.reminder_service.outbox_repository.count_statuses()},
                )
            except Exception as error:  # pragma: no cover - ochrona procesu serwera
                self.reminder_service.record_worker_heartbeat(
                    worker_name="scheduler-loop",
                    worker_role="scheduler",
                    state="error",
                    process_id=os.getpid(),
                    error_message=str(error),
                )
                print(f"Blad petli planowania przypomnien: {error}")
            self._stop_event.wait(self.interval_seconds)


class TaskReminderDeliveryLoop:
    def __init__(self, reminder_service, interval_seconds: int) -> None:
        self.reminder_service = reminder_service
        self.interval_seconds = max(5, int(interval_seconds))
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> bool:
        if not self.reminder_service or not self.reminder_service.is_enabled():
            return False
        self._thread = threading.Thread(target=self._run, name="task-reminder-delivery-loop", daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                result = self.reminder_service.process_due_reminders(worker_name="delivery-worker")
                self.reminder_service.record_worker_heartbeat(
                    worker_name="delivery-worker",
                    worker_role="delivery",
                    state="ok",
                    process_id=os.getpid(),
                    summary={**result, "queue": self.reminder_service.outbox_repository.count_statuses()},
                )
            except Exception as error:  # pragma: no cover - ochrona procesu serwera
                self.reminder_service.record_worker_heartbeat(
                    worker_name="delivery-worker",
                    worker_role="delivery",
                    state="error",
                    process_id=os.getpid(),
                    error_message=str(error),
                )
                print(f"Blad petli dostarczania przypomnien: {error}")
            self._stop_event.wait(self.interval_seconds)
