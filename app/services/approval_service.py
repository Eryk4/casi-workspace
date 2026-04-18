from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.repositories.approval_repository import ApprovalRepository
from app.repositories.entity_attachment_repository import EntityAttachmentRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.task_repository import TaskRepository
from app.services.auth_service import PermissionError
from app.services.attachment_service import AttachmentService
from app.services.storage_service import StorageService
from app.utils import json_dumps, now_iso

KSEF_CORRECTION_REQUEST_KIND = "ksef_field_correction"


class ApprovalService:
    def __init__(
        self,
        approval_repository: ApprovalRepository,
        task_repository: TaskRepository,
        invoice_repository: InvoiceRepository,
        event_repository,
        organization_repository: OrganizationRepository,
        storage_service: StorageService | None = None,
        entity_attachment_repository: EntityAttachmentRepository | None = None,
        invoice_service=None,
    ) -> None:
        self.approval_repository = approval_repository
        self.task_repository = task_repository
        self.invoice_repository = invoice_repository
        self.event_repository = event_repository
        self.organization_repository = organization_repository
        self.attachment_service = (
            AttachmentService(entity_attachment_repository, storage_service)
            if storage_service and entity_attachment_repository
            else None
        )
        self.invoice_service = invoice_service

    def list_requests(
        self,
        *,
        organization_id: int | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
        status: str | None = None,
        limit: int = 50,
        viewer_user: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        requests = self.approval_repository.list_requests(
            organization_id=organization_id,
            entity_type=entity_type,
            entity_id=entity_id,
            status=status,
            limit=limit,
        )
        return [self._decorate_request(item, viewer_user=viewer_user) for item in requests]

    def list_entity_requests(
        self,
        entity_type: str,
        entity_id: int,
        *,
        organization_id: int | None = None,
        viewer_user: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return self.list_requests(
            organization_id=organization_id,
            entity_type=entity_type,
            entity_id=entity_id,
            limit=100,
            viewer_user=viewer_user,
        )

    def create_request(
        self,
        *,
        entity_type: str,
        entity_id: int,
        organization_id: int | None,
        actor_user: dict[str, Any],
        actor: str,
        title: str,
        description: str | None = None,
        requested_user_id: int | None = None,
        approve_status: str | None = None,
        reject_status: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        entity = self._load_entity(
            entity_type,
            entity_id,
            organization_id=organization_id,
            viewer_user_id=int(actor_user["user_id"]),
        )
        if not entity:
            raise ValueError("Nie znaleziono elementu do akceptacji.")
        entity_org_id = int(entity["organization_id"])
        if entity and organization_id is not None and int(organization_id) != entity_org_id:
            raise PermissionError("Element nie nalezy do wskazanej organizacji.")

        default_approve_status, default_reject_status = self._default_entity_statuses(entity_type, entity or {})
        request_id = self.approval_repository.create(
            {
                "organization_id": entity_org_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "title": title,
                "description": description,
                "status": "pending",
                "requested_by_user_id": int(actor_user["user_id"]),
                "requested_user_id": requested_user_id,
                "approve_status": approve_status or default_approve_status,
                "reject_status": reject_status or default_reject_status,
                "metadata_json": json_dumps(metadata or {}),
                "requested_at": now_iso(),
            }
        )
        request = self.approval_repository.get_by_id(request_id, organization_id=entity_org_id)
        assert request is not None
        self.event_repository.log(
            event_type="approval_requested",
            invoice_id=entity_id if entity_type == "invoice" else None,
            organization_id=entity_org_id,
            source=entity_type.upper(),
            status_before=str(entity.get("status") or ""),
            status_after="pending",
            decision_reason=title,
            actor=actor,
            details={
                "approval_request_id": request_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "requested_user_id": requested_user_id,
            },
        )
        return self._decorate_request(request, viewer_user=actor_user)

    def decide_request(
        self,
        approval_request_id: int,
        *,
        decision: str,
        actor_user: dict[str, Any],
        actor: str,
        reason: str | None = None,
    ) -> dict[str, Any]:
        request = self.approval_repository.get_by_id(approval_request_id)
        if not request:
            raise ValueError("Nie znaleziono wniosku akceptacji.")
        decorated_request = self._decorate_request(request, viewer_user=actor_user)
        if not decorated_request.get("can_decide"):
            raise PermissionError("Ta rola nie moze podjac decyzji dla tego wniosku.")
        if str(request.get("status") or "") != "pending":
            raise ValueError("Wniosek akceptacji jest juz rozstrzygniety.")

        normalized_decision = str(decision or "").strip().lower()
        if normalized_decision not in {"approve", "reject", "cancel"}:
            raise ValueError("Nieznana decyzja akceptacji.")

        status_map = {
            "approve": ("approved", request.get("approve_status")),
            "reject": ("rejected", request.get("reject_status")),
            "cancel": ("cancelled", None),
        }
        next_status, entity_status = status_map[normalized_decision]
        entity_type = str(request.get("entity_type") or "").strip()
        entity_id = int(request["entity_id"])
        entity = self._load_entity(
            entity_type,
            entity_id,
            organization_id=int(request["organization_id"]),
            viewer_user_id=int(actor_user["user_id"]),
        )

        self.approval_repository.update(
            approval_request_id,
            {
                "status": next_status,
                "decided_by_user_id": int(actor_user["user_id"]),
                "decided_at": now_iso(),
                "decision_reason": reason,
            },
        )

        metadata = decorated_request.get("metadata")
        if (
            entity_type == "invoice"
            and isinstance(metadata, dict)
            and str(metadata.get("request_kind") or "") == KSEF_CORRECTION_REQUEST_KIND
            and self.invoice_service is not None
            and normalized_decision in {"approve", "reject"}
        ):
            self.invoice_service.apply_ksef_correction_decision(
                decorated_request,
                decision=normalized_decision,
                actor_user=actor_user,
                actor=actor,
                reason=reason,
            )
        elif entity and entity_status:
            self._apply_entity_status(entity_type, entity_id, entity_status, actor=actor)

        self.event_repository.log(
            event_type="approval_approved"
            if normalized_decision == "approve"
            else "approval_rejected"
            if normalized_decision == "reject"
            else "approval_cancelled",
            invoice_id=entity_id if entity_type == "invoice" else None,
            organization_id=int(request["organization_id"]),
            source=entity_type.upper(),
            status_before=str(entity.get("status") or "") if entity else None,
            status_after=str(entity_status or (entity.get("status") if entity else "") or ""),
            decision_reason=reason or str(request.get("title") or ""),
            actor=actor,
            details={
                "approval_request_id": approval_request_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "decision": normalized_decision,
                "entity_status": entity_status,
            },
        )
        refreshed = self.approval_repository.get_by_id(approval_request_id, organization_id=int(request["organization_id"]))
        assert refreshed is not None
        return self._decorate_request(refreshed, viewer_user=actor_user)

    def list_for_entity(
        self,
        entity_type: str,
        entity_id: int,
        *,
        organization_id: int | None = None,
        viewer_user: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return self.list_entity_requests(
            entity_type,
            entity_id,
            organization_id=organization_id,
            viewer_user=viewer_user,
        )

    def get_request_detail(
        self,
        approval_request_id: int,
        *,
        organization_id: int | None = None,
        viewer_user: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        request = self.approval_repository.get_by_id(approval_request_id, organization_id=organization_id)
        if not request:
            return None
        return {
            "request": self._decorate_request(request, viewer_user=viewer_user),
            "attachments": self.list_attachments(
                approval_request_id,
                organization_id=organization_id,
            ),
        }

    def list_attachments(
        self,
        approval_request_id: int,
        *,
        organization_id: int | None = None,
    ) -> list[dict[str, Any]]:
        if not self.attachment_service:
            return []
        return self.attachment_service.list_attachments(
            "approval_request",
            approval_request_id,
            organization_id=organization_id,
        )

    def add_attachment(
        self,
        approval_request_id: int,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any] | None:
        request = self.approval_repository.get_by_id(approval_request_id, organization_id=organization_id)
        if not request or not self.attachment_service:
            return None
        attachment = self.attachment_service.add_attachment(
            "approval_request",
            approval_request_id,
            payload,
            actor_user=actor_user,
            organization_id=int(request["organization_id"]),
            actor=actor,
        )
        self.event_repository.log(
            event_type="approval_attachment_added",
            invoice_id=int(request["entity_id"]) if str(request.get("entity_type") or "") == "invoice" else None,
            organization_id=int(request["organization_id"]),
            source="APPROVAL",
            status_before=str(request.get("status") or ""),
            status_after=str(request.get("status") or ""),
            decision_reason=f"Dodano zalacznik: {attachment['file_name']}.",
            actor=actor,
            details={
                "approval_request_id": approval_request_id,
                "entity_attachment_id": attachment.get("entity_attachment_id"),
            },
        )
        refreshed = self.approval_repository.get_by_id(approval_request_id, organization_id=organization_id)
        if not refreshed:
            return None
        return {
            "request": self._decorate_request(refreshed, viewer_user=actor_user),
            "attachments": self.list_attachments(approval_request_id, organization_id=organization_id),
        }

    def _load_entity(
        self,
        entity_type: str,
        entity_id: int,
        *,
        organization_id: int | None,
        viewer_user_id: int | None = None,
    ) -> dict[str, Any] | None:
        if entity_type == "task":
            return self.task_repository.get_by_id(entity_id, organization_id=organization_id, viewer_user_id=viewer_user_id)
        if entity_type == "invoice":
            return self.invoice_repository.get_by_id(entity_id, organization_id=organization_id)
        return None

    def _apply_entity_status(self, entity_type: str, entity_id: int, status: str, *, actor: str) -> None:
        if entity_type == "task":
            current = self.task_repository.get_by_id(entity_id)
            if current:
                self.task_repository.update(entity_id, {"status": status})
                self.task_repository.create_history(
                    {
                        "task_id": entity_id,
                        "organization_id": int(current["organization_id"]),
                        "action_type": "task_approval_decided",
                        "actor": actor,
                        "message": f"Wniosek akceptacji zmienil status wpisu na {status}.",
                        "details": json_dumps({"task_id": entity_id, "status": status}),
                    }
                )
            return
        if entity_type == "invoice":
            current = self.invoice_repository.get_by_id(entity_id)
            if current:
                self.invoice_repository.update(entity_id, {"status": status})

    def _default_entity_statuses(self, entity_type: str, entity: dict[str, Any]) -> tuple[str | None, str | None]:
        current_status = str(entity.get("status") or "").strip() or None
        if entity_type == "invoice":
            return ("poprawna", "odrzucona")
        if entity_type == "task":
            return ("w_toku", "anulowane")
        return (current_status, None)

    def _decorate_request(self, request: dict[str, Any], viewer_user: dict[str, Any] | None = None) -> dict[str, Any]:
        result = dict(request)
        metadata = result.get("metadata_json")
        if isinstance(metadata, str) and metadata.strip():
            try:
                result["metadata"] = json.loads(metadata)
            except json.JSONDecodeError:
                result["metadata"] = {"raw": metadata}
        else:
            result["metadata"] = {}
        result["is_pending"] = str(result.get("status") or "") == "pending"
        result["can_decide"] = self._can_decide_request(result, viewer_user)
        return result

    def _can_decide_request(self, request: dict[str, Any], viewer_user: dict[str, Any] | None) -> bool:
        if not viewer_user or str(request.get("status") or "") != "pending":
            return False
        if viewer_user.get("is_global_admin"):
            return True

        metadata = request.get("metadata")
        if isinstance(metadata, dict) and str(metadata.get("request_kind") or "") == KSEF_CORRECTION_REQUEST_KIND:
            if (
                str(viewer_user.get("role") or "") == "organization_admin"
                and int(viewer_user.get("organization_id") or 0) == int(request.get("organization_id") or 0)
            ):
                return True

            organization = self.organization_repository.get_by_id(int(request.get("organization_id") or 0))
            if not organization:
                return False
            delegate_user_id = organization.get("ksef_correction_delegate_user_id")
            expires_at = str(organization.get("ksef_correction_delegate_expires_at") or "").strip()
            if not delegate_user_id or not expires_at:
                return False
            try:
                expires_dt = datetime.strptime(expires_at, "%Y-%m-%dT%H:%M")
            except ValueError:
                return False
            return (
                int(delegate_user_id) == int(viewer_user.get("user_id") or 0)
                and expires_dt >= datetime.now()
                and int(viewer_user.get("organization_id") or 0) == int(request.get("organization_id") or 0)
            )

        return int(viewer_user.get("organization_id") or 0) == int(request.get("organization_id") or 0)
