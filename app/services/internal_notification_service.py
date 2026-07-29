from __future__ import annotations

import base64
import hashlib
import json
from datetime import date
from typing import Any

from app.domain.constants import SYSTEM_OWNER_ROLE
from app.repositories.event_repository import EventRepository
from app.repositories.internal_notification_repository import InternalNotificationRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository
from app.services.billing_service import BillingService
from app.services.organization_service import OrganizationService
from app.utils import current_local_date_value


INTERNAL_NOTIFICATION_SOURCE_BILLING_ATTENTION = "billing_next_step_attention"
INTERNAL_NOTIFICATION_FILTERS = {"inbox", "unread", "all", "archived"}
INTERNAL_NOTIFICATION_STATE_ACTIONS = {"read", "unread", "archived"}


class InternalNotificationNotFoundError(ValueError):
    pass


class InternalNotificationService:
    def __init__(
        self,
        *,
        repository: InternalNotificationRepository,
        billing_service: BillingService,
        event_repository: EventRepository,
        organization_repository: OrganizationRepository,
        organization_service: OrganizationService,
        user_repository: UserRepository,
    ) -> None:
        self.repository = repository
        self.billing_service = billing_service
        self.event_repository = event_repository
        self.organization_repository = organization_repository
        self.organization_service = organization_service
        self.user_repository = user_repository

    def materialize_billing_attention(
        self,
        *,
        organization_id: int,
        recipient_user_id: int,
        trigger_actor_user: dict[str, Any] | None,
        trigger_actor: str,
        as_of_date: str | date | None = None,
    ) -> dict[str, Any]:
        self._validate_recipient_scope(
            organization_id=organization_id,
            recipient_user_id=recipient_user_id,
            actor_user=trigger_actor_user,
            require_write=True,
        )
        reference_date = self._normalize_date(as_of_date)
        attention = self.billing_service.get_next_step_attention(
            organization_id=organization_id,
            as_of_date=reference_date,
        )
        created_ids: list[int] = []
        existing_ids: list[int] = []
        actor_user_id = int(trigger_actor_user["user_id"]) if trigger_actor_user else None
        for candidate in attention["candidates"]:
            source_event_id = int(candidate["billing_next_step_event_id"])
            reason_code = str(candidate["reason_code"])
            dedupe_key = self.build_dedupe_key(
                organization_id=organization_id,
                recipient_user_id=recipient_user_id,
                source_event_id=source_event_id,
                reason_code=reason_code,
            )
            stored, created = self.repository.create_notification(
                {
                    "organization_id": organization_id,
                    "recipient_user_id": recipient_user_id,
                    "source_type": INTERNAL_NOTIFICATION_SOURCE_BILLING_ATTENTION,
                    "source_event_id": source_event_id,
                    "reason_code": reason_code,
                    "detected_on": reference_date,
                    "planned_for": candidate.get("planned_for"),
                    "title_snapshot": str(candidate.get("title") or "Nastepny krok rozliczeniowy")[:200],
                    "target_type": str(candidate.get("target_type") or "billing_summary")[:60],
                    "target_id": candidate.get("target_id"),
                    "related_issue_key": str(candidate.get("related_issue_key") or "")[:300] or None,
                    "target_label_snapshot": str(candidate.get("target_label") or "Zrodlo historyczne")[:200],
                    "internal_link_snapshot": self._safe_internal_link(candidate.get("target_href")),
                    "dedupe_key": dedupe_key,
                    "created_by_user_id": actor_user_id,
                }
            )
            notification_id = int(stored["internal_notification_id"])
            (created_ids if created else existing_ids).append(notification_id)

        if created_ids:
            self.event_repository.log(
                event_type="internal_notifications_materialized",
                invoice_id=None,
                organization_id=organization_id,
                source="INTERNAL_NOTIFICATIONS",
                status_before=None,
                status_after="materialized",
                decision_reason="Jawnie sprawdzono nowe wewnetrzne powiadomienia.",
                actor=trigger_actor,
                details={
                    "recipient_user_id": recipient_user_id,
                    "source_type": INTERNAL_NOTIFICATION_SOURCE_BILLING_ATTENTION,
                    "candidates_count": len(attention["candidates"]),
                    "created_count": len(created_ids),
                    "existing_count": len(existing_ids),
                },
            )
        return {
            "organization_id": organization_id,
            "recipient_user_id": recipient_user_id,
            "as_of_date": reference_date,
            "candidates_count": len(attention["candidates"]),
            "created_count": len(created_ids),
            "existing_count": len(existing_ids),
            "created_notification_ids": created_ids,
        }

    def list_notifications(
        self,
        *,
        organization_id: int,
        recipient_user_id: int,
        actor_user: dict[str, Any],
        filter_name: str = "inbox",
        limit: int = 50,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        self._validate_recipient_scope(
            organization_id=organization_id,
            recipient_user_id=recipient_user_id,
            actor_user=actor_user,
            require_write=False,
        )
        normalized_filter = str(filter_name or "inbox").strip().lower()
        if normalized_filter not in INTERNAL_NOTIFICATION_FILTERS:
            raise ValueError("Nieprawidlowy filtr powiadomien.")
        normalized_limit = min(max(int(limit), 1), 100)
        cursor_values = self._decode_cursor(
            cursor,
            organization_id=organization_id,
            recipient_user_id=recipient_user_id,
            filter_name=normalized_filter,
        )
        rows = self.repository.list_notifications(
            organization_id=organization_id,
            recipient_user_id=recipient_user_id,
            filter_name=normalized_filter,
            limit=normalized_limit + 1,
            cursor_created_at=cursor_values[0] if cursor_values else None,
            cursor_notification_id=cursor_values[1] if cursor_values else None,
        )
        has_more = len(rows) > normalized_limit
        items = rows[:normalized_limit]
        next_cursor = None
        if has_more and items:
            last = items[-1]
            next_cursor = self._encode_cursor(
                organization_id=organization_id,
                recipient_user_id=recipient_user_id,
                filter_name=normalized_filter,
                created_at=str(last["created_at"]),
                notification_id=int(last["internal_notification_id"]),
            )
        return {
            "organization_id": organization_id,
            "recipient_user_id": recipient_user_id,
            "filter": normalized_filter,
            "limit": normalized_limit,
            "items": [self._serialize_notification(item) for item in items],
            "next_cursor": next_cursor,
            "has_more": has_more,
        }

    def unread_count(
        self,
        *,
        organization_id: int,
        recipient_user_id: int,
        actor_user: dict[str, Any],
    ) -> dict[str, Any]:
        self._validate_recipient_scope(
            organization_id=organization_id,
            recipient_user_id=recipient_user_id,
            actor_user=actor_user,
            require_write=False,
        )
        return {
            "organization_id": organization_id,
            "recipient_user_id": recipient_user_id,
            "unread_count": self.repository.count_unread(
                organization_id=organization_id,
                recipient_user_id=recipient_user_id,
            ),
        }

    def add_state_event(
        self,
        notification_id: int,
        action: str,
        *,
        organization_id: int,
        recipient_user_id: int,
        actor_user: dict[str, Any],
        actor: str,
    ) -> dict[str, Any]:
        self._validate_recipient_scope(
            organization_id=organization_id,
            recipient_user_id=recipient_user_id,
            actor_user=actor_user,
            require_write=True,
        )
        normalized_action = str(action or "").strip().lower()
        if normalized_action not in INTERNAL_NOTIFICATION_STATE_ACTIONS:
            raise ValueError("Nieprawidlowa akcja stanu powiadomienia.")
        notification = self.repository.get_notification(
            int(notification_id),
            organization_id=organization_id,
            recipient_user_id=recipient_user_id,
        )
        if not notification:
            raise InternalNotificationNotFoundError("Nie znaleziono powiadomienia.")
        current_state = str(notification.get("state_action") or "unread")
        if current_state == "archived":
            if normalized_action == "archived":
                return {"notification": self._serialize_notification(notification), "changed": False}
            raise ValueError("Zarchiwizowanego powiadomienia nie mozna zmienic w v1.")
        if current_state == normalized_action:
            return {"notification": self._serialize_notification(notification), "changed": False}
        event = self.repository.add_state_event(
            {
                "notification_id": int(notification_id),
                "organization_id": organization_id,
                "recipient_user_id": recipient_user_id,
                "action": normalized_action,
                "actor_user_id": int(actor_user["user_id"]),
            }
        )
        self.event_repository.log(
            event_type="internal_notification_state_changed",
            invoice_id=None,
            organization_id=organization_id,
            source="INTERNAL_NOTIFICATIONS",
            status_before=current_state,
            status_after=normalized_action,
            decision_reason="Jawnie zmieniono stan wewnetrznego powiadomienia.",
            actor=actor,
            details={
                "notification_id": int(notification_id),
                "recipient_user_id": recipient_user_id,
                "action": normalized_action,
            },
        )
        refreshed = self.repository.get_notification(
            int(notification_id),
            organization_id=organization_id,
            recipient_user_id=recipient_user_id,
        )
        assert refreshed is not None
        return {
            "notification": self._serialize_notification(refreshed),
            "state_event": event,
            "changed": True,
        }

    @staticmethod
    def build_dedupe_key(
        *,
        organization_id: int,
        recipient_user_id: int,
        source_event_id: int,
        reason_code: str,
    ) -> str:
        raw = ":".join(
            [
                str(organization_id),
                str(recipient_user_id),
                INTERNAL_NOTIFICATION_SOURCE_BILLING_ATTENTION,
                str(source_event_id),
                str(reason_code),
            ]
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _validate_recipient_scope(
        self,
        *,
        organization_id: int,
        recipient_user_id: int,
        actor_user: dict[str, Any] | None,
        require_write: bool,
    ) -> None:
        organization = self.organization_repository.get_by_id(int(organization_id))
        if not organization or (require_write and not organization.get("is_active")):
            raise ValueError("Wybrana organizacja nie istnieje albo jest nieaktywna.")
        recipient = self.user_repository.get_by_id(int(recipient_user_id))
        if not recipient or not int(recipient.get("is_active") or 0):
            raise ValueError("Odbiorca powiadomienia nie istnieje albo jest nieaktywny.")
        if actor_user is not None:
            resolver = self.organization_service.resolve_write_scope if require_write else self.organization_service.resolve_data_scope
            resolved = resolver(actor_user, int(organization_id))
            if resolved != int(organization_id) or int(actor_user.get("user_id") or 0) != int(recipient_user_id):
                raise InternalNotificationNotFoundError("Nie znaleziono powiadomienia.")
            return
        if recipient.get("organization_id") == int(organization_id):
            return
        memberships = self.user_repository.list_memberships(int(recipient_user_id))
        if any(
            int(item.get("organization_id") or 0) == int(organization_id)
            and str(item.get("membership_status") or "active") == "active"
            for item in memberships
        ):
            return
        if recipient.get("organization_id") is None and str(recipient.get("role") or "") == SYSTEM_OWNER_ROLE:
            return
        raise InternalNotificationNotFoundError("Nie znaleziono powiadomienia.")

    @staticmethod
    def _normalize_date(value: str | date | None) -> str:
        normalized = value.isoformat() if isinstance(value, date) else str(value or current_local_date_value()).strip()
        try:
            return date.fromisoformat(normalized).isoformat()
        except ValueError:
            raise ValueError("Data materializacji musi byc poprawna data RRRR-MM-DD.") from None

    @staticmethod
    def _safe_internal_link(value: Any) -> str | None:
        normalized = str(value or "").strip()
        return normalized if normalized.startswith("/rozliczenia") and not normalized.startswith("//") else None

    @staticmethod
    def _serialize_notification(item: dict[str, Any]) -> dict[str, Any]:
        serialized = dict(item)
        state = str(serialized.get("state_action") or "unread")
        serialized["state"] = state
        serialized["is_unread"] = state == "unread"
        serialized["is_archived"] = state == "archived"
        serialized.pop("state_action", None)
        return serialized

    @staticmethod
    def _encode_cursor(
        *,
        organization_id: int,
        recipient_user_id: int,
        filter_name: str,
        created_at: str,
        notification_id: int,
    ) -> str:
        payload = json.dumps(
            {
                "o": organization_id,
                "r": recipient_user_id,
                "f": filter_name,
                "c": created_at,
                "i": notification_id,
            },
            separators=(",", ":"),
        ).encode("utf-8")
        return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")

    @staticmethod
    def _decode_cursor(
        cursor: str | None,
        *,
        organization_id: int,
        recipient_user_id: int,
        filter_name: str,
    ) -> tuple[str, int] | None:
        normalized = str(cursor or "").strip()
        if not normalized:
            return None
        try:
            padding = "=" * (-len(normalized) % 4)
            payload = json.loads(base64.urlsafe_b64decode(normalized + padding).decode("utf-8"))
            if (
                int(payload["o"]) != int(organization_id)
                or int(payload["r"]) != int(recipient_user_id)
                or str(payload["f"]) != filter_name
            ):
                raise ValueError
            created_at = str(payload["c"])
            notification_id = int(payload["i"])
            if not created_at or notification_id <= 0:
                raise ValueError
            return created_at, notification_id
        except (KeyError, TypeError, ValueError, json.JSONDecodeError, UnicodeDecodeError):
            raise ValueError("Nieprawidlowy albo niezgodny kursor powiadomien.") from None
