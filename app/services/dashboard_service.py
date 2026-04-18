from __future__ import annotations

import json
from typing import Any

from app.domain.constants import INVOICE_SLA_THRESHOLDS_DAYS, INVOICE_WORKFLOW_SLA_THRESHOLDS_DAYS
from app.repositories.contractor_repository import ContractorRepository
from app.repositories.event_repository import EventRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.intake_repository import IntakeRepository
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.task_repository import TaskRepository
from app.utils import age_in_days


class DashboardService:
    def __init__(
        self,
        invoice_repository: InvoiceRepository,
        contractor_repository: ContractorRepository,
        event_repository: EventRepository,
        task_repository: TaskRepository,
        organization_repository: OrganizationRepository,
        knowledge_repository: KnowledgeRepository | None = None,
        knowledge_service: Any | None = None,
        intake_repository: IntakeRepository | None = None,
    ) -> None:
        self.invoice_repository = invoice_repository
        self.contractor_repository = contractor_repository
        self.event_repository = event_repository
        self.task_repository = task_repository
        self.organization_repository = organization_repository
        self.knowledge_repository = knowledge_repository
        self.knowledge_service = knowledge_service
        self.intake_repository = intake_repository

    def get_snapshot(
        self,
        organization_id: int | None = None,
        viewer_user_id: int | None = None,
    ) -> dict[str, Any]:
        invoices = self.invoice_repository.list_invoices({}, organization_id=organization_id)
        contractors = self.contractor_repository.list_contractors(organization_id=organization_id)
        events = self.event_repository.list_logs(limit=40, organization_id=organization_id)
        events = self._filter_events_for_viewer(events, viewer_user_id)[:12]
        reminders = self.task_repository.list_active_reminders(
            organization_id=organization_id,
            viewer_user_id=viewer_user_id,
            limit=6,
        )
        return {
            "cards": {
                "nowe_faktury": sum(1 for item in invoices if item["status"] == "nowa"),
                "do_weryfikacji": sum(1 for item in invoices if item["status"] == "weryfikacja"),
                "podejrzenia_duplikatow": sum(1 for item in invoices if item["duplicate_type"] == "podejrzenie"),
                "pewne_duplikaty": sum(1 for item in invoices if item["duplicate_type"] == "pewny"),
                "nowi_kontrahenci": sum(1 for item in contractors if item["is_new"]),
                "aktywne_przypomnienia": self.task_repository.count_due_reminders(
                    organization_id=organization_id,
                    viewer_user_id=viewer_user_id,
                ),
            },
            "recent_events": events,
            "active_reminders": reminders,
            "knowledge_queue": self._build_knowledge_queue(
                organization_id=organization_id,
                viewer_user_id=viewer_user_id,
            ),
            "operational_alerts": self._build_operational_alerts(
                invoices=invoices,
                reminders=reminders,
                organization_id=organization_id,
                viewer_user_id=viewer_user_id,
            ),
        }

    def _build_operational_alerts(
        self,
        *,
        invoices: list[dict[str, Any]],
        reminders: list[dict[str, Any]],
        organization_id: int | None,
        viewer_user_id: int | None,
    ) -> list[dict[str, Any]]:
        organizations = self.organization_repository.list_organizations(only_active=True)
        if organization_id is not None:
            organizations = [
                item for item in organizations if int(item.get("organization_id") or 0) == int(organization_id)
            ]

        alerts: list[dict[str, Any]] = []

        verification_items = [item for item in invoices if item["status"] == "weryfikacja"]
        verification_count = len(verification_items)
        verification_stale = self._count_sla_breaches(
            verification_items,
            threshold_days=int(INVOICE_SLA_THRESHOLDS_DAYS["verification"]),
        )
        if verification_count:
            alerts.append(
                {
                    "severity": "danger" if verification_stale else "warning",
                    "category": "invoices",
                    "title": "Faktury czekaja na weryfikacje",
                    "description": self._build_invoice_queue_alert_description(
                        verification_count,
                        verification_stale,
                        threshold_days=int(INVOICE_SLA_THRESHOLDS_DAYS["verification"]),
                        queue_label="faktur wymaga recznego sprawdzenia",
                    ),
                    "organization_id": organization_id,
                    "organization_name": None,
                    "action_view": "invoices",
                    "action_label": "Otworz workspace faktur",
                    "action_bucket": "verification",
                }
            )

        duplicate_items = [item for item in invoices if item["duplicate_type"] in {"podejrzenie", "pewny"}]
        duplicate_count = len(duplicate_items)
        duplicate_stale = self._count_sla_breaches(
            duplicate_items,
            threshold_days=int(INVOICE_SLA_THRESHOLDS_DAYS["duplicates"]),
        )
        if duplicate_count:
            alerts.append(
                {
                    "severity": "danger" if duplicate_stale else "warning",
                    "category": "invoices",
                    "title": "Duplikaty wymagaja decyzji",
                    "description": self._build_invoice_queue_alert_description(
                        duplicate_count,
                        duplicate_stale,
                        threshold_days=int(INVOICE_SLA_THRESHOLDS_DAYS["duplicates"]),
                        queue_label="faktur wymaga decyzji o duplikacie",
                    ),
                    "organization_id": organization_id,
                    "organization_name": None,
                    "action_view": "invoices",
                    "action_label": "Sprawdz duplikaty",
                    "action_bucket": "duplicates",
                }
            )

        ocr_attention_items = [
            item
            for item in verification_items
            if str(item.get("source") or "").upper() in {"EMAIL", "TELEGRAM"}
            and "ocr" in str(item.get("flag_reason") or "").lower()
        ]
        ocr_attention_count = len(ocr_attention_items)
        ocr_attention_stale = self._count_sla_breaches(
            ocr_attention_items,
            threshold_days=int(INVOICE_SLA_THRESHOLDS_DAYS["ocr_attention"]),
        )
        if ocr_attention_count:
            alerts.append(
                {
                    "severity": "danger" if ocr_attention_stale else "warning",
                    "category": "invoices",
                    "title": "OCR wymaga pilnej uwagi",
                    "description": self._build_invoice_queue_alert_description(
                        ocr_attention_count,
                        ocr_attention_stale,
                        threshold_days=int(INVOICE_SLA_THRESHOLDS_DAYS["ocr_attention"]),
                        queue_label="dokumentow ma niepelny odczyt OCR",
                    ),
                    "organization_id": organization_id,
                    "organization_name": None,
                    "action_view": "invoices",
                    "action_label": "Otworz OCR do weryfikacji",
                    "action_bucket": "ocr_attention",
                }
            )

        ksef_pending_items = self.invoice_repository.list_pending_ksef_correction_invoices(
            organization_id=organization_id,
            limit=100,
        )
        ksef_pending_count = len(ksef_pending_items)
        ksef_pending_stale = self._count_sla_breaches(
            ksef_pending_items,
            threshold_days=int(INVOICE_SLA_THRESHOLDS_DAYS["ksef_corrections"]),
            timestamp_field="latest_request_at",
        )
        if ksef_pending_count:
            alerts.append(
                {
                    "severity": "danger" if ksef_pending_stale else "warning",
                    "category": "invoices",
                    "title": "Korekty KSeF czekaja na decyzje",
                    "description": self._build_invoice_queue_alert_description(
                        ksef_pending_count,
                        ksef_pending_stale,
                        threshold_days=int(INVOICE_SLA_THRESHOLDS_DAYS["ksef_corrections"]),
                        queue_label="faktur czeka na zatwierdzenie korekty KSeF",
                    ),
                    "organization_id": organization_id,
                    "organization_name": None,
                    "action_view": "invoices",
                    "action_label": "Sprawdz korekty KSeF",
                    "action_bucket": "ksef_corrections",
                }
            )

        ready_for_handoff_items = [
            item
            for item in invoices
            if str(item.get("workflow_state") or "").strip().lower() == "gotowa_do_przekazania"
        ]
        ready_for_handoff_count = len(ready_for_handoff_items)
        ready_for_handoff_stale = self._count_sla_breaches(
            ready_for_handoff_items,
            threshold_days=int(INVOICE_WORKFLOW_SLA_THRESHOLDS_DAYS["ready_for_handoff"]),
            timestamp_field="ready_for_handoff_at",
        )
        if ready_for_handoff_count:
            alerts.append(
                {
                    "severity": "danger" if ready_for_handoff_stale else "warning",
                    "category": "invoices",
                    "title": "Faktury czekaja na przekazanie",
                    "description": self._build_invoice_queue_alert_description(
                        ready_for_handoff_count,
                        ready_for_handoff_stale,
                        threshold_days=int(INVOICE_WORKFLOW_SLA_THRESHOLDS_DAYS["ready_for_handoff"]),
                        queue_label="faktur jest gotowych do przekazania dalej",
                    ),
                    "organization_id": organization_id,
                    "organization_name": None,
                    "action_view": "invoices",
                    "action_label": "Sprawdz przekazanie",
                    "action_bucket": "handoff_ready",
                }
            )

        if self.intake_repository:
            exception_items = [
                item
                for item in self.intake_repository.list_items(
                    organization_id=organization_id,
                    source_kind="invoice_exception",
                    limit=200,
                )
                if str(item.get("status") or "").strip().lower() not in {"zakonczone", "zarchiwizowane"}
            ]
            if exception_items:
                alerts.append(
                    {
                        "severity": "warning",
                        "category": "invoices",
                        "title": "Wyjatki w obiegu faktur",
                        "description": f"W centrum wyjatkow czeka {len(exception_items)} otwartych spraw wymagajacych uwagi.",
                        "organization_id": organization_id,
                        "organization_name": None,
                        "action_view": "invoices",
                        "action_label": "Otworz wyjatki",
                        "action_bucket": "exceptions",
                    }
                )

        if reminders:
            alerts.append(
                {
                    "severity": "info",
                    "category": "tasks",
                    "title": "Aktywne przypomnienia w zespolu",
                    "description": f"Do wyswietlenia jest {len(reminders)} aktywnych przypomnien.",
                    "organization_id": organization_id,
                    "organization_name": None,
                    "action_view": "tasks",
                    "action_label": "Otworz zadania",
                }
            )

        if self.knowledge_repository and organization_id is not None:
            knowledge_documents = self.knowledge_repository.list_documents(int(organization_id), include_deleted=False)
            review_documents = [
                item
                for item in knowledge_documents
                if str(item.get("business_status") or "").strip().lower() == "do_sprawdzenia"
                and str(item.get("lifecycle_status") or "active") == "active"
            ]
            approval_documents = [
                item
                for item in knowledge_documents
                if str(item.get("business_status") or "").strip().lower() == "do_akceptacji"
                and str(item.get("lifecycle_status") or "active") == "active"
            ]
            if review_documents:
                alerts.append(
                    {
                        "severity": "warning",
                        "category": "knowledge",
                        "title": "Dokumenty czekaja na sprawdzenie",
                        "description": f"{len(review_documents)} dokumentow firmowych czeka na review przed akceptacja.",
                        "organization_id": organization_id,
                        "organization_name": None,
                        "action_view": "knowledge",
                        "action_label": "Otworz dokumenty",
                        "action_bucket": "knowledge_review",
                    }
                )
            if approval_documents:
                alerts.append(
                    {
                        "severity": "warning",
                        "category": "knowledge",
                        "title": "Dokumenty czekaja na akceptacje",
                        "description": f"{len(approval_documents)} dokumentow firmowych czeka na decyzje osoby akceptujacej.",
                        "organization_id": organization_id,
                        "organization_name": None,
                        "action_view": "knowledge",
                        "action_label": "Otworz decyzje",
                        "action_bucket": "knowledge_approval",
                    }
                )
            if viewer_user_id is not None:
                my_drafts = [
                    item
                    for item in knowledge_documents
                    if str(item.get("business_status") or "").strip().lower() == "roboczy"
                    and int(item.get("owner_user_id") or 0) == int(viewer_user_id)
                    and str(item.get("lifecycle_status") or "active") == "active"
                ]
                my_reviews = [
                    item
                    for item in knowledge_documents
                    if str(item.get("business_status") or "").strip().lower() == "do_sprawdzenia"
                    and int(item.get("reviewer_user_id") or 0) == int(viewer_user_id)
                    and str(item.get("lifecycle_status") or "active") == "active"
                ]
                my_approvals = [
                    item
                    for item in knowledge_documents
                    if str(item.get("business_status") or "").strip().lower() == "do_akceptacji"
                    and int(item.get("approver_user_id") or 0) == int(viewer_user_id)
                    and str(item.get("lifecycle_status") or "active") == "active"
                ]
                my_total = len(my_drafts) + len(my_reviews) + len(my_approvals)
                if my_total:
                    alerts.append(
                        {
                            "severity": "info" if not (my_reviews or my_approvals) else "warning",
                            "category": "knowledge",
                            "title": "Na Ciebie czekaja dokumenty firmowe",
                            "description": (
                                f"Robocze: {len(my_drafts)}, do sprawdzenia: {len(my_reviews)}, "
                                f"do akceptacji: {len(my_approvals)}."
                            ),
                            "organization_id": organization_id,
                            "organization_name": None,
                            "action_view": "knowledge",
                            "action_label": "Otworz moja kolejke",
                            "action_bucket": "knowledge_my_queue",
                        }
                    )

        for organization in organizations:
            organization_name = organization.get("name")
            org_id = int(organization["organization_id"])
            email_status = str(organization.get("email_last_connection_status") or "").strip().lower()
            ksef_status = str(organization.get("ksef_last_connection_status") or "").strip().lower()
            if int(organization.get("email_integration_enabled") or 0) and email_status and "dziala" not in email_status:
                alerts.append(
                    {
                        "severity": "danger",
                        "category": "integrations",
                        "title": "Problem z integracja e-mail",
                        "description": f"Organizacja {organization_name} ma blad polaczenia e-mail.",
                        "organization_id": org_id,
                        "organization_name": organization_name,
                        "action_view": "email-center",
                        "action_label": "Otworz integracje",
                    }
                )
            if int(organization.get("ksef_integration_enabled") or 0) and ksef_status and "gotowe" not in ksef_status and "dziala" not in ksef_status:
                alerts.append(
                    {
                        "severity": "warning",
                        "category": "integrations",
                        "title": "Problem z integracja KSeF",
                        "description": f"Organizacja {organization_name} wymaga sprawdzenia ustawien KSeF.",
                        "organization_id": org_id,
                        "organization_name": organization_name,
                        "action_view": "email-center",
                        "action_label": "Sprawdz KSeF",
                    }
                )

        return alerts[:8]

    def _build_knowledge_queue(
        self,
        *,
        organization_id: int | None,
        viewer_user_id: int | None,
    ) -> list[dict[str, Any]]:
        if not self.knowledge_service or organization_id is None:
            return []
        payload = self.knowledge_service.list_documents(
            organization_id=int(organization_id),
            viewer_user_id=viewer_user_id,
        )
        documents = list(payload.get("documents") or [])
        queue: list[dict[str, Any]] = []
        for item in documents:
            if str(item.get("lifecycle_status") or "active") != "active":
                continue
            decision_actions = list(item.get("decision_actions") or [])
            if not decision_actions:
                continue
            business_status = str(item.get("business_status") or "roboczy")
            queue.append(
                {
                    "knowledge_document_id": int(item.get("knowledge_document_id") or 0),
                    "title": item.get("title") or "Dokument firmowy",
                    "library_path_label": item.get("library_path_label") or "Bez folderu",
                    "business_status": business_status,
                    "business_status_label": item.get("business_status_label") or business_status,
                    "workflow_status": item.get("workflow_status"),
                    "workflow_status_label": item.get("workflow_status_label"),
                    "current_version_number": int(item.get("current_version_number") or 0),
                    "official_version_number": int(item.get("official_version_number") or 0),
                    "reviewer_user_id": item.get("reviewer_user_id"),
                    "reviewer_user_label": item.get("reviewer_user_label"),
                    "approver_user_id": item.get("approver_user_id"),
                    "approver_user_label": item.get("approver_user_label"),
                    "owner_user_id": item.get("owner_user_id"),
                    "owner_user_label": item.get("owner_user_label"),
                    "decision_actions": decision_actions,
                    "updated_at": item.get("updated_at"),
                }
            )
        priority_order = {
            "do_akceptacji": 0,
            "do_sprawdzenia": 1,
            "roboczy": 2,
            "obowiazujacy": 3,
            "archiwalny": 4,
        }
        queue.sort(
            key=lambda item: (
                priority_order.get(str(item.get("business_status") or "roboczy"), 9),
                str(item.get("updated_at") or ""),
                -int(item.get("knowledge_document_id") or 0),
            )
        )
        return queue[:6]

    def _count_sla_breaches(
        self,
        items: list[dict[str, Any]],
        *,
        threshold_days: int,
        timestamp_field: str = "updated_at",
    ) -> int:
        return sum(
            1
            for item in items
            if (age_in_days(item.get(timestamp_field) or item.get("incoming_date")) or 0) >= threshold_days
        )

    def _build_invoice_queue_alert_description(
        self,
        total_count: int,
        stale_count: int,
        *,
        threshold_days: int,
        queue_label: str,
    ) -> str:
        if stale_count:
            return (
                f"{stale_count} z {total_count} {queue_label} dluzej niz {threshold_days} "
                f"{'dzien' if threshold_days == 1 else 'dni'}."
            )
        return f"{total_count} {queue_label} i powinno zostac przejrzane na biezaco."

    def _filter_events_for_viewer(
        self,
        events: list[dict[str, Any]],
        viewer_user_id: int | None,
    ) -> list[dict[str, Any]]:
        if viewer_user_id is None:
            return events

        visible_events: list[dict[str, Any]] = []
        for event in events:
            task_id = self._extract_task_id(event)
            event_type = str(event.get("event_type") or "")

            if task_id is None:
                if event_type.startswith("task_"):
                    continue
                visible_events.append(event)
                continue

            if self.task_repository.can_user_view_task(task_id, viewer_user_id):
                visible_events.append(event)
        return visible_events

    def _extract_task_id(self, event: dict[str, Any]) -> int | None:
        details = event.get("details")
        if not details:
            return None
        if isinstance(details, dict):
            raw_task_id = details.get("task_id")
        else:
            try:
                parsed = json.loads(details)
            except (TypeError, json.JSONDecodeError):
                return None
            raw_task_id = parsed.get("task_id")
        if raw_task_id in (None, ""):
            return None
        try:
            return int(raw_task_id)
        except (TypeError, ValueError):
            return None
