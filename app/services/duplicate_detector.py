from __future__ import annotations

from typing import Any

from app.repositories.invoice_repository import InvoiceRepository


class DuplicateDetector:
    def __init__(self, invoice_repository: InvoiceRepository) -> None:
        self.invoice_repository = invoice_repository

    def evaluate(self, invoice: dict[str, Any], exclude_invoice_id: int | None = None) -> dict[str, Any]:
        ksef_number = (invoice.get("ksef_number") or "").strip()
        invoice_number = (invoice.get("invoice_number") or "").strip()
        issuer_nip = (invoice.get("issuer_nip") or "").strip()
        organization_id = invoice.get("organization_id")

        exact_matches = self.invoice_repository.find_exact_ksef_duplicates(
            ksef_number,
            exclude_invoice_id,
            organization_id=organization_id,
        )
        if exact_matches:
            existing_ids = [match["id"] for match in exact_matches]
            reason = (
                f"Wykryto pewny duplikat. Powód: zgodny numer KSeF: {ksef_number}. "
                f"Istniejące rekordy: {', '.join(str(item) for item in existing_ids)}."
            )
            return {
                "status": "pewny_duplikat",
                "duplicate_type": "pewny",
                "flag_reason": reason,
                "relations": [
                    {
                        "related_invoice_id": match["id"],
                        "relation_type": "pewny_duplikat",
                        "reason": f"Zgodny numer KSeF: {ksef_number}",
                    }
                    for match in exact_matches
                ],
            }

        suspected_matches = self.invoice_repository.find_suspected_duplicates(
            invoice_number,
            issuer_nip,
            exclude_invoice_id,
            organization_id=organization_id,
        )
        if suspected_matches:
            existing_ids = [match["id"] for match in suspected_matches]
            reason = (
                "Wykryto podejrzenie duplikatu. Powód: zgodny numer faktury + NIP wystawcy. "
                f"Numer faktury: {invoice_number}. NIP: {issuer_nip}. "
                f"Istniejące rekordy: {', '.join(str(item) for item in existing_ids)}."
            )
            return {
                "status": "podejrzenie_duplikatu",
                "duplicate_type": "podejrzenie",
                "flag_reason": reason,
                "relations": [
                    {
                        "related_invoice_id": match["id"],
                        "relation_type": "podejrzenie_duplikatu",
                        "reason": f"Zgodny numer faktury {invoice_number} oraz NIP {issuer_nip}",
                    }
                    for match in suspected_matches
                ],
            }

        return {
            "status": invoice.get("status") if invoice.get("status") not in {"podejrzenie_duplikatu", "pewny_duplikat"} else "nowa",
            "duplicate_type": "brak",
            "flag_reason": None,
            "relations": [],
        }

    def similar_invoices(self, invoice: dict[str, Any], exclude_invoice_id: int | None = None) -> list[dict[str, Any]]:
        result = self.evaluate(invoice, exclude_invoice_id)
        relations = result["relations"]
        related_ids = [relation["related_invoice_id"] for relation in relations]
        if not related_ids:
            return []
        all_invoices = self.invoice_repository.list_invoices({}, organization_id=invoice.get("organization_id"))
        by_id = {item["id"]: item for item in all_invoices}
        output = []
        for relation in relations:
            related = by_id.get(relation["related_invoice_id"])
            if not related:
                continue
            related_copy = dict(related)
            related_copy["match_reason"] = relation["reason"]
            related_copy["match_type"] = relation["relation_type"]
            output.append(related_copy)
        return output
