from __future__ import annotations

from app.repositories.billing_repository import BillingRepository
from app.repositories.calendar_repository import CalendarRepository
from app.repositories.contractor_repository import ContractorRepository
from app.repositories.email_import_repository import EmailImportRepository
from app.repositories.email_oauth_repository import EmailOAuthRepository
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.automation_repository import AutomationRepository
from app.repositories.billing_ledger_repository import BillingLedgerRepository
from app.repositories.dashboard_view_repository import DashboardViewRepository
from app.repositories.entity_attachment_repository import EntityAttachmentRepository
from app.repositories.event_repository import EventRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.invoice_handoff_repository import InvoiceHandoffRepository
from app.repositories.invoice_ksef_override_repository import InvoiceKSeFOverrideRepository
from app.repositories.intake_repository import IntakeRepository
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.ksef_import_repository import KSeFImportRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.system_settings_repository import SystemSettingsRepository
from app.repositories.task_template_repository import TaskTemplateRepository
from app.repositories.task_reminder_outbox_repository import TaskReminderOutboxRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.repositories.whiteboard_repository import WhiteboardRepository
from app.services.auth_service import AuthService
from app.services.billing_service import BillingService
from app.services.calendar_service import CalendarService
from app.services.dashboard_service import DashboardService
from app.services.duplicate_detector import DuplicateDetector
from app.services.invoice_service import InvoiceService
from app.services.knowledge_service import KnowledgeService
from app.services.natural_task_command_service import NaturalTaskCommandService
from app.services.approval_service import ApprovalService
from app.services.attachment_service import AttachmentService
from app.services.automation_service import AutomationService
from app.services.billing_ledger_service import BillingLedgerService
from app.services.dashboard_view_service import DashboardViewService
from app.services.notification_service import NotificationService
from app.services.organization_service import OrganizationService
from app.services.intake_service import IntakeService
from app.services.search_service import SearchService
from app.services.storage_service import LocalStorageService
from app.services.system_settings_service import SystemSettingsService
from app.services.task_service import TaskService
from app.services.task_reminder_service import TaskReminderService
from app.services.whiteboard_service import WhiteboardService
from app.integrations.email_google_oauth import EmailGoogleOAuthAdapter
from app.config import DEFAULT_ADMIN_LOGIN, TASK_REMINDER_RETRY_MINUTES
from app.config import TASK_REMINDER_MAX_ATTEMPTS, TASK_REMINDER_PROCESSING_TIMEOUT_MINUTES


def build_services() -> dict[str, object]:
    billing_repository = BillingRepository()
    invoice_repository = InvoiceRepository()
    contractor_repository = ContractorRepository()
    email_import_repository = EmailImportRepository()
    ksef_import_repository = KSeFImportRepository()
    email_oauth_repository = EmailOAuthRepository()
    event_repository = EventRepository()
    organization_repository = OrganizationRepository()
    knowledge_repository = KnowledgeRepository()
    calendar_repository = CalendarRepository()
    whiteboard_repository = WhiteboardRepository()
    user_repository = UserRepository()
    session_repository = SessionRepository()
    system_settings_repository = SystemSettingsRepository()
    task_repository = TaskRepository()
    task_reminder_outbox_repository = TaskReminderOutboxRepository()
    approval_repository = ApprovalRepository()
    automation_repository = AutomationRepository()
    billing_ledger_repository = BillingLedgerRepository()
    dashboard_view_repository = DashboardViewRepository()
    entity_attachment_repository = EntityAttachmentRepository()
    intake_repository = IntakeRepository()
    invoice_handoff_repository = InvoiceHandoffRepository()
    invoice_ksef_override_repository = InvoiceKSeFOverrideRepository()
    task_template_repository = TaskTemplateRepository()
    duplicate_detector = DuplicateDetector(invoice_repository)
    notification_service = NotificationService(event_repository)
    storage_service = LocalStorageService()
    email_google_oauth_adapter = EmailGoogleOAuthAdapter()
    organization_service = OrganizationService(
        organization_repository=organization_repository,
        event_repository=event_repository,
        user_repository=user_repository,
    )
    system_settings_service = SystemSettingsService(
        system_settings_repository=system_settings_repository,
        event_repository=event_repository,
    )
    organization_service.ensure_default_setup(DEFAULT_ADMIN_LOGIN)
    auth_service = AuthService(
        user_repository=user_repository,
        session_repository=session_repository,
        event_repository=event_repository,
        organization_repository=organization_repository,
        organization_service=organization_service,
    )
    calendar_service = CalendarService(
        calendar_repository=calendar_repository,
        user_repository=user_repository,
        organization_repository=organization_repository,
        event_repository=event_repository,
    )
    invoice_service = InvoiceService(
        invoice_repository=invoice_repository,
        contractor_repository=contractor_repository,
        email_import_repository=email_import_repository,
        ksef_import_repository=ksef_import_repository,
        event_repository=event_repository,
        user_repository=user_repository,
        organization_repository=organization_repository,
        task_repository=task_repository,
        duplicate_detector=duplicate_detector,
        notification_service=notification_service,
        storage_service=storage_service,
        email_oauth_repository=email_oauth_repository,
        email_google_oauth_adapter=email_google_oauth_adapter,
        approval_repository=approval_repository,
        invoice_ksef_override_repository=invoice_ksef_override_repository,
        intake_repository=intake_repository,
        invoice_handoff_repository=invoice_handoff_repository,
        system_settings_service=system_settings_service,
    )
    knowledge_service = KnowledgeService(
        knowledge_repository=knowledge_repository,
        organization_repository=organization_repository,
        user_repository=user_repository,
        event_repository=event_repository,
        storage_service=storage_service,
    )
    task_service = TaskService(
        task_repository=task_repository,
        event_repository=event_repository,
        user_repository=user_repository,
        organization_repository=organization_repository,
        invoice_repository=invoice_repository,
        contractor_repository=contractor_repository,
        knowledge_repository=knowledge_repository,
        calendar_service=calendar_service,
        storage_service=storage_service,
        task_template_repository=task_template_repository,
        approval_repository=approval_repository,
    )
    natural_task_command_service = NaturalTaskCommandService(
        user_repository=user_repository,
        calendar_service=calendar_service,
    )
    task_reminder_service = TaskReminderService(
        task_repository=task_repository,
        event_repository=event_repository,
        outbox_repository=task_reminder_outbox_repository,
        organization_repository=organization_repository,
        telegram_adapter=invoice_service.telegram_adapter,
        retry_minutes=TASK_REMINDER_RETRY_MINUTES,
        processing_timeout_minutes=TASK_REMINDER_PROCESSING_TIMEOUT_MINUTES,
        max_attempts=TASK_REMINDER_MAX_ATTEMPTS,
    )
    intake_service = IntakeService(
        intake_repository=intake_repository,
        event_repository=event_repository,
        organization_repository=organization_repository,
        storage_service=storage_service,
        entity_attachment_repository=entity_attachment_repository,
    )
    billing_ledger_service = BillingLedgerService(
        billing_ledger_repository=billing_ledger_repository,
        billing_repository=billing_repository,
        event_repository=event_repository,
    )
    approval_service = ApprovalService(
        approval_repository=approval_repository,
        task_repository=task_repository,
        invoice_repository=invoice_repository,
        event_repository=event_repository,
        organization_repository=organization_repository,
        storage_service=storage_service,
        entity_attachment_repository=entity_attachment_repository,
        invoice_service=invoice_service,
    )
    billing_service = BillingService(
        billing_repository=billing_repository,
        event_repository=event_repository,
        organization_repository=organization_repository,
        billing_ledger_service=billing_ledger_service,
    )
    dashboard_view_service = DashboardViewService(
        dashboard_view_repository=dashboard_view_repository,
        event_repository=event_repository,
        organization_repository=organization_repository,
    )
    automation_service = AutomationService(
        automation_repository=automation_repository,
        event_repository=event_repository,
        intake_service=intake_service,
    )
    whiteboard_service = WhiteboardService(
        whiteboard_repository=whiteboard_repository,
        organization_repository=organization_repository,
        event_repository=event_repository,
        storage_service=storage_service,
    )
    dashboard_service = DashboardService(
        invoice_repository=invoice_repository,
        contractor_repository=contractor_repository,
        event_repository=event_repository,
        task_repository=task_repository,
        organization_repository=organization_repository,
        knowledge_repository=knowledge_repository,
        knowledge_service=knowledge_service,
        intake_repository=intake_repository,
    )
    search_service = SearchService(
        auth_service=auth_service,
        invoice_repository=invoice_repository,
        contractor_repository=contractor_repository,
        task_repository=task_repository,
        knowledge_repository=knowledge_repository,
        billing_repository=billing_repository,
        event_repository=event_repository,
        user_repository=user_repository,
        organization_repository=organization_repository,
    )
    return {
        "organization_repository": organization_repository,
        "system_settings_repository": system_settings_repository,
        "organization_service": organization_service,
        "system_settings_service": system_settings_service,
        "billing_repository": billing_repository,
        "invoice_repository": invoice_repository,
        "knowledge_repository": knowledge_repository,
        "calendar_repository": calendar_repository,
        "whiteboard_repository": whiteboard_repository,
        "task_repository": task_repository,
        "task_reminder_outbox_repository": task_reminder_outbox_repository,
        "approval_repository": approval_repository,
        "automation_repository": automation_repository,
        "billing_ledger_repository": billing_ledger_repository,
        "dashboard_view_repository": dashboard_view_repository,
        "entity_attachment_repository": entity_attachment_repository,
        "intake_repository": intake_repository,
        "invoice_handoff_repository": invoice_handoff_repository,
        "invoice_ksef_override_repository": invoice_ksef_override_repository,
        "task_template_repository": task_template_repository,
        "contractor_repository": contractor_repository,
        "email_import_repository": email_import_repository,
        "ksef_import_repository": ksef_import_repository,
        "event_repository": event_repository,
        "email_oauth_repository": email_oauth_repository,
        "storage_service": storage_service,
        "email_google_oauth_adapter": email_google_oauth_adapter,
        "user_repository": user_repository,
        "session_repository": session_repository,
        "auth_service": auth_service,
        "invoice_service": invoice_service,
        "knowledge_service": knowledge_service,
        "calendar_service": calendar_service,
        "task_service": task_service,
        "natural_task_command_service": natural_task_command_service,
        "task_reminder_service": task_reminder_service,
        "intake_service": intake_service,
        "billing_ledger_service": billing_ledger_service,
        "approval_service": approval_service,
        "billing_service": billing_service,
        "dashboard_view_service": dashboard_view_service,
        "automation_service": automation_service,
        "whiteboard_service": whiteboard_service,
        "dashboard_service": dashboard_service,
        "search_service": search_service,
    }
