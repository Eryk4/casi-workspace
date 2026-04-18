from __future__ import annotations

import hashlib
from typing import Any


class KSeFClientError(RuntimeError):
    pass


class KSeFClient:
    def __init__(self) -> None:
        self._environment_labels = {
            "demo": "Srodowisko demo KSeF",
            "production": "Srodowisko produkcyjne KSeF",
        }

    def integration_status(self) -> dict[str, Any]:
        return {
            "enabled": True,
            "mode": "mvp_stub",
            "provider": "ksef_mvp",
            "supports_manual_check": True,
            "supports_history": True,
        }

    def test_connection(self, organization: dict[str, Any]) -> dict[str, Any]:
        company_identifier = str(organization.get("ksef_company_identifier") or "").strip()
        if not company_identifier:
            raise KSeFClientError("Uzupelnij identyfikator firmy w KSeF przed testem polaczenia.")

        environment = self._normalize_environment(organization.get("ksef_environment"))
        return {
            "connected": True,
            "environment": environment,
            "environment_label": self._environment_labels[environment],
            "company_identifier": company_identifier,
            "message": (
                f"Polaczenie KSeF jest gotowe dla identyfikatora {company_identifier} "
                f"w trybie {self._environment_labels[environment].lower()}."
            ),
        }

    def fetch_invoice_candidates(
        self,
        organization: dict[str, Any],
        *,
        limit: int = 25,
        trigger_mode: str = "manual",
    ) -> dict[str, Any]:
        company_identifier = str(organization.get("ksef_company_identifier") or "").strip()
        if not company_identifier:
            raise KSeFClientError("Brakuje identyfikatora firmy w KSeF.")

        environment = self._normalize_environment(organization.get("ksef_environment"))
        seed = f"{organization.get('organization_id')}|{company_identifier}|{environment}"
        suffix = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8].upper()
        candidates = [
            {
                "incoming_date": "2026-04-13",
                "source": "KSEF",
                "file_name": f"ksef_{suffix}_001.xml",
                "document_type": "xml",
                "invoice_number": f"FV/KSEF/{suffix}/001",
                "ksef_number": f"KSEF-{environment.upper()}-{suffix}-001",
                "issuer_nip": company_identifier,
                "issuer_name": organization.get("name") or "Organizacja KSeF",
                "issue_date": "2026-04-13",
                "sale_date": "2026-04-13",
                "gross_amount": 512.40,
                "currency": "PLN",
                "source_external_id": f"ksef-{environment}-{suffix}-001",
                "source_metadata": {
                    "kanal": "KSeF API",
                    "status_pobrania": "mvp",
                    "environment": environment,
                    "company_identifier": company_identifier,
                    "trigger_mode": trigger_mode,
                },
                "notes": "MVP importu KSeF.",
            },
            {
                "incoming_date": "2026-04-13",
                "source": "KSEF",
                "file_name": f"ksef_{suffix}_002.xml",
                "document_type": "xml",
                "invoice_number": f"FV/KSEF/{suffix}/002",
                "ksef_number": f"KSEF-{environment.upper()}-{suffix}-002",
                "issuer_nip": company_identifier,
                "issuer_name": organization.get("name") or "Organizacja KSeF",
                "issue_date": "2026-04-13",
                "sale_date": "2026-04-13",
                "gross_amount": 781.15,
                "currency": "PLN",
                "source_external_id": f"ksef-{environment}-{suffix}-002",
                "source_metadata": {
                    "kanal": "KSeF API",
                    "status_pobrania": "mvp",
                    "environment": environment,
                    "company_identifier": company_identifier,
                    "trigger_mode": trigger_mode,
                },
                "notes": "MVP importu KSeF.",
            },
        ]
        return {
            "candidates": candidates[: max(1, int(limit))],
            "checked_document_count": min(len(candidates), max(1, int(limit))),
            "environment": environment,
            "company_identifier": company_identifier,
        }

    def fetch_mock_invoice(self) -> dict[str, Any]:
        return {
            "incoming_date": "2026-04-07",
            "source": "KSEF",
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

    def _normalize_environment(self, raw_value: Any) -> str:
        normalized = str(raw_value or "").strip().lower()
        if normalized in {"", "demo", "test"}:
            return "demo"
        if normalized in {"production", "prod", "produkcyjne"}:
            return "production"
        raise KSeFClientError("Nieznane srodowisko KSeF.")
