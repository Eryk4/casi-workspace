from __future__ import annotations

import threading


class EmailImportSchedulerLoop:
    def __init__(self, invoice_service, interval_seconds: int) -> None:
        self.invoice_service = invoice_service
        self.interval_seconds = max(60, int(interval_seconds))
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> bool:
        if not self.invoice_service:
            return False
        status = self.invoice_service.email_scheduler_status()
        if not status.get("active"):
            return False
        self._thread = threading.Thread(target=self._run, name="email-import-scheduler-loop", daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.invoice_service.run_email_scheduler_cycle(actor="system-email-scheduler")
            except Exception as error:  # pragma: no cover - ochrona procesu serwera
                print(f"Blad petli automatycznego sprawdzania e-mail: {error}")
            self._stop_event.wait(self.interval_seconds)
