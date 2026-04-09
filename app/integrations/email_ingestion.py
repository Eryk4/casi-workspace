from __future__ import annotations


class EmailIngestionAdapter:
    def fetch_mock_invoice(self) -> dict:
        # TODO: tutaj podłącz prawdziwy odbiór wiadomości e-mail, parsowanie załączników PDF i metadanych wiadomości.
        return {
            "incoming_date": "2026-04-07",
            "source": "EMAIL",
            "file_name": "mail_fv_marketing_2026_04_07.pdf",
            "document_type": "pdf",
            "invoice_number": "FV/MAIL/100/04/2026",
            "ksef_number": "",
            "issuer_nip": "8943001122",
            "issuer_name": "Agencja Marketing Operacyjny",
            "issue_date": "2026-04-06",
            "sale_date": "2026-04-06",
            "gross_amount": 1890.00,
            "currency": "PLN",
            "source_external_id": "email-wiadomosc-2026-04-07-001",
            "source_sender_name": "faktury@marketing-operacyjny.pl",
            "source_metadata": {
                "temat": "Faktura FV/MAIL/100/04/2026",
                "skrzynka": "faktury@twojafirma.pl",
            },
            "notes": "Mock importu z e-maila.",
        }
