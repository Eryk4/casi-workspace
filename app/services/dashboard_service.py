from __future__ import annotations

from typing import Any

from app.repositories.contractor_repository import ContractorRepository
from app.repositories.event_repository import EventRepository
from app.repositories.invoice_repository import InvoiceRepository


class DashboardService:
    def __init__(
        self,
        invoice_repository: InvoiceRepository,
        contractor_repository: ContractorRepository,
        event_repository: EventRepository,
    ) -> None:
        self.invoice_repository = invoice_repository
        self.contractor_repository = contractor_repository
        self.event_repository = event_repository

    def get_snapshot(self, organization_id: int | None = None) -> dict[str, Any]:
        invoices = self.invoice_repository.list_invoices({}, organization_id=organization_id)
        contractors = self.contractor_repository.list_contractors(organization_id=organization_id)
        events = self.event_repository.list_logs(limit=12, organization_id=organization_id)
        return {
            "cards": {
                "nowe_faktury": sum(1 for item in invoices if item["status"] == "nowa"),
                "do_weryfikacji": sum(1 for item in invoices if item["status"] == "weryfikacja"),
                "podejrzenia_duplikatow": sum(1 for item in invoices if item["duplicate_type"] == "podejrzenie"),
                "pewne_duplikaty": sum(1 for item in invoices if item["duplicate_type"] == "pewny"),
                "nowi_kontrahenci": sum(1 for item in contractors if item["is_new"]),
            },
            "recent_events": events,
        }
