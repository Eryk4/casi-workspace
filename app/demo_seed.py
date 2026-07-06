from __future__ import annotations

import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from app.config import KNOWLEDGE_DIR
from app.config import DEFAULT_ADMIN_LOGIN, DEFAULT_ADMIN_PASSWORD
from app.domain.constants import MANAGER_ASSISTANT_MODULE
from app.repositories.invoice_repository import InvoiceRepository
from app.services.auth_service import AuthService
from app.services.billing_service import BillingService
from app.services.calendar_service import CalendarService
from app.services.invoice_service import InvoiceService
from app.services.knowledge_service import KnowledgeService
from app.repositories.organization_repository import OrganizationRepository
from app.services.task_service import TaskService
from app.services.work_item_service import WorkItemService


SEED_ORGANIZATIONS = [
    {
        "name": "CASI",
        "slug": "casi",
        "is_active": 1,
        "telegram_chat_id": "-100210001001",
        "telegram_chat_name": "CASI operacje",
        "email_inbox_address": "faktury@casi24.com",
        "email_allowed_sender": "powiadomienia@casi24.com",
        "email_subject_keyword": "faktura",
        "email_integration_enabled": 1,
        "enabled_modules": [MANAGER_ASSISTANT_MODULE],
        "demo_email_connection_status": "Polaczenie IMAP dziala poprawnie.",
        "demo_email_connection_minutes_ago": 35,
        "demo_email_check_status": "Brak nowych dokumentow e-mail do importu.",
        "demo_email_check_minutes_ago": 28,
    },
    {
        "name": "Misja Robotyka",
        "slug": "misja-robotyka",
        "is_active": 1,
        "telegram_chat_id": "-100210001002",
        "telegram_chat_name": "Misja Robotyka zespol",
        "email_inbox_address": "rozliczenia@misjarobotyka.pl",
        "email_allowed_sender": "faktury@robotyka.edu.pl",
        "email_subject_keyword": "robotyka",
        "email_integration_enabled": 1,
        "enabled_modules": [MANAGER_ASSISTANT_MODULE],
        "demo_email_connection_status": "Polaczenie IMAP dziala poprawnie.",
        "demo_email_connection_minutes_ago": 22,
        "demo_email_check_status": "Zaimportowano 3 nowe dokumenty e-mail.",
        "demo_email_check_minutes_ago": 18,
    },
    {
        "name": "Biuro Rachunkowe Alfa",
        "slug": "biuro-rachunkowe-alfa",
        "is_active": 1,
        "telegram_chat_id": "-100210001003",
        "telegram_chat_name": "Biuro Alfa dokumenty",
        "email_inbox_address": "klienci@biuroalfa.pl",
        "email_allowed_sender": "powiadomienia@klientpremium.pl",
        "email_subject_keyword": "vat",
        "email_integration_enabled": 1,
        "enabled_modules": [MANAGER_ASSISTANT_MODULE],
        "demo_email_connection_status": (
            "Nie udalo sie zalogowac do skrzynki IMAP. Sprawdz haslo aplikacji Google Workspace."
        ),
        "demo_email_connection_minutes_ago": 11,
        "demo_email_check_status": "Wymaga ponownego testu polaczenia przed importem.",
        "demo_email_check_minutes_ago": 11,
    },
    {
        "name": "Klient Archiwalny Demo",
        "slug": "klient-archiwalny-demo",
        "is_active": 0,
        "telegram_chat_id": "-100210001099",
        "telegram_chat_name": "Klient archiwalny demo",
        "email_inbox_address": "archiwum@klient-demo.pl",
        "email_allowed_sender": "archiwum@klient-demo.pl",
        "email_subject_keyword": "archiwum",
        "email_integration_enabled": 0,
    },
]

SEED_USERS = [
    {
        "login": "demo_operator",
        "display_name": "Operator Demo",
        "password": "Demo1234",
        "role": "operator",
        "telegram_user_id": "610001",
        "organization_slug": "organizacja-domyslna",
    },
    {
        "login": "demo_gosc",
        "display_name": "Gosc Demo",
        "password": "Demo1234",
        "role": "guest",
        "telegram_user_id": "610002",
        "organization_slug": "organizacja-domyslna",
    },
    {
        "login": "casi_admin",
        "display_name": "Administrator organizacji CASI",
        "password": "Casi1234",
        "role": "organization_admin",
        "telegram_user_id": "620001",
        "organization_slug": "casi",
    },
    {
        "login": "casi_ola",
        "display_name": "Ola CASI",
        "password": "Casi1234",
        "role": "coordinator",
        "telegram_user_id": "620002",
        "organization_slug": "casi",
    },
    {
        "login": "casi_gosc",
        "display_name": "Gosc CASI",
        "password": "Casi1234",
        "role": "guest",
        "telegram_user_id": "620003",
        "organization_slug": "casi",
    },
    {
        "login": "robotyka_admin",
        "display_name": "Administrator organizacji Robotyka",
        "password": "Robot1234",
        "role": "organization_admin",
        "telegram_user_id": "630001",
        "organization_slug": "misja-robotyka",
    },
    {
        "login": "robotyka_marek",
        "display_name": "Marek Robotyka",
        "password": "Robot1234",
        "role": "operator",
        "telegram_user_id": "630002",
        "organization_slug": "misja-robotyka",
    },
    {
        "login": "alfa_admin",
        "display_name": "Administrator organizacji Alfa",
        "password": "Alfa1234",
        "role": "organization_admin",
        "telegram_user_id": "640001",
        "organization_slug": "biuro-rachunkowe-alfa",
    },
    {
        "login": "alfa_ania",
        "display_name": "Ania Alfa",
        "password": "Alfa1234",
        "role": "operator",
        "telegram_user_id": "640002",
        "organization_slug": "biuro-rachunkowe-alfa",
    },
]


def _normalize_organization_slug(slug: object) -> str:
    value = str(slug or "").strip()
    if not value or value == "organizacja-domyslna":
        return OrganizationRepository.DEFAULT_ORGANIZATION_SLUG
    return value


def build_quick_login_presets() -> list[dict[str, str]]:
    organization_names = {
        str(item["slug"]): str(item["name"])
        for item in SEED_ORGANIZATIONS
        if str(item.get("is_active", 1)) != "0"
    }
    presets = [
        {
            "login": DEFAULT_ADMIN_LOGIN,
            "password": DEFAULT_ADMIN_PASSWORD,
            "display_name": "Wlasciciel systemu",
            "role": "system_owner",
            "organization_name": "Konto globalne",
        }
    ]
    for payload in SEED_USERS:
        presets.append(
            {
                "login": str(payload["login"]),
                "password": str(payload["password"]),
                    "display_name": str(payload["display_name"]),
                    "role": str(payload["role"]),
                    "organization_name": organization_names.get(
                        _normalize_organization_slug(payload.get("organization_slug")),
                        "Organizacja demo",
                    ),
                }
            )
    return presets


SEED_INVOICES = [
    {
        "incoming_date": "2026-04-01",
        "source": "KSeF",
        "file_name": "ksef_fv_biuroserwis_2026_04_01.xml",
        "document_type": "xml",
        "invoice_number": "FV/BS/01/04/2026",
        "ksef_number": "KSEF-2026-0001-PL",
        "issuer_nip": "1234567890",
        "issuer_name": "Biuro Serwis Sp. z o.o.",
        "issue_date": "2026-04-01",
        "sale_date": "2026-04-01",
        "gross_amount": 1999.99,
        "currency": "PLN",
        "status": "poprawna",
        "source_external_id": "ksef-fv-biuroserwis-2026-04-01",
        "notes": "Faktura potwierdzona w KSeF; nie wymaga reakcji wlasciciela.",
    },
    {
        "incoming_date": "2026-04-02",
        "source": "EMAIL",
        "file_name": "email_duplikat_ksef_biuroserwis_2026_04_02.pdf",
        "document_type": "pdf",
        "invoice_number": "FV/BS/01/04/2026",
        "ksef_number": "KSEF-2026-0001-PL",
        "issuer_nip": "1234567890",
        "issuer_name": "Biuro Serwis Sp. z o.o.",
        "issue_date": "2026-04-01",
        "sale_date": "2026-04-01",
        "gross_amount": 1999.99,
        "currency": "PLN",
        "status": "nowa",
        "source_external_id": "email-duplikat-ksef-2026-04-02",
        "source_sender_name": "faktury@biuroserwis.pl",
        "notes": "Ten sam numer KSeF dotarl drugim kanalem, dlatego sprawa wymaga tylko potwierdzenia duplikatu.",
    },
    {
        "incoming_date": "2026-04-03",
        "source": "EMAIL",
        "file_name": "email_fv_druksystem_2026_04_03.pdf",
        "document_type": "pdf",
        "invoice_number": "FV/DS/77/04/2026",
        "ksef_number": "",
        "issuer_nip": "9876543210",
        "issuer_name": "Druk-System S.A.",
        "issue_date": "2026-04-03",
        "sale_date": "2026-04-03",
        "gross_amount": 650.50,
        "currency": "PLN",
        "status": "weryfikacja",
        "source_external_id": "email-druksystem-2026-04-03",
        "source_sender_name": "ksiegowosc@druksystem.pl",
        "notes": "Faktura bazowa od stalego dostawcy materialow drukowanych.",
    },
    {
        "incoming_date": "2026-04-04",
        "source": "TELEGRAM",
        "file_name": "telegram_podejrzenie_duplikatu_druksystem_2026_04_04.jpg",
        "document_type": "zdjecie",
        "invoice_number": "FV/DS/77/04/2026",
        "ksef_number": "",
        "issuer_nip": "9876543210",
        "issuer_name": "Druk-System S.A.",
        "issue_date": "2026-04-04",
        "sale_date": "2026-04-04",
        "gross_amount": 650.50,
        "currency": "PLN",
        "status": "nowa",
        "source_external_id": "telegram-wiadomosc-2026-04-04-880",
        "source_sender_name": "druksystem_faktury",
        "source_sender_id": "77441002",
        "source_metadata": {
            "kanal": "Bot Telegram / Druk-System",
            "typ_wiadomosci": "upload_zdjecia",
        },
        "ocr_raw_text": (
            "Skan faktury Druk-System\n"
            "Numer faktury FV/DS/77/04/2026\n"
            "NIP 9876543210\n"
            "Kwota brutto 650.50 PLN\n"
        ),
        "ocr_confidence": 0.88,
        "notes": "Zdjecie z Telegrama wyglada na druga kopie tej samej faktury od Druk-System.",
    },
    {
        "incoming_date": "2026-04-05",
        "source": "TELEGRAM",
        "file_name": "telegram_nowy_kontrahent_2026_04_05.pdf",
        "document_type": "pdf",
        "invoice_number": "FV/NK/15/04/2026",
        "ksef_number": "",
        "issuer_nip": "5556667778",
        "issuer_name": "Nowy Kontrahent Logistics",
        "issue_date": "2026-04-05",
        "sale_date": "2026-04-05",
        "gross_amount": 812.30,
        "currency": "PLN",
        "status": "nowa",
        "source_external_id": "telegram-wiadomosc-2026-04-05-915",
        "source_sender_name": "nowy_kontrahent_logistics",
        "source_sender_id": "99812021",
        "source_metadata": {
            "kanal": "Bot Telegram / Nowi dostawcy",
            "typ_wiadomosci": "upload_pdf",
        },
        "ocr_raw_text": (
            "PDF z Telegrama\n"
            "Numer faktury FV/NK/15/04/2026\n"
            "NIP 5556667778\n"
            "Kwota brutto 812.30 PLN\n"
        ),
        "ocr_confidence": 0.91,
        "notes": "Nowy dostawca transportu wymaga sprawdzenia danych przed akceptacja kosztu.",
    },
]

SEED_EXTRA_INVOICES = [
    {
        "organization_slug": "organizacja-domyslna",
        "incoming_date": "2026-04-06",
        "source": "EMAIL",
        "file_name": "email_fv_marketing_2026_04_06.pdf",
        "document_type": "pdf",
        "invoice_number": "FV/MKT/04/2026",
        "ksef_number": "",
        "issuer_nip": "1122334455",
        "issuer_name": "Marketing Studio Sp. z o.o.",
        "issue_date": "2026-04-06",
        "sale_date": "2026-04-06",
        "gross_amount": 1490.00,
        "currency": "PLN",
        "status": "zaksiegowana",
        "source_external_id": "email-marketing-2026-04-06",
        "source_sender_name": "faktury@marketingstudio.pl",
        "notes": "Koszt kampanii wizerunkowej gotowy do rutynowego opisu.",
    },
    {
        "organization_slug": "casi",
        "incoming_date": "2026-04-07",
        "source": "KSeF",
        "file_name": "ksef_fv_casi_szkolenia_2026_04_07.xml",
        "document_type": "xml",
        "invoice_number": "FV/CASI/17/04/2026",
        "ksef_number": "KSEF-CASI-2026-0017",
        "issuer_nip": "6655443322",
        "issuer_name": "Szkolenia Biznesowe Pro Sp. z o.o.",
        "issue_date": "2026-04-07",
        "sale_date": "2026-04-07",
        "gross_amount": 3280.00,
        "currency": "PLN",
        "status": "zaksiegowana",
        "source_external_id": "ksef-casi-szkolenia-2026-04-07",
        "notes": "Szkolenie zespolu operacyjnego zostalo juz opisane i zaksiegowane.",
    },
    {
        "organization_slug": "casi",
        "incoming_date": "2026-04-08",
        "source": "EMAIL",
        "file_name": "email_fv_rekrutacja_casi_2026_04_08.pdf",
        "document_type": "pdf",
        "invoice_number": "FV/HR/08/2026",
        "ksef_number": "",
        "issuer_nip": "4433221100",
        "issuer_name": "HR Partner Advisory",
        "issue_date": "2026-04-08",
        "sale_date": "2026-04-08",
        "gross_amount": 890.50,
        "currency": "PLN",
        "status": "odrzucona",
        "source_external_id": "email-casi-hr-2026-04-08",
        "source_sender_name": "biuro@hrpartner.pl",
        "notes": "Koszt rekrutacyjny odrzucony po porownaniu z zaakceptowanym budzetem.",
    },
    {
        "organization_slug": "casi",
        "incoming_date": "2026-04-09",
        "source": "TELEGRAM",
        "file_name": "telegram_fv_casi_event_2026_04_09.jpg",
        "document_type": "zdjecie",
        "invoice_number": "FV/EVT/09/2026",
        "ksef_number": "",
        "issuer_nip": "3344556677",
        "issuer_name": "Event Support Polska",
        "issue_date": "2026-04-09",
        "sale_date": "2026-04-09",
        "gross_amount": 1240.00,
        "currency": "PLN",
        "status": "weryfikacja",
        "source_external_id": "telegram-casi-event-2026-04-09",
        "source_sender_name": "event_support_casi",
        "source_sender_id": "620900",
        "source_metadata": {
            "kanal": "Bot Telegram / CASI operacje",
            "typ_wiadomosci": "upload_zdjecia",
            "chat_id": "-100210001001",
        },
        "ocr_raw_text": (
            "Skan faktury Event Support Polska\n"
            "Numer faktury FV/EVT/09/2026\n"
            "NIP 3344556677\n"
            "Kwota brutto 1240.00 PLN\n"
        ),
        "ocr_confidence": 0.79,
        "notes": "Skan z wydarzenia wymaga dopisania projektu i osoby odpowiedzialnej.",
    },
    {
        "organization_slug": "misja-robotyka",
        "incoming_date": "2026-04-09",
        "source": "EMAIL",
        "file_name": "email_fv_lego_robotyka_2026_04_09.pdf",
        "document_type": "pdf",
        "invoice_number": "FV/MR/LEGO/04/2026",
        "ksef_number": "",
        "issuer_nip": "5566778899",
        "issuer_name": "Lego Edu Partner",
        "issue_date": "2026-04-09",
        "sale_date": "2026-04-09",
        "gross_amount": 2150.40,
        "currency": "PLN",
        "status": "poprawna",
        "source_external_id": "email-robotyka-lego-2026-04-09",
        "source_sender_name": "faktury@legoedu.pl",
        "notes": "Materialy edukacyjne dla grup robotyki sa zgodne z zamowieniem.",
    },
    {
        "organization_slug": "misja-robotyka",
        "incoming_date": "2026-04-10",
        "source": "TELEGRAM",
        "file_name": "telegram_fv_robotyka_transport_2026_04_10.jpg",
        "document_type": "zdjecie",
        "invoice_number": "FV/TR/44/04/2026",
        "ksef_number": "",
        "issuer_nip": "6677889900",
        "issuer_name": "Transport Edukacyjny SA",
        "issue_date": "2026-04-10",
        "sale_date": "2026-04-10",
        "gross_amount": 440.00,
        "currency": "PLN",
        "status": "weryfikacja",
        "source_external_id": "telegram-robotyka-transport-2026-04-10",
        "source_sender_name": "transport_robotyka",
        "source_sender_id": "630002",
        "source_metadata": {
            "kanal": "Bot Telegram / Instruktorzy",
            "typ_wiadomosci": "upload_zdjecia",
            "chat_id": "-100210001002",
        },
        "ocr_raw_text": (
            "Skan faktury Transport Edukacyjny\n"
            "Numer faktury FV/TR/44/04/2026\n"
            "NIP 6677889900\n"
            "Kwota brutto 440.00 PLN\n"
        ),
        "ocr_confidence": 0.82,
        "notes": "Transport na warsztaty wymaga potwierdzenia trasy przez koordynatora.",
    },
    {
        "organization_slug": "biuro-rachunkowe-alfa",
        "incoming_date": "2026-04-11",
        "source": "KSeF",
        "file_name": "ksef_fv_alfa_klient_2026_04_11.xml",
        "document_type": "xml",
        "invoice_number": "FV/ALFA/11/04/2026",
        "ksef_number": "KSEF-ALFA-2026-0011",
        "issuer_nip": "7788990011",
        "issuer_name": "Klient Premium Alfa sp. z o.o.",
        "issue_date": "2026-04-11",
        "sale_date": "2026-04-11",
        "gross_amount": 5120.90,
        "currency": "PLN",
        "status": "poprawna",
        "source_external_id": "ksef-alfa-klient-2026-04-11",
        "notes": "Poprawna faktura klienta prowadzona przez Biuro Alfa.",
    },
    {
        "organization_slug": "biuro-rachunkowe-alfa",
        "incoming_date": "2026-04-12",
        "source": "EMAIL",
        "file_name": "email_fv_alfa_media_2026_04_12.pdf",
        "document_type": "pdf",
        "invoice_number": "FV/MEDIA/12/2026",
        "ksef_number": "",
        "issuer_nip": "8899001122",
        "issuer_name": "Media Support Polska",
        "issue_date": "2026-04-12",
        "sale_date": "2026-04-12",
        "gross_amount": 620.10,
        "currency": "PLN",
        "status": "weryfikacja",
        "source_external_id": "email-alfa-media-2026-04-12",
        "source_sender_name": "fv@mediasupport.pl",
        "notes": "Koszt mediow klienta premium wymaga opisania przed zamknieciem miesiaca.",
    },
    {
        "organization_slug": "biuro-rachunkowe-alfa",
        "incoming_date": "2026-04-13",
        "source": "EMAIL",
        "file_name": "email_fv_alfa_consulting_2026_04_13.pdf",
        "document_type": "pdf",
        "invoice_number": "FV/CONS/13/2026",
        "ksef_number": "",
        "issuer_nip": "9011223344",
        "issuer_name": "Consulting Tax Advisory",
        "issue_date": "2026-04-13",
        "sale_date": "2026-04-13",
        "gross_amount": 1880.00,
        "currency": "PLN",
        "status": "zaksiegowana",
        "source_external_id": "email-alfa-consulting-2026-04-13",
        "source_sender_name": "faktury@consultingtax.pl",
        "notes": "Staly koszt doradztwa podatkowego jest juz opisany i zamkniety.",
    },
    {
        "organization_slug": "organizacja-domyslna",
        "incoming_date": "2026-04-14",
        "source": "EMAIL",
        "file_name": "email_fv_marketing_2026_04_14.pdf",
        "document_type": "pdf",
        "invoice_number": "FV/MKT/05/2026",
        "ksef_number": "",
        "issuer_nip": "1122334455",
        "issuer_name": "Marketing Studio Sp. z o.o.",
        "issue_date": "2026-04-14",
        "sale_date": "2026-04-14",
        "gross_amount": 980.00,
        "currency": "PLN",
        "status": "poprawna",
        "source_external_id": "email-marketing-2026-04-14",
        "source_sender_name": "faktury@marketingstudio.pl",
        "notes": "Druga faktura od tego samego kontrahenta, zeby bylo widac historie wspolpracy.",
    },
    {
        "organization_slug": "organizacja-domyslna",
        "incoming_date": "2026-04-15",
        "source": "EMAIL",
        "file_name": "email_fv_hosting_2026_04_15.pdf",
        "document_type": "pdf",
        "invoice_number": "FV/HOST/15/2026",
        "ksef_number": "",
        "issuer_nip": "2233445566",
        "issuer_name": "Hosting Core Polska",
        "issue_date": "2026-04-15",
        "sale_date": "2026-04-15",
        "gross_amount": 410.00,
        "currency": "PLN",
        "status": "nowa",
        "source_external_id": "email-hosting-2026-04-15",
        "source_sender_name": "billing@hostingcore.pl",
        "notes": "Nowy kontrahent do pokazania karty nowych podmiotow na pulpicie.",
    },
    {
        "organization_slug": "casi",
        "incoming_date": "2026-04-16",
        "source": "EMAIL",
        "file_name": "email_fv_casi_szkolenia_followup_2026_04_16.pdf",
        "document_type": "pdf",
        "invoice_number": "FV/CASI/24/04/2026",
        "ksef_number": "",
        "issuer_nip": "6655443322",
        "issuer_name": "Szkolenia Biznesowe Pro Sp. z o.o.",
        "issue_date": "2026-04-16",
        "sale_date": "2026-04-16",
        "gross_amount": 1760.00,
        "currency": "PLN",
        "status": "poprawna",
        "source_external_id": "email-casi-szkolenia-2026-04-16",
        "source_sender_name": "faktury@szkoleniabiznesowepro.pl",
        "notes": "Kolejna faktura od znanego kontrahenta, zeby karta kontrahenta nie byla pusta.",
    },
    {
        "organization_slug": "casi",
        "incoming_date": "2026-04-17",
        "source": "EMAIL",
        "file_name": "email_fv_travel_casi_2026_04_17.pdf",
        "document_type": "pdf",
        "invoice_number": "FV/TRAVEL/17/2026",
        "ksef_number": "",
        "issuer_nip": "7788112233",
        "issuer_name": "Travel Desk Polska",
        "issue_date": "2026-04-17",
        "sale_date": "2026-04-17",
        "gross_amount": 2330.00,
        "currency": "PLN",
        "status": "nowa",
        "source_external_id": "email-casi-travel-2026-04-17",
        "source_sender_name": "delegacje@traveldesk.pl",
        "notes": "Nowy kontrahent powiazany z obszarem delegacji CASI.",
    },
    {
        "organization_slug": "misja-robotyka",
        "incoming_date": "2026-04-18",
        "source": "EMAIL",
        "file_name": "email_fv_lego_robotyka_followup_2026_04_18.pdf",
        "document_type": "pdf",
        "invoice_number": "FV/MR/LEGO/05/2026",
        "ksef_number": "",
        "issuer_nip": "5566778899",
        "issuer_name": "Lego Edu Partner",
        "issue_date": "2026-04-18",
        "sale_date": "2026-04-18",
        "gross_amount": 1685.00,
        "currency": "PLN",
        "status": "zaksiegowana",
        "source_external_id": "email-robotyka-lego-2026-04-18",
        "source_sender_name": "faktury@legoedu.pl",
        "notes": "Dodatkowa faktura od stalego kontrahenta dla widoku kontrahentow.",
    },
    {
        "organization_slug": "biuro-rachunkowe-alfa",
        "incoming_date": "2026-04-19",
        "source": "EMAIL",
        "file_name": "email_fv_alfa_media_followup_2026_04_19.pdf",
        "document_type": "pdf",
        "invoice_number": "FV/MEDIA/19/2026",
        "ksef_number": "",
        "issuer_nip": "8899001122",
        "issuer_name": "Media Support Polska",
        "issue_date": "2026-04-19",
        "sale_date": "2026-04-19",
        "gross_amount": 710.20,
        "currency": "PLN",
        "status": "poprawna",
        "source_external_id": "email-alfa-media-2026-04-19",
        "source_sender_name": "fv@mediasupport.pl",
        "notes": "Druga faktura od tego samego kontrahenta dla bogatszego profilu klienta.",
    },
]

SEED_USER_CALENDARS = [
    {
        "owner_login": "admin",
        "display_name": "Kalendarz zarzadczy firmy",
        "calendar_kind": "organizacja",
        "organization_slug": "organizacja-domyslna",
        "default_duration_minutes": 45,
        "description": "Glowny kalendarz terminow operacyjnych i decyzji wlasciciela.",
        "is_active": 1,
    },
    {
        "owner_login": "admin",
        "display_name": "Prezentacje produktu",
        "calendar_kind": "prywatny",
        "organization_slug": "organizacja-domyslna",
        "default_duration_minutes": 50,
        "description": "Kalendarz rozmow z klientami, follow-upow i spotkan decyzyjnych.",
        "is_active": 1,
    },
    {
        "owner_login": "admin",
        "display_name": "Sprawy prywatne i wyjazdy",
        "calendar_kind": "rodzinny",
        "organization_slug": "organizacja-domyslna",
        "default_duration_minutes": 120,
        "description": "Drugi kalendarz administratora, zeby bylo widac rozne typy feedow i wpisow.",
        "is_active": 1,
    },
    {
        "owner_login": "casi_admin",
        "display_name": "CASI Operacje",
        "calendar_kind": "organizacja",
        "organization_slug": "casi",
        "default_duration_minutes": 60,
        "description": "Kalendarz terminow operacyjnych CASI: delegacje, spotkania i decyzje zespolu.",
        "is_active": 1,
    },
    {
        "owner_login": "casi_admin",
        "display_name": "CASI - rekrutacje i eventy",
        "calendar_kind": "inne",
        "organization_slug": "casi",
        "default_duration_minutes": 45,
        "description": "Kalendarz rekrutacji, spotkan kandydatow i wydarzen zespolowych CASI.",
        "is_active": 1,
    },
    {
        "owner_login": "casi_ola",
        "display_name": "Ola CASI - kalendarz sluzbowy",
        "calendar_kind": "inne",
        "organization_slug": "casi",
        "default_duration_minutes": 30,
        "description": "Osobisty kalendarz sluzbowy Oli: onboarding, dostepy i zadania operacyjne.",
        "is_active": 1,
    },
    {
        "owner_login": "robotyka_admin",
        "display_name": "Robotyka - grafik instruktorow",
        "calendar_kind": "organizacja",
        "organization_slug": "misja-robotyka",
        "default_duration_minutes": 90,
        "description": "Kalendarz zajec, zastepstw instruktorow i spotkan z rodzicami.",
        "is_active": 1,
    },
    {
        "owner_login": "robotyka_admin",
        "display_name": "Robotyka - archiwum",
        "calendar_kind": "inne",
        "organization_slug": "misja-robotyka",
        "default_duration_minutes": 60,
        "description": "Nieaktywny kalendarz pokazujacy stan archiwalny.",
        "is_active": 0,
    },
    {
        "owner_login": "alfa_admin",
        "display_name": "Biuro Alfa - terminy klientow",
        "calendar_kind": "organizacja",
        "organization_slug": "biuro-rachunkowe-alfa",
        "default_duration_minutes": 60,
        "description": "Kalendarz terminow klientowskich, VAT i akceptacji platnosci Biura Alfa.",
        "is_active": 1,
    },
    {
        "owner_login": "alfa_admin",
        "display_name": "Biuro Alfa - archiwum klientow",
        "calendar_kind": "inne",
        "organization_slug": "biuro-rachunkowe-alfa",
        "default_duration_minutes": 30,
        "description": "Nieaktywny kalendarz archiwalny pokazujacy stary harmonogram klientow.",
        "is_active": 0,
    },
]

SEED_TASK_SCENARIOS = [
    {
        "organization_slug": "organizacja-domyslna",
        "owner_login": "admin",
        "title": "Sprawdzic poranny przeglad operacyjny",
        "task_type": "zadanie",
        "visibility_scope": "organizacja",
        "status": "w_toku",
        "priority": "wysoki",
        "due_offset_days": 0,
        "due_hour": 14,
        "due_minute": 0,
        "remind_minutes_before": 60,
        "calendar_name": "Kalendarz zarzadczy firmy",
        "assigned_login": "demo_operator",
        "description": "Przejrzec poranne sygnaly: zalegle zadania, faktury do opisania i dokumenty wymagajace decyzji.",
        "notes": ["Wlasciciel chce zaczac dzien od trzech najpilniejszych spraw, nie od pelnej listy systemowej."],
        "attachment": {
            "file_name": "checklista_porannego_przegladu.txt",
            "content": "1. Sprawy pilne\n2. Faktury do opisania\n3. Dokumenty do decyzji\n4. Rzeczy do odlozenia\n",
        },
    },
    {
        "organization_slug": "organizacja-domyslna",
        "owner_login": "admin",
        "title": "Notatka strategiczna produktu",
        "task_type": "notatka",
        "visibility_scope": "prywatne",
        "status": "nowe",
        "priority": "normalny",
        "description": "Ta aplikacja pozostaje osobnym produktem, ale jest gotowa do dzialania we wspolnym ekosystemie.",
    },
    {
        "organization_slug": "organizacja-domyslna",
        "owner_login": "admin",
        "title": "Oddzwonic do klienta po brakujace dane do faktury",
        "task_type": "przypomnienie",
        "visibility_scope": "organizacja",
        "status": "nowe",
        "priority": "krytyczny",
        "due_offset_days": -1,
        "due_hour": 9,
        "due_minute": 0,
        "remind_minutes_before": 120,
        "calendar_name": "Prezentacje produktu",
        "assigned_login": "demo_operator",
        "description": "Klient nie uzupelnil numeru zamowienia, a faktura czeka na opis przed platnoscia.",
        "notes": ["Jesli numer zamowienia nie przyjdzie rano, przenies sprawdzanie platnosci na jutro."],
    },
    {
        "organization_slug": "organizacja-domyslna",
        "owner_login": "admin",
        "title": "Przygotowac liste spraw na rozmowe z wlascicielem",
        "task_type": "zadanie",
        "visibility_scope": "organizacja",
        "status": "nowe",
        "priority": "wysoki",
        "due_offset_days": 1,
        "due_hour": 10,
        "due_minute": 0,
        "remind_minutes_before": 90,
        "calendar_name": "Prezentacje produktu",
        "assigned_login": "demo_operator",
        "description": "Zebrac trzy decyzje operacyjne: ktore faktury opisac dzis, do kogo oddzwonic i co mozna odlozyc.",
    },
    {
        "organization_slug": "organizacja-domyslna",
        "owner_login": "admin",
        "title": "Przejrzec plan spokojnych usprawnien na weekend",
        "task_type": "wydarzenie",
        "visibility_scope": "prywatne",
        "status": "oczekuje",
        "priority": "normalny",
        "due_offset_days": 4,
        "due_hour": 11,
        "due_minute": 30,
        "remind_minutes_before": 60,
        "calendar_name": "Sprawy prywatne i wyjazdy",
        "description": "Niepilny przeglad usprawnien procesu, dobry do odlozenia po zamknieciu spraw dzisiejszych.",
    },
    {
        "organization_slug": "casi",
        "owner_login": "casi_admin",
        "title": "Przejrzec delegacje krajowe CASI",
        "task_type": "zadanie",
        "visibility_scope": "wybrane_osoby",
        "status": "nowe",
        "priority": "krytyczny",
        "due_offset_days": -1,
        "due_hour": 11,
        "due_minute": 0,
        "remind_minutes_before": 30,
        "calendar_name": "CASI Operacje",
        "assigned_login": "casi_ola",
        "visible_logins": ["casi_ola", "casi_gosc"],
        "description": "Sprawdzic komplet dokumentow i potwierdzic, kto ma zatwierdzic wyjazdy krajowe.",
        "notes": ["Do zadania dolaczono procedury z bazy wiedzy CASI."],
    },
    {
        "organization_slug": "casi",
        "owner_login": "casi_ola",
        "title": "Przygotowac onboarding operatora CASI",
        "task_type": "zadanie",
        "visibility_scope": "prywatne",
        "status": "w_toku",
        "priority": "normalny",
        "due_offset_days": 2,
        "due_hour": 10,
        "due_minute": 30,
        "remind_minutes_before": 45,
        "calendar_name": "Ola CASI - kalendarz sluzbowy",
        "description": "Zebrane dostepy, checklista wdrozeniowa i komplet informacji dla nowej osoby.",
        "attachment": {
            "file_name": "onboarding_casi.txt",
            "content": "Laptop\nKonto e-mail\nDostep do CRM\nSzkolenie z procedur delegacji\n",
        },
    },
    {
        "organization_slug": "casi",
        "owner_login": "casi_admin",
        "title": "Spotkanie operacyjne zespolu CASI",
        "task_type": "wydarzenie",
        "visibility_scope": "organizacja",
        "status": "oczekuje",
        "priority": "wysoki",
        "due_offset_days": 1,
        "due_hour": 9,
        "due_minute": 15,
        "remind_minutes_before": 20,
        "calendar_name": "CASI Operacje",
        "assigned_login": "casi_ola",
        "description": "Cotygodniowe spotkanie zespolu z przegladem delegacji, urlopow i nowych wnioskow.",
        "notes": ["Na spotkaniu trzeba domknac delegacje, urlopy i wnioski kosztowe przed koncem dnia."],
    },
    {
        "organization_slug": "casi",
        "owner_login": "casi_admin",
        "title": "Zweryfikowac harmonogram rekrutacji CASI",
        "task_type": "przypomnienie",
        "visibility_scope": "organizacja",
        "status": "w_toku",
        "priority": "wysoki",
        "due_offset_days": 0,
        "due_hour": 16,
        "due_minute": 0,
        "remind_minutes_before": 45,
        "calendar_name": "CASI - rekrutacje i eventy",
        "assigned_login": "casi_ola",
        "description": "Kandydat ma dzisiaj potwierdzic termin rozmowy, a zespol potrzebuje decyzji o kolejnym kroku.",
        "notes": ["Jesli kandydat nie odpowie do 16:00, przenies follow-up na jutro rano."],
    },
    {
        "organization_slug": "misja-robotyka",
        "owner_login": "robotyka_admin",
        "title": "Spotkanie z rodzicami grupy wtorkowej",
        "task_type": "wydarzenie",
        "visibility_scope": "organizacja",
        "status": "oczekuje",
        "priority": "normalny",
        "due_offset_days": 1,
        "due_hour": 17,
        "due_minute": 30,
        "remind_minutes_before": 60,
        "calendar_name": "Robotyka - grafik instruktorow",
        "description": "Omowienie frekwencji, platnosci i nowych zapisow na kolejny miesiac.",
    },
    {
        "organization_slug": "misja-robotyka",
        "owner_login": "robotyka_admin",
        "title": "Wyslac przypomnienie o platnosciach semestralnych",
        "task_type": "przypomnienie",
        "visibility_scope": "wybrane_osoby",
        "status": "nowe",
        "priority": "wysoki",
        "due_offset_days": 3,
        "due_hour": 9,
        "due_minute": 0,
        "remind_minutes_before": 15,
        "assigned_login": "robotyka_marek",
        "visible_logins": ["robotyka_marek"],
        "description": "Przypomnienie dla zespolu o wysylce informacji do rodzin z platnoscia semestralna.",
        "notes": ["Do komunikatu dolacz liste rodzin z saldem otwartym."],
    },
    {
        "organization_slug": "misja-robotyka",
        "owner_login": "robotyka_admin",
        "title": "Zweryfikowac grafik zastepstw instruktora",
        "task_type": "zadanie",
        "visibility_scope": "organizacja",
        "status": "zakonczone",
        "priority": "wysoki",
        "due_offset_days": -3,
        "due_hour": 8,
        "due_minute": 15,
        "remind_minutes_before": 30,
        "calendar_name": "Robotyka - grafik instruktorow",
        "description": "Zastepstwo instruktora zostalo potwierdzone, a wpis zostaje w historii dla kontekstu grafiku.",
    },
    {
        "organization_slug": "misja-robotyka",
        "owner_login": "robotyka_admin",
        "title": "Warsztaty pokazowe dla nowej szkoly",
        "task_type": "wydarzenie",
        "visibility_scope": "organizacja",
        "status": "nowe",
        "priority": "wysoki",
        "due_offset_days": 4,
        "due_hour": 16,
        "due_minute": 45,
        "remind_minutes_before": 120,
        "calendar_name": "Robotyka - grafik instruktorow",
        "description": "Ustalic materialy, sale i osobe prowadzaca przed wyslaniem zaproszenia do szkoly.",
    },
    {
        "organization_slug": "biuro-rachunkowe-alfa",
        "owner_login": "alfa_admin",
        "title": "Akceptacja listy platnosci klientow",
        "task_type": "zadanie",
        "visibility_scope": "organizacja",
        "status": "w_toku",
        "priority": "krytyczny",
        "due_offset_days": 0,
        "due_hour": 12,
        "due_minute": 30,
        "remind_minutes_before": 20,
        "calendar_name": "Biuro Alfa - terminy klientow",
        "assigned_login": "alfa_ania",
        "description": "Przejrzec wszystkie pozycje do platnosci i potwierdzic kolejke przelewow klientowskich.",
        "notes": ["Najpierw sprawdz priorytet klientow premium i dokumenty oczekujace weryfikacji."],
    },
    {
        "organization_slug": "biuro-rachunkowe-alfa",
        "owner_login": "alfa_admin",
        "title": "Oddzwonic do klienta w sprawie brakujacej umowy",
        "task_type": "zadanie",
        "visibility_scope": "wybrane_osoby",
        "status": "anulowane",
        "priority": "niski",
        "due_offset_days": 2,
        "due_hour": 15,
        "due_minute": 0,
        "remind_minutes_before": 30,
        "visible_logins": ["alfa_ania"],
        "description": "Sprawa zamknieta po doslaniu umowy przez klienta; zostaje w historii jako kontekst kontaktu.",
    },
    {
        "organization_slug": "biuro-rachunkowe-alfa",
        "owner_login": "alfa_ania",
        "title": "Notatka o obiegu dokumentow klienta premium",
        "task_type": "notatka",
        "visibility_scope": "prywatne",
        "status": "nowe",
        "priority": "niski",
        "description": "Klient premium wymaga dodatkowej akceptacji glównej ksiegowej przed wysylka dokumentow.",
    },
    {
        "organization_slug": "biuro-rachunkowe-alfa",
        "owner_login": "alfa_admin",
        "title": "Przygotowac zestawienie terminow VAT",
        "task_type": "przypomnienie",
        "visibility_scope": "organizacja",
        "status": "nowe",
        "priority": "wysoki",
        "due_offset_days": 1,
        "due_hour": 8,
        "due_minute": 45,
        "remind_minutes_before": 25,
        "calendar_name": "Biuro Alfa - terminy klientow",
        "assigned_login": "alfa_ania",
        "description": "Przypomnienie o przygotowaniu zestawienia terminow VAT i statusow dokumentow klientowskich.",
        "notes": ["Najpierw sprawdz klientow z dokumentami niekompletnymi, potem przygotuj podsumowanie dla zespolu."],
    },
    {
        "organization_slug": "biuro-rachunkowe-alfa",
        "owner_login": "alfa_admin",
        "title": "Spotkanie statusowe z klientem premium",
        "task_type": "wydarzenie",
        "visibility_scope": "organizacja",
        "status": "oczekuje",
        "priority": "normalny",
        "due_offset_days": 2,
        "due_hour": 13,
        "due_minute": 15,
        "remind_minutes_before": 30,
        "calendar_name": "Biuro Alfa - terminy klientow",
        "assigned_login": "alfa_ania",
        "description": "Pokazowy wpis kalendarzowy dla klienta premium z przypisana osoba i terminem.",
    },
]

SEED_BILLING_SCHOOLS = [
    {
        "organization_slug": "misja-robotyka",
        "full_name": "Szkola Podstawowa nr 4 w Bielsku Podlaskim",
        "short_name": "SP4 BP",
        "city": "Bielsk Podlaski",
    },
    {
        "organization_slug": "misja-robotyka",
        "full_name": "Szkola Podstawowa nr 5 w Bielsku Podlaskim",
        "short_name": "SP5 BP",
        "city": "Bielsk Podlaski",
    },
    {
        "organization_slug": "misja-robotyka",
        "full_name": "Szkola Podstawowa nr 3 w Bielsku Podlaskim",
        "short_name": "SP3 BP",
        "city": "Bielsk Podlaski",
    },
    {
        "organization_slug": "misja-robotyka",
        "full_name": "Niepubliczna Szkola Podstawowa Robotik",
        "short_name": "NSP Robotik",
        "city": "Bielsk Podlaski",
    },
]

SEED_BILLING_MODELS = [
    {
        "organization_slug": "misja-robotyka",
        "name": "26/27 Poniedzialek",
        "school_year": "2026/2027",
        "lesson_day": "poniedzialek",
        "settlement_mode": "monthly",
        "monthly_rate_amount": 57,
        "semester_rate_amount": 54,
        "sibling_discount_amount": 100,
        "large_family_discount_amount": 50,
        "intro_free_lessons_count": 1,
        "contract_required": 1,
        "notes": "Standardowy model miesieczny dla poniedzialkowych zajec szkolnych.",
    },
    {
        "organization_slug": "misja-robotyka",
        "name": "26/27 Wtorek",
        "school_year": "2026/2027",
        "lesson_day": "wtorek",
        "settlement_mode": "monthly",
        "monthly_rate_amount": 57,
        "semester_rate_amount": 54,
        "sibling_discount_amount": 100,
        "large_family_discount_amount": 50,
        "intro_free_lessons_count": 1,
        "contract_required": 1,
        "notes": "Standardowy model miesieczny dla wtorkowych zajec szkolnych.",
    },
    {
        "organization_slug": "misja-robotyka",
        "name": "26/27 Sroda Semestr",
        "school_year": "2026/2027",
        "lesson_day": "sroda",
        "settlement_mode": "semester",
        "monthly_rate_amount": 57,
        "semester_rate_amount": 54,
        "sibling_discount_amount": 100,
        "large_family_discount_amount": 50,
        "intro_free_lessons_count": 1,
        "contract_required": 1,
        "notes": "Model semestralny rozliczany z gory dla rodzin wybierajacych platnosc jednorazowa.",
    },
    {
        "organization_slug": "misja-robotyka",
        "name": "26/27 Piatek",
        "school_year": "2026/2027",
        "lesson_day": "piatek",
        "settlement_mode": "monthly",
        "monthly_rate_amount": 57,
        "semester_rate_amount": 54,
        "sibling_discount_amount": 100,
        "large_family_discount_amount": 50,
        "intro_free_lessons_count": 1,
        "contract_required": 1,
        "notes": "Model miesieczny dla piatkowych grup popoludniowych.",
    },
    {
        "organization_slug": "misja-robotyka",
        "name": "26/27 Wlasny Indywidualny",
        "school_year": "2026/2027",
        "lesson_day": "indywidualnie",
        "settlement_mode": "custom",
        "monthly_rate_amount": 65,
        "semester_rate_amount": 60,
        "sibling_discount_amount": 100,
        "large_family_discount_amount": 50,
        "intro_free_lessons_count": 1,
        "contract_required": 0,
        "notes": "Model indywidualny dla rodzin z niestandardowa liczba zajec.",
    },
]

SEED_BILLING_PAYERS = [
    {
        "organization_slug": "misja-robotyka",
        "display_name": "Rodzina Kruk",
        "contact_phone": "500600700",
        "has_large_family_card": 1,
        "email": "kruk@example.com",
        "notes": "Rodzina z KDR i dwojka dzieci w grupach miesiecznych.",
    },
    {
        "organization_slug": "misja-robotyka",
        "display_name": "Rodzina Nowak",
        "contact_phone": "501600700",
        "has_large_family_card": 0,
        "email": "nowak@example.com",
        "notes": "Rodzina z jednym uczniem w grupie wtorkowej.",
    },
    {
        "organization_slug": "misja-robotyka",
        "display_name": "Rodzina Zielinskich",
        "contact_phone": "502700800",
        "has_large_family_card": 0,
        "email": "zielinscy@example.com",
        "notes": "Rodzina z trojka dzieci i jednym przelewem zbiorczym.",
    },
    {
        "organization_slug": "misja-robotyka",
        "display_name": "Rodzina Adamskich",
        "contact_phone": "503700800",
        "has_large_family_card": 0,
        "email": "adamscy@example.com",
        "notes": "Rodzina rozliczana semestralnie z gory.",
    },
    {
        "organization_slug": "misja-robotyka",
        "display_name": "Rodzina Wisniewskich",
        "contact_phone": "504700800",
        "has_large_family_card": 0,
        "email": "wisniewscy@example.com",
        "notes": "Rodzina z indywidualnym modelem rozliczenia.",
    },
    {
        "organization_slug": "misja-robotyka",
        "display_name": "Rodzina Dabrowskich",
        "contact_phone": "505700800",
        "has_large_family_card": 0,
        "email": "dabrowscy@example.com",
        "notes": "Rodzina z pojedynczym dzieckiem w grupie piatkowej.",
    },
    {
        "organization_slug": "misja-robotyka",
        "display_name": "Rodzina Lewandowskich",
        "contact_phone": "506700800",
        "has_large_family_card": 0,
        "email": "lewandowscy@example.com",
        "notes": "Rodzina z nowym uczniem, ktora ma naliczenie oczekujace na pierwsza wplate.",
    },
]

SEED_BILLING_STUDENTS = [
    {
        "organization_slug": "misja-robotyka",
        "full_name": "Lena Kruk",
        "payer_phone": "500600700",
        "school_short_name": "SP4 BP",
        "model_name": "26/27 Wtorek",
        "family_billing_order": 1,
        "group_name": "Robotyka Wtorek A",
    },
    {
        "organization_slug": "misja-robotyka",
        "full_name": "Maja Kruk",
        "payer_phone": "500600700",
        "school_short_name": "SP4 BP",
        "model_name": "26/27 Wtorek",
        "family_billing_order": 2,
        "group_name": "Robotyka Wtorek A",
    },
    {
        "organization_slug": "misja-robotyka",
        "full_name": "Alicja Zielinska",
        "payer_phone": "502700800",
        "school_short_name": "SP3 BP",
        "model_name": "26/27 Poniedzialek",
        "family_billing_order": 1,
        "group_name": "Robotyka Poniedzialek A",
    },
    {
        "organization_slug": "misja-robotyka",
        "full_name": "Olek Zielinski",
        "payer_phone": "502700800",
        "school_short_name": "SP3 BP",
        "model_name": "26/27 Poniedzialek",
        "family_billing_order": 2,
        "group_name": "Robotyka Poniedzialek A",
    },
    {
        "organization_slug": "misja-robotyka",
        "full_name": "Zosia Zielinska",
        "payer_phone": "502700800",
        "school_short_name": "SP3 BP",
        "model_name": "26/27 Poniedzialek",
        "family_billing_order": 3,
        "group_name": "Robotyka Poniedzialek A",
    },
    {
        "organization_slug": "misja-robotyka",
        "full_name": "Igor Nowak",
        "payer_phone": "501600700",
        "school_short_name": "SP5 BP",
        "model_name": "26/27 Piatek",
        "family_billing_order": 1,
        "group_name": "Robotyka Piatek B",
    },
    {
        "organization_slug": "misja-robotyka",
        "full_name": "Julia Adamska",
        "payer_phone": "503700800",
        "school_short_name": "SP5 BP",
        "model_name": "26/27 Sroda Semestr",
        "family_billing_order": 1,
        "group_name": "Robotyka Sroda C",
    },
    {
        "organization_slug": "misja-robotyka",
        "full_name": "Filip Adamski",
        "payer_phone": "503700800",
        "school_short_name": "SP5 BP",
        "model_name": "26/27 Sroda Semestr",
        "family_billing_order": 2,
        "group_name": "Robotyka Sroda C",
    },
    {
        "organization_slug": "misja-robotyka",
        "full_name": "Milosz Wisniewski",
        "payer_phone": "504700800",
        "school_short_name": "NSP Robotik",
        "model_name": "26/27 Wlasny Indywidualny",
        "family_billing_order": 1,
        "group_name": "Robotyka Indywidualna",
    },
    {
        "organization_slug": "misja-robotyka",
        "full_name": "Hanna Dabrowska",
        "payer_phone": "505700800",
        "school_short_name": "NSP Robotik",
        "model_name": "26/27 Piatek",
        "family_billing_order": 1,
        "group_name": "Robotyka Piatek B",
    },
    {
        "organization_slug": "misja-robotyka",
        "full_name": "Tymon Lewandowski",
        "payer_phone": "506700800",
        "school_short_name": "NSP Robotik",
        "model_name": "26/27 Piatek",
        "family_billing_order": 1,
        "group_name": "Robotyka Piatek B",
    },
]

SEED_BILLING_CHARGE_BATCHES = [
    {
        "organization_slug": "misja-robotyka",
        "model_name": "26/27 Poniedzialek",
        "period_label": "Pazdziernik 2026",
        "due_date": "2026-10-10",
        "lesson_count": 4,
    },
    {
        "organization_slug": "misja-robotyka",
        "model_name": "26/27 Poniedzialek",
        "period_label": "Listopad 2026",
        "due_date": "2026-11-10",
        "lesson_count": 4,
    },
    {
        "organization_slug": "misja-robotyka",
        "model_name": "26/27 Wtorek",
        "period_label": "Pazdziernik 2026",
        "due_date": "2026-10-10",
        "lesson_count": 4,
    },
    {
        "organization_slug": "misja-robotyka",
        "model_name": "26/27 Wtorek",
        "period_label": "Listopad 2026",
        "due_date": "2026-11-10",
        "lesson_count": 3,
    },
    {
        "organization_slug": "misja-robotyka",
        "model_name": "26/27 Wtorek",
        "period_label": "Grudzien 2026",
        "due_date": "2026-12-10",
        "lesson_count": 3,
    },
    {
        "organization_slug": "misja-robotyka",
        "model_name": "26/27 Sroda Semestr",
        "period_label": "Semestr zimowy 2026/2027",
        "due_date": "2026-10-31",
        "lesson_count": 14,
    },
    {
        "organization_slug": "misja-robotyka",
        "model_name": "26/27 Sroda Semestr",
        "period_label": "Semestr letni 2026/2027",
        "due_date": "2027-03-01",
        "lesson_count": 15,
    },
    {
        "organization_slug": "misja-robotyka",
        "model_name": "26/27 Piatek",
        "period_label": "Pazdziernik 2026",
        "due_date": "2026-10-24",
        "lesson_count": 4,
    },
    {
        "organization_slug": "misja-robotyka",
        "model_name": "26/27 Piatek",
        "period_label": "Listopad 2026",
        "due_date": "2026-11-10",
        "lesson_count": 4,
    },
    {
        "organization_slug": "misja-robotyka",
        "model_name": "26/27 Wlasny Indywidualny",
        "period_label": "Pakiet startowy Pazdziernik 2026",
        "due_date": "2026-10-15",
        "lesson_count": 2,
    },
    {
        "organization_slug": "misja-robotyka",
        "model_name": "26/27 Wlasny Indywidualny",
        "period_label": "Pakiet indywidualny Listopad 2026",
        "due_date": "2026-11-15",
        "lesson_count": 3,
    },
]

SEED_BILLING_BANK_ACCOUNTS = [
    {
        "organization_slug": "misja-robotyka",
        "account_name": "Wplaty za zajecia",
        "bank_name": "ING",
        "iban": "PL85105018231000009744356362",
        "currency": "PLN",
    },
    {
        "organization_slug": "misja-robotyka",
        "account_name": "Wplaty semestralne",
        "bank_name": "mBank",
        "iban": "PL12114020040000300201355387",
        "currency": "PLN",
    },
]

SEED_BILLING_STATEMENT_ROWS = [
    {
        "organization_slug": "misja-robotyka",
        "account_iban": "PL85105018231000009744356362",
        "booking_date": "2026-10-08",
        "value_date": "2026-10-08",
        "amount": "192.00",
        "currency": "PLN",
        "title": "500600700 Lena i Maja Kruk Pazdziernik 2026",
        "counterparty_name": "Rodzina Kruk",
        "counterparty_account": "PL02105018231000009999111111",
        "reference": "MR-DEMO-001",
    },
    {
        "organization_slug": "misja-robotyka",
        "account_iban": "PL85105018231000009744356362",
        "booking_date": "2026-10-09",
        "value_date": "2026-10-09",
        "amount": "171.00",
        "currency": "PLN",
        "title": "501600700 Igor Nowak Pazdziernik 2026",
        "counterparty_name": "Rodzina Nowak",
        "counterparty_account": "PL03105018231000009999222222",
        "reference": "MR-DEMO-002",
    },
    {
        "organization_slug": "misja-robotyka",
        "account_iban": "PL85105018231000009744356362",
        "booking_date": "2026-11-07",
        "value_date": "2026-11-07",
        "amount": "342.00",
        "currency": "PLN",
        "title": "500600700 Kruk Listopad 2026",
        "counterparty_name": "Rodzina Kruk",
        "counterparty_account": "PL02105018231000009999111111",
        "reference": "MR-DEMO-003",
    },
    {
        "organization_slug": "misja-robotyka",
        "account_iban": "PL85105018231000009744356362",
        "booking_date": "2026-10-11",
        "value_date": "2026-10-11",
        "amount": "313.00",
        "currency": "PLN",
        "title": "502700800 Alicja Olek Zosia Zielinscy Pazdziernik 2026",
        "counterparty_name": "Rodzina Zielinskich",
        "counterparty_account": "PL04105018231000009999333333",
        "reference": "MR-DEMO-004",
    },
    {
        "organization_slug": "misja-robotyka",
        "account_iban": "PL12114020040000300201355387",
        "booking_date": "2026-10-20",
        "value_date": "2026-10-20",
        "amount": "1304.00",
        "currency": "PLN",
        "title": "503700800 Julia Filip Adamscy semestr zimowy",
        "counterparty_name": "Rodzina Adamskich",
        "counterparty_account": "PL05114020040000300201999111",
        "reference": "MR-DEMO-005",
    },
    {
        "organization_slug": "misja-robotyka",
        "account_iban": "PL85105018231000009744356362",
        "booking_date": "2026-10-15",
        "value_date": "2026-10-15",
        "amount": "65.00",
        "currency": "PLN",
        "title": "504700800 Milosz Wisniewski pakiet startowy",
        "counterparty_name": "Rodzina Wisniewskich",
        "counterparty_account": "PL06105018231000009999444444",
        "reference": "MR-DEMO-006",
    },
    {
        "organization_slug": "misja-robotyka",
        "account_iban": "PL85105018231000009744356362",
        "booking_date": "2026-10-24",
        "value_date": "2026-10-24",
        "amount": "171.00",
        "currency": "PLN",
        "title": "505700800 Hanna Dabrowska Pazdziernik 2026",
        "counterparty_name": "Rodzina Dabrowskich",
        "counterparty_account": "PL07105018231000009999555555",
        "reference": "MR-DEMO-007",
    },
    {
        "organization_slug": "misja-robotyka",
        "account_iban": "PL85105018231000009744356362",
        "booking_date": "2026-11-09",
        "value_date": "2026-11-09",
        "amount": "228.00",
        "currency": "PLN",
        "title": "501600700 Listopad 2026",
        "counterparty_name": "Rodzina Nowak",
        "counterparty_account": "PL03105018231000009999222222",
        "reference": "MR-DEMO-008",
    },
    {
        "organization_slug": "misja-robotyka",
        "account_iban": "PL85105018231000009744356362",
        "booking_date": "2026-11-10",
        "value_date": "2026-11-10",
        "amount": "484.00",
        "currency": "PLN",
        "title": "502700800 listopad",
        "counterparty_name": "Rodzina Zielinskich",
        "counterparty_account": "PL04105018231000009999333333",
        "reference": "MR-DEMO-009",
    },
    {
        "organization_slug": "misja-robotyka",
        "account_iban": "PL85105018231000009744356362",
        "booking_date": "2026-12-09",
        "value_date": "2026-12-09",
        "amount": "242.00",
        "currency": "PLN",
        "title": "500600700",
        "counterparty_name": "Rodzina Kruk",
        "counterparty_account": "PL02105018231000009999111111",
        "reference": "MR-DEMO-010",
    },
]

SEED_KNOWLEDGE_MANUAL_DOCUMENTS = [
    {
        "organization_slug": "organizacja-domyslna",
        "title": "Zasady porannego przegladu operacyjnego",
        "file_name": "zasady_porannego_przegladu_operacyjnego.txt",
        "library_path": "Procedury/Operacyjne",
        "content_text": (
            "Poranny przeglad ma wskazac, co wymaga decyzji wlasciciela jeszcze dzisiaj. "
            "Lista powinna laczyc pilne zadania, faktury, kontrahentow i dokumenty bez pokazywania calego backlogu."
        ),
    },
    {
        "organization_slug": "organizacja-domyslna",
        "title": "Instrukcja konfiguracji srodowiska",
        "file_name": "instrukcja_konfiguracji_srodowiska.txt",
        "library_path": "Onboarding/Checklisty",
        "content_text": (
            "Przed testem aplikacji nalezy sprawdzic logowanie, wybor organizacji, stan bazy wiedzy oraz panel uzytkownikow."
        ),
    },
    {
        "organization_slug": "organizacja-domyslna",
        "title": "Wzor wniosku urlopowego",
        "file_name": "wzor_wniosku_urlopowego.txt",
        "library_path": "Wzory/HR",
        "use_in_assistant": False,
        "content_text": (
            "Wzor dokumentu: imie i nazwisko, termin urlopu, liczba dni, zastepstwo oraz podpis przelozonego."
        ),
    },
    {
        "organization_slug": "casi",
        "title": "Polityka delegacji CASI",
        "file_name": "polityka_delegacji_casi.txt",
        "library_path": "Procedury/Delegacje",
        "content_text": (
            "Delegacje krajowe w CASI zatwierdza dyrektor operacyjny. "
            "Delegacje zagraniczne zatwierdza zarzad. "
            "Wniosek delegacyjny skladamy minimum 3 dni robocze przed wyjazdem."
        ),
    },
    {
        "organization_slug": "casi",
        "title": "Dostepy i onboarding CASI",
        "file_name": "dostepy_onboarding_casi.txt",
        "library_path": "Onboarding",
        "content_text": (
            "Dostep do systemow nadaje koordynator operacyjny po akceptacji przelozonego. "
            "Nowy pracownik powinien otrzymac checkliste wdrozeniowa w pierwszym dniu pracy."
        ),
    },
    {
        "organization_slug": "casi",
        "title": "Wzor umowy wspolpracy CASI",
        "file_name": "wzor_umowy_wspolpracy_casi.txt",
        "library_path": "Wzory/Umowy",
        "use_in_assistant": False,
        "content_text": (
            "Wzor umowy wspolpracy B2B CASI: zakres obowiazkow, wynagrodzenie, poufnosc, okres wypowiedzenia."
        ),
    },
    {
        "organization_slug": "misja-robotyka",
        "title": "Procedura zastepstw instruktora",
        "file_name": "procedura_zastepstw_robotyka.txt",
        "library_path": "Procedury/Zastepstwa",
        "content_text": (
            "Nieobecnosc instruktora zglaszamy koordynatorowi najpozniej do 7:30. "
            "Zastepstwa zatwierdza administrator organizacji."
        ),
    },
    {
        "organization_slug": "misja-robotyka",
        "title": "Dostepy do panelu zajec",
        "file_name": "dostepy_panel_robotyka.txt",
        "library_path": "Systemy/Dostepy",
        "content_text": (
            "Dostepy do panelu zajec i list obecnosci nadaje administrator organizacji. "
            "Prosbe o nowe konto wysylamy przez formularz operacyjny."
        ),
    },
    {
        "organization_slug": "biuro-rachunkowe-alfa",
        "title": "Obieg dokumentow Biuro Alfa",
        "file_name": "obieg_dokumentow_alfa.txt",
        "library_path": "Procedury/Ksiegowosc",
        "content_text": (
            "Faktury kosztowe wprowadzamy w dniu otrzymania. "
            "Dokumenty do platnosci akceptuje glowna ksiegowa, a delegacje zatwierdza koordynator organizacji."
        ),
    },
    {
        "organization_slug": "biuro-rachunkowe-alfa",
        "title": "Urlopy Biuro Alfa",
        "file_name": "urlopy_biuro_alfa.txt",
        "library_path": "HR/Urlopy",
        "content_text": (
            "Wniosek urlopowy skladamy minimum 5 dni roboczych przed planowanym terminem. "
            "Nagla nieobecnosc zglaszamy telefonicznie do przelozonego przed 8:00."
        ),
    },
]

SEED_KNOWLEDGE_FOLDER_DOCUMENTS = [
    {
        "organization_slug": "organizacja-domyslna",
        "relative_path": "Procedury/Wsparcie/instrukcja_obslugi_zgloszen_klientow.txt",
        "content_text": (
            "Zgloszenia klientow z brakujacymi dokumentami opisujemy krotko: czego brakuje, kto odpowiada i do kiedy trzeba wrocic z informacja."
        ),
    },
    {
        "organization_slug": "casi",
        "relative_path": "HR/Urlopy/zasady_urlopow_i_zastepstw_w_zespole.txt",
        "content_text": (
            "Urlop okolicznosciowy w CASI zglaszamy bezposrednio do lidera zespolu i potwierdzamy wpisem w systemie."
        ),
    },
    {
        "organization_slug": "misja-robotyka",
        "relative_path": "Komunikacja/Rodzice/plan_komunikacji_z_rodzicami_przed_zajeciami.txt",
        "content_text": (
            "Wiadomosci do rodzicow wysylamy przez panel organizacji, a tresc komunikatu zatwierdza koordynator."
        ),
    },
    {
        "organization_slug": "biuro-rachunkowe-alfa",
        "relative_path": "Systemy/Dostepy/procedura_nadawania_dostepow_systemowych.txt",
        "content_text": (
            "Dostep do systemu obiegu faktur w Biurze Alfa nadaje koordynator organizacji po zatwierdzeniu przez glowna ksiegowa."
        ),
    },
]

SEED_KNOWLEDGE_VERSION_UPDATES = [
    {
        "organization_slug": "casi",
        "title": "Polityka delegacji CASI",
        "target_version_number": 2,
        "file_name": "polityka_delegacji_casi_v2.txt",
        "content_text": (
            "Delegacje krajowe w CASI zatwierdza dyrektor operacyjny. "
            "Delegacje zagraniczne zatwierdza zarzad. "
            "Wniosek delegacyjny skladamy minimum 3 dni robocze przed wyjazdem. "
            "Po powrocie rozliczenie delegacji zapisujemy dodatkowo w CRM i oznaczamy numer projektu."
        ),
    },
]

SEED_WORK_ITEMS = [
    {
        "organization_slug": "casi",
        "assigned_login": "casi_ola",
        "source_type": "invoice",
        "title": "Uzupelnic opis faktury za hosting i monitoring",
        "description": (
            "Brakuje jednoznacznego opisu kosztu przed przekazaniem faktury do rozliczenia. "
            "Sprawdzic, czy dotyczy infrastruktury CASI czy projektu klienta."
        ),
        "status": "w_toku",
        "priority_level": "wysoki",
        "due_offset_days": 0,
        "due_hour": 15,
        "sla_offset_hours": 5,
        "invoice_search": "FV/TRAVEL/17/2026",
        "contractor_search": "Travel Desk",
        "document_search": "Polityka delegacji CASI",
        "business_context": "Faktura moze utknac w weryfikacji, jesli opis kosztu nie bedzie jasny.",
        "attention_reason": "Wplywa na dzisiejsza kolejke faktur do opisania.",
    },
    {
        "organization_slug": "casi",
        "assigned_login": "casi_admin",
        "source_type": "knowledge",
        "title": "Sprawdzic aktualnosc procedury delegacji",
        "description": (
            "W dokumentach jest nowsza wersja zasad delegacji. Potwierdzic, czy zespol ma korzystac "
            "z tej wersji przy najblizszych wyjazdach."
        ),
        "status": "nowe",
        "priority_level": "normalny",
        "due_offset_days": 2,
        "due_hour": 12,
        "sla_offset_hours": 26,
        "document_search": "Polityka delegacji CASI",
        "business_context": "Dokument jest wazny operacyjnie, ale nie blokuje pracy na dzis.",
        "attention_reason": "Warto uporzadkowac przed kolejnym obiegiem delegacji.",
    },
    {
        "organization_slug": "misja-robotyka",
        "assigned_login": "robotyka_marek",
        "source_type": "invoice",
        "title": "Wyjasnic platnosc za zajecia robotyki",
        "description": (
            "W rozliczeniach widac wplate, ktora wymaga potwierdzenia z kontrahentem przed oznaczeniem "
            "jako rozliczona."
        ),
        "status": "w_toku",
        "priority_level": "wysoki",
        "due_offset_days": 0,
        "due_hour": 16,
        "sla_offset_hours": 6,
        "invoice_search": "FV/MR/LEGO/05/2026",
        "contractor_search": "Lego Edu Partner",
        "document_search": "Procedura zastepstw instruktora",
        "business_context": "Temat dotyczy biezacej platnosci i moze blokowac zamkniecie rozliczen.",
        "attention_reason": "Wymaga kontaktu przed koncem dnia.",
    },
    {
        "organization_slug": "misja-robotyka",
        "assigned_login": "robotyka_admin",
        "source_type": "knowledge",
        "title": "Potwierdzic zgody rodzicow na warsztaty sobotnie",
        "description": (
            "Przed wysylka przypomnienia do grupy trzeba sprawdzic, czy dokumenty zgod sa kompletne "
            "dla listy uczestnikow."
        ),
        "status": "nowe",
        "priority_level": "normalny",
        "due_offset_days": 1,
        "due_hour": 11,
        "sla_offset_hours": 24,
        "document_search": "Dostepy do panelu zajec",
        "business_context": "Sprawa organizacyjna do dopilnowania przed warsztatami.",
        "attention_reason": "Nie jest krytyczna teraz, ale powinna byc widoczna w karcie sprawy.",
    },
]


def seed_demo_data(
    invoice_service: InvoiceService,
    invoice_repository: InvoiceRepository,
    task_service: TaskService | None = None,
    auth_service: AuthService | None = None,
    billing_service: BillingService | None = None,
    knowledge_service: KnowledgeService | None = None,
    calendar_service: CalendarService | None = None,
    work_item_service: WorkItemService | None = None,
) -> None:
    if not auth_service:
        _ensure_legacy_default_invoices(invoice_service, invoice_repository)
        return
    if auth_service:
        _ensure_demo_organizations_and_users(auth_service)
    if auth_service and billing_service:
        _ensure_demo_billing_data(auth_service, billing_service)
    if auth_service and knowledge_service:
        _ensure_demo_knowledge_data(auth_service, knowledge_service)
    if auth_service:
        _ensure_demo_invoice_data(auth_service, invoice_service, invoice_repository)
    if auth_service and task_service and calendar_service:
        _ensure_demo_task_data(auth_service, task_service, calendar_service)
    if auth_service and work_item_service:
        _ensure_demo_work_item_data(
            auth_service,
            work_item_service,
            invoice_service=invoice_service,
            knowledge_service=knowledge_service,
        )


def _ensure_legacy_default_invoices(
    invoice_service: InvoiceService,
    invoice_repository: InvoiceRepository,
) -> None:
    for payload in SEED_INVOICES:
        source_external_id = str(payload.get("source_external_id") or "").strip()
        if source_external_id:
            existing = invoice_repository.get_by_source_external_id(
                source_external_id,
                source=str(payload.get("source") or ""),
                organization_id=None,
            )
            if existing:
                continue
        invoice_service.create_invoice(dict(payload), actor="system")


def _organization_map(auth_service: AuthService, actor_user: dict[str, Any]) -> dict[str, dict[str, Any]]:
    organizations = {
        item["slug"]: item
        for item in auth_service.organization_service.list_organizations(actor_user)
    }
    default_organization = auth_service.organization_repository.ensure_default_organization()
    organizations[default_organization["slug"]] = default_organization
    return organizations


def _ensure_demo_invoice_data(
    auth_service: AuthService,
    invoice_service: InvoiceService,
    invoice_repository: InvoiceRepository,
) -> None:
    users_by_login = {item["login"]: item for item in auth_service.list_users()}
    actor_user = users_by_login.get(DEFAULT_ADMIN_LOGIN)
    if not actor_user:
        return

    organizations_by_slug = _organization_map(auth_service, actor_user)
    for payload in [*SEED_INVOICES, *SEED_EXTRA_INVOICES]:
        organization = organizations_by_slug.get(
            _normalize_organization_slug(payload.get("organization_slug"))
        )
        organization_id = int(organization["organization_id"]) if organization else None
        source_external_id = str(payload.get("source_external_id") or "").strip()
        if source_external_id:
            existing = invoice_repository.get_by_source_external_id(
                source_external_id,
                source=str(payload.get("source") or ""),
                organization_id=organization_id,
            )
            if existing:
                continue
        invoice_payload = {key: value for key, value in payload.items() if key != "organization_slug"}
        invoice_service.create_invoice(
            invoice_payload,
            actor=actor_user.get("display_name") or actor_user["login"],
            organization_id=organization_id,
        )


def _build_demo_datetime(days_offset: int, hour: int, minute: int = 0) -> str:
    base = datetime.now().replace(second=0, microsecond=0)
    target = (base + timedelta(days=days_offset)).replace(hour=hour, minute=minute)
    return target.strftime("%Y-%m-%dT%H:%M")


def _build_demo_recent_timestamp(minutes_ago: int) -> str:
    base = datetime.now().replace(second=0, microsecond=0)
    target = base - timedelta(minutes=max(0, int(minutes_ago)))
    return target.isoformat(timespec="minutes")


def _organization_seed_fields(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": payload["name"],
        "slug": payload["slug"],
        "is_active": payload.get("is_active", 1),
        "telegram_chat_id": payload.get("telegram_chat_id"),
        "telegram_chat_name": payload.get("telegram_chat_name"),
        "email_inbox_address": payload.get("email_inbox_address"),
        "email_allowed_sender": payload.get("email_allowed_sender"),
        "email_subject_keyword": payload.get("email_subject_keyword"),
        "email_integration_enabled": payload.get("email_integration_enabled", 0),
        "enabled_modules": payload.get("enabled_modules") or [],
    }


def _organization_runtime_seed_fields(payload: dict[str, Any]) -> dict[str, Any]:
    connection_status = payload.get("demo_email_connection_status")
    connection_minutes_ago = int(payload.get("demo_email_connection_minutes_ago", 30))
    check_status = payload.get("demo_email_check_status")
    check_minutes_ago = int(payload.get("demo_email_check_minutes_ago", 20))
    return {
        "email_last_connection_tested_at": (
            _build_demo_recent_timestamp(connection_minutes_ago) if connection_status else None
        ),
        "email_last_connection_status": connection_status,
        "email_last_checked_at": _build_demo_recent_timestamp(check_minutes_ago) if check_status else None,
        "email_last_check_status": check_status,
    }


def _build_demo_task_payloads() -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for item in SEED_TASK_SCENARIOS:
        payload = dict(item)
        due_offset_days = payload.pop("due_offset_days", None)
        due_hour = payload.pop("due_hour", 9)
        due_minute = payload.pop("due_minute", 0)
        remind_minutes_before = payload.pop("remind_minutes_before", None)
        due_at = None
        if due_offset_days is not None:
            due_at = _build_demo_datetime(int(due_offset_days), int(due_hour), int(due_minute))
            payload["due_at"] = due_at
        if remind_minutes_before is not None and due_at:
            remind_at = datetime.strptime(due_at, "%Y-%m-%dT%H:%M") - timedelta(minutes=int(remind_minutes_before))
            payload["remind_at"] = remind_at.strftime("%Y-%m-%dT%H:%M")
        payloads.append(payload)
    return payloads


def _ensure_demo_task_data(
    auth_service: AuthService,
    task_service: TaskService,
    calendar_service: CalendarService,
) -> None:
    users_by_login = {item["login"]: item for item in auth_service.list_users()}
    actor_user = users_by_login.get(DEFAULT_ADMIN_LOGIN)
    if not actor_user:
        return

    organizations_by_slug = _organization_map(auth_service, actor_user)
    calendars_by_owner_and_name: dict[tuple[str, str], dict[str, Any]] = {}

    for calendar_payload in SEED_USER_CALENDARS:
        owner_user = users_by_login.get(calendar_payload["owner_login"])
        if not owner_user:
            continue
        owner_login = str(owner_user["login"])
        display_name = str(calendar_payload["display_name"])
        existing = next(
            (
                item
                for item in calendar_service.list_user_calendars(owner_user)
                if str(item.get("display_name") or "").strip() == display_name
            ),
            None,
        )
        linked_organization = organizations_by_slug.get(
            _normalize_organization_slug(calendar_payload.get("organization_slug"))
        )
        create_payload = {
            "display_name": display_name,
            "calendar_kind": calendar_payload.get("calendar_kind"),
            "linked_organization_id": linked_organization["organization_id"] if linked_organization else None,
            "default_duration_minutes": calendar_payload.get("default_duration_minutes", 60),
            "description": calendar_payload.get("description"),
            "is_active": calendar_payload.get("is_active", 1),
        }
        if existing:
            refreshed = calendar_service.update_user_calendar(
                int(existing["user_calendar_id"]),
                create_payload,
                actor_user=owner_user,
                actor=owner_user.get("display_name") or owner_login,
            )
            calendars_by_owner_and_name[(owner_login, display_name)] = refreshed or existing
        else:
            created = calendar_service.create_user_calendar(
                create_payload,
                actor_user=owner_user,
                actor=owner_user.get("display_name") or owner_login,
            )
            calendars_by_owner_and_name[(owner_login, display_name)] = created

    for task_payload in _build_demo_task_payloads():
        owner_user = users_by_login.get(task_payload["owner_login"])
        organization = organizations_by_slug.get(
            _normalize_organization_slug(task_payload["organization_slug"])
        )
        if not owner_user or not organization:
            continue
        owner_login = str(owner_user["login"])
        organization_id = int(organization["organization_id"])
        actor = owner_user.get("display_name") or owner_login
        calendar_name = task_payload.get("calendar_name")
        calendar = (
            calendars_by_owner_and_name.get((owner_login, str(calendar_name)))
            if calendar_name
            else None
        )
        assigned_user = users_by_login.get(task_payload.get("assigned_login") or "")
        visible_user_ids = [
            int(users_by_login[login]["user_id"])
            for login in task_payload.get("visible_logins", [])
            if login in users_by_login
        ]
        payload = {
            "title": task_payload["title"],
            "task_type": task_payload["task_type"],
            "visibility_scope": task_payload["visibility_scope"],
            "status": task_payload["status"],
            "priority": task_payload["priority"],
            "description": task_payload.get("description"),
            "due_at": task_payload.get("due_at"),
            "remind_at": task_payload.get("remind_at"),
            "assigned_user_id": assigned_user["user_id"] if assigned_user else None,
            "visible_user_ids": visible_user_ids,
            "calendar_id": calendar["user_calendar_id"] if calendar else None,
            "calendar_duration_minutes": calendar.get("default_duration_minutes") if calendar else None,
        }
        existing = next(
            (
                item
                for item in task_service.list_tasks({}, organization_id=organization_id, viewer_user=owner_user)
                if str(item.get("title") or "").strip() == task_payload["title"]
                and int(item.get("owner_user_id") or 0) == int(owner_user["user_id"])
            ),
            None,
        )
        if existing:
            task = task_service.update_task(
                int(existing["task_id"]),
                payload,
                actor_user=owner_user,
                actor=actor,
                organization_id=organization_id,
            )
        else:
            task = task_service.create_task(
                payload,
                actor_user=owner_user,
                actor=actor,
                organization_id=organization_id,
            )
        if not task:
            continue
        detail = task_service.get_task_detail(
            int(task["task_id"]),
            organization_id=organization_id,
            viewer_user=owner_user,
        )
        if not detail:
            continue
        existing_notes = {str(item.get("note_text") or "").strip() for item in detail.get("notes", [])}
        for note_text in task_payload.get("notes", []):
            if str(note_text).strip() in existing_notes:
                continue
            detail = task_service.add_task_note(
                int(task["task_id"]),
                note_text,
                actor_user=owner_user,
                actor=actor,
                organization_id=organization_id,
            ) or detail
            existing_notes.add(str(note_text).strip())

        attachment = task_payload.get("attachment")
        if attachment:
            existing_attachment_names = {
                str(item.get("file_name") or "").strip()
                for item in detail.get("attachments", [])
            }
            if str(attachment.get("file_name") or "").strip() not in existing_attachment_names:
                task_service.add_task_attachment(
                    int(task["task_id"]),
                    {
                        "file_name": attachment["file_name"],
                        "content_type": "text/plain",
                        "content_base64": base64.b64encode(
                            str(attachment["content"]).encode("utf-8")
                        ).decode("ascii"),
                    },
                    actor_user=owner_user,
                    actor=actor,
                    organization_id=organization_id,
                )


def _ensure_demo_work_item_data(
    auth_service: AuthService,
    work_item_service: WorkItemService,
    *,
    invoice_service: InvoiceService,
    knowledge_service: KnowledgeService | None = None,
) -> None:
    users_by_login = {item["login"]: item for item in auth_service.list_users()}
    actor_user = users_by_login.get(DEFAULT_ADMIN_LOGIN)
    if not actor_user:
        return

    organizations_by_slug = _organization_map(auth_service, actor_user)
    actor = actor_user.get("display_name") or actor_user["login"]

    for seed_item in SEED_WORK_ITEMS:
        organization = organizations_by_slug.get(
            _normalize_organization_slug(seed_item["organization_slug"])
        )
        if not organization:
            continue
        organization_id = int(organization["organization_id"])
        title = str(seed_item["title"]).strip()
        existing_items = work_item_service.list_work_items(
            {"only_open": "0"},
            organization_id=organization_id,
            limit=500,
        )
        if any(str(item.get("title") or "").strip() == title for item in existing_items):
            continue

        assigned_user = users_by_login.get(str(seed_item.get("assigned_login") or ""))
        due_at = _build_demo_datetime(
            int(seed_item.get("due_offset_days") or 0),
            int(seed_item.get("due_hour") or 12),
        )
        sla_deadline_at = (
            datetime.strptime(due_at, "%Y-%m-%dT%H:%M")
            + timedelta(hours=int(seed_item.get("sla_offset_hours") or 24))
        ).strftime("%Y-%m-%dT%H:%M")
        metadata = _build_work_item_metadata(
            seed_item,
            organization_id=organization_id,
            invoice_service=invoice_service,
            knowledge_service=knowledge_service,
        )

        work_item_service.create_work_item(
            {
                "source_type": seed_item.get("source_type") or "manual",
                "source_id": _work_item_seed_source_id(metadata),
                "title": title,
                "description": seed_item.get("description"),
                "status": seed_item.get("status") or "nowe",
                "priority_level": seed_item.get("priority_level") or "normalny",
                "assigned_user_id": assigned_user["user_id"] if assigned_user else None,
                "due_at": due_at,
                "sla_deadline_at": sla_deadline_at,
                "metadata": metadata,
            },
            actor_user=actor_user,
            actor=actor,
            organization_id=organization_id,
        )


def _work_item_seed_source_id(metadata: dict[str, Any]) -> int | None:
    invoice_id = metadata.get("invoice_id")
    if invoice_id not in (None, ""):
        return int(invoice_id)
    document_ids = metadata.get("knowledge_document_ids")
    if isinstance(document_ids, list) and document_ids:
        return int(document_ids[0])
    return None


def _build_work_item_metadata(
    seed_item: dict[str, Any],
    *,
    organization_id: int,
    invoice_service: InvoiceService,
    knowledge_service: KnowledgeService | None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "business_context": seed_item.get("business_context"),
        "attention_reason": seed_item.get("attention_reason"),
    }
    invoice = _find_seed_invoice(
        invoice_service,
        organization_id=organization_id,
        search=str(seed_item.get("invoice_search") or ""),
    )
    if invoice:
        metadata.update(
            {
                "invoice_id": int(invoice["id"]),
                "invoice_number": invoice.get("invoice_number"),
                "invoice_status": invoice.get("status"),
                "invoice_contractor_name": invoice.get("contractor_name") or invoice.get("issuer_name"),
                "invoice_amount_label": _format_amount_label(invoice),
            }
        )
        if invoice.get("contractor_id"):
            metadata["contractor_id"] = int(invoice["contractor_id"])
            metadata["contractor_name"] = invoice.get("contractor_name") or invoice.get("issuer_name")
    contractor = _find_seed_contractor(
        invoice_service,
        organization_id=organization_id,
        search=str(seed_item.get("contractor_search") or ""),
    )
    if contractor:
        metadata["contractor_id"] = int(contractor["contractor_id"])
        metadata["contractor_name"] = contractor.get("name")
        metadata["contractor_relation"] = "Powiazany kontrahent operacyjny"
    document = _find_seed_document(
        knowledge_service,
        organization_id=organization_id,
        search=str(seed_item.get("document_search") or ""),
    )
    if document:
        metadata["knowledge_document_ids"] = [int(document["knowledge_document_id"])]
        metadata["document_title"] = document.get("title")
        metadata["document_folder"] = document.get("library_path") or "Baza wiedzy"
        metadata["document_context"] = "Dokument pomocny przy wyjasnieniu tej sprawy"
    return {key: value for key, value in metadata.items() if value not in (None, "", [])}


def _find_seed_invoice(
    invoice_service: InvoiceService,
    *,
    organization_id: int,
    search: str,
) -> dict[str, Any] | None:
    if not search:
        return None
    invoices = invoice_service.list_invoices({"search": search}, organization_id=organization_id)
    return invoices[0] if invoices else None


def _find_seed_contractor(
    invoice_service: InvoiceService,
    *,
    organization_id: int,
    search: str,
) -> dict[str, Any] | None:
    if not search:
        return None
    contractors = invoice_service.list_contractors(search=search, organization_id=organization_id)
    return contractors[0] if contractors else None


def _find_seed_document(
    knowledge_service: KnowledgeService | None,
    *,
    organization_id: int,
    search: str,
) -> dict[str, Any] | None:
    if not knowledge_service or not search:
        return None
    documents = knowledge_service.list_documents(organization_id=organization_id, search=search)["documents"]
    return documents[0] if documents else None


def _format_amount_label(invoice: dict[str, Any]) -> str:
    amount = invoice.get("gross_amount")
    currency = invoice.get("currency") or "PLN"
    try:
        return f"{float(amount):.2f} {currency}"
    except (TypeError, ValueError):
        return str(currency)


def _ensure_demo_organizations_and_users(auth_service: AuthService) -> None:
    users_by_login = {item["login"]: item for item in auth_service.list_users()}
    admin_user = users_by_login.get(DEFAULT_ADMIN_LOGIN)
    if not admin_user:
        return

    organizations_by_slug: dict[str, dict[str, Any]] = {}
    for organization in auth_service.organization_service.list_organizations(admin_user):
        organizations_by_slug[organization["slug"]] = organization

    default_organization = auth_service.organization_repository.ensure_default_organization()
    auth_service.organization_repository.replace_enabled_modules(
        int(default_organization["organization_id"]),
        [MANAGER_ASSISTANT_MODULE],
        enabled_by_user_id=int(admin_user["user_id"]),
    )
    default_organization = auth_service.organization_repository.get_by_id(int(default_organization["organization_id"])) or default_organization
    organizations_by_slug[default_organization["slug"]] = default_organization

    for payload in SEED_ORGANIZATIONS:
        existing = auth_service.organization_repository.get_by_slug(payload["slug"])
        if existing:
            organization_id = int(existing["organization_id"])
        else:
            created = auth_service.organization_service.create_organization(
                _organization_seed_fields(payload),
                actor_user=admin_user,
                actor_login=admin_user["login"],
            )
            organization_id = int(created["organization_id"])
        auth_service.organization_repository.update(
            organization_id,
            {
                **_organization_seed_fields(payload),
                **_organization_runtime_seed_fields(payload),
            },
        )
        refreshed = auth_service.organization_repository.get_by_id(organization_id)
        if refreshed:
            organizations_by_slug[refreshed["slug"]] = refreshed

    for payload in SEED_USERS:
        if auth_service.user_repository.get_by_login(payload["login"]):
            continue
        organization = organizations_by_slug.get(
            _normalize_organization_slug(payload["organization_slug"])
        )
        if not organization:
            continue
        auth_service.create_user(
            {
                "login": payload["login"],
                "display_name": payload["display_name"],
                "password": payload["password"],
                "role": payload["role"],
                "is_active": 1,
                "telegram_user_id": payload["telegram_user_id"],
                "organization_id": organization["organization_id"],
            },
            actor_login=admin_user["login"],
            actor_user_id=admin_user["user_id"],
            actor_user=admin_user,
        )


def _ensure_demo_billing_data(auth_service: AuthService, billing_service: BillingService) -> None:
    users_by_login = {item["login"]: item for item in auth_service.list_users()}
    actor_user = (
        users_by_login.get("robotyka_marek")
        or users_by_login.get("robotyka_admin")
        or users_by_login.get(DEFAULT_ADMIN_LOGIN)
    )
    if not actor_user:
        return

    organization = auth_service.organization_repository.get_by_slug("misja-robotyka")
    if not organization:
        return

    organization_id = int(organization["organization_id"])
    actor = actor_user.get("display_name") or actor_user["login"]

    existing_schools = {
        str(item.get("short_name") or "").strip().upper(): item
        for item in billing_service.list_schools(organization_id=organization_id)
    }
    for payload in SEED_BILLING_SCHOOLS:
        if _normalize_organization_slug(payload["organization_slug"]) != organization["slug"]:
            continue
        short_name_key = str(payload["short_name"]).strip().upper()
        if short_name_key in existing_schools:
            continue
        created = billing_service.create_school(
            {
                "full_name": payload["full_name"],
                "short_name": payload["short_name"],
                "city": payload.get("city"),
                "notes": payload.get("notes"),
            },
            actor_user=actor_user,
            actor=actor,
            organization_id=organization_id,
        )
        existing_schools[str(created["short_name"]).strip().upper()] = created

    existing_models = {
        str(item.get("name") or "").strip(): item
        for item in billing_service.list_models(organization_id=organization_id)
    }
    for payload in SEED_BILLING_MODELS:
        if _normalize_organization_slug(payload["organization_slug"]) != organization["slug"]:
            continue
        if payload["name"] in existing_models:
            continue
        created = billing_service.create_model(
            {
                "name": payload["name"],
                "school_year": payload["school_year"],
                "lesson_day": payload["lesson_day"],
                "settlement_mode": payload["settlement_mode"],
                "monthly_rate_amount": payload["monthly_rate_amount"],
                "semester_rate_amount": payload["semester_rate_amount"],
                "sibling_discount_amount": payload["sibling_discount_amount"],
                "large_family_discount_amount": payload["large_family_discount_amount"],
                "intro_free_lessons_count": payload["intro_free_lessons_count"],
                "contract_required": payload["contract_required"],
                "notes": payload.get("notes"),
            },
            actor_user=actor_user,
            actor=actor,
            organization_id=organization_id,
        )
        existing_models[created["name"]] = created

    existing_payers = {
        str(item.get("contact_phone") or "").strip(): item
        for item in billing_service.list_payers(organization_id=organization_id)
    }
    for payload in SEED_BILLING_PAYERS:
        if _normalize_organization_slug(payload["organization_slug"]) != organization["slug"]:
            continue
        if payload["contact_phone"] in existing_payers:
            continue
        created = billing_service.create_payer(
            {
                "display_name": payload["display_name"],
                "contact_phone": payload["contact_phone"],
                "has_large_family_card": payload.get("has_large_family_card", 0),
                "email": payload.get("email"),
                "notes": payload.get("notes"),
            },
            actor_user=actor_user,
            actor=actor,
            organization_id=organization_id,
        )
        existing_payers[created["contact_phone"]] = created

    existing_students = {
        (str(item.get("full_name") or "").strip(), int(item.get("billing_payer_id") or 0)): item
        for item in billing_service.list_students(organization_id=organization_id)
    }
    for payload in SEED_BILLING_STUDENTS:
        if _normalize_organization_slug(payload["organization_slug"]) != organization["slug"]:
            continue
        payer = existing_payers.get(payload["payer_phone"])
        school = existing_schools.get(str(payload["school_short_name"]).strip().upper())
        model = existing_models.get(payload["model_name"])
        if not payer or not school or not model:
            continue
        student_key = (payload["full_name"], int(payer["billing_payer_id"]))
        if student_key in existing_students:
            continue
        created = billing_service.create_student(
            {
                "full_name": payload["full_name"],
                "billing_payer_id": payer["billing_payer_id"],
                "billing_school_id": school["billing_school_id"],
                "billing_model_id": model["billing_model_id"],
                "lesson_day": model.get("lesson_day"),
                "family_billing_order": payload["family_billing_order"],
                "group_name": payload.get("group_name"),
                "notes": payload.get("notes"),
            },
            actor_user=actor_user,
            actor=actor,
            organization_id=organization_id,
        )
        existing_students[(created["full_name"], int(created["billing_payer_id"]))] = created

    existing_accounts = {
        str(item.get("iban") or "").strip(): item
        for item in billing_service.list_bank_accounts(organization_id=organization_id)
    }
    for payload in SEED_BILLING_BANK_ACCOUNTS:
        if _normalize_organization_slug(payload["organization_slug"]) != organization["slug"]:
            continue
        if payload["iban"] in existing_accounts:
            continue
        created = billing_service.create_bank_account(
            {
                "account_name": payload["account_name"],
                "bank_name": payload["bank_name"],
                "iban": payload["iban"],
                "currency": payload["currency"],
            },
            actor_user=actor_user,
            actor=actor,
            organization_id=organization_id,
        )
        existing_accounts[created["iban"]] = created

    existing_charge_keys = {
        (str(item.get("model_name") or "").strip(), str(item.get("period_label") or "").strip())
        for item in billing_service.list_charges(organization_id=organization_id, limit=500)
    }
    for payload in SEED_BILLING_CHARGE_BATCHES:
        if _normalize_organization_slug(payload["organization_slug"]) != organization["slug"]:
            continue
        key = (payload["model_name"], payload["period_label"])
        if key in existing_charge_keys:
            continue
        model = existing_models.get(payload["model_name"])
        if not model:
            continue
        billing_service.generate_charges_for_model(
            {
                "billing_model_id": model["billing_model_id"],
                "period_label": payload["period_label"],
                "due_date": payload["due_date"],
                "lesson_count": payload["lesson_count"],
                "notes": "Naliczono z harmonogramu zajec i przypisano do platnika.",
            },
            actor_user=actor_user,
            actor=actor,
            organization_id=organization_id,
        )
        existing_charge_keys.add(key)

    existing_transactions = billing_service.list_transactions(organization_id=organization_id, limit=1000)
    existing_references_by_account: dict[int, set[str]] = {}
    for transaction in existing_transactions:
        try:
            account_id = int(transaction.get("billing_bank_account_id") or 0)
        except (TypeError, ValueError):
            continue
        reference = str(transaction.get("reference") or "").strip()
        if not account_id or not reference:
            continue
        existing_references_by_account.setdefault(account_id, set()).add(reference)

    statement_rows_by_iban: dict[str, list[dict[str, Any]]] = {}
    default_account_iban = next(iter(existing_accounts.keys()), "")
    for payload in SEED_BILLING_STATEMENT_ROWS:
        if _normalize_organization_slug(payload["organization_slug"]) != organization["slug"]:
            continue
        account_iban = str(payload.get("account_iban") or default_account_iban).strip()
        if not account_iban:
            continue
        statement_rows_by_iban.setdefault(account_iban, []).append(payload)

    for account_iban, statement_rows in statement_rows_by_iban.items():
        bank_account = existing_accounts.get(account_iban)
        if not bank_account or not statement_rows:
            continue

        account_id = int(bank_account["billing_bank_account_id"])
        incoming_references = {
            str(row.get("reference") or "").strip()
            for row in statement_rows
            if str(row.get("reference") or "").strip()
        }
        if incoming_references and incoming_references.issubset(existing_references_by_account.get(account_id, set())):
            continue

        rows = [
            "booking_date;value_date;amount;currency;title;counterparty_name;counterparty_account;reference",
        ]
        for payload in statement_rows:
            rows.append(
                ";".join(
                    [
                        payload["booking_date"],
                        payload["value_date"],
                        payload["amount"],
                        payload["currency"],
                        payload["title"],
                        payload["counterparty_name"],
                        payload["counterparty_account"],
                        payload["reference"],
                    ]
                )
            )
        csv_content = "\n".join(rows)
        safe_account_name = str(bank_account.get("account_name") or "konto").replace(" ", "_").lower()
        billing_service.import_statement_csv(
            account_id,
            csv_content,
            source_file_name=f"wyciag_misja_robotyka_{safe_account_name}.csv",
            actor_user=actor_user,
            actor=actor,
            organization_id=organization_id,
        )
        existing_references_by_account.setdefault(account_id, set()).update(incoming_references)


def _ensure_demo_knowledge_data(auth_service: AuthService, knowledge_service: KnowledgeService) -> None:
    users_by_login = {item["login"]: item for item in auth_service.list_users()}
    actor_user = users_by_login.get(DEFAULT_ADMIN_LOGIN)
    if not actor_user:
        return

    actor = actor_user.get("display_name") or actor_user["login"]
    organizations_by_slug = {
        item["slug"]: item
        for item in auth_service.organization_service.list_organizations(actor_user)
    }
    default_organization = auth_service.organization_repository.ensure_default_organization()
    organizations_by_slug[default_organization["slug"]] = default_organization

    queued_jobs = 0
    for payload in SEED_KNOWLEDGE_MANUAL_DOCUMENTS:
        organization = organizations_by_slug.get(
            _normalize_organization_slug(payload["organization_slug"])
        )
        if not organization:
            continue
        organization_id = int(organization["organization_id"])
        existing_documents = knowledge_service.list_documents(organization_id)["documents"]
        already_exists = any(
            str(item.get("title") or "").strip() == payload["title"]
            or str(item.get("file_name") or "").strip() == payload["file_name"]
            for item in existing_documents
        )
        if already_exists:
            continue
        knowledge_service.add_document(
            organization_id=organization_id,
            title=payload["title"],
            actor_user=actor_user,
            actor=actor,
            file_name=payload["file_name"],
            content_text=payload["content_text"],
            library_path=payload.get("library_path"),
            is_downloadable=bool(payload.get("is_downloadable", True)),
            use_in_assistant=bool(payload.get("use_in_assistant", True)),
        )
        queued_jobs += 1

    for payload in SEED_KNOWLEDGE_FOLDER_DOCUMENTS:
        organization = organizations_by_slug.get(
            _normalize_organization_slug(payload["organization_slug"])
        )
        if not organization:
            continue
        organization_id = int(organization["organization_id"])
        folder_path = KNOWLEDGE_DIR / "organizacje" / str(organization["slug"])
        folder_path.mkdir(parents=True, exist_ok=True)
        relative_path = Path(str(payload.get("relative_path") or payload["file_name"]))
        source_file = folder_path / relative_path
        source_file.parent.mkdir(parents=True, exist_ok=True)
        if not source_file.exists() or source_file.read_text(encoding="utf-8") != payload["content_text"]:
            source_file.write_text(payload["content_text"], encoding="utf-8")
        sync_result = knowledge_service.sync_folder(
            organization_id=organization_id,
            actor_user=actor_user,
            actor=actor,
        )
        queued_jobs += int(sync_result.get("imported_count") or 0) + int(sync_result.get("updated_count") or 0)

    if queued_jobs:
        knowledge_service.process_pending_jobs(limit=max(queued_jobs * 3, 24))

    version_jobs = 0
    for payload in SEED_KNOWLEDGE_VERSION_UPDATES:
        organization = organizations_by_slug.get(
            _normalize_organization_slug(payload["organization_slug"])
        )
        if not organization:
            continue
        organization_id = int(organization["organization_id"])
        existing_documents = knowledge_service.list_documents(organization_id)["documents"]
        document = next(
            (
                item
                for item in existing_documents
                if str(item.get("title") or "").strip() == payload["title"]
            ),
            None,
        )
        if not document:
            continue
        if int(document.get("current_version_number") or 0) >= int(payload.get("target_version_number") or 2):
            continue
        knowledge_service.replace_document_file(
            organization_id=organization_id,
            knowledge_document_id=int(document["knowledge_document_id"]),
            actor_user=actor_user,
            actor=actor,
            file_name=str(payload.get("file_name") or document.get("file_name") or "dokument_v2.txt"),
            file_bytes=str(payload["content_text"]).encode("utf-8"),
            mime_type="text/plain",
        )
        version_jobs += 1

    if version_jobs:
        knowledge_service.process_pending_jobs(limit=max(version_jobs * 3, 12))


