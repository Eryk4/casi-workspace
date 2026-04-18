from __future__ import annotations

import base64
import binascii
import hashlib
import mimetypes
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.repositories.entity_attachment_repository import EntityAttachmentRepository
from app.services.storage_service import LocalStorageService, StorageService


class AttachmentService:
    MAX_BYTES = 8 * 1024 * 1024

    def __init__(
        self,
        attachment_repository: EntityAttachmentRepository,
        storage_service: StorageService,
    ) -> None:
        self.attachment_repository = attachment_repository
        self.storage_service = storage_service

    def list_attachments(
        self,
        entity_type: str,
        entity_id: int,
        *,
        organization_id: int | None = None,
    ) -> list[dict[str, Any]]:
        return self.attachment_repository.list_attachments(
            entity_type,
            entity_id,
            organization_id=organization_id,
        )

    def add_attachment(
        self,
        entity_type: str,
        entity_id: int,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any] | None,
        organization_id: int | None,
        actor: str,
    ) -> dict[str, Any]:
        if organization_id is None:
            raise ValueError("Wybierz organizację przed dodaniem załącznika.")

        attachment_kind = str(payload.get("attachment_kind") or "file").strip().lower()
        file_name = str(payload.get("file_name") or "").strip()
        content_base64 = str(payload.get("content_base64") or "").strip()
        attachment_url = str(payload.get("attachment_url") or "").strip()
        mime_type = self._normalize_optional_text(payload.get("content_type"))

        if attachment_kind == "link" or attachment_url:
            if not attachment_url:
                raise ValueError("Wybierz link do dodania.")
            parsed_url = urlparse(attachment_url)
            if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
                raise ValueError("Link musi zaczynac sie od http:// albo https://.")
            safe_name = self._sanitize_attachment_name(file_name or self._attachment_name_from_url(attachment_url))
            file_size = len(attachment_url.encode("utf-8"))
            stored = {
                "storage_backend": "external_link",
                "storage_key": f"link/{entity_type}/{entity_id}/{hashlib.sha256(attachment_url.encode('utf-8')).hexdigest()[:24]}",
                "public_link": attachment_url,
            }
            if not mime_type:
                mime_type = "text/uri-list"
        else:
            if not file_name or not content_base64:
                raise ValueError("Wybierz plik do dodania albo podaj link.")
            safe_name = self._sanitize_attachment_name(file_name)
            try:
                content = base64.b64decode(content_base64, validate=True)
            except (ValueError, binascii.Error):
                raise ValueError("Nie udalo sie odczytac tresci pliku.") from None

            if not content:
                raise ValueError("Plik jest pusty.")
            if len(content) > self.MAX_BYTES:
                max_mb = self.MAX_BYTES // (1024 * 1024)
                raise ValueError(f"Plik jest zbyt duzy. Maksymalny rozmiar to {max_mb} MB.")

            relative_path = Path(entity_type) / str(entity_id) / safe_name
            stored = self.storage_service.save_binary("document", relative_path, content)
            file_size = len(content)
            if not mime_type:
                mime_type = mimetypes.guess_type(safe_name)[0] or "application/octet-stream"

        storage_key = stored["storage_key"] if isinstance(stored, dict) else stored.storage_key
        public_link = stored["public_link"] if isinstance(stored, dict) else stored.public_link
        storage_backend = stored["storage_backend"] if isinstance(stored, dict) else stored.storage_backend
        attachment_id = self.attachment_repository.create_attachment(
            {
                "organization_id": organization_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "file_name": safe_name,
                "mime_type": mime_type,
                "file_size": file_size,
                "file_link": public_link,
                "file_storage_key": storage_key,
                "storage_backend": storage_backend,
                "uploaded_by_user_id": int(actor_user["user_id"]) if actor_user else None,
            }
        )
        attachment = self.attachment_repository.list_attachments(
            entity_type,
            entity_id,
            organization_id=organization_id,
        )
        created = next((item for item in attachment if int(item["entity_attachment_id"]) == int(attachment_id)), None)
        return created or attachment[0]

    def _sanitize_attachment_name(self, value: str) -> str:
        normalized = str(value or "").strip().replace("\\", "/")
        normalized = normalized.rsplit("/", 1)[-1]
        normalized = re.sub(r"[^A-Za-z0-9._ -]+", "_", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip(" ._")
        return normalized or "zalacznik"

    def _attachment_name_from_url(self, value: str) -> str:
        parsed = urlparse(value)
        host = parsed.netloc or "link"
        tail = parsed.path.rsplit("/", 1)[-1].strip()
        if tail:
            return self._sanitize_attachment_name(tail)
        return f"{host or 'link'}.url"

    def _normalize_optional_text(self, value: Any) -> str | None:
        normalized = str(value or "").strip()
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized or None
