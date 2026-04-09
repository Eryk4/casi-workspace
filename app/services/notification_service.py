from __future__ import annotations

from typing import Any

from app.repositories.event_repository import EventRepository


class NotificationService:
    def __init__(self, event_repository: EventRepository) -> None:
        self.event_repository = event_repository

    def prepare_duplicate_notification(self, invoice: dict[str, Any], duplicate_result: dict[str, Any]) -> str | None:
        if duplicate_result["duplicate_type"] == "brak":
            return None

        related_ids = [str(item["related_invoice_id"]) for item in duplicate_result["relations"]]
        source = invoice.get("source") or "-"
        invoice_id = invoice.get("id") or invoice.get("invoice_id")

        if duplicate_result["duplicate_type"] == "pewny":
            message = (
                f"Wykryto pewny duplikat. ID faktury: {invoice_id}. "
                f"Powód: zgodny numer KSeF: {invoice.get('ksef_number')}. "
                f"Istniejący rekord: {', '.join(related_ids)}. "
                f"Źródło: {source}."
            )
        else:
            message = (
                f"Wykryto podejrzenie duplikatu. ID faktury: {invoice_id}. "
                "Powód: zgodny numer faktury + NIP wystawcy. "
                f"Numer faktury: {invoice.get('invoice_number')}. "
                f"NIP: {invoice.get('issuer_nip')}. "
                f"Istniejący rekord: {', '.join(related_ids)}. "
                f"Źródło: {source}."
            )

        self.event_repository.log(
            event_type="telegram_notification_prepared",
            invoice_id=invoice_id,
            organization_id=invoice.get("organization_id"),
            source=source,
            status_before=None,
            status_after=duplicate_result["status"],
            decision_reason=duplicate_result["flag_reason"],
            actor="system",
            details={"message": message},
        )
        return message
