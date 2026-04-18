from __future__ import annotations

from app.bootstrap import build_services
from app.config import EMAIL_GOOGLE_CLIENT_ID, EMAIL_GOOGLE_CLIENT_SECRET, PUBLIC_BASE_URL
from app.db import initialize_database


def _oauth_missing_settings() -> list[str]:
    missing: list[str] = []
    if not PUBLIC_BASE_URL:
        missing.append("INVOICE_PUBLIC_BASE_URL")
    if not EMAIL_GOOGLE_CLIENT_ID:
        missing.append("INVOICE_EMAIL_GOOGLE_CLIENT_ID")
    if not EMAIL_GOOGLE_CLIENT_SECRET:
        missing.append("INVOICE_EMAIL_GOOGLE_CLIENT_SECRET")
    return missing


def _print_google_oauth_section(status: dict[str, object], scheduler_status: dict[str, object]) -> None:
    print("=== Google Workspace OAuth ===")
    oauth_missing = _oauth_missing_settings()
    google_connection = status.get("google_connection") or {}

    if PUBLIC_BASE_URL and not PUBLIC_BASE_URL.lower().startswith("https://"):
        print("Publiczny adres aplikacji jest ustawiony, ale nie zaczyna sie od https://")
        print("Google OAuth dla skrzynki e-mail wymaga publicznego adresu HTTPS.")
    elif PUBLIC_BASE_URL:
        print(f"Publiczny adres aplikacji: {PUBLIC_BASE_URL}")

    if oauth_missing:
        print("Google OAuth: jeszcze niegotowe")
        print("Brakujace ustawienia: " + ", ".join(oauth_missing))
    else:
        print("Google OAuth: konfiguracja systemowa gotowa")

    if google_connection.get("google_email"):
        print(f"Polaczona centralna skrzynka: {google_connection.get('google_email')}")
    else:
        print("Centralna skrzynka Google Workspace nie jest jeszcze polaczona.")
        if not oauth_missing:
            print("Nastepny krok: uruchom aplikacje pod publicznym HTTPS i kliknij 'Polacz Google Workspace'.")

    if scheduler_status.get("enabled"):
        interval_seconds = int(scheduler_status.get("interval_seconds") or 0)
        print(f"Automatyczne sprawdzanie: wlaczone co {max(1, round(interval_seconds / 60))} min")
        if not scheduler_status.get("configured"):
            print("Stan automatu: czeka na globalna konfiguracje e-mail.")
    else:
        print("Automatyczne sprawdzanie: wylaczone")

    print()


def main() -> int:
    initialize_database()
    services = build_services()
    invoice_service = services["invoice_service"]
    organization_repository = services["organization_repository"]

    print("=== Sprawdzenie gotowosci modulu e-mail ===")
    status = invoice_service.email_integration_info()
    scheduler_status = invoice_service.email_scheduler_status()

    if status.get("enabled"):
        print("System e-mail: gotowy")
        print(f"Tryb: {status.get('mode')}")
        print(f"Folder domyslny: {status.get('folder')}")
        print(f"Limit pobran: {status.get('fetch_limit')}")
        if status.get("mailbox_address"):
            print(f"Centralna skrzynka: {status.get('mailbox_address')}")
    else:
        print("System e-mail: brak konfiguracji globalnej")
        print("Uzupelnij IMAP albo podlacz centralna skrzynke Google Workspace.")
        print("Do pierwszych testow lokalnych najprostsze jest .env.local z IMAP.")

    print()
    _print_google_oauth_section(status, scheduler_status)

    organizations = organization_repository.list_organizations()
    if not organizations:
        print("Brak organizacji w systemie.")
        return 1

    ready_count = 0
    for organization in organizations:
        name = organization["name"]
        active = int(organization.get("is_active") or 0) == 1
        inbox = str(organization.get("email_inbox_address") or "").strip()
        enabled = int(organization.get("email_integration_enabled") or 0) == 1
        tested_at = organization.get("email_last_connection_tested_at")
        tested_status = str(organization.get("email_last_connection_status") or "").strip()
        import_status = str(organization.get("email_last_check_status") or "").strip()

        blockers: list[str] = []
        next_steps: list[str] = []

        if not active:
            blockers.append("organizacja nieaktywna")
        if not inbox:
            blockers.append("brak skrzynki e-mail")
        if not enabled:
            blockers.append("integracja e-mail wylaczona")
        if status.get("enabled") is not True:
            blockers.append("brak globalnej konfiguracji e-mail")

        if inbox and status.get("enabled") is True and not tested_at:
            next_steps.append("kliknij 'Testuj polaczenie'")
        if tested_at and enabled and active and status.get("enabled") is True:
            next_steps.append("kliknij 'Sprawdz e-mail'")

        print(f"- {name}")
        if blockers:
            print("  Stan: jeszcze niegotowa")
            print("  Braki: " + ", ".join(blockers))
        else:
            ready_count += 1
            print("  Stan: gotowa do importu")

        if inbox:
            print(f"  Skrzynka: {inbox}")
        if tested_at:
            print(f"  Ostatni test polaczenia: {tested_at}")
        if tested_status:
            print(f"  Wynik testu polaczenia: {tested_status}")
        if import_status:
            print(f"  Ostatni wynik importu: {import_status}")
        if next_steps:
            print("  Nastepny krok: " + " -> ".join(next_steps))
        print()

    if status.get("enabled") is not True:
        return 1
    if ready_count == 0:
        print("Zadna organizacja nie jest jeszcze gotowa do importu e-mail.")
        return 1

    print(f"Gotowe organizacje do dalszego testu: {ready_count}")
    if not _oauth_missing_settings() and not (status.get("google_connection") or {}).get("google_email"):
        print("Google OAuth jest gotowy konfiguracyjnie. Po publicznym HTTPS mozesz polaczyc centralna skrzynke.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
