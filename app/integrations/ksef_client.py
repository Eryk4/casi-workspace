from __future__ import annotations


class KSeFClient:
    def fetch_mock_invoice(self) -> dict:
        # TODO: tutaj podłącz prawdziwe API KSeF i mapowanie odpowiedzi do wspólnego modelu faktury.
        return {
            "incoming_date": "2026-04-07",
            "source": "KSeF",
            "file_name": "ksef_fv_telekom_2026_04_07.xml",
            "document_type": "xml",
            "invoice_number": "FV/KSEF/204/04/2026",
            "ksef_number": "KSEF-2026-0042-PL",
            "issuer_nip": "5214567890",
            "issuer_name": "Telekom Serwis Polska",
            "issue_date": "2026-04-07",
            "sale_date": "2026-04-07",
            "gross_amount": 512.40,
            "currency": "PLN",
            "source_external_id": "ksef-dokument-2026-0042",
            "source_metadata": {
                "kanal": "KSeF API",
                "status_pobrania": "mock",
            },
            "notes": "Mock importu z KSeF.",
        }
