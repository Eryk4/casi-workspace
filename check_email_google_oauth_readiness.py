from __future__ import annotations

from typing import Any

from app.bootstrap import build_services
from app.config import EMAIL_GOOGLE_CLIENT_ID, EMAIL_GOOGLE_CLIENT_SECRET, PUBLIC_BASE_URL
from app.db import initialize_database


def evaluate_google_email_oauth_readiness(
    *,
    public_base_url: str,
    client_id: str,
    client_secret: str,
    connection: dict[str, Any] | None,
) -> dict[str, Any]:
    missing: list[str] = []
    if not public_base_url:
        missing.append("INVOICE_PUBLIC_BASE_URL")
    if not client_id:
        missing.append("INVOICE_EMAIL_GOOGLE_CLIENT_ID")
    if not client_secret:
        missing.append("INVOICE_EMAIL_GOOGLE_CLIENT_SECRET")

    uses_https = bool(public_base_url) and public_base_url.lower().startswith("https://")
    ready = not missing and uses_https
    connected = bool((connection or {}).get("google_email"))

    return {
        "ready": ready,
        "connected": connected,
        "missing": missing,
        "uses_https": uses_https,
        "public_base_url": public_base_url,
        "google_email": (connection or {}).get("google_email"),
    }


def main() -> int:
    initialize_database()
    services = build_services()
    invoice_service = services["invoice_service"]
    status = invoice_service.email_integration_info()
    connection = status.get("google_connection") or {}

    result = evaluate_google_email_oauth_readiness(
        public_base_url=PUBLIC_BASE_URL,
        client_id=EMAIL_GOOGLE_CLIENT_ID,
        client_secret=EMAIL_GOOGLE_CLIENT_SECRET,
        connection=connection,
    )

    print("=== Sprawdzenie gotowosci Google Workspace OAuth dla e-mail ===")

    if result["public_base_url"]:
        print(f"Publiczny adres aplikacji: {result['public_base_url']}")
    else:
        print("Publiczny adres aplikacji: brak")

    print(f"Client ID ustawiony: {'tak' if EMAIL_GOOGLE_CLIENT_ID else 'nie'}")
    print(f"Client Secret ustawiony: {'tak' if EMAIL_GOOGLE_CLIENT_SECRET else 'nie'}")
    print(f"Adres HTTPS: {'tak' if result['uses_https'] else 'nie'}")

    if result["missing"]:
        print("Brakujace ustawienia: " + ", ".join(result["missing"]))

    if result["public_base_url"] and not result["uses_https"]:
        print("Google OAuth wymaga publicznego adresu HTTPS. Obecny adres trzeba jeszcze poprawic.")

    if result["connected"]:
        print(f"Centralna skrzynka jest juz polaczona: {result['google_email']}")
    else:
        print("Centralna skrzynka nie jest jeszcze polaczona.")

    if result["ready"]:
        print("Google OAuth jest gotowy do uruchomienia autoryzacji.")
        if not result["connected"]:
            print("Nastepny krok: uruchom aplikacje pod publicznym HTTPS i kliknij 'Polacz Google Workspace'.")
        return 0

    print("Google OAuth nie jest jeszcze gotowy do autoryzacji.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
