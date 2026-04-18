from __future__ import annotations

from getpass import getpass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOCAL_ENV_PATH = BASE_DIR / ".env.local"
EXAMPLE_ENV_PATH = BASE_DIR / ".env.local.example"
EMAIL_IMAP_KEYS = [
    "INVOICE_EMAIL_IMAP_HOST",
    "INVOICE_EMAIL_IMAP_PORT",
    "INVOICE_EMAIL_IMAP_USERNAME",
    "INVOICE_EMAIL_IMAP_PASSWORD",
    "INVOICE_EMAIL_IMAP_FOLDER",
    "INVOICE_EMAIL_IMAP_USE_SSL",
    "INVOICE_EMAIL_FETCH_LIMIT",
]
EMAIL_OAUTH_KEYS = [
    "INVOICE_PUBLIC_BASE_URL",
    "INVOICE_EMAIL_GOOGLE_CLIENT_ID",
    "INVOICE_EMAIL_GOOGLE_CLIENT_SECRET",
]
EMAIL_AUTOCHECK_KEYS = [
    "INVOICE_EMAIL_AUTOCHECK_ENABLED",
    "INVOICE_EMAIL_AUTOCHECK_SECONDS",
]
EMAIL_KEYS = EMAIL_IMAP_KEYS + EMAIL_OAUTH_KEYS + EMAIL_AUTOCHECK_KEYS


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def parse_env_values(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def build_updated_env_text(existing_text: str, email_values: dict[str, str]) -> str:
    preserved_lines: list[str] = []
    for raw_line in existing_text.splitlines():
        stripped = raw_line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in EMAIL_KEYS:
                continue
        preserved_lines.append(raw_line)

    while preserved_lines and not preserved_lines[-1].strip():
        preserved_lines.pop()

    email_block = [
        "# Ustawienia e-mail / IMAP",
        f"INVOICE_EMAIL_IMAP_HOST={email_values['INVOICE_EMAIL_IMAP_HOST']}",
        f"INVOICE_EMAIL_IMAP_PORT={email_values['INVOICE_EMAIL_IMAP_PORT']}",
        f"INVOICE_EMAIL_IMAP_USERNAME={email_values['INVOICE_EMAIL_IMAP_USERNAME']}",
        f"INVOICE_EMAIL_IMAP_PASSWORD={email_values['INVOICE_EMAIL_IMAP_PASSWORD']}",
        f"INVOICE_EMAIL_IMAP_FOLDER={email_values['INVOICE_EMAIL_IMAP_FOLDER']}",
        f"INVOICE_EMAIL_IMAP_USE_SSL={email_values['INVOICE_EMAIL_IMAP_USE_SSL']}",
        f"INVOICE_EMAIL_FETCH_LIMIT={email_values['INVOICE_EMAIL_FETCH_LIMIT']}",
        "",
        "# Automat sprawdzania skrzynki",
        f"INVOICE_EMAIL_AUTOCHECK_ENABLED={email_values.get('INVOICE_EMAIL_AUTOCHECK_ENABLED', '0')}",
        f"INVOICE_EMAIL_AUTOCHECK_SECONDS={email_values.get('INVOICE_EMAIL_AUTOCHECK_SECONDS', '300')}",
        "",
        "# Google Workspace OAuth dla centralnej skrzynki",
        f"INVOICE_PUBLIC_BASE_URL={email_values.get('INVOICE_PUBLIC_BASE_URL', '')}",
        f"INVOICE_EMAIL_GOOGLE_CLIENT_ID={email_values.get('INVOICE_EMAIL_GOOGLE_CLIENT_ID', '')}",
        f"INVOICE_EMAIL_GOOGLE_CLIENT_SECRET={email_values.get('INVOICE_EMAIL_GOOGLE_CLIENT_SECRET', '')}",
    ]

    final_lines = preserved_lines[:]
    if final_lines:
        final_lines.append("")
    final_lines.extend(email_block)
    return "\n".join(final_lines) + "\n"


def prompt_value(label: str, default: str, *, secret: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    prompt = f"{label}{suffix}: "
    if secret:
        entered = getpass(prompt)
    else:
        entered = input(prompt)
    entered = entered.strip()
    return entered or default


def main() -> int:
    existing_text = _read_text(LOCAL_ENV_PATH) or _read_text(EXAMPLE_ENV_PATH)
    existing_values = parse_env_values(existing_text)

    print("=== Konfigurator e-mail IMAP ===")
    print("Najczesciej dla Google Workspace / Gmail zostaw host imap.gmail.com i port 993.")
    print("Sekcja Google Workspace OAuth jest opcjonalna na start, ale warto przygotowac ja od razu.")
    print("Do przycisku 'Polacz Google Workspace' potrzebny jest publiczny adres aplikacji i dane klienta OAuth.")
    print()

    values = {
        "INVOICE_EMAIL_IMAP_HOST": prompt_value(
            "Host IMAP",
            existing_values.get("INVOICE_EMAIL_IMAP_HOST", "imap.gmail.com"),
        ),
        "INVOICE_EMAIL_IMAP_PORT": prompt_value(
            "Port IMAP",
            existing_values.get("INVOICE_EMAIL_IMAP_PORT", "993"),
        ),
        "INVOICE_EMAIL_IMAP_USERNAME": prompt_value(
            "Pelny adres skrzynki",
            existing_values.get("INVOICE_EMAIL_IMAP_USERNAME", ""),
        ),
        "INVOICE_EMAIL_IMAP_PASSWORD": prompt_value(
            "Haslo aplikacji Google",
            existing_values.get("INVOICE_EMAIL_IMAP_PASSWORD", ""),
            secret=True,
        ),
        "INVOICE_EMAIL_IMAP_FOLDER": prompt_value(
            "Folder skrzynki",
            existing_values.get("INVOICE_EMAIL_IMAP_FOLDER", "INBOX"),
        ),
        "INVOICE_EMAIL_IMAP_USE_SSL": prompt_value(
            "SSL (1 lub 0)",
            existing_values.get("INVOICE_EMAIL_IMAP_USE_SSL", "1"),
        ),
        "INVOICE_EMAIL_FETCH_LIMIT": prompt_value(
            "Limit sprawdzanych wiadomosci",
            existing_values.get("INVOICE_EMAIL_FETCH_LIMIT", "100"),
        ),
        "INVOICE_EMAIL_AUTOCHECK_ENABLED": prompt_value(
            "Automatyczne sprawdzanie skrzynki (1 lub 0)",
            existing_values.get("INVOICE_EMAIL_AUTOCHECK_ENABLED", "0"),
        ),
        "INVOICE_EMAIL_AUTOCHECK_SECONDS": prompt_value(
            "Co ile sekund uruchamiac automat",
            existing_values.get("INVOICE_EMAIL_AUTOCHECK_SECONDS", "300"),
        ),
        "INVOICE_PUBLIC_BASE_URL": prompt_value(
            "Publiczny adres aplikacji (do Google OAuth)",
            existing_values.get("INVOICE_PUBLIC_BASE_URL", ""),
        ),
        "INVOICE_EMAIL_GOOGLE_CLIENT_ID": prompt_value(
            "Google OAuth Client ID",
            existing_values.get("INVOICE_EMAIL_GOOGLE_CLIENT_ID", ""),
        ),
        "INVOICE_EMAIL_GOOGLE_CLIENT_SECRET": prompt_value(
            "Google OAuth Client Secret",
            existing_values.get("INVOICE_EMAIL_GOOGLE_CLIENT_SECRET", ""),
            secret=True,
        ),
    }

    updated_text = build_updated_env_text(_read_text(LOCAL_ENV_PATH), values)
    LOCAL_ENV_PATH.write_text(updated_text, encoding="utf-8")

    print()
    print(f"Zapisano ustawienia w: {LOCAL_ENV_PATH}")
    print("Nastepne kroki:")
    print("1. Uruchom '09 - Test polaczenia e-mail.bat'")
    print("2. Uruchom '10 - Sprawdz gotowosc e-mail.bat'")
    print("3. Jesli uzupelniles sekcje OAuth, uruchom '12 - Sprawdz gotowosc Google OAuth e-mail.bat'")
    print("4. W panelu organizacji kliknij 'Testuj polaczenie'")
    print("5. Potem kliknij 'Sprawdz e-mail'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
