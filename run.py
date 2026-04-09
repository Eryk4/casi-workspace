from __future__ import annotations

import argparse

from app.api.http_server import create_server
from app.bootstrap import build_services
from app.config import (
    ENABLE_DEMO_SEED,
    DEFAULT_ADMIN_LOGIN,
    DEFAULT_ADMIN_PASSWORD,
    SECURE_COOKIES,
    SQLITE_DB_PATH,
    STORAGE_ROOT,
    TELEGRAM_WEBHOOK_SECRET,
    database_label,
    telegram_integration_enabled,
    uses_postgresql,
)
from app.db import initialize_database, reset_database
from app.demo_seed import seed_demo_data


def main() -> None:
    parser = argparse.ArgumentParser(description="MVP panelu faktur firmowych.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reset", action="store_true", help="Resetuje skonfigurowaną bazę i seed demo.")
    args = parser.parse_args()

    if args.reset:
        reset_database()
    else:
        initialize_database()

    services = build_services()
    services["auth_service"].ensure_default_admin()
    if ENABLE_DEMO_SEED:
        seed_demo_data(services["invoice_service"], services["invoice_repository"])
    server = create_server(args.host, args.port, services)

    print(f"Serwer uruchomiony na http://{args.host}:{args.port}")
    print(f"Aktywna baza danych: {database_label()}")
    if not uses_postgresql():
        print(f"Plik lokalnej bazy SQLite: {SQLITE_DB_PATH}")
    print(f"Magazyn dokumentów i OCR: {STORAGE_ROOT}")
    print(f"Demo seed: {'włączony' if ENABLE_DEMO_SEED else 'wyłączony'}")
    print(f"Bezpieczne ciasteczka sesji: {'włączone' if SECURE_COOKIES else 'wyłączone'}")
    print(
        "Konto startowe administratora: "
        f"login {DEFAULT_ADMIN_LOGIN}, hasło {DEFAULT_ADMIN_PASSWORD}, "
        "jeśli baza jest pusta i nie nadpisano ich zmiennymi środowiskowymi."
    )

    if uses_postgresql() and DEFAULT_ADMIN_LOGIN == "admin" and DEFAULT_ADMIN_PASSWORD == "Admin1234":
        print("UWAGA: zmień domyślne dane administratora przed użyciem środowiska produkcyjnego.")

    if telegram_integration_enabled():
        print(f"Webhook Telegram: /api/telegram/webhook/{TELEGRAM_WEBHOOK_SECRET}")
    else:
        print("Webhook Telegram: wyłączony (brak tokenu bota lub sekretu webhooka).")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nZatrzymywanie serwera...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
