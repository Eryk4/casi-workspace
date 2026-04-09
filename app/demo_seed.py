from __future__ import annotations

from typing import Any

from app.repositories.invoice_repository import InvoiceRepository
from app.services.auth_service import AuthService
from app.services.invoice_service import InvoiceService
from app.services.task_service import TaskService


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
        "notes": "Przykład poprawnej faktury z KSeF.",
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
        "notes": "Przykład pewnego duplikatu po numerze KSeF.",
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
        "notes": "Faktura bazowa do przykładu podejrzenia duplikatu.",
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
        "notes": "Przykład podejrzenia duplikatu po numerze faktury i NIP.",
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
        "notes": "Przykład nowego kontrahenta z Telegrama.",
    },
]

SEED_TASKS = [
    {
        "title": "Sprawdzic nowe faktury z Telegrama",
        "task_type": "zadanie",
        "status": "nowe",
        "priority": "wysoki",
        "due_at": "2026-04-09T09:00",
        "remind_at": "2026-04-09T08:15",
        "description": "Przejrzec dzisiejsze dokumenty i potwierdzic, czy nie ma duplikatow.",
    },
    {
        "title": "Spotkanie statusowe z klientem",
        "task_type": "wydarzenie",
        "status": "oczekuje",
        "priority": "normalny",
        "due_at": "2026-04-10T13:30",
        "remind_at": "2026-04-10T12:45",
        "description": "Krotkie omowienie zaleglych faktur i nowych kontrahentow.",
    },
    {
        "title": "Przypomnienie o backupie danych",
        "task_type": "przypomnienie",
        "status": "nowe",
        "priority": "krytyczny",
        "due_at": "2026-04-10T18:00",
        "remind_at": "2026-04-10T17:30",
        "description": "Zweryfikowac, czy kopia bazy i plikow wykonala sie poprawnie.",
    },
]


def seed_demo_data(
    invoice_service: InvoiceService,
    invoice_repository: InvoiceRepository,
    task_service: TaskService | None = None,
    auth_service: AuthService | None = None,
) -> None:
    if invoice_repository.count_all() > 0:
        return
    for payload in SEED_INVOICES:
        invoice_service.create_invoice(payload, actor="seed")

    if not task_service or not auth_service:
        return

    users = auth_service.list_users()
    if not users:
        return
    actor_user = users[0]
    invoices = invoice_repository.list_invoices({})
    if not invoices:
        return
    organization_id = invoices[0].get("organization_id")
    if not organization_id:
        return

    for payload in SEED_TASKS:
        task_service.create_task(
            payload,
            actor_user=actor_user,
            actor=actor_user.get("display_name") or actor_user["login"],
            organization_id=int(organization_id),
        )
