from __future__ import annotations

import re
from typing import Any

from app.domain.constants import BILLING_TRANSACTION_MATCH_STATUSES
from app.repositories.billing_ledger_repository import BillingLedgerRepository
from app.repositories.billing_repository import BillingRepository
from app.repositories.event_repository import EventRepository
from app.utils import extract_phone_identifiers, normalize_phone_identifier, now_iso


class BillingLedgerService:
    def __init__(
        self,
        billing_ledger_repository: BillingLedgerRepository,
        billing_repository: BillingRepository,
        event_repository: EventRepository,
    ) -> None:
        self.billing_ledger_repository = billing_ledger_repository
        self.billing_repository = billing_repository
        self.event_repository = event_repository

    def list_balances(self, organization_id: int | None = None) -> list[dict[str, Any]]:
        return self.billing_ledger_repository.list_balance_rows(organization_id=organization_id)

    def list_ledger_entries(
        self,
        *,
        organization_id: int | None = None,
        billing_payer_id: int | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        return self.billing_ledger_repository.list_ledger_entries(
            organization_id=organization_id,
            billing_payer_id=billing_payer_id,
            limit=limit,
        )

    def list_payment_matches(
        self,
        *,
        organization_id: int | None = None,
        billing_payer_id: int | None = None,
        billing_transaction_id: int | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        return self.billing_ledger_repository.list_payment_matches(
            organization_id=organization_id,
            billing_payer_id=billing_payer_id,
            billing_transaction_id=billing_transaction_id,
            limit=limit,
        )

    def record_charge_generation(
        self,
        charges: list[dict[str, Any]],
        *,
        actor_user: dict[str, Any] | None,
        actor: str,
        organization_id: int | None,
    ) -> None:
        if organization_id is None or not charges:
            return
        balances = {int(row["billing_payer_id"]): row for row in self.list_balances(organization_id=organization_id)}
        grouped: dict[int, list[dict[str, Any]]] = {}
        for charge in charges:
            grouped.setdefault(int(charge["billing_payer_id"]), []).append(charge)

        for payer_id, payer_charges in grouped.items():
            payer_row = balances.get(payer_id) or {}
            current_balance = float(payer_row.get("balance_due") or 0) - sum(float(item.get("total_amount") or 0) for item in payer_charges)
            for charge in payer_charges:
                amount = float(charge.get("total_amount") or 0)
                current_balance = round(current_balance + amount, 2)
                self.billing_ledger_repository.create_ledger_entry(
                    {
                        "organization_id": organization_id,
                        "billing_payer_id": payer_id,
                        "billing_charge_id": charge.get("billing_charge_id"),
                        "billing_transaction_id": None,
                        "entry_kind": "charge_created",
                        "amount_delta": amount,
                        "balance_after": current_balance,
                        "note": charge.get("period_label") or charge.get("notes"),
                        "created_by_user_id": actor_user.get("user_id") if actor_user else None,
                        "created_at": now_iso(),
                    }
                )
        self.event_repository.log(
            event_type="billing_ledger_charge_recorded",
            invoice_id=None,
            organization_id=organization_id,
            source="BILLING",
            status_before=None,
            status_after=None,
            decision_reason=f"Zapisano ledger dla {len(charges)} naliczen.",
            actor=actor,
            details={"charge_count": len(charges)},
        )

    def match_transaction(
        self,
        transaction: dict[str, Any],
        *,
        billing_payer_id: int,
        matched_amount: float,
        actor_user: dict[str, Any] | None,
        actor: str,
        organization_id: int | None,
        billing_charge_id: int | None = None,
        match_reason: str | None = None,
        match_status: str = "rozliczona",
    ) -> dict[str, Any]:
        if organization_id is None:
            raise ValueError("Wybierz organizacje przed dopasowaniem wplaty.")
        if match_status not in BILLING_TRANSACTION_MATCH_STATUSES:
            raise ValueError("Nieprawidlowy status dopasowania transakcji.")

        transaction_id = int(transaction["billing_transaction_id"])
        transaction_amount = abs(float(transaction.get("amount") or 0))
        if transaction_amount <= 0:
            raise ValueError("Transakcja nie ma dodatniej kwoty do rozliczenia.")
        if float(matched_amount or 0) <= 0:
            raise ValueError("Kwota dopasowania musi byc dodatnia.")

        current_balance = self.billing_ledger_repository.get_balance_row(organization_id, billing_payer_id) or {}
        balance_before = float(current_balance.get("balance_due") or 0)
        balance_after = round(balance_before - float(matched_amount), 2)

        current_status = str(transaction.get("matched_status") or "nieprzypisana").strip()
        existing_total_matched_amount = round(
            sum(
                float(item.get("matched_amount") or 0)
                for item in self.billing_ledger_repository.list_payment_matches(
                    organization_id=organization_id,
                    billing_transaction_id=transaction_id,
                    limit=200,
                )
            ),
            2,
        )
        total_matched_amount = round(existing_total_matched_amount + float(matched_amount), 2)
        transaction_status = "rozliczona" if total_matched_amount >= transaction_amount else "czesciowo_rozliczona"

        match_id = self.billing_ledger_repository.create_payment_match(
            {
                "organization_id": organization_id,
                "billing_transaction_id": transaction_id,
                "billing_payer_id": billing_payer_id,
                "billing_charge_id": billing_charge_id,
                "matched_amount": matched_amount,
                "match_status": transaction_status,
                "match_reason": match_reason,
                "matched_by_user_id": actor_user.get("user_id") if actor_user else None,
                "matched_at": now_iso(),
            }
        )

        self.billing_repository.update_transaction(
            transaction_id,
            {
                "matched_status": transaction_status,
            },
        )

        self.billing_ledger_repository.create_ledger_entry(
            {
                "organization_id": organization_id,
                "billing_payer_id": billing_payer_id,
                "billing_charge_id": billing_charge_id,
                "billing_transaction_id": transaction_id,
                "entry_kind": "payment_matched",
                "amount_delta": -abs(float(matched_amount)),
                "balance_after": balance_after,
                "note": match_reason or transaction.get("title") or transaction.get("reference"),
                "created_by_user_id": actor_user.get("user_id") if actor_user else None,
                "created_at": now_iso(),
            }
        )
        self.event_repository.log(
            event_type="billing_payment_matched",
            invoice_id=None,
            organization_id=organization_id,
            source="BILLING",
            status_before=current_status,
            status_after=transaction_status,
            decision_reason=match_reason or "Dopasowano wplate do platnika.",
            actor=actor,
            details={
                "billing_payment_match_id": match_id,
                "billing_transaction_id": transaction_id,
                "billing_payer_id": billing_payer_id,
                "matched_amount": matched_amount,
                "transaction_status": transaction_status,
                "matched_amount_total": total_matched_amount,
                "balance_after": balance_after,
            },
        )
        return {
            "billing_payment_match_id": match_id,
            "billing_payer_id": billing_payer_id,
            "matched_amount": matched_amount,
            "transaction_status": transaction_status,
            "matched_amount_total": total_matched_amount,
            "balance_after": balance_after,
        }

    def auto_match_transaction(
        self,
        transaction: dict[str, Any],
        *,
        organization_id: int | None,
        actor_user: dict[str, Any] | None,
        actor: str,
    ) -> dict[str, Any] | None:
        if organization_id is None:
            return None
        searchable = " ".join(
            [
                str(transaction.get("title") or ""),
                str(transaction.get("reference") or ""),
                str(transaction.get("counterparty_name") or ""),
                str(transaction.get("counterparty_account") or ""),
            ]
        )
        identifiers = extract_phone_identifiers(searchable)
        if not identifiers:
            return None
        payers = self.billing_repository.list_payers(organization_id=organization_id)
        payer = None
        for candidate in payers:
            payment_identifier = normalize_phone_identifier(candidate.get("payment_identifier"))
            if payment_identifier and payment_identifier in identifiers:
                payer = candidate
                break
        if not payer:
            return None
        amount = abs(float(transaction.get("amount") or 0))
        if amount <= 0:
            return None
        return self.match_transaction(
            transaction,
            billing_payer_id=int(payer["billing_payer_id"]),
            matched_amount=amount,
            actor_user=actor_user,
            actor=actor,
            organization_id=organization_id,
            match_reason="Automatyczne dopasowanie po identyfikatorze platnosci.",
            match_status="rozliczona",
        )
