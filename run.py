from __future__ import annotations

import argparse
import threading
import time

from app.api.http_server import create_server
from app.bootstrap import build_services
from app.config import (
    APP_RELEASE_ID,
    DATA_DIR,
    DEFAULT_ADMIN_LOGIN,
    DEFAULT_ADMIN_PASSWORD,
    DB_ENGINE,
    EMAIL_AUTOCHECK_SECONDS,
    ENABLE_DEMO_SEED,
    KNOWLEDGE_FOLDER_SCAN_SECONDS,
    KNOWLEDGE_PIPELINE_POLL_SECONDS,
    SECURE_COOKIES,
    SQLITE_DB_PATH,
    STORAGE_ROOT,
    TASK_REMINDER_POLL_SECONDS,
    TASK_REMINDER_WORKER_POLL_SECONDS,
    TELEGRAM_WEBHOOK_SECRET,
    database_label,
    default_login_hint_enabled,
    telegram_integration_enabled,
)
from app.db import initialize_database, reset_database
from app.demo_seed import seed_demo_data
from app.reset_guard import prepare_local_sandbox_reset_from_environment
from app.workers.email_import_worker import EmailImportSchedulerLoop
from app.workers.task_reminder_worker import TaskReminderDeliveryLoop, TaskReminderSchedulerLoop


def _is_missing_organizations_table_error(error: Exception) -> bool:
    message = str(error).lower()
    return 'relation "organizations" does not exist' in message or "no such table: organizations" in message


class KnowledgePipelineLoop:
    def __init__(self, knowledge_service, poll_seconds: int, scan_seconds: int) -> None:
        self.knowledge_service = knowledge_service
        self.poll_seconds = max(5, int(poll_seconds))
        self.scan_seconds = max(self.poll_seconds, int(scan_seconds))
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> bool:
        if not self.knowledge_service:
            return False
        self._thread = threading.Thread(target=self._run, name="knowledge-pipeline-loop", daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _run(self) -> None:
        elapsed_since_scan = self.scan_seconds
        while not self._stop_event.is_set():
            try:
                if elapsed_since_scan >= self.scan_seconds:
                    self.knowledge_service.scan_all_folders(actor="system")
                    elapsed_since_scan = 0
                self.knowledge_service.process_pending_jobs(limit=5)
            except Exception as error:  # pragma: no cover - ochrona procesu serwera
                print(f"Blad petli bazy wiedzy: {error}")
            self._stop_event.wait(self.poll_seconds)
            elapsed_since_scan += self.poll_seconds


def _print_environment_info() -> None:
    print(f"Wersja aplikacji: {APP_RELEASE_ID}")
    print(f"Aktywna baza danych: {database_label()}")
    print(f"Magazyn dokumentow i OCR: {STORAGE_ROOT}")
    print(f"Demo seed: {'wlaczony' if ENABLE_DEMO_SEED else 'wylaczony'}")
    print(f"Bezpieczne ciasteczka sesji: {'wlaczone' if SECURE_COOKIES else 'wylaczone'}")
    if default_login_hint_enabled():
        print(
            "Konto startowe administratora: "
            f"login {DEFAULT_ADMIN_LOGIN}, haslo {DEFAULT_ADMIN_PASSWORD}, "
            "jesli baza jest pusta i nie nadpisano ich zmiennymi srodowiskowymi."
        )
    if DEFAULT_ADMIN_LOGIN == "admin" and DEFAULT_ADMIN_PASSWORD == "Admin1234":
        print("UWAGA: zmien domyslne dane administratora przed uzyciem srodowiska produkcyjnego.")
    if telegram_integration_enabled():
        print(f"Webhook Telegram: /api/telegram/webhook/{TELEGRAM_WEBHOOK_SECRET}")
    else:
        print("Webhook Telegram: wylaczony (brak tokenu bota lub sekretu webhooka).")


def main() -> None:
    parser = argparse.ArgumentParser(description="MVP panelu faktur firmowych.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--mode",
        choices=("standalone", "web", "worker"),
        default="standalone",
        help=(
            "standalone uruchamia web i background w jednym procesie, "
            "web startuje tylko panel HTTP, worker uruchamia tylko petle tla."
        ),
    )
    parser.add_argument("--reset", action="store_true", help="Resetuje lokalny sandbox SQLite po guardrailu bezpieczenstwa.")
    args = parser.parse_args()

    print("[START] Inicjalizacja bazy...", flush=True)
    if args.reset:
        reset_plan = prepare_local_sandbox_reset_from_environment(
            db_engine=DB_ENGINE,
            sqlite_path=SQLITE_DB_PATH,
            data_dir=DATA_DIR,
        )
        if reset_plan.backup_path is not None:
            print(f"[OK] Backup lokalnej bazy przed resetem: {reset_plan.backup_path}", flush=True)
        else:
            print("[INFO] Brak istniejacego pliku SQLite do backupu przed resetem.", flush=True)
        reset_database()
    else:
        initialize_database()
    print("[OK] Inicjalizacja bazy zakonczona.", flush=True)

    print("[START] Budowanie serwisow...", flush=True)
    try:
        services = build_services()
    except Exception as error:
        if not _is_missing_organizations_table_error(error):
            raise
        print(
            "[WARN] Wykryto brak tabeli organizations podczas startu. "
            "Ponawiam inicjalizacje schematu i budowanie serwisow...",
            flush=True,
        )
        initialize_database()
        services = build_services()
    services["auth_service"].ensure_default_admin()
    print("[OK] Serwisy gotowe.", flush=True)
    if ENABLE_DEMO_SEED:
        print("[START] Seed danych demo...", flush=True)
        seed_demo_data(
            services["invoice_service"],
            services["invoice_repository"],
            task_service=services.get("task_service"),
            auth_service=services["auth_service"],
            billing_service=services.get("billing_service"),
            knowledge_service=services.get("knowledge_service"),
            calendar_service=services.get("calendar_service"),
            work_item_service=services.get("work_item_service"),
        )
        print("[OK] Seed danych demo zakonczony.", flush=True)

    _print_environment_info()

    reminder_scheduler_loop = None
    reminder_delivery_loop = None
    email_scheduler_loop = None
    knowledge_loop = None
    server = None

    if args.mode in {"standalone", "worker"}:
        email_scheduler_loop = EmailImportSchedulerLoop(
            services.get("invoice_service"),
            EMAIL_AUTOCHECK_SECONDS,
        )
        if email_scheduler_loop.start():
            print(f"Automatyczne sprawdzanie e-mail: wlaczone (co {EMAIL_AUTOCHECK_SECONDS} s).")
        else:
            scheduler_status = services["invoice_service"].email_scheduler_status()
            if scheduler_status.get("enabled") and not scheduler_status.get("configured"):
                print("Automatyczne sprawdzanie e-mail: czeka na konfiguracje IMAP.")
            else:
                print("Automatyczne sprawdzanie e-mail: wylaczone.")

    if args.mode in {"standalone", "worker"}:
        reminder_scheduler_loop = TaskReminderSchedulerLoop(
            services.get("task_reminder_service"),
            TASK_REMINDER_POLL_SECONDS,
        )
        if reminder_scheduler_loop.start():
            print(f"Planowanie przypomnien: wlaczone (co {TASK_REMINDER_POLL_SECONDS} s).")
        else:
            print("Planowanie przypomnien: wylaczone.")

    if args.mode in {"standalone", "worker"}:
        reminder_delivery_loop = TaskReminderDeliveryLoop(
            services.get("task_reminder_service"),
            TASK_REMINDER_WORKER_POLL_SECONDS,
        )
        delivery_started = reminder_delivery_loop.start()
        if delivery_started:
            print(f"Dostarczanie przypomnien: wlaczone (co {TASK_REMINDER_WORKER_POLL_SECONDS} s).")
        else:
            print("Dostarczanie przypomnien: wylaczone.")
            if args.mode == "worker":
                return

    if args.mode in {"standalone", "worker"}:
        knowledge_loop = KnowledgePipelineLoop(
            services.get("knowledge_service"),
            KNOWLEDGE_PIPELINE_POLL_SECONDS,
            KNOWLEDGE_FOLDER_SCAN_SECONDS,
        )
        if knowledge_loop.start():
            print(
                "Pipeline bazy wiedzy: wlaczony "
                f"(kolejka co {KNOWLEDGE_PIPELINE_POLL_SECONDS} s, skan folderow co {KNOWLEDGE_FOLDER_SCAN_SECONDS} s)."
            )
        else:
            print("Pipeline bazy wiedzy: wylaczony.")

    if args.mode in {"standalone", "web"}:
        server = create_server(args.host, args.port, services)
        print(f"Serwer uruchomiony na http://{args.host}:{args.port}")
    else:
        print("Tryb worker: bez serwera HTTP.")

    try:
        if server is not None:
            server.serve_forever()
        else:
            while True:
                time.sleep(3600)
    except KeyboardInterrupt:
        print("\nZatrzymywanie procesu...")
    finally:
        if email_scheduler_loop:
            email_scheduler_loop.stop()
        if reminder_scheduler_loop:
            reminder_scheduler_loop.stop()
        if reminder_delivery_loop:
            reminder_delivery_loop.stop()
        if knowledge_loop:
            knowledge_loop.stop()
        if server is not None:
            server.server_close()


if __name__ == "__main__":
    main()
