from __future__ import annotations

from app.bootstrap import build_services
from app.db import initialize_database
from app.integrations.email_ingestion import EmailIngestionError


def main() -> int:
    initialize_database()
    services = build_services()
    invoice_service = services["invoice_service"]
    invoice_repository = services["invoice_repository"]
    organization_repository = services["organization_repository"]

    print("=== Test polaczenia e-mail ===")
    status = invoice_service.email_integration_info()
    if not status.get("enabled"):
        print("IMAP nie jest jeszcze skonfigurowany na poziomie systemu.")
        print("Uzupelnij plik .env.local albo data/local.env.")
        return 1

    try:
        probe = invoice_service.email_adapter.test_connection(limit=5)
    except EmailIngestionError as error:
        print(f"Blad polaczenia: {error}")
        return 1

    print("Polaczenie IMAP OK.")
    print(f"Host: {probe['host']}")
    print(f"Port: {probe['port']}")
    print(f"Folder: {probe['folder']}")
    print(f"SSL: {'tak' if probe['use_ssl'] else 'nie'}")
    print(f"Login: {probe['username_masked']}")
    print(f"Wiadomosci widoczne w folderze: {probe['message_count']}")
    if probe["preview_uids"]:
        print("Ostatnie UID-y: " + ", ".join(probe["preview_uids"]))

    organizations = organization_repository.list_organizations()
    ready_organizations = [
        item
        for item in organizations
        if int(item.get("is_active") or 0) == 1
        and int(item.get("email_integration_enabled") or 0) == 1
        and str(item.get("email_inbox_address") or "").strip()
    ]

    print()
    if not ready_organizations:
        print("Brak aktywnych organizacji z wlaczona integracja e-mail.")
        print("Uzupelnij organizacje w panelu i kliknij potem 'Sprawdz e-mail'.")
        return 0

    print("=== Podglad organizacji gotowych do importu ===")
    for organization in ready_organizations:
        print(f"\n- {organization['name']} ({organization['email_inbox_address']})")
        try:
            candidates = invoice_service.email_adapter.fetch_invoice_candidates(organization)
        except EmailIngestionError as error:
            print(f"  Blad sprawdzania organizacji: {error}")
            continue

        new_count = 0
        known_count = 0
        for candidate in candidates:
            existing = invoice_repository.get_by_source_external_id(
                str(candidate.get("source_external_id") or ""),
                source="EMAIL",
                organization_id=int(organization["organization_id"]),
            )
            if existing:
                known_count += 1
            else:
                new_count += 1

        print(f"  Pasujace dokumenty: {len(candidates)}")
        print(f"  Nowe do importu: {new_count}")
        print(f"  Juz znane: {known_count}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
