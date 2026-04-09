from __future__ import annotations

from app.repositories.contractor_repository import ContractorRepository
from app.repositories.event_repository import EventRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.dashboard_service import DashboardService
from app.services.duplicate_detector import DuplicateDetector
from app.services.invoice_service import InvoiceService
from app.services.notification_service import NotificationService
from app.services.organization_service import OrganizationService
from app.services.storage_service import LocalStorageService
from app.config import DEFAULT_ADMIN_LOGIN


def build_services() -> dict[str, object]:
    invoice_repository = InvoiceRepository()
    contractor_repository = ContractorRepository()
    event_repository = EventRepository()
    organization_repository = OrganizationRepository()
    user_repository = UserRepository()
    session_repository = SessionRepository()
    duplicate_detector = DuplicateDetector(invoice_repository)
    notification_service = NotificationService(event_repository)
    storage_service = LocalStorageService()
    organization_service = OrganizationService(
        organization_repository=organization_repository,
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
    invoice_service = InvoiceService(
        invoice_repository=invoice_repository,
        contractor_repository=contractor_repository,
        event_repository=event_repository,
        user_repository=user_repository,
        organization_repository=organization_repository,
        duplicate_detector=duplicate_detector,
        notification_service=notification_service,
        storage_service=storage_service,
    )
    dashboard_service = DashboardService(
        invoice_repository=invoice_repository,
        contractor_repository=contractor_repository,
        event_repository=event_repository,
    )
    return {
        "organization_repository": organization_repository,
        "organization_service": organization_service,
        "invoice_repository": invoice_repository,
        "contractor_repository": contractor_repository,
        "event_repository": event_repository,
        "storage_service": storage_service,
        "user_repository": user_repository,
        "session_repository": session_repository,
        "auth_service": auth_service,
        "invoice_service": invoice_service,
        "dashboard_service": dashboard_service,
    }
