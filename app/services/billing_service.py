from __future__ import annotations

import csv
from datetime import datetime
import hashlib
import io
import re
from typing import Any

from app.domain.constants import BILLING_TRANSACTION_MATCH_STATUSES
from app.services.billing_ledger_service import BillingLedgerService
from app.repositories.billing_repository import BillingRepository
from app.repositories.event_repository import EventRepository
from app.repositories.organization_repository import OrganizationRepository
from app.utils import extract_phone_identifiers, normalize_phone_identifier, now_iso

PAYMENT_REVIEW_STATUSES = {
    "needs_review": "Do wyjasnienia",
    "checked": "Sprawdzone",
    "waiting_for_contact": "Czeka na kontakt",
    "waiting_for_payment": "Czeka na wplate",
    "do_not_auto_match": "Nie ruszac automatycznie",
}


class BillingService:
    HEADER_ALIASES = {
        "booking_date": {"bookingdate", "dataksiegowania", "dataoperacji", "data"},
        "value_date": {"valuedate", "datawaluty"},
        "amount": {"amount", "kwota", "kwotatransakcji"},
        "currency": {"currency", "waluta"},
        "title": {"title", "opis", "tytul", "description", "szczegoly"},
        "counterparty_name": {"counterpartyname", "kontrahent", "nadawcaodbiorca", "nazwa"},
        "counterparty_account": {"counterpartyaccount", "rachunekkontrahenta", "nrrachunku", "rachunek"},
        "reference": {"reference", "referencja", "numerreferencyjny"},
    }

    def __init__(
        self,
        billing_repository: BillingRepository,
        event_repository: EventRepository,
        organization_repository: OrganizationRepository,
        billing_ledger_service: BillingLedgerService | None = None,
    ) -> None:
        self.billing_repository = billing_repository
        self.event_repository = event_repository
        self.organization_repository = organization_repository
        self.billing_ledger_service = billing_ledger_service

    def list_models(self, organization_id: int | None = None) -> list[dict[str, Any]]:
        return self.billing_repository.list_models(organization_id=organization_id)

    def list_schools(self, organization_id: int | None = None) -> list[dict[str, Any]]:
        return self.billing_repository.list_schools(organization_id=organization_id)

    def list_payers(self, organization_id: int | None = None) -> list[dict[str, Any]]:
        payers = self.billing_repository.list_payers(organization_id=organization_id)
        payers = self._attach_latest_family_payments(payers, organization_id=organization_id)
        if self.billing_ledger_service:
            balance_rows = self.billing_ledger_service.list_balances(organization_id=organization_id)
            balance_map = {int(item["billing_payer_id"]): item for item in balance_rows}
            for payer in payers:
                balance = balance_map.get(int(payer["billing_payer_id"]))
                if balance:
                    payer["billing_total_charges"] = balance.get("total_charges")
                    payer["billing_total_matches"] = balance.get("total_matches")
                    payer["billing_balance_due"] = balance.get("balance_due")
                    payer["billing_last_payment_at"] = balance.get("last_payment_at")
                    payer["billing_last_payment_amount"] = balance.get("last_payment_amount")
                    payer["billing_last_payment_currency"] = balance.get("last_payment_currency")
                    payer["billing_last_payment_title"] = balance.get("last_payment_title")
                    payer["billing_last_payment_reference"] = balance.get("last_payment_reference")
                    payer["billing_matched_payment_count"] = balance.get("matched_payment_count")
                    if balance.get("last_payment_at"):
                        payer["latest_payment_date"] = balance.get("last_payment_at")
                        payer["latest_payment_amount"] = balance.get("last_payment_amount")
                        payer["latest_payment_currency"] = balance.get("last_payment_currency")
                        payer["latest_payment_title"] = balance.get("last_payment_title")
                else:
                    payer["billing_total_charges"] = 0
                    payer["billing_total_matches"] = 0
                    payer["billing_balance_due"] = 0
                    payer["billing_last_payment_at"] = None
                    payer["billing_last_payment_amount"] = None
                    payer["billing_last_payment_currency"] = None
                    payer["billing_last_payment_title"] = None
                    payer["billing_last_payment_reference"] = None
                    payer["billing_matched_payment_count"] = 0
        return payers

    def list_payer_notes(
        self,
        billing_payer_id: int,
        *,
        organization_id: int | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        payer = self.billing_repository.get_payer_by_id(billing_payer_id, organization_id=organization_id)
        if not payer:
            raise ValueError("Nie znaleziono platnika w wybranej organizacji.")
        return self.billing_repository.list_payer_notes(
            billing_payer_id,
            organization_id=organization_id,
            limit=limit,
        )

    def add_payer_note(
        self,
        billing_payer_id: int,
        note_text: str,
        *,
        actor_user: dict[str, Any] | None,
        actor: str,
        organization_id: int | None = None,
    ) -> dict[str, Any]:
        if organization_id is None:
            raise ValueError("Wybierz organizacje przed dodaniem notatki rozliczeniowej.")

        organization = self.organization_repository.get_by_id(organization_id)
        if not organization or not organization.get("is_active"):
            raise ValueError("Wybrana organizacja nie istnieje albo jest nieaktywna.")

        payer = self.billing_repository.get_payer_by_id(billing_payer_id, organization_id=organization_id)
        if not payer:
            raise ValueError("Nie znaleziono platnika w wybranej organizacji.")

        normalized_text = str(note_text or "").strip()
        if not normalized_text:
            raise ValueError("Notatka rozliczeniowa nie moze byc pusta.")
        if len(normalized_text) > 2000:
            raise ValueError("Notatka rozliczeniowa moze miec maksymalnie 2000 znakow.")
        if not actor_user or not actor_user.get("user_id"):
            raise ValueError("Nie mozna dodac notatki bez zalogowanego uzytkownika.")

        created_note_id = self.billing_repository.add_payer_note(
            {
                "organization_id": organization_id,
                "billing_payer_id": billing_payer_id,
                "author_user_id": int(actor_user["user_id"]),
                "note_type": "operator_note",
                "note_text": normalized_text,
            }
        )
        self.event_repository.log(
            event_type="billing_payer_note_added",
            invoice_id=None,
            organization_id=organization_id,
            source="BILLING",
            status_before=None,
            status_after=None,
            decision_reason="Dodano notatke rozliczeniowa do platnika.",
            actor=actor,
            details={
                "billing_note_id": created_note_id,
                "billing_payer_id": billing_payer_id,
                "note_length": len(normalized_text),
            },
        )
        notes = self.billing_repository.list_payer_notes(
            billing_payer_id,
            organization_id=organization_id,
            limit=100,
        )
        return next(
            (item for item in notes if int(item.get("billing_note_id") or 0) == int(created_note_id)),
            {
                "billing_note_id": created_note_id,
                "organization_id": organization_id,
                "billing_payer_id": billing_payer_id,
                "author_user_id": int(actor_user["user_id"]),
                "author_user_name": actor_user.get("display_name") or actor_user.get("login"),
                "note_type": "operator_note",
                "note_text": normalized_text,
            },
        )

    def list_students(self, organization_id: int | None = None) -> list[dict[str, Any]]:
        students = self.billing_repository.list_students(organization_id=organization_id)
        if not students:
            return []

        payers = self._attach_latest_family_payments(
            self.billing_repository.list_payers(organization_id=organization_id),
            organization_id=organization_id,
        )
        payer_map = {int(item["billing_payer_id"]): item for item in payers}
        for student in students:
            payer = payer_map.get(int(student["billing_payer_id"]))
            if not payer:
                continue
            student["payer_label"] = self._payer_label(payer)
            student["family_last_payment_date"] = payer.get("billing_last_payment_at") or payer.get("latest_payment_date")
            student["family_last_payment_amount"] = payer.get("billing_last_payment_amount")
            if student["family_last_payment_amount"] is None:
                student["family_last_payment_amount"] = payer.get("latest_payment_amount")
            student["family_last_payment_currency"] = (
                payer.get("billing_last_payment_currency") or payer.get("latest_payment_currency")
            )
            student["family_last_payment_title"] = payer.get("billing_last_payment_title") or payer.get(
                "latest_payment_title"
            )
            student["family_balance_due"] = payer.get("billing_balance_due")
        return students

    def list_charges(
        self,
        *,
        organization_id: int | None = None,
        billing_model_id: int | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        return self.billing_repository.list_charges(
            organization_id=organization_id,
            billing_model_id=billing_model_id,
            limit=limit,
        )

    def create_model(
        self,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any]:
        if organization_id is None:
            raise ValueError("Wybierz organizacje przed dodaniem modelu rozliczen.")

        organization = self.organization_repository.get_by_id(organization_id)
        if not organization or not organization.get("is_active"):
            raise ValueError("Wybrana organizacja nie istnieje albo jest nieaktywna.")

        name = self._normalize_required_text(payload.get("name"), field_label="Nazwa modelu rozliczen")
        school_year = self._normalize_required_text(payload.get("school_year"), field_label="Rok szkolny")
        lesson_day = self._normalize_optional_text(payload.get("lesson_day"))
        settlement_mode = self._normalize_settlement_mode(payload.get("settlement_mode"))
        profile_type = self._normalize_optional_text(payload.get("profile_type")) or "education_student"
        monthly_rate_amount = self._normalize_optional_amount(payload.get("monthly_rate_amount"))
        semester_rate_amount = self._normalize_optional_amount(payload.get("semester_rate_amount"))
        sibling_discount_amount = self._normalize_amount_with_default(payload.get("sibling_discount_amount"), default=100)
        large_family_discount_amount = self._normalize_amount_with_default(
            payload.get("large_family_discount_amount"),
            default=50,
        )
        intro_free_lessons_count = self._normalize_non_negative_int(
            payload.get("intro_free_lessons_count"),
            field_label="Liczba darmowych zajec na start",
            default=1,
        )
        contract_required = 1 if payload.get("contract_required") in {True, 1, "1", "true", "tak"} else 0
        notes = self._normalize_optional_text(payload.get("notes"))

        if monthly_rate_amount is None and semester_rate_amount is None:
            raise ValueError("Podaj co najmniej jedna stawke modelu rozliczen.")
        if settlement_mode == "monthly" and monthly_rate_amount is None:
            raise ValueError("Dla modelu miesiecznego podaj stawke za zajecia miesieczne.")
        if settlement_mode == "semester" and semester_rate_amount is None:
            raise ValueError("Dla modelu semestralnego podaj stawke za zajecia semestralne.")

        existing = self.billing_repository.get_model_by_name(name, organization_id=organization_id)
        if existing:
            raise ValueError("Model rozliczen o tej nazwie jest juz dodany w tej organizacji.")

        model_id = self.billing_repository.create_model(
            {
                "organization_id": organization_id,
                "name": name,
                "profile_type": profile_type,
                "school_year": school_year,
                "lesson_day": lesson_day,
                "settlement_mode": settlement_mode,
                "monthly_rate_amount": monthly_rate_amount,
                "semester_rate_amount": semester_rate_amount,
                "sibling_discount_amount": sibling_discount_amount,
                "large_family_discount_amount": large_family_discount_amount,
                "intro_free_lessons_count": intro_free_lessons_count,
                "contract_required": contract_required,
                "notes": notes,
                "is_active": 1 if payload.get("is_active", True) not in {False, 0, "0", "false"} else 0,
            }
        )
        created = self.billing_repository.get_model_by_id(model_id, organization_id=organization_id)
        assert created is not None

        self.event_repository.log(
            event_type="billing_model_created",
            invoice_id=None,
            organization_id=organization_id,
            source="BILLING",
            status_before=None,
            status_after="aktywny" if created.get("is_active") else "nieaktywny",
            decision_reason=f"Dodano model rozliczen {created['name']}.",
            actor=actor,
            details={
                "billing_model_id": model_id,
                "school_year": created["school_year"],
                "settlement_mode": created["settlement_mode"],
                "created_by_user_id": actor_user.get("user_id"),
            },
        )
        return created

    def list_bank_accounts(self, organization_id: int | None = None) -> list[dict[str, Any]]:
        return self.billing_repository.list_bank_accounts(organization_id=organization_id)

    def list_transactions(
        self,
        *,
        organization_id: int | None = None,
        billing_bank_account_id: int | None = None,
        matched_status: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        normalized_status = str(matched_status or "").strip()
        if normalized_status and normalized_status not in BILLING_TRANSACTION_MATCH_STATUSES:
            raise ValueError("Nieprawidlowy status dopasowania transakcji.")
        return self.billing_repository.list_transactions(
            organization_id=organization_id,
            billing_bank_account_id=billing_bank_account_id,
            matched_status=normalized_status or None,
            limit=limit,
        )

    def list_payment_review_events(
        self,
        billing_transaction_id: int,
        *,
        organization_id: int | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        if organization_id is None:
            raise ValueError("Wybierz organizacje przed sprawdzeniem statusu wplaty.")
        transaction = self.billing_repository.get_transaction_by_id(
            billing_transaction_id,
            organization_id=organization_id,
        )
        if not transaction:
            raise ValueError("Nie znaleziono wplaty w wybranej organizacji.")
        events = self.billing_repository.list_payment_review_events(
            billing_transaction_id,
            organization_id=organization_id,
            limit=limit,
        )
        return {
            "billing_transaction_id": billing_transaction_id,
            "organization_id": organization_id,
            "current": events[0] if events else None,
            "history": events,
        }

    def add_payment_review_event(
        self,
        billing_transaction_id: int,
        status: str,
        note_text: str | None = None,
        *,
        actor_user: dict[str, Any] | None,
        actor: str,
        organization_id: int | None = None,
    ) -> dict[str, Any]:
        if organization_id is None:
            raise ValueError("Wybierz organizacje przed zapisaniem statusu wplaty.")

        organization = self.organization_repository.get_by_id(organization_id)
        if not organization or not organization.get("is_active"):
            raise ValueError("Wybrana organizacja nie istnieje albo jest nieaktywna.")

        transaction = self.billing_repository.get_transaction_by_id(
            billing_transaction_id,
            organization_id=organization_id,
        )
        if not transaction:
            raise ValueError("Nie znaleziono wplaty w wybranej organizacji.")
        direction = str(transaction.get("direction") or "").strip().lower()
        if direction and direction not in {"uznanie", "inflow", "credit"}:
            raise ValueError("Status operacyjny mozna ustawic tylko dla wplaty przychodzacej.")

        normalized_status = str(status or "").strip()
        if normalized_status not in PAYMENT_REVIEW_STATUSES:
            raise ValueError("Nieprawidlowy status operacyjny wplaty.")

        normalized_note = str(note_text or "").strip()
        if len(normalized_note) > 1000:
            raise ValueError("Notatka statusu moze miec maksymalnie 1000 znakow.")
        if not actor_user or not actor_user.get("user_id"):
            raise ValueError("Nie mozna zapisac statusu bez zalogowanego uzytkownika.")

        review_event_id = self.billing_repository.add_payment_review_event(
            {
                "organization_id": organization_id,
                "billing_transaction_id": billing_transaction_id,
                "status": normalized_status,
                "note_text": normalized_note or None,
                "created_by_user_id": int(actor_user["user_id"]),
            }
        )
        self.event_repository.log(
            event_type="billing_payment_review_status_changed",
            invoice_id=None,
            organization_id=organization_id,
            source="BILLING",
            status_before=None,
            status_after=normalized_status,
            decision_reason="Zmieniono operacyjny status wplaty.",
            actor=actor,
            details={
                "billing_payment_review_event_id": review_event_id,
                "billing_transaction_id": billing_transaction_id,
                "status": normalized_status,
                "note_length": len(normalized_note),
            },
        )
        events = self.billing_repository.list_payment_review_events(
            billing_transaction_id,
            organization_id=organization_id,
            limit=20,
        )
        return next(
            (
                item
                for item in events
                if int(item.get("billing_payment_review_event_id") or 0) == int(review_event_id)
            ),
            {
                "billing_payment_review_event_id": review_event_id,
                "organization_id": organization_id,
                "billing_transaction_id": billing_transaction_id,
                "status": normalized_status,
                "note_text": normalized_note or None,
                "created_by_user_id": int(actor_user["user_id"]),
                "created_by_user_name": actor_user.get("display_name") or actor_user.get("login"),
            },
        )

    def generate_charges_for_model(
        self,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any]:
        if organization_id is None:
            raise ValueError("Wybierz organizacje przed generowaniem naleznosci.")

        organization = self.organization_repository.get_by_id(organization_id)
        if not organization or not organization.get("is_active"):
            raise ValueError("Wybrana organizacja nie istnieje albo jest nieaktywna.")

        try:
            billing_model_id = int(payload.get("billing_model_id") or 0)
        except (TypeError, ValueError):
            raise ValueError("Wybierz model rozliczen do wygenerowania naleznosci.") from None

        model = self.billing_repository.get_model_by_id(billing_model_id, organization_id=organization_id)
        if not model:
            raise ValueError("Nie znaleziono modelu rozliczen w tej organizacji.")
        if not model.get("is_active"):
            raise ValueError("Nie mozna generowac naleznosci dla nieaktywnego modelu rozliczen.")

        period_label = self._normalize_required_text(payload.get("period_label"), field_label="Okres rozliczeniowy")
        due_date = self._normalize_date(payload.get("due_date"), field_label="termin platnosci")
        lesson_count = self._normalize_positive_int(
            payload.get("lesson_count"),
            field_label="Liczba zajec",
            default=1,
        )
        notes = self._normalize_optional_text(payload.get("notes"))

        existing_batch = self.billing_repository.get_charge_batch_by_model_and_period(
            organization_id=organization_id,
            billing_model_id=billing_model_id,
            period_label=period_label,
        )
        if existing_batch:
            raise ValueError("Dla tego modelu i okresu naleznosci zostaly juz wygenerowane.")

        unit_rate_amount = self._resolve_charge_unit_rate(model)
        intro_free_lessons_count = int(model.get("intro_free_lessons_count") or 0)
        sibling_discount_amount = self._round_amount(float(model.get("sibling_discount_amount") or 0))
        large_family_discount_amount = self._round_amount(float(model.get("large_family_discount_amount") or 0))
        school_year = str(model.get("school_year") or "")

        students = [
            item
            for item in self.billing_repository.list_students(organization_id=organization_id, only_active=True)
            if int(item.get("billing_model_id") or 0) == billing_model_id
        ]
        if not students:
            raise ValueError("Brak aktywnych uczniow przypisanych do tego modelu rozliczen.")

        payers = {
            int(item["billing_payer_id"]): item
            for item in self.billing_repository.list_payers(organization_id=organization_id)
        }

        students_by_payer: dict[int, list[dict[str, Any]]] = {}
        for student in students:
            payer_id = int(student["billing_payer_id"])
            students_by_payer.setdefault(payer_id, []).append(student)

        charge_drafts: list[dict[str, Any]] = []
        student_state_updates: dict[int, dict[str, Any]] = {}
        payer_state_updates: dict[int, dict[str, Any]] = {}

        for payer_id in sorted(students_by_payer):
            payer = payers.get(payer_id)
            if not payer:
                raise ValueError("Brakuje danych rodziny dla jednego z uczniow przypisanych do modelu.")

            payer_state: dict[str, Any] | None = None
            if self._normalize_boolean_flag(payer.get("has_large_family_card")) and large_family_discount_amount > 0:
                payer_state = self.billing_repository.get_payer_charge_state(
                    organization_id=organization_id,
                    billing_payer_id=payer_id,
                    school_year=school_year,
                )
                if payer_state:
                    payer_state = dict(payer_state)
                else:
                    payer_state = {
                        "organization_id": organization_id,
                        "billing_payer_id": payer_id,
                        "school_year": school_year,
                        "large_family_discount_remaining_amount": large_family_discount_amount,
                        "large_family_discount_initialized": 1,
                    }
                if not self._normalize_boolean_flag(payer_state.get("large_family_discount_initialized")):
                    payer_state["large_family_discount_remaining_amount"] = large_family_discount_amount
                    payer_state["large_family_discount_initialized"] = 1

            ordered_students = sorted(
                students_by_payer[payer_id],
                key=lambda item: (
                    int(item.get("family_billing_order") or 1),
                    int(item.get("billing_student_id") or 0),
                ),
            )

            for student in ordered_students:
                student_id = int(student["billing_student_id"])
                family_billing_order = max(1, int(student.get("family_billing_order") or 1))
                student_state = self.billing_repository.get_student_charge_state(
                    organization_id=organization_id,
                    billing_student_id=student_id,
                    school_year=school_year,
                )
                if student_state:
                    student_state = dict(student_state)
                else:
                    student_state = {
                        "organization_id": organization_id,
                        "billing_student_id": student_id,
                        "school_year": school_year,
                        "intro_free_lessons_remaining": intro_free_lessons_count,
                        "sibling_discount_remaining_amount": sibling_discount_amount if family_billing_order > 1 else 0,
                        "sibling_discount_initialized": 1 if family_billing_order > 1 and sibling_discount_amount > 0 else 0,
                    }

                if family_billing_order > 1 and sibling_discount_amount > 0:
                    if not self._normalize_boolean_flag(student_state.get("sibling_discount_initialized")):
                        student_state["sibling_discount_remaining_amount"] = sibling_discount_amount
                        student_state["sibling_discount_initialized"] = 1
                else:
                    student_state["sibling_discount_remaining_amount"] = 0

                base_amount = self._round_amount(lesson_count * unit_rate_amount)
                intro_remaining = int(student_state.get("intro_free_lessons_remaining") or 0)
                intro_lessons_used = min(intro_remaining, lesson_count)
                intro_discount = self._round_amount(intro_lessons_used * unit_rate_amount)
                available_after_intro = self._round_amount(max(base_amount - intro_discount, 0))

                sibling_remaining = self._round_amount(float(student_state.get("sibling_discount_remaining_amount") or 0))
                applied_sibling_discount = 0.0
                if family_billing_order > 1 and sibling_remaining > 0 and available_after_intro > 0:
                    applied_sibling_discount = self._round_amount(min(sibling_remaining, available_after_intro))
                available_after_sibling = self._round_amount(max(available_after_intro - applied_sibling_discount, 0))

                applied_large_family_discount = 0.0
                if payer_state:
                    payer_remaining = self._round_amount(
                        float(payer_state.get("large_family_discount_remaining_amount") or 0)
                    )
                    if payer_remaining > 0 and available_after_sibling > 0:
                        applied_large_family_discount = self._round_amount(min(payer_remaining, available_after_sibling))
                        payer_state["large_family_discount_remaining_amount"] = self._round_amount(
                            max(payer_remaining - applied_large_family_discount, 0)
                        )

                total_amount = self._round_amount(
                    max(base_amount - intro_discount - applied_sibling_discount - applied_large_family_discount, 0)
                )

                student_state["intro_free_lessons_remaining"] = max(intro_remaining - intro_lessons_used, 0)
                if family_billing_order > 1:
                    student_state["sibling_discount_remaining_amount"] = self._round_amount(
                        max(sibling_remaining - applied_sibling_discount, 0)
                    )
                    if sibling_discount_amount > 0:
                        student_state["sibling_discount_initialized"] = 1

                charge_drafts.append(
                    {
                        "organization_id": organization_id,
                        "billing_model_id": billing_model_id,
                        "billing_student_id": student_id,
                        "billing_payer_id": payer_id,
                        "school_year": school_year,
                        "period_label": period_label,
                        "due_date": due_date,
                        "lesson_count": lesson_count,
                        "unit_rate_amount": unit_rate_amount,
                        "base_amount": base_amount,
                        "intro_free_discount_amount": intro_discount,
                        "sibling_discount_amount": applied_sibling_discount,
                        "large_family_discount_amount": applied_large_family_discount,
                        "total_amount": total_amount,
                        "status": "otwarta",
                        "notes": notes,
                    }
                )
                student_state_updates[student_id] = student_state

            if payer_state:
                payer_state_updates[payer_id] = payer_state

        batch_id = self.billing_repository.create_charge_batch(
            {
                "organization_id": organization_id,
                "billing_model_id": billing_model_id,
                "school_year": school_year,
                "period_type": model["settlement_mode"],
                "period_label": period_label,
                "due_date": due_date,
                "lesson_count": lesson_count,
                "generated_by_user_id": actor_user.get("user_id"),
                "notes": notes,
            }
        )

        for charge in charge_drafts:
            self.billing_repository.create_charge(
                {
                    **charge,
                    "billing_charge_batch_id": batch_id,
                }
            )

        for state in student_state_updates.values():
            state_id = state.get("billing_student_charge_state_id")
            if state_id:
                self.billing_repository.update_student_charge_state(
                    int(state_id),
                    {
                        "intro_free_lessons_remaining": state["intro_free_lessons_remaining"],
                        "sibling_discount_remaining_amount": state["sibling_discount_remaining_amount"],
                        "sibling_discount_initialized": state.get("sibling_discount_initialized", 0),
                    },
                )
            else:
                self.billing_repository.create_student_charge_state(state)

        for state in payer_state_updates.values():
            state_id = state.get("billing_payer_charge_state_id")
            if state_id:
                self.billing_repository.update_payer_charge_state(
                    int(state_id),
                    {
                        "large_family_discount_remaining_amount": state["large_family_discount_remaining_amount"],
                        "large_family_discount_initialized": state.get("large_family_discount_initialized", 0),
                    },
                )
            else:
                self.billing_repository.create_payer_charge_state(state)

        created_batch = self.billing_repository.get_charge_batch_by_id(batch_id, organization_id=organization_id)
        assert created_batch is not None
        created_charges = self.billing_repository.list_charges(
            organization_id=organization_id,
            billing_charge_batch_id=batch_id,
            limit=max(len(charge_drafts), 1),
        )
        total_amount = self._round_amount(sum(float(item.get("total_amount") or 0) for item in created_charges))
        if self.billing_ledger_service:
            self.billing_ledger_service.record_charge_generation(
                created_charges,
                actor_user=actor_user,
                actor=actor,
                organization_id=organization_id,
            )

        self.event_repository.log(
            event_type="billing_charge_batch_generated",
            invoice_id=None,
            organization_id=organization_id,
            source="BILLING",
            status_before=None,
            status_after="otwarta",
            decision_reason=f"Wygenerowano naleznosci {period_label} dla modelu {model['name']}.",
            actor=actor,
            details={
                "billing_charge_batch_id": batch_id,
                "billing_model_id": billing_model_id,
                "period_label": period_label,
                "lesson_count": lesson_count,
                "charge_count": len(created_charges),
                "total_amount": total_amount,
                "generated_by_user_id": actor_user.get("user_id"),
            },
        )

        return {
            "batch": created_batch,
            "charges": created_charges,
            "charge_count": len(created_charges),
            "total_amount": total_amount,
        }

    def create_payer(
        self,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any]:
        if organization_id is None:
            raise ValueError("Wybierz organizacje przed dodaniem rodziny.")

        organization = self.organization_repository.get_by_id(organization_id)
        if not organization or not organization.get("is_active"):
            raise ValueError("Wybrana organizacja nie istnieje albo jest nieaktywna.")

        contact_phone = self._normalize_required_phone(payload.get("contact_phone"))
        display_name = self._normalize_optional_text(payload.get("display_name"))
        email = self._normalize_optional_text(payload.get("email"))
        notes = self._normalize_optional_text(payload.get("notes"))
        has_large_family_card = self._normalize_boolean_flag(payload.get("has_large_family_card"))

        existing = self.billing_repository.get_payer_by_payment_identifier(
            contact_phone,
            organization_id=organization_id,
        )
        if existing:
            raise ValueError("Ta rodzina jest juz dodana w tej organizacji dla tego numeru telefonu.")

        payer_id = self.billing_repository.create_payer(
            {
                "organization_id": organization_id,
                "display_name": display_name,
                "contact_phone": contact_phone,
                "payment_identifier": contact_phone,
                "has_large_family_card": has_large_family_card,
                "email": email,
                "notes": notes,
                "is_active": 1 if payload.get("is_active", True) not in {False, 0, "0", "false"} else 0,
            }
        )
        created = self.billing_repository.get_payer_by_id(payer_id, organization_id=organization_id)
        assert created is not None
        created["payer_label"] = self._payer_label(created)

        self.event_repository.log(
            event_type="billing_payer_created",
            invoice_id=None,
            organization_id=organization_id,
            source="BILLING",
            status_before=None,
            status_after="aktywna" if created.get("is_active") else "nieaktywna",
            decision_reason=f"Dodano rodzine {created['payer_label']}.",
            actor=actor,
            details={
                "billing_payer_id": payer_id,
                "contact_phone": created["contact_phone"],
                "created_by_user_id": actor_user.get("user_id"),
            },
        )
        return created

    def create_student(
        self,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any]:
        if organization_id is None:
            raise ValueError("Wybierz organizacje przed dodaniem ucznia.")

        organization = self.organization_repository.get_by_id(organization_id)
        if not organization or not organization.get("is_active"):
            raise ValueError("Wybrana organizacja nie istnieje albo jest nieaktywna.")

        payer: dict[str, Any] | None = None
        payer_id: int | None = None
        raw_payer_id = payload.get("billing_payer_id")
        raw_payer_phone = self._normalize_optional_text(payload.get("payer_contact_phone"))
        payer_phone = normalize_phone_identifier(raw_payer_phone) if raw_payer_phone else None
        payer_display_name = self._normalize_optional_text(payload.get("payer_display_name"))

        if str(raw_payer_id or "").strip():
            try:
                payer_id = int(raw_payer_id)
            except (TypeError, ValueError):
                raise ValueError("Nieprawidlowy identyfikator rodziny.") from None
            payer = self.billing_repository.get_payer_by_id(payer_id, organization_id=organization_id)
            if not payer:
                raise ValueError("Nie znaleziono rodziny w tej organizacji.")

        if payer and payer_phone and str(payer.get("contact_phone") or "") != payer_phone:
            raise ValueError("Wybrana rodzina ma inny numer telefonu niz wpisany przy uczniu.")

        if not payer:
            if not payer_phone:
                raise ValueError("Wybierz rodzine albo podaj numer telefonu rodziny dla ucznia.")
            payer = self.billing_repository.get_payer_by_payment_identifier(
                payer_phone,
                organization_id=organization_id,
            )
            if not payer:
                payer = self.create_payer(
                    {
                        "display_name": payer_display_name,
                        "contact_phone": payer_phone,
                        "email": self._normalize_optional_text(payload.get("payer_email")),
                        "has_large_family_card": payload.get("payer_has_large_family_card"),
                        "notes": self._normalize_optional_text(payload.get("payer_notes")),
                    },
                    actor_user=actor_user,
                    actor=actor,
                    organization_id=organization_id,
                )
            payer_id = int(payer["billing_payer_id"])

        school_id: int | None = None
        raw_school_id = payload.get("billing_school_id")
        if str(raw_school_id or "").strip():
            try:
                school_id = int(raw_school_id)
            except (TypeError, ValueError):
                raise ValueError("Nieprawidlowy identyfikator szkoly.") from None
            school = self.billing_repository.get_school_by_id(school_id, organization_id=organization_id)
            if not school:
                raise ValueError("Nie znaleziono szkoly w tej organizacji.")

        model_id: int | None = None
        model: dict[str, Any] | None = None
        raw_model_id = payload.get("billing_model_id")
        if str(raw_model_id or "").strip():
            try:
                model_id = int(raw_model_id)
            except (TypeError, ValueError):
                raise ValueError("Nieprawidlowy identyfikator modelu rozliczen.") from None
            model = self.billing_repository.get_model_by_id(model_id, organization_id=organization_id)
            if not model:
                raise ValueError("Nie znaleziono modelu rozliczen w tej organizacji.")

        full_name = self._normalize_required_text(payload.get("full_name"), field_label="Imie i nazwisko ucznia")
        lesson_day = self._normalize_optional_text(payload.get("lesson_day")) or (model.get("lesson_day") if model else None)
        family_billing_order = self._normalize_positive_int(
            payload.get("family_billing_order"),
            field_label="Kolejnosc ucznia w rodzinie",
            default=1,
        )
        group_name = self._normalize_optional_text(payload.get("group_name"))
        notes = self._normalize_optional_text(payload.get("notes"))

        student_id = self.billing_repository.create_student(
            {
                "organization_id": organization_id,
                "billing_payer_id": payer_id,
                "billing_school_id": school_id,
                "billing_model_id": model_id,
                "full_name": full_name,
                "lesson_day": lesson_day,
                "family_billing_order": family_billing_order,
                "group_name": group_name,
                "notes": notes,
                "is_active": 1 if payload.get("is_active", True) not in {False, 0, "0", "false"} else 0,
            }
        )
        created = self.billing_repository.get_student_by_id(student_id, organization_id=organization_id)
        assert created is not None
        created["payer_label"] = self._payer_label(payer)

        self.event_repository.log(
            event_type="billing_student_created",
            invoice_id=None,
            organization_id=organization_id,
            source="BILLING",
            status_before=None,
            status_after="aktywny" if created.get("is_active") else "nieaktywny",
            decision_reason=f"Dodano ucznia {created['full_name']}.",
            actor=actor,
            details={
                "billing_student_id": student_id,
                "billing_payer_id": payer_id,
                "billing_school_id": created.get("billing_school_id"),
                "billing_model_id": created.get("billing_model_id"),
                "created_by_user_id": actor_user.get("user_id"),
            },
        )
        return created

    def create_school(
        self,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any]:
        if organization_id is None:
            raise ValueError("Wybierz organizacje przed dodaniem szkoly.")

        organization = self.organization_repository.get_by_id(organization_id)
        if not organization or not organization.get("is_active"):
            raise ValueError("Wybrana organizacja nie istnieje albo jest nieaktywna.")

        full_name = self._normalize_required_text(payload.get("full_name"), field_label="Pelna nazwa szkoly")
        short_name = self._normalize_school_short_name(payload.get("short_name"))
        city = self._normalize_optional_text(payload.get("city"))
        notes = self._normalize_optional_text(payload.get("notes"))

        schools = self.billing_repository.list_schools(organization_id=organization_id)
        if any(str(item.get("full_name") or "").strip().casefold() == full_name.casefold() for item in schools):
            raise ValueError("Ta szkola jest juz dodana w tej organizacji.")

        existing_by_short_name = self.billing_repository.get_school_by_short_name(
            short_name,
            organization_id=organization_id,
        )
        if existing_by_short_name:
            raise ValueError("Ten skrot szkoly jest juz uzywany w tej organizacji.")

        school_id = self.billing_repository.create_school(
            {
                "organization_id": organization_id,
                "full_name": full_name,
                "short_name": short_name,
                "city": city,
                "notes": notes,
                "is_active": 1 if payload.get("is_active", True) not in {False, 0, "0", "false"} else 0,
            }
        )
        created = self.billing_repository.get_school_by_id(school_id, organization_id=organization_id)
        assert created is not None

        self.event_repository.log(
            event_type="billing_school_created",
            invoice_id=None,
            organization_id=organization_id,
            source="BILLING",
            status_before=None,
            status_after="aktywna" if created.get("is_active") else "nieaktywna",
            decision_reason=f"Dodano szkole {created['short_name']}.",
            actor=actor,
            details={
                "billing_school_id": school_id,
                "full_name": created["full_name"],
                "short_name": created["short_name"],
                "created_by_user_id": actor_user.get("user_id"),
            },
        )
        return created

    def create_bank_account(
        self,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any]:
        if organization_id is None:
            raise ValueError("Wybierz organizacje przed dodaniem rachunku bankowego.")

        organization = self.organization_repository.get_by_id(organization_id)
        if not organization or not organization.get("is_active"):
            raise ValueError("Wybrana organizacja nie istnieje albo jest nieaktywna.")

        account_name = str(payload.get("account_name") or "").strip()
        if not account_name:
            raise ValueError("Nazwa rachunku bankowego jest wymagana.")

        iban = self._normalize_iban(payload.get("iban"))
        existing = self.billing_repository.get_bank_account_by_iban(iban, organization_id=organization_id)
        if existing:
            raise ValueError("Ten rachunek bankowy jest juz dodany w tej organizacji.")

        bank_account_id = self.billing_repository.create_bank_account(
            {
                "organization_id": organization_id,
                "account_name": account_name,
                "bank_name": self._normalize_optional_text(payload.get("bank_name")),
                "iban": iban,
                "currency": self._normalize_currency(payload.get("currency") or "PLN"),
                "is_active": 1 if payload.get("is_active", True) not in {False, 0, "0", "false"} else 0,
            }
        )
        created = self.billing_repository.get_bank_account_by_id(
            bank_account_id,
            organization_id=organization_id,
        )
        assert created is not None

        self.event_repository.log(
            event_type="billing_bank_account_created",
            invoice_id=None,
            organization_id=organization_id,
            source="BANK_STATEMENT",
            status_before=None,
            status_after="aktywny" if created.get("is_active") else "nieaktywny",
            decision_reason=f"Dodano rachunek bankowy {created['account_name']}.",
            actor=actor,
            details={
                "billing_bank_account_id": bank_account_id,
                "iban": created["iban"],
                "currency": created["currency"],
                "created_by_user_id": actor_user.get("user_id"),
            },
        )
        return created

    def import_statement_csv(
        self,
        bank_account_id: int,
        csv_content: str,
        *,
        source_file_name: str | None,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any]:
        if organization_id is None:
            raise ValueError("Wybierz organizacje przed importem wyciagu.")

        bank_account = self.billing_repository.get_bank_account_by_id(
            bank_account_id,
            organization_id=organization_id,
        )
        if not bank_account:
            raise ValueError("Nie znaleziono rachunku bankowego w tej organizacji.")
        if not bank_account.get("is_active"):
            raise ValueError("Nie mozna importowac wyciagu do nieaktywnego rachunku bankowego.")

        rows = self._parse_csv_rows(csv_content)
        statement_import_id = self.billing_repository.create_statement_import(
            {
                "organization_id": organization_id,
                "billing_bank_account_id": bank_account_id,
                "source_type": "manual_csv",
                "source_file_name": self._normalize_optional_text(source_file_name),
                "imported_by_user_id": actor_user.get("user_id"),
                "imported_at": now_iso(),
                "status": "przetwarzany",
            }
        )

        imported_count = 0
        skipped_count = 0
        auto_matched_count = 0

        try:
            normalized_rows = [
                self._normalize_statement_row(row, bank_account=bank_account, row_number=index)
                for index, row in enumerate(rows, start=1)
            ]

            for source_row, normalized_row in zip(rows, normalized_rows):
                transaction_hash = self._build_transaction_hash(bank_account_id, normalized_row)
                existing = self.billing_repository.get_transaction_by_hash(
                    organization_id=organization_id,
                    billing_bank_account_id=bank_account_id,
                    transaction_hash=transaction_hash,
                )
                if existing:
                    skipped_count += 1
                    continue

                transaction_id = self.billing_repository.create_transaction(
                    {
                        "organization_id": organization_id,
                        "billing_bank_account_id": bank_account_id,
                        "billing_statement_import_id": statement_import_id,
                        "booking_date": normalized_row["booking_date"],
                        "value_date": normalized_row.get("value_date"),
                        "amount": normalized_row["amount"],
                        "currency": normalized_row["currency"],
                        "direction": normalized_row["direction"],
                        "counterparty_name": normalized_row.get("counterparty_name"),
                        "counterparty_account": normalized_row.get("counterparty_account"),
                        "title": normalized_row.get("title"),
                        "reference": normalized_row.get("reference"),
                        "raw_data": source_row,
                        "transaction_hash": transaction_hash,
                    }
                )
                imported_count += 1

                if self.billing_ledger_service:
                    created_transaction = self.billing_repository.get_transaction_by_id(
                        transaction_id,
                        organization_id=organization_id,
                    )
                    if created_transaction:
                        match_result = self.billing_ledger_service.auto_match_transaction(
                            created_transaction,
                            organization_id=organization_id,
                            actor_user=actor_user,
                            actor=actor,
                        )
                        if match_result:
                            auto_matched_count += 1
        except ValueError as error:
            self.billing_repository.update_statement_import(
                statement_import_id,
                {
                    "row_count": len(rows),
                    "imported_transaction_count": imported_count,
                    "skipped_transaction_count": skipped_count,
                    "status": "blad",
                    "notes": str(error),
                },
            )
            raise

        self.billing_repository.update_statement_import(
            statement_import_id,
            {
                "row_count": len(rows),
                "imported_transaction_count": imported_count,
                "skipped_transaction_count": skipped_count,
                "status": "zaimportowany",
                "notes": None,
            },
        )

        statement_import = self.billing_repository.get_statement_import_by_id(
            statement_import_id,
            organization_id=organization_id,
        )
        assert statement_import is not None

        self.event_repository.log(
            event_type="billing_statement_imported",
            invoice_id=None,
            organization_id=organization_id,
            source="BANK_STATEMENT",
            status_before=None,
            status_after="zaimportowany",
            decision_reason=f"Zaladowano wyciag CSV do rachunku {bank_account['account_name']}.",
            actor=actor,
            details={
                "billing_statement_import_id": statement_import_id,
                "billing_bank_account_id": bank_account_id,
                "source_file_name": statement_import.get("source_file_name"),
                "row_count": len(rows),
                "imported_transaction_count": imported_count,
                "skipped_transaction_count": skipped_count,
                "auto_matched_transaction_count": auto_matched_count,
            },
        )
        return {
            "statement_import": statement_import,
            "imported_transaction_count": imported_count,
            "skipped_transaction_count": skipped_count,
            "auto_matched_transaction_count": auto_matched_count,
        }

    def _parse_csv_rows(self, csv_content: str) -> list[dict[str, str]]:
        normalized_content = str(csv_content or "").lstrip("\ufeff").strip()
        if not normalized_content:
            raise ValueError("Plik wyciagu CSV jest pusty.")

        first_line = normalized_content.splitlines()[0]
        delimiter = ";" if first_line.count(";") >= first_line.count(",") else ","
        reader = csv.DictReader(io.StringIO(normalized_content), delimiter=delimiter)
        if not reader.fieldnames:
            raise ValueError("Nie udalo sie odczytac naglowkow pliku CSV.")

        rows: list[dict[str, str]] = []
        for raw_row in reader:
            if raw_row is None:
                continue
            row = {str(key or "").strip(): str(value or "").strip() for key, value in raw_row.items()}
            if not any(value for value in row.values()):
                continue
            rows.append(row)

        if not rows:
            raise ValueError("Wyciag nie zawiera zadnych wierszy transakcji.")
        return rows

    def _normalize_statement_row(
        self,
        row: dict[str, str],
        *,
        bank_account: dict[str, Any],
        row_number: int,
    ) -> dict[str, Any]:
        normalized_lookup = {self._normalize_header_key(key): value for key, value in row.items()}

        booking_date = self._normalize_date(
            self._pick_value(normalized_lookup, "booking_date"),
            field_label=f"data ksiegowania (wiersz {row_number})",
        )
        value_date_raw = self._pick_value(normalized_lookup, "value_date")
        value_date = (
            self._normalize_date(value_date_raw, field_label=f"data waluty (wiersz {row_number})")
            if value_date_raw
            else None
        )
        amount = self._normalize_amount(
            self._pick_value(normalized_lookup, "amount"),
            field_label=f"kwota (wiersz {row_number})",
        )
        currency = self._normalize_currency(
            self._pick_value(normalized_lookup, "currency") or bank_account.get("currency") or "PLN"
        )

        return {
            "booking_date": booking_date,
            "value_date": value_date,
            "amount": amount,
            "currency": currency,
            "direction": "uznanie" if amount >= 0 else "obciazenie",
            "title": self._normalize_optional_text(self._pick_value(normalized_lookup, "title")),
            "counterparty_name": self._normalize_optional_text(self._pick_value(normalized_lookup, "counterparty_name")),
            "counterparty_account": self._normalize_optional_text(
                self._pick_value(normalized_lookup, "counterparty_account")
            ),
            "reference": self._normalize_optional_text(self._pick_value(normalized_lookup, "reference")),
        }

    def _pick_value(self, normalized_lookup: dict[str, str], canonical_name: str) -> str:
        aliases = self.HEADER_ALIASES[canonical_name]
        for alias in aliases:
            if alias in normalized_lookup:
                return str(normalized_lookup[alias] or "").strip()
        if canonical_name in {"booking_date", "amount"}:
            raise ValueError(f"Brakuje wymaganej kolumny CSV: {canonical_name}.")
        return ""

    def _normalize_header_key(self, value: Any) -> str:
        normalized = str(value or "").strip().lower()
        normalized = normalized.translate(
            str.maketrans(
                {
                    "\u0105": "a",
                    "\u0107": "c",
                    "\u0119": "e",
                    "\u0142": "l",
                    "\u0144": "n",
                    "\u00f3": "o",
                    "\u015b": "s",
                    "\u017c": "z",
                    "\u017a": "z",
                }
            )
        )
        return re.sub(r"[^a-z0-9]+", "", normalized)

    def _normalize_iban(self, value: Any) -> str:
        normalized = re.sub(r"\s+", "", str(value or "").upper())
        if len(normalized) < 15:
            raise ValueError("Numer IBAN rachunku bankowego jest nieprawidlowy.")
        if not normalized[:2].isalpha() or not normalized[2:].isalnum():
            raise ValueError("Numer IBAN rachunku bankowego jest nieprawidlowy.")
        return normalized

    def _normalize_currency(self, value: Any) -> str:
        normalized = str(value or "").strip().upper()
        if not re.fullmatch(r"[A-Z]{3}", normalized):
            raise ValueError("Waluta musi miec format kodu ISO, na przyklad PLN albo EUR.")
        return normalized

    def _normalize_optional_text(self, value: Any) -> str | None:
        normalized = str(value or "").strip()
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized or None

    def _normalize_required_text(self, value: Any, *, field_label: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError(f"{field_label} jest wymagana.")
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized

    def _normalize_school_short_name(self, value: Any) -> str:
        normalized = self._normalize_required_text(value, field_label="Skrot szkoly")
        return normalized.upper()

    def _normalize_settlement_mode(self, value: Any) -> str:
        normalized = str(value or "").strip().lower()
        if normalized not in {"monthly", "semester", "custom"}:
            raise ValueError("Tryb rozliczen musi miec wartosc monthly, semester albo custom.")
        return normalized

    def _normalize_required_phone(self, value: Any) -> str:
        normalized = normalize_phone_identifier(value)
        if not normalized:
            raise ValueError("Numer telefonu rodziny jest wymagany i musi miec prawidlowy format.")
        return normalized

    def _normalize_optional_amount(self, value: Any) -> float | None:
        normalized = self._normalize_optional_text(value)
        if normalized is None:
            return None
        normalized = normalized.replace(" ", "").replace(",", ".")
        try:
            parsed = float(normalized)
        except ValueError as error:
            raise ValueError("Kwota modelu rozliczen musi byc liczba.") from error
        if parsed < 0:
            raise ValueError("Kwota modelu rozliczen nie moze byc ujemna.")
        return round(parsed, 2)

    def _normalize_amount_with_default(self, value: Any, *, default: float) -> float:
        parsed = self._normalize_optional_amount(value)
        return default if parsed is None else parsed

    def _normalize_non_negative_int(self, value: Any, *, field_label: str, default: int) -> int:
        if value in {None, ""}:
            return default
        try:
            parsed = int(value)
        except (TypeError, ValueError) as error:
            raise ValueError(f"{field_label} musi byc liczba calkowita.") from error
        if parsed < 0:
            raise ValueError(f"{field_label} nie moze byc ujemna.")
        return parsed

    def _normalize_positive_int(self, value: Any, *, field_label: str, default: int) -> int:
        parsed = self._normalize_non_negative_int(value, field_label=field_label, default=default)
        if parsed <= 0:
            raise ValueError(f"{field_label} musi byc wieksza od zera.")
        return parsed

    def _normalize_boolean_flag(self, value: Any) -> int:
        return 1 if value in {True, 1, "1", "true", "tak", "on"} else 0

    def _resolve_charge_unit_rate(self, model: dict[str, Any]) -> float:
        settlement_mode = str(model.get("settlement_mode") or "").strip().lower()
        monthly_rate = self._normalize_optional_amount(model.get("monthly_rate_amount"))
        semester_rate = self._normalize_optional_amount(model.get("semester_rate_amount"))

        if settlement_mode == "monthly":
            if monthly_rate is None:
                raise ValueError("Model miesieczny nie ma stawki do generowania naleznosci.")
            return monthly_rate
        if settlement_mode == "semester":
            if semester_rate is None:
                raise ValueError("Model semestralny nie ma stawki do generowania naleznosci.")
            return semester_rate

        if monthly_rate is not None:
            return monthly_rate
        if semester_rate is not None:
            return semester_rate
        raise ValueError("Model wlasny nie ma zadnej stawki do generowania naleznosci.")

    def _round_amount(self, value: float) -> float:
        return round(float(value or 0), 2)

    def _attach_latest_family_payments(
        self,
        payers: list[dict[str, Any]],
        *,
        organization_id: int | None,
    ) -> list[dict[str, Any]]:
        if not payers:
            return []

        transactions = self.billing_repository.list_recent_incoming_transactions(
            organization_id=organization_id,
            limit=5000,
        )
        latest_by_phone: dict[tuple[int | None, str], dict[str, Any]] = {}
        for transaction in transactions:
            searchable_text = " ".join(
                [
                    str(transaction.get("title") or ""),
                    str(transaction.get("reference") or ""),
                ]
            )
            for phone in extract_phone_identifiers(searchable_text):
                key = (transaction.get("organization_id"), phone)
                if key in latest_by_phone:
                    continue
                latest_by_phone[key] = {
                    "latest_payment_date": transaction.get("booking_date"),
                    "latest_payment_amount": transaction.get("amount"),
                    "latest_payment_currency": transaction.get("currency"),
                    "latest_payment_title": transaction.get("title"),
                }

        for payer in payers:
            payer["payer_label"] = self._payer_label(payer)
            summary = latest_by_phone.get(
                (
                    payer.get("organization_id"),
                    str(payer.get("payment_identifier") or ""),
                )
            )
            if summary:
                payer.update(summary)
            else:
                payer["latest_payment_date"] = None
                payer["latest_payment_amount"] = None
                payer["latest_payment_currency"] = None
                payer["latest_payment_title"] = None
        return payers

    def _payer_label(self, payer: dict[str, Any]) -> str:
        display_name = str(payer.get("display_name") or "").strip()
        if display_name:
            return display_name
        return f"Rodzina {payer.get('contact_phone')}"

    def _normalize_date(self, value: Any, *, field_label: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError(f"Pole {field_label} jest wymagane.")

        for input_format in ("%Y-%m-%d", "%Y/%m/%d", "%d.%m.%Y", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(normalized, input_format).strftime("%Y-%m-%d")
            except ValueError:
                continue
        raise ValueError(f"Nieprawidlowy format daty dla pola {field_label}.")

    def _normalize_amount(self, value: Any, *, field_label: str) -> float:
        normalized = str(value or "").strip().replace("\u00a0", "").replace(" ", "").replace(",", ".")
        normalized = re.sub(r"[^0-9.\-+]", "", normalized)
        if not normalized:
            raise ValueError(f"Pole {field_label} jest wymagane.")
        if normalized.count(".") > 1:
            raise ValueError(f"Nieprawidlowy format liczby dla pola {field_label}.")
        try:
            return float(normalized)
        except ValueError as error:
            raise ValueError(f"Nieprawidlowy format liczby dla pola {field_label}.") from error

    def _build_transaction_hash(self, bank_account_id: int, row: dict[str, Any]) -> str:
        raw = "|".join(
            [
                str(bank_account_id),
                str(row.get("booking_date") or ""),
                str(row.get("value_date") or ""),
                f"{float(row.get('amount') or 0.0):.2f}",
                str(row.get("currency") or ""),
                str(row.get("counterparty_name") or ""),
                str(row.get("counterparty_account") or ""),
                str(row.get("title") or ""),
                str(row.get("reference") or ""),
            ]
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
