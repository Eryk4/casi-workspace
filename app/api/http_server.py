from __future__ import annotations

import json
import mimetypes
from email.parser import BytesParser
from email.policy import default
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from app.config import (
    APP_RELEASE_ID,
    CASI_SERVE_LEGACY_STATIC,
    DB_ENGINE,
    ENABLE_DEMO_SEED,
    SECURE_COOKIES,
    SESSION_COOKIE_NAME,
    SESSION_DURATION_HOURS,
    STATIC_DIR,
    PUBLIC_BASE_URL,
    database_label,
    default_login_hint_enabled,
    google_calendar_direct_enabled,
    google_email_direct_enabled,
    test_imports_enabled,
)
from app.demo_seed import build_quick_login_presets
from app.domain.constants import (
    CALENDAR_KIND_LABELS,
    CALENDAR_KINDS,
    GUEST_ROLE,
    DUPLICATE_TYPES,
    INVOICE_STATUSES,
    INVOICE_DECISION_ROLES,
    INVOICE_WORKFLOW_STATES,
    KNOWLEDGE_ASSISTANT_USE_CAPABILITY,
    KNOWLEDGE_CAPABILITIES,
    KNOWLEDGE_DOWNLOAD_CAPABILITY,
    KNOWLEDGE_MANAGE_CAPABILITY,
    KNOWLEDGE_READ_CAPABILITY,
    KNOWLEDGE_SYNC_CAPABILITY,
    KNOWLEDGE_UPLOAD_CAPABILITY,
    MANAGER_ASSISTANT_MANAGER_ROLES,
    MANAGER_ASSISTANT_MODULE,
    MANAGER_ASSISTANT_WORKSPACE_ROLES,
    MANAGER_TASK_FOCUS_VIEWS,
    ORGANIZATION_MANAGEMENT_ROLES,
    ORGANIZATION_SETTINGS_ROLES,
    OWNER_CALENDAR_KINDS,
    SOURCES,
    TASK_ASSIGNMENT_ROLES,
    APPROVAL_ENTITY_TYPES,
    APPROVAL_STATUSES,
    TASK_NOTE_KINDS,
    TASK_FOCUS_VIEWS,
    TASK_FOCUS_VIEW_LABELS,
    TASK_PRIORITIES,
    TASK_RECURRENCE_EDIT_SCOPES,
    TASK_RECURRENCE_PATTERNS,
    TASK_STATUSES,
    TASK_TYPES,
    TASK_VISIBILITY_SCOPES,
    USER_MANAGEMENT_ROLES,
    USER_ROLES,
    WORK_ITEM_PRIORITY_LEVELS,
    WORK_ITEM_SLA_STAGES,
    WORK_ITEM_SOURCE_TYPES,
    WORK_ITEM_STATUSES,
    WORKER_CALENDAR_KINDS,
    WORKER_TASK_FOCUS_VIEWS,
    WRITE_ROLES,
    READ_ROLES,
)
from app.services.auth_service import AuthError, PermissionError
from app.services.knowledge_service import KnowledgeError
from app.services.organization_service import OrganizationError, OrganizationPermissionError
from app.services.system_settings_service import SystemSettingsError
from app.services.storage_service import StorageError, StorageNotFoundError
from app.utils import now_iso


def create_server(host: str, port: int, services: dict[str, object]) -> ThreadingHTTPServer:
    class InvoiceOpsHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            return

        @property
        def invoice_service(self):
            return services["invoice_service"]

        @property
        def dashboard_service(self):
            return services["dashboard_service"]

        @property
        def task_service(self):
            return services["task_service"]

        @property
        def work_item_service(self):
            return services["work_item_service"]

        @property
        def calendar_service(self):
            return services["calendar_service"]

        @property
        def task_reminder_service(self):
            return services["task_reminder_service"]

        @property
        def approval_service(self):
            return services["approval_service"]

        @property
        def intake_service(self):
            return services["intake_service"]

        @property
        def dashboard_view_service(self):
            return services["dashboard_view_service"]

        @property
        def automation_service(self):
            return services["automation_service"]

        @property
        def billing_ledger_service(self):
            return services["billing_ledger_service"]

        @property
        def natural_task_command_service(self):
            return services["natural_task_command_service"]

        @property
        def billing_service(self):
            return services["billing_service"]

        @property
        def whiteboard_service(self):
            return services["whiteboard_service"]

        @property
        def auth_service(self):
            return services["auth_service"]

        @property
        def organization_service(self):
            return services["organization_service"]

        @property
        def system_settings_service(self):
            return services["system_settings_service"]

        @property
        def knowledge_service(self):
            return services["knowledge_service"]

        @property
        def search_service(self):
            return services["search_service"]

        @property
        def storage_service(self):
            return services["storage_service"]

        @property
        def telegram_adapter(self):
            return self.invoice_service.telegram_adapter

        @property
        def slack_adapter(self):
            return self.invoice_service.slack_adapter

        @property
        def current_user(self) -> dict[str, Any] | None:
            if not hasattr(self, "_cached_user"):
                self._cached_user = self.auth_service.get_current_user(self._session_token())
            return self._cached_user

        def _quick_login_presets(self) -> list[dict[str, Any]]:
            if not ENABLE_DEMO_SEED:
                return []
            presets: list[dict[str, Any]] = []
            for payload in build_quick_login_presets():
                user = self.auth_service.user_repository.get_by_login(str(payload.get("login") or "").strip())
                if not user or not int(user.get("is_active") or 0):
                    continue
                presets.append(
                    {
                        "login": payload["login"],
                        "password": payload["password"],
                        "display_name": payload["display_name"],
                        "role": payload["role"],
                        "organization_name": payload["organization_name"],
                    }
                )
            return presets

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)

            if self._is_public_static_path(path):
                return self._serve_static(path)

            if path == "/health":
                return self._send_json({"ok": True})

            if path.startswith("/api/calendar-feeds/") and path.endswith(".ics"):
                sync_token = path.removeprefix("/api/calendar-feeds/").removesuffix(".ics").strip()
                if not sync_token:
                    return self._not_found()
                built_feed = self.calendar_service.build_calendar_feed(sync_token)
                if not built_feed:
                    return self._not_found()
                content, display_name = built_feed
                return self._send_text(
                    content,
                    content_type="text/calendar; charset=utf-8",
                    download_name=f"{display_name}.ics",
                )

            if path == "/api/google-calendar/oauth/callback":
                code = self._query_one(query, "code")
                state_token = self._query_one(query, "state")
                error_code = self._query_one(query, "error")
                try:
                    self.calendar_service.finalize_google_calendar_connection(state_token, code, error_code)
                except ValueError as error:
                    return self._send_text(
                        f"<html><body><h2>Polaczenie Google Calendar nie udalo sie.</h2><p>{str(error)}</p></body></html>",
                        content_type="text/html; charset=utf-8",
                        status=400,
                    )
                return self._send_text(
                    "<html><body><h2>Konto Google zostalo zapisane.</h2><p>Moze wymagac zatwierdzenia przez Administratora organizacji albo Wlasciciela systemu. Mozesz zamknac to okno i wrocic do aplikacji.</p><script>if(window.opener){window.opener.postMessage({type:'google-calendar-connected'}, '*');}</script></body></html>",
                    content_type="text/html; charset=utf-8",
                )

            if path == "/api/email/oauth/callback":
                code = self._query_one(query, "code")
                state_token = self._query_one(query, "state")
                error_code = self._query_one(query, "error")
                try:
                    self.invoice_service.finalize_email_google_connection(
                        state_token=state_token,
                        code=code,
                        error_code=error_code,
                        public_base_url=self._public_base_url(),
                    )
                except ValueError as error:
                    return self._send_text(
                        f"<html><body><h2>Polaczenie Google Workspace dla e-mail nie udalo sie.</h2><p>{str(error)}</p></body></html>",
                        content_type="text/html; charset=utf-8",
                        status=400,
                    )
                return self._send_text(
                    "<html><body><h2>Centralna skrzynka Google Workspace zostala polaczona.</h2><p>Mozez zamknac to okno i wrocic do aplikacji.</p><script>if(window.opener){window.opener.postMessage({type:'email-google-connected'}, '*');}</script></body></html>",
                    content_type="text/html; charset=utf-8",
                )

            if path == "/api/meta":
                email_info = self.invoice_service.email_integration_info()
                ksef_info = self.invoice_service.ksef_integration_info()
                return self._send_json(
                    {
                        "sources": list(SOURCES),
                        "statuses": list(INVOICE_STATUSES),
                        "workflow_states": list(INVOICE_WORKFLOW_STATES),
                        "duplicate_types": list(DUPLICATE_TYPES),
                        "task_types": list(TASK_TYPES),
                        "task_statuses": list(TASK_STATUSES),
                        "task_priorities": list(TASK_PRIORITIES),
                        "task_recurrence_patterns": list(TASK_RECURRENCE_PATTERNS),
                        "task_recurrence_edit_scopes": list(TASK_RECURRENCE_EDIT_SCOPES),
                        "task_focus_views": list(TASK_FOCUS_VIEWS),
                        "task_focus_view_labels": dict(TASK_FOCUS_VIEW_LABELS),
                        "task_focus_views_manager": list(MANAGER_TASK_FOCUS_VIEWS),
                        "task_focus_views_worker": list(WORKER_TASK_FOCUS_VIEWS),
                        "task_visibility_scopes": list(TASK_VISIBILITY_SCOPES),
                        "work_item_statuses": list(WORK_ITEM_STATUSES),
                        "work_item_priority_levels": list(WORK_ITEM_PRIORITY_LEVELS),
                        "work_item_source_types": list(WORK_ITEM_SOURCE_TYPES),
                        "work_item_sla_stages": list(WORK_ITEM_SLA_STAGES),
                        "work_item_sort_fields": [
                            "priority_score",
                            "sla_deadline_at",
                            "due_at",
                            "updated_at",
                            "created_at",
                        ],
                        "task_note_kinds": list(TASK_NOTE_KINDS),
                        "approval_statuses": list(APPROVAL_STATUSES),
                        "approval_entity_types": list(APPROVAL_ENTITY_TYPES),
                        "calendar_kinds": list(CALENDAR_KINDS),
                        "calendar_kind_labels": dict(CALENDAR_KIND_LABELS),
                        "calendar_kinds_owner": list(OWNER_CALENDAR_KINDS),
                        "calendar_kinds_worker": list(WORKER_CALENDAR_KINDS),
                        "calendar_providers": ["google_api", "google_ics"],
                        "roles": list(USER_ROLES),
                        "knowledge_capabilities": list(KNOWLEDGE_CAPABILITIES),
                        "database_label": database_label(),
                        "db_engine": DB_ENGINE,
                        "app_release_id": APP_RELEASE_ID,
                        "email_enabled": email_info["enabled"],
                        "email_mode": email_info["mode"],
                        "email_routing_mode": email_info.get("routing_mode"),
                        "email_scheduler_status": self.invoice_service.email_scheduler_status(),
                        "email_google_oauth_enabled": google_email_direct_enabled(),
                        "email_google_connection": email_info.get("google_connection"),
                        "ksef_enabled": ksef_info["enabled"],
                        "ksef_mode": ksef_info["mode"],
                        "ksef_provider": ksef_info.get("provider"),
                        "ksef_fetch_limit": ksef_info.get("fetch_limit"),
                        "telegram_enabled": self.invoice_service.telegram_integration_info()["enabled"],
                        "slack_enabled": self.invoice_service.slack_integration_info()["enabled"],
                        "ocr_enabled": self.invoice_service.ocr_integration_info()["enabled"],
                        "ocr_mode": self.invoice_service.ocr_integration_info()["mode"],
                        "storage_backend": self.invoice_service.storage_integration_info()["backend"],
                        "public_base_url": self._public_base_url(),
                        "test_imports_enabled": test_imports_enabled(),
                        "default_login_hint_enabled": default_login_hint_enabled(),
                        "quick_login_presets": self._quick_login_presets(),
                        "google_calendar_direct_enabled": google_calendar_direct_enabled(),
                        "task_reminder_status": self.task_reminder_service.integration_status(),
                    }
                )

            if path == "/api/invoices/verification-inbox":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                limit = self._parse_optional_int(self._query_one(query, "limit")) or 6
                return self._send_json(
                    self.invoice_service.verification_inbox_snapshot(
                        organization_id=organization_id,
                        limit=min(max(limit, 1), 25),
                    )
                )

            if path == "/api/invoices/verification-workspace":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                limit = self._parse_optional_int(self._query_one(query, "limit")) or 20
                bucket = self._query_one(query, "bucket")
                return self._send_json(
                    self.invoice_service.verification_workspace_snapshot(
                        organization_id=organization_id,
                        limit_per_bucket=min(max(limit, 1), 60),
                        active_bucket=bucket,
                    )
                )

            if path == "/api/invoices/compare":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                left_id = self._parse_optional_int(self._query_one(query, "left_id"))
                right_id = self._parse_optional_int(self._query_one(query, "right_id"))
                if not left_id or not right_id:
                    return self._send_json({"error": "Podaj dwie faktury do porownania."}, status=400)
                try:
                    comparison = self.invoice_service.compare_invoices(
                        left_id,
                        right_id,
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not comparison:
                    return self._send_json({"error": "Nie znaleziono jednej z faktur do porownania."}, status=404)
                return self._send_json(comparison)

            if path == "/api/session/current":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                return self._send_json(user)

            if path == "/api/organization-shared-note":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                requested_organization_id = self._requested_organization_id(query)
                try:
                    note = self.organization_service.get_shared_note(
                        actor_user=user,
                        requested_organization_id=requested_organization_id,
                    )
                except (OrganizationError, OrganizationPermissionError) as error:
                    return self._handle_scope_error(error)
                return self._send_json(note)

            if path == "/api/user-personal-note":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                try:
                    return self._send_json(self.auth_service.get_personal_note(user))
                except AuthError as error:
                    return self._send_json({"error": str(error)}, status=400)

            if path == "/api/user-calendars":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query)
                if organization_id is ...:
                    return
                return self._send_json(
                    self.calendar_service.list_user_calendars(user, base_url=self._public_base_url())
                )

            if path == "/api/google-calendar/status":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query)
                if organization_id is ...:
                    return
                try:
                    return self._send_json(self.calendar_service.get_google_connection_status(user))
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)

            if path == "/api/google-calendar/external-calendars":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query)
                if organization_id is ...:
                    return
                try:
                    return self._send_json(self.calendar_service.list_external_google_calendars(user))
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)

            if path == "/api/google-calendar/admin-users":
                user = self._require_user(USER_MANAGEMENT_ROLES)
                if not user:
                    return
                requested_organization_id = self._requested_organization_id(query)
                try:
                    snapshot = self.calendar_service.list_google_connection_admin_snapshot(
                        user,
                        requested_organization_id=requested_organization_id,
                        base_url=self._public_base_url(),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(snapshot)

            if path == "/api/google-calendar/organization-calendars":
                user = self._require_user(USER_MANAGEMENT_ROLES)
                if not user:
                    return
                requested_organization_id = self._requested_organization_id(query)
                try:
                    calendars = self.calendar_service.list_assignable_organization_calendars(
                        user,
                        requested_organization_id=requested_organization_id,
                        base_url=self._public_base_url(),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(calendars)

            if path == "/api/user-reminder-preferences":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query)
                if organization_id is ...:
                    return
                return self._send_json(self.calendar_service.get_reminder_preferences(user))

            if path == "/api/tasks/reminders/status":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query)
                if organization_id is ...:
                    return
                return self._send_json(self.task_reminder_service.integration_status(organization_id=organization_id))

            if path == "/api/tasks/reminders/outbox":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query)
                if organization_id is ...:
                    return
                status = self._query_one(query, "status")
                limit = self._parse_optional_int(self._query_one(query, "limit")) or 25
                return self._send_json(
                    self.task_reminder_service.list_outbox_deliveries(
                        limit=limit,
                        organization_id=organization_id,
                        viewer_user_id=int(user["user_id"]),
                        status=status,
                    )
                )

            if path == "/api/task-templates":
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query)
                if organization_id is ...:
                    return
                return self._send_json(self.task_service.list_task_templates(organization_id=organization_id))

            if path == "/api/approvals":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                entity_type = self._query_one(query, "entity_type")
                entity_id = self._parse_optional_int(self._query_one(query, "entity_id"))
                status = self._query_one(query, "status")
                limit = self._parse_optional_int(self._query_one(query, "limit")) or 50
                if entity_type and entity_type not in APPROVAL_ENTITY_TYPES:
                    return self._send_json({"error": "Nieprawidlowy typ akceptacji."}, status=400)
                return self._send_json(
                    self.approval_service.list_requests(
                        organization_id=organization_id,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        status=status,
                        limit=limit,
                        viewer_user=user,
                    )
                )

            if path.startswith("/api/approvals/") and path.endswith("/attachments"):
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                approval_id = self._extract_id(path, "/api/approvals/", suffix="/attachments")
                if approval_id is None:
                    return self._not_found()
                detail = self.approval_service.get_request_detail(
                    approval_id,
                    organization_id=organization_id,
                    viewer_user=user,
                )
                if not detail:
                    return self._send_json({"error": "Nie znaleziono wniosku akceptacji."}, status=404)
                return self._send_json(detail)

            if path.startswith("/api/approvals/") and not path.endswith("/approve") and not path.endswith("/reject"):
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                approval_id = self._extract_id(path, "/api/approvals/")
                if approval_id is None:
                    return self._not_found()
                detail = self.approval_service.get_request_detail(
                    approval_id,
                    organization_id=organization_id,
                    viewer_user=user,
                )
                if not detail:
                    return self._send_json({"error": "Nie znaleziono wniosku akceptacji."}, status=404)
                return self._send_json(detail)

            if path == "/api/support/requests":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_support_scope(user, query)
                if organization_id is ...:
                    return
                status = self._query_one(query, "status")
                search = self._query_one(query, "search")
                limit = self._parse_optional_int(self._query_one(query, "limit")) or 100
                return self._send_json(
                    self.intake_service.list_support_requests(
                        organization_id=organization_id,
                        viewer_user=user,
                        status=status or None,
                        search=search or None,
                        limit=min(limit, 300),
                    )
                )

            if path.startswith("/api/support/requests/"):
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_support_scope(user, query)
                if organization_id is ...:
                    return
                request_id = self._extract_id(path, "/api/support/requests/")
                if request_id is None:
                    return self._not_found()
                detail = self.intake_service.get_support_request_detail(
                    request_id,
                    organization_id=organization_id,
                    viewer_user=user,
                )
                if not detail:
                    return self._send_json({"error": "Nie znaleziono zgłoszenia supportowego."}, status=404)
                return self._send_json(detail)

            if path == "/api/intake/forms":
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                include_inactive = self._parse_optional_bool(self._query_one(query, "include_inactive"), False)
                return self._send_json(
                    self.intake_service.list_forms(
                        organization_id=organization_id,
                        include_inactive=bool(include_inactive),
                    )
                )

            if path == "/api/intake/items":
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                status = self._query_one(query, "status")
                source_kind = self._query_one(query, "source_kind")
                search = self._query_one(query, "search")
                assigned_user_id = self._parse_optional_int(self._query_one(query, "assigned_user_id"))
                limit = self._parse_optional_int(self._query_one(query, "limit")) or 200
                return self._send_json(
                    self.intake_service.list_items(
                        organization_id=organization_id,
                        status=status or None,
                        source_kind=source_kind or None,
                        search=search or None,
                        assigned_user_id=assigned_user_id,
                        limit=min(limit, 1000),
                    )
                )

            if path.startswith("/api/intake/items/"):
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                item_id = self._extract_id(path, "/api/intake/items/")
                if item_id is None:
                    return self._not_found()
                detail = self.intake_service.get_item_detail(item_id, organization_id=organization_id)
                if not detail:
                    return self._send_json({"error": "Nie znaleziono sprawy."}, status=404)
                return self._send_json(detail)

            if path == "/api/dashboard/views":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                module_key = self._query_one(query, "module_key") or "dashboard"
                include_hidden = self._parse_optional_bool(self._query_one(query, "include_hidden"), False)
                try:
                    return self._send_json(
                        self.dashboard_view_service.list_views(
                            module_key,
                            organization_id=organization_id,
                            include_hidden=bool(include_hidden),
                        )
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)

            if path == "/api/automation/rules":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                include_inactive = self._parse_optional_bool(self._query_one(query, "include_inactive"), False)
                return self._send_json(
                    self.automation_service.list_rules(
                        organization_id=organization_id,
                        include_inactive=bool(include_inactive),
                    )
                )

            if path == "/api/automation/executions":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                automation_rule_id = self._parse_optional_int(self._query_one(query, "automation_rule_id"))
                limit = self._parse_optional_int(self._query_one(query, "limit")) or 100
                return self._send_json(
                    self.automation_service.list_executions(
                        organization_id=organization_id,
                        automation_rule_id=automation_rule_id,
                        limit=min(limit, 500),
                    )
                )

            if path == "/api/billing/ledger/balances":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                return self._send_json(self.billing_ledger_service.list_balances(organization_id=organization_id))

            if path == "/api/billing/ledger/entries":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                billing_payer_id = self._parse_optional_int(self._query_one(query, "billing_payer_id"))
                limit = self._parse_optional_int(self._query_one(query, "limit")) or 200
                return self._send_json(
                    self.billing_ledger_service.list_ledger_entries(
                        organization_id=organization_id,
                        billing_payer_id=billing_payer_id,
                        limit=min(limit, 1000),
                    )
                )

            if path == "/api/billing/ledger/matches":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                billing_payer_id = self._parse_optional_int(self._query_one(query, "billing_payer_id"))
                billing_transaction_id = self._parse_optional_int(self._query_one(query, "billing_transaction_id"))
                limit = self._parse_optional_int(self._query_one(query, "limit")) or 200
                return self._send_json(
                    self.billing_ledger_service.list_payment_matches(
                        organization_id=organization_id,
                        billing_payer_id=billing_payer_id,
                        billing_transaction_id=billing_transaction_id,
                        limit=min(limit, 1000),
                    )
                )

            if path == "/api/system/health":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                return self._send_json(self._build_system_health_snapshot(organization_id, viewer_user=user))

            if path == "/api/organizations":
                user = self._require_user(ORGANIZATION_SETTINGS_ROLES)
                if not user:
                    return
                try:
                    organizations = self.organization_service.list_organizations(user)
                except (OrganizationError, OrganizationPermissionError) as error:
                    return self._handle_scope_error(error)
                return self._send_json(organizations)

            if path.startswith("/api/organizations/") and path.endswith("/email-import-runs"):
                user = self._require_user(ORGANIZATION_SETTINGS_ROLES)
                if not user:
                    return
                organization_id = self._extract_id(path, "/api/organizations/", suffix="/email-import-runs")
                if organization_id is None:
                    return self._not_found()
                if not user.get("is_global_admin") and int(user.get("organization_id") or 0) != int(organization_id):
                    return self._send_json({"error": "Brak uprawnien do tej organizacji."}, status=403)
                try:
                    runs = self.invoice_service.list_organization_email_import_runs(
                        organization_id,
                        limit=int(self._query_one(query, "limit") or "8"),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(runs)

            if path.startswith("/api/organizations/") and path.endswith("/ksef-import-runs"):
                user = self._require_user(ORGANIZATION_SETTINGS_ROLES)
                if not user:
                    return
                organization_id = self._extract_id(path, "/api/organizations/", suffix="/ksef-import-runs")
                if organization_id is None:
                    return self._not_found()
                if not user.get("is_global_admin") and int(user.get("organization_id") or 0) != int(organization_id):
                    return self._send_json({"error": "Brak uprawnien do tej organizacji."}, status=403)
                try:
                    runs = self.invoice_service.list_organization_ksef_import_runs(
                        organization_id,
                        limit=int(self._query_one(query, "limit") or "8"),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(runs)

            if path == "/api/integration-center":
                user = self._require_user(ORGANIZATION_SETTINGS_ROLES)
                if not user:
                    return
                requested_organization_id = self._requested_organization_id(query)
                if not user.get("is_global_admin"):
                    requested_organization_id = int(user.get("organization_id") or 0) or None
                try:
                    snapshot = self.invoice_service.integration_center_snapshot(
                        viewer_user=user,
                        requested_organization_id=requested_organization_id,
                        limit=int(self._query_one(query, "limit") or "25"),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(snapshot)

            if path == "/api/system/communication-settings":
                user = self._require_user(ORGANIZATION_SETTINGS_ROLES)
                if not user:
                    return
                try:
                    snapshot = self.system_settings_service.build_communication_settings_snapshot(
                        actor_user=user,
                        public_base_url=self._public_base_url(),
                    )
                except SystemSettingsError as error:
                    return self._send_json({"error": str(error)}, status=403)
                return self._send_json(snapshot)

            if path == "/api/email-center":
                user = self._require_user(ORGANIZATION_SETTINGS_ROLES)
                if not user:
                    return
                requested_organization_id = self._requested_organization_id(query)
                if not user.get("is_global_admin"):
                    requested_organization_id = int(user.get("organization_id") or 0) or None
                try:
                    snapshot = self.invoice_service.email_center_snapshot(
                        viewer_user=user,
                        requested_organization_id=requested_organization_id,
                        limit=int(self._query_one(query, "limit") or "25"),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(snapshot)

            if path == "/api/users":
                user = self._require_user(USER_MANAGEMENT_ROLES)
                if not user:
                    return
                try:
                    requested_organization_id = self._requested_organization_id(query)
                    users = self.auth_service.list_users(user, requested_organization_id=requested_organization_id)
                except PermissionError as error:
                    return self._send_json({"error": str(error)}, status=403)
                except AuthError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(users)
            if path == "/api/tasks/users":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query)
                if organization_id is ...:
                    return
                if not self._role_can_open_manager_assistant_manager_view(user):
                    return self._send_json(
                        {"error": "To konto nie ma dostepu do listy osob dla pelnego Asystenta Szefa."},
                        status=403,
                    )
                return self._send_json(self.task_service.list_assignable_users(organization_id=organization_id))
            if path == "/api/tasks/planner":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query)
                if organization_id is ...:
                    return
                return self._send_json(
                    self.task_service.get_planner_snapshot(
                        organization_id=organization_id,
                        viewer_user=user,
                    )
                )
            if path == "/api/tasks/focus":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query)
                if organization_id is ...:
                    return
                return self._send_json(
                    self.task_service.get_focus_snapshot(
                        organization_id=organization_id,
                        viewer_user=user,
                    )
                )
            if path == "/api/work-items":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                limit = self._parse_optional_int(self._query_one(query, "limit")) or 100
                filters = {
                    "search": self._query_one(query, "search"),
                    "status": self._query_one(query, "status"),
                    "priority_level": self._query_one(query, "priority_level"),
                    "sla_stage": self._query_one(query, "sla_stage"),
                    "source_type": self._query_one(query, "source_type"),
                    "assigned_user_id": self._query_one(query, "assigned_user_id"),
                    "only_open": self._query_one(query, "only_open"),
                    "unassigned_only": self._query_one(query, "unassigned_only"),
                    "due_before": self._query_one(query, "due_before"),
                    "due_overdue_only": self._query_one(query, "due_overdue_only"),
                    "sla_overdue_only": self._query_one(query, "sla_overdue_only"),
                    "sort_by": self._query_one(query, "sort_by"),
                    "sort_dir": self._query_one(query, "sort_dir"),
                }
                return self._send_json(
                    self.work_item_service.list_work_items(
                        filters,
                        organization_id=organization_id,
                        limit=min(max(limit, 1), 300),
                    )
                )
            if path == "/api/work-items/summary":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                return self._send_json(
                    self.work_item_service.get_summary(
                        organization_id=organization_id,
                    )
                )
            if path == "/api/work-items/sla-policy":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                try:
                    return self._send_json(
                        self.work_item_service.get_sla_policy(
                            organization_id=organization_id,
                        )
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
            if path == "/api/work-items/workload":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                limit = self._parse_optional_int(self._query_one(query, "limit")) or 20
                return self._send_json(
                    self.work_item_service.get_workload(
                        organization_id=organization_id,
                        limit=min(max(limit, 1), 200),
                    )
                )
            if path.startswith("/api/work-items/"):
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                work_item_id = self._extract_id(path, "/api/work-items/")
                if work_item_id is None:
                    return self._not_found()
                detail = self.work_item_service.get_work_item_detail(
                    work_item_id,
                    organization_id=organization_id,
                )
                if not detail:
                    return self._send_json({"error": "Nie znaleziono pozycji pracy."}, status=404)
                return self._send_json(detail)
            if path == "/api/whiteboard":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_whiteboard_scope(user, query, require_active=False)
                if organization_id is ...:
                    return
                after_event_id = self._parse_optional_int(self._query_one(query, "since_event_id"))
                try:
                    return self._send_json(
                        self.whiteboard_service.get_board_state(
                            organization_id=organization_id,
                            after_event_id=after_event_id,
                        )
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
            if path == "/api/knowledge/documents":
                user = self._require_knowledge_read_user()
                if not user:
                    return
                organization_id = self._resolve_knowledge_scope(user, query)
                if organization_id is ...:
                    return
                search = self._query_one(query, "search")
                try:
                    return self._send_json(
                        self.knowledge_service.list_documents(
                            organization_id=organization_id,
                            search=search,
                            include_deleted=bool(
                                self.auth_service.has_capability(user, KNOWLEDGE_MANAGE_CAPABILITY)
                                and self._parse_optional_bool(self._query_one(query, "include_deleted"), default=False)
                            ),
                            viewer_user_id=int(user["user_id"]),
                        )
                    )
                except KnowledgeError as error:
                    return self._send_json({"error": str(error)}, status=400)
            if path == "/api/knowledge/assignment-candidates":
                user = self._require_knowledge_manage_user()
                if not user:
                    return
                organization_id = self._resolve_knowledge_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                try:
                    return self._send_json(self.knowledge_service.list_assignment_candidates(organization_id))
                except KnowledgeError as error:
                    return self._send_json({"error": str(error)}, status=400)
            if path.startswith("/api/knowledge/documents/"):
                user = self._require_knowledge_read_user()
                if not user:
                    return
                organization_id = self._resolve_knowledge_scope(user, query)
                if organization_id is ...:
                    return
                if path.endswith("/compare"):
                    document_id = self._extract_id(path, "/api/knowledge/documents/", suffix="/compare")
                    if document_id is None:
                        return self._not_found()
                    try:
                        left_version_number = int(self._query_one(query, "left_version") or 0)
                        right_version_number = int(self._query_one(query, "right_version") or 0)
                        return self._send_json(
                            self.knowledge_service.compare_document_versions(
                                organization_id=organization_id,
                                knowledge_document_id=document_id,
                                left_version_number=left_version_number,
                                right_version_number=right_version_number,
                            )
                        )
                    except (KnowledgeError, ValueError) as error:
                        return self._send_json({"error": str(error)}, status=400)
                if path.endswith("/preview-file"):
                    document_id = self._extract_id(path, "/api/knowledge/documents/", suffix="/preview-file")
                    if document_id is None:
                        return self._not_found()
                    can_preview_binary = self.auth_service.has_capability(
                        user, KNOWLEDGE_DOWNLOAD_CAPABILITY
                    ) or self.auth_service.has_capability(user, KNOWLEDGE_MANAGE_CAPABILITY)
                    if not can_preview_binary:
                        return self._send_json(
                            {"error": "To konto nie ma prawa otwierac podgladu plikow firmowych."},
                            status=403,
                        )
                    try:
                        detail = self.knowledge_service.get_document_detail(
                            organization_id=organization_id,
                            knowledge_document_id=document_id,
                            include_deleted=self.auth_service.has_capability(user, KNOWLEDGE_MANAGE_CAPABILITY),
                            viewer_user_id=int(user["user_id"]),
                        )
                    except KnowledgeError as error:
                        return self._send_json({"error": str(error)}, status=404)
                    if str(detail.get("lifecycle_status") or "active") == "deleted":
                        return self._send_json({"error": "Nie mozna otworzyc usunietego dokumentu."}, status=410)
                    preview_kind = str(detail.get("file_preview_kind") or "none")
                    if preview_kind not in {"pdf", "image", "text"}:
                        return self._send_json({"error": "Tego typu pliku nie mozna pokazac inline."}, status=415)
                    try:
                        data = self.storage_service.read_binary("knowledge", str(detail["file_storage_key"]))
                    except StorageNotFoundError:
                        return self._not_found()
                    except StorageError:
                        return self._send_json({"error": "Nieprawidlowa sciezka pliku."}, status=400)
                    content_type = detail.get("mime_type") or mimetypes.guess_type(str(detail.get("file_name") or ""))[0] or "application/octet-stream"
                    if preview_kind == "text":
                        content_type = "text/plain; charset=utf-8"
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Length", str(len(data)))
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    self.wfile.write(data)
                    return
                if path.endswith("/download"):
                    if not self.auth_service.has_capability(user, KNOWLEDGE_DOWNLOAD_CAPABILITY):
                        return self._send_json({"error": "To konto nie ma prawa pobierać plików firmowych."}, status=403)
                    document_id = self._extract_id(path, "/api/knowledge/documents/", suffix="/download")
                    if document_id is None:
                        return self._not_found()
                    try:
                        detail = self.knowledge_service.get_document_detail(
                            organization_id=organization_id,
                            knowledge_document_id=document_id,
                            include_deleted=self.auth_service.has_capability(user, KNOWLEDGE_MANAGE_CAPABILITY),
                            viewer_user_id=int(user["user_id"]),
                        )
                    except KnowledgeError as error:
                        return self._send_json({"error": str(error)}, status=404)
                    if str(detail.get("lifecycle_status") or "active") == "deleted":
                        return self._send_json({"error": "Nie mozna pobrac usunietego dokumentu."}, status=410)
                    try:
                        data = self.storage_service.read_binary("knowledge", str(detail["file_storage_key"]))
                    except StorageNotFoundError:
                        return self._not_found()
                    except StorageError:
                        return self._send_json({"error": "Nieprawidlowa sciezka pliku."}, status=400)
                    self.knowledge_service.record_document_download(
                        organization_id=organization_id,
                        knowledge_document_id=document_id,
                        actor_user=user,
                        actor=self._actor_label(user),
                    )
                    content_type = mimetypes.guess_type(str(detail.get("file_name") or ""))[0] or "application/octet-stream"
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Disposition", f'attachment; filename="{detail["file_name"]}"')
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
                document_id = self._extract_id(path, "/api/knowledge/documents/")
                if document_id is None:
                    return self._not_found()
                try:
                    return self._send_json(
                        self.knowledge_service.get_document_detail(
                            organization_id=organization_id,
                            knowledge_document_id=document_id,
                            include_deleted=self.auth_service.has_capability(user, KNOWLEDGE_MANAGE_CAPABILITY),
                            viewer_user_id=int(user["user_id"]),
                        )
                    )
                except KnowledgeError as error:
                    return self._send_json({"error": str(error)}, status=404)

            matched_storage = self._match_storage_path(path)
            if matched_storage:
                storage_user = self._require_user(READ_ROLES)
                if not storage_user:
                    return
                artifact_type, storage_key = matched_storage
                return self._send_storage_file(artifact_type, storage_key, storage_user)

            user = self._require_user(WRITE_ROLES)
            if not user:
                return

            if path == "/api/billing/bank-accounts":
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                only_active = self._query_one(query, "only_active") in {"1", "true", "tak"}
                bank_accounts = self.billing_service.list_bank_accounts(
                    organization_id=organization_id if organization_id is not None else None
                )
                if only_active:
                    bank_accounts = [item for item in bank_accounts if item.get("is_active")]
                return self._send_json(bank_accounts)
            if path == "/api/billing/transactions":
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                bank_account_id = self._parse_optional_int(self._query_one(query, "bank_account_id"))
                limit = self._parse_optional_int(self._query_one(query, "limit")) or 200
                if limit < 1:
                    limit = 200
                try:
                    transactions = self.billing_service.list_transactions(
                        organization_id=organization_id,
                        billing_bank_account_id=bank_account_id,
                        matched_status=self._query_one(query, "matched_status") or None,
                        limit=min(limit, 1000),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(transactions)
            if path == "/api/billing/payment-review-statuses":
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                limit = self._parse_optional_int(self._query_one(query, "limit")) or 500
                try:
                    review_statuses = self.billing_service.list_latest_payment_review_statuses(
                        organization_id=organization_id,
                        limit=min(max(limit, 1), 1000),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(review_statuses)
            if path == "/api/billing/work-queue/events":
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                limit = self._parse_optional_int(self._query_one(query, "limit")) or 500
                try:
                    work_queue_events = self.billing_service.list_work_queue_events(
                        organization_id=organization_id,
                        limit=min(max(limit, 1), 1000),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(work_queue_events)
            if path == "/api/billing/schools":
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                return self._send_json(self.billing_service.list_schools(organization_id=organization_id))
            if path == "/api/billing/models":
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                return self._send_json(self.billing_service.list_models(organization_id=organization_id))
            if path.startswith("/api/billing/payers/") and path.endswith("/notes"):
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                payer_id = self._extract_id(path, "/api/billing/payers/", suffix="/notes")
                if payer_id is None:
                    return self._not_found()
                limit = self._parse_optional_int(self._query_one(query, "limit")) or 100
                try:
                    notes = self.billing_service.list_payer_notes(
                        payer_id,
                        organization_id=organization_id,
                        limit=min(max(limit, 1), 200),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=404)
                return self._send_json(notes)
            if path.startswith("/api/billing/payments/") and path.endswith("/review-status"):
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                payment_id = self._extract_id(path, "/api/billing/payments/", suffix="/review-status")
                if payment_id is None:
                    return self._not_found()
                limit = self._parse_optional_int(self._query_one(query, "limit")) or 20
                try:
                    review_status = self.billing_service.list_payment_review_events(
                        payment_id,
                        organization_id=organization_id,
                        limit=min(max(limit, 1), 50),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=404)
                return self._send_json(review_status)
            if path == "/api/billing/payers":
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                return self._send_json(self.billing_service.list_payers(organization_id=organization_id))
            if path == "/api/billing/students":
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                return self._send_json(self.billing_service.list_students(organization_id=organization_id))
            if path == "/api/billing/charges":
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                billing_model_id = self._parse_optional_int(self._query_one(query, "billing_model_id"))
                limit = self._parse_optional_int(self._query_one(query, "limit")) or 200
                if limit < 1:
                    limit = 200
                return self._send_json(
                    self.billing_service.list_charges(
                        organization_id=organization_id,
                        billing_model_id=billing_model_id,
                        limit=min(limit, 1000),
                    )
                )
            if path == "/api/dashboard":
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                snapshot = self.dashboard_service.get_snapshot(
                    organization_id=organization_id,
                    viewer_user_id=int(user["user_id"]),
                )
                return self._send_json(self._filter_dashboard_snapshot(snapshot, organization_id))
            if path == "/api/invoices":
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                filters = {
                    "search": self._query_one(query, "search"),
                    "source": self._query_one(query, "source"),
                    "status": self._query_one(query, "status"),
                    "workflow_state": self._query_one(query, "workflow_state"),
                    "duplicate_type": self._query_one(query, "duplicate_type"),
                    "date_from": self._query_one(query, "date_from"),
                    "date_to": self._query_one(query, "date_to"),
                    "contractor_id": self._query_one(query, "contractor_id"),
                    "assigned_user_id": self._query_one(query, "assigned_user_id"),
                    "nip": self._query_one(query, "nip"),
                    "invoice_number": self._query_one(query, "invoice_number"),
                    "ksef_number": self._query_one(query, "ksef_number"),
                    "sort_by": self._query_one(query, "sort_by"),
                    "sort_order": self._query_one(query, "sort_order"),
                }
                return self._send_json(self.invoice_service.list_invoices(filters, organization_id=organization_id))
            if path == "/api/invoices/assignable-users":
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                return self._send_json(self.invoice_service.list_assignable_invoice_users(organization_id=organization_id))
            if path.startswith("/api/invoices/") and path.endswith("/preview"):
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                invoice_id = self._extract_id(path, "/api/invoices/", suffix="/preview")
                if invoice_id is None:
                    return self._not_found()
                preview = self.invoice_service.get_invoice_preview(
                    invoice_id,
                    organization_id=organization_id,
                    viewer_user=user,
                )
                if not preview:
                    return self._send_json({"error": "Nie znaleziono faktury."}, status=404)
                return self._send_json(preview)
            if path == "/api/invoices/document-intake":
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                limit = self._parse_optional_int(self._query_one(query, "limit")) or 20
                return self._send_json(
                    self.invoice_service.document_intake_snapshot(
                        organization_id=organization_id,
                        limit=min(max(limit, 1), 100),
                    )
                )
            if path == "/api/invoices/exceptions":
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                limit = self._parse_optional_int(self._query_one(query, "limit")) or 20
                return self._send_json(
                    self.invoice_service.exception_center_snapshot(
                        organization_id=organization_id,
                        limit=min(max(limit, 1), 100),
                    )
                )
            if path == "/api/invoice-handoff-batches":
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                limit = self._parse_optional_int(self._query_one(query, "limit")) or 20
                return self._send_json(
                    self.invoice_service.list_handoff_batches(
                        organization_id=organization_id,
                        limit=min(max(limit, 1), 100),
                    )
                )
            if path.startswith("/api/invoice-handoff-batches/") and path.endswith("/export"):
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                batch_id = self._extract_id(path, "/api/invoice-handoff-batches/", suffix="/export")
                if batch_id is None:
                    return self._not_found()
                try:
                    export_payload = self.invoice_service.export_handoff_batch_csv(
                        batch_id,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except PermissionError as error:
                    return self._send_json({"error": str(error)}, status=403)
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(export_payload)
            if path.startswith("/api/invoice-handoff-batches/"):
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                batch_id = self._extract_id(path, "/api/invoice-handoff-batches/")
                if batch_id is None:
                    return self._not_found()
                detail = self.invoice_service.get_handoff_batch_detail(
                    batch_id,
                    organization_id=organization_id,
                )
                if not detail:
                    return self._send_json({"error": "Nie znaleziono paczki przekazania."}, status=404)
                return self._send_json(detail)
            if path.startswith("/api/invoices/"):
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                invoice_id = self._extract_id(path, "/api/invoices/")
                if invoice_id is None:
                    return self._not_found()
                detail = self.invoice_service.get_invoice_detail(
                    invoice_id,
                    organization_id=organization_id,
                    viewer_user=user,
                )
                if not detail:
                    return self._send_json({"error": "Nie znaleziono faktury."}, status=404)
                detail["history"] = self.invoice_service._sanitize_invoice_history_events(detail.get("history") or [])
                return self._send_json(detail)
            if path == "/api/contractors":
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                search = self._query_one(query, "search")
                only_new = self._query_one(query, "only_new") in {"1", "true", "tak"}
                return self._send_json(
                    self.invoice_service.list_contractors(
                        search,
                        only_new=only_new,
                        organization_id=organization_id,
                    )
                )
            if path.startswith("/api/contractors/"):
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                contractor_id = self._extract_id(path, "/api/contractors/")
                if contractor_id is None:
                    return self._not_found()
                detail = self.invoice_service.get_contractor_detail(
                    contractor_id,
                    organization_id=organization_id,
                    viewer_user=user,
                )
                if not detail:
                    return self._send_json({"error": "Nie znaleziono kontrahenta."}, status=404)
                return self._send_json(detail)
            if path == "/api/logs":
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                return self._send_json(
                    self.invoice_service.list_logs(
                        organization_id=organization_id,
                        viewer_user_id=int(user["user_id"]),
                    )
                )
            if path == "/api/tasks":
                organization_id = self._resolve_manager_assistant_scope(user, query)
                if organization_id is ...:
                    return
                filters = {
                    "search": self._query_one(query, "search"),
                    "task_type": self._query_one(query, "task_type"),
                    "status": self._query_one(query, "status"),
                    "priority": self._query_one(query, "priority"),
                    "assigned_user_id": self._query_one(query, "assigned_user_id"),
                    "focus_view": self._query_one(query, "focus_view"),
                    "recurrence_pattern": self._query_one(query, "recurrence_pattern"),
                    "due_from": self._query_one(query, "due_from"),
                    "due_to": self._query_one(query, "due_to"),
                    "remind_from": self._query_one(query, "remind_from"),
                    "remind_to": self._query_one(query, "remind_to"),
                    "due_reminders_only": self._query_one(query, "due_reminders_only"),
                }
                return self._send_json(
                    self.task_service.list_tasks(
                        filters,
                        organization_id=organization_id,
                        viewer_user=user,
                    )
                )
            if path.startswith("/api/tasks/"):
                organization_id = self._resolve_manager_assistant_scope(user, query)
                if organization_id is ...:
                    return
                task_id = self._extract_id(path, "/api/tasks/")
                if task_id is None:
                    return self._not_found()
                detail = self.task_service.get_task_detail(
                    task_id,
                    organization_id=organization_id,
                    viewer_user=user,
                )
                if not detail:
                    return self._send_json({"error": "Nie znaleziono zadania."}, status=404)
                return self._send_json(detail)
            if path == "/api/search":
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                return self._send_json(
                    self.search_service.search(
                        self._query_one(query, "q"),
                        actor_user=user,
                        organization_id=organization_id,
                    )
                )
            if "." in path.rsplit("/", 1)[-1]:
                return self._not_found()
            if CASI_SERVE_LEGACY_STATIC:
                return self._serve_static("/")
            return self._not_found()

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)

            if self.slack_adapter.webhook_path and path == self.slack_adapter.webhook_path:
                raw_body = self._read_body_bytes()
                try:
                    is_valid_request = self.slack_adapter.verify_request(self.headers, raw_body)
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not is_valid_request:
                    return self._send_json({"error": "Nieprawidlowy podpis webhooka Slack."}, status=403)
                try:
                    payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
                except json.JSONDecodeError:
                    return self._send_json({"error": "Webhook Slack zawiera nieprawidlowy JSON."}, status=400)
                if str(payload.get("type") or "").strip() == "url_verification":
                    return self._send_text(
                        str(payload.get("challenge") or ""),
                        content_type="text/plain; charset=utf-8",
                    )
                try:
                    invoice = self.invoice_service.import_slack_event(payload)
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if invoice is None:
                    return self._send_json({"ok": True, "ignored": True})
                return self._send_json({"ok": True, "invoice_id": invoice["id"]})

            if self.telegram_adapter.webhook_path and path == self.telegram_adapter.webhook_path:
                payload = self._read_json()
                try:
                    invoice = self.invoice_service.import_telegram_update(payload)
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json({"ok": True, "invoice_id": invoice["id"]})

            if path == "/api/session/login":
                payload = self._read_json()
                try:
                    user, session_token = self.auth_service.login(
                        payload.get("login", ""),
                        payload.get("password", ""),
                        self._client_ip(),
                        self.headers.get("User-Agent"),
                        self._device_id(),
                        self._device_label(),
                    )
                except AuthError as error:
                    return self._send_json({"error": str(error)}, status=401)
                self._cached_user = user
                return self._send_json(
                    user,
                    extra_headers=[("Set-Cookie", self._build_session_cookie(session_token))],
                )

            if path == "/api/session/logout":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                token = self._session_token()
                if token:
                    self.auth_service.logout(token, actor_login=self._actor_label(user))
                self._cached_user = None
                return self._send_json(
                    {"ok": True},
                    extra_headers=[("Set-Cookie", self._build_clear_cookie())],
                )

            if path == "/api/google-calendar/connect":
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    connection = self.calendar_service.begin_google_calendar_connection(
                        user,
                        confirm_work_account_visibility=bool(payload.get("confirm_work_account_visibility")),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(connection)

            if path.startswith("/api/google-calendar/connections/") and path.endswith("/approve"):
                user = self._require_user(USER_MANAGEMENT_ROLES)
                if not user:
                    return
                target_user_id = self._extract_id(path, "/api/google-calendar/connections/", suffix="/approve")
                if target_user_id is None:
                    return self._not_found()
                try:
                    status = self.calendar_service.approve_google_calendar_connection(
                        target_user_id,
                        actor_user=user,
                        actor=self._actor_label(user),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(status)

            if path.startswith("/api/google-calendar/connections/") and path.endswith("/reject"):
                user = self._require_user(USER_MANAGEMENT_ROLES)
                if not user:
                    return
                target_user_id = self._extract_id(path, "/api/google-calendar/connections/", suffix="/reject")
                if target_user_id is None:
                    return self._not_found()
                try:
                    status = self.calendar_service.reject_google_calendar_connection(
                        target_user_id,
                        actor_user=user,
                        actor=self._actor_label(user),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(status)

            if path == "/api/google-calendar/assignments":
                user = self._require_user(USER_MANAGEMENT_ROLES)
                if not user:
                    return
                payload = self._read_json()
                user_id = self._parse_optional_int(str(payload.get("user_id") or ""))
                user_calendar_id = self._parse_optional_int(str(payload.get("user_calendar_id") or ""))
                if user_id is None or user_calendar_id is None:
                    return self._send_json({"error": "Wskaz uzytkownika i kalendarz organizacji."}, status=400)
                try:
                    assigned = self.calendar_service.assign_organization_calendar_to_user(
                        user_id,
                        user_calendar_id,
                        actor_user=user,
                        actor=self._actor_label(user),
                        base_url=self._public_base_url(),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(assigned)

            if path == "/api/email/google/connect":
                user = self._require_user(ORGANIZATION_MANAGEMENT_ROLES)
                if not user:
                    return
                payload = self._read_json()
                try:
                    connection = self.invoice_service.begin_email_google_connection(
                        actor_user=user,
                        public_base_url=self._public_base_url(),
                        login_hint=str(payload.get("login_hint") or "").strip() or None,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(connection)

            if path == "/api/email/google/disconnect":
                user = self._require_user(ORGANIZATION_MANAGEMENT_ROLES)
                if not user:
                    return
                try:
                    status = self.invoice_service.disconnect_email_google_connection(actor_user=user)
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(status)

            if path == "/api/google-calendar/disconnect":
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                try:
                    status = self.calendar_service.disconnect_google_calendar(
                        user,
                        actor=self._actor_label(user),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(status)

            if path == "/api/user-calendars":
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                payload = self._read_json()
                allowed_fields = {
                    "display_name",
                    "description",
                    "provider",
                    "calendar_kind",
                    "linked_organization_id",
                    "default_duration_minutes",
                    "is_active",
                    "external_calendar_id",
                }
                if any(key not in allowed_fields for key in payload):
                    return self._send_json(
                        {
                            "error": (
                                "user-calendars przyjmuje tylko pola display_name, description, provider, "
                                "calendar_kind, linked_organization_id, default_duration_minutes, is_active "
                                "i external_calendar_id."
                            )
                        },
                        status=400,
                    )
                try:
                    created = self.calendar_service.create_user_calendar(
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        base_url=self._public_base_url(),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(created, status=201)

            if path == "/api/user-reminder-preferences":
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                payload = self._read_json()
                allowed_fields = {
                    "telegram_reminders_enabled",
                    "browser_notifications_enabled",
                    "quiet_hours_start",
                    "quiet_hours_end",
                    "repeat_interval_minutes",
                }
                if any(key not in allowed_fields for key in payload):
                    return self._send_json(
                        {
                            "error": (
                                "Endpoint przyjmuje tylko pola telegram_reminders_enabled, "
                                "browser_notifications_enabled, quiet_hours_start, quiet_hours_end "
                                "i repeat_interval_minutes."
                            )
                        },
                        status=400,
                    )
                try:
                    updated = self.calendar_service.update_reminder_preferences(
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(updated)

            if path == "/api/tasks/reminders/dispatch":
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                result = self.task_reminder_service.dispatch_due_reminders(
                    organization_id=organization_id,
                    viewer_user_id=int(user["user_id"]),
                )
                return self._send_json(
                    {
                        "result": result,
                        "status": self.task_reminder_service.integration_status(organization_id=organization_id),
                    }
                )

            if path.startswith("/api/tasks/reminders/outbox/") and path.endswith("/retry"):
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                outbox_id = self._extract_id(path, "/api/tasks/reminders/outbox/", suffix="/retry")
                if outbox_id is None:
                    return self._not_found()
                try:
                    detail = self.task_reminder_service.retry_outbox_delivery(
                        outbox_id,
                        organization_id=organization_id,
                        viewer_user_id=int(user["user_id"]),
                        actor=self._actor_label(user),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not detail:
                    return self._send_json({"error": "Nie znaleziono wpisu outboxa."}, status=404)
                return self._send_json(detail, status=200)

            if path == "/api/task-templates":
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    created = self.task_service.create_task_template(
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(created, status=201)

            if path.startswith("/api/task-templates/") and path.endswith("/apply"):
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                template_id = self._extract_id(path, "/api/task-templates/", suffix="/apply")
                if template_id is None:
                    return self._not_found()
                payload = self._read_json()
                try:
                    created = self.task_service.apply_task_template(
                        template_id,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                        anchor_at=self._query_one(query, "anchor_at"),
                        overrides=payload,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not created:
                    return self._send_json({"error": "Nie znaleziono szablonu."}, status=404)
                return self._send_json(created, status=201)

            if path == "/api/approvals":
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                payload = self._read_json()
                entity_type = str(payload.get("entity_type") or "").strip()
                if entity_type not in APPROVAL_ENTITY_TYPES:
                    return self._send_json({"error": "Nieprawidlowy typ akceptacji."}, status=400)
                entity_id = self._parse_optional_int(str(payload.get("entity_id") or ""))
                if entity_id is None:
                    return self._send_json({"error": "Brakuje identyfikatora elementu."}, status=400)
                try:
                    created = self.approval_service.create_request(
                        entity_type=entity_type,
                        entity_id=entity_id,
                        organization_id=organization_id,
                        actor_user=user,
                        actor=self._actor_label(user),
                        title=str(payload.get("title") or "").strip() or "Wniosek akceptacji",
                        description=str(payload.get("description") or "").strip() or None,
                        requested_user_id=self._parse_optional_int(str(payload.get("requested_user_id") or "")),
                        approve_status=str(payload.get("approve_status") or "").strip() or None,
                        reject_status=str(payload.get("reject_status") or "").strip() or None,
                        metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else None,
                    )
                except PermissionError as error:
                    return self._send_json({"error": str(error)}, status=403)
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(created, status=201)

            if path.startswith("/api/approvals/") and path.endswith("/attachments"):
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                approval_id = self._extract_id(path, "/api/approvals/", suffix="/attachments")
                if approval_id is None:
                    return self._not_found()
                payload = self._read_json()
                try:
                    result = self.approval_service.add_attachment(
                        approval_id,
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not result:
                    return self._send_json({"error": "Nie znaleziono wniosku akceptacji."}, status=404)
                return self._send_json(result, status=201)

            if path == "/api/support/requests":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_support_scope(user, query)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    created = self.intake_service.create_support_request(
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(created, status=201)

            if path.startswith("/api/support/requests/") and path.endswith("/comments"):
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_support_scope(user, query)
                if organization_id is ...:
                    return
                request_id = self._extract_id(path, "/api/support/requests/", suffix="/comments")
                if request_id is None:
                    return self._not_found()
                payload = self._read_json()
                allowed_fields = {"note_text", "parent_comment_id"}
                if any(key not in allowed_fields for key in payload):
                    return self._send_json(
                        {"error": "Endpoint przyjmuje tylko pola note_text i parent_comment_id."},
                        status=400,
                    )
                try:
                    detail = self.intake_service.add_support_comment(
                        request_id,
                        str(payload.get("note_text") or ""),
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                        parent_comment_id=self._parse_optional_int(payload.get("parent_comment_id")),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not detail:
                    return self._send_json({"error": "Nie znaleziono zgłoszenia supportowego."}, status=404)
                return self._send_json(detail, status=201)

            if path.startswith("/api/support/requests/") and path.endswith("/attachments"):
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_support_scope(user, query)
                if organization_id is ...:
                    return
                request_id = self._extract_id(path, "/api/support/requests/", suffix="/attachments")
                if request_id is None:
                    return self._not_found()
                payload = self._read_json()
                try:
                    detail = self.intake_service.add_support_attachment(
                        request_id,
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not detail:
                    return self._send_json({"error": "Nie znaleziono zgłoszenia supportowego."}, status=404)
                return self._send_json(detail, status=201)

            if path == "/api/intake/forms":
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    created = self.intake_service.create_form(
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(created, status=201)

            if path == "/api/intake/items":
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    created = self.intake_service.create_item(
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(created, status=201)

            if path.startswith("/api/intake/items/") and path.endswith("/comments"):
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                item_id = self._extract_id(path, "/api/intake/items/", suffix="/comments")
                if item_id is None:
                    return self._not_found()
                payload = self._read_json()
                allowed_fields = {"note_text", "parent_comment_id"}
                if any(key not in allowed_fields for key in payload):
                    return self._send_json(
                        {"error": "Endpoint przyjmuje tylko pola note_text i parent_comment_id."},
                        status=400,
                    )
                try:
                    detail = self.intake_service.add_comment(
                        item_id,
                        str(payload.get("note_text") or ""),
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                        parent_comment_id=self._parse_optional_int(payload.get("parent_comment_id")),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not detail:
                    return self._send_json({"error": "Nie znaleziono sprawy."}, status=404)
                return self._send_json(detail, status=201)

            if path.startswith("/api/intake/items/") and path.endswith("/attachments"):
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                item_id = self._extract_id(path, "/api/intake/items/", suffix="/attachments")
                if item_id is None:
                    return self._not_found()
                payload = self._read_json()
                try:
                    detail = self.intake_service.add_attachment(
                        item_id,
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not detail:
                    return self._send_json({"error": "Nie znaleziono sprawy."}, status=404)
                return self._send_json(detail, status=201)

            if path == "/api/dashboard/views":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                payload = self._read_json()
                allowed_fields = {
                    "module_key",
                    "view_name",
                    "view_slug",
                    "description",
                    "view_state",
                    "view_state_json",
                    "is_shared",
                    "is_default",
                }
                if any(key not in allowed_fields for key in payload):
                    return self._send_json(
                        {
                            "error": (
                                "dashboard views przyjmuje tylko pola module_key, view_name, view_slug, "
                                "description, view_state, view_state_json, is_shared i is_default."
                            )
                        },
                        status=400,
                    )
                try:
                    created = self.dashboard_view_service.create_view(
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(created, status=201)

            if path == "/api/automation/rules":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    created = self.automation_service.create_rule(
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(created, status=201)

            if path.startswith("/api/automation/rules/") and path.endswith("/run"):
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                rule_id = self._extract_id(path, "/api/automation/rules/", suffix="/run")
                if rule_id is None:
                    return self._not_found()
                try:
                    result = self.automation_service.run_rule(
                        rule_id,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if result is None:
                    return self._send_json({"error": "Nie znaleziono reguly automatyzacji."}, status=404)
                return self._send_json(result, status=201)

            if path == "/api/billing/ledger/matches":
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    transaction_id = int(payload.get("billing_transaction_id") or 0)
                    payer_id = int(payload.get("billing_payer_id") or 0)
                    matched_amount = float(payload.get("matched_amount") or 0)
                except (TypeError, ValueError):
                    return self._send_json({"error": "Nieprawidlowe dane dopasowania."}, status=400)
                transaction = self.billing_service.billing_repository.get_transaction_by_id(
                    transaction_id,
                    organization_id=organization_id,
                )
                if not transaction:
                    return self._send_json({"error": "Nie znaleziono transakcji."}, status=404)
                try:
                    result = self.billing_ledger_service.match_transaction(
                        transaction,
                        billing_payer_id=payer_id,
                        matched_amount=matched_amount,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                        billing_charge_id=self._parse_optional_int(payload.get("billing_charge_id")),
                        match_reason=str(payload.get("match_reason") or "").strip() or None,
                        match_status=str(payload.get("match_status") or "rozliczona").strip() or "rozliczona",
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(result, status=201)

            if path.startswith("/api/approvals/") and path.endswith("/approve"):
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                approval_id = self._extract_id(path, "/api/approvals/", suffix="/approve")
                if approval_id is None:
                    return self._not_found()
                payload = self._read_json()
                try:
                    updated = self.approval_service.decide_request(
                        approval_id,
                        decision="approve",
                        actor_user=user,
                        actor=self._actor_label(user),
                        reason=str(payload.get("reason") or "").strip() or None,
                    )
                except PermissionError as error:
                    return self._send_json({"error": str(error)}, status=403)
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(updated)

            if path.startswith("/api/approvals/") and path.endswith("/reject"):
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                approval_id = self._extract_id(path, "/api/approvals/", suffix="/reject")
                if approval_id is None:
                    return self._not_found()
                payload = self._read_json()
                try:
                    updated = self.approval_service.decide_request(
                        approval_id,
                        decision="reject",
                        actor_user=user,
                        actor=self._actor_label(user),
                        reason=str(payload.get("reason") or "").strip() or None,
                    )
                except PermissionError as error:
                    return self._send_json({"error": str(error)}, status=403)
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(updated)

            if path == "/api/organizations":
                user = self._require_user(ORGANIZATION_SETTINGS_ROLES)
                if not user:
                    return
                payload = self._read_json()
                if not user.get("is_global_admin"):
                    return self._send_json({"error": "Tylko Wlasciciel systemu moze tworzyc organizacje."}, status=403)
                try:
                    created = self.organization_service.create_organization(
                        payload,
                        actor_user=user,
                        actor_login=self._actor_label(user),
                    )
                except (OrganizationError, OrganizationPermissionError) as error:
                    return self._handle_scope_error(error)
                return self._send_json(created, status=201)

            if path == "/api/users":
                user = self._require_user(USER_MANAGEMENT_ROLES)
                if not user:
                    return
                payload = self._read_json()
                try:
                    created = self.auth_service.create_user(
                        payload,
                        actor_login=self._actor_label(user),
                        actor_user_id=int(user["user_id"]),
                        actor_user=user,
                    )
                except PermissionError as error:
                    return self._send_json({"error": str(error)}, status=403)
                except AuthError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(created, status=201)

            if path == "/api/knowledge/documents":
                user = self._require_knowledge_upload_user()
                if not user:
                    return
                organization_id = self._resolve_knowledge_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                try:
                    content_type = self.headers.get("Content-Type", "")
                    if "multipart/form-data" in content_type:
                        payload = self._read_multipart_form()
                    else:
                        payload = self._read_json()
                    uploaded_file = payload.get("file") if isinstance(payload.get("file"), dict) else None
                    created = self.knowledge_service.add_document(
                        organization_id=organization_id,
                        title=str(payload.get("title", "")),
                        actor_user=user,
                        actor=self._actor_label(user),
                        file_name=str(
                            payload.get("file_name")
                            or (uploaded_file or {}).get("file_name")
                            or ""
                        ),
                        content_text=str(payload.get("content_text", "")),
                        file_bytes=(uploaded_file or {}).get("content"),
                        mime_type=(uploaded_file or {}).get("content_type"),
                        library_path=str(payload.get("library_path", "")),
                        is_downloadable=self._parse_optional_bool(payload.get("is_downloadable"), default=True),
                        use_in_assistant=self._parse_optional_bool(payload.get("use_in_assistant"), default=True),
                    )
                except KnowledgeError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(created, status=201)

            if path == "/api/knowledge/documents/bulk":
                user = self._require_knowledge_manage_user()
                if not user:
                    return
                organization_id = self._resolve_knowledge_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    result = self.knowledge_service.bulk_update_documents(
                        organization_id=organization_id,
                        knowledge_document_ids=payload.get("knowledge_document_ids") or payload.get("document_ids") or [],
                        action=str(payload.get("action") or ""),
                        actor_user=user,
                        actor=self._actor_label(user),
                        library_path=payload.get("library_path"),
                        enabled=self._parse_optional_bool(payload.get("enabled")),
                    )
                except KnowledgeError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(result)

            if path == "/api/knowledge/sync":
                user = self._require_knowledge_sync_user()
                if not user:
                    return
                organization_id = self._resolve_knowledge_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                try:
                    result = self.knowledge_service.sync_folder(
                        organization_id=organization_id,
                        actor_user=user,
                        actor=self._actor_label(user),
                    )
                except KnowledgeError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(result)

            if path == "/api/knowledge/activity/mark-seen":
                user = self._require_knowledge_read_user()
                if not user:
                    return
                organization_id = self._resolve_knowledge_scope(user, query)
                if organization_id is ...:
                    return
                return self._send_json(
                    self.knowledge_service.mark_activity_feed_seen(
                        organization_id=organization_id,
                        viewer_user_id=int(user["user_id"]),
                    )
                )

            if path.startswith("/api/knowledge/documents/") and path.endswith("/reprocess"):
                user = self._require_knowledge_manage_user()
                if not user:
                    return
                organization_id = self._resolve_knowledge_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                document_id = self._extract_id(path, "/api/knowledge/documents/", suffix="/reprocess")
                if document_id is None:
                    return self._not_found()
                try:
                    result = self.knowledge_service.reprocess_document(
                        organization_id=organization_id,
                        knowledge_document_id=document_id,
                        actor_user=user,
                        actor=self._actor_label(user),
                    )
                except KnowledgeError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(result, status=202)

            if path.startswith("/api/knowledge/documents/") and path.endswith("/replace"):
                user = self._require_knowledge_upload_user()
                if not user:
                    return
                organization_id = self._resolve_knowledge_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                document_id = self._extract_id(path, "/api/knowledge/documents/", suffix="/replace")
                if document_id is None:
                    return self._not_found()
                content_type = self.headers.get("Content-Type", "")
                payload = self._read_multipart_form() if "multipart/form-data" in content_type else self._read_json()
                uploaded_file = payload.get("file") if isinstance(payload.get("file"), dict) else None
                if not uploaded_file:
                    return self._send_json({"error": "Wybierz nowy plik dokumentu."}, status=400)
                try:
                    updated = self.knowledge_service.replace_document_file(
                        organization_id=organization_id,
                        knowledge_document_id=document_id,
                        actor_user=user,
                        actor=self._actor_label(user),
                        file_name=str(uploaded_file.get("file_name") or payload.get("file_name") or ""),
                        file_bytes=uploaded_file.get("content") or b"",
                        mime_type=uploaded_file.get("content_type"),
                        content_text=str(payload.get("content_text", "")),
                    )
                except KnowledgeError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(updated, status=202)

            if path.startswith("/api/knowledge/documents/") and path.endswith("/archive"):
                user = self._require_knowledge_manage_user()
                if not user:
                    return
                organization_id = self._resolve_knowledge_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                document_id = self._extract_id(path, "/api/knowledge/documents/", suffix="/archive")
                if document_id is None:
                    return self._not_found()
                try:
                    updated = self.knowledge_service.archive_document(
                        organization_id=organization_id,
                        knowledge_document_id=document_id,
                        actor_user=user,
                        actor=self._actor_label(user),
                    )
                except KnowledgeError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(updated)

            if path.startswith("/api/knowledge/documents/") and path.endswith("/restore"):
                user = self._require_knowledge_manage_user()
                if not user:
                    return
                organization_id = self._resolve_knowledge_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                document_id = self._extract_id(path, "/api/knowledge/documents/", suffix="/restore")
                if document_id is None:
                    return self._not_found()
                try:
                    updated = self.knowledge_service.restore_document(
                        organization_id=organization_id,
                        knowledge_document_id=document_id,
                        actor_user=user,
                        actor=self._actor_label(user),
                    )
                except KnowledgeError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(updated)

            if path.startswith("/api/knowledge/documents/") and path.endswith("/restore-version"):
                user = self._require_knowledge_manage_user()
                if not user:
                    return
                organization_id = self._resolve_knowledge_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                document_id = self._extract_id(path, "/api/knowledge/documents/", suffix="/restore-version")
                if document_id is None:
                    return self._not_found()
                payload = self._read_json()
                allowed_fields = {"version_number"}
                if any(key not in allowed_fields for key in payload):
                    return self._send_json({"error": "restore-version przyjmuje tylko pole version_number."}, status=400)
                try:
                    updated = self.knowledge_service.restore_document_version(
                        organization_id=organization_id,
                        knowledge_document_id=document_id,
                        version_number=int(payload.get("version_number") or 0),
                        actor_user=user,
                        actor=self._actor_label(user),
                    )
                except (KnowledgeError, ValueError) as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(updated, status=202)

            if path.startswith("/api/knowledge/documents/") and path.endswith("/mark-official-version"):
                user = self._require_knowledge_manage_user()
                if not user:
                    return
                organization_id = self._resolve_knowledge_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                document_id = self._extract_id(path, "/api/knowledge/documents/", suffix="/mark-official-version")
                if document_id is None:
                    return self._not_found()
                payload = self._read_json()
                allowed_fields = {"version_number"}
                if any(key not in allowed_fields for key in payload):
                    return self._send_json(
                        {"error": "mark-official-version przyjmuje tylko pole version_number."},
                        status=400,
                    )
                try:
                    updated = self.knowledge_service.mark_document_official_version(
                        organization_id=organization_id,
                        knowledge_document_id=document_id,
                        version_number=int(payload.get("version_number") or 0),
                        actor_user=user,
                        actor=self._actor_label(user),
                    )
                except (KnowledgeError, ValueError) as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(updated)

            if path.startswith("/api/knowledge/documents/") and path.endswith("/decision"):
                user = self._require_knowledge_read_user()
                if not user:
                    return
                organization_id = self._resolve_knowledge_scope(user, query)
                if organization_id is ...:
                    return
                document_id = self._extract_id(path, "/api/knowledge/documents/", suffix="/decision")
                if document_id is None:
                    return self._not_found()
                payload = self._read_json()
                try:
                    updated = self.knowledge_service.decide_document_workflow(
                        organization_id=organization_id,
                        knowledge_document_id=document_id,
                        action=payload.get("action"),
                        reason=str(payload.get("reason") or ""),
                        actor_user=user,
                        actor=self._actor_label(user),
                        owner_user_id=payload.get("owner_user_id", ...),
                        reviewer_user_id=payload.get("reviewer_user_id", ...),
                        approver_user_id=payload.get("approver_user_id", ...),
                    )
                except (KnowledgeError, ValueError) as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(updated)

            if path.startswith("/api/knowledge/documents/") and path.endswith("/tasks"):
                user = self._require_knowledge_read_user()
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                document_id = self._extract_id(path, "/api/knowledge/documents/", suffix="/tasks")
                if document_id is None:
                    return self._not_found()
                try:
                    self.knowledge_service.get_document_detail(
                        organization_id=organization_id,
                        knowledge_document_id=document_id,
                        viewer_user_id=int(user["user_id"]),
                    )
                except KnowledgeError as error:
                    return self._send_json({"error": str(error)}, status=404)
                payload = self._read_json()
                linked_entities = list(payload.get("linked_entities") or [])
                linked_entities.append({"entity_type": "knowledge_document", "entity_id": int(document_id)})
                try:
                    created_task = self.task_service.create_task(
                        {
                            **payload,
                            "linked_entities": linked_entities,
                        },
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                    detail = self.knowledge_service.record_linked_task_created(
                        organization_id=organization_id,
                        knowledge_document_id=document_id,
                        task_id=int(created_task["task_id"]),
                        task_title=str(created_task.get("title") or ""),
                        actor_user=user,
                        actor=self._actor_label(user),
                    )
                except (KnowledgeError, ValueError) as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json({"task": created_task, "document": detail}, status=201)

            if path.startswith("/api/knowledge/documents/") and path.endswith("/comments"):
                user = self._require_knowledge_read_user()
                if not user:
                    return
                organization_id = self._resolve_knowledge_scope(user, query)
                if organization_id is ...:
                    return
                document_id = self._extract_id(path, "/api/knowledge/documents/", suffix="/comments")
                if document_id is None:
                    return self._not_found()
                payload = self._read_json()
                allowed_fields = {"note_text", "version_number", "annotation_kind", "anchor_label", "anchor_excerpt"}
                if any(key not in allowed_fields for key in payload):
                    return self._send_json(
                        {
                            "error": (
                                "Endpoint przyjmuje tylko pola note_text, version_number, "
                                "annotation_kind, anchor_label i anchor_excerpt."
                            )
                        },
                        status=400,
                    )
                try:
                    updated = self.knowledge_service.add_document_comment(
                        organization_id=organization_id,
                        knowledge_document_id=document_id,
                        note_text=str(payload.get("note_text") or ""),
                        version_number=self._parse_optional_int(payload.get("version_number")),
                        annotation_kind=str(payload.get("annotation_kind") or "comment"),
                        anchor_label=payload.get("anchor_label"),
                        anchor_excerpt=payload.get("anchor_excerpt"),
                        actor_user=user,
                        actor=self._actor_label(user),
                    )
                except (KnowledgeError, ValueError) as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(updated, status=201)

            if path == "/api/knowledge/ask":
                user = self._require_knowledge_assistant_user()
                if not user:
                    return
                organization_id = self._resolve_knowledge_scope(user, query)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    return self._send_json(
                        self.knowledge_service.answer_question(
                            payload.get("question", ""),
                            organization_id=organization_id,
                        )
                    )
                except KnowledgeError as error:
                    return self._send_json({"error": str(error)}, status=400)

            if path == "/api/whiteboard/events":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_whiteboard_scope(user, query, require_active=True)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    return self._send_json(
                        self.whiteboard_service.add_strokes(
                            organization_id=organization_id,
                            strokes=payload.get("strokes") or [],
                            actor_user=user,
                            actor=self._actor_label(user),
                        ),
                        status=201,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)

            if path == "/api/whiteboard/images":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_whiteboard_scope(user, query, require_active=True)
                if organization_id is ...:
                    return
                content_type = self.headers.get("Content-Type", "")
                payload = self._read_multipart_form() if "multipart/form-data" in content_type else self._read_json()
                uploaded_file = payload.get("file") if isinstance(payload.get("file"), dict) else None
                try:
                    return self._send_json(
                        self.whiteboard_service.add_image(
                            organization_id=organization_id,
                            file_name=str(payload.get("file_name") or (uploaded_file or {}).get("file_name") or ""),
                            file_bytes=(uploaded_file or {}).get("content"),
                            mime_type=(uploaded_file or {}).get("content_type"),
                            placement={
                                "x": payload.get("x"),
                                "y": payload.get("y"),
                                "width": payload.get("width"),
                                "height": payload.get("height"),
                            },
                            actor_user=user,
                            actor=self._actor_label(user),
                        ),
                        status=201,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)

            user = self._require_user(WRITE_ROLES)
            if not user:
                return

            if path == "/api/whiteboard/actions/clear":
                organization_id = self._resolve_whiteboard_scope(user, query, require_active=True)
                if organization_id is ...:
                    return
                try:
                    return self._send_json(
                        self.whiteboard_service.clear_board(
                            organization_id=organization_id,
                            actor_user=user,
                            actor=self._actor_label(user),
                        )
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)

            if path.startswith("/api/organizations/") and path.endswith("/actions/test-email-connection"):
                user = self._require_user(ORGANIZATION_SETTINGS_ROLES)
                if not user:
                    return
                organization_id = self._extract_id(path, "/api/organizations/", suffix="/actions/test-email-connection")
                if organization_id is None:
                    return self._not_found()
                if not user.get("is_global_admin") and int(user.get("organization_id") or 0) != int(organization_id):
                    return self._send_json({"error": "Brak uprawnien do tej organizacji."}, status=403)
                try:
                    result = self.invoice_service.test_organization_email_connection(
                        organization_id,
                        actor=self._actor_label(user),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(result, status=200)

            if path.startswith("/api/organizations/") and path.endswith("/actions/test-ksef-connection"):
                user = self._require_user(ORGANIZATION_SETTINGS_ROLES)
                if not user:
                    return
                organization_id = self._extract_id(path, "/api/organizations/", suffix="/actions/test-ksef-connection")
                if organization_id is None:
                    return self._not_found()
                if not user.get("is_global_admin") and int(user.get("organization_id") or 0) != int(organization_id):
                    return self._send_json({"error": "Brak uprawnien do tej organizacji."}, status=403)
                try:
                    result = self.invoice_service.test_organization_ksef_connection(
                        organization_id,
                        actor=self._actor_label(user),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(result, status=200)

            if path.startswith("/api/organizations/") and path.endswith("/actions/check-email"):
                user = self._require_user(ORGANIZATION_SETTINGS_ROLES)
                if not user:
                    return
                organization_id = self._extract_id(path, "/api/organizations/", suffix="/actions/check-email")
                if organization_id is None:
                    return self._not_found()
                if not user.get("is_global_admin") and int(user.get("organization_id") or 0) != int(organization_id):
                    return self._send_json({"error": "Brak uprawnien do tej organizacji."}, status=403)
                try:
                    result = self.invoice_service.check_organization_email(
                        organization_id,
                        actor=self._actor_label(user),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(result, status=200)

            if path.startswith("/api/organizations/") and path.endswith("/actions/check-ksef"):
                user = self._require_user(ORGANIZATION_SETTINGS_ROLES)
                if not user:
                    return
                organization_id = self._extract_id(path, "/api/organizations/", suffix="/actions/check-ksef")
                if organization_id is None:
                    return self._not_found()
                if not user.get("is_global_admin") and int(user.get("organization_id") or 0) != int(organization_id):
                    return self._send_json({"error": "Brak uprawnien do tej organizacji."}, status=403)
                try:
                    result = self.invoice_service.check_organization_ksef(
                        organization_id,
                        actor=self._actor_label(user),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(result, status=200)

            if path == "/api/invoices/actions/batch":
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    result = self.invoice_service.apply_batch_action(
                        payload.get("invoice_ids") or [],
                        str(payload.get("action") or ""),
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(result, status=200)

            if path == "/api/invoice-handoff-batches":
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    result = self.invoice_service.create_handoff_batch(
                        payload.get("invoice_ids") or [],
                        handoff_target=payload.get("handoff_target"),
                        note=payload.get("note"),
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except PermissionError as error:
                    return self._send_json({"error": str(error)}, status=403)
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(result, status=201)

            if path.startswith("/api/invoices/") and path.endswith("/comments"):
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                invoice_id = self._extract_id(path, "/api/invoices/", suffix="/comments")
                if invoice_id is None:
                    return self._not_found()
                payload = self._read_json()
                if any(key != "note_text" for key in payload):
                    return self._send_json({"error": "Endpoint przyjmuje tylko pole note_text."}, status=400)
                try:
                    comment = self.invoice_service.add_invoice_comment(
                        invoice_id,
                        str(payload.get("note_text") or ""),
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(comment, status=201)

            if path.startswith("/api/contractors/") and path.endswith("/notes"):
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                contractor_id = self._extract_id(path, "/api/contractors/", suffix="/notes")
                if contractor_id is None:
                    return self._not_found()
                payload = self._read_json()
                if any(key != "note_text" for key in payload):
                    return self._send_json({"error": "Endpoint przyjmuje tylko pole note_text."}, status=400)
                try:
                    note = self.invoice_service.add_contractor_note(
                        contractor_id,
                        str(payload.get("note_text") or ""),
                        actor_user=user,
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(note, status=201)

            if path == "/api/work-items/sla/sweep":
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                payload = self._read_json()
                if any(key != "limit" for key in payload):
                    return self._send_json({"error": "Endpoint przyjmuje tylko pole limit."}, status=400)
                limit = self._parse_optional_int(str(payload.get("limit") or "")) or 50
                result = self.work_item_service.run_sla_sweep(
                    organization_id=organization_id,
                    actor=self._actor_label(user),
                    limit=min(max(limit, 1), 300),
                )
                return self._send_json({"result": result})

            if path == "/api/work-items":
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    created = self.work_item_service.create_work_item(
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(created, status=201)

            if path == "/api/work-items/bulk":
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    result = self.work_item_service.bulk_apply(
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(result, status=200)

            if path == "/api/work-items/sla-policy":
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    result = self.work_item_service.update_sla_policy(
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(result, status=200)

            if path.startswith("/api/work-items/") and path.endswith("/assign"):
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                work_item_id = self._extract_id(path, "/api/work-items/", suffix="/assign")
                if work_item_id is None:
                    return self._not_found()
                payload = self._read_json()
                if any(key != "assigned_user_id" for key in payload):
                    return self._send_json({"error": "Endpoint przyjmuje tylko pole assigned_user_id."}, status=400)
                assigned_user_id = self._parse_optional_int(str(payload.get("assigned_user_id") or ""))
                try:
                    updated = self.work_item_service.assign_work_item(
                        work_item_id,
                        assigned_user_id,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not updated:
                    return self._send_json({"error": "Nie znaleziono pozycji pracy."}, status=404)
                return self._send_json(updated)

            if path.startswith("/api/work-items/") and path.endswith("/snooze"):
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                work_item_id = self._extract_id(path, "/api/work-items/", suffix="/snooze")
                if work_item_id is None:
                    return self._not_found()
                payload = self._read_json()
                if any(key != "mode" for key in payload):
                    return self._send_json({"error": "Endpoint przyjmuje tylko pole mode."}, status=400)
                try:
                    updated = self.work_item_service.snooze_work_item(
                        work_item_id,
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not updated:
                    return self._send_json({"error": "Nie znaleziono pozycji pracy."}, status=404)
                return self._send_json(updated)

            if path.startswith("/api/work-items/") and path.endswith("/escalate"):
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                work_item_id = self._extract_id(path, "/api/work-items/", suffix="/escalate")
                if work_item_id is None:
                    return self._not_found()
                payload = self._read_json()
                if any(key != "assigned_user_id" for key in payload):
                    return self._send_json({"error": "Endpoint przyjmuje tylko pole assigned_user_id."}, status=400)
                try:
                    updated = self.work_item_service.escalate_work_item(
                        work_item_id,
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not updated:
                    return self._send_json({"error": "Nie znaleziono pozycji pracy."}, status=404)
                return self._send_json(updated)

            if path.startswith("/api/work-items/") and path.endswith("/close"):
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                work_item_id = self._extract_id(path, "/api/work-items/", suffix="/close")
                if work_item_id is None:
                    return self._not_found()
                payload = self._read_json()
                if any(key != "reason" for key in payload):
                    return self._send_json({"error": "Endpoint przyjmuje tylko pole reason."}, status=400)
                try:
                    updated = self.work_item_service.close_work_item(
                        work_item_id,
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not updated:
                    return self._send_json({"error": "Nie znaleziono pozycji pracy."}, status=404)
                return self._send_json(updated)

            if path.startswith("/api/work-items/") and path.endswith("/reopen"):
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                work_item_id = self._extract_id(path, "/api/work-items/", suffix="/reopen")
                if work_item_id is None:
                    return self._not_found()
                payload = self._read_json()
                allowed_fields = {"status", "reason", "due_at", "sla_deadline_at", "sla_warning_minutes", "sla_warning_at"}
                if any(key not in allowed_fields for key in payload):
                    return self._send_json(
                        {
                            "error": (
                                "Endpoint przyjmuje tylko pola status, reason, due_at, "
                                "sla_deadline_at, sla_warning_minutes i sla_warning_at."
                            )
                        },
                        status=400,
                    )
                try:
                    updated = self.work_item_service.reopen_work_item(
                        work_item_id,
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not updated:
                    return self._send_json({"error": "Nie znaleziono pozycji pracy."}, status=404)
                return self._send_json(updated)

            if path == "/api/tasks":
                organization_id = self._resolve_manager_assistant_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    created = self.task_service.create_task(
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(created, status=201)

            if path == "/api/tasks/parse-natural":
                organization_id = self._resolve_manager_assistant_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    preview = self.natural_task_command_service.parse(
                        str(payload.get("command_text") or ""),
                        actor_user=user,
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(preview, status=200)

            if path.startswith("/api/tasks/") and path.endswith("/send-reminder"):
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                task_id = self._extract_id(path, "/api/tasks/", suffix="/send-reminder")
                if task_id is None:
                    return self._not_found()
                try:
                    task = self.task_reminder_service.send_reminder_now(
                        task_id,
                        organization_id=organization_id,
                        viewer_user_id=int(user["user_id"]),
                        actor=self._actor_label(user),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not task:
                    return self._send_json({"error": "Nie znaleziono zadania."}, status=404)
                detail = self.task_service.get_task_detail(
                    task_id,
                    organization_id=organization_id,
                    viewer_user=user,
                )
                if not detail:
                    return self._send_json({"error": "Nie znaleziono zadania."}, status=404)
                return self._send_json(detail, status=200)

            if path.startswith("/api/tasks/") and path.endswith("/sync-calendar"):
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                task_id = self._extract_id(path, "/api/tasks/", suffix="/sync-calendar")
                if task_id is None:
                    return self._not_found()
                try:
                    detail = self.task_service.sync_task_calendar(
                        task_id,
                        organization_id=organization_id,
                        actor_user=user,
                        actor=self._actor_label(user),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not detail:
                    return self._send_json({"error": "Nie znaleziono zadania."}, status=404)
                return self._send_json(detail, status=200)

            if path.startswith("/api/tasks/") and path.endswith("/check-calendar"):
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                task_id = self._extract_id(path, "/api/tasks/", suffix="/check-calendar")
                if task_id is None:
                    return self._not_found()
                try:
                    detail = self.task_service.check_task_calendar_sync(
                        task_id,
                        organization_id=organization_id,
                        actor_user=user,
                        actor=self._actor_label(user),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not detail:
                    return self._send_json({"error": "Nie znaleziono zadania."}, status=404)
                return self._send_json(detail, status=200)

            if path.startswith("/api/tasks/") and path.endswith("/snooze-reminder"):
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                task_id = self._extract_id(path, "/api/tasks/", suffix="/snooze-reminder")
                if task_id is None:
                    return self._not_found()
                payload = self._read_json()
                if any(key != "mode" for key in payload):
                    return self._send_json({"error": "Endpoint przyjmuje tylko pole mode."}, status=400)
                try:
                    detail = self.task_service.snooze_task_reminder(
                        task_id,
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not detail:
                    return self._send_json({"error": "Nie znaleziono zadania."}, status=404)
                return self._send_json(detail, status=200)

            if path.startswith("/api/tasks/") and path.endswith("/attachments"):
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                task_id = self._extract_id(path, "/api/tasks/", suffix="/attachments")
                if task_id is None:
                    return self._not_found()
                payload = self._read_json()
                try:
                    detail = self.task_service.add_task_attachment(
                        task_id,
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except (ValueError, StorageError) as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not detail:
                    return self._send_json({"error": "Nie znaleziono zadania."}, status=404)
                return self._send_json(detail, status=201)

            if path.startswith("/api/tasks/") and (path.endswith("/notes") or path.endswith("/comments")):
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                task_id = self._extract_id(path, "/api/tasks/", suffix="/notes") if path.endswith("/notes") else self._extract_id(path, "/api/tasks/", suffix="/comments")
                if task_id is None:
                    return self._not_found()
                payload = self._read_json()
                allowed_fields = {"note_text", "parent_note_id", "note_kind"}
                if any(key not in allowed_fields for key in payload):
                    return self._send_json(
                        {"error": "Endpoint przyjmuje tylko pola note_text, parent_note_id i note_kind."},
                        status=400,
                    )
                try:
                    detail = self.task_service.add_task_note(
                        task_id,
                        str(payload.get("note_text") or ""),
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                        parent_note_id=self._parse_optional_int(str(payload.get("parent_note_id") or "")),
                        note_kind=str(payload.get("note_kind") or "comment"),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not detail:
                    return self._send_json({"error": "Nie znaleziono zadania."}, status=404)
                return self._send_json(detail, status=201)

            if path.startswith("/api/tasks/") and path.endswith("/checklist"):
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                task_id = self._extract_id(path, "/api/tasks/", suffix="/checklist")
                if task_id is None:
                    return self._not_found()
                payload = self._read_json()
                allowed_fields = {"item_text"}
                if any(key not in allowed_fields for key in payload):
                    return self._send_json({"error": "checklist przyjmuje tylko pole item_text."}, status=400)
                try:
                    detail = self.task_service.add_task_checklist_item(
                        task_id,
                        str(payload.get("item_text") or ""),
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not detail:
                    return self._send_json({"error": "Nie znaleziono zadania."}, status=404)
                return self._send_json(detail, status=201)

            if path == "/api/billing/bank-accounts":
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    created = self.billing_service.create_bank_account(
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(created, status=201)

            if path == "/api/billing/schools":
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    created = self.billing_service.create_school(
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(created, status=201)

            if path == "/api/billing/models":
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    created = self.billing_service.create_model(
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(created, status=201)

            if path == "/api/billing/payers":
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    created = self.billing_service.create_payer(
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(created, status=201)

            if path.startswith("/api/billing/payers/") and path.endswith("/notes"):
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                payer_id = self._extract_id(path, "/api/billing/payers/", suffix="/notes")
                if payer_id is None:
                    return self._not_found()
                payload = self._read_json()
                if any(key != "note_text" for key in payload):
                    return self._send_json({"error": "Endpoint przyjmuje tylko pole note_text."}, status=400)
                try:
                    note = self.billing_service.add_payer_note(
                        payer_id,
                        str(payload.get("note_text") or ""),
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    if "Nie znaleziono platnika" in str(error):
                        return self._send_json({"error": str(error)}, status=404)
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(note, status=201)

            if path.startswith("/api/billing/payments/") and path.endswith("/review-status"):
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                payment_id = self._extract_id(path, "/api/billing/payments/", suffix="/review-status")
                if payment_id is None:
                    return self._not_found()
                payload = self._read_json()
                allowed_fields = {"status", "note_text"}
                if any(key not in allowed_fields for key in payload):
                    return self._send_json({"error": "Endpoint przyjmuje tylko pola status i note_text."}, status=400)
                try:
                    review_event = self.billing_service.add_payment_review_event(
                        payment_id,
                        str(payload.get("status") or ""),
                        payload.get("note_text"),
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    if "Nie znaleziono wplaty" in str(error):
                        return self._send_json({"error": str(error)}, status=404)
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(review_event, status=201)

            if path == "/api/billing/work-queue/events":
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                payload = self._read_json()
                allowed_fields = {"issue_key", "issue_type", "target_type", "target_id", "action", "note_text"}
                if any(key not in allowed_fields for key in payload):
                    return self._send_json(
                        {
                            "error": (
                                "Endpoint przyjmuje tylko pola issue_key, issue_type, target_type, "
                                "target_id, action i note_text."
                            )
                        },
                        status=400,
                    )
                try:
                    work_queue_event = self.billing_service.add_work_queue_event(
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    if "Nie znaleziono wplaty" in str(error) or "Nie znaleziono platnika" in str(error):
                        return self._send_json({"error": str(error)}, status=404)
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(work_queue_event, status=201)

            if path == "/api/billing/students":
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    created = self.billing_service.create_student(
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(created, status=201)

            if path == "/api/billing/charges/generate":
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    result = self.billing_service.generate_charges_for_model(
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(result, status=201)

            if path == "/api/billing/statements/import-csv":
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    bank_account_id = int(payload.get("billing_bank_account_id") or 0)
                except (TypeError, ValueError):
                    return self._send_json({"error": "Nieprawidlowy identyfikator rachunku bankowego."}, status=400)
                try:
                    result = self.billing_service.import_statement_csv(
                        bank_account_id,
                        str(payload.get("csv_content") or ""),
                        source_file_name=str(payload.get("source_file_name") or "").strip() or None,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(result, status=201)

            if path.startswith("/api/tasks/") and path.endswith("/notes"):
                organization_id = self._resolve_manager_assistant_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                task_id = self._extract_id(path, "/api/tasks/", suffix="/notes")
                if task_id is None:
                    return self._not_found()
                payload = self._read_json()
                try:
                    detail = self.task_service.add_task_note(
                        task_id,
                        payload.get("note_text", ""),
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not detail:
                    return self._send_json({"error": "Nie znaleziono zadania."}, status=404)
                return self._send_json(detail, status=201)

            if path.startswith("/api/invoices/") and path.endswith("/actions/confirm-duplicate"):
                if user["role"] not in INVOICE_DECISION_ROLES:
                    return self._send_json({"error": "Ta rola nie moze potwierdzac duplikatow."}, status=403)
                invoice_id = self._extract_id(path, "/api/invoices/", suffix="/actions/confirm-duplicate")
                if invoice_id is None:
                    return self._not_found()
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                invoice = self.invoice_service.confirm_duplicate(
                    invoice_id,
                    actor=self._actor_label(user),
                    organization_id=organization_id,
                )
                if not invoice:
                    return self._send_json({"error": "Nie znaleziono faktury."}, status=404)
                return self._send_json(invoice)

            if path.startswith("/api/invoices/") and path.endswith("/actions/mark-ready"):
                invoice_id = self._extract_id(path, "/api/invoices/", suffix="/actions/mark-ready")
                if invoice_id is None:
                    return self._not_found()
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    invoice = self.invoice_service.mark_invoice_ready_for_handoff(
                        invoice_id,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                        handoff_target=payload.get("handoff_target"),
                        handoff_note=payload.get("handoff_note"),
                    )
                except PermissionError as error:
                    return self._send_json({"error": str(error)}, status=403)
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not invoice:
                    return self._send_json({"error": "Nie znaleziono faktury."}, status=404)
                return self._send_json(invoice)

            if path.startswith("/api/invoices/") and path.endswith("/actions/undo-last"):
                invoice_id = self._extract_id(path, "/api/invoices/", suffix="/actions/undo-last")
                if invoice_id is None:
                    return self._not_found()
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                try:
                    invoice = self.invoice_service.undo_last_invoice_workflow_decision(
                        invoice_id,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except PermissionError as error:
                    return self._send_json({"error": str(error)}, status=403)
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not invoice:
                    return self._send_json({"error": "Nie znaleziono faktury."}, status=404)
                return self._send_json(invoice)

            if path.startswith("/api/invoices/") and path.endswith("/actions/handoff"):
                invoice_id = self._extract_id(path, "/api/invoices/", suffix="/actions/handoff")
                if invoice_id is None:
                    return self._not_found()
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    invoice = self.invoice_service.handoff_invoice(
                        invoice_id,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                        handoff_target=payload.get("handoff_target"),
                        handoff_note=payload.get("handoff_note"),
                    )
                except PermissionError as error:
                    return self._send_json({"error": str(error)}, status=403)
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not invoice:
                    return self._send_json({"error": "Nie znaleziono faktury."}, status=404)
                return self._send_json(invoice)

            if path.startswith("/api/invoices/") and path.endswith("/actions/reopen"):
                invoice_id = self._extract_id(path, "/api/invoices/", suffix="/actions/reopen")
                if invoice_id is None:
                    return self._not_found()
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    invoice = self.invoice_service.reopen_invoice(
                        invoice_id,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                        reason=payload.get("reason"),
                    )
                except PermissionError as error:
                    return self._send_json({"error": str(error)}, status=403)
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not invoice:
                    return self._send_json({"error": "Nie znaleziono faktury."}, status=404)
                return self._send_json(invoice)

            if path.startswith("/api/invoices/") and path.endswith("/actions/close"):
                invoice_id = self._extract_id(path, "/api/invoices/", suffix="/actions/close")
                if invoice_id is None:
                    return self._not_found()
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    invoice = self.invoice_service.close_invoice(
                        invoice_id,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                        reason=payload.get("reason"),
                    )
                except PermissionError as error:
                    return self._send_json({"error": str(error)}, status=403)
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not invoice:
                    return self._send_json({"error": "Nie znaleziono faktury."}, status=404)
                return self._send_json(invoice)

            if path.startswith("/api/invoices/") and path.endswith("/actions/reject-duplicate"):
                if user["role"] not in INVOICE_DECISION_ROLES:
                    return self._send_json({"error": "Ta rola nie moze zatwierdzac faktur po weryfikacji."}, status=403)
                invoice_id = self._extract_id(path, "/api/invoices/", suffix="/actions/reject-duplicate")
                if invoice_id is None:
                    return self._not_found()
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                invoice = self.invoice_service.reject_duplicate(
                    invoice_id,
                    actor=self._actor_label(user),
                    organization_id=organization_id,
                )
                if not invoice:
                    return self._send_json({"error": "Nie znaleziono faktury."}, status=404)
                return self._send_json(invoice)

            if path.startswith("/api/import/"):
                if not test_imports_enabled():
                    return self._send_json({"error": "Import testowy jest wyłączony w tym środowisku."}, status=403)
                source = path.removeprefix("/api/import/")
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                try:
                    invoice = self.invoice_service.import_mock(
                        source,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                except Exception as error:  # pragma: no cover
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(invoice, status=201)

            return self._not_found()

        def do_PATCH(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)

            if path == "/api/system/communication-settings":
                user = self._require_user(ORGANIZATION_SETTINGS_ROLES)
                if not user:
                    return
                payload = self._read_json()
                try:
                    self.system_settings_service.update_communication_settings(
                        payload,
                        actor_user=user,
                        actor_login=self._actor_label(user),
                    )
                    self.invoice_service.refresh_communication_adapters()
                    snapshot = self.system_settings_service.build_communication_settings_snapshot(
                        actor_user=user,
                        public_base_url=self._public_base_url(),
                    )
                except SystemSettingsError as error:
                    status = 403 if "Tylko Wlasciciel systemu" in str(error) else 400
                    return self._send_json({"error": str(error)}, status=status)
                return self._send_json(snapshot)

            if path == "/api/session/workspace-state":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                payload = self._read_json()
                try:
                    updated_user = self.auth_service.update_workspace_state(
                        user,
                        payload.get("workspace_state") or {},
                        device_id=self._device_id(),
                    )
                except AuthError as error:
                    return self._send_json({"error": str(error)}, status=400)
                self._cached_user = updated_user
                return self._send_json(updated_user)

            if path == "/api/organization-shared-note":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                payload = self._read_json()
                if any(key != "shared_note_text" for key in payload):
                    return self._send_json({"error": "Endpoint przyjmuje tylko pole shared_note_text."}, status=400)
                requested_organization_id = self._requested_organization_id(query)
                try:
                    note = self.organization_service.update_shared_note(
                        actor_user=user,
                        actor_login=self._actor_label(user),
                        requested_organization_id=requested_organization_id,
                        shared_note_text=payload.get("shared_note_text"),
                    )
                except (OrganizationError, OrganizationPermissionError) as error:
                    return self._handle_scope_error(error)
                return self._send_json(note)

            if path == "/api/user-personal-note":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                payload = self._read_json()
                if any(key != "personal_note_text" for key in payload):
                    return self._send_json({"error": "Endpoint przyjmuje tylko pole personal_note_text."}, status=400)
                try:
                    note = self.auth_service.update_personal_note(
                        user,
                        personal_note_text=payload.get("personal_note_text"),
                        actor_login=self._actor_label(user),
                    )
                except AuthError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(note)

            if path.startswith("/api/work-items/"):
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                work_item_id = self._extract_id(path, "/api/work-items/")
                if work_item_id is None:
                    return self._not_found()
                payload = self._read_json()
                try:
                    updated = self.work_item_service.update_work_item(
                        work_item_id,
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not updated:
                    return self._send_json({"error": "Nie znaleziono pozycji pracy."}, status=404)
                return self._send_json(updated)

            if path.startswith("/api/whiteboard/images/"):
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_whiteboard_scope(user, query, require_active=True)
                if organization_id is ...:
                    return
                image_event_id = self._extract_id(path, "/api/whiteboard/images/")
                if image_event_id is None:
                    return self._not_found()
                payload = self._read_json()
                try:
                    updated = self.whiteboard_service.update_image_transform(
                        organization_id=organization_id,
                        image_event_id=image_event_id,
                        placement={
                            "x": payload.get("x"),
                            "y": payload.get("y"),
                            "width": payload.get("width"),
                            "height": payload.get("height"),
                            "rotation_deg": payload.get("rotation_deg"),
                        },
                        actor_user=user,
                        actor=self._actor_label(user),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(updated)

            if path.startswith("/api/intake/forms/"):
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                form_id = self._extract_id(path, "/api/intake/forms/")
                if form_id is None:
                    return self._not_found()
                payload = self._read_json()
                try:
                    updated = self.intake_service.update_form(
                        form_id,
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not updated:
                    return self._send_json({"error": "Nie znaleziono formularza."}, status=404)
                return self._send_json(updated)

            if path.startswith("/api/intake/items/"):
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                item_id = self._extract_id(path, "/api/intake/items/")
                if item_id is None:
                    return self._not_found()
                payload = self._read_json()
                try:
                    updated = self.intake_service.update_item(
                        item_id,
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not updated:
                    return self._send_json({"error": "Nie znaleziono sprawy."}, status=404)
                return self._send_json(updated)

            if path.startswith("/api/dashboard/views/"):
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                view_id = self._extract_id(path, "/api/dashboard/views/")
                if view_id is None:
                    return self._not_found()
                payload = self._read_json()
                allowed_fields = {
                    "module_key",
                    "view_name",
                    "view_slug",
                    "description",
                    "view_state",
                    "view_state_json",
                    "is_shared",
                    "is_default",
                }
                if any(key not in allowed_fields for key in payload):
                    return self._send_json(
                        {
                            "error": (
                                "dashboard views przyjmuje tylko pola module_key, view_name, view_slug, "
                                "description, view_state, view_state_json, is_shared i is_default."
                            )
                        },
                        status=400,
                    )
                try:
                    updated = self.dashboard_view_service.update_view(
                        view_id,
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not updated:
                    return self._send_json({"error": "Nie znaleziono widoku."}, status=404)
                return self._send_json(updated)

            if path.startswith("/api/automation/rules/"):
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                rule_id = self._extract_id(path, "/api/automation/rules/")
                if rule_id is None:
                    return self._not_found()
                payload = self._read_json()
                try:
                    updated = self.automation_service.update_rule(
                        rule_id,
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not updated:
                    return self._send_json({"error": "Nie znaleziono reguly automatyzacji."}, status=404)
                return self._send_json(updated)

            if path.startswith("/api/organizations/"):
                user = self._require_user(ORGANIZATION_SETTINGS_ROLES)
                if not user:
                    return
                organization_id = self._extract_id(path, "/api/organizations/")
                if organization_id is None:
                    return self._not_found()
                payload = self._read_json()
                try:
                    updated = self.organization_service.update_organization(
                        organization_id,
                        payload,
                        actor_user=user,
                        actor_login=self._actor_label(user),
                    )
                except (OrganizationError, OrganizationPermissionError) as error:
                    return self._handle_scope_error(error)
                return self._send_json(updated)

            if path.startswith("/api/users/"):
                user = self._require_user(USER_MANAGEMENT_ROLES)
                if not user:
                    return
                user_id = self._extract_id(path, "/api/users/")
                if user_id is None:
                    return self._not_found()
                payload = self._read_json()
                try:
                    updated = self.auth_service.update_user(
                        user_id,
                        payload,
                        actor_login=self._actor_label(user),
                        actor_user=user,
                    )
                except PermissionError as error:
                    return self._send_json({"error": str(error)}, status=403)
                except AuthError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(updated)

            if path.startswith("/api/knowledge/documents/"):
                user = self._require_knowledge_manage_user()
                if not user:
                    return
                organization_id = self._resolve_knowledge_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                document_id = self._extract_id(path, "/api/knowledge/documents/")
                if document_id is None:
                    return self._not_found()
                payload = self._read_json()
                try:
                    updated = self.knowledge_service.update_document_metadata(
                        organization_id=organization_id,
                        knowledge_document_id=document_id,
                        actor_user=user,
                        actor=self._actor_label(user),
                        title=payload.get("title"),
                        library_path=payload.get("library_path"),
                        is_downloadable=self._parse_optional_bool(payload.get("is_downloadable")),
                        use_in_assistant=self._parse_optional_bool(payload.get("use_in_assistant")),
                        business_status=payload.get("business_status"),
                        owner_user_id=payload.get("owner_user_id", ...),
                        reviewer_user_id=payload.get("reviewer_user_id", ...),
                        approver_user_id=payload.get("approver_user_id", ...),
                    )
                except KnowledgeError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(updated)

            if path.startswith("/api/user-calendars/"):
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                user_calendar_id = self._extract_id(path, "/api/user-calendars/")
                if user_calendar_id is None:
                    return self._not_found()
                payload = self._read_json()
                allowed_fields = {
                    "display_name",
                    "description",
                    "provider",
                    "calendar_kind",
                    "linked_organization_id",
                    "default_duration_minutes",
                    "is_active",
                    "external_calendar_id",
                }
                if any(key not in allowed_fields for key in payload):
                    return self._send_json(
                        {
                            "error": (
                                "user-calendars przyjmuje tylko pola display_name, description, provider, "
                                "calendar_kind, linked_organization_id, default_duration_minutes, is_active "
                                "i external_calendar_id."
                            )
                        },
                        status=400,
                    )
                try:
                    updated = self.calendar_service.update_user_calendar(
                        user_calendar_id,
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        base_url=self._public_base_url(),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not updated:
                    return self._send_json({"error": "Nie znaleziono kalendarza."}, status=404)
                return self._send_json(updated)

            if path.startswith("/api/invoices/"):
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                invoice_id = self._extract_id(path, "/api/invoices/")
                if invoice_id is None:
                    return self._not_found()
                payload = self._read_json()
                try:
                    invoice = self.invoice_service.update_invoice(
                        invoice_id,
                        payload,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                        actor_user=user,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not invoice:
                    return self._send_json({"error": "Nie znaleziono faktury."}, status=404)
                return self._send_json(invoice)

            if path.startswith("/api/task-templates/"):
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                template_id = self._extract_id(path, "/api/task-templates/")
                if template_id is None:
                    return self._not_found()
                payload = self._read_json()
                try:
                    updated = self.task_service.update_task_template(
                        template_id,
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not updated:
                    return self._send_json({"error": "Nie znaleziono szablonu."}, status=404)
                return self._send_json(updated)

            if path.startswith("/api/tasks/") and "/checklist/" in path:
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                prefix = "/api/tasks/"
                checklist_prefix = "/checklist/"
                task_id_str = path[len(prefix) : path.index(checklist_prefix)]
                item_id_str = path[path.index(checklist_prefix) + len(checklist_prefix) :]
                try:
                    task_id = int(task_id_str)
                    item_id = int(item_id_str)
                except ValueError:
                    return self._not_found()
                try:
                    updated = self.task_service.toggle_task_checklist_item(
                        task_id,
                        item_id,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not updated:
                    return self._send_json({"error": "Nie znaleziono zadania."}, status=404)
                return self._send_json(updated)

            if path.startswith("/api/tasks/"):
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                task_id = self._extract_id(path, "/api/tasks/")
                if task_id is None:
                    return self._not_found()
                payload = self._read_json()
                try:
                    task = self.task_service.update_task(
                        task_id,
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not task:
                    return self._send_json({"error": "Nie znaleziono zadania."}, status=404)
                return self._send_json(task)

            return self._not_found()

        def do_DELETE(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)

            if path.startswith("/api/google-calendar/assignments/"):
                user = self._require_user(USER_MANAGEMENT_ROLES)
                if not user:
                    return
                target_user_id = self._extract_id(path, "/api/google-calendar/assignments/")
                if target_user_id is None:
                    return self._not_found()
                try:
                    deleted = self.calendar_service.remove_organization_calendar_assignment(
                        target_user_id,
                        actor_user=user,
                        actor=self._actor_label(user),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not deleted:
                    return self._send_json({"error": "Nie znaleziono przypisania kalendarza."}, status=404)
                return self._send_json({"ok": True})

            if path.startswith("/api/user-calendars/"):
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_manager_assistant_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                user_calendar_id = self._extract_id(path, "/api/user-calendars/")
                if user_calendar_id is None:
                    return self._not_found()
                deleted = self.calendar_service.delete_user_calendar(
                    user_calendar_id,
                    actor_user=user,
                    actor=self._actor_label(user),
                )
                if not deleted:
                    return self._send_json({"error": "Nie znaleziono kalendarza."}, status=404)
                return self._send_json({"ok": True})

            if path.startswith("/api/dashboard/views/"):
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                view_id = self._extract_id(path, "/api/dashboard/views/")
                if view_id is None:
                    return self._not_found()
                try:
                    deleted = self.dashboard_view_service.delete_view(
                        view_id,
                        organization_id=organization_id,
                        actor=self._actor_label(user),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not deleted:
                    return self._send_json({"error": "Nie znaleziono widoku."}, status=404)
                return self._send_json({"ok": True})

            if path.startswith("/api/automation/rules/"):
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                rule_id = self._extract_id(path, "/api/automation/rules/")
                if rule_id is None:
                    return self._not_found()
                try:
                    deleted = self.automation_service.delete_rule(
                        rule_id,
                        organization_id=organization_id,
                        actor=self._actor_label(user),
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not deleted:
                    return self._send_json({"error": "Nie znaleziono reguly automatyzacji."}, status=404)
                return self._send_json({"ok": True})

            if path.startswith("/api/intake/forms/"):
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                form_id = self._extract_id(path, "/api/intake/forms/")
                if form_id is None:
                    return self._not_found()
                deleted = self.intake_service.delete_form(
                    form_id,
                    actor_user=user,
                    organization_id=organization_id,
                    actor=self._actor_label(user),
                )
                if not deleted:
                    return self._send_json({"error": "Nie znaleziono formularza."}, status=404)
                return self._send_json({"ok": True})

            if path.startswith("/api/knowledge/documents/"):
                user = self._require_knowledge_manage_user()
                if not user:
                    return
                organization_id = self._resolve_knowledge_scope(user, query, require_write=True)
                if organization_id is ...:
                    return
                document_id = self._extract_id(path, "/api/knowledge/documents/")
                if document_id is None:
                    return self._not_found()
                try:
                    deleted = self.knowledge_service.delete_document(
                        organization_id=organization_id,
                        knowledge_document_id=document_id,
                        actor_user=user,
                        actor=self._actor_label(user),
                    )
                except KnowledgeError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(deleted)

            return self._not_found()

        def _serve_static(self, path: str) -> None:
            if path in {"/", ""}:
                target = STATIC_DIR / "index.html"
            else:
                target = STATIC_DIR / path.lstrip("/")
            if not target.exists() or not target.is_file():
                return self._not_found()

            content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
            data = target.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _is_public_static_path(self, path: str) -> bool:
            if not CASI_SERVE_LEGACY_STATIC:
                return False
            if path.startswith("/api/"):
                return False
            if self._match_storage_path(path):
                return False
            if path in {"/", ""}:
                return True
            target = STATIC_DIR / path.lstrip("/")
            return target.exists() and target.is_file()

        def _match_storage_path(self, path: str) -> tuple[str, str] | None:
            for artifact_type in ("document", "ocr", "knowledge", "whiteboard"):
                route_prefix = self.storage_service.route_prefix(artifact_type)
                if path.startswith(route_prefix):
                    return artifact_type, path.removeprefix(route_prefix)
            return None

        def _send_storage_file(self, artifact_type: str, storage_key: str, user: dict[str, Any]) -> None:
            normalized_key = storage_key.lstrip("/")
            if not self._can_access_storage_path(normalized_key, user):
                return self._send_json({"error": "Brak dostępu do plików innej organizacji."}, status=403)

            if artifact_type == "knowledge":
                if not self.auth_service.has_capability(user, KNOWLEDGE_DOWNLOAD_CAPABILITY):
                    return self._send_json({"error": "To konto nie ma prawa pobierać plików firmowych."}, status=403)
                organization_id = self._organization_id_from_storage_key(normalized_key)
                if organization_id is not None:
                    document = self.knowledge_service.knowledge_repository.get_by_storage_key(organization_id, normalized_key)
                    if document and str(document.get("lifecycle_status") or "active") == "deleted":
                        return self._send_json({"error": "Nie mozna pobrac usunietego dokumentu."}, status=410)
                    if document:
                        self.knowledge_service.record_document_download(
                            organization_id=organization_id,
                            knowledge_document_id=int(document["knowledge_document_id"]),
                            actor_user=user,
                            actor=self._actor_label(user),
                        )

            try:
                data = self.storage_service.read_binary(artifact_type, normalized_key)
            except StorageNotFoundError:
                return self._not_found()
            except StorageError:
                return self._send_json({"error": "Nieprawidlowa sciezka pliku."}, status=400)
            content_type = mimetypes.guess_type(normalized_key)[0] or "text/plain; charset=utf-8"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _can_access_storage_path(self, relative_path: str, user: dict[str, Any]) -> bool:
            if user.get("is_global_admin"):
                return True
            organization_slug = str(user.get("organization_slug") or "").strip()
            if not organization_slug:
                return False
            normalized_parts = Path(relative_path).parts
            return len(normalized_parts) >= 2 and normalized_parts[0] == "organizacje" and normalized_parts[1] == organization_slug

        def _organization_id_from_storage_key(self, storage_key: str) -> int | None:
            parts = Path(storage_key).parts
            if len(parts) < 2 or parts[0] != "organizacje":
                return None
            organization = self.organization_service.organization_repository.get_by_slug(parts[1])
            return int(organization["organization_id"]) if organization else None

        def _send_json(self, payload: Any, status: int = 200, extra_headers: list[tuple[str, str]] | None = None) -> None:
            data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            if extra_headers:
                for key, value in extra_headers:
                    self.send_header(key, value)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _send_text(
            self,
            text: str,
            *,
            content_type: str,
            download_name: str | None = None,
            status: int = 200,
        ) -> None:
            data = text.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            if download_name:
                self.send_header("Content-Disposition", f'inline; filename="{download_name}"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _read_body_bytes(self) -> bytes:
            length = int(self.headers.get("Content-Length", "0"))
            if length == 0:
                return b""
            return self.rfile.read(length)

        def _read_json(self) -> dict[str, Any]:
            raw = self._read_body_bytes()
            if not raw:
                return {}
            return json.loads(raw.decode("utf-8"))

        def _read_multipart_form(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            content_type = self.headers.get("Content-Type", "")
            if length == 0 or not content_type:
                return {}

            raw = self.rfile.read(length)
            envelope = f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8") + raw
            message = BytesParser(policy=default).parsebytes(envelope)
            payload: dict[str, Any] = {}

            for part in message.iter_parts():
                if part.get_content_disposition() != "form-data":
                    continue
                field_name = part.get_param("name", header="content-disposition")
                if not field_name:
                    continue
                file_name = part.get_filename()
                content = part.get_payload(decode=True) or b""
                if file_name is not None:
                    payload[field_name] = {
                        "file_name": file_name,
                        "content_type": part.get_content_type(),
                        "content": content,
                    }
                    continue
                charset = part.get_content_charset() or "utf-8"
                payload[field_name] = content.decode(charset, errors="replace")

            return payload

        def _public_base_url(self) -> str:
            if PUBLIC_BASE_URL:
                return PUBLIC_BASE_URL
            forwarded_proto = (self.headers.get("X-Forwarded-Proto") or "").strip()
            proto = forwarded_proto or ("https" if SECURE_COOKIES else "http")
            host = (self.headers.get("X-Forwarded-Host") or self.headers.get("Host") or "").strip()
            if not host:
                host = f"{self.server.server_address[0]}:{self.server.server_address[1]}"
            return f"{proto}://{host}".rstrip("/")

        def _query_one(self, query: dict[str, list[str]], key: str) -> str:
            values = query.get(key)
            return values[0] if values else ""

        def _requested_organization_id(self, query: dict[str, list[str]]) -> int | None:
            raw = self._query_one(query, "organization_id").strip()
            if not raw:
                return None
            return int(raw) if raw.isdigit() else None

        def _parse_optional_int(self, value: str) -> int | None:
            normalized = str(value or "").strip()
            return int(normalized) if normalized.isdigit() else None

        def _parse_optional_bool(self, value: Any, default: bool | None = None) -> bool | None:
            if value is None:
                return default
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            normalized = str(value).strip().lower()
            if normalized in {"1", "true", "tak", "yes", "on"}:
                return True
            if normalized in {"0", "false", "nie", "no", "off"}:
                return False
            return default

        def _resolve_data_scope(self, user: dict[str, Any], query: dict[str, list[str]]) -> int | None | Ellipsis:
            try:
                return self.organization_service.resolve_data_scope(user, self._requested_organization_id(query))
            except (OrganizationError, OrganizationPermissionError) as error:
                self._handle_scope_error(error)
                return ...

        def _resolve_write_scope(self, user: dict[str, Any], query: dict[str, list[str]]) -> int | None | Ellipsis:
            try:
                return self.organization_service.resolve_write_scope(user, self._requested_organization_id(query))
            except (OrganizationError, OrganizationPermissionError) as error:
                self._handle_scope_error(error)
                return ...

        def _resolve_knowledge_scope(
            self,
            user: dict[str, Any],
            query: dict[str, list[str]],
            require_write: bool = False,
        ) -> int | Ellipsis:
            resolver = self._resolve_write_scope if require_write else self._resolve_data_scope
            organization_id = resolver(user, query)
            if organization_id is ...:
                return ...
            if organization_id is None:
                self._send_json({"error": "Wybierz konkretną organizację dla modułu bazy wiedzy."}, status=400)
                return ...
            return int(organization_id)

        def _resolve_support_scope(self, user: dict[str, Any], query: dict[str, list[str]]) -> int | Ellipsis:
            organization_id = self._resolve_data_scope(user, query)
            if organization_id is ...:
                return ...
            if organization_id is None:
                self._send_json({"error": "Wybierz konkretna organizacje, aby otworzyc modul Pomoc."}, status=400)
                return ...
            return int(organization_id)

        def _resolve_whiteboard_scope(
            self,
            user: dict[str, Any],
            query: dict[str, list[str]],
            *,
            require_active: bool,
        ) -> int | Ellipsis:
            resolver = self._resolve_write_scope if require_active else self._resolve_data_scope
            organization_id = resolver(user, query)
            if organization_id is ...:
                return ...
            if organization_id is None:
                self._send_json({"error": "Wybierz konkretna organizacje dla wspolnej tablicy."}, status=400)
                return ...
            return int(organization_id)

        def _role_can_use_manager_assistant_workspace(self, user: dict[str, Any]) -> bool:
            return user.get("role") in MANAGER_ASSISTANT_WORKSPACE_ROLES

        def _role_can_open_manager_assistant_manager_view(self, user: dict[str, Any]) -> bool:
            return user.get("role") in MANAGER_ASSISTANT_MANAGER_ROLES

        def _manager_assistant_enabled_for_scope(self, organization_id: int | None) -> bool:
            if organization_id is None:
                return False
            return self.organization_service.organization_has_module(int(organization_id), MANAGER_ASSISTANT_MODULE)

        def _resolve_manager_assistant_scope(
            self,
            user: dict[str, Any],
            query: dict[str, list[str]],
            require_write: bool = False,
        ) -> int | Ellipsis:
            resolver = self._resolve_write_scope if require_write else self._resolve_data_scope
            organization_id = resolver(user, query)
            if organization_id is ...:
                return ...
            if organization_id is None:
                self._send_json({"error": "Wybierz konkretna organizacje dla modulu Asystent Szefa."}, status=400)
                return ...
            if not self._role_can_use_manager_assistant_workspace(user):
                self._send_json({"error": "To konto nie ma dostepu do obszaru Moja praca."}, status=403)
                return ...
            if not self._manager_assistant_enabled_for_scope(int(organization_id)):
                self._send_json(
                    {"error": "Ta organizacja nie ma wlaczonego modulu Asystent Szefa i sekcji Moja praca."},
                    status=403,
                )
                return ...
            return int(organization_id)

        def _filter_dashboard_snapshot(
            self,
            snapshot: dict[str, Any],
            organization_id: int | None,
        ) -> dict[str, Any]:
            if self._manager_assistant_enabled_for_scope(organization_id):
                return snapshot
            filtered_snapshot = dict(snapshot or {})
            cards = dict(filtered_snapshot.get("cards") or {})
            cards["aktywne_przypomnienia"] = 0
            filtered_snapshot["cards"] = cards
            filtered_snapshot["active_reminders"] = []
            filtered_snapshot["recent_events"] = [
                item
                for item in list(filtered_snapshot.get("recent_events") or [])
                if not str(item.get("event_type") or "").startswith("task_")
            ]
            return filtered_snapshot

        def _build_system_health_snapshot(
            self,
            organization_id: int | None,
            *,
            viewer_user: dict[str, Any] | None = None,
        ) -> dict[str, Any]:
            org = self.organization_service.organization_repository.get_by_id(organization_id) if organization_id else None
            reminder_status = self.task_reminder_service.integration_status(organization_id=organization_id)
            inbox_forms = self.intake_service.list_forms(organization_id=organization_id, include_inactive=True)
            inbox_items = self.intake_service.list_items(organization_id=organization_id, limit=500)
            views = self.dashboard_view_service.list_views("health", organization_id=organization_id, include_hidden=True)
            automation_rules = self.automation_service.list_rules(
                organization_id=organization_id,
                include_inactive=True,
            )
            automation_executions = self.automation_service.list_executions(
                organization_id=organization_id,
                limit=50,
            )
            balances = self.billing_ledger_service.list_balances(organization_id=organization_id)
            matches = self.billing_ledger_service.list_payment_matches(organization_id=organization_id, limit=50)
            pending_approvals = self.approval_service.list_requests(
                organization_id=organization_id,
                status="pending",
                limit=20,
                viewer_user=viewer_user,
            )

            inbox_counts = {
                "forms": len(inbox_forms),
                "items": len(inbox_items),
                "new_items": sum(1 for item in inbox_items if str(item.get("status") or "") == "nowe"),
                "in_progress": sum(1 for item in inbox_items if str(item.get("status") or "") == "w_toku"),
                "waiting": sum(1 for item in inbox_items if str(item.get("status") or "") == "oczekuje"),
                "done": sum(1 for item in inbox_items if str(item.get("status") or "") == "zakonczone"),
            }
            billing_overdue = [row for row in balances if float(row.get("balance_due") or 0) > 0]

            return {
                "generated_at": now_iso(),
                "organization": {
                    "organization_id": org.get("organization_id") if org else organization_id,
                    "name": org.get("name") if org else None,
                    "slug": org.get("slug") if org else None,
                },
                "worker": reminder_status,
                "inbox": {
                    "counts": inbox_counts,
                    "recent_forms": inbox_forms[:6],
                    "recent_items": inbox_items[:10],
                },
                "saved_views": {
                    "count": len(views),
                    "views": views[:10],
                },
                "automations": {
                    "rules_count": len(automation_rules),
                    "active_rules_count": sum(1 for rule in automation_rules if int(rule.get("is_active") or 0) == 1),
                    "execution_count": len(automation_executions),
                    "recent_rules": automation_rules[:8],
                    "recent_executions": automation_executions[:10],
                },
                "billing": {
                    "payer_count": len(balances),
                    "overdue_count": len(billing_overdue),
                    "total_balance_due": round(sum(float(row.get("balance_due") or 0) for row in balances), 2),
                    "recent_balances": balances[:10],
                    "recent_matches": matches[:10],
                },
                "approvals": {
                    "pending_count": len(pending_approvals),
                    "pending_requests": pending_approvals[:10],
                },
                "summary": {
                    "health_views": len(views),
                    "worker_online": any(
                        str(worker.get("state") or "").strip().lower() != "error"
                        for worker in (reminder_status.get("workers") or [])
                    )
                    if isinstance(reminder_status, dict)
                    else False,
                    "inbox_items": inbox_counts["items"],
                    "overdue_billing": len(billing_overdue),
                    "pending_approvals": len(pending_approvals),
                    "automation_rules": len(automation_rules),
                },
            }

        def _handle_scope_error(self, error: Exception) -> None:
            status = 403 if isinstance(error, OrganizationPermissionError) else 400
            self._send_json({"error": str(error)}, status=status)

        def _extract_id(self, path: str, prefix: str, suffix: str = "") -> int | None:
            value = path.removeprefix(prefix)
            if suffix and value.endswith(suffix):
                value = value[: -len(suffix)]
            value = value.strip("/")
            return int(value) if value.isdigit() else None

        def _require_user(self, allowed_roles: tuple[str, ...]) -> dict[str, Any] | None:
            try:
                self.auth_service.require_role(self.current_user, allowed_roles)
            except PermissionError as error:
                status = 401 if not self.current_user else 403
                self._send_json({"error": str(error)}, status=status)
                return None
            return self.current_user

        def _require_knowledge_upload_user(self) -> dict[str, Any] | None:
            user = self._require_user(WRITE_ROLES)
            if not user:
                return None
            if self.auth_service.has_capability(user, KNOWLEDGE_UPLOAD_CAPABILITY):
                return user
            self._send_json(
                {"error": "To konto nie ma uprawnienia do dodawania plików do bazy wiedzy."},
                status=403,
            )
            return None

        def _require_knowledge_read_user(self) -> dict[str, Any] | None:
            user = self._require_user(READ_ROLES)
            if not user:
                return None
            if self.auth_service.has_capability(user, KNOWLEDGE_READ_CAPABILITY):
                return user
            self._send_json({"error": "To konto nie ma dostępu do bazy wiedzy."}, status=403)
            return None

        def _require_knowledge_download_user(self) -> dict[str, Any] | None:
            user = self._require_knowledge_read_user()
            if not user:
                return None
            if self.auth_service.has_capability(user, KNOWLEDGE_DOWNLOAD_CAPABILITY):
                return user
            self._send_json({"error": "To konto nie ma prawa pobierac plikow firmowych."}, status=403)
            return None

        def _require_knowledge_assistant_user(self) -> dict[str, Any] | None:
            user = self._require_knowledge_read_user()
            if not user:
                return None
            if self.auth_service.has_capability(user, KNOWLEDGE_ASSISTANT_USE_CAPABILITY):
                return user
            self._send_json({"error": "To konto nie ma prawa korzystac z asystenta dokumentow."}, status=403)
            return None

        def _require_knowledge_sync_user(self) -> dict[str, Any] | None:
            user = self._require_user(WRITE_ROLES)
            if not user:
                return None
            if self.auth_service.has_capability(user, KNOWLEDGE_SYNC_CAPABILITY):
                return user
            self._send_json(
                {"error": "To konto nie ma uprawnienia do dodawania plików do bazy wiedzy ani synchronizacji folderu."},
                status=403,
            )
            return None

        def _require_knowledge_manage_user(self) -> dict[str, Any] | None:
            user = self._require_user(WRITE_ROLES)
            if not user:
                return None
            if self.auth_service.has_capability(user, KNOWLEDGE_MANAGE_CAPABILITY):
                return user
            self._send_json(
                {"error": "To konto nie ma uprawnienia do zarządzania przetwarzaniem dokumentów."},
                status=403,
            )
            return None

        def _session_token(self) -> str | None:
            raw_cookie = self.headers.get("Cookie")
            if not raw_cookie:
                return None
            cookie = SimpleCookie()
            cookie.load(raw_cookie)
            morsel = cookie.get(SESSION_COOKIE_NAME)
            return morsel.value if morsel else None

        def _build_session_cookie(self, session_token: str) -> str:
            cookie = SimpleCookie()
            cookie[SESSION_COOKIE_NAME] = session_token
            cookie[SESSION_COOKIE_NAME]["path"] = "/"
            cookie[SESSION_COOKIE_NAME]["httponly"] = True
            cookie[SESSION_COOKIE_NAME]["samesite"] = "Lax"
            if SECURE_COOKIES:
                cookie[SESSION_COOKIE_NAME]["secure"] = True
            cookie[SESSION_COOKIE_NAME]["max-age"] = str(SESSION_DURATION_HOURS * 3600)
            return cookie.output(header="").strip()

        def _build_clear_cookie(self) -> str:
            cookie = SimpleCookie()
            cookie[SESSION_COOKIE_NAME] = ""
            cookie[SESSION_COOKIE_NAME]["path"] = "/"
            cookie[SESSION_COOKIE_NAME]["httponly"] = True
            cookie[SESSION_COOKIE_NAME]["samesite"] = "Lax"
            if SECURE_COOKIES:
                cookie[SESSION_COOKIE_NAME]["secure"] = True
            cookie[SESSION_COOKIE_NAME]["expires"] = "Thu, 01 Jan 1970 00:00:00 GMT"
            cookie[SESSION_COOKIE_NAME]["max-age"] = "0"
            return cookie.output(header="").strip()

        def _client_ip(self) -> str | None:
            return self.client_address[0] if self.client_address else None

        def _device_id(self) -> str | None:
            return (self.headers.get("X-CASI-Device-Id") or "").strip() or None

        def _device_label(self) -> str | None:
            return (self.headers.get("X-CASI-Device-Label") or "").strip() or None

        def _actor_label(self, user: dict[str, Any]) -> str:
            return user.get("display_name") or user["login"]

        def _not_found(self) -> None:
            self._send_json({"error": "Nie znaleziono zasobu."}, status=404)

    return ThreadingHTTPServer((host, port), InvoiceOpsHandler)
