from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_SECRET
from app.integrations.email_ingestion import EmailIngestionAdapter
from app.integrations.ksef_client import KSeFClient
from app.integrations.ocr_engine import OCREngine
from app.integrations.telegram_bot import TelegramBotAdapter, TelegramBotError
from app.repositories.contractor_repository import ContractorRepository
from app.repositories.event_repository import EventRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository
from app.services.duplicate_detector import DuplicateDetector
from app.services.notification_service import NotificationService
from app.services.storage_service import StorageService
from app.utils import now_iso


class InvoiceService:
    def __init__(
        self,
        invoice_repository: InvoiceRepository,
        contractor_repository: ContractorRepository,
        event_repository: EventRepository,
        user_repository: UserRepository,
        organization_repository: OrganizationRepository,
        duplicate_detector: DuplicateDetector,
        notification_service: NotificationService,
        storage_service: StorageService,
    ) -> None:
        self.invoice_repository = invoice_repository
        self.contractor_repository = contractor_repository
        self.event_repository = event_repository
        self.user_repository = user_repository
        self.organization_repository = organization_repository
        self.duplicate_detector = duplicate_detector
        self.notification_service = notification_service
        self.storage_service = storage_service
        self.ksef_client = KSeFClient()
        self.email_adapter = EmailIngestionAdapter()
        self.telegram_adapter = TelegramBotAdapter(
            OCREngine(),
            bot_token=TELEGRAM_BOT_TOKEN,
            webhook_secret=TELEGRAM_WEBHOOK_SECRET,
        )

    def telegram_integration_info(self) -> dict[str, Any]:
        return self.telegram_adapter.integration_status()

    def storage_integration_info(self) -> dict[str, Any]:
        return {"backend": self.storage_service.backend_name}

    def list_invoices(self, filters: dict[str, Any], organization_id: int | None = None) -> list[dict[str, Any]]:
        return self.invoice_repository.list_invoices(filters, organization_id=organization_id)

    def list_contractors(
        self,
        search: str = "",
        only_new: bool = False,
        organization_id: int | None = None,
    ) -> list[dict[str, Any]]:
        return self.contractor_repository.list_contractors(search, only_new=only_new, organization_id=organization_id)

    def list_logs(self, organization_id: int | None = None) -> list[dict[str, Any]]:
        return self.event_repository.list_logs(organization_id=organization_id)

    def get_invoice_detail(self, invoice_id: int, organization_id: int | None = None) -> dict[str, Any] | None:
        invoice = self.invoice_repository.get_by_id(invoice_id, organization_id=organization_id)
        if not invoice:
            return None

        relations = self.invoice_repository.list_relations(invoice_id)
        history = self.event_repository.list_by_invoice(invoice_id, organization_id=invoice.get("organization_id"))
        similar = self.duplicate_detector.similar_invoices(invoice, exclude_invoice_id=invoice_id)

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

        return {
            "invoice": invoice,
            "relations": relations,
            "similar_invoices": similar,
            "history": history,
            "contractor": contractor,
            "contractor_known_before": contractor_known_before,
            "source_trace": self._build_source_trace(invoice),
            "document_trace": self._build_document_trace(invoice),
        }

    def get_contractor_detail(self, contractor_id: int, organization_id: int | None = None) -> dict[str, Any] | None:
        contractor = self.contractor_repository.get_by_id(contractor_id, organization_id=organization_id)
        if not contractor:
            return None
        invoices = self.invoice_repository.list_invoices(
            {"contractor_id": contractor_id},
            organization_id=contractor.get("organization_id"),
        )
        return {"contractor": contractor, "invoices": invoices}

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
        base_payload.setdefault("currency", "PLN")
        base_payload.setdefault("incoming_date", now_iso()[:10])
        base_payload.setdefault("document_type", self._infer_document_type(base_payload))

        if isinstance(base_payload.get("source_metadata"), dict):
            base_payload["source_metadata"] = json.dumps(base_payload["source_metadata"], ensure_ascii=False, indent=2)

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
        return final_invoice

    def update_invoice(
        self,
        invoice_id: int,
        changes: dict[str, Any],
        actor: str = "uzytkownik",
        organization_id: int | None = None,
    ) -> dict[str, Any] | None:
        current = self.invoice_repository.get_by_id(invoice_id, organization_id=organization_id)
        if not current:
            return None
        previous_status = current["status"]
        previous_contractor_id = current.get("contractor_id")
        contractor_created = False

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
            }
        }
        if "source_metadata" in cleaned_changes and isinstance(cleaned_changes["source_metadata"], dict):
            cleaned_changes["source_metadata"] = json.dumps(cleaned_changes["source_metadata"], ensure_ascii=False, indent=2)
        if "gross_amount" in cleaned_changes and cleaned_changes["gross_amount"] not in ("", None):
            cleaned_changes["gross_amount"] = float(cleaned_changes["gross_amount"])
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

        if "contractor_id" not in cleaned_changes and {"issuer_nip", "issuer_name"} & set(cleaned_changes):
            projection = dict(current)
            projection.update(cleaned_changes)
            contractor_id, contractor_created = self._ensure_contractor(projection, int(current["organization_id"]))
            cleaned_changes["contractor_id"] = contractor_id

        self.invoice_repository.update(invoice_id, cleaned_changes)

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

        return refreshed

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

    def reject_duplicate(
        self,
        invoice_id: int,
        actor: str = "uzytkownik",
        organization_id: int | None = None,
    ) -> dict[str, Any] | None:
        invoice = self.invoice_repository.get_by_id(invoice_id, organization_id=organization_id)
        if not invoice:
            return None
        previous_status = invoice["status"]
        self.invoice_repository.delete_relations(invoice_id)
        self.invoice_repository.update(
            invoice_id,
            {
                "status": "poprawna",
                "duplicate_type": "brak",
                "flag_reason": "Faktura została oznaczona jako poprawna ręcznie.",
            },
        )
        self.event_repository.log(
            event_type="duplicate_rejected",
            invoice_id=invoice_id,
            organization_id=invoice.get("organization_id"),
            source=invoice["source"],
            status_before=previous_status,
            status_after="poprawna",
            decision_reason="Faktura została oznaczona jako poprawna ręcznie.",
            actor=actor,
            details={"manual_rejection": True},
        )
        return self.invoice_repository.get_by_id(invoice_id)

    def import_mock(
        self,
        source: str,
        actor: str = "system",
        organization_id: int | None = None,
    ) -> dict[str, Any]:
        normalized = source.upper()
        if normalized == "KSEF":
            payload = self.ksef_client.fetch_mock_invoice()
        elif normalized == "EMAIL":
            payload = self.email_adapter.fetch_mock_invoice()
        elif normalized == "TELEGRAM":
            payload = self.telegram_adapter.fetch_mock_invoice()
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
        if preserve_manual_status and invoice["status"] in {"poprawna", "odrzucona", "zaksiegowana"} and evaluation["duplicate_type"] == "brak":
            next_status = invoice["status"]

        self.invoice_repository.update(
            invoice_id,
            {
                "status": next_status,
                "duplicate_type": evaluation["duplicate_type"],
                "flag_reason": evaluation["flag_reason"],
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
            "document_type": invoice.get("document_type"),
            "organization_name": invoice.get("organization_name"),
            "organization_slug": invoice.get("organization_slug"),
            "source_external_id": invoice.get("source_external_id"),
            "source_sender_name": invoice.get("source_sender_name"),
            "source_sender_id": invoice.get("source_sender_id"),
            "linked_user": self._sanitize_linked_user(linked_user),
            "metadata": metadata,
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
            self._validate_telegram_chat_for_organization(organization, incoming_chat_id)
            return organization

        if incoming_chat_id:
            organization = self.organization_repository.get_by_telegram_chat_id(incoming_chat_id)
            if organization:
                if not organization.get("is_active", 1):
                    raise ValueError("Organizacja przypisana do tego kanalu Telegram jest nieaktywna.")
                return organization

        raise ValueError(
            "Nie mozna ustalic organizacji dla dokumentu z Telegrama. "
            "Powiaz ID uzytkownika Telegram z kontem albo ustaw ID kanalu Telegram w organizacji."
        )

    def _resolve_incoming_telegram_chat_id(self, payload: dict[str, Any]) -> str:
        source_metadata = payload.get("source_metadata") or {}
        return str(source_metadata.get("chat_id") or "").strip()

    def _validate_telegram_chat_for_organization(
        self,
        organization: dict[str, Any],
        incoming_chat_id: str,
    ) -> None:
        configured_chat_id = str(organization.get("telegram_chat_id") or "").strip()
        if configured_chat_id and incoming_chat_id and configured_chat_id != incoming_chat_id:
            raise ValueError("Wiadomosc z Telegrama przyszla z innego kanalu niz przypisany do tej organizacji.")

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

    def _is_duplicate_invoice_hash_error(self, error: Exception) -> bool:
        message = str(error).lower()
        return "invoice_hash" in message and (
            "unique constraint failed" in message
            or "duplicate key value violates unique constraint" in message
            or "unique violation" in message
        )

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
