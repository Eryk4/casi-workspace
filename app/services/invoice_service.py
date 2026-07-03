from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import re
import secrets
import threading
from datetime import datetime, timedelta, timezone
from typing import Any

from app.config import (
    EMAIL_AUTOCHECK_ENABLED,
    EMAIL_AUTOCHECK_SECONDS,
    KSEF_FETCH_LIMIT,
    SLACK_BOT_TOKEN,
    SLACK_SIGNING_SECRET,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_WEBHOOK_SECRET,
)
from app.domain.constants import (
    INVOICE_SLA_THRESHOLDS_DAYS,
    INVOICE_VERIFICATION_BUCKET_ORDER,
    INVOICE_WORKFLOW_STATES,
    ORGANIZATION_ADMIN_ROLE,
    INVOICE_DECISION_ROLES,
    WRITE_ROLES,
)
from app.integrations.email_ingestion import EmailIngestionAdapter, EmailIngestionError
from app.integrations.email_google_oauth import EmailGoogleOAuthAdapter, EmailGoogleOAuthError
from app.integrations.ksef_client import KSeFClient
from app.integrations.ocr_engine import OCREngine
from app.integrations.slack_bot import SlackBotAdapter, SlackBotError
from app.integrations.telegram_bot import TelegramBotAdapter, TelegramBotError
from app.repositories.contractor_repository import ContractorRepository
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.email_import_repository import EmailImportRepository
from app.repositories.email_oauth_repository import EmailOAuthRepository
from app.repositories.event_repository import EventRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.invoice_handoff_repository import InvoiceHandoffRepository
from app.repositories.invoice_ksef_override_repository import InvoiceKSeFOverrideRepository
from app.repositories.intake_repository import IntakeRepository
from app.repositories.ksef_import_repository import KSeFImportRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import PermissionError
from app.services.duplicate_detector import DuplicateDetector
from app.services.notification_service import NotificationService
from app.services.system_settings_service import SystemSettingsService
from app.services.storage_service import StorageService
from app.utils import age_in_days, now_iso

SOURCE_PRIORITIES = {
    "TELEGRAM": 1,
    "SLACK": 1,
    "EMAIL": 2,
    "KSEF": 3,
}

KSEF_AUTHORITATIVE_FIELDS = (
    "invoice_number",
    "ksef_number",
    "issuer_nip",
    "issuer_name",
    "issue_date",
    "sale_date",
    "gross_amount",
    "currency",
)

KSEF_CORRECTION_REQUEST_KIND = "ksef_field_correction"
INVOICE_DOCUMENT_INTAKE_KIND = "invoice_document"
INVOICE_EXCEPTION_INTAKE_KIND = "invoice_exception"
INVOICE_WORKFLOW_UNDO_EVENT_TYPES = (
    "invoice_ready_for_handoff",
    "invoice_handed_off",
    "invoice_closed",
    "invoice_reopened",
)


class InvoiceService:
    def __init__(
        self,
        invoice_repository: InvoiceRepository,
        contractor_repository: ContractorRepository,
        email_import_repository: EmailImportRepository,
        ksef_import_repository: KSeFImportRepository,
        event_repository: EventRepository,
        user_repository: UserRepository,
        organization_repository: OrganizationRepository,
        task_repository: TaskRepository,
        duplicate_detector: DuplicateDetector,
        notification_service: NotificationService,
        storage_service: StorageService,
        email_oauth_repository: EmailOAuthRepository | None = None,
        email_google_oauth_adapter: EmailGoogleOAuthAdapter | None = None,
        approval_repository: ApprovalRepository | None = None,
        invoice_ksef_override_repository: InvoiceKSeFOverrideRepository | None = None,
        intake_repository: IntakeRepository | None = None,
        invoice_handoff_repository: InvoiceHandoffRepository | None = None,
        system_settings_service: SystemSettingsService | None = None,
    ) -> None:
        self.invoice_repository = invoice_repository
        self.contractor_repository = contractor_repository
        self.email_import_repository = email_import_repository
        self.ksef_import_repository = ksef_import_repository
        self.event_repository = event_repository
        self.user_repository = user_repository
        self.organization_repository = organization_repository
        self.task_repository = task_repository
        self.duplicate_detector = duplicate_detector
        self.notification_service = notification_service
        self.storage_service = storage_service
        self.email_oauth_repository = email_oauth_repository or EmailOAuthRepository()
        self.email_google_oauth_adapter = email_google_oauth_adapter or EmailGoogleOAuthAdapter()
        self.approval_repository = approval_repository
        self.invoice_ksef_override_repository = invoice_ksef_override_repository or InvoiceKSeFOverrideRepository()
        self.intake_repository = intake_repository
        self.invoice_handoff_repository = invoice_handoff_repository
        self.system_settings_service = system_settings_service
        self.ksef_client = KSeFClient()
        self.ocr_engine = OCREngine()
        self.email_adapter = EmailIngestionAdapter(
            self.ocr_engine,
            oauth_repository=self.email_oauth_repository,
            google_oauth_adapter=self.email_google_oauth_adapter,
        )
        self.telegram_adapter = TelegramBotAdapter(
            self.ocr_engine,
            bot_token=TELEGRAM_BOT_TOKEN,
            webhook_secret=TELEGRAM_WEBHOOK_SECRET,
        )
        self.slack_adapter = SlackBotAdapter(
            self.ocr_engine,
            bot_token=SLACK_BOT_TOKEN,
            signing_secret=SLACK_SIGNING_SECRET,
        )
        self.refresh_communication_adapters()
        self._email_scheduler_lock = threading.Lock()
        self._email_scheduler_state_lock = threading.Lock()
        self._email_scheduler_state: dict[str, Any] = {
            "running": False,
            "last_started_at": None,
            "last_finished_at": None,
            "last_status": "disabled" if not EMAIL_AUTOCHECK_ENABLED else "idle",
            "last_message": (
                "Automatyczne sprawdzanie e-mail jest wylaczone w konfiguracji."
                if not EMAIL_AUTOCHECK_ENABLED
                else "Automatyczne sprawdzanie e-mail czeka na pierwszy cykl."
            ),
            "last_result": None,
        }

    def telegram_integration_info(self) -> dict[str, Any]:
        self.refresh_communication_adapters()
        return self.telegram_adapter.integration_status()

    def slack_integration_info(self) -> dict[str, Any]:
        self.refresh_communication_adapters()
        return self.slack_adapter.integration_status()

    def refresh_communication_adapters(self) -> None:
        telegram_bot_token = TELEGRAM_BOT_TOKEN
        telegram_webhook_secret = TELEGRAM_WEBHOOK_SECRET
        slack_bot_token = SLACK_BOT_TOKEN
        slack_signing_secret = SLACK_SIGNING_SECRET

        if self.system_settings_service is not None:
            telegram_credentials = self.system_settings_service.resolve_telegram_credentials()
            slack_credentials = self.system_settings_service.resolve_slack_credentials()
            telegram_bot_token = str(telegram_credentials.get("bot_token") or "").strip()
            telegram_webhook_secret = str(telegram_credentials.get("webhook_secret") or "").strip()
            slack_bot_token = str(slack_credentials.get("bot_token") or "").strip()
            slack_signing_secret = str(slack_credentials.get("signing_secret") or "").strip()

        self.telegram_adapter.configure(
            bot_token=telegram_bot_token,
            webhook_secret=telegram_webhook_secret,
        )
        self.slack_adapter.configure(
            bot_token=slack_bot_token,
            signing_secret=slack_signing_secret,
        )

    def email_integration_info(self) -> dict[str, Any]:
        info = self.email_adapter.integration_status()
        google_connection = self.email_oauth_repository.get_google_connection()
        info["google_oauth_enabled"] = bool(self.email_google_oauth_adapter.is_enabled())
        info["google_connection"] = self._sanitize_email_google_connection(google_connection)
        return info

    def ksef_integration_info(self) -> dict[str, Any]:
        info = self.ksef_client.integration_status()
        info["fetch_limit"] = KSEF_FETCH_LIMIT
        return info

    def begin_email_google_connection(
        self,
        *,
        actor_user: dict[str, Any],
        public_base_url: str,
        login_hint: str | None = None,
    ) -> dict[str, Any]:
        if not self.email_google_oauth_adapter.is_enabled(public_base_url):
            raise ValueError(
                "Integracja Google Workspace dla e-mail nie jest jeszcze gotowa. "
                "Uzupelnij dane OAuth i publiczny adres aplikacji."
            )
        state_token = secrets.token_urlsafe(32)
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=15)).replace(microsecond=0).isoformat()
        self.email_oauth_repository.clear_expired_google_oauth_states(now_iso())
        self.email_oauth_repository.create_google_oauth_state(
            state_token=state_token,
            created_by_user_id=actor_user.get("user_id"),
            login_hint=login_hint,
            expires_at=expires_at,
        )
        authorization_url = self.email_google_oauth_adapter.build_authorization_url(
            state_token,
            login_hint=login_hint,
            public_base_url=public_base_url,
        )
        return {
            "authorization_url": authorization_url,
            "callback_url": self.email_google_oauth_adapter.callback_url(public_base_url),
            "expires_at": expires_at,
        }

    def finalize_email_google_connection(
        self,
        *,
        state_token: str,
        code: str,
        error_code: str,
        public_base_url: str,
    ) -> dict[str, Any]:
        if error_code:
            raise ValueError("Google Workspace przerwal autoryzacje skrzynki e-mail.")
        if not state_token or not code:
            raise ValueError("Brakuje danych wymaganych do dokonczenia polaczenia Google Workspace.")

        self.email_oauth_repository.clear_expired_google_oauth_states(now_iso())
        state = self.email_oauth_repository.consume_google_oauth_state(state_token)
        if not state:
            raise ValueError("Sesja autoryzacji e-mail wygasla albo jest nieprawidlowa. Sprobuj ponownie.")
        if self._email_oauth_state_expired(state.get("expires_at")):
            raise ValueError("Sesja autoryzacji e-mail wygasla. Sprobuj ponownie.")

        try:
            tokens = self.email_google_oauth_adapter.exchange_code_for_tokens(code, public_base_url=public_base_url)
            user_info = self.email_google_oauth_adapter.fetch_user_info(tokens["access_token"])
        except EmailGoogleOAuthError as error:
            raise ValueError(str(error)) from error

        google_email = str(user_info.get("email") or "").strip()
        if not google_email:
            raise ValueError("Google Workspace nie zwrocil adresu skrzynki e-mail.")

        payload = {
            "google_email": google_email,
            "access_token": tokens["access_token"],
            "refresh_token": tokens.get("refresh_token"),
            "token_expires_at": tokens["token_expires_at"],
            "scope": tokens.get("scope"),
        }
        self.email_oauth_repository.upsert_google_connection(
            payload,
            created_by_user_id=state.get("created_by_user_id"),
        )
        actor = self._actor_from_user_id(state.get("created_by_user_id")) or "system"
        self.event_repository.log(
            event_type="email_google_connected",
            invoice_id=None,
            organization_id=None,
            source="EMAIL",
            status_before=None,
            status_after="connected",
            decision_reason=f"Polaczono centralna skrzynke Google Workspace: {google_email}.",
            actor=actor,
            details={
                "provider": "google_workspace",
                "google_email": google_email,
                "scope": tokens.get("scope"),
            },
        )
        return {
            "status": "connected",
            "google_email": google_email,
            "connection": self._sanitize_email_google_connection(self.email_oauth_repository.get_google_connection()),
        }

    def disconnect_email_google_connection(self, *, actor_user: dict[str, Any]) -> dict[str, Any]:
        existing = self.email_oauth_repository.get_google_connection()
        self.email_oauth_repository.delete_google_connection()
        self.event_repository.log(
            event_type="email_google_disconnected",
            invoice_id=None,
            organization_id=None,
            source="EMAIL",
            status_before="connected" if existing else None,
            status_after="disconnected",
            decision_reason="Rozlaczono centralna skrzynke Google Workspace dla e-mail.",
            actor=self._actor_label_from_user(actor_user),
            details={
                "provider": "google_workspace",
                "google_email": (existing or {}).get("google_email"),
            },
        )
        return {
            "status": "disconnected",
            "google_email": (existing or {}).get("google_email"),
        }

    def integration_center_snapshot(
        self,
        *,
        viewer_user: dict[str, Any],
        requested_organization_id: int | None = None,
        limit: int = 25,
    ) -> dict[str, Any]:
        if viewer_user.get("is_global_admin"):
            effective_organization_id = requested_organization_id
        else:
            effective_organization_id = int(viewer_user.get("organization_id") or 0) or None

        email_runs = self.email_import_repository.list_runs(
            organization_id=effective_organization_id,
            limit=limit,
            preview_items_limit=4,
        )
        ksef_runs = self.ksef_import_repository.list_runs(
            organization_id=effective_organization_id,
            limit=limit,
            preview_items_limit=4,
        )
        email_summary = {
            "runs_total": len(email_runs),
            "imports_completed": sum(1 for run in email_runs if str(run.get("status") or "") == "completed"),
            "imports_with_issues": sum(1 for run in email_runs if str(run.get("status") or "") == "completed_with_issues"),
            "imports_failed": sum(1 for run in email_runs if str(run.get("status") or "") == "failed"),
            "imports_without_new_documents": sum(1 for run in email_runs if str(run.get("status") or "") == "no_new_documents"),
            "imported_invoice_count": sum(int(run.get("imported_invoice_count") or 0) for run in email_runs),
            "checked_message_count": sum(int(run.get("checked_message_count") or 0) for run in email_runs),
        }
        ksef_summary = {
            "runs_total": len(ksef_runs),
            "imports_completed": sum(1 for run in ksef_runs if str(run.get("status") or "") == "completed"),
            "imports_with_issues": sum(1 for run in ksef_runs if str(run.get("status") or "") == "completed_with_issues"),
            "imports_failed": sum(1 for run in ksef_runs if str(run.get("status") or "") == "failed"),
            "imports_without_new_documents": sum(1 for run in ksef_runs if str(run.get("status") or "") == "no_new_documents"),
            "imported_invoice_count": sum(int(run.get("imported_invoice_count") or 0) for run in ksef_runs),
            "checked_document_count": sum(int(run.get("checked_document_count") or 0) for run in ksef_runs),
        }
        ready_organizations = self.organization_repository.list_email_ready_organizations(only_active=True)
        ready_ksef_organizations = self.organization_repository.list_ksef_ready_organizations(only_active=True)
        if effective_organization_id is not None:
            ready_organizations = [
                item for item in ready_organizations if int(item.get("organization_id") or 0) == int(effective_organization_id)
            ]
            ready_ksef_organizations = [
                item for item in ready_ksef_organizations if int(item.get("organization_id") or 0) == int(effective_organization_id)
            ]
        return {
            "scope": {
                "organization_id": effective_organization_id,
                "organization_name": self._organization_name(effective_organization_id),
            },
            "email": {
                "integration": self.email_integration_info(),
                "summary": email_summary,
                "ready_organization_count": len(ready_organizations),
                "runs": email_runs,
            },
            "ksef": {
                "integration": self.ksef_integration_info(),
                "summary": ksef_summary,
                "ready_organization_count": len(ready_ksef_organizations),
                "runs": ksef_runs,
            },
            "telegram": self.telegram_integration_info(),
            "slack": self.slack_integration_info(),
            "ocr": self.ocr_integration_info(),
            "storage": self.storage_integration_info(),
            "scheduler": self.email_scheduler_status(),
        }

    def email_center_snapshot(
        self,
        *,
        viewer_user: dict[str, Any],
        requested_organization_id: int | None = None,
        limit: int = 25,
    ) -> dict[str, Any]:
        snapshot = self.integration_center_snapshot(
            viewer_user=viewer_user,
            requested_organization_id=requested_organization_id,
            limit=limit,
        )
        return {
            "scope": snapshot["scope"],
            "integration": snapshot["email"]["integration"],
            "scheduler": snapshot["scheduler"],
            "ready_organization_count": snapshot["email"]["ready_organization_count"],
            "summary": snapshot["email"]["summary"],
            "runs": snapshot["email"]["runs"],
            "ksef": snapshot["ksef"],
            "telegram": snapshot["telegram"],
            "slack": snapshot["slack"],
            "ocr": snapshot["ocr"],
            "storage": snapshot["storage"],
        }

    def email_scheduler_status(self) -> dict[str, Any]:
        with self._email_scheduler_state_lock:
            state = dict(self._email_scheduler_state)
        last_result = state.pop("last_result", None)
        configured = self.email_adapter.is_configured()
        enabled = bool(EMAIL_AUTOCHECK_ENABLED)
        return {
            "enabled": enabled,
            "configured": configured,
            "active": enabled and configured,
            "interval_seconds": EMAIL_AUTOCHECK_SECONDS,
            "mode": "automatic_interval" if enabled else "manual_only",
            "last_summary": {
                "status": (last_result or {}).get("status"),
                "checked_organization_count": (last_result or {}).get("checked_organization_count"),
                "imported_invoice_count": (last_result or {}).get("imported_invoice_count"),
                "organizations_with_imports": (last_result or {}).get("organizations_with_imports"),
                "organizations_without_new_documents": (last_result or {}).get("organizations_without_new_documents"),
                "organizations_with_errors": (last_result or {}).get("organizations_with_errors"),
            },
            **state,
        }

    def run_email_scheduler_cycle(self, actor: str = "system-email-scheduler") -> dict[str, Any]:
        status = self.email_scheduler_status()
        if not status["enabled"]:
            result = {
                "status": "disabled",
                "message": "Automatyczne sprawdzanie e-mail jest wylaczone w konfiguracji.",
                "checked_organization_count": 0,
                "imported_invoice_count": 0,
                "organizations_with_imports": 0,
                "organizations_without_new_documents": 0,
                "organizations_with_errors": 0,
                "results": [],
            }
            self._update_email_scheduler_state(
                running=False,
                last_status="disabled",
                last_message=result["message"],
                last_result=result,
            )
            return result

        if not status["configured"]:
            result = {
                "status": "not_configured",
                "message": "Automatyczne sprawdzanie e-mail czeka na konfiguracje IMAP.",
                "checked_organization_count": 0,
                "imported_invoice_count": 0,
                "organizations_with_imports": 0,
                "organizations_without_new_documents": 0,
                "organizations_with_errors": 0,
                "results": [],
            }
            self._update_email_scheduler_state(
                running=False,
                last_status="not_configured",
                last_message=result["message"],
                last_result=result,
            )
            return result

        if not self._email_scheduler_lock.acquire(blocking=False):
            return {
                "status": "already_running",
                "message": "Automatyczne sprawdzanie e-mail jest juz w trakcie pracy.",
                "checked_organization_count": 0,
                "imported_invoice_count": 0,
                "organizations_with_imports": 0,
                "organizations_without_new_documents": 0,
                "organizations_with_errors": 0,
                "results": [],
            }

        started_at = now_iso()
        self._update_email_scheduler_state(
            running=True,
            last_started_at=started_at,
            last_status="running",
            last_message="Automatyczne sprawdzanie e-mail trwa.",
        )

        try:
            organizations = self.organization_repository.list_email_ready_organizations(only_active=True)
            if not organizations:
                result = {
                    "status": "no_ready_organizations",
                    "message": "Brak organizacji gotowych do automatycznego importu e-mail.",
                    "checked_organization_count": 0,
                    "imported_invoice_count": 0,
                    "organizations_with_imports": 0,
                    "organizations_without_new_documents": 0,
                    "organizations_with_errors": 0,
                    "results": [],
                }
                self._update_email_scheduler_state(
                    running=False,
                    last_finished_at=now_iso(),
                    last_status=result["status"],
                    last_message=result["message"],
                    last_result=result,
                )
                return result

            organization_results: list[dict[str, Any]] = []
            imported_invoice_count = 0
            organizations_with_imports = 0
            organizations_without_new_documents = 0
            organizations_with_errors = 0

            for organization in organizations:
                organization_id = int(organization["organization_id"])
                try:
                    check_result = self._check_organization_email_for_organization(
                        organization,
                        actor=actor,
                        trigger_mode="automatic",
                    )
                    imported_count = int(check_result.get("imported_count") or 0)
                    result_status = str(check_result.get("status") or "")
                    imported_invoice_count += imported_count
                    if imported_count > 0:
                        organizations_with_imports += 1
                    if result_status == "no_new_documents":
                        organizations_without_new_documents += 1
                    elif result_status == "completed_with_issues":
                        organizations_with_errors += 1
                    organization_results.append(
                        {
                            "organization_id": organization_id,
                            "organization_name": organization.get("name"),
                            "status": result_status,
                            "message": check_result.get("message"),
                            "imported_count": imported_count,
                            "skipped_existing_count": int(check_result.get("skipped_existing_count") or 0),
                            "skipped_error_count": int(check_result.get("skipped_error_count") or 0),
                            "checked_message_count": int(check_result.get("checked_message_count") or 0),
                            "matched_message_count": int(check_result.get("matched_message_count") or 0),
                            "matched_attachment_count": int(check_result.get("matched_attachment_count") or 0),
                            "run_id": int((check_result.get("run") or {}).get("email_import_run_id") or 0) or None,
                        }
                    )
                except ValueError as error:
                    organizations_with_errors += 1
                    organization_results.append(
                        {
                            "organization_id": organization_id,
                            "organization_name": organization.get("name"),
                            "status": "failed",
                            "message": str(error),
                            "imported_count": 0,
                            "skipped_existing_count": 0,
                            "skipped_error_count": 1,
                            "checked_message_count": 0,
                            "matched_message_count": 0,
                            "matched_attachment_count": 0,
                            "run_id": None,
                        }
                    )

            checked_organization_count = len(organizations)
            if imported_invoice_count:
                message = (
                    f"Automatyczne sprawdzenie e-mail zakonczylo sie sukcesem. "
                    f"Organizacje: {checked_organization_count}. Zaimportowane faktury: {imported_invoice_count}."
                )
                status_name = "completed"
            elif organizations_with_errors:
                message = (
                    f"Automatyczne sprawdzenie e-mail zakonczylo sie z uwagami. "
                    f"Organizacje z bledami lub dokumentami do sprawdzenia: {organizations_with_errors}."
                )
                status_name = "completed_with_issues"
            else:
                message = (
                    f"Automatyczne sprawdzenie e-mail nie znalazlo nowych dokumentow. "
                    f"Sprawdzone organizacje: {checked_organization_count}."
                )
                status_name = "no_new_documents"

            result = {
                "status": status_name,
                "message": message,
                "checked_organization_count": checked_organization_count,
                "imported_invoice_count": imported_invoice_count,
                "organizations_with_imports": organizations_with_imports,
                "organizations_without_new_documents": organizations_without_new_documents,
                "organizations_with_errors": organizations_with_errors,
                "results": organization_results,
            }
            self._update_email_scheduler_state(
                running=False,
                last_finished_at=now_iso(),
                last_status=status_name,
                last_message=message,
                last_result=result,
            )
            return result
        except Exception as error:
            failure_message = f"Automatyczne sprawdzanie e-mail przerwalo sie bledem: {error}"
            self._update_email_scheduler_state(
                running=False,
                last_finished_at=now_iso(),
                last_status="failed",
                last_message=failure_message,
                last_result={
                    "status": "failed",
                    "message": failure_message,
                    "checked_organization_count": 0,
                    "imported_invoice_count": 0,
                    "organizations_with_imports": 0,
                    "organizations_without_new_documents": 0,
                    "organizations_with_errors": 1,
                    "results": [],
                },
            )
            raise
        finally:
            self._email_scheduler_lock.release()

    def _update_email_scheduler_state(self, **fields: Any) -> None:
        if not fields:
            return
        with self._email_scheduler_state_lock:
            self._email_scheduler_state.update(fields)

    def list_organization_email_import_runs(
        self,
        organization_id: int,
        *,
        limit: int = 8,
    ) -> list[dict[str, Any]]:
        organization = self.organization_repository.get_by_id(organization_id)
        if not organization:
            raise ValueError("Nie znaleziono organizacji.")
        return self.email_import_repository.list_runs_for_organization(organization_id, limit=limit)

    def list_organization_ksef_import_runs(
        self,
        organization_id: int,
        *,
        limit: int = 8,
    ) -> list[dict[str, Any]]:
        organization = self.organization_repository.get_by_id(organization_id)
        if not organization:
            raise ValueError("Nie znaleziono organizacji.")
        return self.ksef_import_repository.list_runs_for_organization(organization_id, limit=limit)

    def ocr_integration_info(self) -> dict[str, Any]:
        return self.ocr_engine.integration_status()

    def storage_integration_info(self) -> dict[str, Any]:
        return {"backend": self.storage_service.backend_name}

    def test_organization_ksef_connection(
        self,
        organization_id: int,
        actor: str = "system",
    ) -> dict[str, Any]:
        organization = self.organization_repository.get_by_id(organization_id)
        if not organization:
            raise ValueError("Nie znaleziono organizacji.")
        if not organization.get("ksef_company_identifier"):
            raise ValueError("Uzupelnij identyfikator firmy w KSeF przed testem polaczenia.")

        checked_at = now_iso()
        try:
            result = self.ksef_client.test_connection(organization)
        except Exception as error:
            message = str(error)
            self.organization_repository.update_ksef_connection_state(
                int(organization["organization_id"]),
                checked_at=checked_at,
                status=message,
            )
            self.event_repository.log(
                event_type="ksef_connection_test_failed",
                invoice_id=None,
                organization_id=int(organization["organization_id"]),
                source="KSEF",
                status_before=None,
                status_after=None,
                decision_reason=message,
                actor=actor,
                details={
                    "mode": "manual-test",
                    "company_identifier": organization.get("ksef_company_identifier"),
                    "environment": organization.get("ksef_environment"),
                },
            )
            raise ValueError(message) from error

        message = str(result.get("message") or "Polaczenie KSeF jest gotowe.")
        self.organization_repository.update_ksef_connection_state(
            int(organization["organization_id"]),
            checked_at=checked_at,
            status=message,
        )
        self.event_repository.log(
            event_type="ksef_connection_tested",
            invoice_id=None,
            organization_id=int(organization["organization_id"]),
            source="KSEF",
            status_before=None,
            status_after="connected",
            decision_reason=message,
            actor=actor,
            details={
                "mode": "manual-test",
                "company_identifier": organization.get("ksef_company_identifier"),
                "environment": organization.get("ksef_environment"),
            },
        )
        return {
            "status": "connection_ok",
            "message": message,
            "environment": result.get("environment"),
            "environment_label": result.get("environment_label"),
            "company_identifier": result.get("company_identifier"),
        }

    def check_organization_ksef(
        self,
        organization_id: int,
        actor: str = "system",
    ) -> dict[str, Any]:
        organization = self.organization_repository.get_by_id(organization_id)
        if not organization:
            raise ValueError("Nie znaleziono organizacji.")
        return self._check_organization_ksef_for_organization(
            organization,
            actor=actor,
            trigger_mode="manual",
        )

    def _check_organization_ksef_for_organization(
        self,
        organization: dict[str, Any],
        *,
        actor: str,
        trigger_mode: str,
    ) -> dict[str, Any]:
        if not organization.get("is_active"):
            raise ValueError("Nie mozna sprawdzic KSeF dla nieaktywnej organizacji.")
        if not organization.get("ksef_integration_enabled"):
            raise ValueError("Integracja KSeF jest wylaczona dla tej organizacji.")
        if not organization.get("ksef_company_identifier"):
            raise ValueError("Uzupelnij identyfikator firmy w KSeF przed sprawdzeniem.")

        normalized_trigger_mode = "automatic" if str(trigger_mode or "").strip().lower() == "automatic" else "manual"
        checked_at = now_iso()
        run_id = self.ksef_import_repository.start_run(
            organization_id=int(organization["organization_id"]),
            company_identifier=organization.get("ksef_company_identifier"),
            environment=organization.get("ksef_environment"),
            trigger_mode=normalized_trigger_mode,
            actor=actor,
            details={
                "company_identifier": organization.get("ksef_company_identifier"),
                "environment": organization.get("ksef_environment"),
                "mode": normalized_trigger_mode,
            },
        )

        try:
            fetch_result = self.ksef_client.fetch_invoice_candidates(
                organization,
                limit=KSEF_FETCH_LIMIT,
                trigger_mode=normalized_trigger_mode,
            )
        except Exception as error:
            message = str(error)
            self.organization_repository.update_ksef_check_state(
                int(organization["organization_id"]),
                checked_at=checked_at,
                status=message,
            )
            self.ksef_import_repository.finalize_run(
                run_id,
                status="failed",
                checked_document_count=0,
                imported_invoice_count=0,
                skipped_existing_count=0,
                skipped_error_count=0,
                summary_message=message,
                details={
                    "company_identifier": organization.get("ksef_company_identifier"),
                    "environment": organization.get("ksef_environment"),
                    "error": message,
                    "mode": normalized_trigger_mode,
                },
            )
            self.event_repository.log(
                event_type="ksef_check_failed",
                invoice_id=None,
                organization_id=int(organization["organization_id"]),
                source="KSEF",
                status_before=None,
                status_after=None,
                decision_reason=message,
                actor=actor,
                details={
                    "mode": normalized_trigger_mode,
                    "company_identifier": organization.get("ksef_company_identifier"),
                    "environment": organization.get("ksef_environment"),
                },
            )
            raise ValueError(message) from error

        candidates = list(fetch_result.get("candidates") or [])
        checked_document_count = int(fetch_result.get("checked_document_count") or len(candidates))
        environment = str(fetch_result.get("environment") or organization.get("ksef_environment") or "demo")
        company_identifier = str(fetch_result.get("company_identifier") or organization.get("ksef_company_identifier") or "")

        imported_invoices: list[dict[str, Any]] = []
        imported_source_external_ids: list[str] = []
        skipped_existing_count = 0
        skipped_error_count = 0
        skipped_errors: list[dict[str, str]] = []

        for payload in candidates:
            existing = self.invoice_repository.get_by_source_external_id(
                str(payload.get("source_external_id") or ""),
                source="KSEF",
                organization_id=int(organization["organization_id"]),
            )
            if existing:
                skipped_existing_count += 1
                self.ksef_import_repository.add_item(
                    run_id=run_id,
                    organization_id=int(organization["organization_id"]),
                    source_external_id=str(payload.get("source_external_id") or ""),
                    ksef_number=str(payload.get("ksef_number") or ""),
                    invoice_number=str(payload.get("invoice_number") or ""),
                    issuer_nip=str(payload.get("issuer_nip") or ""),
                    issue_date=str(payload.get("issue_date") or ""),
                    item_status="skipped_existing",
                    invoice_id=int(existing["id"]),
                    reason="Dokument KSeF byl juz wczesniej zaimportowany.",
                )
                continue

            try:
                imported_invoice = self.create_invoice(
                    {**payload, "organization_id": int(organization["organization_id"])},
                    actor=actor,
                    organization_id=int(organization["organization_id"]),
                )
            except ValueError as error:
                skipped_error_count += 1
                skipped_errors.append(
                    {
                        "invoice_number": str(payload.get("invoice_number") or ""),
                        "ksef_number": str(payload.get("ksef_number") or ""),
                        "error": str(error),
                    }
                )
                self.ksef_import_repository.add_item(
                    run_id=run_id,
                    organization_id=int(organization["organization_id"]),
                    source_external_id=str(payload.get("source_external_id") or ""),
                    ksef_number=str(payload.get("ksef_number") or ""),
                    invoice_number=str(payload.get("invoice_number") or ""),
                    issuer_nip=str(payload.get("issuer_nip") or ""),
                    issue_date=str(payload.get("issue_date") or ""),
                    item_status="skipped_error",
                    invoice_id=None,
                    reason=str(error),
                )
                continue

            imported_invoices.append(imported_invoice)
            imported_source_external_ids.append(str(imported_invoice.get("source_external_id") or ""))
            self.ksef_import_repository.add_item(
                run_id=run_id,
                organization_id=int(organization["organization_id"]),
                source_external_id=str(imported_invoice.get("source_external_id") or ""),
                ksef_number=str(imported_invoice.get("ksef_number") or ""),
                invoice_number=str(imported_invoice.get("invoice_number") or ""),
                issuer_nip=str(imported_invoice.get("issuer_nip") or ""),
                issue_date=str(imported_invoice.get("issue_date") or ""),
                item_status="imported",
                invoice_id=int(imported_invoice["id"]),
                reason="Faktura z KSeF zostala zaimportowana do systemu.",
            )

        imported_count = len(imported_invoices)
        first_imported_invoice = imported_invoices[0] if imported_invoices else None

        if imported_count == 0:
            if skipped_error_count:
                message = (
                    f"Nie zaimportowano nowych faktur z KSeF. "
                    f"{skipped_error_count} dokument(y) wymagaja uwagi."
                )
                result_status = "completed_with_issues"
            else:
                message = "Brak nowych dokumentow KSeF do importu."
                result_status = "no_new_documents"
            self.organization_repository.update_ksef_check_state(
                int(organization["organization_id"]),
                checked_at=checked_at,
                status=message,
            )
            self.ksef_import_repository.finalize_run(
                run_id,
                status=result_status,
                checked_document_count=checked_document_count,
                imported_invoice_count=0,
                skipped_existing_count=skipped_existing_count,
                skipped_error_count=skipped_error_count,
                summary_message=message,
                details={
                    "mode": normalized_trigger_mode,
                    "company_identifier": company_identifier,
                    "environment": environment,
                    "checked_candidates": len(candidates),
                    "checked_document_count": checked_document_count,
                    "skipped_existing_count": skipped_existing_count,
                    "skipped_error_count": skipped_error_count,
                    "errors": skipped_errors,
                },
            )
            self.event_repository.log(
                event_type="ksef_check_executed",
                invoice_id=None,
                organization_id=int(organization["organization_id"]),
                source="KSEF",
                status_before=None,
                status_after=None,
                decision_reason=message,
                actor=actor,
                details={
                    "mode": normalized_trigger_mode,
                    "company_identifier": company_identifier,
                    "environment": environment,
                    "checked_document_count": checked_document_count,
                    "checked_candidates": len(candidates),
                    "skipped_existing_count": skipped_existing_count,
                    "skipped_error_count": skipped_error_count,
                    "errors": skipped_errors,
                },
            )
            return {
                "status": result_status,
                "message": message,
                "checked_at": checked_at,
                "environment": environment,
                "company_identifier": company_identifier,
                "imported_count": 0,
                "checked_document_count": checked_document_count,
                "checked_candidates": len(candidates),
                "skipped_existing_count": skipped_existing_count,
                "skipped_error_count": skipped_error_count,
                "errors": skipped_errors,
                "invoice": None,
                "invoices": [],
                "run": self.ksef_import_repository.list_runs_for_organization(
                    int(organization["organization_id"]),
                    limit=1,
                )[0],
            }

        message = f"Zaimportowano {imported_count} nowych faktur z KSeF."
        if skipped_existing_count:
            message += f" Pominieto {skipped_existing_count} juz znanych dokumentow."
        if skipped_error_count:
            message += f" {skipped_error_count} dokument(y) wymaga(y) uwagi."

        self.organization_repository.update_ksef_check_state(
            int(organization["organization_id"]),
            checked_at=checked_at,
            status=message,
        )
        self.ksef_import_repository.finalize_run(
            run_id,
            status="completed" if skipped_error_count == 0 else "completed_with_issues",
            checked_document_count=checked_document_count,
            imported_invoice_count=imported_count,
            skipped_existing_count=skipped_existing_count,
            skipped_error_count=skipped_error_count,
            summary_message=message,
            details={
                "mode": normalized_trigger_mode,
                "company_identifier": company_identifier,
                "environment": environment,
                "checked_candidates": len(candidates),
                "checked_document_count": checked_document_count,
                "invoice_ids": [item.get("id") for item in imported_invoices],
                "source_external_ids": imported_source_external_ids,
                "skipped_existing_count": skipped_existing_count,
                "skipped_error_count": skipped_error_count,
                "errors": skipped_errors,
            },
        )
        self.event_repository.log(
            event_type="ksef_check_executed",
            invoice_id=int(first_imported_invoice["id"]) if imported_count == 1 and first_imported_invoice else None,
            organization_id=int(organization["organization_id"]),
            source="KSEF",
            status_before=None,
            status_after="imported",
            decision_reason=message,
            actor=actor,
            details={
                "mode": normalized_trigger_mode,
                "company_identifier": company_identifier,
                "environment": environment,
                "checked_document_count": checked_document_count,
                "checked_candidates": len(candidates),
                "invoice_ids": [item.get("id") for item in imported_invoices],
                "source_external_ids": imported_source_external_ids,
                "imported_count": imported_count,
                "skipped_existing_count": skipped_existing_count,
                "skipped_error_count": skipped_error_count,
                "errors": skipped_errors,
            },
        )
        return {
            "status": "invoice_imported" if imported_count == 1 else "invoices_imported",
            "message": message,
            "checked_at": checked_at,
            "environment": environment,
            "company_identifier": company_identifier,
            "imported_count": imported_count,
            "checked_document_count": checked_document_count,
            "checked_candidates": len(candidates),
            "skipped_existing_count": skipped_existing_count,
            "skipped_error_count": skipped_error_count,
            "errors": skipped_errors,
            "invoice": first_imported_invoice,
            "invoices": imported_invoices,
            "run": self.ksef_import_repository.list_runs_for_organization(
                int(organization["organization_id"]),
                limit=1,
            )[0],
        }

    def test_organization_email_connection(
        self,
        organization_id: int,
        actor: str = "system",
    ) -> dict[str, Any]:
        organization = self.organization_repository.get_by_id(organization_id)
        if not organization:
            raise ValueError("Nie znaleziono organizacji.")
        if not organization.get("email_inbox_address"):
            raise ValueError("Uzupelnij adres skrzynki e-mail przed testem polaczenia.")

        checked_at = now_iso()
        try:
            connection_result = self.email_adapter.test_connection(limit=5)
        except EmailIngestionError as error:
            message = str(error)
            self.organization_repository.update_email_connection_state(
                int(organization["organization_id"]),
                checked_at=checked_at,
                status=message,
            )
            self.event_repository.log(
                event_type="email_connection_test_failed",
                invoice_id=None,
                organization_id=int(organization["organization_id"]),
                source="EMAIL",
                status_before=None,
                status_after=None,
                decision_reason=message,
                actor=actor,
                details={
                    "mode": "manual-test",
                    "mailbox": organization.get("email_inbox_address"),
                    "allowed_sender": organization.get("email_allowed_sender"),
                    "subject_keyword": organization.get("email_subject_keyword"),
                },
            )
            raise ValueError(message) from error

        visible_count = int(connection_result.get("message_count") or 0)
        folder_name = str(connection_result.get("folder") or "INBOX")
        message = f"Polaczenie IMAP dziala. Folder: {folder_name}. Wiadomosci widoczne: {visible_count}."
        self.organization_repository.update_email_connection_state(
            int(organization["organization_id"]),
            checked_at=checked_at,
            status=message,
        )
        self.event_repository.log(
            event_type="email_connection_tested",
            invoice_id=None,
            organization_id=int(organization["organization_id"]),
            source="EMAIL",
            status_before=None,
            status_after="connected",
            decision_reason=message,
            actor=actor,
            details={
                "mode": "manual-test",
                "mailbox": organization.get("email_inbox_address"),
                "allowed_sender": organization.get("email_allowed_sender"),
                "subject_keyword": organization.get("email_subject_keyword"),
                "connection": connection_result,
            },
        )
        return {
            "status": "connection_ok",
            "message": message,
            "checked_at": checked_at,
            "mailbox": organization.get("email_inbox_address"),
            "allowed_sender": organization.get("email_allowed_sender"),
            "subject_keyword": organization.get("email_subject_keyword"),
            **connection_result,
        }

    def check_organization_email(
        self,
        organization_id: int,
        actor: str = "system",
    ) -> dict[str, Any]:
        organization = self.organization_repository.get_by_id(organization_id)
        if not organization:
            raise ValueError("Nie znaleziono organizacji.")
        return self._check_organization_email_for_organization(
            organization,
            actor=actor,
            trigger_mode="manual",
        )

    def _check_organization_email_for_organization(
        self,
        organization: dict[str, Any],
        *,
        actor: str,
        trigger_mode: str,
    ) -> dict[str, Any]:
        if not organization.get("is_active"):
            raise ValueError("Nie mozna sprawdzic e-maila dla nieaktywnej organizacji.")
        if not organization.get("email_integration_enabled"):
            raise ValueError("Integracja e-mail jest wylaczona dla tej organizacji.")
        if not organization.get("email_inbox_address"):
            raise ValueError("Uzupelnij adres skrzynki e-mail przed sprawdzeniem.")

        normalized_trigger_mode = "automatic" if str(trigger_mode or "").strip().lower() == "automatic" else "manual"
        checked_at = now_iso()
        run_id = self.email_import_repository.start_run(
            organization_id=int(organization["organization_id"]),
            mailbox_address=self.email_adapter.mailbox_address(),
            inbox_address=organization.get("email_inbox_address"),
            trigger_mode=normalized_trigger_mode,
            actor=actor,
            routing_mode="central_mailbox",
            details={
                "mailbox": organization.get("email_inbox_address"),
                "allowed_sender": organization.get("email_allowed_sender"),
                "subject_keyword": organization.get("email_subject_keyword"),
                "mode": normalized_trigger_mode,
            },
        )
        try:
            fetch_result = self.email_adapter.fetch_invoice_candidates(
                organization,
                trigger_mode=normalized_trigger_mode,
            )
        except EmailIngestionError as error:
            message = str(error)
            self.organization_repository.update_email_check_state(
                int(organization["organization_id"]),
                checked_at=checked_at,
                status=message,
            )
            self.email_import_repository.finalize_run(
                run_id,
                status="failed",
                checked_message_count=0,
                matched_message_count=0,
                matched_attachment_count=0,
                imported_invoice_count=0,
                skipped_existing_count=0,
                skipped_error_count=0,
                summary_message=message,
                details={
                    "mailbox": organization.get("email_inbox_address"),
                    "allowed_sender": organization.get("email_allowed_sender"),
                    "subject_keyword": organization.get("email_subject_keyword"),
                    "error": message,
                    "mode": normalized_trigger_mode,
                },
            )
            self.event_repository.log(
                event_type="email_check_failed",
                invoice_id=None,
                organization_id=int(organization["organization_id"]),
                source="EMAIL",
                status_before=None,
                status_after=None,
                decision_reason=message,
                actor=actor,
                details={
                    "mode": normalized_trigger_mode,
                    "mailbox": organization.get("email_inbox_address"),
                    "allowed_sender": organization.get("email_allowed_sender"),
                },
            )
            raise ValueError(message) from error

        candidates = list(fetch_result.get("candidates") or [])
        checked_message_count = int(fetch_result.get("checked_message_count") or 0)
        matched_message_count = int(fetch_result.get("matched_message_count") or 0)
        matched_attachment_count = int(fetch_result.get("matched_attachment_count") or len(candidates))

        imported_invoices: list[dict[str, Any]] = []
        imported_source_external_ids: list[str] = []
        skipped_existing_count = 0
        skipped_error_count = 0
        skipped_errors: list[dict[str, str]] = []
        for payload in candidates:
            existing = self.invoice_repository.get_by_source_external_id(
                str(payload.get("source_external_id") or ""),
                source="EMAIL",
                organization_id=int(organization["organization_id"]),
            )
            if existing:
                skipped_existing_count += 1
                self.email_import_repository.add_item(
                    run_id=run_id,
                    organization_id=int(organization["organization_id"]),
                    imap_uid=str(payload.get("source_metadata", {}).get("imap_uid") or ""),
                    message_id=str(payload.get("source_metadata", {}).get("message_id") or ""),
                    sender_email=str(payload.get("source_metadata", {}).get("nadawca_email") or ""),
                    subject=str(payload.get("source_metadata", {}).get("temat") or ""),
                    recipients=list(payload.get("source_metadata", {}).get("odbiorcy") or []),
                    matched_recipient=str(payload.get("source_metadata", {}).get("dopasowany_odbiorca") or ""),
                    attachment_name=str(payload.get("file_name") or ""),
                    attachment_type=str(payload.get("source_metadata", {}).get("zalacznik_typ") or ""),
                    attachment_index=int(payload.get("source_metadata", {}).get("zalacznik_index") or 0),
                    source_external_id=str(payload.get("source_external_id") or ""),
                    item_status="skipped_existing",
                    invoice_id=int(existing["id"]),
                    reason="Dokument byl juz wczesniej zaimportowany.",
                )
                continue

            try:
                imported_invoice = self.create_invoice(
                    {**payload, "organization_id": int(organization["organization_id"])},
                    actor=actor,
                    organization_id=int(organization["organization_id"]),
                )
            except ValueError as error:
                skipped_error_count += 1
                skipped_errors.append(
                    {
                        "file_name": str(payload.get("file_name") or ""),
                        "error": str(error),
                    }
                )
                self.email_import_repository.add_item(
                    run_id=run_id,
                    organization_id=int(organization["organization_id"]),
                    imap_uid=str(payload.get("source_metadata", {}).get("imap_uid") or ""),
                    message_id=str(payload.get("source_metadata", {}).get("message_id") or ""),
                    sender_email=str(payload.get("source_metadata", {}).get("nadawca_email") or ""),
                    subject=str(payload.get("source_metadata", {}).get("temat") or ""),
                    recipients=list(payload.get("source_metadata", {}).get("odbiorcy") or []),
                    matched_recipient=str(payload.get("source_metadata", {}).get("dopasowany_odbiorca") or ""),
                    attachment_name=str(payload.get("file_name") or ""),
                    attachment_type=str(payload.get("source_metadata", {}).get("zalacznik_typ") or ""),
                    attachment_index=int(payload.get("source_metadata", {}).get("zalacznik_index") or 0),
                    source_external_id=str(payload.get("source_external_id") or ""),
                    item_status="skipped_error",
                    invoice_id=None,
                    reason=str(error),
                )
                continue

            imported_invoices.append(imported_invoice)
            imported_source_external_ids.append(str(imported_invoice.get("source_external_id") or ""))
            self.email_import_repository.add_item(
                run_id=run_id,
                organization_id=int(organization["organization_id"]),
                imap_uid=str(payload.get("source_metadata", {}).get("imap_uid") or ""),
                message_id=str(payload.get("source_metadata", {}).get("message_id") or ""),
                sender_email=str(payload.get("source_metadata", {}).get("nadawca_email") or ""),
                subject=str(payload.get("source_metadata", {}).get("temat") or ""),
                recipients=list(payload.get("source_metadata", {}).get("odbiorcy") or []),
                matched_recipient=str(payload.get("source_metadata", {}).get("dopasowany_odbiorca") or ""),
                attachment_name=str(payload.get("file_name") or ""),
                attachment_type=str(payload.get("source_metadata", {}).get("zalacznik_typ") or ""),
                attachment_index=int(payload.get("source_metadata", {}).get("zalacznik_index") or 0),
                source_external_id=str(imported_invoice.get("source_external_id") or ""),
                item_status="imported",
                invoice_id=int(imported_invoice["id"]),
                reason="Faktura zostala zaimportowana do systemu.",
            )

        imported_count = len(imported_invoices)
        first_imported_invoice = imported_invoices[0] if imported_invoices else None

        if imported_count == 0:
            if skipped_error_count:
                message = (
                    f"Nie zaimportowano nowych faktur z e-maila. "
                    f"{skipped_error_count} dokument(y) wymagaja uwagi."
                )
                result_status = "completed_with_issues"
            else:
                message = "Brak nowych dokumentow e-mail do importu."
                result_status = "no_new_documents"
            self.organization_repository.update_email_check_state(
                int(organization["organization_id"]),
                checked_at=checked_at,
                status=message,
            )
            self.email_import_repository.finalize_run(
                run_id,
                status=result_status,
                checked_message_count=checked_message_count,
                matched_message_count=matched_message_count,
                matched_attachment_count=matched_attachment_count,
                imported_invoice_count=0,
                skipped_existing_count=skipped_existing_count,
                skipped_error_count=skipped_error_count,
                summary_message=message,
                details={
                    "mode": normalized_trigger_mode,
                    "mailbox": organization.get("email_inbox_address"),
                    "allowed_sender": organization.get("email_allowed_sender"),
                    "checked_candidates": len(candidates),
                    "checked_message_count": checked_message_count,
                    "matched_message_count": matched_message_count,
                    "matched_attachment_count": matched_attachment_count,
                    "skipped_existing_count": skipped_existing_count,
                    "skipped_error_count": skipped_error_count,
                    "errors": skipped_errors,
                },
            )
            self.event_repository.log(
                event_type="email_check_executed",
                invoice_id=None,
                organization_id=int(organization["organization_id"]),
                source="EMAIL",
                status_before=None,
                status_after=None,
                decision_reason=message,
                actor=actor,
                details={
                    "mode": normalized_trigger_mode,
                    "mailbox": organization.get("email_inbox_address"),
                    "allowed_sender": organization.get("email_allowed_sender"),
                    "checked_message_count": checked_message_count,
                    "matched_message_count": matched_message_count,
                    "matched_attachment_count": matched_attachment_count,
                    "checked_candidates": len(candidates),
                    "skipped_existing_count": skipped_existing_count,
                    "skipped_error_count": skipped_error_count,
                    "errors": skipped_errors,
                },
            )
            return {
                "status": result_status,
                "message": message,
                "checked_at": checked_at,
                "imported_count": 0,
                "checked_message_count": checked_message_count,
                "matched_message_count": matched_message_count,
                "matched_attachment_count": matched_attachment_count,
                "checked_candidates": len(candidates),
                "skipped_existing_count": skipped_existing_count,
                "skipped_error_count": skipped_error_count,
                "errors": skipped_errors,
                "invoice": None,
                "invoices": [],
                "run": self.email_import_repository.list_runs_for_organization(int(organization["organization_id"]), limit=1)[0],
            }

        message = f"Zaimportowano {imported_count} nowych faktur z e-maila."
        if skipped_existing_count:
            message += f" Pominieto {skipped_existing_count} juz znanych dokumentow."
        if skipped_error_count:
            message += f" {skipped_error_count} dokument(y) wymaga(y) uwagi."
        self.organization_repository.update_email_check_state(
            int(organization["organization_id"]),
            checked_at=checked_at,
            status=message,
        )
        self.email_import_repository.finalize_run(
            run_id,
            status="completed" if skipped_error_count == 0 else "completed_with_issues",
            checked_message_count=checked_message_count,
            matched_message_count=matched_message_count,
            matched_attachment_count=matched_attachment_count,
            imported_invoice_count=imported_count,
            skipped_existing_count=skipped_existing_count,
            skipped_error_count=skipped_error_count,
            summary_message=message,
            details={
                "mode": normalized_trigger_mode,
                "mailbox": organization.get("email_inbox_address"),
                "allowed_sender": organization.get("email_allowed_sender"),
                "checked_candidates": len(candidates),
                "checked_message_count": checked_message_count,
                "matched_message_count": matched_message_count,
                "matched_attachment_count": matched_attachment_count,
                "invoice_ids": [item.get("id") for item in imported_invoices],
                "source_external_ids": imported_source_external_ids,
                "skipped_existing_count": skipped_existing_count,
                "skipped_error_count": skipped_error_count,
                "errors": skipped_errors,
            },
        )
        self.event_repository.log(
            event_type="email_check_executed",
            invoice_id=int(first_imported_invoice["id"]) if imported_count == 1 and first_imported_invoice else None,
            organization_id=int(organization["organization_id"]),
            source="EMAIL",
            status_before=None,
            status_after="imported",
            decision_reason=message,
            actor=actor,
            details={
                "mode": normalized_trigger_mode,
                "mailbox": organization.get("email_inbox_address"),
                "allowed_sender": organization.get("email_allowed_sender"),
                "checked_message_count": checked_message_count,
                "matched_message_count": matched_message_count,
                "matched_attachment_count": matched_attachment_count,
                "invoice_ids": [item.get("id") for item in imported_invoices],
                "source_external_ids": imported_source_external_ids,
                "checked_candidates": len(candidates),
                "imported_count": imported_count,
                "skipped_existing_count": skipped_existing_count,
                "skipped_error_count": skipped_error_count,
                "errors": skipped_errors,
            },
        )
        return {
            "status": "invoice_imported" if imported_count == 1 else "invoices_imported",
            "message": message,
            "checked_at": checked_at,
            "imported_count": imported_count,
            "checked_message_count": checked_message_count,
            "matched_message_count": matched_message_count,
            "matched_attachment_count": matched_attachment_count,
            "checked_candidates": len(candidates),
            "skipped_existing_count": skipped_existing_count,
            "skipped_error_count": skipped_error_count,
            "errors": skipped_errors,
            "invoice": first_imported_invoice,
            "invoices": imported_invoices,
            "run": self.email_import_repository.list_runs_for_organization(int(organization["organization_id"]), limit=1)[0],
        }

    def list_invoices(self, filters: dict[str, Any], organization_id: int | None = None) -> list[dict[str, Any]]:
        return self.invoice_repository.list_invoices(filters, organization_id=organization_id)

    def verification_inbox_snapshot(
        self,
        *,
        organization_id: int | None = None,
        limit: int = 6,
    ) -> dict[str, Any]:
        queue_items = self._collect_verification_queue_items(organization_id=organization_id, ksef_limit=max(limit * 2, 10))
        sections = {
            "verification": self._build_verification_inbox_section(
                "Do weryfikacji",
                "Faktury wymagajace recznego sprawdzenia danych.",
                queue_items["verification"],
                limit=limit,
                action_key="status_verification",
            ),
            "duplicates": self._build_verification_inbox_section(
                "Duplikaty do decyzji",
                "Dokumenty oznaczone jako podejrzenie albo pewny duplikat.",
                queue_items["duplicates"],
                limit=limit,
                action_key="duplicate_review",
            ),
            "ksef_corrections": self._build_verification_inbox_section(
                "Korekty KSeF do zatwierdzenia",
                "Faktury z oczekujacymi prosbami o lokalna korekte danych potwierdzonych z KSeF.",
                queue_items["ksef_corrections"],
                limit=limit,
                action_key="ksef_pending",
            ),
            "ocr_attention": self._build_verification_inbox_section(
                "OCR wymaga uwagi",
                "Dokumenty, w ktorych OCR nie odczytal kluczowych pol i trzeba je szybko zweryfikowac.",
                queue_items["ocr_attention"],
                limit=limit,
                action_key="ocr_attention",
            ),
        }
        total_open_count = sum(int(section["count"]) for section in sections.values())
        return {
            "summary": {
                "total_open_count": total_open_count,
                "generated_at": now_iso(),
            },
            "sections": sections,
        }

    def verification_workspace_snapshot(
        self,
        *,
        organization_id: int | None = None,
        limit_per_bucket: int = 25,
        active_bucket: str | None = None,
    ) -> dict[str, Any]:
        queue_items = self._collect_verification_queue_items(
            organization_id=organization_id,
            ksef_limit=max(limit_per_bucket * 2, 20),
        )
        sections = {
            "verification": self._build_verification_workspace_section(
                "verification",
                "Do weryfikacji",
                "Faktury wymagajace recznego sprawdzenia danych i decyzji operatora.",
                queue_items["verification"],
                limit=limit_per_bucket,
            ),
            "duplicates": self._build_verification_workspace_section(
                "duplicates",
                "Duplikaty do decyzji",
                "Podejrzenia i pewne duplikaty wymagajace porownania albo potwierdzenia.",
                queue_items["duplicates"],
                limit=limit_per_bucket,
            ),
            "ksef_corrections": self._build_verification_workspace_section(
                "ksef_corrections",
                "Korekty KSeF do zatwierdzenia",
                "Propozycje lokalnych zmian do pol chronionych danymi z KSeF.",
                queue_items["ksef_corrections"],
                limit=limit_per_bucket,
            ),
            "ocr_attention": self._build_verification_workspace_section(
                "ocr_attention",
                "OCR wymaga uwagi",
                "Dokumenty z e-maila, Telegrama albo Slacka, w ktorych OCR nie odczytal kluczowych danych.",
                queue_items["ocr_attention"],
                limit=limit_per_bucket,
            ),
        }
        total_open_count = sum(int(section["count"]) for section in sections.values())
        total_sla_breached = sum(int(section["sla_breached_count"]) for section in sections.values())
        oldest_age_days = max((int(section["oldest_age_days"] or 0) for section in sections.values()), default=0)
        bucket_order = list(INVOICE_VERIFICATION_BUCKET_ORDER)
        resolved_active_bucket = (
            active_bucket
            if active_bucket in sections
            else next((key for key in bucket_order if int(sections[key]["count"]) > 0), bucket_order[0])
        )
        return {
            "summary": {
                "total_open_count": total_open_count,
                "total_sla_breached": total_sla_breached,
                "oldest_age_days": oldest_age_days,
                "generated_at": now_iso(),
                "active_bucket": resolved_active_bucket,
            },
            "bucket_order": bucket_order,
            "sections": sections,
        }

    def compare_invoices(
        self,
        left_invoice_id: int,
        right_invoice_id: int,
        *,
        organization_id: int | None = None,
    ) -> dict[str, Any] | None:
        if int(left_invoice_id) == int(right_invoice_id):
            raise ValueError("Wybierz dwie rozne faktury do porownania.")

        left_invoice = self.invoice_repository.get_by_id(left_invoice_id, organization_id=organization_id)
        right_invoice = self.invoice_repository.get_by_id(right_invoice_id, organization_id=organization_id)
        if not left_invoice or not right_invoice:
            return None

        left_contractor = None
        if left_invoice.get("contractor_id"):
            left_contractor = self.contractor_repository.get_by_id(
                int(left_invoice["contractor_id"]),
                organization_id=left_invoice.get("organization_id"),
            )
        right_contractor = None
        if right_invoice.get("contractor_id"):
            right_contractor = self.contractor_repository.get_by_id(
                int(right_invoice["contractor_id"]),
                organization_id=right_invoice.get("organization_id"),
            )

        left_overrides = self.invoice_ksef_override_repository.list_for_invoice(
            left_invoice_id,
            organization_id=left_invoice.get("organization_id"),
        )
        right_overrides = self.invoice_ksef_override_repository.list_for_invoice(
            right_invoice_id,
            organization_id=right_invoice.get("organization_id"),
        )
        left_provenance = {
            item["field_name"]: item
            for item in self._build_field_provenance(left_invoice, left_overrides, left_contractor)
        }
        right_provenance = {
            item["field_name"]: item
            for item in self._build_field_provenance(right_invoice, right_overrides, right_contractor)
        }

        compare_fields = (
            ("invoice_number", "Numer faktury"),
            ("ksef_number", "Numer KSeF"),
            ("issuer_nip", "NIP wystawcy"),
            ("issuer_name", "Nazwa wystawcy"),
            ("issue_date", "Data wystawienia"),
            ("sale_date", "Data sprzedazy"),
            ("gross_amount", "Kwota brutto"),
            ("currency", "Waluta"),
        )
        rows: list[dict[str, Any]] = []
        matching_count = 0
        for field_name, label in compare_fields:
            left_value = left_invoice.get(field_name)
            right_value = right_invoice.get(field_name)
            matches = self._normalize_duplicate_compare_value(field_name, left_value) == self._normalize_duplicate_compare_value(
                field_name,
                right_value,
            )
            if matches:
                matching_count += 1
            rows.append(
                {
                    "field_name": field_name,
                    "label": label,
                    "matches": matches,
                    "left_value": left_value,
                    "right_value": right_value,
                    "left_source_label": left_provenance.get(field_name, {}).get("source_label"),
                    "right_source_label": right_provenance.get(field_name, {}).get("source_label"),
                    "left_is_ksef_protected": bool(left_provenance.get(field_name, {}).get("is_ksef_protected")),
                    "right_is_ksef_protected": bool(right_provenance.get(field_name, {}).get("is_ksef_protected")),
                    "left_has_local_override": bool(left_provenance.get(field_name, {}).get("has_active_local_override")),
                    "right_has_local_override": bool(right_provenance.get(field_name, {}).get("has_active_local_override")),
                }
            )

        same_ksef_number = bool(left_invoice.get("ksef_number")) and str(left_invoice.get("ksef_number")) == str(
            right_invoice.get("ksef_number")
        )
        same_invoice_number_and_nip = (
            bool(left_invoice.get("invoice_number"))
            and str(left_invoice.get("invoice_number")) == str(right_invoice.get("invoice_number"))
            and bool(left_invoice.get("issuer_nip"))
            and str(left_invoice.get("issuer_nip")) == str(right_invoice.get("issuer_nip"))
        )
        if same_ksef_number:
            recommendation = "Pewny duplikat wedlug numeru KSeF."
        elif same_invoice_number_and_nip:
            recommendation = "Wysokie prawdopodobienstwo duplikatu wedlug numeru faktury i NIP-u wystawcy."
        elif matching_count >= 4:
            recommendation = "Dokumenty sa bardzo podobne i wymagaja szybkiego porownania operacyjnego."
        else:
            recommendation = "Dokumenty roznia sie w kilku kluczowych polach. Wymagana reczna decyzja."

        return {
            "summary": {
                "matching_count": matching_count,
                "different_count": len(rows) - matching_count,
                "same_ksef_number": same_ksef_number,
                "same_invoice_number_and_nip": same_invoice_number_and_nip,
                "recommendation": recommendation,
            },
            "left_invoice": self._build_compare_invoice_header(left_invoice),
            "right_invoice": self._build_compare_invoice_header(right_invoice),
            "rows": rows,
        }

    def list_contractors(
        self,
        search: str = "",
        only_new: bool = False,
        organization_id: int | None = None,
    ) -> list[dict[str, Any]]:
        return self.contractor_repository.list_contractors(search, only_new=only_new, organization_id=organization_id)

    def list_logs(
        self,
        organization_id: int | None = None,
        viewer_user_id: int | None = None,
    ) -> list[dict[str, Any]]:
        events = self.event_repository.list_logs(organization_id=organization_id)
        return self._filter_events_for_viewer(events, viewer_user_id)

    def _parse_json_object(self, raw_value: Any) -> dict[str, Any]:
        if isinstance(raw_value, dict):
            return raw_value
        if not raw_value:
            return {}
        try:
            parsed = json.loads(str(raw_value))
        except (TypeError, ValueError):
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _find_invoice_document_intake_item(
        self,
        invoice_id: int,
        organization_id: int,
    ) -> dict[str, Any] | None:
        if not self.intake_repository:
            return None
        items = self.intake_repository.list_items(
            organization_id=organization_id,
            source_kind=INVOICE_DOCUMENT_INTAKE_KIND,
            linked_invoice_id=invoice_id,
            limit=5,
        )
        return items[0] if items else None

    def _find_invoice_related_document_items(
        self,
        invoice_id: int,
        organization_id: int | None,
    ) -> list[dict[str, Any]]:
        if not self.intake_repository or organization_id in (None, ""):
            return []
        return self.intake_repository.list_items(
            organization_id=int(organization_id),
            source_kind=INVOICE_DOCUMENT_INTAKE_KIND,
            linked_invoice_id=int(invoice_id),
            limit=20,
        )

    def _organization_uses_ksef(self, organization_id: int | None) -> bool:
        if organization_id in (None, ""):
            return False
        organization = self.organization_repository.get_by_id(int(organization_id))
        return bool(organization and int(organization.get("ksef_integration_enabled") or 0))

    def _derive_invoice_document_intake_status(self, invoice: dict[str, Any]) -> str:
        workflow_state = str(invoice.get("workflow_state") or "w_pracy").strip().lower()
        status = str(invoice.get("status") or "").strip().lower()
        if workflow_state in {"przekazana", "zamknieta"}:
            return "zakonczone"
        if status == "weryfikacja":
            return "w_toku"
        return "nowe" if workflow_state == "w_pracy" else "w_toku"

    def _build_invoice_document_intake_payload(self, invoice: dict[str, Any]) -> dict[str, Any]:
        metadata = {
            "invoice_id": int(invoice["id"]),
            "source": invoice.get("source"),
            "source_external_id": invoice.get("source_external_id"),
            "invoice_number": invoice.get("invoice_number"),
            "ksef_number": invoice.get("ksef_number"),
            "file_name": invoice.get("file_name"),
            "file_link": invoice.get("file_link"),
            "ocr_link": invoice.get("ocr_link"),
            "status": invoice.get("status"),
            "workflow_state": invoice.get("workflow_state") or "w_pracy",
            "organization_name": invoice.get("organization_name"),
        }
        invoice_number = str(invoice.get("invoice_number") or "").strip() or f"Faktura #{invoice['id']}"
        return {
            "source_kind": INVOICE_DOCUMENT_INTAKE_KIND,
            "status": self._derive_invoice_document_intake_status(invoice),
            "priority": "normalny",
            "title": f"Przyjety dokument: {invoice_number}",
            "description": (
                f"Dokument zrodla {str(invoice.get('source') or '').upper()} zostal przyjety do obiegu "
                f"i powiazany z faktura #{invoice['id']}."
            ),
            "source_reference": str(invoice.get("source_external_id") or invoice.get("file_name") or invoice["id"]),
            "metadata_json": json.dumps(metadata, ensure_ascii=False, indent=2),
            "linked_invoice_id": int(invoice["id"]),
            "assigned_user_id": invoice.get("assigned_user_id"),
        }

    def _ensure_invoice_document_intake_item(self, invoice: dict[str, Any], actor_user: dict[str, Any] | None) -> None:
        if not self.intake_repository or not invoice.get("organization_id"):
            return
        organization_id = int(invoice["organization_id"])
        existing = self._find_invoice_document_intake_item(int(invoice["id"]), organization_id)
        payload = self._build_invoice_document_intake_payload(invoice)
        payload["organization_id"] = organization_id
        payload["created_by_user_id"] = int(actor_user["user_id"]) if actor_user and actor_user.get("user_id") else None
        payload["last_activity_at"] = now_iso()
        if existing:
            self.intake_repository.update_item(
                int(existing["intake_item_id"]),
                {
                    "status": payload["status"],
                    "priority": payload["priority"],
                    "title": payload["title"],
                    "description": payload["description"],
                    "source_reference": payload["source_reference"],
                    "metadata_json": payload["metadata_json"],
                    "assigned_user_id": payload["assigned_user_id"],
                    "linked_invoice_id": payload["linked_invoice_id"],
                    "last_activity_at": payload["last_activity_at"],
                },
            )
            return
        self.intake_repository.create_item(payload)

    def _build_invoice_exception_specs(self, invoice: dict[str, Any]) -> list[dict[str, Any]]:
        specs: list[dict[str, Any]] = []
        workflow_state = str(invoice.get("workflow_state") or "w_pracy").strip().lower()
        duplicate_type = str(invoice.get("duplicate_type") or "brak").strip().lower()
        flag_reason = str(invoice.get("flag_reason") or "").strip()
        if not invoice.get("contractor_id"):
            specs.append(
                {
                    "code": "missing_contractor",
                    "priority": "wysoki",
                    "title": "Brak kontrahenta",
                    "description": "Faktura nie ma jeszcze przypisanego kontrahenta i wymaga uzupelnienia kartoteki.",
                }
            )
        if "ocr" in flag_reason.lower():
            specs.append(
                {
                    "code": "weak_ocr",
                    "priority": "wysoki",
                    "title": "OCR wymaga uwagi",
                    "description": flag_reason or "OCR nie odczytal wszystkich kluczowych pol dokumentu.",
                }
            )
        if duplicate_type in {"podejrzenie", "pewny"}:
            specs.append(
                {
                    "code": "duplicate_requires_decision",
                    "priority": "wysoki",
                    "title": "Duplikat wymaga decyzji",
                    "description": "Ta faktura jest oznaczona jako duplikat i wymaga decyzji operacyjnej.",
                }
            )
        if (
            self._organization_uses_ksef(invoice.get("organization_id"))
            and str(invoice.get("authoritative_source") or invoice.get("source") or "").strip().upper() != "KSEF"
            and not invoice.get("ksef_number")
            and workflow_state not in {"przekazana", "zamknieta"}
            and (age_in_days(invoice.get("incoming_date")) or 0) >= 1
        ):
            specs.append(
                {
                    "code": "missing_ksef_confirmation",
                    "priority": "normalny",
                    "title": "Brak potwierdzenia z KSeF",
                    "description": "Dla tej faktury nadal nie ma potwierdzenia z KSeF mimo uplywu czasu operacyjnego.",
                }
            )
        return specs

    def _list_invoice_exception_items(
        self,
        invoice_id: int,
        organization_id: int,
    ) -> list[dict[str, Any]]:
        if not self.intake_repository:
            return []
        return self.intake_repository.list_items(
            organization_id=organization_id,
            source_kind=INVOICE_EXCEPTION_INTAKE_KIND,
            linked_invoice_id=invoice_id,
            limit=20,
        )

    def _sync_invoice_exception_items(self, invoice: dict[str, Any], actor_user: dict[str, Any] | None) -> None:
        if not self.intake_repository or not invoice.get("organization_id"):
            return
        organization_id = int(invoice["organization_id"])
        existing_items = self._list_invoice_exception_items(int(invoice["id"]), organization_id)
        existing_by_code = {
            str(item.get("source_reference") or "").strip(): item
            for item in existing_items
            if str(item.get("source_reference") or "").strip()
        }
        active_specs = self._build_invoice_exception_specs(invoice)
        active_codes = {spec["code"] for spec in active_specs}
        timestamp = now_iso()
        creator_user_id = int(actor_user["user_id"]) if actor_user and actor_user.get("user_id") else None

        for spec in active_specs:
            metadata = {
                "invoice_id": int(invoice["id"]),
                "exception_code": spec["code"],
                "invoice_number": invoice.get("invoice_number"),
                "ksef_number": invoice.get("ksef_number"),
                "source": invoice.get("source"),
                "status": invoice.get("status"),
                "workflow_state": invoice.get("workflow_state") or "w_pracy",
            }
            existing = existing_by_code.get(spec["code"])
            update_payload = {
                "status": "w_toku" if existing else "nowe",
                "priority": spec["priority"],
                "title": spec["title"],
                "description": spec["description"],
                "metadata_json": json.dumps(metadata, ensure_ascii=False, indent=2),
                "assigned_user_id": invoice.get("assigned_user_id"),
                "linked_invoice_id": int(invoice["id"]),
                "last_activity_at": timestamp,
            }
            if existing:
                self.intake_repository.update_item(int(existing["intake_item_id"]), update_payload)
                continue
            self.intake_repository.create_item(
                {
                    "organization_id": organization_id,
                    "source_kind": INVOICE_EXCEPTION_INTAKE_KIND,
                    "source_reference": spec["code"],
                    "created_by_user_id": creator_user_id,
                    **update_payload,
                }
            )

        for code, item in existing_by_code.items():
            if code in active_codes:
                continue
            current_status = str(item.get("status") or "").strip().lower()
            if current_status in {"zakonczone", "zarchiwizowane"}:
                continue
            self.intake_repository.update_item(
                int(item["intake_item_id"]),
                {
                    "status": "zakonczone",
                    "last_activity_at": timestamp,
                },
            )

    def _sync_invoice_operational_artifacts(
        self,
        invoice: dict[str, Any],
        actor_user: dict[str, Any] | None = None,
    ) -> None:
        self._ensure_invoice_document_intake_item(invoice, actor_user)
        self._sync_invoice_exception_items(invoice, actor_user)

    def _decorate_intake_item_for_invoice_ops(self, item: dict[str, Any]) -> dict[str, Any]:
        decorated = dict(item)
        invoice_id = decorated.get("linked_invoice_id")
        invoice = None
        if invoice_id not in (None, ""):
            try:
                invoice = self.invoice_repository.get_by_id(int(invoice_id), organization_id=decorated.get("organization_id"))
            except (TypeError, ValueError):
                invoice = None
        decorated["metadata"] = self._parse_json_object(decorated.get("metadata_json"))
        if invoice:
            decorated["linked_invoice"] = {
                "id": int(invoice["id"]),
                "invoice_number": invoice.get("invoice_number"),
                "ksef_number": invoice.get("ksef_number"),
                "issuer_name": invoice.get("issuer_name"),
                "gross_amount": invoice.get("gross_amount"),
                "currency": invoice.get("currency"),
                "status": invoice.get("status"),
                "workflow_state": invoice.get("workflow_state"),
                "file_name": invoice.get("file_name"),
            }
        return decorated

    def document_intake_snapshot(
        self,
        *,
        organization_id: int | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        if not self.intake_repository:
            return {"summary": {"count": 0, "generated_at": now_iso()}, "items": []}
        items = self.intake_repository.list_items(
            organization_id=organization_id,
            source_kind=INVOICE_DOCUMENT_INTAKE_KIND,
            limit=limit,
        )
        decorated = [self._decorate_intake_item_for_invoice_ops(item) for item in items]
        counts_by_status: dict[str, int] = {}
        for item in decorated:
            status = str(item.get("status") or "nowe")
            counts_by_status[status] = counts_by_status.get(status, 0) + 1
        return {
            "summary": {
                "count": len(decorated),
                "counts_by_status": counts_by_status,
                "generated_at": now_iso(),
            },
            "items": decorated,
        }

    def exception_center_snapshot(
        self,
        *,
        organization_id: int | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        if not self.intake_repository:
            return {"summary": {"count": 0, "generated_at": now_iso()}, "items": []}
        items = self.intake_repository.list_items(
            organization_id=organization_id,
            source_kind=INVOICE_EXCEPTION_INTAKE_KIND,
            limit=max(limit * 2, 40),
        )
        active_items = [
            self._decorate_intake_item_for_invoice_ops(item)
            for item in items
            if str(item.get("status") or "").strip().lower() not in {"zakonczone", "zarchiwizowane"}
        ]
        counts_by_code: dict[str, int] = {}
        for item in active_items:
            exception_code = str(item.get("source_reference") or "inne")
            counts_by_code[exception_code] = counts_by_code.get(exception_code, 0) + 1
        return {
            "summary": {
                "count": len(active_items),
                "counts_by_code": counts_by_code,
                "generated_at": now_iso(),
            },
            "items": active_items[:limit],
        }

    def _generate_invoice_handoff_batch_number(self, organization_id: int) -> str:
        if not self.invoice_handoff_repository:
            raise ValueError("Repozytorium paczek przekazania nie jest gotowe.")
        today_prefix = datetime.now().strftime("%Y%m%d")
        batches = self.invoice_handoff_repository.list_batches(organization_id=organization_id, limit=200)
        same_day_count = sum(1 for item in batches if str(item.get("batch_number") or "").startswith(f"PK-{today_prefix}-"))
        return f"PK-{today_prefix}-{same_day_count + 1:03d}"

    def create_handoff_batch(
        self,
        invoice_ids: list[int],
        *,
        handoff_target: str | None,
        note: str | None,
        actor_user: dict[str, Any] | None,
        actor: str,
        organization_id: int | None = None,
    ) -> dict[str, Any]:
        if not self.invoice_handoff_repository:
            raise ValueError("Repozytorium paczek przekazania nie jest gotowe.")
        if not invoice_ids:
            raise ValueError("Wybierz co najmniej jedna fakture do paczki przekazania.")
        normalized_ids: list[int] = []
        seen_ids: set[int] = set()
        for raw_value in invoice_ids:
            try:
                invoice_id = int(raw_value)
            except (TypeError, ValueError):
                continue
            if invoice_id in seen_ids:
                continue
            seen_ids.add(invoice_id)
            normalized_ids.append(invoice_id)
        if not normalized_ids:
            raise ValueError("Nie znaleziono prawidlowych faktur do przekazania.")

        first_invoice = self.invoice_repository.get_by_id(normalized_ids[0], organization_id=organization_id)
        if not first_invoice:
            raise ValueError("Nie znaleziono pierwszej faktury do przekazania.")
        if not self._can_manage_invoice_workflow(actor_user, first_invoice.get("organization_id"), require_decision=True):
            raise PermissionError("Ta rola nie moze tworzyc paczek przekazania.")

        target_organization_id = int(first_invoice["organization_id"])
        batch_id = self.invoice_handoff_repository.create_batch(
            organization_id=target_organization_id,
            batch_number=self._generate_invoice_handoff_batch_number(target_organization_id),
            handoff_target=str(handoff_target or "").strip() or None,
            note=str(note or "").strip() or None,
            created_by_user_id=int(actor_user["user_id"]) if actor_user and actor_user.get("user_id") else None,
        )

        processed_invoices: list[int] = []
        for invoice_id in normalized_ids:
            invoice = self.invoice_repository.get_by_id(invoice_id, organization_id=organization_id)
            if not invoice or int(invoice.get("organization_id") or 0) != target_organization_id:
                continue
            current_state = str(invoice.get("workflow_state") or "w_pracy").strip().lower()
            if current_state == "w_pracy":
                invoice = self.mark_invoice_ready_for_handoff(
                    invoice_id,
                    actor_user=actor_user,
                    actor=actor,
                    organization_id=target_organization_id,
                    handoff_target=handoff_target,
                    handoff_note=note,
                )
                assert invoice is not None
            current_state = str(invoice.get("workflow_state") or "w_pracy").strip().lower()
            if current_state != "przekazana":
                invoice = self.handoff_invoice(
                    invoice_id,
                    actor_user=actor_user,
                    actor=actor,
                    organization_id=target_organization_id,
                    handoff_target=handoff_target,
                    handoff_note=note,
                )
                assert invoice is not None
            self.invoice_handoff_repository.add_batch_item(
                invoice_handoff_batch_id=batch_id,
                invoice_id=invoice_id,
                organization_id=target_organization_id,
                workflow_state_snapshot=invoice.get("workflow_state"),
                status_snapshot=invoice.get("status"),
                source_snapshot=invoice.get("source"),
            )
            processed_invoices.append(invoice_id)

        self.invoice_handoff_repository.update_batch(
            batch_id,
            {
                "invoice_count": len(processed_invoices),
                "status": "przekazana" if processed_invoices else "utworzona",
                "handoff_target": str(handoff_target or "").strip() or None,
                "note": str(note or "").strip() or None,
            },
        )
        batch_detail = self.get_handoff_batch_detail(batch_id, organization_id=target_organization_id)
        self.event_repository.log(
            event_type="invoice_handoff_batch_created",
            invoice_id=processed_invoices[0] if len(processed_invoices) == 1 else None,
            organization_id=target_organization_id,
            source="SYSTEM",
            status_before=None,
            status_after="created",
            decision_reason=f"Utworzono paczke przekazania obejmujaca {len(processed_invoices)} faktur(y).",
            actor=actor,
            details={
                "invoice_handoff_batch_id": batch_id,
                "invoice_ids": processed_invoices,
                "handoff_target": str(handoff_target or "").strip() or None,
                "note": str(note or "").strip() or None,
            },
        )
        assert batch_detail is not None
        return batch_detail

    def list_handoff_batches(
        self,
        *,
        organization_id: int | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        if not self.invoice_handoff_repository:
            return {"summary": {"count": 0, "generated_at": now_iso()}, "batches": []}
        batches = self.invoice_handoff_repository.list_batches(organization_id=organization_id, limit=limit)
        return {
            "summary": {
                "count": len(batches),
                "generated_at": now_iso(),
            },
            "batches": batches,
        }

    def get_handoff_batch_detail(
        self,
        batch_id: int,
        *,
        organization_id: int | None = None,
    ) -> dict[str, Any] | None:
        if not self.invoice_handoff_repository:
            return None
        batch = self.invoice_handoff_repository.get_batch_detail(batch_id, organization_id=organization_id)
        if not batch:
            return None
        items = self.invoice_handoff_repository.list_batch_items(batch_id, organization_id=organization_id)
        return {
            "batch": batch,
            "items": items,
        }

    def export_handoff_batch_csv(
        self,
        batch_id: int,
        *,
        actor_user: dict[str, Any] | None,
        actor: str,
        organization_id: int | None = None,
    ) -> dict[str, Any]:
        if not self.invoice_handoff_repository:
            raise ValueError("Repozytorium paczek przekazania nie jest gotowe.")
        detail = self.get_handoff_batch_detail(batch_id, organization_id=organization_id)
        if not detail:
            raise ValueError("Nie znaleziono paczki przekazania.")
        batch = detail["batch"]
        if not self._can_manage_invoice_workflow(actor_user, batch.get("organization_id"), require_decision=True):
            raise PermissionError("Ta rola nie moze eksportowac paczek przekazania.")
        output = io.StringIO()
        writer = csv.writer(output, delimiter=";")
        writer.writerow(
            [
                "BatchNumber",
                "InvoiceId",
                "InvoiceNumber",
                "KSeFNumber",
                "IssuerName",
                "IssuerNIP",
                "IssueDate",
                "GrossAmount",
                "Currency",
                "Status",
                "WorkflowState",
                "AssignedUser",
            ]
        )
        for item in detail["items"]:
            writer.writerow(
                [
                    batch.get("batch_number"),
                    item.get("invoice_id"),
                    item.get("invoice_number"),
                    item.get("ksef_number"),
                    item.get("issuer_name"),
                    item.get("issuer_nip"),
                    item.get("issue_date"),
                    item.get("gross_amount"),
                    item.get("currency"),
                    item.get("current_status"),
                    item.get("current_workflow_state"),
                    item.get("assigned_user_name"),
                ]
            )
        csv_content = output.getvalue()
        file_name = f"{batch.get('batch_number') or f'paczka-{batch_id}'}.csv"
        self.invoice_handoff_repository.mark_exported(
            batch_id,
            exported_by_user_id=int(actor_user["user_id"]) if actor_user and actor_user.get("user_id") else None,
            export_format="csv",
            export_metadata={
                "row_count": len(detail["items"]),
                "file_name": file_name,
            },
        )
        self.event_repository.log(
            event_type="invoice_handoff_batch_exported",
            invoice_id=None,
            organization_id=batch.get("organization_id"),
            source="SYSTEM",
            status_before=batch.get("status"),
            status_after="wyeksportowana",
            decision_reason=f"Wyeksportowano paczke przekazania {batch.get('batch_number')}.",
            actor=actor,
            details={
                "invoice_handoff_batch_id": batch_id,
                "file_name": file_name,
                "row_count": len(detail["items"]),
            },
        )
        refreshed = self.get_handoff_batch_detail(batch_id, organization_id=organization_id)
        return {
            "batch": refreshed["batch"] if refreshed else batch,
            "file_name": file_name,
            "csv_content": csv_content,
        }

    def get_invoice_detail(
        self,
        invoice_id: int,
        organization_id: int | None = None,
        viewer_user: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        invoice = self.invoice_repository.get_by_id(invoice_id, organization_id=organization_id)
        if not invoice:
            return None

        relations = self.invoice_repository.list_relations(invoice_id)
        history = self._sanitize_invoice_history_events(
            self.event_repository.list_by_invoice(invoice_id, organization_id=invoice.get("organization_id"))
        )
        similar = self.duplicate_detector.similar_invoices(invoice, exclude_invoice_id=invoice_id)
        authoritative_source = self._effective_authoritative_source(invoice)
        ksef_overrides = self.invoice_ksef_override_repository.list_for_invoice(
            invoice_id,
            organization_id=invoice.get("organization_id"),
        )
        approval_requests = (
            self.approval_repository.list_for_entity("invoice", invoice_id, organization_id=invoice.get("organization_id"))
            if self.approval_repository
            else []
        )
        approval_requests = [
            self._decorate_invoice_approval_request(request, invoice=invoice, viewer_user=viewer_user)
            for request in approval_requests
        ]

        contractor = None
        contractor_known_before = False
        if invoice.get("contractor_id"):
            contractor = self.contractor_repository.get_by_id(
                int(invoice["contractor_id"]),
                organization_id=invoice.get("organization_id"),
            )
            all_for_contractor = self.invoice_repository.list_invoices(
                {"contractor_id": invoice["contractor_id"], "sort_by": "issue_date", "sort_order": "asc"},
                organization_id=invoice.get("organization_id"),
            )
            contractor_known_before = any(
                item["id"] != invoice_id
                and (
                    (item.get("incoming_date") or "") < (invoice.get("incoming_date") or "")
                    or (
                        (item.get("incoming_date") or "") == (invoice.get("incoming_date") or "")
                        and item["id"] < invoice_id
                    )
                )
                for item in all_for_contractor
            )

        viewer_user_id = int(viewer_user["user_id"]) if viewer_user and viewer_user.get("user_id") else None
        linked_tasks = self.task_repository.list_linked_tasks(
            "invoice",
            invoice_id,
            organization_id=invoice.get("organization_id"),
            viewer_user_id=viewer_user_id,
            include_completed=False,
            limit=8,
        )

        return {
            "invoice": invoice,
            "relations": relations,
            "similar_invoices": similar,
            "duplicate_center": self._build_duplicate_center(invoice, relations, similar),
            "comments": self.invoice_repository.list_comments(invoice_id),
            "history": history,
            "approval_requests": approval_requests,
            "contractor": contractor,
            "contractor_known_before": contractor_known_before,
            "linked_tasks": linked_tasks,
            "document_intake_items": [
                self._decorate_intake_item_for_invoice_ops(item)
                for item in self._find_invoice_related_document_items(invoice_id, invoice.get("organization_id"))
            ],
            "exceptions": [
                self._decorate_intake_item_for_invoice_ops(item)
                for item in self._list_invoice_exception_items(invoice_id, int(invoice.get("organization_id") or 0))
            ],
            "handoff_batches": (
                self.invoice_handoff_repository.list_batches_for_invoice(
                    invoice_id,
                    organization_id=invoice.get("organization_id"),
                    limit=12,
                )
                if self.invoice_handoff_repository
                else []
            ),
            "source_trace": self._build_source_trace(invoice),
            "document_trace": self._build_document_trace(invoice),
            "ksef_protected": authoritative_source.upper() == "KSEF",
            "ksef_corrections": self._build_ksef_correction_payload(invoice, ksef_overrides),
            "field_provenance": self._build_field_provenance(invoice, ksef_overrides, contractor),
            "workflow": self._build_invoice_workflow_payload(invoice, viewer_user=viewer_user, history=history),
        }

    def get_invoice_preview(
        self,
        invoice_id: int,
        *,
        organization_id: int | None = None,
        viewer_user: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        invoice = self.invoice_repository.get_by_id(invoice_id, organization_id=organization_id)
        if not invoice:
            return None

        contractor = None
        if invoice.get("contractor_id"):
            contractor = self.contractor_repository.get_by_id(
                int(invoice["contractor_id"]),
                organization_id=invoice.get("organization_id"),
            )
        ksef_overrides = self.invoice_ksef_override_repository.list_for_invoice(
            invoice_id,
            organization_id=invoice.get("organization_id"),
        )
        document_trace = self._build_document_trace(invoice)
        preview_kind = self._resolve_invoice_preview_kind(invoice, document_trace)
        ocr_text = str(invoice.get("ocr_raw_text") or "").strip()

        return {
            "invoice": {
                "id": invoice.get("id"),
                "organization_id": invoice.get("organization_id"),
                "organization_name": invoice.get("organization_name"),
                "invoice_number": invoice.get("invoice_number"),
                "ksef_number": invoice.get("ksef_number"),
                "issuer_name": invoice.get("issuer_name"),
                "issuer_nip": invoice.get("issuer_nip"),
                "issue_date": invoice.get("issue_date"),
                "incoming_date": invoice.get("incoming_date"),
                "gross_amount": invoice.get("gross_amount"),
                "currency": invoice.get("currency"),
                "status": invoice.get("status"),
                "duplicate_type": invoice.get("duplicate_type"),
                "source": invoice.get("source"),
                "authoritative_source": self._effective_authoritative_source(invoice),
                "assigned_user_name": invoice.get("assigned_user_name"),
                "contractor_name": invoice.get("contractor_name") or (contractor or {}).get("name"),
                "workflow_state": invoice.get("workflow_state") or "w_pracy",
                "flag_reason": invoice.get("flag_reason"),
            },
            "document_trace": {
                **document_trace,
                "preview_kind": preview_kind,
            },
            "ocr_excerpt": ocr_text[:1200],
            "ocr_excerpt_truncated": len(ocr_text) > 1200,
            "field_provenance": self._build_field_provenance(invoice, ksef_overrides, contractor),
            "workflow": self._build_invoice_workflow_payload(invoice, viewer_user=viewer_user),
        }

    def _invoice_workflow_state_label(self, workflow_state: str | None) -> str:
        labels = {
            "w_pracy": "W pracy",
            "gotowa_do_przekazania": "Gotowa do przekazania",
            "przekazana": "Przekazana",
            "zamknieta": "Zamknieta",
        }
        normalized = str(workflow_state or "w_pracy").strip().lower()
        return labels.get(normalized, normalized or "W pracy")

    def _resolve_invoice_workflow_actor_name(self, user_id: Any) -> str | None:
        try:
            normalized_user_id = int(user_id)
        except (TypeError, ValueError):
            return None
        user = self.user_repository.get_by_id(normalized_user_id)
        if not user:
            return None
        return str(user.get("display_name") or user.get("login") or "").strip() or None

    def _can_manage_invoice_workflow(
        self,
        user: dict[str, Any] | None,
        organization_id: int | None,
        *,
        require_decision: bool = False,
    ) -> bool:
        if not user or organization_id is None:
            return False
        if bool(user.get("is_global_admin")):
            return True
        role = str(user.get("role") or "").strip()
        allowed_roles = INVOICE_DECISION_ROLES if require_decision else WRITE_ROLES
        if role not in allowed_roles:
            return False
        return int(user.get("organization_id") or 0) == int(organization_id)

    def _build_invoice_workflow_payload(
        self,
        invoice: dict[str, Any],
        *,
        viewer_user: dict[str, Any] | None = None,
        history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        state = str(invoice.get("workflow_state") or "w_pracy").strip().lower() or "w_pracy"
        if state not in INVOICE_WORKFLOW_STATES:
            state = INVOICE_WORKFLOW_STATES[0]
        organization_id = invoice.get("organization_id")
        undo = self._resolve_invoice_workflow_undo(invoice, viewer_user=viewer_user, history=history)
        return {
            "state": state,
            "state_label": self._invoice_workflow_state_label(state),
            "ready_for_handoff_at": invoice.get("ready_for_handoff_at"),
            "ready_for_handoff_by_user_id": invoice.get("ready_for_handoff_by_user_id"),
            "ready_for_handoff_by_user_name": self._resolve_invoice_workflow_actor_name(
                invoice.get("ready_for_handoff_by_user_id")
            ),
            "handoff_target": invoice.get("handoff_target"),
            "handoff_note": invoice.get("handoff_note"),
            "handed_off_at": invoice.get("handed_off_at"),
            "handed_off_by_user_id": invoice.get("handed_off_by_user_id"),
            "handed_off_by_user_name": self._resolve_invoice_workflow_actor_name(invoice.get("handed_off_by_user_id")),
            "closed_at": invoice.get("closed_at"),
            "closed_by_user_id": invoice.get("closed_by_user_id"),
            "closed_by_user_name": self._resolve_invoice_workflow_actor_name(invoice.get("closed_by_user_id")),
            "closed_reason": invoice.get("closed_reason"),
            "reopened_at": invoice.get("reopened_at"),
            "reopened_by_user_id": invoice.get("reopened_by_user_id"),
            "reopened_by_user_name": self._resolve_invoice_workflow_actor_name(invoice.get("reopened_by_user_id")),
            "reopen_reason": invoice.get("reopen_reason"),
            "can_mark_ready": self._can_manage_invoice_workflow(viewer_user, organization_id),
            "can_handoff": self._can_manage_invoice_workflow(viewer_user, organization_id, require_decision=True),
            "can_close": self._can_manage_invoice_workflow(viewer_user, organization_id, require_decision=True),
            "can_reopen": self._can_manage_invoice_workflow(viewer_user, organization_id, require_decision=True),
            "undo": undo,
        }

    def _resolve_invoice_preview_kind(
        self,
        invoice: dict[str, Any],
        document_trace: dict[str, Any] | None = None,
    ) -> str:
        file_name = str(
            (document_trace or {}).get("file_name")
            or invoice.get("file_name")
            or ""
        ).strip().lower()
        document_type = str(invoice.get("document_type") or "").strip().lower()
        if file_name.endswith(".pdf") or document_type == "pdf":
            return "pdf"
        if any(file_name.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")):
            return "image"
        if document_type in {"image", "zdjecie", "skan"}:
            return "image"
        if str(invoice.get("ocr_raw_text") or "").strip():
            return "text"
        return "none"

    def _parse_event_details(self, event: dict[str, Any]) -> dict[str, Any]:
        raw = event.get("details")
        if isinstance(raw, dict):
            return raw
        if not raw:
            return {}
        try:
            parsed = json.loads(str(raw))
        except (TypeError, json.JSONDecodeError):
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _sanitize_invoice_history_events(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        sanitized_events: list[dict[str, Any]] = []
        for event in events:
            sanitized = dict(event)
            if sanitized.get("event_type") == "invoice_comment_added":
                details = self._parse_event_details(sanitized)
                note_text = details.pop("note_text", None)
                if note_text is not None and "note_length" not in details:
                    details["note_length"] = len(str(note_text))
                sanitized["details"] = details
            sanitized_events.append(sanitized)
        return sanitized_events

    def _resolve_invoice_workflow_undo(
        self,
        invoice: dict[str, Any],
        *,
        viewer_user: dict[str, Any] | None = None,
        history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        events = history or self.event_repository.list_by_invoice(
            int(invoice["id"]),
            organization_id=invoice.get("organization_id"),
        )
        current_state = str(invoice.get("workflow_state") or "w_pracy").strip().lower() or "w_pracy"
        for event in events:
            event_type = str(event.get("event_type") or "").strip()
            if event_type not in INVOICE_WORKFLOW_UNDO_EVENT_TYPES:
                continue
            details = self._parse_event_details(event)
            before_state = str(details.get("workflow_state_before") or "").strip().lower() or "w_pracy"
            after_state = str(details.get("workflow_state_after") or "").strip().lower() or current_state
            if current_state != after_state:
                continue
            require_decision = event_type != "invoice_ready_for_handoff"
            can_undo = self._can_manage_invoice_workflow(
                viewer_user,
                invoice.get("organization_id"),
                require_decision=require_decision,
            )
            labels = {
                "invoice_ready_for_handoff": "Cofnij przygotowanie do przekazania",
                "invoice_handed_off": "Cofnij przekazanie",
                "invoice_closed": "Cofnij zamkniecie obiegu",
                "invoice_reopened": "Cofnij ponowne otwarcie",
            }
            return {
                "available": bool(can_undo),
                "event_id": event.get("id"),
                "event_type": event_type,
                "action_label": labels.get(event_type, "Cofnij ostatnia decyzje"),
                "target_state": before_state,
                "target_state_label": self._invoice_workflow_state_label(before_state),
                "requires_decision_role": require_decision,
                "can_undo": bool(can_undo),
            }
        return {
            "available": False,
            "event_id": None,
            "event_type": None,
            "action_label": "Cofnij ostatnia decyzje",
            "target_state": None,
            "target_state_label": None,
            "requires_decision_role": False,
            "can_undo": False,
        }

    def mark_invoice_ready_for_handoff(
        self,
        invoice_id: int,
        *,
        actor_user: dict[str, Any] | None,
        actor: str,
        organization_id: int | None = None,
        handoff_target: str | None = None,
        handoff_note: str | None = None,
    ) -> dict[str, Any] | None:
        invoice = self.invoice_repository.get_by_id(invoice_id, organization_id=organization_id)
        if not invoice:
            return None
        if not self._can_manage_invoice_workflow(actor_user, invoice.get("organization_id")):
            raise PermissionError("Ta rola nie moze przygotowac faktury do przekazania.")
        if str(invoice.get("workflow_state") or "w_pracy") == "przekazana":
            raise ValueError("Faktura zostala juz przekazana. Najpierw otworz ja ponownie.")

        update_payload = {
            "workflow_state": "gotowa_do_przekazania",
            "ready_for_handoff_at": now_iso(),
            "ready_for_handoff_by_user_id": int(actor_user["user_id"]) if actor_user and actor_user.get("user_id") else None,
            "handoff_target": str(handoff_target or "").strip() or None,
            "handoff_note": str(handoff_note or "").strip() or None,
        }
        self.invoice_repository.update(invoice_id, update_payload)
        refreshed = self.invoice_repository.get_by_id(invoice_id, organization_id=organization_id)
        assert refreshed is not None
        self.event_repository.log(
            event_type="invoice_ready_for_handoff",
            invoice_id=invoice_id,
            organization_id=invoice.get("organization_id"),
            source=invoice.get("source"),
            status_before=invoice.get("status"),
            status_after=refreshed.get("status"),
            decision_reason="Oznaczono fakture jako gotowa do przekazania dalej.",
            actor=actor,
            details={
                "workflow_state_before": invoice.get("workflow_state") or "w_pracy",
                "workflow_state_after": refreshed.get("workflow_state"),
                "handoff_target": refreshed.get("handoff_target"),
                "handoff_note": refreshed.get("handoff_note"),
            },
        )
        self._sync_invoice_operational_artifacts(refreshed, actor_user)
        return refreshed

    def handoff_invoice(
        self,
        invoice_id: int,
        *,
        actor_user: dict[str, Any] | None,
        actor: str,
        organization_id: int | None = None,
        handoff_target: str | None = None,
        handoff_note: str | None = None,
    ) -> dict[str, Any] | None:
        invoice = self.invoice_repository.get_by_id(invoice_id, organization_id=organization_id)
        if not invoice:
            return None
        if not self._can_manage_invoice_workflow(actor_user, invoice.get("organization_id"), require_decision=True):
            raise PermissionError("Ta rola nie moze przekazac faktury dalej.")
        if str(invoice.get("workflow_state") or "w_pracy") == "przekazana":
            raise ValueError("Ta faktura jest juz przekazana.")

        normalized_target = str(handoff_target or "").strip() or str(invoice.get("handoff_target") or "").strip() or None
        normalized_note = str(handoff_note or "").strip() or str(invoice.get("handoff_note") or "").strip() or None
        actor_user_id = int(actor_user["user_id"]) if actor_user and actor_user.get("user_id") else None
        update_payload = {
            "workflow_state": "przekazana",
            "handoff_target": normalized_target,
            "handoff_note": normalized_note,
            "handed_off_at": now_iso(),
            "handed_off_by_user_id": actor_user_id,
        }
        if not invoice.get("ready_for_handoff_at"):
            update_payload["ready_for_handoff_at"] = now_iso()
        if not invoice.get("ready_for_handoff_by_user_id"):
            update_payload["ready_for_handoff_by_user_id"] = actor_user_id
        self.invoice_repository.update(invoice_id, update_payload)
        refreshed = self.invoice_repository.get_by_id(invoice_id, organization_id=organization_id)
        assert refreshed is not None
        self.event_repository.log(
            event_type="invoice_handed_off",
            invoice_id=invoice_id,
            organization_id=invoice.get("organization_id"),
            source=invoice.get("source"),
            status_before=invoice.get("status"),
            status_after=refreshed.get("status"),
            decision_reason="Przekazano fakture dalej w procesie operacyjnym.",
            actor=actor,
            details={
                "workflow_state_before": invoice.get("workflow_state") or "w_pracy",
                "workflow_state_after": refreshed.get("workflow_state"),
                "handoff_target": refreshed.get("handoff_target"),
                "handoff_note": refreshed.get("handoff_note"),
            },
        )
        self._sync_invoice_operational_artifacts(refreshed, actor_user)
        return refreshed

    def close_invoice(
        self,
        invoice_id: int,
        *,
        actor_user: dict[str, Any] | None,
        actor: str,
        organization_id: int | None = None,
        reason: str | None = None,
    ) -> dict[str, Any] | None:
        invoice = self.invoice_repository.get_by_id(invoice_id, organization_id=organization_id)
        if not invoice:
            return None
        if not self._can_manage_invoice_workflow(actor_user, invoice.get("organization_id"), require_decision=True):
            raise PermissionError("Ta rola nie moze zamknac faktury.")
        current_state = str(invoice.get("workflow_state") or "w_pracy").strip().lower()
        if current_state == "zamknieta":
            raise ValueError("Ta faktura jest juz zamknieta.")
        if current_state == "w_pracy":
            raise ValueError("Nie mozna zamknac faktury, ktora nie zostala jeszcze przygotowana do przekazania.")

        normalized_reason = str(reason or "").strip() or "Zamknieto obieg faktury."
        self.invoice_repository.update(
            invoice_id,
            {
                "workflow_state": "zamknieta",
                "closed_at": now_iso(),
                "closed_by_user_id": int(actor_user["user_id"]) if actor_user and actor_user.get("user_id") else None,
                "closed_reason": normalized_reason,
            },
        )
        refreshed = self.invoice_repository.get_by_id(invoice_id, organization_id=organization_id)
        assert refreshed is not None
        self.event_repository.log(
            event_type="invoice_closed",
            invoice_id=invoice_id,
            organization_id=invoice.get("organization_id"),
            source=invoice.get("source"),
            status_before=invoice.get("status"),
            status_after=refreshed.get("status"),
            decision_reason=f"Zamknieto fakture: {normalized_reason}",
            actor=actor,
            details={
                "workflow_state_before": invoice.get("workflow_state") or "w_pracy",
                "workflow_state_after": refreshed.get("workflow_state"),
                "closed_reason": normalized_reason,
            },
        )
        self._sync_invoice_operational_artifacts(refreshed, actor_user)
        return refreshed

    def reopen_invoice(
        self,
        invoice_id: int,
        *,
        actor_user: dict[str, Any] | None,
        actor: str,
        organization_id: int | None = None,
        reason: str | None = None,
    ) -> dict[str, Any] | None:
        invoice = self.invoice_repository.get_by_id(invoice_id, organization_id=organization_id)
        if not invoice:
            return None
        if not self._can_manage_invoice_workflow(actor_user, invoice.get("organization_id"), require_decision=True):
            raise PermissionError("Ta rola nie moze ponownie otworzyc faktury.")
        if str(invoice.get("workflow_state") or "w_pracy") == "w_pracy":
            raise ValueError("Ta faktura jest juz w pracy.")

        normalized_reason = str(reason or "").strip()
        if not normalized_reason:
            raise ValueError("Podaj powod ponownego otwarcia faktury.")

        self.invoice_repository.update(
            invoice_id,
            {
                "workflow_state": "w_pracy",
                "reopened_at": now_iso(),
                "reopened_by_user_id": int(actor_user["user_id"]) if actor_user and actor_user.get("user_id") else None,
                "reopen_reason": normalized_reason,
            },
        )
        refreshed = self.invoice_repository.get_by_id(invoice_id, organization_id=organization_id)
        assert refreshed is not None
        self.event_repository.log(
            event_type="invoice_reopened",
            invoice_id=invoice_id,
            organization_id=invoice.get("organization_id"),
            source=invoice.get("source"),
            status_before=invoice.get("status"),
            status_after=refreshed.get("status"),
            decision_reason=f"Ponownie otwarto fakture: {normalized_reason}",
            actor=actor,
            details={
                "workflow_state_before": invoice.get("workflow_state") or "w_pracy",
                "workflow_state_after": refreshed.get("workflow_state"),
                "reopen_reason": normalized_reason,
            },
        )
        self._sync_invoice_operational_artifacts(refreshed, actor_user)
        return refreshed

    def undo_last_invoice_workflow_decision(
        self,
        invoice_id: int,
        *,
        actor_user: dict[str, Any] | None,
        actor: str,
        organization_id: int | None = None,
    ) -> dict[str, Any] | None:
        invoice = self.invoice_repository.get_by_id(invoice_id, organization_id=organization_id)
        if not invoice:
            return None
        history = self.event_repository.list_by_invoice(invoice_id, organization_id=invoice.get("organization_id"))
        undo = self._resolve_invoice_workflow_undo(invoice, viewer_user=actor_user, history=history)
        if not undo.get("event_type"):
            raise ValueError("Nie ma zadnej decyzji obiegu, ktora mozna teraz cofnac.")
        if not undo.get("can_undo"):
            raise PermissionError("Ta rola nie moze cofnac ostatniej decyzji obiegu.")

        reverted_event_type = str(undo.get("event_type") or "")
        event = next(
            (
                item
                for item in history
                if int(item.get("id") or 0) == int(undo.get("event_id") or 0)
            ),
            None,
        )
        details = self._parse_event_details(event or {})
        before_state = str(details.get("workflow_state_before") or "w_pracy").strip().lower() or "w_pracy"
        update_payload: dict[str, Any] = {"workflow_state": before_state}

        if reverted_event_type == "invoice_ready_for_handoff":
            update_payload.update(
                {
                    "ready_for_handoff_at": None,
                    "ready_for_handoff_by_user_id": None,
                    "handoff_target": None,
                    "handoff_note": None,
                }
            )
        elif reverted_event_type == "invoice_handed_off":
            update_payload.update(
                {
                    "handed_off_at": None,
                    "handed_off_by_user_id": None,
                }
            )
            if before_state != "gotowa_do_przekazania":
                update_payload.update(
                    {
                        "ready_for_handoff_at": None,
                        "ready_for_handoff_by_user_id": None,
                        "handoff_target": None,
                        "handoff_note": None,
                    }
                )
        elif reverted_event_type == "invoice_closed":
            update_payload.update(
                {
                    "closed_at": None,
                    "closed_by_user_id": None,
                    "closed_reason": None,
                }
            )
        elif reverted_event_type == "invoice_reopened":
            update_payload.update(
                {
                    "reopened_at": None,
                    "reopened_by_user_id": None,
                    "reopen_reason": None,
                }
            )
        else:
            raise ValueError("Nie obslugujemy cofania tego typu decyzji obiegu.")

        self.invoice_repository.update(invoice_id, update_payload)
        refreshed = self.invoice_repository.get_by_id(invoice_id, organization_id=organization_id)
        assert refreshed is not None
        self.event_repository.log(
            event_type="invoice_workflow_undone",
            invoice_id=invoice_id,
            organization_id=invoice.get("organization_id"),
            source=invoice.get("source"),
            status_before=invoice.get("status"),
            status_after=refreshed.get("status"),
            decision_reason=f"Cofnieto decyzje obiegu: {undo.get('action_label')}.",
            actor=actor,
            details={
                "reverted_event_id": undo.get("event_id"),
                "reverted_event_type": reverted_event_type,
                "workflow_state_before": invoice.get("workflow_state") or "w_pracy",
                "workflow_state_after": refreshed.get("workflow_state"),
            },
        )
        self._sync_invoice_operational_artifacts(refreshed, actor_user)
        return refreshed

    def list_assignable_invoice_users(
        self,
        organization_id: int | None = None,
    ) -> list[dict[str, Any]]:
        users = self.user_repository.list_users(organization_id=organization_id)
        return [
            {
                "user_id": int(user["user_id"]),
                "login": user.get("login"),
                "display_name": user.get("display_name") or user.get("login"),
                "role": user.get("role"),
                "organization_id": user.get("organization_id"),
                "organization_name": user.get("organization_name"),
            }
            for user in users
            if int(user.get("is_active") or 0) == 1
        ]

    def add_invoice_comment(
        self,
        invoice_id: int,
        note_text: str,
        *,
        actor_user: dict[str, Any] | None,
        actor: str,
        organization_id: int | None = None,
        parent_comment_id: int | None = None,
    ) -> dict[str, Any]:
        invoice = self.invoice_repository.get_by_id(invoice_id, organization_id=organization_id)
        if not invoice:
            raise ValueError("Nie znaleziono faktury.")

        normalized_text = str(note_text or "").strip()
        if not normalized_text:
            raise ValueError("Komentarz do faktury nie moze byc pusty.")
        if not actor_user or not actor_user.get("user_id"):
            raise ValueError("Nie mozna dodac komentarza bez zalogowanego uzytkownika.")

        created_comment_id = self.invoice_repository.add_comment(
            {
                "invoice_id": invoice_id,
                "organization_id": invoice.get("organization_id"),
                "parent_comment_id": int(parent_comment_id) if parent_comment_id not in (None, "") else None,
                "note_text": normalized_text,
                "created_by_user_id": int(actor_user["user_id"]),
            }
        )
        self.event_repository.log(
            event_type="invoice_comment_added",
            invoice_id=invoice_id,
            organization_id=invoice.get("organization_id"),
            source=invoice.get("source"),
            status_before=invoice.get("status"),
            status_after=invoice.get("status"),
            decision_reason="Dodano komentarz do faktury.",
            actor=actor,
            details={
                "invoice_comment_id": created_comment_id,
                "note_length": len(normalized_text),
            },
        )
        comments = self.invoice_repository.list_comments(invoice_id)
        return next(
            (item for item in comments if int(item.get("invoice_comment_id") or 0) == int(created_comment_id)),
            {
                "invoice_comment_id": created_comment_id,
                "invoice_id": invoice_id,
                "organization_id": invoice.get("organization_id"),
                "parent_comment_id": int(parent_comment_id) if parent_comment_id not in (None, "") else None,
                "note_text": normalized_text,
                "created_by_user_id": int(actor_user["user_id"]),
            },
        )

    def get_contractor_detail(
        self,
        contractor_id: int,
        organization_id: int | None = None,
        viewer_user: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        contractor = self.contractor_repository.get_by_id(contractor_id, organization_id=organization_id)
        if not contractor:
            return None
        invoices = self.invoice_repository.list_invoices(
            {"contractor_id": contractor_id},
            organization_id=contractor.get("organization_id"),
        )
        viewer_user_id = int(viewer_user["user_id"]) if viewer_user and viewer_user.get("user_id") else None
        linked_tasks = self.task_repository.list_linked_tasks(
            "contractor",
            contractor_id,
            organization_id=contractor.get("organization_id"),
            viewer_user_id=viewer_user_id,
            include_completed=False,
            limit=8,
        )
        notes = self.contractor_repository.list_notes(
            contractor_id,
            organization_id=contractor.get("organization_id"),
        )
        return {"contractor": contractor, "invoices": invoices, "linked_tasks": linked_tasks, "notes": notes}

    def add_contractor_note(
        self,
        contractor_id: int,
        note_text: str,
        *,
        actor_user: dict[str, Any] | None,
        organization_id: int | None = None,
    ) -> dict[str, Any]:
        contractor = self.contractor_repository.get_by_id(contractor_id, organization_id=organization_id)
        if not contractor:
            raise ValueError("Nie znaleziono kontrahenta.")

        normalized_text = str(note_text or "").strip()
        if not normalized_text:
            raise ValueError("Notatka kontrahenta nie moze byc pusta.")
        if len(normalized_text) > 2000:
            raise ValueError("Notatka kontrahenta moze miec maksymalnie 2000 znakow.")
        if not actor_user or not actor_user.get("user_id"):
            raise ValueError("Nie mozna dodac notatki bez zalogowanego uzytkownika.")

        created_note_id = self.contractor_repository.add_note(
            {
                "organization_id": contractor.get("organization_id"),
                "contractor_id": contractor_id,
                "author_user_id": int(actor_user["user_id"]),
                "note_text": normalized_text,
            }
        )
        notes = self.contractor_repository.list_notes(
            contractor_id,
            organization_id=contractor.get("organization_id"),
        )
        return next(
            (item for item in notes if int(item.get("contractor_note_id") or 0) == int(created_note_id)),
            {
                "contractor_note_id": created_note_id,
                "organization_id": contractor.get("organization_id"),
                "contractor_id": contractor_id,
                "author_user_id": int(actor_user["user_id"]),
                "note_text": normalized_text,
            },
        )

    def global_search(self, query_text: str, organization_id: int | None = None) -> dict[str, Any]:
        if not query_text.strip():
            return {"invoices": [], "contractors": []}
        return self.invoice_repository.search_global(query_text, organization_id=organization_id)

    def create_invoice(
        self,
        payload: dict[str, Any],
        actor: str = "system",
        organization_id: int | None = None,
    ) -> dict[str, Any]:
        base_payload = dict(payload)
        organization = self._resolve_organization(base_payload.get("organization_id") or organization_id)
        base_payload["organization_id"] = int(organization["organization_id"])
        base_payload["organization_name"] = organization["name"]
        base_payload["organization_slug"] = organization["slug"]
        base_payload.setdefault("status", "nowa")
        base_payload.setdefault("duplicate_type", "brak")
        base_payload.setdefault("authoritative_source", base_payload.get("source"))
        base_payload.setdefault("currency", "PLN")
        base_payload.setdefault("incoming_date", now_iso()[:10])
        base_payload.setdefault("document_type", self._infer_document_type(base_payload))

        authoritative_invoice = self._apply_ksef_authority_to_existing_invoice(base_payload, actor)
        if authoritative_invoice is not None:
            return authoritative_invoice

        ocr_verification_reason = self._build_ocr_verification_reason(base_payload)
        if ocr_verification_reason:
            base_payload["status"] = "weryfikacja"
            base_payload["flag_reason"] = ocr_verification_reason

        if isinstance(base_payload.get("source_metadata"), dict):
            base_payload["source_metadata"] = json.dumps(base_payload["source_metadata"], ensure_ascii=False, indent=2)
        if str(base_payload.get("authoritative_source") or base_payload.get("source") or "").upper() == "KSEF":
            base_payload["source_metadata"] = self._serialize_source_metadata(
                self._seed_authoritative_ksef_metadata(base_payload)
            )

        contractor_id, contractor_created = self._ensure_contractor(base_payload, int(organization["organization_id"]))
        base_payload["contractor_id"] = contractor_id
        base_payload["invoice_hash"] = self._build_invoice_hash(base_payload)

        file_link = self._ensure_document_artifact(base_payload)
        if file_link:
            base_payload["file_link"] = file_link.public_link
            base_payload["file_storage_key"] = file_link.storage_key
            base_payload["storage_backend"] = file_link.storage_backend

        if not base_payload.get("ocr_link") and base_payload.get("ocr_raw_text"):
            ocr_artifact = self._store_ocr_artifact(base_payload)
            base_payload["ocr_link"] = ocr_artifact.public_link
            base_payload["ocr_storage_key"] = ocr_artifact.storage_key
            base_payload.setdefault("storage_backend", ocr_artifact.storage_backend)

        try:
            invoice_id = self.invoice_repository.create(base_payload)
        except Exception as error:
            if self._is_duplicate_invoice_hash_error(error):
                raise ValueError(
                    "Nie można dodać dokumentu, ponieważ identyczna faktura została już wcześniej zapisana."
                ) from error
            raise
        created_invoice = self.invoice_repository.get_by_id(invoice_id)
        assert created_invoice is not None
        linked_user = self._resolve_linked_system_user(created_invoice)
        creation_actor = self._resolve_creation_actor(actor, linked_user)

        self.event_repository.log(
            event_type="invoice_created",
            invoice_id=invoice_id,
            organization_id=created_invoice.get("organization_id"),
            source=created_invoice["source"],
            status_before=None,
            status_after=created_invoice["status"],
            decision_reason=self._invoice_creation_reason(created_invoice, linked_user),
            actor=creation_actor,
            details={
                "file_name": created_invoice["file_name"],
                "document_type": created_invoice.get("document_type"),
                "source_external_id": created_invoice.get("source_external_id"),
                "source_sender_name": created_invoice.get("source_sender_name"),
                "source_sender_id": created_invoice.get("source_sender_id"),
                "linked_user_login": linked_user.get("login") if linked_user else None,
                "file_link": created_invoice.get("file_link"),
                "ocr_link": created_invoice.get("ocr_link"),
            },
        )

        if contractor_created:
            self.event_repository.log(
                event_type="contractor_created",
                invoice_id=invoice_id,
                organization_id=created_invoice.get("organization_id"),
                source=created_invoice["source"],
                status_before=None,
                status_after=created_invoice["status"],
                decision_reason="Utworzono nowego kontrahenta na podstawie faktury.",
                actor=creation_actor,
                details={
                    "contractor_id": contractor_id,
                    "nip": created_invoice["issuer_nip"],
                    "name": created_invoice["issuer_name"],
                },
            )

        self.contractor_repository.refresh_invoice_stats(contractor_id)
        self._apply_duplicate_flags(invoice_id, actor=actor)
        final_invoice = self.invoice_repository.get_by_id(invoice_id)
        assert final_invoice is not None
        self._sync_invoice_operational_artifacts(final_invoice)
        return final_invoice

    def update_invoice(
        self,
        invoice_id: int,
        changes: dict[str, Any],
        actor: str = "uzytkownik",
        organization_id: int | None = None,
        actor_user: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        current = self.invoice_repository.get_by_id(invoice_id, organization_id=organization_id)
        if not current:
            return None
        previous_status = current["status"]
        previous_contractor_id = current.get("contractor_id")
        contractor_created = False
        authoritative_source = self._effective_authoritative_source(current)

        cleaned_changes = {
            key: value
            for key, value in changes.items()
            if key
            not in {
                "id",
                "created_at",
                "updated_at",
                "organization_name",
                "organization_slug",
                "contractor_name",
                "contractor_nip",
                "contractor_email",
                "contractor_phone",
                "contractor_is_new",
                "contractor_notes",
                "authoritative_source",
            }
        }
        protected_ksef_changes: dict[str, Any] = {}
        if authoritative_source.upper() == "KSEF":
            for field_name in KSEF_AUTHORITATIVE_FIELDS:
                if field_name not in cleaned_changes:
                    continue
                normalized_new_value = self._normalize_ksef_field_value(field_name, cleaned_changes.get(field_name))
                normalized_current_value = self._normalize_ksef_field_value(field_name, current.get(field_name))
                if normalized_new_value == normalized_current_value:
                    cleaned_changes[field_name] = current.get(field_name)
                    continue
                protected_ksef_changes[field_name] = normalized_new_value
                cleaned_changes.pop(field_name, None)
        if "source_metadata" in cleaned_changes and isinstance(cleaned_changes["source_metadata"], dict):
            cleaned_changes["source_metadata"] = json.dumps(cleaned_changes["source_metadata"], ensure_ascii=False, indent=2)
        if "gross_amount" in cleaned_changes and cleaned_changes["gross_amount"] not in ("", None):
            cleaned_changes["gross_amount"] = float(cleaned_changes["gross_amount"])
        if "assigned_user_id" in cleaned_changes and cleaned_changes["assigned_user_id"] in ("", None):
            cleaned_changes["assigned_user_id"] = None
        if "assigned_user_id" in cleaned_changes and cleaned_changes["assigned_user_id"] not in (None, ""):
            cleaned_changes["assigned_user_id"] = self._validate_invoice_assignee(
                cleaned_changes["assigned_user_id"],
                int(current["organization_id"]),
            )
        if "contractor_id" in cleaned_changes and cleaned_changes["contractor_id"] in ("", None):
            cleaned_changes["contractor_id"] = None
        if "contractor_id" in cleaned_changes and cleaned_changes["contractor_id"] not in ("", None):
            contractor_id = int(cleaned_changes["contractor_id"])
            contractor = self.contractor_repository.get_by_id(contractor_id, organization_id=int(current["organization_id"]))
            if not contractor:
                raise ValueError("Nie można przypisać kontrahenta z innej organizacji.")
            cleaned_changes["contractor_id"] = contractor_id

        if "organization_id" in cleaned_changes:
            cleaned_changes.pop("organization_id")

        previous_assigned_user_id = current.get("assigned_user_id")
        if "contractor_id" not in cleaned_changes and {"issuer_nip", "issuer_name"} & set(cleaned_changes):
            projection = dict(current)
            projection.update(cleaned_changes)
            contractor_id, contractor_created = self._ensure_contractor(projection, int(current["organization_id"]))
            cleaned_changes["contractor_id"] = contractor_id

        self.invoice_repository.update(invoice_id, cleaned_changes)

        refreshed = self.invoice_repository.get_by_id(invoice_id)
        assert refreshed is not None
        invoice_hash_updates = self._build_invoice_hash_update_payload(refreshed, cleaned_changes)
        if invoice_hash_updates:
            self.invoice_repository.update(invoice_id, invoice_hash_updates)
            refreshed = self.invoice_repository.get_by_id(invoice_id)
            assert refreshed is not None
        self._apply_duplicate_flags(invoice_id, actor=actor, preserve_manual_status=True)
        refreshed = self.invoice_repository.get_by_id(invoice_id)
        assert refreshed is not None

        self.event_repository.log(
            event_type="invoice_updated",
            invoice_id=invoice_id,
            organization_id=refreshed.get("organization_id"),
            source=refreshed["source"],
            status_before=previous_status,
            status_after=refreshed["status"],
            decision_reason="Ręczna aktualizacja danych faktury.",
            actor=actor,
            details=cleaned_changes,
        )

        if "assigned_user_id" in cleaned_changes:
            previous_assignee_name = self._actor_from_user_id(previous_assigned_user_id)
            current_assignee_name = self._actor_from_user_id(refreshed.get("assigned_user_id"))
            if previous_assigned_user_id in (None, "") and refreshed.get("assigned_user_id") not in (None, ""):
                event_type = "invoice_assigned"
                reason = "Przypisano odpowiedzialnego za fakture."
            elif previous_assigned_user_id not in (None, "") and refreshed.get("assigned_user_id") in (None, ""):
                event_type = "invoice_unassigned"
                reason = "Usunieto odpowiedzialnego za fakture."
            elif str(previous_assigned_user_id or "") != str(refreshed.get("assigned_user_id") or ""):
                event_type = "invoice_reassigned"
                reason = "Zmieniono odpowiedzialnego za fakture."
            else:
                event_type = None
                reason = None
            if event_type and reason:
                self.event_repository.log(
                    event_type=event_type,
                    invoice_id=invoice_id,
                    organization_id=refreshed.get("organization_id"),
                    source=refreshed["source"],
                    status_before=previous_status,
                    status_after=refreshed["status"],
                    decision_reason=reason,
                    actor=actor,
                    details={
                        "assigned_user_id_before": previous_assigned_user_id,
                        "assigned_user_name_before": previous_assignee_name,
                        "assigned_user_id_after": refreshed.get("assigned_user_id"),
                        "assigned_user_name_after": current_assignee_name,
                    },
                )

        if contractor_created:
            self.event_repository.log(
                event_type="contractor_created",
                invoice_id=invoice_id,
                organization_id=refreshed.get("organization_id"),
                source=refreshed["source"],
                status_before=previous_status,
                status_after=refreshed["status"],
                decision_reason="Utworzono nowego kontrahenta podczas ręcznej edycji faktury.",
                actor=actor,
                details={
                    "contractor_id": refreshed["contractor_id"],
                    "nip": refreshed["issuer_nip"],
                    "name": refreshed["issuer_name"],
                },
            )

        if previous_contractor_id:
            self.contractor_repository.refresh_invoice_stats(int(previous_contractor_id))
        if refreshed.get("contractor_id"):
            self.contractor_repository.refresh_invoice_stats(int(refreshed["contractor_id"]))

        ksef_correction_result = None
        if protected_ksef_changes:
            if self._can_user_approve_ksef_corrections(actor_user, refreshed.get("organization_id")):
                refreshed, ksef_correction_result = self._apply_immediate_ksef_local_corrections(
                    invoice=refreshed,
                    changes=protected_ksef_changes,
                    actor_user=actor_user,
                    actor=actor,
                )
            else:
                ksef_correction_result = self._create_ksef_correction_request(
                    invoice=refreshed,
                    changes=protected_ksef_changes,
                    actor_user=actor_user,
                    actor=actor,
                )
                refreshed = self.invoice_repository.get_by_id(invoice_id)
                assert refreshed is not None

        self._sync_invoice_operational_artifacts(refreshed, actor_user)

        return {
            "invoice": refreshed,
            "ksef_correction": ksef_correction_result,
        }

    def apply_ksef_correction_decision(
        self,
        approval_request: dict[str, Any],
        *,
        decision: str,
        actor_user: dict[str, Any],
        actor: str,
        reason: str | None = None,
    ) -> None:
        metadata = approval_request.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}
        if str(metadata.get("request_kind") or "") != KSEF_CORRECTION_REQUEST_KIND:
            raise ValueError("To nie jest wniosek o korekte danych KSeF.")

        invoice_id = int(approval_request["entity_id"])
        invoice = self.invoice_repository.get_by_id(invoice_id, organization_id=int(approval_request["organization_id"]))
        if not invoice:
            raise ValueError("Nie znaleziono faktury powiazanej z wnioskiem.")

        overrides = self.invoice_ksef_override_repository.list_for_approval_request(
            int(approval_request["approval_request_id"]),
            organization_id=int(approval_request["organization_id"]),
        )
        if not overrides:
            raise ValueError("Ten wniosek nie ma zapisanych zmian do akceptacji.")

        normalized_decision = str(decision or "").strip().lower()
        timestamp = now_iso()
        if normalized_decision == "approve":
            updates: dict[str, Any] = {}
            for override in overrides:
                self.invoice_ksef_override_repository.update(
                    int(override["invoice_ksef_field_override_id"]),
                    {
                        "status": "approved",
                        "approved_by_user_id": int(actor_user["user_id"]),
                        "decision_reason": reason,
                        "approved_at": timestamp,
                    },
                )
                updates[str(override["field_name"])] = override.get("local_value")

            if updates:
                self._apply_local_ksef_values(
                    invoice_id=invoice_id,
                    current_invoice=invoice,
                    field_updates=updates,
                )
            self.event_repository.log(
                event_type="ksef_correction_applied",
                invoice_id=invoice_id,
                organization_id=invoice.get("organization_id"),
                source=invoice.get("source"),
                status_before=invoice.get("status"),
                status_after=invoice.get("status"),
                decision_reason=reason or "Zatwierdzono lokalna korekte danych KSeF.",
                actor=actor,
                details={
                    "approval_request_id": approval_request["approval_request_id"],
                    "field_names": sorted(updates.keys()),
                },
            )
            return

        if normalized_decision == "reject":
            for override in overrides:
                self.invoice_ksef_override_repository.update(
                    int(override["invoice_ksef_field_override_id"]),
                    {
                        "status": "rejected",
                        "rejected_by_user_id": int(actor_user["user_id"]),
                        "decision_reason": reason,
                        "rejected_at": timestamp,
                    },
                )
            self.event_repository.log(
                event_type="ksef_correction_rejected",
                invoice_id=invoice_id,
                organization_id=invoice.get("organization_id"),
                source=invoice.get("source"),
                status_before=invoice.get("status"),
                status_after=invoice.get("status"),
                decision_reason=reason or "Odrzucono lokalna korekte danych KSeF.",
                actor=actor,
                details={
                    "approval_request_id": approval_request["approval_request_id"],
                    "field_names": sorted(str(item["field_name"]) for item in overrides),
                },
            )
            return

        raise ValueError("Nieznana decyzja dla korekty danych KSeF.")

    def _create_ksef_correction_request(
        self,
        *,
        invoice: dict[str, Any],
        changes: dict[str, Any],
        actor_user: dict[str, Any] | None,
        actor: str,
    ) -> dict[str, Any]:
        if not self.approval_repository:
            raise ValueError("System nie ma jeszcze wlaczonego workflow akceptacji dla korekt KSeF.")

        actor_user_id = int(actor_user["user_id"]) if actor_user and actor_user.get("user_id") is not None else None
        approver_user_id = self._resolve_ksef_delegate_or_admin(invoice.get("organization_id"))
        field_labels = [self._ksef_field_label(field_name) for field_name in changes]
        title = "Prosba o korekte danych KSeF"
        description = (
            "Po zapisie wykryto zmiane w polach potwierdzonych z KSeF. "
            "Oryginalne dane z KSeF zostaly zachowane, a ponizej zapisano prosbe o lokalna korekte: "
            + ", ".join(field_labels)
            + "."
        )
        metadata = {
            "request_kind": KSEF_CORRECTION_REQUEST_KIND,
            "field_changes": [
                {
                    "field_name": field_name,
                    "field_label": self._ksef_field_label(field_name),
                    "source_value": self._current_ksef_source_value(invoice, field_name),
                    "local_value": value,
                }
                for field_name, value in changes.items()
            ],
        }
        request_id = self.approval_repository.create(
            {
                "organization_id": int(invoice["organization_id"]),
                "entity_type": "invoice",
                "entity_id": int(invoice["id"]),
                "title": title,
                "description": description,
                "status": "pending",
                "requested_by_user_id": actor_user_id,
                "requested_user_id": approver_user_id,
                "approve_status": invoice.get("status"),
                "reject_status": invoice.get("status"),
                "metadata_json": json.dumps(metadata, ensure_ascii=False, indent=2),
                "requested_at": now_iso(),
            }
        )
        for field_name, value in changes.items():
            self.invoice_ksef_override_repository.create(
                {
                    "organization_id": int(invoice["organization_id"]),
                    "invoice_id": int(invoice["id"]),
                    "approval_request_id": request_id,
                    "field_name": field_name,
                    "source_value": self._current_ksef_source_value(invoice, field_name),
                    "local_value": self._stringify_ksef_override_value(field_name, value),
                    "status": "pending",
                    "requested_by_user_id": actor_user_id,
                    "request_reason": f"Propozycja lokalnej korekty pola {self._ksef_field_label(field_name)}.",
                }
            )

        self.event_repository.log(
            event_type="ksef_correction_requested",
            invoice_id=int(invoice["id"]),
            organization_id=invoice.get("organization_id"),
            source=invoice.get("source"),
            status_before=invoice.get("status"),
            status_after=invoice.get("status"),
            decision_reason="Utworzono prosbe o lokalna korekte danych KSeF.",
            actor=actor,
            details={
                "approval_request_id": request_id,
                "field_names": sorted(changes.keys()),
                "requested_user_id": approver_user_id,
            },
        )
        request = self.approval_repository.get_by_id(request_id, organization_id=int(invoice["organization_id"]))
        assert request is not None
        return {
            "mode": "request_created",
            "request_id": request_id,
            "title": title,
            "message": "Zapisano zmiany edytowalne i wyslano prosbe o korekte pol potwierdzonych z KSeF.",
            "field_changes": metadata["field_changes"],
            "requested_user_id": approver_user_id,
            "request": request,
        }

    def _apply_immediate_ksef_local_corrections(
        self,
        *,
        invoice: dict[str, Any],
        changes: dict[str, Any],
        actor_user: dict[str, Any] | None,
        actor: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        actor_user_id = int(actor_user["user_id"]) if actor_user and actor_user.get("user_id") is not None else None
        approved_changes: list[dict[str, Any]] = []
        for field_name, value in changes.items():
            source_value = self._current_ksef_source_value(invoice, field_name)
            self.invoice_ksef_override_repository.create(
                {
                    "organization_id": int(invoice["organization_id"]),
                    "invoice_id": int(invoice["id"]),
                    "field_name": field_name,
                    "source_value": source_value,
                    "local_value": self._stringify_ksef_override_value(field_name, value),
                    "status": "approved",
                    "requested_by_user_id": actor_user_id,
                    "approved_by_user_id": actor_user_id,
                    "request_reason": f"Bezposrednia lokalna korekta pola {self._ksef_field_label(field_name)}.",
                    "decision_reason": "Zmiana zatwierdzona bezposrednio przez osobe z uprawnieniem do korekt KSeF.",
                    "approved_at": now_iso(),
                }
            )
            approved_changes.append(
                {
                    "field_name": field_name,
                    "field_label": self._ksef_field_label(field_name),
                    "source_value": source_value,
                    "local_value": value,
                }
            )

        self._apply_local_ksef_values(
            invoice_id=int(invoice["id"]),
            current_invoice=invoice,
            field_updates=changes,
        )
        refreshed = self.invoice_repository.get_by_id(int(invoice["id"]))
        assert refreshed is not None
        self.event_repository.log(
            event_type="ksef_correction_applied",
            invoice_id=int(invoice["id"]),
            organization_id=invoice.get("organization_id"),
            source=invoice.get("source"),
            status_before=invoice.get("status"),
            status_after=refreshed.get("status"),
            decision_reason="Zastosowano lokalna korekte danych potwierdzonych z KSeF.",
            actor=actor,
            details={
                "field_names": sorted(changes.keys()),
                "approved_directly": True,
            },
        )
        return refreshed, {
            "mode": "applied_directly",
            "title": "Zastosowano lokalna korekte",
            "message": "Zapisano zmiany i od razu zastosowano lokalna korekte pol potwierdzonych z KSeF.",
            "field_changes": approved_changes,
        }

    def _apply_local_ksef_values(
        self,
        *,
        invoice_id: int,
        current_invoice: dict[str, Any],
        field_updates: dict[str, Any],
    ) -> None:
        normalized_updates = {
            field_name: self._prepare_invoice_field_value(field_name, value)
            for field_name, value in field_updates.items()
        }
        metadata = self._deserialize_source_metadata(current_invoice.get("source_metadata"))
        local_overrides = metadata.get("local_ksef_overrides")
        if not isinstance(local_overrides, dict):
            local_overrides = {}
        local_overrides.update(
            {
                field_name: self._stringify_ksef_override_value(field_name, value)
                for field_name, value in normalized_updates.items()
            }
        )
        metadata["local_ksef_overrides"] = local_overrides
        update_payload = dict(normalized_updates)
        update_payload["source_metadata"] = self._serialize_source_metadata(metadata)
        projection = dict(current_invoice)
        projection.update(update_payload)
        update_payload["invoice_hash"] = self._build_invoice_hash(projection)
        self.invoice_repository.update(invoice_id, update_payload)

    def _build_ksef_correction_payload(
        self,
        invoice: dict[str, Any],
        overrides: list[dict[str, Any]],
    ) -> dict[str, Any]:
        authoritative_values = self._get_authoritative_ksef_values(invoice)
        pending = [self._serialize_ksef_override(item) for item in overrides if str(item.get("status") or "") == "pending"]
        approved = [self._serialize_ksef_override(item) for item in overrides if str(item.get("status") or "") == "approved"]
        rejected = [self._serialize_ksef_override(item) for item in overrides if str(item.get("status") or "") == "rejected"]
        active_local_values = {
            field_name: invoice.get(field_name)
            for field_name in KSEF_AUTHORITATIVE_FIELDS
            if self._normalize_ksef_field_value(field_name, invoice.get(field_name))
            != self._normalize_ksef_field_value(field_name, authoritative_values.get(field_name))
        }
        return {
            "authoritative_values": authoritative_values,
            "active_local_values": active_local_values,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
        }

    def _serialize_ksef_override(self, override: dict[str, Any]) -> dict[str, Any]:
        result = dict(override)
        result["field_label"] = self._ksef_field_label(str(override.get("field_name") or ""))
        return result

    def _decorate_invoice_approval_request(
        self,
        request: dict[str, Any],
        *,
        invoice: dict[str, Any],
        viewer_user: dict[str, Any] | None,
    ) -> dict[str, Any]:
        result = dict(request)
        metadata_raw = result.get("metadata_json")
        if isinstance(metadata_raw, str) and metadata_raw.strip():
            try:
                metadata = json.loads(metadata_raw)
            except json.JSONDecodeError:
                metadata = {"raw": metadata_raw}
        else:
            metadata = {}
        result["metadata"] = metadata if isinstance(metadata, dict) else {}
        result["can_decide"] = self._can_user_decide_approval_request(
            request=result,
            invoice=invoice,
            viewer_user=viewer_user,
        )
        return result

    def _can_user_decide_approval_request(
        self,
        *,
        request: dict[str, Any],
        invoice: dict[str, Any],
        viewer_user: dict[str, Any] | None,
    ) -> bool:
        if not viewer_user or str(request.get("status") or "") != "pending":
            return False
        metadata = request.get("metadata")
        if isinstance(metadata, dict) and str(metadata.get("request_kind") or "") == KSEF_CORRECTION_REQUEST_KIND:
            return self._can_user_approve_ksef_corrections(viewer_user, invoice.get("organization_id"))
        return bool(viewer_user.get("role")) and int(viewer_user.get("organization_id") or 0) == int(
            request.get("organization_id") or 0
        )

    def _can_user_approve_ksef_corrections(
        self,
        user: dict[str, Any] | None,
        organization_id: int | None,
    ) -> bool:
        if not user or organization_id is None:
            return False
        if user.get("is_global_admin"):
            return True
        if str(user.get("role") or "") == ORGANIZATION_ADMIN_ROLE and int(user.get("organization_id") or 0) == int(organization_id):
            return True
        organization = self.organization_repository.get_by_id(int(organization_id))
        if not organization:
            return False
        delegate_user_id = organization.get("ksef_correction_delegate_user_id")
        if not delegate_user_id or int(delegate_user_id) != int(user.get("user_id") or 0):
            return False
        expires_at = str(organization.get("ksef_correction_delegate_expires_at") or "").strip()
        if not expires_at:
            return False
        try:
            expires_dt = datetime.strptime(expires_at, "%Y-%m-%dT%H:%M")
        except ValueError:
            return False
        return expires_dt >= datetime.now()

    def _resolve_ksef_delegate_or_admin(self, organization_id: int | None) -> int | None:
        if organization_id is None:
            return None
        organization = self.organization_repository.get_by_id(int(organization_id))
        if not organization:
            return None
        delegate_user_id = organization.get("ksef_correction_delegate_user_id")
        expires_at = str(organization.get("ksef_correction_delegate_expires_at") or "").strip()
        if delegate_user_id and expires_at:
            try:
                expires_dt = datetime.strptime(expires_at, "%Y-%m-%dT%H:%M")
            except ValueError:
                expires_dt = None
            if expires_dt and expires_dt >= datetime.now():
                delegate_user = self.user_repository.get_by_id(int(delegate_user_id))
                if delegate_user and int(delegate_user.get("is_active") or 0):
                    return int(delegate_user_id)
        users = self.user_repository.list_users(organization_id=int(organization_id))
        for user in users:
            if str(user.get("role") or "") == ORGANIZATION_ADMIN_ROLE and int(user.get("is_active") or 0):
                return int(user["user_id"])
        return None

    def _get_authoritative_ksef_values(self, invoice: dict[str, Any]) -> dict[str, Any]:
        metadata = self._deserialize_source_metadata(invoice.get("source_metadata"))
        authoritative_fields = metadata.get("authoritative_fields")
        if not isinstance(authoritative_fields, dict):
            authoritative_fields = {}
        return {
            field_name: authoritative_fields.get(field_name, invoice.get(field_name))
            for field_name in KSEF_AUTHORITATIVE_FIELDS
        }

    def _current_ksef_source_value(self, invoice: dict[str, Any], field_name: str) -> Any:
        return self._get_authoritative_ksef_values(invoice).get(field_name)

    def _normalize_ksef_field_value(self, field_name: str, value: Any) -> str:
        if field_name == "gross_amount":
            try:
                return f"{float(value):.2f}" if value not in ("", None) else ""
            except (TypeError, ValueError):
                return str(value or "").strip()
        return str(value or "").strip()

    def _stringify_ksef_override_value(self, field_name: str, value: Any) -> str:
        if field_name == "gross_amount":
            normalized = self._prepare_invoice_field_value(field_name, value)
            return "" if normalized in (None, "") else f"{float(normalized):.2f}"
        return str(value or "").strip()

    def _prepare_invoice_field_value(self, field_name: str, value: Any) -> Any:
        if field_name == "gross_amount":
            if value in ("", None):
                return None
            return float(value)
        normalized = str(value or "").strip()
        return normalized or None

    def _build_invoice_hash_update_payload(self, invoice: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
        hash_fields = {"organization_id", "source", "file_name", "invoice_number", "ksef_number", "issuer_nip", "issue_date", "gross_amount"}
        if not hash_fields & set(changes):
            return {}
        return {"invoice_hash": self._build_invoice_hash(invoice)}

    def _ksef_field_label(self, field_name: str) -> str:
        labels = {
            "invoice_number": "Numer faktury",
            "ksef_number": "Numer KSeF",
            "issuer_nip": "NIP wystawcy",
            "issuer_name": "Nazwa wystawcy",
            "issue_date": "Data wystawienia",
            "sale_date": "Data sprzedazy",
            "gross_amount": "Kwota brutto",
            "currency": "Waluta",
        }
        return labels.get(field_name, field_name)

    def mark_for_verification(
        self,
        invoice_id: int,
        actor: str = "uzytkownik",
        organization_id: int | None = None,
    ) -> dict[str, Any] | None:
        invoice = self.invoice_repository.get_by_id(invoice_id, organization_id=organization_id)
        if not invoice:
            return None
        previous_status = invoice["status"]
        reason = "Faktura została skierowana do weryfikacji ręcznie."
        self.invoice_repository.update(
            invoice_id,
            {
                "status": "weryfikacja",
                "flag_reason": reason,
            },
        )
        self.event_repository.log(
            event_type="invoice_status_changed",
            invoice_id=invoice_id,
            organization_id=invoice.get("organization_id"),
            source=invoice["source"],
            status_before=previous_status,
            status_after="weryfikacja",
            decision_reason=reason,
            actor=actor,
            details={"manual_verification": True},
        )
        return self.invoice_repository.get_by_id(invoice_id)

    def confirm_duplicate(
        self,
        invoice_id: int,
        actor: str = "uzytkownik",
        organization_id: int | None = None,
    ) -> dict[str, Any] | None:
        invoice = self.invoice_repository.get_by_id(invoice_id, organization_id=organization_id)
        if not invoice:
            return None
        previous_status = invoice["status"]
        reason = "Duplikat został potwierdzony ręcznie."
        self.invoice_repository.update(
            invoice_id,
            {
                "status": "pewny_duplikat",
                "duplicate_type": "pewny",
                "flag_reason": reason,
            },
        )
        self.event_repository.log(
            event_type="duplicate_confirmed",
            invoice_id=invoice_id,
            organization_id=invoice.get("organization_id"),
            source=invoice["source"],
            status_before=previous_status,
            status_after="pewny_duplikat",
            decision_reason=reason,
            actor=actor,
            details={"manual_confirmation": True},
        )
        return self.invoice_repository.get_by_id(invoice_id)

    def mark_correct(
        self,
        invoice_id: int,
        actor: str = "uzytkownik",
        organization_id: int | None = None,
        *,
        event_type: str = "invoice_marked_correct",
    ) -> dict[str, Any] | None:
        invoice = self.invoice_repository.get_by_id(invoice_id, organization_id=organization_id)
        if not invoice:
            return None
        previous_status = invoice["status"]
        reason = "Faktura została oznaczona jako poprawna ręcznie."
        self.invoice_repository.delete_relations(invoice_id)
        self.invoice_repository.update(
            invoice_id,
            {
                "status": "poprawna",
                "duplicate_type": "brak",
                "flag_reason": reason,
            },
        )
        self.event_repository.log(
            event_type=event_type,
            invoice_id=invoice_id,
            organization_id=invoice.get("organization_id"),
            source=invoice["source"],
            status_before=previous_status,
            status_after="poprawna",
            decision_reason=reason,
            actor=actor,
            details={"manual_rejection": True},
        )
        return self.invoice_repository.get_by_id(invoice_id)

    def reject_duplicate(
        self,
        invoice_id: int,
        actor: str = "uzytkownik",
        organization_id: int | None = None,
    ) -> dict[str, Any] | None:
        return self.mark_correct(
            invoice_id,
            actor=actor,
            organization_id=organization_id,
            event_type="duplicate_rejected",
        )

    def apply_batch_action(
        self,
        invoice_ids: list[int],
        action: str,
        actor: str = "uzytkownik",
        organization_id: int | None = None,
    ) -> dict[str, Any]:
        normalized_ids = sorted({int(invoice_id) for invoice_id in invoice_ids if int(invoice_id) > 0})
        if not normalized_ids:
            raise ValueError("Nie wybrano żadnej faktury do masowej akcji.")

        handlers = {
            "mark-verification": self.mark_for_verification,
            "confirm-duplicate": self.confirm_duplicate,
            "mark-correct": self.mark_correct,
        }
        handler = handlers.get(action)
        if handler is None:
            raise ValueError("Nieznana masowa akcja dla faktur.")

        processed_ids: list[int] = []
        skipped_ids: list[int] = []
        for invoice_id in normalized_ids:
            result = handler(invoice_id, actor=actor, organization_id=organization_id)
            if result:
                processed_ids.append(invoice_id)
            else:
                skipped_ids.append(invoice_id)

        return {
            "action": action,
            "requested_ids": normalized_ids,
            "processed_ids": processed_ids,
            "skipped_ids": skipped_ids,
            "updated_count": len(processed_ids),
        }

    def import_mock(
        self,
        source: str,
        actor: str = "system",
        organization_id: int | None = None,
    ) -> dict[str, Any]:
        normalized = source.upper()
        organization = self._resolve_organization(organization_id) if organization_id is not None else None
        if normalized == "KSEF":
            payload = self.ksef_client.fetch_mock_invoice()
        elif normalized == "EMAIL":
            payload = self.email_adapter.fetch_mock_invoice(organization)
        elif normalized == "TELEGRAM":
            payload = self.telegram_adapter.fetch_mock_invoice()
        elif normalized == "SLACK":
            payload = self.slack_adapter.fetch_mock_invoice()
        else:
            raise ValueError(f"Nieznane źródło importu testowego: {source}")

        invoice = self.create_invoice(payload, actor=actor, organization_id=organization_id)
        linked_user = self._resolve_linked_system_user(invoice)
        import_actor = self._resolve_creation_actor(actor, linked_user)
        self.event_repository.log(
            event_type="mock_import_executed",
            invoice_id=invoice["id"],
            organization_id=invoice.get("organization_id"),
            source=invoice["source"],
            status_before=None,
            status_after=invoice["status"],
            decision_reason=f"Wykonano import testowy ze źródła {invoice['source']}.",
            actor=import_actor,
            details={
                "source": source,
                "linked_user_login": linked_user.get("login") if linked_user else None,
            },
        )
        return invoice

    def import_telegram_update(self, update: dict[str, Any], actor: str = "system") -> dict[str, Any]:
        self.refresh_communication_adapters()
        try:
            payload = self.telegram_adapter.create_invoice_payload_from_update(update)
        except TelegramBotError as error:
            raise ValueError(str(error)) from error

        linked_user = None
        telegram_user_id = str(payload.get("source_sender_id") or "").strip()
        if telegram_user_id:
            linked_user = self.user_repository.get_by_telegram_user_id(telegram_user_id)

        resolved_organization = self._resolve_telegram_organization(payload, linked_user)
        invoice = self.create_invoice(
            payload,
            actor=actor,
            organization_id=int(resolved_organization["organization_id"]),
        )
        return invoice

    def import_slack_event(self, payload: dict[str, Any], actor: str = "system") -> dict[str, Any] | None:
        self.refresh_communication_adapters()
        try:
            invoice_payload = self.slack_adapter.create_invoice_payload_from_event(payload)
        except SlackBotError as error:
            raise ValueError(str(error)) from error

        if not invoice_payload:
            return None

        resolved_organization = self._resolve_slack_organization(invoice_payload)
        return self.create_invoice(
            invoice_payload,
            actor=actor,
            organization_id=int(resolved_organization["organization_id"]),
        )

    def _apply_ksef_authority_to_existing_invoice(self, payload: dict[str, Any], actor: str) -> dict[str, Any] | None:
        if str(payload.get("source") or "").upper() != "KSEF":
            return None

        organization_id = int(payload["organization_id"])
        candidate = self._find_authoritative_merge_candidate(payload, organization_id)
        if not candidate:
            return None

        previous_status = candidate["status"]
        previous_contractor_id = candidate.get("contractor_id")
        previous_authoritative_source = self._effective_authoritative_source(candidate)
        updates = self._build_ksef_authoritative_updates(candidate, payload)

        projection = dict(candidate)
        projection.update(updates)
        contractor_id, contractor_created = self._ensure_contractor(projection, organization_id)
        updates["contractor_id"] = contractor_id

        projection.update({"contractor_id": contractor_id})
        updates["invoice_hash"] = self._build_invoice_hash(projection)

        self.invoice_repository.update(int(candidate["id"]), updates)
        self._apply_duplicate_flags(int(candidate["id"]), actor=actor, preserve_manual_status=True)

        refreshed = self.invoice_repository.get_by_id(int(candidate["id"]))
        assert refreshed is not None

        self.event_repository.log(
            event_type="ksef_authority_applied",
            invoice_id=int(candidate["id"]),
            organization_id=refreshed.get("organization_id"),
            source="KSeF",
            status_before=previous_status,
            status_after=refreshed["status"],
            decision_reason="Dane faktury zostały potwierdzone i nadpisane danymi z KSeF.",
            actor=actor,
            details={
                "previous_authoritative_source": previous_authoritative_source,
                "current_authoritative_source": refreshed.get("authoritative_source"),
                "updated_fields": sorted(updates.keys()),
                "incoming_ksef_number": payload.get("ksef_number"),
                "incoming_source_external_id": payload.get("source_external_id"),
            },
        )

        if contractor_created:
            self.event_repository.log(
                event_type="contractor_created",
                invoice_id=int(candidate["id"]),
                organization_id=refreshed.get("organization_id"),
                source="KSeF",
                status_before=previous_status,
                status_after=refreshed["status"],
                decision_reason="Utworzono nowego kontrahenta podczas potwierdzenia danych z KSeF.",
                actor=actor,
                details={
                    "contractor_id": contractor_id,
                    "nip": refreshed["issuer_nip"],
                    "name": refreshed["issuer_name"],
                },
            )

        if previous_contractor_id:
            self.contractor_repository.refresh_invoice_stats(int(previous_contractor_id))
        self.contractor_repository.refresh_invoice_stats(contractor_id)
        return refreshed

    def _find_authoritative_merge_candidate(
        self,
        payload: dict[str, Any],
        organization_id: int,
    ) -> dict[str, Any] | None:
        ksef_number = str(payload.get("ksef_number") or "").strip()
        invoice_number = str(payload.get("invoice_number") or "").strip()
        issuer_nip = str(payload.get("issuer_nip") or "").strip()

        candidates = self.invoice_repository.find_exact_ksef_duplicates(
            ksef_number,
            organization_id=organization_id,
        )
        if not candidates:
            candidates = self.invoice_repository.find_suspected_duplicates(
                invoice_number,
                issuer_nip,
                organization_id=organization_id,
            )
        if not candidates:
            return None

        ranked = sorted(
            candidates,
            key=lambda invoice: (-self._source_priority(self._effective_authoritative_source(invoice)), int(invoice["id"])),
        )
        return ranked[0]

    def _build_ksef_authoritative_updates(
        self,
        current_invoice: dict[str, Any],
        incoming_payload: dict[str, Any],
    ) -> dict[str, Any]:
        metadata = self._merge_authoritative_source_metadata(current_invoice, incoming_payload)
        updates: dict[str, Any] = {
            "authoritative_source": "KSeF",
            "source_metadata": self._serialize_source_metadata(metadata),
        }
        local_overrides = metadata.get("local_ksef_overrides")
        if not isinstance(local_overrides, dict):
            local_overrides = {}

        for field_name in KSEF_AUTHORITATIVE_FIELDS:
            value = incoming_payload.get(field_name)
            if field_name in local_overrides and local_overrides.get(field_name) not in (None, ""):
                updates[field_name] = self._prepare_invoice_field_value(field_name, local_overrides.get(field_name))
            elif value not in (None, ""):
                updates[field_name] = value

        if incoming_payload.get("source_external_id"):
            updates["source_external_id"] = incoming_payload.get("source_external_id")

        if current_invoice.get("status") == "weryfikacja" and current_invoice.get("duplicate_type") == "brak":
            updates["status"] = "nowa"
            updates["flag_reason"] = None

        return updates

    def _ensure_contractor(self, invoice_payload: dict[str, Any], organization_id: int) -> tuple[int, bool]:
        nip = (invoice_payload.get("issuer_nip") or "").strip()
        name = (invoice_payload.get("issuer_name") or "").strip() or "Nieznany kontrahent"
        if not nip:
            synthetic_nip = f"brak-nip-{self._build_invoice_hash(invoice_payload)[:12]}"
            nip = synthetic_nip
            invoice_payload["issuer_nip"] = synthetic_nip

        existing = self.contractor_repository.get_by_nip(nip, organization_id=organization_id)
        if existing:
            return int(existing["contractor_id"]), False

        contractor_id = self.contractor_repository.create(
            {
                "organization_id": organization_id,
                "name": name,
                "nip": nip,
                "email": None,
                "phone": None,
                "is_new": 1,
                "last_invoice_date": invoice_payload.get("issue_date"),
                "last_invoice_number": invoice_payload.get("invoice_number"),
                "invoice_count": 0,
                "notes": "Kontrahent utworzony automatycznie podczas importu faktury.",
            }
        )
        return contractor_id, True

    def _build_invoice_hash(self, invoice_payload: dict[str, Any]) -> str:
        raw = "|".join(
            str(invoice_payload.get(key) or "")
            for key in (
                "organization_id",
                "source",
                "file_name",
                "invoice_number",
                "ksef_number",
                "issuer_nip",
                "issue_date",
                "gross_amount",
            )
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _ensure_document_artifact(self, invoice_payload: dict[str, Any]):
        document_bytes = invoice_payload.get("document_bytes")
        if isinstance(document_bytes, (bytes, bytearray)):
            relative_path = self._build_document_relative_path(invoice_payload)
            return self.storage_service.save_binary("document", relative_path, bytes(document_bytes))
        return self._store_document_placeholder(invoice_payload)

    def _store_document_placeholder(self, invoice_payload: dict[str, Any]):
        file_name = invoice_payload["file_name"]
        relative_path = self._build_storage_relative_path(invoice_payload, suffix="_dokument.txt")
        contents = (
            "DOKUMENT TESTOWY FAKTURY\n"
            f"Organizacja: {invoice_payload.get('organization_name')}\n"
            f"Źródło: {invoice_payload.get('source')}\n"
            f"Nazwa pliku wejściowego: {file_name}\n"
            f"Typ dokumentu: {invoice_payload.get('document_type')}\n"
            f"Identyfikator źródła: {invoice_payload.get('source_external_id')}\n"
            f"Nadawca źródła: {invoice_payload.get('source_sender_name')}\n"
            f"Id nadawcy: {invoice_payload.get('source_sender_id')}\n"
            f"Numer faktury: {invoice_payload.get('invoice_number')}\n"
            f"Numer KSeF: {invoice_payload.get('ksef_number')}\n"
            f"NIP wystawcy: {invoice_payload.get('issuer_nip')}\n"
            f"Kwota brutto: {invoice_payload.get('gross_amount')} {invoice_payload.get('currency', 'PLN')}\n"
        )
        return self.storage_service.save_text("document", relative_path, contents)

    def _store_ocr_artifact(self, invoice_payload: dict[str, Any]):
        relative_path = self._build_storage_relative_path(invoice_payload, suffix="_ocr.txt")
        return self.storage_service.save_text("ocr", relative_path, str(invoice_payload.get("ocr_raw_text") or ""))

    def _apply_duplicate_flags(self, invoice_id: int, actor: str, preserve_manual_status: bool = False) -> None:
        invoice = self.invoice_repository.get_by_id(invoice_id)
        if not invoice:
            return
        previous_status = invoice["status"]
        self.invoice_repository.delete_relations(invoice_id)

        evaluation = self.duplicate_detector.evaluate(invoice, exclude_invoice_id=invoice_id)
        next_status = evaluation["status"]
        next_flag_reason = evaluation["flag_reason"]
        if preserve_manual_status and invoice["status"] in {"poprawna", "odrzucona", "zaksiegowana"} and evaluation["duplicate_type"] == "brak":
            next_status = invoice["status"]
        elif evaluation["duplicate_type"] == "brak" and invoice["status"] == "weryfikacja" and invoice.get("flag_reason"):
            next_status = "weryfikacja"
            next_flag_reason = invoice["flag_reason"]

        self.invoice_repository.update(
            invoice_id,
            {
                "status": next_status,
                "duplicate_type": evaluation["duplicate_type"],
                "flag_reason": next_flag_reason,
            },
        )

        for relation in evaluation["relations"]:
            self.invoice_repository.add_relation(
                invoice_id=invoice_id,
                related_invoice_id=relation["related_invoice_id"],
                relation_type=relation["relation_type"],
                reason=relation["reason"],
            )

        refreshed = self.invoice_repository.get_by_id(invoice_id)
        assert refreshed is not None

        if evaluation["duplicate_type"] != "brak":
            self.event_repository.log(
                event_type="duplicate_detected",
                invoice_id=invoice_id,
                organization_id=refreshed.get("organization_id"),
                source=refreshed["source"],
                status_before=previous_status,
                status_after=refreshed["status"],
                decision_reason=evaluation["flag_reason"],
                actor=actor,
                details={"relations": evaluation["relations"]},
            )
            self.notification_service.prepare_duplicate_notification(refreshed, evaluation)

    def _build_ocr_verification_reason(self, invoice_payload: dict[str, Any]) -> str | None:
        source = str(invoice_payload.get("source") or "").upper()
        if source not in {"TELEGRAM", "EMAIL", "SLACK"}:
            return None

        raw_text = str(invoice_payload.get("ocr_raw_text") or "").strip()
        invoice_number = str(invoice_payload.get("invoice_number") or "").strip()
        issuer_nip = str(invoice_payload.get("issuer_nip") or "").strip()
        gross_amount = invoice_payload.get("gross_amount")

        missing_core_fields = not invoice_number and not issuer_nip and gross_amount in (None, "", 0, 0.0)
        fallback_ocr_message = raw_text.startswith("Nie udało się odczytać treści dokumentu lokalnym OCR.")

        if fallback_ocr_message or missing_core_fields:
            if source == "EMAIL":
                return "Dokument z e-maila wymaga weryfikacji, ponieważ OCR nie odczytał kluczowych pól faktury."
            if source == "SLACK":
                return "Dokument ze Slacka wymaga weryfikacji, ponieważ OCR nie odczytal kluczowych pol faktury."
            return "Dokument z Telegrama wymaga weryfikacji, ponieważ OCR nie odczytał kluczowych pól faktury."
        return None

    def _build_storage_relative_path(self, invoice_payload: dict[str, Any], suffix: str) -> Path:
        organization_segment = self._slug(invoice_payload.get("organization_slug") or "organizacja")
        source_segment = self._slug(invoice_payload.get("source") or "inne")
        incoming_date = str(invoice_payload.get("incoming_date") or now_iso()[:10]).replace("/", "-")
        file_stem = self._slug(Path(str(invoice_payload.get("file_name") or "plik")).stem)
        hash_fragment = str(invoice_payload.get("invoice_hash") or "")[:12]
        file_name = f"{file_stem}_{hash_fragment}{suffix}" if hash_fragment else f"{file_stem}{suffix}"
        return Path("organizacje") / organization_segment / source_segment / incoming_date / file_name

    def _build_document_relative_path(self, invoice_payload: dict[str, Any]) -> Path:
        organization_segment = self._slug(invoice_payload.get("organization_slug") or "organizacja")
        source_segment = self._slug(invoice_payload.get("source") or "inne")
        incoming_date = str(invoice_payload.get("incoming_date") or now_iso()[:10]).replace("/", "-")
        original_file_name = Path(str(invoice_payload.get("file_name") or "plik.bin"))
        file_stem = self._slug(original_file_name.stem)
        extension = original_file_name.suffix or self._document_extension(invoice_payload.get("document_type"))
        hash_fragment = str(invoice_payload.get("invoice_hash") or "")[:12]
        stored_name = f"{file_stem}_{hash_fragment}{extension}"
        return Path("organizacje") / organization_segment / source_segment / incoming_date / stored_name

    def _slug(self, value: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value or "").strip())
        return cleaned.strip("._") or "plik"

    def _infer_document_type(self, invoice_payload: dict[str, Any]) -> str:
        extension = Path(str(invoice_payload.get("file_name") or "")).suffix.lower()
        mapping = {
            ".pdf": "pdf",
            ".jpg": "zdjecie",
            ".jpeg": "zdjecie",
            ".png": "zdjecie",
            ".tif": "skan",
            ".tiff": "skan",
            ".xml": "xml",
        }
        return mapping.get(extension, "plik")

    def _document_extension(self, document_type: Any) -> str:
        mapping = {
            "pdf": ".pdf",
            "zdjecie": ".jpg",
            "skan": ".tif",
            "xml": ".xml",
        }
        return mapping.get(str(document_type or "").strip().lower(), ".bin")

    def _invoice_creation_reason(self, invoice: dict[str, Any], linked_user: dict[str, Any] | None = None) -> str:
        if linked_user:
            return (
                f"Dodano nową fakturę z Telegrama przypisaną do użytkownika "
                f"{linked_user.get('display_name') or linked_user['login']}."
            )
        if invoice["source"] == "EMAIL" and invoice.get("source_sender_name"):
            return f"Dodano nową fakturę z e-maila od {invoice['source_sender_name']}."
        if invoice["source"] == "SLACK" and invoice.get("source_sender_name"):
            return (
                f"Dodano nowa fakture ze Slacka od {invoice['source_sender_name']} "
                f"({invoice.get('source_sender_id') or 'brak ID'})."
            )
        if invoice["source"] == "TELEGRAM" and invoice.get("source_sender_name"):
            return (
                f"Dodano nową fakturę z Telegrama od użytkownika "
                f"{invoice['source_sender_name']} ({invoice.get('source_sender_id') or 'brak ID'})."
            )
        return "Dodano nową fakturę."

    def _build_source_trace(self, invoice: dict[str, Any]) -> dict[str, Any]:
        metadata_raw = invoice.get("source_metadata")
        metadata = {}
        if metadata_raw:
            try:
                metadata = json.loads(metadata_raw)
            except (TypeError, json.JSONDecodeError):
                metadata = {"wartosc_surowa": metadata_raw}
        linked_user = self._resolve_linked_system_user(invoice)
        return {
            "source": invoice.get("source"),
            "authoritative_source": invoice.get("authoritative_source") or invoice.get("source"),
            "document_type": invoice.get("document_type"),
            "organization_name": invoice.get("organization_name"),
            "organization_slug": invoice.get("organization_slug"),
            "source_external_id": invoice.get("source_external_id"),
            "source_sender_name": invoice.get("source_sender_name"),
            "source_sender_id": invoice.get("source_sender_id"),
            "linked_user": self._sanitize_linked_user(linked_user),
            "metadata": metadata,
        }

    def _build_field_provenance(
        self,
        invoice: dict[str, Any],
        ksef_overrides: list[dict[str, Any]],
        contractor: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        authoritative_source = self._effective_authoritative_source(invoice).upper()
        correction_payload = self._build_ksef_correction_payload(invoice, ksef_overrides)
        authoritative_values = correction_payload.get("authoritative_values") or {}
        active_local_values = correction_payload.get("active_local_values") or {}
        pending_by_field: dict[str, list[dict[str, Any]]] = {}
        approved_by_field: dict[str, list[dict[str, Any]]] = {}

        for item in correction_payload.get("pending") or []:
            pending_by_field.setdefault(str(item.get("field_name") or ""), []).append(item)
        for item in correction_payload.get("approved") or []:
            approved_by_field.setdefault(str(item.get("field_name") or ""), []).append(item)

        field_definitions = (
            ("incoming_date", "Data wplywu", invoice.get("incoming_date"), "document_meta"),
            ("file_name", "Nazwa pliku", invoice.get("file_name"), "document_meta"),
            ("source", "Zrodlo dokumentu", invoice.get("source"), "document_meta"),
            ("invoice_number", "Numer faktury", invoice.get("invoice_number"), "invoice_data"),
            ("ksef_number", "Numer KSeF", invoice.get("ksef_number"), "invoice_data"),
            ("issuer_nip", "NIP wystawcy", invoice.get("issuer_nip"), "invoice_data"),
            ("issuer_name", "Nazwa wystawcy", invoice.get("issuer_name"), "invoice_data"),
            ("issue_date", "Data wystawienia", invoice.get("issue_date"), "invoice_data"),
            ("sale_date", "Data sprzedazy", invoice.get("sale_date"), "invoice_data"),
            ("gross_amount", "Kwota brutto", invoice.get("gross_amount"), "invoice_data"),
            ("currency", "Waluta", invoice.get("currency"), "invoice_data"),
            ("contractor_id", "Powiazany kontrahent", contractor.get("name") if contractor else None, "local_binding"),
            ("notes", "Notatki", invoice.get("notes"), "local_note"),
        )

        result: list[dict[str, Any]] = []
        for field_name, label, current_value, category in field_definitions:
            is_ksef_protected = authoritative_source == "KSEF" and field_name in KSEF_AUTHORITATIVE_FIELDS
            authoritative_value = authoritative_values.get(field_name)
            has_active_override = field_name in active_local_values
            pending_items = pending_by_field.get(field_name, [])
            approved_items = approved_by_field.get(field_name, [])

            if is_ksef_protected and has_active_override:
                source_kind = "approved_local_override"
                source_label = "Lokalna korekta po KSeF"
            elif is_ksef_protected:
                source_kind = "ksef"
                source_label = "Potwierdzone z KSeF"
            elif category == "document_meta":
                source_kind = "document_meta"
                source_label = "Metadane dokumentu"
            elif category == "local_binding":
                source_kind = "local_binding"
                source_label = "Powiazanie lokalne"
            elif category == "local_note":
                source_kind = "local_note"
                source_label = "Notatka lokalna"
            else:
                source_kind = str(invoice.get("source") or "").strip().lower() or "document_source"
                source_label = f"Dokument zrodlowy: {invoice.get('source') or '-'}"

            result.append(
                {
                    "field_name": field_name,
                    "label": label,
                    "current_value": current_value,
                    "source_kind": source_kind,
                    "source_label": source_label,
                    "authoritative_value": authoritative_value,
                    "has_authoritative_value": authoritative_value not in (None, ""),
                    "has_active_local_override": has_active_override,
                    "pending_count": len(pending_items),
                    "pending_local_values": [item.get("local_value") for item in pending_items],
                    "approved_count": len(approved_items),
                    "latest_approved_local_value": approved_items[0].get("local_value") if approved_items else None,
                    "is_ksef_protected": is_ksef_protected,
                }
            )
        return result

    def _build_duplicate_center(
        self,
        invoice: dict[str, Any],
        relations: list[dict[str, Any]],
        similar: list[dict[str, Any]],
    ) -> dict[str, Any]:
        candidate_map: dict[int, dict[str, Any]] = {}
        for relation in relations:
            candidate_id = int(relation.get("related_invoice_id") or 0)
            if not candidate_id:
                continue
            candidate_map[candidate_id] = {
                "invoice_id": candidate_id,
                "invoice_number": relation.get("invoice_number"),
                "ksef_number": relation.get("ksef_number"),
                "issuer_nip": relation.get("issuer_nip"),
                "issue_date": relation.get("issue_date"),
                "gross_amount": relation.get("gross_amount"),
                "status": relation.get("status"),
                "source": relation.get("source"),
                "file_name": relation.get("file_name"),
                "relation_type": relation.get("relation_type"),
                "relation_reason": relation.get("reason"),
            }
        for item in similar:
            candidate_id = int(item.get("id") or 0)
            if not candidate_id:
                continue
            existing = candidate_map.get(candidate_id, {})
            existing.update(
                {
                    "invoice_id": candidate_id,
                    "invoice_number": item.get("invoice_number"),
                    "ksef_number": item.get("ksef_number"),
                    "issuer_nip": item.get("issuer_nip"),
                    "issuer_name": item.get("issuer_name"),
                    "issue_date": item.get("issue_date"),
                    "sale_date": item.get("sale_date"),
                    "gross_amount": item.get("gross_amount"),
                    "currency": item.get("currency"),
                    "status": item.get("status"),
                    "duplicate_type": item.get("duplicate_type"),
                    "source": item.get("source"),
                    "file_name": item.get("file_name"),
                }
            )
            candidate_map[candidate_id] = existing

        compare_fields = (
            ("invoice_number", "Numer faktury"),
            ("ksef_number", "Numer KSeF"),
            ("issuer_nip", "NIP wystawcy"),
            ("issuer_name", "Nazwa wystawcy"),
            ("issue_date", "Data wystawienia"),
            ("sale_date", "Data sprzedazy"),
            ("gross_amount", "Kwota brutto"),
            ("currency", "Waluta"),
        )
        candidates: list[dict[str, Any]] = []
        for candidate in candidate_map.values():
            matching_labels: list[str] = []
            different_fields: list[dict[str, Any]] = []
            for field_name, label in compare_fields:
                invoice_value = self._normalize_duplicate_compare_value(field_name, invoice.get(field_name))
                candidate_value = self._normalize_duplicate_compare_value(field_name, candidate.get(field_name))
                if invoice_value == candidate_value:
                    matching_labels.append(label)
                    continue
                different_fields.append(
                    {
                        "field_name": field_name,
                        "label": label,
                        "current_value": invoice.get(field_name),
                        "candidate_value": candidate.get(field_name),
                    }
                )
            candidates.append(
                {
                    **candidate,
                    "matching_labels": matching_labels,
                    "different_fields": different_fields,
                    "match_strength": len(matching_labels),
                }
            )

        candidates.sort(
            key=lambda item: (
                int(item.get("match_strength") or 0),
                1 if str(item.get("relation_type") or "").strip() else 0,
                int(item.get("invoice_id") or 0),
            ),
            reverse=True,
        )
        return {
            "candidate_count": len(candidates),
            "candidates": candidates,
        }

    def _build_document_trace(self, invoice: dict[str, Any]) -> dict[str, Any]:
        return {
            "file_name": invoice.get("file_name"),
            "file_link": invoice.get("file_link"),
            "file_storage_key": invoice.get("file_storage_key"),
            "ocr_link": invoice.get("ocr_link"),
            "ocr_storage_key": invoice.get("ocr_storage_key"),
            "storage_backend": invoice.get("storage_backend"),
            "invoice_hash": invoice.get("invoice_hash"),
            "ocr_confidence": invoice.get("ocr_confidence"),
        }

    def _build_verification_inbox_section(
        self,
        title: str,
        description: str,
        items: list[dict[str, Any]],
        *,
        limit: int,
        action_key: str,
    ) -> dict[str, Any]:
        prepared_items = [
            {
                "invoice_id": int(item.get("id") or item.get("invoice_id") or 0),
                "invoice_number": item.get("invoice_number"),
                "ksef_number": item.get("ksef_number"),
                "issuer_name": item.get("issuer_name"),
                "issuer_nip": item.get("issuer_nip"),
                "status": item.get("status"),
                "duplicate_type": item.get("duplicate_type"),
                "source": item.get("source"),
                "incoming_date": item.get("incoming_date"),
                "issue_date": item.get("issue_date"),
                "gross_amount": item.get("gross_amount"),
                "currency": item.get("currency"),
                "file_name": item.get("file_name"),
                "flag_reason": item.get("flag_reason"),
                "organization_name": item.get("organization_name"),
                "assigned_user_id": item.get("assigned_user_id"),
                "assigned_user_name": item.get("assigned_user_name"),
                "assigned_user_role": item.get("assigned_user_role"),
                "invoice_comment_count": int(item.get("invoice_comment_count") or 0),
                "pending_override_count": item.get("pending_override_count"),
                "latest_request_at": item.get("latest_request_at"),
            }
            for item in items[:limit]
        ]
        return {
            "title": title,
            "description": description,
            "count": len(items),
            "action_key": action_key,
            "items": prepared_items,
        }

    def _collect_verification_queue_items(
        self,
        *,
        organization_id: int | None,
        ksef_limit: int,
    ) -> dict[str, list[dict[str, Any]]]:
        verification_items = self.invoice_repository.list_invoices(
            {"status": "weryfikacja", "sort_by": "updated_at", "sort_order": "desc"},
            organization_id=organization_id,
        )
        duplicate_items = self.invoice_repository.list_invoices(
            {"duplicate_type": "podejrzenie", "sort_by": "updated_at", "sort_order": "desc"},
            organization_id=organization_id,
        )
        certain_duplicate_items = self.invoice_repository.list_invoices(
            {"duplicate_type": "pewny", "sort_by": "updated_at", "sort_order": "desc"},
            organization_id=organization_id,
        )
        ksef_pending_items = self.invoice_repository.list_pending_ksef_correction_invoices(
            organization_id=organization_id,
            limit=max(1, int(ksef_limit)),
        )

        duplicate_by_id: dict[int, dict[str, Any]] = {}
        for item in [*duplicate_items, *certain_duplicate_items]:
            duplicate_by_id[int(item["id"])] = item
        duplicate_items_ordered = sorted(
            duplicate_by_id.values(),
            key=lambda item: (str(item.get("updated_at") or ""), int(item.get("id") or 0)),
            reverse=True,
        )
        ocr_attention_items = [
            item
            for item in verification_items
            if str(item.get("source") or "").upper() in {"EMAIL", "TELEGRAM", "SLACK"}
            and "ocr" in str(item.get("flag_reason") or "").lower()
        ]
        return {
            "verification": verification_items,
            "duplicates": duplicate_items_ordered,
            "ksef_corrections": ksef_pending_items,
            "ocr_attention": ocr_attention_items,
        }

    def _build_verification_workspace_section(
        self,
        section_key: str,
        title: str,
        description: str,
        items: list[dict[str, Any]],
        *,
        limit: int,
    ) -> dict[str, Any]:
        threshold_days = int(INVOICE_SLA_THRESHOLDS_DAYS.get(section_key, 1))
        prepared_items = [self._build_verification_workspace_item(section_key, item) for item in items[:limit]]
        all_age_days = [self._resolve_verification_item_age_days(section_key, item) for item in items]
        age_days_values = [int(age) for age in all_age_days if age is not None]
        return {
            "key": section_key,
            "title": title,
            "description": description,
            "count": len(items),
            "sla_days": threshold_days,
            "sla_breached_count": sum(1 for age in age_days_values if age >= threshold_days),
            "oldest_age_days": max(age_days_values, default=0),
            "items": prepared_items,
        }

    def _build_verification_workspace_item(
        self,
        section_key: str,
        item: dict[str, Any],
    ) -> dict[str, Any]:
        age_days = self._resolve_verification_item_age_days(section_key, item)
        sla_days = int(INVOICE_SLA_THRESHOLDS_DAYS.get(section_key, 1))
        compare_target_id = self._pick_duplicate_compare_target(item) if section_key == "duplicates" else None
        return {
            "invoice_id": int(item.get("id") or item.get("invoice_id") or 0),
            "invoice_number": item.get("invoice_number"),
            "ksef_number": item.get("ksef_number"),
            "issuer_name": item.get("issuer_name"),
            "issuer_nip": item.get("issuer_nip"),
            "status": item.get("status"),
            "duplicate_type": item.get("duplicate_type"),
            "source": item.get("source"),
            "incoming_date": item.get("incoming_date"),
            "issue_date": item.get("issue_date"),
            "gross_amount": item.get("gross_amount"),
            "currency": item.get("currency"),
            "file_name": item.get("file_name"),
            "flag_reason": item.get("flag_reason"),
            "organization_name": item.get("organization_name"),
            "assigned_user_id": item.get("assigned_user_id"),
            "assigned_user_name": item.get("assigned_user_name"),
            "assigned_user_role": item.get("assigned_user_role"),
            "invoice_comment_count": int(item.get("invoice_comment_count") or 0),
            "pending_override_count": item.get("pending_override_count"),
            "latest_request_at": item.get("latest_request_at"),
            "age_days": age_days,
            "sla_days": sla_days,
            "sla_breached": bool(age_days is not None and age_days >= sla_days),
            "attention_label": self._build_verification_attention_label(section_key, item),
            "compare_target_invoice_id": compare_target_id,
        }

    def _resolve_verification_item_age_days(
        self,
        section_key: str,
        item: dict[str, Any],
    ) -> int | None:
        if section_key == "ksef_corrections":
            return age_in_days(item.get("latest_request_at") or item.get("updated_at") or item.get("incoming_date"))
        return age_in_days(item.get("updated_at") or item.get("incoming_date"))

    def _build_verification_attention_label(
        self,
        section_key: str,
        item: dict[str, Any],
    ) -> str:
        if section_key == "duplicates":
            duplicate_type = str(item.get("duplicate_type") or "").strip()
            if duplicate_type == "pewny":
                return "Pewny duplikat czeka na decyzje"
            return "Podejrzenie duplikatu wymaga porownania"
        if section_key == "ksef_corrections":
            count = int(item.get("pending_override_count") or 0)
            if count:
                return f"{count} korekt KSeF czeka na zatwierdzenie"
            return "Oczekuje zatwierdzenie korekty KSeF"
        if section_key == "ocr_attention":
            return "OCR nie odczytal kluczowych pol"
        return "Faktura wymaga recznej weryfikacji"

    def _pick_duplicate_compare_target(self, invoice: dict[str, Any]) -> int | None:
        invoice_id = int(invoice.get("id") or invoice.get("invoice_id") or 0)
        if not invoice_id:
            return None
        relations = self.invoice_repository.list_relations(invoice_id)
        if relations:
            return int(relations[0].get("related_invoice_id") or 0) or None
        similar = self.duplicate_detector.similar_invoices(invoice, exclude_invoice_id=invoice_id)
        if similar:
            return int(similar[0].get("id") or 0) or None
        return None

    def _build_compare_invoice_header(self, invoice: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": int(invoice.get("id") or 0),
            "organization_name": invoice.get("organization_name"),
            "invoice_number": invoice.get("invoice_number"),
            "ksef_number": invoice.get("ksef_number"),
            "issuer_name": invoice.get("issuer_name"),
            "issuer_nip": invoice.get("issuer_nip"),
            "incoming_date": invoice.get("incoming_date"),
            "issue_date": invoice.get("issue_date"),
            "gross_amount": invoice.get("gross_amount"),
            "currency": invoice.get("currency"),
            "status": invoice.get("status"),
            "duplicate_type": invoice.get("duplicate_type"),
            "source": invoice.get("source"),
            "authoritative_source": invoice.get("authoritative_source") or invoice.get("source"),
        }

    def _normalize_duplicate_compare_value(self, field_name: str, value: Any) -> str:
        if field_name == "gross_amount":
            try:
                return "" if value in (None, "") else f"{float(value):.2f}"
            except (TypeError, ValueError):
                return str(value or "").strip()
        return str(value or "").strip()

    def _resolve_linked_system_user(self, invoice: dict[str, Any]) -> dict[str, Any] | None:
        if invoice.get("source") != "TELEGRAM":
            return None
        telegram_user_id = str(invoice.get("source_sender_id") or "").strip()
        if not telegram_user_id:
            return None
        user = self.user_repository.get_by_telegram_user_id(telegram_user_id)
        if not user:
            return None
        invoice_organization_id = invoice.get("organization_id")
        if user.get("organization_id") in {None, invoice_organization_id}:
            return user
        return None

    def _resolve_creation_actor(self, actor: str, linked_user: dict[str, Any] | None) -> str:
        if actor != "system" or not linked_user:
            return actor
        return linked_user.get("display_name") or linked_user["login"]

    def _resolve_telegram_organization(
        self,
        payload: dict[str, Any],
        linked_user: dict[str, Any] | None,
    ) -> dict[str, Any]:
        incoming_chat_id = self._resolve_incoming_telegram_chat_id(payload)

        if linked_user and linked_user.get("organization_id"):
            organization = self.organization_repository.get_by_id(int(linked_user["organization_id"]))
            if not organization:
                raise ValueError("Nie znaleziono organizacji przypisanej do uzytkownika Telegram.")
            if not organization.get("is_active", 1):
                raise ValueError("Organizacja przypisana do tego uzytkownika Telegram jest nieaktywna.")
            if not self._organization_uses_telegram(organization):
                raise ValueError("Organizacja przypisana do tego uzytkownika ma aktywny inny komunikator niz Telegram.")
            self._validate_telegram_chat_for_organization(organization, incoming_chat_id)
            return organization

        if incoming_chat_id:
            organization = self.organization_repository.get_by_telegram_chat_id(incoming_chat_id)
            if organization:
                if not organization.get("is_active", 1):
                    raise ValueError("Organizacja przypisana do tego kanalu Telegram jest nieaktywna.")
                if not self._organization_uses_telegram(organization):
                    raise ValueError("Organizacja przypisana do tego kanalu ma aktywny inny komunikator niz Telegram.")
                return organization

        raise ValueError(
            "Nie mozna ustalic organizacji dla dokumentu z Telegrama. "
            "Powiaz ID uzytkownika Telegram z kontem albo ustaw ID kanalu Telegram w organizacji."
        )

    def _resolve_incoming_telegram_chat_id(self, payload: dict[str, Any]) -> str:
        source_metadata = payload.get("source_metadata") or {}
        return str(source_metadata.get("chat_id") or "").strip()

    def _resolve_slack_organization(self, payload: dict[str, Any]) -> dict[str, Any]:
        incoming_channel_id = self._resolve_incoming_slack_channel_id(payload)
        if not incoming_channel_id:
            raise ValueError(
                "Nie mozna ustalic organizacji dla dokumentu ze Slacka. "
                "Webhook musi pochodzic z konkretnego kanalu Slack."
            )

        organization = self.organization_repository.get_by_active_slack_channel_id(incoming_channel_id)
        if not organization:
            raise ValueError(
                "Nie mozna ustalic organizacji dla dokumentu ze Slacka. "
                "Ustaw ID kanalu Slack w aktywnej konfiguracji organizacji."
            )
        if not organization.get("is_active", 1):
            raise ValueError("Organizacja przypisana do tego kanalu Slack jest nieaktywna.")
        if not self._organization_uses_slack(organization):
            raise ValueError("Organizacja przypisana do tego kanalu ma aktywny inny komunikator niz Slack.")
        return organization

    def _resolve_incoming_slack_channel_id(self, payload: dict[str, Any]) -> str:
        source_metadata = payload.get("source_metadata") or {}
        return str(
            source_metadata.get("slack_channel_id")
            or source_metadata.get("channel_id")
            or ""
        ).strip()

    def _validate_telegram_chat_for_organization(
        self,
        organization: dict[str, Any],
        incoming_chat_id: str,
    ) -> None:
        if not self._organization_uses_telegram(organization):
            raise ValueError("Ta organizacja nie ma aktywnego komunikatora Telegram.")
        configured_chat_id = str(organization.get("telegram_chat_id") or "").strip()
        if configured_chat_id and incoming_chat_id and configured_chat_id != incoming_chat_id:
            raise ValueError("Wiadomosc z Telegrama przyszla z innego kanalu niz przypisany do tej organizacji.")

    def _organization_uses_telegram(self, organization: dict[str, Any] | None) -> bool:
        if not organization:
            return False
        return str(organization.get("communication_provider") or "telegram").strip().lower() == "telegram"

    def _organization_uses_slack(self, organization: dict[str, Any] | None) -> bool:
        if not organization:
            return False
        return str(organization.get("communication_provider") or "").strip().lower() == "slack"

    def _resolve_telegram_organization_id(self, linked_user: dict[str, Any] | None) -> int:
        if linked_user and linked_user.get("organization_id"):
            return int(linked_user["organization_id"])
        raise ValueError(
            "Nie można ustalić organizacji dla dokumentu z Telegrama. "
            "Powiąż ID użytkownika Telegram z kontem przypisanym do organizacji."
        )

    def _resolve_organization(self, organization_id: Any) -> dict[str, Any]:
        if organization_id not in (None, ""):
            organization = self.organization_repository.get_by_id(int(organization_id))
            if organization:
                if not organization.get("is_active", 1):
                    raise ValueError("Wybrana organizacja jest nieaktywna.")
                return organization
            raise ValueError("Wybrana organizacja nie istnieje.")
        organization = self.organization_repository.ensure_default_organization()
        if not organization.get("is_active", 1):
            raise ValueError("Domyślna organizacja jest nieaktywna.")
        return organization

    def _validate_invoice_assignee(self, user_id: Any, organization_id: int) -> int:
        try:
            normalized_user_id = int(user_id)
        except (TypeError, ValueError):
            raise ValueError("Wybrany odpowiedzialny za fakture jest nieprawidlowy.") from None
        user = self.user_repository.get_by_id(normalized_user_id)
        if not user:
            raise ValueError("Nie znaleziono wybranego odpowiedzialnego za fakture.")
        if int(user.get("is_active") or 0) != 1:
            raise ValueError("Nie mozna przypisac nieaktywnego uzytkownika do faktury.")
        if int(user.get("organization_id") or 0) != int(organization_id):
            raise ValueError("Nie mozna przypisac odpowiedzialnego z innej organizacji.")
        return normalized_user_id

    def _is_duplicate_invoice_hash_error(self, error: Exception) -> bool:
        message = str(error).lower()
        return "invoice_hash" in message and (
            "unique constraint failed" in message
            or "duplicate key value violates unique constraint" in message
            or "unique violation" in message
        )

    def _effective_authoritative_source(self, invoice: dict[str, Any]) -> str:
        return str(invoice.get("authoritative_source") or invoice.get("source") or "").strip()

    def _source_priority(self, source: str) -> int:
        return SOURCE_PRIORITIES.get(str(source or "").upper(), 0)

    def _merge_authoritative_source_metadata(
        self,
        current_invoice: dict[str, Any],
        incoming_payload: dict[str, Any],
    ) -> dict[str, Any]:
        metadata = self._deserialize_source_metadata(current_invoice.get("source_metadata"))
        history = metadata.get("source_history")
        if not isinstance(history, list):
            history = []

        history.append(
            {
                "source": incoming_payload.get("source"),
                "source_external_id": incoming_payload.get("source_external_id"),
                "applied_at": now_iso(),
            }
        )
        metadata["source_history"] = history[-10:]
        metadata["authoritative_source"] = "KSeF"
        metadata["authoritative_reason"] = "Dane z KSeF mają najwyższy priorytet dla faktury."
        metadata["authoritative_updated_at"] = now_iso()
        metadata["authoritative_ksef_number"] = incoming_payload.get("ksef_number")
        authoritative_fields = metadata.get("authoritative_fields")
        if not isinstance(authoritative_fields, dict):
            authoritative_fields = {}
        for field_name in KSEF_AUTHORITATIVE_FIELDS:
            if incoming_payload.get(field_name) not in (None, ""):
                authoritative_fields[field_name] = self._stringify_ksef_override_value(field_name, incoming_payload.get(field_name))
        metadata["authoritative_fields"] = authoritative_fields
        if current_invoice.get("source") and current_invoice.get("source") != "KSeF":
            metadata["original_source"] = current_invoice.get("source")
        return metadata

    def _seed_authoritative_ksef_metadata(self, invoice_payload: dict[str, Any]) -> dict[str, Any]:
        metadata = self._deserialize_source_metadata(invoice_payload.get("source_metadata"))
        authoritative_fields = metadata.get("authoritative_fields")
        if not isinstance(authoritative_fields, dict):
            authoritative_fields = {}
        for field_name in KSEF_AUTHORITATIVE_FIELDS:
            if invoice_payload.get(field_name) not in (None, ""):
                authoritative_fields[field_name] = self._stringify_ksef_override_value(field_name, invoice_payload.get(field_name))
        metadata["authoritative_fields"] = authoritative_fields
        metadata["authoritative_source"] = "KSeF"
        metadata["authoritative_reason"] = "Dane z KSeF mają najwyższy priorytet dla faktury."
        metadata["authoritative_updated_at"] = now_iso()
        metadata["authoritative_ksef_number"] = invoice_payload.get("ksef_number")
        return metadata

    def _deserialize_source_metadata(self, value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return dict(value)
        if not value:
            return {}
        try:
            parsed = json.loads(str(value))
            return parsed if isinstance(parsed, dict) else {"raw_value": value}
        except (TypeError, json.JSONDecodeError):
            return {"raw_value": value}

    def _serialize_source_metadata(self, metadata: dict[str, Any]) -> str:
        return json.dumps(metadata, ensure_ascii=False, indent=2)

    def _sanitize_linked_user(self, user: dict[str, Any] | None) -> dict[str, Any] | None:
        if not user:
            return None
        return {
            "user_id": user["user_id"],
            "login": user["login"],
            "display_name": user.get("display_name") or user["login"],
            "telegram_user_id": user.get("telegram_user_id"),
            "organization_id": user.get("organization_id"),
            "organization_name": user.get("organization_name"),
        }

    def _sanitize_email_google_connection(self, connection: dict[str, Any] | None) -> dict[str, Any] | None:
        if not connection:
            return None
        return {
            "provider": connection.get("provider"),
            "google_email": connection.get("google_email"),
            "token_expires_at": connection.get("token_expires_at"),
            "scope": connection.get("scope"),
            "created_by_user_id": connection.get("created_by_user_id"),
            "updated_at": connection.get("updated_at"),
        }

    def _email_oauth_state_expired(self, raw_value: Any) -> bool:
        normalized = str(raw_value or "").strip()
        if not normalized:
            return True
        try:
            expires_at = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        except ValueError:
            return True
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return expires_at <= datetime.now(timezone.utc)

    def _actor_from_user_id(self, user_id: Any) -> str | None:
        if user_id in (None, ""):
            return None
        try:
            normalized_user_id = int(user_id)
        except (TypeError, ValueError):
            return None
        user = self.user_repository.get_by_id(normalized_user_id)
        if not user:
            return None
        return user.get("display_name") or user.get("login")

    def _organization_name(self, organization_id: int | None) -> str | None:
        if organization_id in (None, ""):
            return None
        organization = self.organization_repository.get_by_id(int(organization_id))
        return organization.get("name") if organization else None

    def _actor_label_from_user(self, user: dict[str, Any] | None) -> str:
        if not user:
            return "system"
        return str(user.get("display_name") or user.get("login") or "system")

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
