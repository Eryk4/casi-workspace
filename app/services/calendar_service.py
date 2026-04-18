from __future__ import annotations

from datetime import datetime, timedelta, timezone
import secrets
from typing import Any
from zoneinfo import ZoneInfo

from app.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, PUBLIC_BASE_URL, google_calendar_direct_enabled
from app.domain.constants import (
    CALENDAR_KIND_LABELS,
    CALENDAR_KINDS,
    ORGANIZATION_ADMIN_ROLE,
    OWNER_CALENDAR_KINDS,
    SYSTEM_OWNER_ROLE,
    WORKER_CALENDAR_KINDS,
)
from app.integrations.google_calendar_api import GoogleCalendarApiAdapter, GoogleCalendarIntegrationError
from app.repositories.calendar_repository import CalendarRepository
from app.repositories.event_repository import EventRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository
from app.utils import now_iso

CALENDAR_PROVIDERS = ("google_api", "google_ics")
LOCAL_TIMEZONE = "Europe/Warsaw"


class CalendarService:
    def __init__(
        self,
        calendar_repository: CalendarRepository,
        user_repository: UserRepository,
        organization_repository: OrganizationRepository,
        event_repository: EventRepository,
        google_adapter: GoogleCalendarApiAdapter | None = None,
    ) -> None:
        self.calendar_repository = calendar_repository
        self.user_repository = user_repository
        self.organization_repository = organization_repository
        self.event_repository = event_repository
        self.google_adapter = google_adapter or GoogleCalendarApiAdapter()

    def list_user_calendars(self, actor_user: dict[str, Any], *, base_url: str | None = None) -> list[dict[str, Any]]:
        calendars = self.calendar_repository.list_visible_user_calendars(int(actor_user["user_id"]))
        allowed_owned_kinds = set(self._allowed_calendar_kinds_for_user(actor_user))
        visible: list[dict[str, Any]] = []
        for item in calendars:
            access_mode = str(item.get("access_mode") or "owner")
            calendar_kind = str(item.get("calendar_kind") or "inne")
            if access_mode == "owner" and calendar_kind not in allowed_owned_kinds:
                continue
            visible.append(self._decorate_calendar(item, base_url=base_url))
        return visible

    def get_user_calendar_options(self, actor_user: dict[str, Any], *, base_url: str | None = None) -> list[dict[str, Any]]:
        return [item for item in self.list_user_calendars(actor_user, base_url=base_url) if item.get("is_active")]

    def get_google_connection_status(self, actor_user: dict[str, Any]) -> dict[str, Any]:
        client_id_ready = bool(GOOGLE_CLIENT_ID)
        client_secret_ready = bool(GOOGLE_CLIENT_SECRET)
        public_base_url_ready = bool(PUBLIC_BASE_URL)
        oauth_ready = client_id_ready and client_secret_ready and public_base_url_ready
        enabled = google_calendar_direct_enabled() and self.google_adapter.is_enabled()
        connection = self.calendar_repository.get_google_connection(int(actor_user["user_id"]))
        calendars = self.calendar_repository.list_visible_user_calendars(int(actor_user["user_id"]))
        mapped_owned = [
            item
            for item in calendars
            if str(item.get("provider") or "") == "google_api" and str(item.get("access_mode") or "owner") == "owner"
        ]
        assignment = self.calendar_repository.get_assignment_for_user(int(actor_user["user_id"]))
        assigned_calendar = None
        if assignment:
            assigned_calendar_raw = self.calendar_repository.get_by_id_for_user(
                int(assignment["user_calendar_id"]),
                int(actor_user["user_id"]),
            )
            if assigned_calendar_raw:
                assigned_calendar = self._decorate_calendar(assigned_calendar_raw)
        approval_status = str(connection.get("approval_status") or "").strip() if connection else ""
        approved = approval_status == "approved"
        pending_approval = approval_status == "pending_approval"
        checks = [
            {"code": "google_client_id", "label": "Google Client ID", "ok": client_id_ready},
            {"code": "google_client_secret", "label": "Google Client Secret", "ok": client_secret_ready},
            {"code": "public_base_url", "label": "Publiczny adres aplikacji", "ok": public_base_url_ready},
            {"code": "oauth_ready", "label": "Gotowosc OAuth Google", "ok": oauth_ready},
            {"code": "account_connected", "label": "Konto Google zapisane", "ok": bool(connection)},
            {"code": "account_approved", "label": "Konto Google zatwierdzone", "ok": approved},
            {
                "code": "mapped_calendars",
                "label": "Wlasne kalendarze Google",
                "ok": bool(mapped_owned),
                "details": str(len(mapped_owned)),
            },
        ]
        missing_items = [item["label"] for item in checks if not item["ok"]]
        return {
            "enabled": enabled,
            "configured": oauth_ready,
            "connection_exists": bool(connection),
            "connected": approved,
            "approved": approved,
            "approval_pending": pending_approval,
            "approval_status": approval_status or ("approved" if approved else "disconnected"),
            "google_email": connection.get("google_email") if connection else None,
            "token_expires_at": connection.get("token_expires_at") if connection else None,
            "employee_visibility_confirmed": bool(connection.get("employee_visibility_confirmed")) if connection else False,
            "employee_confirmation_at": connection.get("employee_confirmation_at") if connection else None,
            "approved_by_login": connection.get("approved_by_login") if connection else None,
            "approved_by_display_name": connection.get("approved_by_display_name") if connection else None,
            "approved_at": connection.get("approved_at") if connection else None,
            "callback_url": self.google_adapter.callback_url() if enabled else None,
            "mapped_calendar_count": len(mapped_owned),
            "assigned_calendar": assigned_calendar,
            "client_id_ready": client_id_ready,
            "client_secret_ready": client_secret_ready,
            "public_base_url_ready": public_base_url_ready,
            "oauth_ready": oauth_ready,
            "ready_for_direct_sync": approved and bool(mapped_owned) and enabled,
            "missing_items": missing_items,
            "setup_checks": checks,
        }

    def begin_google_calendar_connection(
        self,
        actor_user: dict[str, Any],
        *,
        confirm_work_account_visibility: bool,
    ) -> dict[str, Any]:
        if not google_calendar_direct_enabled() or not self.google_adapter.is_enabled():
            raise ValueError(
                "Integracja Google Calendar nie jest jeszcze skonfigurowana. Brakuje danych OAuth albo publicznego adresu aplikacji."
            )
        if not confirm_work_account_visibility:
            raise ValueError(
                "Potwierdz, ze podlaczasz konto uzywane do pracy w tej organizacji i ze adres bedzie widoczny dla administratora."
            )
        self.calendar_repository.clear_expired_google_oauth_states(now_iso())
        state_token = secrets.token_urlsafe(24)
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=20)).replace(microsecond=0).isoformat()
        self.calendar_repository.create_google_oauth_state(int(actor_user["user_id"]), state_token, expires_at)
        return {
            "authorization_url": self.google_adapter.build_authorization_url(state_token),
            "expires_at": expires_at,
            "state_token": state_token,
        }

    def finalize_google_calendar_connection(
        self,
        state_token: str,
        code: str | None,
        error_code: str | None = None,
    ) -> dict[str, Any]:
        if error_code:
            raise ValueError("Polaczenie z Google zostalo anulowane lub odrzucone.")
        if not code:
            raise ValueError("Google nie zwrocilo kodu autoryzacyjnego.")
        state = self.calendar_repository.consume_google_oauth_state(state_token)
        if not state:
            raise ValueError("Link polaczenia z Google jest nieaktualny albo zostal juz wykorzystany.")
        try:
            token_payload = self.google_adapter.exchange_code_for_tokens(code)
            user_info = self.google_adapter.fetch_user_info(token_payload["access_token"])
        except GoogleCalendarIntegrationError as error:
            raise ValueError(str(error)) from error
        timestamp = now_iso()
        self.calendar_repository.upsert_google_connection(
            int(state["user_id"]),
            {
                "google_email": user_info.get("email"),
                "access_token": token_payload["access_token"],
                "refresh_token": token_payload.get("refresh_token"),
                "token_expires_at": token_payload["token_expires_at"],
                "scope": token_payload.get("scope"),
                "employee_visibility_confirmed": 1,
                "employee_confirmation_at": timestamp,
                "approval_status": "pending_approval",
                "approved_by_user_id": None,
                "approved_at": None,
            },
        )
        user = self.user_repository.get_by_id(int(state["user_id"]))
        if not user:
            raise ValueError("Nie znaleziono uzytkownika do polaczenia Google Calendar.")
        auto_approved = str(user.get("role") or "") in {SYSTEM_OWNER_ROLE, ORGANIZATION_ADMIN_ROLE}
        if auto_approved:
            self.calendar_repository.approve_google_connection(int(user["user_id"]), int(user["user_id"]))
        self.event_repository.log(
            event_type="google_calendar_connection_approved" if auto_approved else "google_calendar_connection_pending",
            invoice_id=None,
            organization_id=user.get("organization_id"),
            source="GOOGLE_CALENDAR",
            status_before="rozlaczone",
            status_after="zatwierdzone" if auto_approved else "oczekuje_na_zatwierdzenie",
            decision_reason=(
                "Podlaczono i zatwierdzono konto Google Calendar uzytkownika."
                if auto_approved
                else "Podlaczono konto Google Calendar. Czeka na zatwierdzenie przez administratora."
            ),
            actor=user.get("login") or "system",
            details={
                "user_id": user["user_id"],
                "google_email": user_info.get("email"),
                "approval_status": "approved" if auto_approved else "pending_approval",
            },
        )
        return self.get_google_connection_status(user)

    def disconnect_google_calendar(self, actor_user: dict[str, Any], *, actor: str) -> dict[str, Any]:
        self.calendar_repository.delete_google_connection(int(actor_user["user_id"]))
        self._downgrade_owned_google_api_calendars(int(actor_user["user_id"]))
        self.event_repository.log(event_type="google_calendar_disconnected", invoice_id=None, organization_id=actor_user.get("organization_id"), source="GOOGLE_CALENDAR", status_before="polaczone", status_after="rozlaczone", decision_reason="Rozlaczono konto Google Calendar uzytkownika.", actor=actor, details={"user_id": actor_user["user_id"]})
        return self.get_google_connection_status(actor_user)

    def approve_google_calendar_connection(
        self,
        target_user_id: int,
        *,
        actor_user: dict[str, Any],
        actor: str,
    ) -> dict[str, Any]:
        target_user = self._get_user_for_calendar_admin_action(target_user_id, actor_user)
        connection = self.calendar_repository.get_google_connection(int(target_user_id))
        if not connection:
            raise ValueError("Ten uzytkownik nie ma podlaczonego konta Google.")
        approved = self.calendar_repository.approve_google_connection(int(target_user_id), int(actor_user["user_id"]))
        if not approved:
            raise ValueError("Nie udalo sie zatwierdzic konta Google.")
        self.event_repository.log(
            event_type="google_calendar_connection_approved",
            invoice_id=None,
            organization_id=target_user.get("organization_id"),
            source="GOOGLE_CALENDAR",
            status_before=str(connection.get("approval_status") or "pending_approval"),
            status_after="approved",
            decision_reason="Administrator zatwierdzil konto Google pracownika.",
            actor=actor,
            details={"user_id": target_user_id, "google_email": connection.get("google_email")},
        )
        return self.get_google_connection_status(target_user)

    def reject_google_calendar_connection(
        self,
        target_user_id: int,
        *,
        actor_user: dict[str, Any],
        actor: str,
    ) -> dict[str, Any]:
        target_user = self._get_user_for_calendar_admin_action(target_user_id, actor_user)
        connection = self.calendar_repository.get_google_connection(int(target_user_id))
        if not connection:
            raise ValueError("Ten uzytkownik nie ma podlaczonego konta Google.")
        downgraded_count = self._downgrade_owned_google_api_calendars(int(target_user_id))
        self.calendar_repository.delete_google_connection(int(target_user_id))
        self.event_repository.log(
            event_type="google_calendar_connection_rejected",
            invoice_id=None,
            organization_id=target_user.get("organization_id"),
            source="GOOGLE_CALENDAR",
            status_before=str(connection.get("approval_status") or "pending_approval"),
            status_after="rejected",
            decision_reason="Administrator odrzucil albo odlaczyl konto Google pracownika.",
            actor=actor,
            details={
                "user_id": target_user_id,
                "google_email": connection.get("google_email"),
                "downgraded_calendar_count": downgraded_count,
            },
        )
        return self.get_google_connection_status(target_user)

    def assign_organization_calendar_to_user(
        self,
        target_user_id: int,
        user_calendar_id: int,
        *,
        actor_user: dict[str, Any],
        actor: str,
        base_url: str | None = None,
    ) -> dict[str, Any]:
        target_user = self._get_user_for_calendar_admin_action(target_user_id, actor_user)
        target_organization_id = self._as_int(target_user.get("organization_id"))
        if target_organization_id is None:
            raise ValueError("Ten uzytkownik nie ma przypisanej organizacji.")
        calendar = self.calendar_repository.get_by_id(user_calendar_id)
        if not calendar or not calendar.get("is_active"):
            raise ValueError("Mozesz przypisac tylko aktywny kalendarz organizacji.")
        if str(calendar.get("calendar_kind") or "") != "organizacja":
            raise ValueError("Przypisac mozna tylko kalendarz organizacji.")
        if self._as_int(calendar.get("linked_organization_id")) != target_organization_id:
            raise ValueError("Mozesz przypisac tylko kalendarz z tej samej organizacji co uzytkownik.")
        self.calendar_repository.assign_calendar_to_user(
            user_id=int(target_user_id),
            user_calendar_id=int(user_calendar_id),
            assigned_by_user_id=int(actor_user["user_id"]),
        )
        assigned_calendar = self.calendar_repository.get_by_id_for_user(int(user_calendar_id), int(target_user_id))
        assert assigned_calendar is not None
        self.event_repository.log(
            event_type="organization_calendar_assigned",
            invoice_id=None,
            organization_id=target_user.get("organization_id"),
            source="GOOGLE_CALENDAR",
            status_before=None,
            status_after="assigned",
            decision_reason="Przypisano kalendarz organizacji do uzytkownika.",
            actor=actor,
            details={
                "user_id": target_user_id,
                "user_calendar_id": user_calendar_id,
                "calendar_name": calendar.get("display_name"),
            },
        )
        return self._decorate_calendar(assigned_calendar, base_url=base_url)

    def remove_organization_calendar_assignment(
        self,
        target_user_id: int,
        *,
        actor_user: dict[str, Any],
        actor: str,
    ) -> bool:
        target_user = self._get_user_for_calendar_admin_action(target_user_id, actor_user)
        assignment = self.calendar_repository.get_assignment_for_user(int(target_user_id))
        if not assignment:
            return False
        self.calendar_repository.delete_assignment_for_user(int(target_user_id))
        self.event_repository.log(
            event_type="organization_calendar_assignment_removed",
            invoice_id=None,
            organization_id=target_user.get("organization_id"),
            source="GOOGLE_CALENDAR",
            status_before="assigned",
            status_after="removed",
            decision_reason="Usunieto przypisanie kalendarza organizacji dla uzytkownika.",
            actor=actor,
            details={
                "user_id": target_user_id,
                "user_calendar_id": assignment.get("user_calendar_id"),
                "calendar_name": assignment.get("assigned_calendar_name"),
            },
        )
        return True

    def list_google_connection_admin_snapshot(
        self,
        actor_user: dict[str, Any],
        *,
        requested_organization_id: int | None = None,
        base_url: str | None = None,
    ) -> list[dict[str, Any]]:
        organization_id = self._resolve_calendar_admin_scope(actor_user, requested_organization_id)
        users = self.user_repository.list_users(organization_id=organization_id)
        user_ids = [int(item["user_id"]) for item in users]
        connections_map = {
            int(item["user_id"]): item
            for item in self.calendar_repository.list_google_connections(
                organization_id=organization_id,
                user_ids=user_ids,
            )
        }
        assignments_map = {
            int(item["user_id"]): item
            for item in self.calendar_repository.list_assignments(
                user_ids=user_ids,
                organization_id=organization_id,
            )
        }
        result: list[dict[str, Any]] = []
        for user in users:
            user_id = int(user["user_id"])
            connection = connections_map.get(user_id)
            assignment = assignments_map.get(user_id)
            decorated_assignment = None
            if assignment:
                assigned_calendar = self.calendar_repository.get_by_id_for_user(
                    int(assignment["user_calendar_id"]),
                    user_id,
                )
                if assigned_calendar:
                    decorated_assignment = self._decorate_calendar(assigned_calendar, base_url=base_url)
            approval_status = str(connection.get("approval_status") or "").strip() if connection else ""
            result.append(
                {
                    "user_id": user_id,
                    "google_connection_exists": bool(connection),
                    "google_connection_status": approval_status or "disconnected",
                    "google_connection_email": connection.get("google_email") if connection else None,
                    "google_connection_employee_visibility_confirmed": bool(connection.get("employee_visibility_confirmed")) if connection else False,
                    "google_connection_employee_confirmation_at": connection.get("employee_confirmation_at") if connection else None,
                    "google_connection_approved_by_login": connection.get("approved_by_login") if connection else None,
                    "google_connection_approved_by_display_name": connection.get("approved_by_display_name") if connection else None,
                    "google_connection_approved_at": connection.get("approved_at") if connection else None,
                    "assigned_organization_calendar": decorated_assignment,
                    "assigned_organization_calendar_id": decorated_assignment.get("user_calendar_id") if decorated_assignment else None,
                    "assigned_organization_calendar_name": decorated_assignment.get("display_name") if decorated_assignment else None,
                }
            )
        return result

    def list_assignable_organization_calendars(
        self,
        actor_user: dict[str, Any],
        *,
        requested_organization_id: int | None = None,
        base_url: str | None = None,
    ) -> list[dict[str, Any]]:
        organization_id = self._resolve_calendar_admin_scope(actor_user, requested_organization_id)
        if organization_id is None:
            return []
        calendars = self.calendar_repository.list_organization_calendars(int(organization_id))
        return [self._decorate_calendar(item, base_url=base_url) for item in calendars]

    def list_external_google_calendars(self, actor_user: dict[str, Any]) -> list[dict[str, Any]]:
        connection = self._ensure_google_connection(int(actor_user["user_id"]))
        try:
            calendars = self.google_adapter.list_calendars(connection["access_token"])
        except GoogleCalendarIntegrationError as error:
            raise ValueError(str(error)) from error
        linked = {str(item.get("external_calendar_id") or ""): item for item in self.calendar_repository.list_user_calendars(int(actor_user["user_id"])) if str(item.get("provider") or "") == "google_api" and str(item.get("external_calendar_id") or "").strip()}
        for item in calendars:
            existing = linked.get(str(item.get("external_calendar_id") or ""))
            item["mapped_user_calendar_id"] = existing.get("user_calendar_id") if existing else None
            item["mapped_display_name"] = existing.get("display_name") if existing else None
        return calendars

    def has_google_connection(self, user_id: int) -> bool:
        return bool(self.calendar_repository.get_google_connection(user_id))

    def create_user_calendar(self, payload: dict[str, Any], *, actor_user: dict[str, Any], actor: str, base_url: str | None = None) -> dict[str, Any]:
        owner_user_id = int(actor_user["user_id"])
        display_name = str(payload.get("display_name") or "").strip()
        description = str(payload.get("description") or "").strip() or None
        provider = self._normalize_provider(payload.get("provider"))
        calendar_kind = self._normalize_calendar_kind(payload.get("calendar_kind"))
        self._ensure_calendar_kind_allowed(calendar_kind, actor_user)
        linked_organization_id = self._validate_linked_organization(payload.get("linked_organization_id"), calendar_kind=calendar_kind, actor_user=actor_user)
        default_duration_minutes = self._normalize_minutes(payload.get("default_duration_minutes"), default=60)
        is_active = 1 if payload.get("is_active", True) not in {False, 0, "0", "false"} else 0
        if not display_name:
            raise ValueError("Nazwa kalendarza jest wymagana.")
        self._ensure_unique_display_name(owner_user_id, display_name)
        external_calendar_id = None
        external_calendar_name = None
        external_calendar_timezone = None
        if provider == "google_api":
            connection = self._ensure_google_connection(owner_user_id)
            external_calendar_id = str(payload.get("external_calendar_id") or "").strip()
            if not external_calendar_id:
                raise ValueError("Wybierz docelowy kalendarz Google dla trybu bezposredniego.")
            external_target = self._resolve_external_calendar_details(connection["access_token"], external_calendar_id)
            external_calendar_name = external_target["external_calendar_name"]
            external_calendar_timezone = external_target["external_calendar_timezone"]
        user_calendar_id = self.calendar_repository.create({"owner_user_id": owner_user_id, "provider": provider, "display_name": display_name, "calendar_kind": calendar_kind, "linked_organization_id": linked_organization_id, "default_duration_minutes": default_duration_minutes, "description": description, "sync_token": secrets.token_urlsafe(24), "external_calendar_id": external_calendar_id, "external_calendar_name": external_calendar_name, "external_calendar_timezone": external_calendar_timezone, "is_active": is_active})
        created = self.calendar_repository.get_by_id(user_calendar_id)
        assert created is not None
        self.event_repository.log(event_type="user_calendar_created", invoice_id=None, organization_id=actor_user.get("organization_id"), source="GOOGLE_CALENDAR", status_before=None, status_after="aktywne" if is_active else "nieaktywne", decision_reason=f"Dodano kalendarz uzytkownika: {display_name}.", actor=actor, details={"user_calendar_id": user_calendar_id, "owner_user_id": owner_user_id, "display_name": display_name, "provider": provider, "calendar_kind": calendar_kind})
        return self._decorate_calendar(created, base_url=base_url)

    def update_user_calendar(self, user_calendar_id: int, payload: dict[str, Any], *, actor_user: dict[str, Any], actor: str, base_url: str | None = None) -> dict[str, Any] | None:
        current = self.calendar_repository.get_by_id_for_owner(user_calendar_id, int(actor_user["user_id"]))
        if not current:
            return None
        updates: dict[str, Any] = {}
        next_provider = str(current.get("provider") or "google_ics")
        next_calendar_kind = str(current.get("calendar_kind") or "inne")
        if "display_name" in payload:
            display_name = str(payload.get("display_name") or "").strip()
            if not display_name:
                raise ValueError("Nazwa kalendarza jest wymagana.")
            self._ensure_unique_display_name(int(actor_user["user_id"]), display_name, exclude_id=user_calendar_id)
            if display_name != current["display_name"]:
                updates["display_name"] = display_name
        if "provider" in payload:
            next_provider = self._normalize_provider(payload.get("provider"))
            if next_provider != str(current.get("provider") or "google_ics"):
                updates["provider"] = next_provider
        if "calendar_kind" in payload:
            next_calendar_kind = self._normalize_calendar_kind(payload.get("calendar_kind"))
            self._ensure_calendar_kind_allowed(next_calendar_kind, actor_user)
            if next_calendar_kind != str(current.get("calendar_kind") or "inne"):
                updates["calendar_kind"] = next_calendar_kind
        if "linked_organization_id" in payload or "calendar_kind" in payload:
            linked_organization_id = self._validate_linked_organization(payload.get("linked_organization_id", current.get("linked_organization_id")), calendar_kind=next_calendar_kind, actor_user=actor_user)
            if self._as_int(current.get("linked_organization_id")) != linked_organization_id:
                updates["linked_organization_id"] = linked_organization_id
        if "default_duration_minutes" in payload:
            default_duration_minutes = self._normalize_minutes(payload.get("default_duration_minutes"), default=int(current.get("default_duration_minutes") or 60))
            if int(current.get("default_duration_minutes") or 60) != default_duration_minutes:
                updates["default_duration_minutes"] = default_duration_minutes
        if "description" in payload:
            description = str(payload.get("description") or "").strip() or None
            if description != current.get("description"):
                updates["description"] = description
        if "is_active" in payload:
            is_active = 1 if payload.get("is_active", True) not in {False, 0, "0", "false"} else 0
            if int(current.get("is_active") or 0) != is_active:
                updates["is_active"] = is_active
        if next_provider == "google_api":
            external_calendar_id = str(payload.get("external_calendar_id") if "external_calendar_id" in payload else current.get("external_calendar_id") or "").strip()
            if "provider" in payload or "external_calendar_id" in payload:
                connection = self._ensure_google_connection(int(actor_user["user_id"]))
                if not external_calendar_id:
                    raise ValueError("Wybierz docelowy kalendarz Google dla trybu bezposredniego.")
                external_target = self._resolve_external_calendar_details(connection["access_token"], external_calendar_id)
                updates["external_calendar_id"] = external_calendar_id
                updates["external_calendar_name"] = external_target["external_calendar_name"]
                updates["external_calendar_timezone"] = external_target["external_calendar_timezone"]
        elif any(current.get(key) for key in ("external_calendar_id", "external_calendar_name", "external_calendar_timezone")):
            updates["external_calendar_id"] = None
            updates["external_calendar_name"] = None
            updates["external_calendar_timezone"] = None
        if updates:
            self.calendar_repository.update(user_calendar_id, updates)
            refreshed = self.calendar_repository.get_by_id(user_calendar_id)
            assert refreshed is not None
            self.event_repository.log(event_type="user_calendar_updated", invoice_id=None, organization_id=actor_user.get("organization_id"), source="GOOGLE_CALENDAR", status_before=None, status_after="aktywne" if refreshed.get("is_active") else "nieaktywne", decision_reason=f"Zmieniono kalendarz uzytkownika: {refreshed['display_name']}.", actor=actor, details={"user_calendar_id": user_calendar_id, "updates": list(updates.keys())})
            return self._decorate_calendar(refreshed, base_url=base_url)
        return self._decorate_calendar(current, base_url=base_url)

    def delete_user_calendar(self, user_calendar_id: int, *, actor_user: dict[str, Any], actor: str) -> bool:
        current = self.calendar_repository.get_by_id_for_owner(user_calendar_id, int(actor_user["user_id"]))
        if not current:
            return False
        self.calendar_repository.delete(user_calendar_id)
        self.event_repository.log(event_type="user_calendar_deleted", invoice_id=None, organization_id=actor_user.get("organization_id"), source="GOOGLE_CALENDAR", status_before="aktywne" if current.get("is_active") else "nieaktywne", status_after="usuniete", decision_reason=f"Usunieto kalendarz uzytkownika: {current['display_name']}.", actor=actor, details={"user_calendar_id": user_calendar_id})
        return True

    def get_reminder_preferences(self, actor_user: dict[str, Any]) -> dict[str, Any]:
        refreshed = self.user_repository.get_by_id(int(actor_user["user_id"]))
        if not refreshed:
            raise ValueError("Nie znaleziono uzytkownika.")
        return self._build_reminder_preferences(refreshed)

    def update_reminder_preferences(self, payload: dict[str, Any], *, actor_user: dict[str, Any], actor: str) -> dict[str, Any]:
        current = self.user_repository.get_by_id(int(actor_user["user_id"]))
        if not current:
            raise ValueError("Nie znaleziono uzytkownika.")
        quiet_start = self._normalize_optional_time(payload.get("quiet_hours_start"))
        quiet_end = self._normalize_optional_time(payload.get("quiet_hours_end"))
        repeat_interval = self._normalize_repeat_interval(payload.get("repeat_interval_minutes"))
        telegram_reminders_enabled = 1 if payload.get("telegram_reminders_enabled", True) not in {False, 0, "0", "false"} else 0
        browser_notifications_enabled = 1 if payload.get("browser_notifications_enabled", False) in {True, 1, "1", "true", "tak", "on"} else 0
        self.user_repository.update(
            int(actor_user["user_id"]),
            {
                "telegram_reminders_enabled": telegram_reminders_enabled,
                "browser_notifications_enabled": browser_notifications_enabled,
                "reminder_quiet_hours_start": quiet_start,
                "reminder_quiet_hours_end": quiet_end,
                "reminder_repeat_interval_minutes": repeat_interval,
            },
        )
        refreshed = self.user_repository.get_by_id(int(actor_user["user_id"]))
        assert refreshed is not None
        self.event_repository.log(
            event_type="user_reminder_preferences_updated",
            invoice_id=None,
            organization_id=actor_user.get("organization_id"),
            source="TELEGRAM",
            status_before=None,
            status_after=None,
            decision_reason=f"Zmieniono ustawienia przypomnien uzytkownika {refreshed['login']}.",
            actor=actor,
            details={
                "user_id": refreshed["user_id"],
                "telegram_reminders_enabled": telegram_reminders_enabled,
                "browser_notifications_enabled": browser_notifications_enabled,
                "quiet_hours_start": quiet_start,
                "quiet_hours_end": quiet_end,
                "repeat_interval_minutes": repeat_interval,
            },
        )
        return self._build_reminder_preferences(refreshed)

    def validate_calendar_for_user(self, user_calendar_id: int | None, actor_user: dict[str, Any]) -> dict[str, Any] | None:
        if user_calendar_id is None:
            return None
        calendar = self.calendar_repository.get_by_id_for_user(user_calendar_id, int(actor_user["user_id"]))
        if not calendar or not calendar.get("is_active"):
            raise ValueError("Mozesz wybrac tylko aktywny kalendarz dostepny dla Ciebie.")
        access_mode = str(calendar.get("access_mode") or "owner")
        calendar_kind = str(calendar.get("calendar_kind") or "inne")
        if access_mode == "owner" and calendar_kind not in set(self._allowed_calendar_kinds_for_user(actor_user)):
            raise ValueError("Ten typ kalendarza nie jest dostepny dla Twojej roli w systemie.")
        return self._decorate_calendar(calendar)

    def build_calendar_feed(self, sync_token: str) -> tuple[str, str] | None:
        calendar = self.calendar_repository.get_by_sync_token(sync_token)
        if not calendar:
            return None
        if str(calendar.get("provider") or "google_ics") != "google_ics":
            return None
        tasks = self.calendar_repository.list_tasks_for_calendar(int(calendar["user_calendar_id"]))
        content = self._build_ics_document(calendar, tasks)
        return content, str(calendar["display_name"])

    def sync_task_to_google(self, task: dict[str, Any]) -> dict[str, Any] | None:
        if str(task.get("calendar_provider") or "google_ics") != "google_api":
            return None
        external_calendar_id = str(task.get("calendar_external_calendar_id") or "").strip()
        if not external_calendar_id:
            raise ValueError("Wybrany kalendarz nie ma przypisanego docelowego kalendarza Google.")
        connection_user_id = self._google_connection_user_id_for_task(task)
        connection = self._ensure_google_connection(connection_user_id)
        event_payload = self._build_google_event_payload(task)
        event_id = str(task.get("external_calendar_event_id") or "").strip() or None
        try:
            response = self.google_adapter.upsert_event(connection["access_token"], external_calendar_id=external_calendar_id, event_id=event_id, event_payload=event_payload)
        except GoogleCalendarIntegrationError as error:
            raise ValueError(str(error)) from error
        remote_event_id = str(response.get("id") or event_id or "").strip()
        remote_updated_at = str(response.get("updated") or "").strip() or None
        remote_etag = str(response.get("etag") or "").strip() or None
        remote_event_url = str(response.get("htmlLink") or "").strip() or None
        return {
            "external_calendar_event_id": remote_event_id or None,
            "external_calendar_event_url": remote_event_url,
            "external_calendar_synced_at": now_iso(),
            "external_calendar_sync_error": None,
            "external_calendar_sync_state": "zsynchronizowano",
            "external_calendar_sync_message": "Wpis zapisano w Google Calendar z aplikacji.",
            "external_calendar_last_checked_at": now_iso(),
            "external_calendar_last_check_error": None,
            "external_calendar_remote_updated_at": remote_updated_at,
            "external_calendar_remote_etag": remote_etag,
            "external_calendar_last_sync_source": "app",
        }

    def inspect_task_google_sync(self, task: dict[str, Any]) -> dict[str, Any]:
        if str(task.get("calendar_provider") or "google_ics") != "google_api":
            raise ValueError("Sprawdzenie stanu Google Calendar jest dostepne tylko dla bezposredniego polaczenia.")
        external_calendar_id = str(task.get("calendar_external_calendar_id") or "").strip()
        if not external_calendar_id:
            raise ValueError("Wybrany kalendarz nie ma przypisanego docelowego kalendarza Google.")
        checked_at = now_iso()
        event_id = str(task.get("external_calendar_event_id") or "").strip()
        if not event_id:
            return {
                "external_calendar_sync_error": None,
                "external_calendar_sync_state": "oczekuje_synchronizacji",
                "external_calendar_sync_message": "Wpis nie ma jeszcze powiazanego wydarzenia Google.",
                "external_calendar_last_checked_at": checked_at,
                "external_calendar_last_check_error": None,
                "external_calendar_last_sync_source": "app",
            }
        connection_user_id = self._google_connection_user_id_for_task(task)
        connection = self._ensure_google_connection(connection_user_id)
        try:
            remote_event = self.google_adapter.get_event(
                connection["access_token"],
                external_calendar_id=external_calendar_id,
                event_id=event_id,
            )
        except GoogleCalendarIntegrationError as error:
            raise ValueError(str(error)) from error

        if not remote_event:
            return {
                "external_calendar_event_id": None,
                "external_calendar_event_url": None,
                "external_calendar_sync_error": None,
                "external_calendar_sync_state": "brak_w_google",
                "external_calendar_sync_message": "Nie znaleziono wydarzenia w Google Calendar. Kolejna synchronizacja utworzy je od nowa.",
                "external_calendar_last_checked_at": checked_at,
                "external_calendar_last_check_error": None,
                "external_calendar_remote_updated_at": None,
                "external_calendar_remote_etag": None,
                "external_calendar_last_sync_source": "google",
            }

        expected_snapshot = self._normalize_google_event_snapshot(self._build_google_event_payload(task))
        remote_snapshot = self._normalize_google_event_snapshot(remote_event)
        differences = self._compare_google_event_snapshots(expected_snapshot, remote_snapshot)
        remote_updated_at = str(remote_event.get("updated") or "").strip() or None
        remote_etag = str(remote_event.get("etag") or "").strip() or None
        remote_event_url = str(remote_event.get("htmlLink") or "").strip() or task.get("external_calendar_event_url") or None
        if differences:
            return {
                "external_calendar_event_url": remote_event_url,
                "external_calendar_sync_error": None,
                "external_calendar_sync_state": "wymaga_uwagi",
                "external_calendar_sync_message": f"Roznice w Google Calendar: {', '.join(differences)}.",
                "external_calendar_last_checked_at": checked_at,
                "external_calendar_last_check_error": None,
                "external_calendar_remote_updated_at": remote_updated_at,
                "external_calendar_remote_etag": remote_etag,
                "external_calendar_last_sync_source": "google",
            }

        return {
            "external_calendar_event_url": remote_event_url,
            "external_calendar_sync_error": None,
            "external_calendar_sync_state": "zsynchronizowano",
            "external_calendar_sync_message": "Dane w Google sa zgodne z aplikacja.",
            "external_calendar_last_checked_at": checked_at,
            "external_calendar_last_check_error": None,
            "external_calendar_remote_updated_at": remote_updated_at,
            "external_calendar_remote_etag": remote_etag,
            "external_calendar_last_sync_source": "google",
        }

    def remove_task_from_google(self, task: dict[str, Any]) -> None:
        if str(task.get("calendar_provider") or "") != "google_api":
            return
        external_calendar_id = str(task.get("calendar_external_calendar_id") or "").strip()
        event_id = str(task.get("external_calendar_event_id") or "").strip()
        if not external_calendar_id or not event_id:
            return
        connection_user_id = self._google_connection_user_id_for_task(task)
        connection = self.calendar_repository.get_google_connection(connection_user_id)
        if not connection:
            return
        try:
            connection = self._ensure_google_connection(connection_user_id)
            self.google_adapter.delete_event(connection["access_token"], external_calendar_id=external_calendar_id, event_id=event_id)
        except (ValueError, GoogleCalendarIntegrationError):
            return

    def _build_ics_document(self, calendar: dict[str, Any], tasks: list[dict[str, Any]]) -> str:
        lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//CASI//Asystent Szefa//PL", "CALSCALE:GREGORIAN", "METHOD:PUBLISH", f"X-WR-CALNAME:{self._escape_ics_text(str(calendar['display_name']))}", "X-WR-TIMEZONE:Europe/Warsaw"]
        for task in tasks:
            event_block = self._build_ics_event(calendar, task)
            if event_block:
                lines.extend(event_block)
        lines.append("END:VCALENDAR")
        return "\r\n".join(lines) + "\r\n"

    def _build_ics_event(self, calendar: dict[str, Any], task: dict[str, Any]) -> list[str] | None:
        start_value = str(task.get("due_at") or task.get("remind_at") or "").strip()
        if not start_value:
            return None
        start_at = self._parse_local_datetime(start_value)
        if start_at is None:
            return None
        end_at = start_at + timedelta(minutes=self._resolve_duration_minutes(task))
        status = "CANCELLED" if str(task.get("status") or "") == "anulowane" else "CONFIRMED"
        updated_at = self._parse_iso_datetime(str(task.get("updated_at") or task.get("created_at") or now_iso()))
        created_at = self._parse_iso_datetime(str(task.get("created_at") or now_iso()))
        description_lines = [f"Typ: {self._task_type_label(str(task.get('task_type') or ''))}", f"Organizacja: {task.get('organization_name') or '-'}", f"Wlasciciel: {task.get('owner_user_name') or '-'}"]
        if task.get("assigned_user_name"):
            description_lines.append(f"Przypisano: {task['assigned_user_name']}")
        if task.get("description"):
            description_lines.extend(["", str(task["description"])])
        return ["BEGIN:VEVENT", f"UID:task-{task['task_id']}-calendar-{calendar['user_calendar_id']}@casi-workspace", f"DTSTAMP:{self._format_ics_timestamp(updated_at or datetime.utcnow())}", f"CREATED:{self._format_ics_timestamp(created_at or datetime.utcnow())}", f"LAST-MODIFIED:{self._format_ics_timestamp(updated_at or datetime.utcnow())}", f"SUMMARY:{self._escape_ics_text(str(task.get('title') or 'Wpis'))}", f"DESCRIPTION:{self._escape_ics_text(chr(10).join(description_lines))}", f"DTSTART;TZID=Europe/Warsaw:{self._format_ics_local(start_at)}", f"DTEND;TZID=Europe/Warsaw:{self._format_ics_local(end_at)}", f"STATUS:{status}", f"CATEGORIES:{self._escape_ics_text(self._task_type_label(str(task.get('task_type') or '')))}", "END:VEVENT"]

    def _build_google_event_payload(self, task: dict[str, Any]) -> dict[str, Any]:
        start_value = str(task.get("due_at") or task.get("remind_at") or "").strip()
        if not start_value:
            raise ValueError("Aby zsynchronizowac wpis z Google Calendar, ustaw termin albo przypomnienie.")
        start_at = self._parse_local_datetime(start_value)
        if start_at is None:
            raise ValueError("Nieprawidlowy termin wpisu dla synchronizacji Google Calendar.")
        end_at = start_at + timedelta(minutes=self._resolve_duration_minutes(task))
        description_lines = [f"Typ: {self._task_type_label(str(task.get('task_type') or ''))}", f"Organizacja: {task.get('organization_name') or '-'}", f"Wlasciciel: {task.get('owner_user_name') or '-'}"]
        if task.get("assigned_user_name"):
            description_lines.append(f"Przypisano: {task['assigned_user_name']}")
        if task.get("description"):
            description_lines.extend(["", str(task["description"])])
        local_zone = ZoneInfo(LOCAL_TIMEZONE)
        return {"summary": str(task.get("title") or "Wpis"), "description": "\n".join(description_lines), "start": {"dateTime": start_at.replace(tzinfo=local_zone).isoformat(), "timeZone": LOCAL_TIMEZONE}, "end": {"dateTime": end_at.replace(tzinfo=local_zone).isoformat(), "timeZone": LOCAL_TIMEZONE}, "status": "cancelled" if str(task.get("status") or "") == "anulowane" else "confirmed"}

    def _normalize_google_event_snapshot(self, payload: dict[str, Any]) -> dict[str, str | None]:
        start_payload = payload.get("start") if isinstance(payload.get("start"), dict) else {}
        end_payload = payload.get("end") if isinstance(payload.get("end"), dict) else {}
        return {
            "summary": self._normalize_compare_text(payload.get("summary")),
            "description": self._normalize_compare_text(payload.get("description")),
            "start": self._normalize_google_datetime(start_payload.get("dateTime")),
            "end": self._normalize_google_datetime(end_payload.get("dateTime")),
            "status": self._normalize_compare_text(payload.get("status")),
        }

    def _compare_google_event_snapshots(
        self,
        expected: dict[str, str | None],
        remote: dict[str, str | None],
    ) -> list[str]:
        differences: list[str] = []
        if expected.get("summary") != remote.get("summary"):
            differences.append("tytul")
        if expected.get("description") != remote.get("description"):
            differences.append("opis")
        if expected.get("start") != remote.get("start") or expected.get("end") != remote.get("end"):
            differences.append("termin")
        if expected.get("status") != remote.get("status"):
            differences.append("status")
        return differences

    def _resolve_duration_minutes(self, task: dict[str, Any]) -> int:
        for raw_duration in (task.get("calendar_duration_minutes"), task.get("calendar_default_duration_minutes"), task.get("default_duration_minutes")):
            try:
                duration = int(raw_duration)
            except (TypeError, ValueError):
                duration = 0
            if duration > 0:
                return duration
        task_type = str(task.get("task_type") or "")
        if task_type == "przypomnienie":
            return 15
        if task_type == "zadanie":
            return 30
        return 60

    def _ensure_unique_display_name(self, owner_user_id: int, display_name: str, exclude_id: int | None = None) -> None:
        for item in self.calendar_repository.list_user_calendars(owner_user_id):
            if exclude_id is not None and int(item["user_calendar_id"]) == int(exclude_id):
                continue
            if str(item.get("display_name") or "").strip().lower() == display_name.lower():
                raise ValueError("Masz juz kalendarz o takiej nazwie.")

    def _build_reminder_preferences(self, user: dict[str, Any]) -> dict[str, Any]:
        return {
            "telegram_reminders_enabled": int(
                user.get("telegram_reminders_enabled") if user.get("telegram_reminders_enabled") is not None else 1
            ),
            "browser_notifications_enabled": int(user.get("browser_notifications_enabled") or 0),
            "quiet_hours_start": user.get("reminder_quiet_hours_start"),
            "quiet_hours_end": user.get("reminder_quiet_hours_end"),
            "repeat_interval_minutes": int(user.get("reminder_repeat_interval_minutes") or 0),
        }

    def _decorate_calendar(self, calendar: dict[str, Any], *, base_url: str | None = None) -> dict[str, Any]:
        result = dict(calendar)
        provider = str(result.get("provider") or "google_ics")
        calendar_kind = str(result.get("calendar_kind") or "inne")
        access_mode = str(result.get("access_mode") or "owner")
        result["provider"] = provider
        result["provider_label"] = self._provider_label(provider)
        result["calendar_kind"] = calendar_kind
        result["calendar_kind_label"] = self._calendar_kind_label(calendar_kind)
        result["access_mode"] = access_mode
        result["access_mode_label"] = {
            "owner": "Wlasny kalendarz",
            "assigned": "Przypisany kalendarz organizacji",
        }.get(access_mode, "Kalendarz")
        result["linked_organization_id"] = self._as_int(result.get("linked_organization_id"))
        result["default_duration_minutes"] = int(result.get("default_duration_minutes") or 60)
        result["feed_url"] = f"{base_url}/api/calendar-feeds/{calendar['sync_token']}.ics" if provider == "google_ics" and base_url else None
        return result

    def _ensure_google_connection(self, user_id: int) -> dict[str, Any]:
        connection = self.calendar_repository.get_google_connection(user_id)
        if not connection:
            raise ValueError("Najpierw polacz swoje konto Google Calendar.")
        approval_status = str(connection.get("approval_status") or "").strip()
        if approval_status != "approved":
            if approval_status == "pending_approval":
                raise ValueError("To konto Google Calendar czeka jeszcze na zatwierdzenie przez administratora.")
            raise ValueError("To konto Google Calendar nie jest zatwierdzone do uzycia w systemie.")
        expires_at = self._parse_iso_datetime(str(connection.get("token_expires_at") or "").strip())
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        if expires_at and expires_at > now_utc:
            return connection
        refresh_token = str(connection.get("refresh_token") or "").strip()
        if not refresh_token:
            raise ValueError("Polaczenie Google Calendar wygaslo. Polacz konto ponownie.")
        try:
            refreshed = self.google_adapter.refresh_tokens(refresh_token)
        except GoogleCalendarIntegrationError as error:
            raise ValueError(str(error)) from error
        self.calendar_repository.upsert_google_connection(
            user_id,
            {
                "google_email": connection.get("google_email"),
                "access_token": refreshed["access_token"],
                "refresh_token": refreshed.get("refresh_token") or refresh_token,
                "token_expires_at": refreshed["token_expires_at"],
                "scope": refreshed.get("scope") or connection.get("scope"),
                "employee_visibility_confirmed": int(connection.get("employee_visibility_confirmed") or 0),
                "employee_confirmation_at": connection.get("employee_confirmation_at"),
                "approval_status": approval_status or "approved",
                "approved_by_user_id": connection.get("approved_by_user_id"),
                "approved_at": connection.get("approved_at"),
            },
        )
        updated = self.calendar_repository.get_google_connection(user_id)
        if not updated:
            raise ValueError("Nie udalo sie odswiezyc polaczenia Google Calendar.")
        return updated

    def _resolve_calendar_admin_scope(
        self,
        actor_user: dict[str, Any],
        requested_organization_id: int | None,
    ) -> int | None:
        role = str(actor_user.get("role") or "")
        actor_organization_id = self._as_int(actor_user.get("organization_id"))
        if role == SYSTEM_OWNER_ROLE:
            return requested_organization_id
        if role == ORGANIZATION_ADMIN_ROLE:
            if requested_organization_id is not None and actor_organization_id != requested_organization_id:
                raise ValueError("Administrator organizacji moze pracowac tylko na swojej organizacji.")
            if actor_organization_id is None:
                raise ValueError("Administrator organizacji nie ma przypisanej organizacji.")
            return actor_organization_id
        raise ValueError("To konto nie moze zarzadzac polaczeniami Google Calendar innych uzytkownikow.")

    def _get_user_for_calendar_admin_action(
        self,
        target_user_id: int,
        actor_user: dict[str, Any],
    ) -> dict[str, Any]:
        target_user = self.user_repository.get_by_id(int(target_user_id))
        if not target_user:
            raise ValueError("Nie znaleziono wskazanego uzytkownika.")
        role = str(actor_user.get("role") or "")
        if role == SYSTEM_OWNER_ROLE:
            return target_user
        if role != ORGANIZATION_ADMIN_ROLE:
            raise ValueError("To konto nie moze zarzadzac polaczeniami Google Calendar innych uzytkownikow.")
        actor_organization_id = self._as_int(actor_user.get("organization_id"))
        target_organization_id = self._as_int(target_user.get("organization_id"))
        if actor_organization_id is None or target_organization_id is None or actor_organization_id != target_organization_id:
            raise ValueError("Mozesz zarzadzac tylko uzytkownikami ze swojej organizacji.")
        return target_user

    def _downgrade_owned_google_api_calendars(self, owner_user_id: int) -> int:
        downgraded_count = 0
        for calendar in self.calendar_repository.list_user_calendars(owner_user_id):
            if str(calendar.get("provider") or "") != "google_api":
                continue
            self.calendar_repository.update(
                int(calendar["user_calendar_id"]),
                {
                    "provider": "google_ics",
                    "external_calendar_id": None,
                    "external_calendar_name": None,
                    "external_calendar_timezone": None,
                },
            )
            downgraded_count += 1
        return downgraded_count

    def _google_connection_user_id_for_task(self, task: dict[str, Any]) -> int:
        owner_user_id = self._as_int(task.get("calendar_owner_user_id")) or self._as_int(task.get("owner_user_id"))
        if owner_user_id is None:
            raise ValueError("Nie mozna ustalic wlasciciela polaczenia Google Calendar dla tego wpisu.")
        return owner_user_id

    def _resolve_external_calendar_details(self, access_token: str, external_calendar_id: str) -> dict[str, str]:
        try:
            calendars = self.google_adapter.list_calendars(access_token)
        except GoogleCalendarIntegrationError as error:
            raise ValueError(str(error)) from error
        match = next((item for item in calendars if str(item.get("external_calendar_id") or "") == external_calendar_id), None)
        if not match:
            raise ValueError("Nie znaleziono wybranego kalendarza Google. Odswiez liste i sprobuj ponownie.")
        return {"external_calendar_name": str(match.get("external_calendar_name") or external_calendar_id), "external_calendar_timezone": str(match.get("external_calendar_timezone") or LOCAL_TIMEZONE)}

    def _normalize_provider(self, value: Any) -> str:
        normalized = str(value or "").strip() or "google_ics"
        if normalized not in CALENDAR_PROVIDERS:
            raise ValueError("Nieprawidlowy typ polaczenia kalendarza.")
        return normalized

    def _normalize_calendar_kind(self, value: Any) -> str:
        normalized = str(value or "").strip() or "inne"
        if normalized not in CALENDAR_KINDS:
            raise ValueError("Nieprawidlowy rodzaj kalendarza.")
        return normalized

    def _allowed_calendar_kinds_for_user(self, actor_user: dict[str, Any]) -> tuple[str, ...]:
        role = str(actor_user.get("role") or "")
        if role in {SYSTEM_OWNER_ROLE, ORGANIZATION_ADMIN_ROLE}:
            return OWNER_CALENDAR_KINDS
        return WORKER_CALENDAR_KINDS

    def _ensure_calendar_kind_allowed(self, calendar_kind: str, actor_user: dict[str, Any]) -> None:
        allowed_kinds = set(self._allowed_calendar_kinds_for_user(actor_user))
        if calendar_kind in allowed_kinds:
            return
        if calendar_kind in {"prywatny", "rodzinny"}:
            raise ValueError(
                "Kalendarz prywatny lub rodzinny moze zalozyc tylko Wlasciciel systemu albo Administrator organizacji."
            )
        if calendar_kind == "organizacja":
            raise ValueError(
                "Kalendarz dla calej organizacji moze zalozyc tylko Wlasciciel systemu albo Administrator organizacji."
            )
        raise ValueError("Ten rodzaj kalendarza nie jest dostepny dla Twojej roli.")

    def _validate_linked_organization(self, value: Any, *, calendar_kind: str, actor_user: dict[str, Any]) -> int | None:
        if calendar_kind != "organizacja":
            return None
        role = str(actor_user.get("role") or "")
        if role not in {SYSTEM_OWNER_ROLE, ORGANIZATION_ADMIN_ROLE}:
            raise ValueError(
                "Kalendarz dla calej organizacji moze zalozyc tylko Wlasciciel systemu albo Administrator organizacji."
            )
        organization_id = self._as_int(value) or self._as_int(actor_user.get("organization_id"))
        if organization_id is None:
            return None
        organization = self.organization_repository.get_by_id(organization_id)
        if not organization:
            raise ValueError("Wybrana organizacja kalendarza nie istnieje.")
        actor_organization_id = self._as_int(actor_user.get("organization_id"))
        if role == ORGANIZATION_ADMIN_ROLE and actor_organization_id is not None and actor_organization_id != organization_id:
            raise ValueError("Administrator organizacji moze powiazac kalendarz tylko ze swoja organizacja.")
        return organization_id

    def _normalize_minutes(self, value: Any, *, default: int) -> int:
        normalized = str(value or "").strip()
        if not normalized:
            return max(1, int(default))
        if not normalized.isdigit():
            raise ValueError("Czas kalendarza musi byc liczba minut.")
        return min(max(1, int(normalized)), 1440)

    def _provider_label(self, provider: str) -> str:
        return {"google_api": "Google Calendar bezposrednio", "google_ics": "Google Calendar przez adres URL"}.get(str(provider or "").strip(), "Google Calendar")

    def _calendar_kind_label(self, calendar_kind: str) -> str:
        return CALENDAR_KIND_LABELS.get(str(calendar_kind or "").strip(), "Inne")

    def _as_int(self, value: Any) -> int | None:
        normalized = str(value or "").strip()
        if not normalized:
            return None
        if not normalized.isdigit():
            raise ValueError("Nieprawidlowy identyfikator.")
        return int(normalized)

    def _normalize_optional_time(self, value: Any) -> str | None:
        normalized = str(value or "").strip()
        if not normalized:
            return None
        if len(normalized) != 5 or normalized[2] != ":":
            raise ValueError("Godzina ciszy nocnej musi miec format HH:MM.")
        hours, minutes = normalized.split(":", 1)
        if not (hours.isdigit() and minutes.isdigit()):
            raise ValueError("Godzina ciszy nocnej musi miec format HH:MM.")
        hours_int = int(hours)
        minutes_int = int(minutes)
        if hours_int not in range(24) or minutes_int not in range(60):
            raise ValueError("Godzina ciszy nocnej musi miec poprawny zakres.")
        return f"{hours_int:02d}:{minutes_int:02d}"

    def _normalize_repeat_interval(self, value: Any) -> int:
        normalized = str(value or "").strip()
        if not normalized:
            return 0
        if not normalized.isdigit():
            raise ValueError("Interwal ponowienia przypomnienia musi byc liczba minut.")
        minutes = int(normalized)
        if minutes < 0:
            raise ValueError("Interwal ponowienia przypomnienia nie moze byc ujemny.")
        return min(minutes, 1440)

    def _parse_local_datetime(self, value: str) -> datetime | None:
        try:
            return datetime.strptime(value, "%Y-%m-%dT%H:%M")
        except ValueError:
            return None

    def _parse_iso_datetime(self, value: str) -> datetime | None:
        normalized = value.strip()
        if not normalized:
            return None
        try:
            parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed

    def _normalize_google_datetime(self, value: Any) -> str | None:
        normalized = str(value or "").strip()
        if not normalized:
            return None
        parsed = self._parse_iso_datetime(normalized)
        if not parsed:
            return normalized
        return parsed.isoformat()

    def _normalize_compare_text(self, value: Any) -> str | None:
        normalized = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
        return normalized or None

    def _format_ics_local(self, value: datetime) -> str:
        return value.strftime("%Y%m%dT%H%M%S")

    def _format_ics_timestamp(self, value: datetime) -> str:
        return value.strftime("%Y%m%dT%H%M%SZ")

    def _escape_ics_text(self, value: str) -> str:
        return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n")

    def _task_type_label(self, task_type: str) -> str:
        return {"zadanie": "Zadanie", "wydarzenie": "Wydarzenie", "przypomnienie": "Przypomnienie", "notatka": "Notatka"}.get(task_type, "Wpis")
