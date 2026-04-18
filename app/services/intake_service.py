from __future__ import annotations

import json
import re
from typing import Any
from uuid import uuid4

from app.repositories.entity_attachment_repository import EntityAttachmentRepository
from app.repositories.event_repository import EventRepository
from app.repositories.intake_repository import IntakeRepository
from app.repositories.organization_repository import OrganizationRepository
from app.services.attachment_service import AttachmentService
from app.services.storage_service import StorageService
from app.utils import json_dumps, now_iso


class IntakeService:
    DEFAULT_FIELD_SCHEMA = [
        {"key": "title", "label": "Tytuł", "type": "text", "required": True},
        {"key": "description", "label": "Opis", "type": "textarea", "required": False},
        {"key": "requester_name", "label": "Zgłaszający", "type": "text", "required": False},
        {"key": "requester_email", "label": "E-mail", "type": "email", "required": False},
        {"key": "priority", "label": "Priorytet", "type": "select", "required": False},
    ]

    def __init__(
        self,
        intake_repository: IntakeRepository,
        event_repository: EventRepository,
        organization_repository: OrganizationRepository,
        storage_service: StorageService,
        entity_attachment_repository: EntityAttachmentRepository,
    ) -> None:
        self.intake_repository = intake_repository
        self.event_repository = event_repository
        self.organization_repository = organization_repository
        self.attachment_service = AttachmentService(entity_attachment_repository, storage_service)

    def list_forms(self, organization_id: int | None = None, *, include_inactive: bool = False) -> list[dict[str, Any]]:
        return self.intake_repository.list_forms(organization_id=organization_id, include_inactive=include_inactive)

    def list_items(
        self,
        *,
        organization_id: int | None = None,
        status: str | None = None,
        source_kind: str | None = None,
        search: str | None = None,
        assigned_user_id: int | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        return self.intake_repository.list_items(
            organization_id=organization_id,
            status=status,
            source_kind=source_kind,
            search=search,
            assigned_user_id=assigned_user_id,
            limit=limit,
        )

    def get_item_detail(self, intake_item_id: int, *, organization_id: int | None = None) -> dict[str, Any] | None:
        item = self.intake_repository.get_item_by_id(intake_item_id, organization_id=organization_id)
        if not item:
            return None
        return {
            "item": self._decorate_item(item),
            "comments": self.intake_repository.list_comments(intake_item_id),
            "attachments": self.attachment_service.list_attachments(
                "intake_item",
                intake_item_id,
                organization_id=organization_id,
            ),
            "history": self.intake_repository.list_history(intake_item_id),
        }

    def create_form(
        self,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any]:
        if organization_id is None:
            raise ValueError("Wybierz organizacje przed dodaniem formularza.")
        organization = self.organization_repository.get_by_id(organization_id)
        if not organization or not organization.get("is_active"):
            raise ValueError("Wybrana organizacja nie istnieje albo jest nieaktywna.")

        form_name = self._normalize_required_text(payload.get("form_name"), "Nazwa formularza")
        form_slug = self._normalize_slug(payload.get("form_slug") or form_name)
        if self.intake_repository.get_form_by_slug(organization_id, form_slug):
            raise ValueError("Formularz o tym identyfikatorze juz istnieje w tej organizacji.")

        public_token = str(payload.get("public_token") or uuid4().hex)
        field_schema_json = self._normalize_field_schema(payload.get("field_schema_json"))
        form_id = self.intake_repository.create_form(
            {
                "organization_id": organization_id,
                "form_name": form_name,
                "form_slug": form_slug,
                "description": self._normalize_optional_text(payload.get("description")),
                "field_schema_json": field_schema_json,
                "is_public": 1 if payload.get("is_public", True) not in {False, 0, "0", "false"} else 0,
                "allow_attachments": 1 if payload.get("allow_attachments", True) not in {False, 0, "0", "false"} else 0,
                "default_priority": self._normalize_priority(payload.get("default_priority") or "normalny"),
                "default_assigned_user_id": self._normalize_optional_int(payload.get("default_assigned_user_id")),
                "public_token": public_token,
                "created_by_user_id": int(actor_user["user_id"]),
            }
        )
        created = self.intake_repository.get_form_by_id(form_id, organization_id=organization_id)
        assert created is not None
        self.event_repository.log(
            event_type="intake_form_created",
            invoice_id=None,
            organization_id=organization_id,
            source="INTAKE",
            status_before=None,
            status_after="aktywny" if created.get("is_public") else "ukryty",
            decision_reason=f"Dodano formularz {created['form_name']}.",
            actor=actor,
            details={
                "intake_form_id": form_id,
                "form_slug": created["form_slug"],
                "public_token": created["public_token"],
                "created_by_user_id": actor_user.get("user_id"),
            },
        )
        return self._decorate_form(created)

    def update_form(
        self,
        intake_form_id: int,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any] | None:
        current = self.intake_repository.get_form_by_id(intake_form_id, organization_id=organization_id)
        if not current:
            return None
        updates: dict[str, Any] = {}
        if "form_name" in payload:
            updates["form_name"] = self._normalize_required_text(payload.get("form_name"), "Nazwa formularza")
        if "form_slug" in payload:
            updates["form_slug"] = self._normalize_slug(payload.get("form_slug"))
        if "description" in payload:
            updates["description"] = self._normalize_optional_text(payload.get("description"))
        if "field_schema_json" in payload:
            updates["field_schema_json"] = self._normalize_field_schema(payload.get("field_schema_json"))
        if "is_public" in payload:
            updates["is_public"] = 1 if payload.get("is_public") not in {False, 0, "0", "false"} else 0
        if "allow_attachments" in payload:
            updates["allow_attachments"] = 1 if payload.get("allow_attachments") not in {False, 0, "0", "false"} else 0
        if "default_priority" in payload:
            updates["default_priority"] = self._normalize_priority(payload.get("default_priority"))
        if "default_assigned_user_id" in payload:
            updates["default_assigned_user_id"] = self._normalize_optional_int(payload.get("default_assigned_user_id"))
        if updates:
            self.intake_repository.update_form(intake_form_id, updates)
            refreshed = self.intake_repository.get_form_by_id(intake_form_id, organization_id=organization_id)
            assert refreshed is not None
            self.event_repository.log(
                event_type="intake_form_updated",
                invoice_id=None,
                organization_id=organization_id,
                source="INTAKE",
                status_before=None,
                status_after="aktywny" if refreshed.get("is_public") else "ukryty",
                decision_reason=f"Zmieniono formularz {refreshed['form_name']}.",
                actor=actor,
                details={
                    "intake_form_id": intake_form_id,
                    "updated_fields": sorted(updates.keys()),
                    "updated_by_user_id": actor_user.get("user_id"),
                },
            )
            return self._decorate_form(refreshed)
        return self._decorate_form(current)

    def delete_form(
        self,
        intake_form_id: int,
        *,
        actor_user: dict[str, Any] | None,
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any] | None:
        current = self.intake_repository.get_form_by_id(intake_form_id, organization_id=organization_id)
        if not current:
            return None
        self.intake_repository.update_form(
            intake_form_id,
            {
                "is_public": 0,
            },
        )
        refreshed = self.intake_repository.get_form_by_id(intake_form_id, organization_id=organization_id)
        assert refreshed is not None
        self.event_repository.log(
            event_type="intake_form_archived",
            invoice_id=None,
            organization_id=int(refreshed["organization_id"]),
            source="INTAKE",
            status_before="aktywny" if current.get("is_public") else "ukryty",
            status_after="ukryty",
            decision_reason=f"Wyłączono formularz {refreshed['form_name']}.",
            actor=actor,
            details={
                "intake_form_id": intake_form_id,
                "deleted_by_user_id": actor_user.get("user_id") if actor_user else None,
            },
        )
        return self._decorate_form(refreshed)

    def submit_form(self, public_token: str, payload: dict[str, Any]) -> dict[str, Any]:
        form = self.intake_repository.get_form_by_token(public_token)
        if not form:
            raise ValueError("Nie znaleziono formularza.")
        if not int(form.get("is_public") or 0):
            raise ValueError("Ten formularz nie jest publicznie dostepny.")
        return self._create_item_from_payload(
            payload,
            organization_id=int(form["organization_id"]),
            form=form,
            source_kind="form",
            actor_user=None,
            actor="form",
        )

    def create_item(
        self,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any] | None,
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any]:
        return self._create_item_from_payload(
            payload,
            organization_id=organization_id,
            form=None,
            source_kind=str(payload.get("source_kind") or "manual").strip().lower() or "manual",
            actor_user=actor_user,
            actor=actor,
        )

    def list_support_requests(
        self,
        *,
        organization_id: int,
        viewer_user: dict[str, Any],
        status: str | None = None,
        search: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        viewer_user_id = int(viewer_user["user_id"])
        items = self.intake_repository.list_items(
            organization_id=organization_id,
            status=status,
            source_kind="support",
            search=search,
            created_by_user_id=viewer_user_id,
            limit=limit,
        )
        return [self._decorate_item(item) for item in items]

    def get_support_request_detail(
        self,
        intake_item_id: int,
        *,
        organization_id: int,
        viewer_user: dict[str, Any],
    ) -> dict[str, Any] | None:
        current = self.intake_repository.get_item_by_id(
            intake_item_id,
            organization_id=organization_id,
            created_by_user_id=int(viewer_user["user_id"]),
        )
        if not current or str(current.get("source_kind") or "").strip().lower() != "support":
            return None
        return {
            "item": self._decorate_item(current),
            "comments": self.intake_repository.list_comments(intake_item_id),
            "attachments": self.attachment_service.list_attachments(
                "intake_item",
                intake_item_id,
                organization_id=organization_id,
            ),
            "history": self.intake_repository.list_history(intake_item_id),
        }

    def create_support_request(
        self,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int,
    ) -> dict[str, Any]:
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        support_category = self._normalize_optional_text(payload.get("support_category"))
        if support_category:
            metadata = dict(metadata)
            metadata["support_category"] = support_category
        if not metadata:
            metadata = {"channel": "support_center"}
        elif "channel" not in metadata:
            metadata = dict(metadata)
            metadata["channel"] = "support_center"
        return self.create_standalone_item(
            title=str(payload.get("title") or ""),
            description=str(payload.get("description") or ""),
            organization_id=organization_id,
            source_kind="support",
            payload={
                "status": "nowe",
                "priority": payload.get("priority") or "normalny",
                "requester_name": payload.get("requester_name")
                or actor_user.get("display_name")
                or actor_user.get("login"),
                "requester_email": payload.get("requester_email") or actor_user.get("email"),
                "metadata": metadata,
            },
            actor_user=actor_user,
            actor=actor,
        )

    def add_support_comment(
        self,
        intake_item_id: int,
        note_text: str,
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int,
        parent_comment_id: int | None = None,
    ) -> dict[str, Any] | None:
        current = self.intake_repository.get_item_by_id(
            intake_item_id,
            organization_id=organization_id,
            created_by_user_id=int(actor_user["user_id"]),
        )
        if not current or str(current.get("source_kind") or "").strip().lower() != "support":
            return None
        return self.add_comment(
            intake_item_id,
            note_text,
            actor_user=actor_user,
            actor=actor,
            organization_id=organization_id,
            parent_comment_id=parent_comment_id,
        )

    def add_support_attachment(
        self,
        intake_item_id: int,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int,
    ) -> dict[str, Any] | None:
        current = self.intake_repository.get_item_by_id(
            intake_item_id,
            organization_id=organization_id,
            created_by_user_id=int(actor_user["user_id"]),
        )
        if not current or str(current.get("source_kind") or "").strip().lower() != "support":
            return None
        return self.add_attachment(
            intake_item_id,
            payload,
            actor_user=actor_user,
            actor=actor,
            organization_id=organization_id,
        )

    def update_item(
        self,
        intake_item_id: int,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any] | None:
        current = self.intake_repository.get_item_by_id(intake_item_id, organization_id=organization_id)
        if not current:
            return None

        updates: dict[str, Any] = {}
        for key in (
            "status",
            "priority",
            "title",
            "description",
            "requester_name",
            "requester_email",
            "source_reference",
            "due_at",
            "assigned_user_id",
            "linked_task_id",
            "linked_invoice_id",
        ):
            if key in payload:
                value = payload.get(key)
                if key == "status":
                    updates[key] = self._normalize_status(value)
                elif key == "priority":
                    updates[key] = self._normalize_priority(value)
                elif key in {"title", "description", "requester_name", "requester_email", "source_reference", "due_at"}:
                    updates[key] = self._normalize_optional_text(value) if key != "title" else self._normalize_required_text(value, "Tytuł")
                else:
                    updates[key] = self._normalize_optional_int(value)
        if "metadata_json" in payload:
            updates["metadata_json"] = self._normalize_json_text(payload.get("metadata_json"))
        if updates:
            updates["last_activity_at"] = now_iso()
            self.intake_repository.update_item(intake_item_id, updates)
            refreshed = self.intake_repository.get_item_by_id(intake_item_id, organization_id=organization_id)
            assert refreshed is not None
            self.intake_repository.create_history(
                {
                    "intake_item_id": intake_item_id,
                    "organization_id": int(refreshed["organization_id"]),
                    "action_type": "intake_item_updated",
                    "actor": actor,
                    "message": f"Zaktualizowano sprawę: {refreshed['title']}.",
                    "details": json_dumps({"updated_fields": sorted(updates.keys()), "updated_by_user_id": actor_user.get("user_id")}),
                }
            )
            self.event_repository.log(
                event_type="intake_item_updated",
                invoice_id=None,
                organization_id=int(refreshed["organization_id"]),
                source="INTAKE",
                status_before=str(current.get("status") or ""),
                status_after=str(refreshed.get("status") or ""),
                decision_reason=f"Zaktualizowano sprawę {refreshed['title']}.",
                actor=actor,
                details={"intake_item_id": intake_item_id, "updated_fields": sorted(updates.keys())},
            )
            return self._decorate_item(refreshed)
        return self._decorate_item(current)

    def add_comment(
        self,
        intake_item_id: int,
        note_text: str,
        *,
        actor_user: dict[str, Any],
        actor: str,
        organization_id: int | None,
        parent_comment_id: int | None = None,
    ) -> dict[str, Any] | None:
        current = self.intake_repository.get_item_by_id(intake_item_id, organization_id=organization_id)
        if not current:
            return None
        normalized = self._normalize_required_text(note_text, "Komentarz")
        self.intake_repository.create_comment(
            {
                "intake_item_id": intake_item_id,
                "organization_id": int(current["organization_id"]),
                "note_text": normalized,
                "created_by_user_id": int(actor_user["user_id"]),
                "parent_comment_id": parent_comment_id,
            }
        )
        self.intake_repository.update_item(
            intake_item_id,
            {"last_activity_at": now_iso()},
        )
        self.intake_repository.create_history(
            {
                "intake_item_id": intake_item_id,
                "organization_id": int(current["organization_id"]),
                "action_type": "intake_comment_added",
                "actor": actor,
                "message": "Dodano komentarz do sprawy.",
                "details": json_dumps({"created_by_user_id": actor_user.get("user_id"), "parent_comment_id": parent_comment_id}),
            }
        )
        self.event_repository.log(
            event_type="intake_comment_added",
            invoice_id=None,
            organization_id=int(current["organization_id"]),
            source="INTAKE",
            status_before=str(current.get("status") or ""),
            status_after=str(current.get("status") or ""),
            decision_reason="Dodano komentarz do sprawy.",
            actor=actor,
            details={"intake_item_id": intake_item_id},
        )
        return self.get_item_detail(intake_item_id, organization_id=organization_id)

    def add_attachment(
        self,
        intake_item_id: int,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any] | None,
        actor: str,
        organization_id: int | None,
    ) -> dict[str, Any] | None:
        current = self.intake_repository.get_item_by_id(intake_item_id, organization_id=organization_id)
        if not current:
            return None
        attachment = self.attachment_service.add_attachment(
            "intake_item",
            intake_item_id,
            payload,
            actor_user=actor_user,
            organization_id=int(current["organization_id"]),
            actor=actor,
        )
        self.intake_repository.update_item(
            intake_item_id,
            {"last_activity_at": now_iso()},
        )
        self.intake_repository.create_history(
            {
                "intake_item_id": intake_item_id,
                "organization_id": int(current["organization_id"]),
                "action_type": "intake_attachment_added",
                "actor": actor,
                "message": f"Dodano zalacznik: {attachment['file_name']}.",
                "details": json_dumps({"entity_attachment_id": attachment["entity_attachment_id"]}),
            }
        )
        self.event_repository.log(
            event_type="intake_attachment_added",
            invoice_id=None,
            organization_id=int(current["organization_id"]),
            source="INTAKE",
            status_before=str(current.get("status") or ""),
            status_after=str(current.get("status") or ""),
            decision_reason=f"Dodano zalacznik: {attachment['file_name']}.",
            actor=actor,
            details={"intake_item_id": intake_item_id, "entity_attachment_id": attachment["entity_attachment_id"]},
        )
        return self.get_item_detail(intake_item_id, organization_id=organization_id)

    def create_standalone_item(
        self,
        *,
        title: str,
        description: str | None,
        organization_id: int,
        source_kind: str,
        payload: dict[str, Any] | None = None,
        actor_user: dict[str, Any] | None,
        actor: str,
    ) -> dict[str, Any]:
        return self._create_item_from_payload(
            payload or {},
            organization_id=organization_id,
            form=None,
            source_kind=source_kind,
            actor_user=actor_user,
            actor=actor,
            override_title=title,
            override_description=description,
        )

    def create_form_submission_from_event(
        self,
        *,
        organization_id: int,
        title: str,
        description: str | None,
        source_kind: str,
        form: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
        actor_user: dict[str, Any] | None,
        actor: str,
    ) -> dict[str, Any]:
        return self._create_item_from_payload(
            payload or {},
            organization_id=organization_id,
            form=form,
            source_kind=source_kind,
            actor_user=actor_user,
            actor=actor,
            override_title=title,
            override_description=description,
        )

    def _create_item_from_payload(
        self,
        payload: dict[str, Any],
        *,
        organization_id: int | None,
        form: dict[str, Any] | None,
        source_kind: str,
        actor_user: dict[str, Any] | None,
        actor: str,
        override_title: str | None = None,
        override_description: str | None = None,
    ) -> dict[str, Any]:
        if organization_id is None:
            raise ValueError("Wybierz organizacje przed dodaniem sprawy.")
        organization = self.organization_repository.get_by_id(organization_id)
        if not organization or not organization.get("is_active"):
            raise ValueError("Wybrana organizacja nie istnieje albo jest nieaktywna.")

        title = self._normalize_required_text(override_title if override_title is not None else payload.get("title"), "Tytuł")
        description = self._normalize_optional_text(override_description if override_description is not None else payload.get("description"))
        request = {
            "organization_id": organization_id,
            "intake_form_id": int(form["intake_form_id"]) if form else self._normalize_optional_int(payload.get("intake_form_id")),
            "source_kind": self._normalize_source_kind(source_kind),
            "status": self._normalize_status(payload.get("status") or "nowe"),
            "priority": self._normalize_priority(payload.get("priority") or (form.get("default_priority") if form else "normalny")),
            "title": title,
            "description": description,
            "requester_name": self._normalize_optional_text(payload.get("requester_name")),
            "requester_email": self._normalize_optional_text(payload.get("requester_email")),
            "source_reference": self._normalize_optional_text(payload.get("source_reference")),
            "due_at": self._normalize_optional_text(payload.get("due_at")),
            "metadata_json": self._normalize_json_text(payload.get("metadata_json") or payload.get("metadata") or {}),
            "assigned_user_id": self._normalize_optional_int(
                payload.get("assigned_user_id") or (form.get("default_assigned_user_id") if form else None)
            ),
            "linked_task_id": self._normalize_optional_int(payload.get("linked_task_id")),
            "linked_invoice_id": self._normalize_optional_int(payload.get("linked_invoice_id")),
            "created_by_user_id": int(actor_user["user_id"]) if actor_user else None,
        }
        item_id = self.intake_repository.create_item(request)
        item = self.intake_repository.get_item_by_id(item_id, organization_id=organization_id)
        assert item is not None
        self.intake_repository.create_history(
            {
                "intake_item_id": item_id,
                "organization_id": organization_id,
                "action_type": "intake_item_created",
                "actor": actor,
                "message": f"Utworzono sprawę: {item['title']}.",
                "details": json_dumps(
                    {
                        "source_kind": source_kind,
                        "created_by_user_id": actor_user.get("user_id") if actor_user else None,
                        "intake_form_id": request.get("intake_form_id"),
                    }
                ),
            }
        )
        self.event_repository.log(
            event_type="intake_item_created",
            invoice_id=None,
            organization_id=organization_id,
            source=source_kind.upper(),
            status_before=None,
            status_after=item["status"],
            decision_reason=f"Utworzono sprawę {item['title']}.",
            actor=actor,
            details={
                "intake_item_id": item_id,
                "source_kind": source_kind,
                "intake_form_id": request.get("intake_form_id"),
            },
        )
        return self._decorate_item(item)

    def _decorate_item(self, item: dict[str, Any]) -> dict[str, Any]:
        result = dict(item)
        metadata_raw = result.get("metadata_json")
        if isinstance(metadata_raw, str) and metadata_raw.strip():
            try:
                result["metadata_json"] = json.loads(metadata_raw)
            except json.JSONDecodeError:
                result["metadata_json"] = metadata_raw
        return result

    def _decorate_form(self, form: dict[str, Any]) -> dict[str, Any]:
        result = dict(form)
        schema_raw = result.get("field_schema_json")
        if isinstance(schema_raw, str) and schema_raw.strip():
            try:
                result["field_schema_json"] = json.loads(schema_raw)
            except json.JSONDecodeError:
                result["field_schema_json"] = schema_raw
        return result

    def _normalize_required_text(self, value: Any, field_label: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError(f"{field_label} jest wymagana.")
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized

    def _normalize_optional_text(self, value: Any) -> str | None:
        normalized = str(value or "").strip()
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized or None

    def _normalize_slug(self, value: Any) -> str:
        normalized = self._normalize_required_text(value, "Identyfikator")
        normalized = normalized.lower()
        normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
        normalized = re.sub(r"-+", "-", normalized).strip("-")
        if not normalized:
            raise ValueError("Identyfikator formularza jest nieprawidlowy.")
        return normalized

    def _normalize_status(self, value: Any) -> str:
        normalized = str(value or "").strip().lower()
        if normalized not in {"nowe", "w_toku", "oczekuje", "zakonczone", "zarchiwizowane"}:
            raise ValueError("Nieprawidlowy status sprawy.")
        return normalized

    def _normalize_priority(self, value: Any) -> str:
        normalized = str(value or "").strip().lower()
        if normalized in {"niski", "low"}:
            return "niski"
        if normalized in {"normalny", "normal", "medium"}:
            return "normalny"
        if normalized in {"wysoki", "high"}:
            return "wysoki"
        if normalized in {"pilny", "critical"}:
            return "pilny"
        raise ValueError("Nieprawidlowy priorytet.")

    def _normalize_optional_int(self, value: Any) -> int | None:
        if value in {None, ""}:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValueError("Nieprawidlowy identyfikator liczbowy.") from None

    def _normalize_json_text(self, value: Any) -> str:
        if isinstance(value, str):
            candidate = value.strip()
            if not candidate:
                return "{}"
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError as error:
                raise ValueError("Nieprawidlowy format danych JSON.") from error
            return json_dumps(parsed)
        return json_dumps(value if value is not None else {})

    def _normalize_source_kind(self, value: Any) -> str:
        normalized = str(value or "").strip().lower()
        normalized = re.sub(r"[^a-z0-9_]+", "_", normalized)
        normalized = re.sub(r"_+", "_", normalized).strip("_")
        if not normalized:
            raise ValueError("Nieprawidlowe zrodlo sprawy.")
        return normalized[:64]
