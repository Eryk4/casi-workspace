from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from difflib import SequenceMatcher
import hashlib
from io import BytesIO
import json
import mimetypes
from pathlib import Path
import re
from typing import Any
import zipfile
from xml.etree import ElementTree

from app.config import KNOWLEDGE_DIR
from app.integrations.ocr_engine import OCREngine
from app.repositories.event_repository import EventRepository
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository
from app.services.storage_service import StorageError, StorageService
from app.utils import now_iso


class KnowledgeError(ValueError):
    pass


@dataclass(frozen=True)
class KnowledgeMatch:
    score: float
    document: dict[str, Any]
    snippet: str


class KnowledgeService:
    TEXT_EXTENSIONS = {
        ".txt",
        ".md",
        ".markdown",
        ".csv",
        ".json",
        ".xml",
        ".html",
        ".htm",
        ".log",
        ".ini",
        ".yaml",
        ".yml",
    }
    IMAGE_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tif",
        ".tiff",
        ".webp",
    }
    STOPWORDS = {
        "a",
        "aby",
        "albo",
        "ale",
        "bo",
        "by",
        "byc",
        "byl",
        "byla",
        "bylo",
        "co",
        "czy",
        "dla",
        "do",
        "i",
        "ich",
        "jak",
        "jest",
        "jego",
        "jej",
        "jesli",
        "lub",
        "ma",
        "na",
        "nie",
        "o",
        "od",
        "oraz",
        "po",
        "pod",
        "przez",
        "przy",
        "sie",
        "tak",
        "te",
        "ten",
        "to",
        "u",
        "w",
        "we",
        "z",
        "za",
        "ze",
    }
    MAX_CONTENT_LENGTH = 120_000
    MAX_UPLOAD_BYTES = 15 * 1024 * 1024
    DOCUMENT_LIST_VERSION_LIMIT = 10
    DOCUMENT_LIST_JOB_LIMIT = 6
    DETAIL_VERSION_LIMIT = 25
    DETAIL_JOB_LIMIT = 12
    DETAIL_AUDIT_LIMIT = 18
    DETAIL_COMMENT_LIMIT = 30
    ACTIVITY_FEED_LIMIT = 12
    COMPARE_MAX_BLOCKS = 24
    COMPARE_MAX_LINES_PER_BLOCK = 12
    COMPARE_CONTEXT_EDGE_LINES = 2
    COMPARE_MAX_SIDE_BY_SIDE_ROWS = 80
    COMPARE_MAX_ROW_TEXT_LENGTH = 240
    COMPARE_TOPIC_LIMIT = 3
    COMPARE_KEYWORD_LIMIT = 4
    BULK_ACTION_LIMIT = 80
    SIMILARITY_THRESHOLD = 0.72
    AUDIT_EVENT_LABELS = {
        "knowledge_document_created": "Dodanie dokumentu",
        "knowledge_document_updated": "Przetworzenie dokumentu",
        "knowledge_document_replaced": "Podmiana pliku",
        "knowledge_document_archived": "Archiwizacja",
        "knowledge_document_restored": "Przywrocenie dokumentu",
        "knowledge_document_deleted": "Usuniecie logiczne",
        "knowledge_document_version_restored": "Przywrocenie wersji",
        "knowledge_document_official_version_marked": "Oznaczenie wersji obowiazujacej",
        "knowledge_document_comment_added": "Komentarz lub adnotacja",
        "knowledge_document_downloaded": "Pobranie pliku",
        "knowledge_document_workflow_updated": "Zmiana obiegu dokumentu",
        "knowledge_document_assignments_updated": "Zmiana osob odpowiedzialnych",
        "knowledge_document_decision_taken": "Decyzja dokumentowa",
        "knowledge_document_task_created": "Powiazane zadanie",
    }
    BULK_ACTION_LABELS = {
        "archive": "Archiwizacja",
        "restore": "Przywrocenie",
        "move_folder": "Przeniesienie do folderu",
        "set_downloadable": "Widocznosc w bibliotece",
        "set_assistant_usage": "Uzycie przez asystenta",
    }
    WORKFLOW_STATUS_LABELS = {
        "stable": "stabilny",
        "review_needed": "wymaga decyzji",
        "official_missing": "brak wersji obowiazujacej",
        "processing": "w przetwarzaniu",
        "archived": "archiwalny",
        "deleted": "usuniety",
    }
    BUSINESS_STATUS_LABELS = {
        "roboczy": "roboczy",
        "do_sprawdzenia": "do sprawdzenia",
        "do_akceptacji": "do akceptacji",
        "obowiazujacy": "obowiazujacy",
        "archiwalny": "archiwalny",
    }
    DECISION_ACTION_LABELS = {
        "send_for_review": "Wyslij do sprawdzenia",
        "send_for_approval": "Przekaz do akceptacji",
        "approve": "Zatwierdz",
        "return_for_changes": "Odeslij do poprawy",
        "reassign": "Zmien osoby odpowiedzialne",
    }
    ACTIVITY_EVENT_TYPES = (
        "knowledge_document_comment_added",
        "knowledge_document_official_version_marked",
        "knowledge_document_replaced",
        "knowledge_document_version_restored",
        "knowledge_document_workflow_updated",
        "knowledge_document_assignments_updated",
        "knowledge_document_decision_taken",
        "knowledge_document_task_created",
    )
    MODULE_INBOX_KEY = "knowledge"

    def __init__(
        self,
        knowledge_repository: KnowledgeRepository,
        organization_repository: OrganizationRepository,
        user_repository: UserRepository,
        event_repository: EventRepository,
        storage_service: StorageService,
        ocr_engine: OCREngine | None = None,
    ) -> None:
        self.knowledge_repository = knowledge_repository
        self.organization_repository = organization_repository
        self.user_repository = user_repository
        self.event_repository = event_repository
        self.storage_service = storage_service
        self.ocr_engine = ocr_engine or OCREngine()

    def list_documents(
        self,
        organization_id: int,
        search: str = "",
        include_deleted: bool = False,
        viewer_user_id: int | None = None,
    ) -> dict[str, Any]:
        organization = self._resolve_organization(organization_id)
        folder_path = self._organization_folder_path(organization["slug"])
        folder_path.mkdir(parents=True, exist_ok=True)
        documents = self.knowledge_repository.list_documents(
            int(organization["organization_id"]),
            search=search,
            include_deleted=include_deleted,
        )
        ocr_status = self.ocr_engine.integration_status()
        serialized_documents = [self._serialize_document(item, viewer_user_id=viewer_user_id) for item in documents]
        activity_payload = self.get_activity_feed(
            organization_id=int(organization["organization_id"]),
            viewer_user_id=viewer_user_id,
        )
        return {
            "organization_id": organization["organization_id"],
            "organization_name": organization["name"],
            "organization_slug": organization["slug"],
            "folder_path": str(folder_path),
            "supported_formats": self.supported_formats(),
            "ocr_enabled": bool(ocr_status.get("enabled")),
            "ocr_mode": ocr_status.get("mode") or "fallback",
            "documents": serialized_documents,
            "document_summary": self._build_document_summary(serialized_documents),
            "folder_summary": self._build_folder_summary(serialized_documents),
            "activity_feed": activity_payload["items"],
            "activity_summary": self._build_activity_summary(
                serialized_documents,
                unread_count=int(activity_payload["summary"].get("unread_count") or 0),
                viewer_user_id=viewer_user_id,
            ),
            "watch_status": self._serialize_watch_status(
                self.knowledge_repository.get_watch_status(int(organization["organization_id"]))
            ),
            "limits": {
                "max_upload_bytes": self.MAX_UPLOAD_BYTES,
                "max_upload_megabytes": round(self.MAX_UPLOAD_BYTES / (1024 * 1024), 1),
            },
        }

    def list_assignment_candidates(self, organization_id: int) -> list[dict[str, Any]]:
        organization = self._resolve_organization(organization_id)
        members = self.user_repository.list_active_organization_members(int(organization["organization_id"]))
        candidates: list[dict[str, Any]] = []
        for member in members:
            user_id = int(member.get("user_id") or 0)
            if user_id <= 0:
                continue
            display_name = str(member.get("display_name") or member.get("login") or f"uzytkownik #{user_id}").strip()
            candidates.append(
                {
                    "user_id": user_id,
                    "login": member.get("login"),
                    "display_name": display_name,
                    "label": display_name,
                    "role": member.get("role"),
                    "membership_role": member.get("membership_role") or member.get("role"),
                    "organization_id": int(member.get("organization_id") or organization["organization_id"]),
                    "organization_name": member.get("organization_name") or organization["name"],
                    "is_primary": bool(member.get("is_primary")),
                }
            )
        return candidates

    def get_document_detail(
        self,
        *,
        organization_id: int,
        knowledge_document_id: int,
        include_deleted: bool = False,
        viewer_user_id: int | None = None,
    ) -> dict[str, Any]:
        document = self.knowledge_repository.get_by_id(knowledge_document_id, organization_id=organization_id)
        if not document:
            raise KnowledgeError("Nie znaleziono dokumentu bazy wiedzy.")
        if not include_deleted and str(document.get("lifecycle_status") or "active") == "deleted":
            raise KnowledgeError("Ten dokument zostal usuniety i nie jest widoczny w tym widoku.")
        return self._serialize_document(
            document,
            version_limit=self.DETAIL_VERSION_LIMIT,
            job_limit=self.DETAIL_JOB_LIMIT,
            include_audit=True,
            include_comments=True,
            include_full_content=True,
            viewer_user_id=viewer_user_id,
        )

    def compare_document_versions(
        self,
        *,
        organization_id: int,
        knowledge_document_id: int,
        left_version_number: int,
        right_version_number: int,
    ) -> dict[str, Any]:
        document = self.knowledge_repository.get_by_id(knowledge_document_id, organization_id=organization_id)
        if not document:
            raise KnowledgeError("Nie znaleziono dokumentu bazy wiedzy.")

        left_number = int(left_version_number)
        right_number = int(right_version_number)
        if left_number <= 0 or right_number <= 0:
            raise KnowledgeError("Numery wersji musza byc dodatnie.")
        if left_number == right_number:
            raise KnowledgeError("Wybierz dwie rozne wersje do porownania.")

        left_version = self.knowledge_repository.get_version_by_number(knowledge_document_id, left_number)
        right_version = self.knowledge_repository.get_version_by_number(knowledge_document_id, right_number)
        if not left_version or not right_version:
            raise KnowledgeError("Nie znaleziono jednej z wybranych wersji dokumentu.")

        if int(left_version.get("version_number") or 0) >= int(right_version.get("version_number") or 0):
            target_version = left_version
            base_version = right_version
        else:
            target_version = right_version
            base_version = left_version

        base_lines = self._prepare_text_lines_for_compare(str(base_version.get("content_text") or ""))
        target_lines = self._prepare_text_lines_for_compare(str(target_version.get("content_text") or ""))
        matcher = SequenceMatcher(None, base_lines, target_lines)

        blocks: list[dict[str, Any]] = []
        added_lines: list[str] = []
        removed_lines: list[str] = []
        added_line_count = 0
        removed_line_count = 0
        unchanged_line_count = 0
        changed_block_count = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                chunk = base_lines[i1:i2]
                unchanged_line_count += len(chunk)
                block = self._build_version_compare_block("context", chunk)
                if block:
                    blocks.append(block)
                continue

            changed_block_count += 1
            if tag in {"replace", "delete"}:
                removed_chunk = base_lines[i1:i2]
                removed_line_count += len(removed_chunk)
                removed_lines.extend(removed_chunk)
                block = self._build_version_compare_block("removed", removed_chunk)
                if block:
                    blocks.append(block)
            if tag in {"replace", "insert"}:
                added_chunk = target_lines[j1:j2]
                added_line_count += len(added_chunk)
                added_lines.extend(added_chunk)
                block = self._build_version_compare_block("added", added_chunk)
                if block:
                    blocks.append(block)

        visible_blocks = blocks[: self.COMPARE_MAX_BLOCKS]
        side_by_side_rows = self._build_side_by_side_compare_rows(base_lines, target_lines, matcher)
        visible_rows = side_by_side_rows[: self.COMPARE_MAX_SIDE_BY_SIDE_ROWS]
        similarity_ratio = round(matcher.ratio(), 3)
        summary = {
            "added_line_count": added_line_count,
            "removed_line_count": removed_line_count,
            "unchanged_line_count": unchanged_line_count,
            "changed_block_count": changed_block_count,
            "similarity_ratio": similarity_ratio,
            "truncated_block_count": max(0, len(blocks) - len(visible_blocks)),
            "truncated_side_by_side_row_count": max(0, len(side_by_side_rows) - len(visible_rows)),
            "comparison_basis": "older_to_newer",
        }
        return {
            "knowledge_document_id": int(document["knowledge_document_id"]),
            "document_title": document["title"],
            "compare_label": f"v{left_number} vs v{right_number}",
            "left_version": self._serialize_version_compare_meta(left_version),
            "right_version": self._serialize_version_compare_meta(right_version),
            "base_version": self._serialize_version_compare_meta(base_version),
            "target_version": self._serialize_version_compare_meta(target_version),
            "summary": summary,
            "change_summary": self._build_version_change_summary(
                base_version=base_version,
                target_version=target_version,
                base_lines=base_lines,
                target_lines=target_lines,
                added_lines=added_lines,
                removed_lines=removed_lines,
                changed_block_count=changed_block_count,
                similarity_ratio=similarity_ratio,
            ),
            "blocks": visible_blocks,
            "side_by_side_rows": visible_rows,
        }

    def bulk_update_documents(
        self,
        *,
        organization_id: int,
        knowledge_document_ids: list[Any],
        action: str,
        actor_user: dict[str, Any],
        actor: str,
        library_path: str | None = None,
        enabled: bool | None = None,
    ) -> dict[str, Any]:
        normalized_action = str(action or "").strip()
        if normalized_action not in self.BULK_ACTION_LABELS:
            raise KnowledgeError("Nieprawidlowa akcja masowa dla dokumentow.")

        document_ids = self._normalize_bulk_document_ids(knowledge_document_ids)
        if not document_ids:
            raise KnowledgeError("Zaznacz przynajmniej jeden dokument.")
        if len(document_ids) > self.BULK_ACTION_LIMIT:
            raise KnowledgeError(
                f"Jedna akcja masowa moze obejmowac maksymalnie {self.BULK_ACTION_LIMIT} dokumentow."
            )

        normalized_library_path = None
        if normalized_action == "move_folder":
            normalized_library_path = self._normalize_library_path(library_path or "")
        if normalized_action in {"set_downloadable", "set_assistant_usage"} and enabled is None:
            raise KnowledgeError("Brakuje docelowej wartosci dla akcji masowej.")

        succeeded: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []

        for document_id in document_ids:
            document = self.knowledge_repository.get_by_id(document_id, organization_id=organization_id)
            if not document:
                failed.append(
                    {
                        "knowledge_document_id": document_id,
                        "title": None,
                        "message": "Nie znaleziono dokumentu w tej organizacji.",
                    }
                )
                continue

            lifecycle_status = str(document.get("lifecycle_status") or "active")
            title = str(document.get("title") or f"Dokument #{document_id}")
            try:
                if normalized_action == "archive":
                    if lifecycle_status == "archived":
                        skipped.append(
                            {
                                "knowledge_document_id": document_id,
                                "title": title,
                                "message": "Dokument jest juz archiwalny.",
                            }
                        )
                        continue
                    if lifecycle_status == "deleted":
                        failed.append(
                            {
                                "knowledge_document_id": document_id,
                                "title": title,
                                "message": "Usuniety dokument najpierw trzeba przywrocic.",
                            }
                        )
                        continue
                    updated = self.archive_document(
                        organization_id=organization_id,
                        knowledge_document_id=document_id,
                        actor_user=actor_user,
                        actor=actor,
                    )
                elif normalized_action == "restore":
                    if lifecycle_status == "active":
                        skipped.append(
                            {
                                "knowledge_document_id": document_id,
                                "title": title,
                                "message": "Dokument jest juz aktywny.",
                            }
                        )
                        continue
                    updated = self.restore_document(
                        organization_id=organization_id,
                        knowledge_document_id=document_id,
                        actor_user=actor_user,
                        actor=actor,
                    )
                elif normalized_action == "move_folder":
                    assert normalized_library_path is not None
                    current_path = self._normalize_library_path(document.get("library_path") or "")
                    if current_path == normalized_library_path:
                        skipped.append(
                            {
                                "knowledge_document_id": document_id,
                                "title": title,
                                "message": "Dokument jest juz w tym folderze.",
                            }
                        )
                        continue
                    updated = self.update_document_metadata(
                        organization_id=organization_id,
                        knowledge_document_id=document_id,
                        actor_user=actor_user,
                        actor=actor,
                        library_path=normalized_library_path,
                    )
                elif normalized_action == "set_downloadable":
                    desired_downloadable = bool(enabled)
                    if bool(document.get("is_downloadable")) == desired_downloadable:
                        skipped.append(
                            {
                                "knowledge_document_id": document_id,
                                "title": title,
                                "message": "Widocznosc w bibliotece juz jest ustawiona w ten sposob.",
                            }
                        )
                        continue
                    updated = self.update_document_metadata(
                        organization_id=organization_id,
                        knowledge_document_id=document_id,
                        actor_user=actor_user,
                        actor=actor,
                        is_downloadable=desired_downloadable,
                    )
                else:
                    desired_assistant_usage = bool(enabled)
                    if bool(document.get("use_in_assistant")) == desired_assistant_usage:
                        skipped.append(
                            {
                                "knowledge_document_id": document_id,
                                "title": title,
                                "message": "Uzycie przez asystenta juz ma taka wartosc.",
                            }
                        )
                        continue
                    updated = self.update_document_metadata(
                        organization_id=organization_id,
                        knowledge_document_id=document_id,
                        actor_user=actor_user,
                        actor=actor,
                        use_in_assistant=desired_assistant_usage,
                    )
                succeeded.append(
                    {
                        "knowledge_document_id": int(updated["knowledge_document_id"]),
                        "title": updated["title"],
                        "lifecycle_status": updated["lifecycle_status"],
                        "library_path": updated.get("library_path") or "",
                        "is_downloadable": bool(updated.get("is_downloadable")),
                        "use_in_assistant": bool(updated.get("use_in_assistant")),
                    }
                )
            except KnowledgeError as error:
                failed.append(
                    {
                        "knowledge_document_id": document_id,
                        "title": title,
                        "message": str(error),
                    }
                )

        return {
            "action": normalized_action,
            "action_label": self.BULK_ACTION_LABELS[normalized_action],
            "requested_count": len(document_ids),
            "succeeded_count": len(succeeded),
            "skipped_count": len(skipped),
            "failed_count": len(failed),
            "target_library_path": normalized_library_path,
            "target_enabled": None if enabled is None else bool(enabled),
            "succeeded": succeeded,
            "skipped": skipped,
            "failed": failed,
        }

    def supported_formats(self) -> list[str]:
        return [
            "TXT",
            "MD",
            "CSV",
            "JSON",
            "XML",
            "HTML",
            "DOCX",
            "PDF",
            "XLSX",
            "JPG",
            "PNG",
            "TIFF",
        ]

    def _serialize_version_compare_meta(self, version: dict[str, Any]) -> dict[str, Any]:
        return {
            "version_number": int(version["version_number"]),
            "file_name": version.get("file_name"),
            "char_count": int(version.get("char_count") or 0),
            "source_type": version.get("source_type") or "manual",
            "created_at": version.get("created_at"),
            "extraction_method": version.get("extraction_method"),
        }

    def _build_side_by_side_compare_rows(
        self,
        base_lines: list[str],
        target_lines: list[str],
        matcher: SequenceMatcher,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            left_chunk = base_lines[i1:i2]
            right_chunk = target_lines[j1:j2]
            if tag == "equal":
                for offset, line in enumerate(left_chunk):
                    rows.append(
                        self._serialize_side_by_side_row(
                            row_type="context",
                            left_line_number=i1 + offset + 1,
                            right_line_number=j1 + offset + 1,
                            left_text=line,
                            right_text=line,
                        )
                    )
                continue

            pair_count = max(len(left_chunk), len(right_chunk))
            for offset in range(pair_count):
                left_text = left_chunk[offset] if offset < len(left_chunk) else ""
                right_text = right_chunk[offset] if offset < len(right_chunk) else ""
                left_line_number = i1 + offset + 1 if offset < len(left_chunk) else None
                right_line_number = j1 + offset + 1 if offset < len(right_chunk) else None
                if tag == "replace":
                    row_type = "changed"
                elif tag == "delete":
                    row_type = "removed"
                else:
                    row_type = "added"
                rows.append(
                    self._serialize_side_by_side_row(
                        row_type=row_type,
                        left_line_number=left_line_number,
                        right_line_number=right_line_number,
                        left_text=left_text,
                        right_text=right_text,
                    )
                )
        return rows

    def _serialize_side_by_side_row(
        self,
        *,
        row_type: str,
        left_line_number: int | None,
        right_line_number: int | None,
        left_text: str,
        right_text: str,
    ) -> dict[str, Any]:
        return {
            "type": row_type,
            "left_line_number": left_line_number,
            "right_line_number": right_line_number,
            "left_text": self._truncate_compare_row_text(left_text),
            "right_text": self._truncate_compare_row_text(right_text),
        }

    def _truncate_compare_row_text(self, value: str) -> str:
        normalized = re.sub(r"\s+", " ", str(value or "").strip())
        if len(normalized) <= self.COMPARE_MAX_ROW_TEXT_LENGTH:
            return normalized
        return f"{normalized[: self.COMPARE_MAX_ROW_TEXT_LENGTH].rstrip()}..."

    def _build_version_change_summary(
        self,
        *,
        base_version: dict[str, Any],
        target_version: dict[str, Any],
        base_lines: list[str],
        target_lines: list[str],
        added_lines: list[str],
        removed_lines: list[str],
        changed_block_count: int,
        similarity_ratio: float,
    ) -> dict[str, Any]:
        base_number = int(base_version.get("version_number") or 0)
        target_number = int(target_version.get("version_number") or 0)
        added_line_count = len(added_lines)
        removed_line_count = len(removed_lines)
        line_delta = len(target_lines) - len(base_lines)
        char_delta = int(target_version.get("char_count") or 0) - int(base_version.get("char_count") or 0)

        if changed_block_count == 0:
            return {
                "change_kind": "no_change",
                "impact_level": "minor",
                "impact_label": "brak zmian",
                "overview": f"Wersje v{target_number} i v{base_number} sa tekstowo identyczne.",
                "line_delta": line_delta,
                "char_delta": char_delta,
                "key_changes": [],
                "added_topics": [],
                "removed_topics": [],
                "added_keywords": [],
                "removed_keywords": [],
            }

        if added_line_count >= removed_line_count * 1.5 and line_delta >= 0:
            change_kind = "expansion"
            change_kind_label = "rozszerza dokument"
        elif removed_line_count >= added_line_count * 1.5 and line_delta <= 0:
            change_kind = "reduction"
            change_kind_label = "upraszcza lub skraca dokument"
        else:
            change_kind = "mixed"
            change_kind_label = "miesza rozszerzenia z korektami"

        if similarity_ratio < 0.65 or changed_block_count >= 5 or abs(line_delta) >= 6:
            impact_level = "major"
            impact_label = "duza aktualizacja"
        elif similarity_ratio < 0.85 or changed_block_count >= 2 or abs(line_delta) >= 2:
            impact_level = "moderate"
            impact_label = "srednia aktualizacja"
        else:
            impact_level = "minor"
            impact_label = "lekka korekta"

        if char_delta > 0:
            volume_note = f"objetosc wzrosla o {char_delta} znakow"
        elif char_delta < 0:
            volume_note = f"objetosc spadla o {abs(char_delta)} znakow"
        else:
            volume_note = "objetosc dokumentu pozostala zblizona"

        added_topics = self._select_compare_topics(added_lines)
        removed_topics = self._select_compare_topics(removed_lines)
        added_keywords = self._extract_compare_keywords(added_lines, removed_lines)
        removed_keywords = self._extract_compare_keywords(removed_lines, added_lines)

        key_changes: list[str] = []
        if added_topics:
            key_changes.append("Nowe akcenty: " + "; ".join(added_topics) + ".")
        if removed_topics:
            key_changes.append("Tylko w starszej wersji zostaly: " + "; ".join(removed_topics) + ".")
        if added_keywords:
            key_changes.append("Mocniej zaakcentowano tematy: " + ", ".join(added_keywords) + ".")
        if removed_keywords:
            key_changes.append("Slabiej widoczne sa tematy: " + ", ".join(removed_keywords) + ".")

        return {
            "change_kind": change_kind,
            "impact_level": impact_level,
            "impact_label": impact_label,
            "overview": (
                f"Nowsza wersja v{target_number} {change_kind_label} wzgledem v{base_number}: "
                f"dodano {added_line_count} linii, usunieto {removed_line_count}, a {volume_note}."
            ),
            "line_delta": line_delta,
            "char_delta": char_delta,
            "key_changes": key_changes[:4],
            "added_topics": added_topics,
            "removed_topics": removed_topics,
            "added_keywords": added_keywords,
            "removed_keywords": removed_keywords,
        }

    def _select_compare_topics(self, lines: list[str]) -> list[str]:
        ranked: list[tuple[float, str]] = []
        seen: set[str] = set()
        for raw_line in lines:
            candidate = re.sub(r"\s+", " ", str(raw_line or "").strip())
            if len(candidate) < 12:
                continue
            candidate = candidate[:140].rstrip(" ,.;")
            key = candidate.lower()
            if key in seen:
                continue
            seen.add(key)
            token_count = len(self._tokenize(candidate))
            score = (token_count * 3.0) + min(len(candidate), 140) / 20.0
            if ":" in candidate:
                score += 2.0
            if any(character.isdigit() for character in candidate):
                score += 1.0
            ranked.append((score, candidate))
        return [item[1] for item in sorted(ranked, key=lambda entry: (-entry[0], entry[1]))[: self.COMPARE_TOPIC_LIMIT]]

    def _extract_compare_keywords(self, primary_lines: list[str], secondary_lines: list[str]) -> list[str]:
        primary_counter = Counter(
            token
            for line in primary_lines
            for token in self._tokenize(line)
            if len(token) >= 4 and not token.isdigit()
        )
        secondary_tokens = {
            token
            for line in secondary_lines
            for token in self._tokenize(line)
            if len(token) >= 4 and not token.isdigit()
        }
        keywords: list[str] = []
        for token, _count in primary_counter.most_common():
            if token in secondary_tokens or token in keywords:
                continue
            keywords.append(token)
            if len(keywords) >= self.COMPARE_KEYWORD_LIMIT:
                break
        return keywords

    def _normalize_bulk_document_ids(self, knowledge_document_ids: list[Any]) -> list[int]:
        normalized: list[int] = []
        seen: set[int] = set()
        for raw_value in knowledge_document_ids or []:
            try:
                document_id = int(raw_value)
            except (TypeError, ValueError):
                continue
            if document_id <= 0 or document_id in seen:
                continue
            seen.add(document_id)
            normalized.append(document_id)
        return normalized

    def _prepare_text_lines_for_compare(self, text: str) -> list[str]:
        normalized = self._normalize_content_text(text)
        if not normalized:
            return []
        return [line.strip() for line in normalized.splitlines() if line.strip()]

    def _build_version_compare_block(self, block_type: str, lines: list[str]) -> dict[str, Any] | None:
        if not lines:
            return None
        normalized_type = str(block_type or "context")
        line_count = len(lines)
        collapsed_line_count = 0
        if normalized_type == "context" and line_count > self.COMPARE_CONTEXT_EDGE_LINES * 2:
            kept_lines = lines[: self.COMPARE_CONTEXT_EDGE_LINES] + lines[-self.COMPARE_CONTEXT_EDGE_LINES :]
            collapsed_line_count = line_count - len(kept_lines)
        elif normalized_type in {"added", "removed"} and line_count > self.COMPARE_MAX_LINES_PER_BLOCK:
            kept_lines = lines[: self.COMPARE_MAX_LINES_PER_BLOCK]
            collapsed_line_count = line_count - len(kept_lines)
        else:
            kept_lines = lines

        return {
            "type": normalized_type,
            "line_count": line_count,
            "collapsed_line_count": collapsed_line_count,
            "lines": kept_lines,
        }

    def add_document(
        self,
        *,
        organization_id: int,
        title: str,
        actor_user: dict[str, Any],
        actor: str,
        file_name: str | None = None,
        content_text: str | None = None,
        file_bytes: bytes | None = None,
        mime_type: str | None = None,
        library_path: str | None = None,
        is_downloadable: bool = True,
        use_in_assistant: bool = True,
    ) -> dict[str, Any]:
        organization = self._resolve_organization(organization_id)
        normalized_title = (title or "").strip()
        normalized_file_name = (file_name or "").strip()
        supplemental_text = self._normalize_content_text(content_text or "")
        normalized_library_path = self._normalize_library_path(library_path or "")
        if file_bytes is None and not supplemental_text:
            raise KnowledgeError("Dodaj plik albo wklej treść dokumentu.")

        if file_bytes is not None:
            if not normalized_file_name:
                raise KnowledgeError("Brakuje nazwy pliku.")
            self._validate_file_payload(normalized_file_name, file_bytes)
            if not supplemental_text and not self._supports_text_extraction(normalized_file_name, mime_type):
                supplemental_text = self._build_storage_only_description(
                    normalized_file_name,
                    normalized_library_path,
                )
                use_in_assistant = False
            stored_name = self._build_stored_file_name(normalized_file_name, file_bytes)
            relative_path = self._build_upload_relative_path(organization["slug"], stored_name)
            artifact = self.storage_service.save_binary("knowledge", relative_path, file_bytes)
            source_type = "upload"
            source_hash = hashlib.sha256(file_bytes).hexdigest()
            resolved_mime_type = mime_type or mimetypes.guess_type(normalized_file_name)[0] or "application/octet-stream"
        else:
            normalized_file_name = normalized_file_name or self._default_file_name(normalized_title)
            normalized_file_name = self._ensure_text_extension(normalized_file_name)
            raw_text = supplemental_text.encode("utf-8")
            stored_name = self._build_stored_file_name(normalized_file_name, raw_text)
            relative_path = self._build_upload_relative_path(organization["slug"], stored_name)
            artifact = self.storage_service.save_text("knowledge", relative_path, supplemental_text)
            source_type = "manual"
            source_hash = hashlib.sha256(raw_text).hexdigest()
            resolved_mime_type = "text/plain"

        normalized_title = (
            normalized_title
            or Path(normalized_file_name).stem.replace("_", " ").replace("-", " ").strip()
            or "Dokument"
        )
        document_id = self.knowledge_repository.create(
            {
                "organization_id": int(organization["organization_id"]),
                "title": normalized_title,
                "file_name": normalized_file_name,
                "mime_type": resolved_mime_type,
                "file_link": artifact.public_link,
                "file_storage_key": artifact.storage_key,
                "content_text": supplemental_text,
                "content_hash": source_hash,
                "char_count": len(supplemental_text),
                "source_type": source_type,
                "library_path": normalized_library_path,
                "is_downloadable": bool(is_downloadable),
                "use_in_assistant": bool(use_in_assistant),
                "business_status": "roboczy",
                "lifecycle_status": "active",
                "processing_status": "queued",
                "processing_error": None,
                "current_version_number": 0,
                "owner_user_id": actor_user.get("user_id"),
                "created_by_user_id": actor_user.get("user_id"),
            }
        )
        job_id = self.knowledge_repository.create_job(
            {
                "organization_id": int(organization["organization_id"]),
                "knowledge_document_id": document_id,
                "job_type": "ingest",
                "source_storage_key": artifact.storage_key,
                "source_file_name": normalized_file_name,
                "source_mime_type": resolved_mime_type,
                "source_type": source_type,
                "source_content_hash": source_hash,
                "supplemental_text": supplemental_text,
                "created_by_user_id": actor_user.get("user_id"),
            }
        )
        created = self.knowledge_repository.get_by_id(document_id, organization_id=int(organization["organization_id"]))
        assert created is not None
        self._refresh_document_relationships(document_id, int(organization["organization_id"]))
        created = self.knowledge_repository.get_by_id(document_id, organization_id=int(organization["organization_id"]))
        assert created is not None
        self.event_repository.log(
            event_type="knowledge_document_created",
            invoice_id=None,
            organization_id=int(organization["organization_id"]),
            source="WIEDZA",
            status_before=None,
            status_after=None,
            decision_reason=f"Dodano dokument bazy wiedzy do kolejki: {created['title']}.",
            actor=actor,
            details={
                "knowledge_document_id": document_id,
                "knowledge_processing_job_id": job_id,
                "file_name": created["file_name"],
                "file_link": created["file_link"],
                "source_type": created["source_type"],
                "library_path": created.get("library_path") or "",
                "is_downloadable": bool(created.get("is_downloadable")),
                "use_in_assistant": bool(created.get("use_in_assistant")),
                "business_status": created.get("business_status") or "roboczy",
                "lifecycle_status": created.get("lifecycle_status") or "active",
                "processing_status": "queued",
            },
        )
        return self._serialize_document(created)

    def sync_folder(
        self,
        *,
        organization_id: int,
        actor_user: dict[str, Any],
        actor: str,
    ) -> dict[str, Any]:
        organization = self._resolve_organization(organization_id)
        folder_path = self._organization_folder_path(organization["slug"])
        folder_path.mkdir(parents=True, exist_ok=True)

        started_at = now_iso()
        self.knowledge_repository.upsert_watch_status(
            int(organization["organization_id"]),
            {
                "watch_mode": "polling",
                "last_scan_started_at": started_at,
                "last_scan_status": "running",
                "last_actor": actor,
                "last_error": None,
            },
        )

        queued_new = 0
        queued_updates = 0
        unchanged_count = 0
        duplicate_count = 0
        similar_count = 0
        skipped: list[dict[str, str]] = []

        try:
            for file_path in self._iter_organization_files(folder_path):
                file_bytes = file_path.read_bytes()
                if len(file_bytes) > self.MAX_UPLOAD_BYTES:
                    skipped.append(
                        {
                            "file_name": file_path.name,
                            "reason": f"Przekroczono limit {round(self.MAX_UPLOAD_BYTES / (1024 * 1024), 1)} MB.",
                        }
                    )
                    continue
                source_hash = hashlib.sha256(file_bytes).hexdigest()
                file_storage_key = file_path.relative_to(KNOWLEDGE_DIR).as_posix()
                existing = self.knowledge_repository.get_by_storage_key(
                    int(organization["organization_id"]),
                    file_storage_key,
                )
                if (
                    existing
                    and existing.get("content_hash") == source_hash
                    and existing.get("processing_status") in {"queued", "processing", "ready"}
                    and str(existing.get("lifecycle_status") or "active") != "deleted"
                ):
                    unchanged_count += 1
                    self.knowledge_repository.update(
                        int(existing["knowledge_document_id"]),
                        {"last_seen_in_folder_at": now_iso()},
                    )
                    continue

                detected_extractable = self._supports_text_extraction(
                    file_path.name,
                    mimetypes.guess_type(str(file_path))[0],
                )
                payload = {
                    "title": file_path.stem.replace("_", " ").replace("-", " ").strip() or file_path.stem,
                    "file_name": file_path.name,
                    "mime_type": mimetypes.guess_type(str(file_path))[0] or "application/octet-stream",
                    "file_link": self.storage_service.build_public_link("knowledge", file_storage_key),
                    "file_storage_key": file_storage_key,
                    "content_hash": source_hash,
                    "source_type": "folder_sync",
                    "library_path": self._library_path_from_relative_file(file_path, folder_path),
                    "is_downloadable": True,
                    "use_in_assistant": bool(detected_extractable),
                    "lifecycle_status": "active",
                    "processing_status": "queued",
                    "processing_error": None,
                    "processing_started_at": None,
                    "business_status": (
                        self._business_status_after_new_version(existing)
                        if existing is not None
                        else "roboczy"
                    ),
                    "owner_user_id": (
                        actor_user.get("user_id")
                        if existing is None
                        else existing.get("owner_user_id")
                    ),
                    "created_by_user_id": actor_user.get("user_id"),
                    "last_seen_in_folder_at": now_iso(),
                }
                supplemental_text = (
                    ""
                    if detected_extractable
                    else self._build_storage_only_description(
                        file_path.name,
                        payload["library_path"],
                    )
                )

                if existing is None:
                    document_id = self.knowledge_repository.create(
                        {
                            "organization_id": int(organization["organization_id"]),
                            "content_text": supplemental_text,
                            "char_count": len(supplemental_text),
                            "current_version_number": 0,
                            **payload,
                        }
                    )
                    queued_new += 1
                else:
                    document_id = int(existing["knowledge_document_id"])
                    self.knowledge_repository.update(document_id, payload)
                    queued_updates += 1

                self.knowledge_repository.create_job(
                    {
                        "organization_id": int(organization["organization_id"]),
                        "knowledge_document_id": document_id,
                        "job_type": "ingest",
                        "source_storage_key": file_storage_key,
                        "source_file_name": file_path.name,
                        "source_mime_type": payload["mime_type"],
                        "source_type": "folder_sync",
                        "source_content_hash": source_hash,
                        "supplemental_text": supplemental_text,
                        "created_by_user_id": actor_user.get("user_id"),
                    }
                )
                self._refresh_document_relationships(document_id, int(organization["organization_id"]))
                refreshed = self.knowledge_repository.get_by_id(
                    document_id,
                    organization_id=int(organization["organization_id"]),
                )
                if refreshed:
                    duplicate_status = str(refreshed.get("duplicate_status") or "none")
                    if duplicate_status == "exact_duplicate":
                        duplicate_count += 1
                    elif duplicate_status == "similar_version":
                        similar_count += 1
        except Exception as error:
            self.knowledge_repository.upsert_watch_status(
                int(organization["organization_id"]),
                {
                    "watch_mode": "polling",
                    "last_scan_completed_at": now_iso(),
                    "last_scan_status": "error",
                    "last_actor": actor,
                    "last_error": str(error),
                    "queued_new": queued_new,
                    "queued_updates": queued_updates,
                    "unchanged_count": unchanged_count,
                    "skipped_count": len(skipped),
                    "duplicate_count": duplicate_count,
                    "similar_count": similar_count,
                },
            )
            raise

        self.event_repository.log(
            event_type="knowledge_sync_executed",
            invoice_id=None,
            organization_id=int(organization["organization_id"]),
            source="WIEDZA",
            status_before=None,
            status_after=None,
            decision_reason="Wykonano synchronizację folderu bazy wiedzy.",
            actor=actor,
            details={
                "queued_new": queued_new,
                "queued_updates": queued_updates,
                "unchanged_count": unchanged_count,
                "skipped_count": len(skipped),
                "duplicate_count": duplicate_count,
                "similar_count": similar_count,
            },
        )
        self.event_repository.log(
            event_type="knowledge_watch_scan",
            invoice_id=None,
            organization_id=int(organization["organization_id"]),
            source="WIEDZA",
            status_before=None,
            status_after=None,
            decision_reason="Watcher bazy wiedzy zakonczyl skan folderu organizacji.",
            actor=actor,
            details={
                "watch_mode": "polling",
                "queued_new": queued_new,
                "queued_updates": queued_updates,
                "unchanged_count": unchanged_count,
                "skipped_count": len(skipped),
                "duplicate_count": duplicate_count,
                "similar_count": similar_count,
            },
        )
        self.knowledge_repository.upsert_watch_status(
            int(organization["organization_id"]),
            {
                "watch_mode": "polling",
                "last_scan_completed_at": now_iso(),
                "last_scan_status": "ok",
                "last_actor": actor,
                "last_error": None,
                "queued_new": queued_new,
                "queued_updates": queued_updates,
                "unchanged_count": unchanged_count,
                "skipped_count": len(skipped),
                "duplicate_count": duplicate_count,
                "similar_count": similar_count,
            },
        )
        return {
            "organization_id": organization["organization_id"],
            "organization_name": organization["name"],
            "folder_path": str(folder_path),
            "imported_count": queued_new,
            "updated_count": queued_updates,
            "queued_new": queued_new,
            "queued_updates": queued_updates,
            "unchanged_count": unchanged_count,
            "duplicate_count": duplicate_count,
            "similar_count": similar_count,
            "skipped": skipped,
        }

    def update_document_metadata(
        self,
        *,
        organization_id: int,
        knowledge_document_id: int,
        actor_user: dict[str, Any],
        actor: str,
        title: str | None = None,
        library_path: str | None = None,
        is_downloadable: bool | None = None,
        use_in_assistant: bool | None = None,
        business_status: str | None = None,
        owner_user_id: Any = ...,
        reviewer_user_id: Any = ...,
        approver_user_id: Any = ...,
    ) -> dict[str, Any]:
        document = self.knowledge_repository.get_by_id(knowledge_document_id, organization_id=organization_id)
        if not document:
            raise KnowledgeError("Nie znaleziono dokumentu bazy wiedzy.")
        if str(document.get("lifecycle_status") or "active") == "deleted":
            raise KnowledgeError("Najpierw przywroc dokument, aby zmienic jego ustawienia.")

        fields: dict[str, Any] = {}
        generic_field_changes = False
        business_status_changed = False
        assignments_changed = False
        if title is not None:
            normalized_title = str(title or "").strip()
            if normalized_title and normalized_title != str(document.get("title") or "").strip():
                fields["title"] = normalized_title
                generic_field_changes = True
        if library_path is not None:
            normalized_library_path = self._normalize_library_path(library_path)
            if normalized_library_path != self._normalize_library_path(document.get("library_path") or ""):
                fields["library_path"] = normalized_library_path
                generic_field_changes = True
        if is_downloadable is not None:
            normalized_downloadable = bool(is_downloadable)
            if normalized_downloadable != bool(document.get("is_downloadable", 1)):
                fields["is_downloadable"] = normalized_downloadable
                generic_field_changes = True
        if use_in_assistant is not None:
            normalized_use_in_assistant = bool(use_in_assistant)
            if normalized_use_in_assistant != bool(document.get("use_in_assistant", 1)):
                fields["use_in_assistant"] = normalized_use_in_assistant
                generic_field_changes = True
        if business_status is not None:
            normalized_business_status = self._normalize_business_status(business_status, strict=True)
            current_business_status = self._normalize_business_status(
                document.get("business_status") or self._derive_business_status_from_document(document)
            )
            lifecycle_status = str(document.get("lifecycle_status") or "active")
            if lifecycle_status == "archived" and normalized_business_status != "archiwalny":
                raise KnowledgeError("Przywroc dokument przed zmiana jego stanu obiegu.")
            if lifecycle_status != "archived" and normalized_business_status == "archiwalny":
                raise KnowledgeError("Aby ustawic stan archiwalny, uzyj akcji archiwizacji dokumentu.")
            if normalized_business_status != current_business_status:
                fields["business_status"] = normalized_business_status
                business_status_changed = True

        assignment_candidates = None
        previous_assignments = {
            "owner_user_id": self._parse_optional_positive_int(document.get("owner_user_id")),
            "reviewer_user_id": self._parse_optional_positive_int(document.get("reviewer_user_id")),
            "approver_user_id": self._parse_optional_positive_int(document.get("approver_user_id")),
        }
        assignment_labels = {
            "owner_user_id": "Prowadzi",
            "reviewer_user_id": "Sprawdza",
            "approver_user_id": "Akceptuje",
        }
        for field_name, raw_value in (
            ("owner_user_id", owner_user_id),
            ("reviewer_user_id", reviewer_user_id),
            ("approver_user_id", approver_user_id),
        ):
            if raw_value is ...:
                continue
            normalized_user_id = self._parse_assignment_user_id(raw_value)
            if assignment_candidates is None:
                assignment_candidates = {
                    int(item["user_id"]): item for item in self.list_assignment_candidates(organization_id)
                }
            if normalized_user_id is not None and normalized_user_id not in assignment_candidates:
                raise KnowledgeError(f"{assignment_labels[field_name]} musi byc aktywnym czlonkiem tej organizacji.")
            if normalized_user_id != previous_assignments[field_name]:
                fields[field_name] = normalized_user_id
                assignments_changed = True

        if not fields:
            return self._serialize_document(document)

        self.knowledge_repository.update(knowledge_document_id, fields)
        refreshed = self.knowledge_repository.get_by_id(knowledge_document_id, organization_id=organization_id)
        assert refreshed is not None

        if generic_field_changes:
            self.event_repository.log(
                event_type="knowledge_document_updated",
                invoice_id=None,
                organization_id=organization_id,
                source="WIEDZA",
                status_before=None,
                status_after=None,
                decision_reason=f"Zmieniono metadane dokumentu: {refreshed['title']}.",
                actor=actor,
                details={
                    "knowledge_document_id": knowledge_document_id,
                    "title": refreshed["title"],
                    "library_path": refreshed.get("library_path") or "",
                    "is_downloadable": bool(refreshed.get("is_downloadable")),
                    "use_in_assistant": bool(refreshed.get("use_in_assistant")),
                    "updated_by_user_id": actor_user.get("user_id"),
                },
            )
        if business_status_changed:
            previous_status = self._normalize_business_status(
                document.get("business_status") or self._derive_business_status_from_document(document)
            )
            next_status = self._normalize_business_status(
                refreshed.get("business_status") or self._derive_business_status_from_document(refreshed)
            )
            self.event_repository.log(
                event_type="knowledge_document_workflow_updated",
                invoice_id=None,
                organization_id=organization_id,
                source="WIEDZA",
                status_before=previous_status,
                status_after=next_status,
                decision_reason=(
                    f"Zmieniono stan obiegu dokumentu {refreshed['title']}: "
                    f"{self.BUSINESS_STATUS_LABELS.get(previous_status, previous_status)} -> "
                    f"{self.BUSINESS_STATUS_LABELS.get(next_status, next_status)}."
                ),
                actor=actor,
                details={
                    "knowledge_document_id": knowledge_document_id,
                    "title": refreshed["title"],
                    "previous_business_status": previous_status,
                    "business_status": next_status,
                    "updated_by_user_id": actor_user.get("user_id"),
                },
            )
        if assignments_changed:
            self.event_repository.log(
                event_type="knowledge_document_assignments_updated",
                invoice_id=None,
                organization_id=organization_id,
                source="WIEDZA",
                status_before=None,
                status_after=None,
                decision_reason=f"Zmieniono osoby odpowiedzialne za dokument: {refreshed['title']}.",
                actor=actor,
                details={
                    "knowledge_document_id": knowledge_document_id,
                    "title": refreshed["title"],
                    "owner_user_id": refreshed.get("owner_user_id"),
                    "owner_user_label": self._assignee_label(refreshed, "owner"),
                    "reviewer_user_id": refreshed.get("reviewer_user_id"),
                    "reviewer_user_label": self._assignee_label(refreshed, "reviewer"),
                    "approver_user_id": refreshed.get("approver_user_id"),
                    "approver_user_label": self._assignee_label(refreshed, "approver"),
                    "updated_by_user_id": actor_user.get("user_id"),
                },
            )
        return self._serialize_document(refreshed)

    def replace_document_file(
        self,
        *,
        organization_id: int,
        knowledge_document_id: int,
        actor_user: dict[str, Any],
        actor: str,
        file_name: str,
        file_bytes: bytes,
        mime_type: str | None = None,
        content_text: str | None = None,
    ) -> dict[str, Any]:
        document = self.knowledge_repository.get_by_id(knowledge_document_id, organization_id=organization_id)
        if not document:
            raise KnowledgeError("Nie znaleziono dokumentu bazy wiedzy.")
        if str(document.get("lifecycle_status") or "active") == "deleted":
            raise KnowledgeError("Najpierw przywroc dokument, a dopiero potem podmien jego plik.")
        normalized_file_name = str(file_name or "").strip()
        if not normalized_file_name:
            raise KnowledgeError("Brakuje nazwy nowego pliku.")
        self._validate_file_payload(normalized_file_name, file_bytes)
        organization = self._resolve_organization(organization_id)
        normalized_description = self._normalize_content_text(content_text or "")
        if not normalized_description and not self._supports_text_extraction(normalized_file_name, mime_type):
            normalized_description = self._build_storage_only_description(
                normalized_file_name,
                self._normalize_library_path(document.get("library_path") or ""),
            )
        stored_name = self._build_stored_file_name(normalized_file_name, file_bytes)
        artifact = self.storage_service.save_binary(
            "knowledge",
            self._build_upload_relative_path(organization["slug"], stored_name),
            file_bytes,
        )
        source_hash = hashlib.sha256(file_bytes).hexdigest()
        resolved_mime_type = mime_type or mimetypes.guess_type(normalized_file_name)[0] or "application/octet-stream"
        use_in_assistant = bool(document.get("use_in_assistant", 1)) and self._supports_text_extraction(
            normalized_file_name,
            resolved_mime_type,
        )

        self.knowledge_repository.update(
            knowledge_document_id,
            {
                "file_name": normalized_file_name,
                "mime_type": resolved_mime_type,
                "file_link": artifact.public_link,
                "file_storage_key": artifact.storage_key,
                "content_hash": source_hash,
                "processing_status": "queued",
                "processing_error": None,
                "processing_started_at": None,
                "use_in_assistant": use_in_assistant,
                "business_status": self._business_status_after_new_version(document),
            },
        )
        job_id = self.knowledge_repository.create_job(
            {
                "organization_id": organization_id,
                "knowledge_document_id": knowledge_document_id,
                "job_type": "replace",
                "source_storage_key": artifact.storage_key,
                "source_file_name": normalized_file_name,
                "source_mime_type": resolved_mime_type,
                "source_type": document.get("source_type") or "upload",
                "source_content_hash": source_hash,
                "supplemental_text": normalized_description,
                "created_by_user_id": actor_user.get("user_id"),
            }
        )
        self._refresh_document_relationships(knowledge_document_id, organization_id)
        refreshed = self.knowledge_repository.get_by_id(knowledge_document_id, organization_id=organization_id)
        assert refreshed is not None
        self.event_repository.log(
            event_type="knowledge_document_replaced",
            invoice_id=None,
            organization_id=organization_id,
            source="WIEDZA",
            status_before=None,
            status_after=None,
            decision_reason=f"Podmieniono plik dokumentu: {refreshed['title']}.",
            actor=actor,
            details={
                "knowledge_document_id": knowledge_document_id,
                "title": refreshed["title"],
                "knowledge_processing_job_id": job_id,
                "file_name": normalized_file_name,
                "use_in_assistant": bool(refreshed.get("use_in_assistant")),
                "business_status": refreshed.get("business_status") or "roboczy",
            },
        )
        return self._serialize_document(refreshed)

    def archive_document(
        self,
        *,
        organization_id: int,
        knowledge_document_id: int,
        actor_user: dict[str, Any],
        actor: str,
    ) -> dict[str, Any]:
        return self._set_document_lifecycle(
            organization_id=organization_id,
            knowledge_document_id=knowledge_document_id,
            lifecycle_status="archived",
            actor_user=actor_user,
            actor=actor,
            event_type="knowledge_document_archived",
            reason_prefix="Zarchiwizowano dokument",
        )

    def restore_document(
        self,
        *,
        organization_id: int,
        knowledge_document_id: int,
        actor_user: dict[str, Any],
        actor: str,
    ) -> dict[str, Any]:
        return self._set_document_lifecycle(
            organization_id=organization_id,
            knowledge_document_id=knowledge_document_id,
            lifecycle_status="active",
            actor_user=actor_user,
            actor=actor,
            event_type="knowledge_document_restored",
            reason_prefix="Przywrocono dokument",
        )

    def delete_document(
        self,
        *,
        organization_id: int,
        knowledge_document_id: int,
        actor_user: dict[str, Any],
        actor: str,
    ) -> dict[str, Any]:
        return self._set_document_lifecycle(
            organization_id=organization_id,
            knowledge_document_id=knowledge_document_id,
            lifecycle_status="deleted",
            actor_user=actor_user,
            actor=actor,
            event_type="knowledge_document_deleted",
            reason_prefix="Usunieto dokument",
        )

    def restore_document_version(
        self,
        *,
        organization_id: int,
        knowledge_document_id: int,
        version_number: int,
        actor_user: dict[str, Any],
        actor: str,
    ) -> dict[str, Any]:
        document = self.knowledge_repository.get_by_id(knowledge_document_id, organization_id=organization_id)
        if not document:
            raise KnowledgeError("Nie znaleziono dokumentu bazy wiedzy.")
        version = self.knowledge_repository.get_version_by_number(knowledge_document_id, int(version_number))
        if not version:
            raise KnowledgeError("Nie znaleziono wskazanej wersji dokumentu.")
        self.knowledge_repository.update(
            knowledge_document_id,
            {
                "processing_status": "queued",
                "processing_error": None,
                "processing_started_at": None,
                "business_status": self._business_status_after_new_version(document),
            },
        )
        job_id = self.knowledge_repository.create_job(
            {
                "organization_id": organization_id,
                "knowledge_document_id": knowledge_document_id,
                "job_type": "restore_version",
                "source_storage_key": version["file_storage_key"],
                "source_file_name": version["file_name"],
                "source_mime_type": version.get("mime_type"),
                "source_type": version.get("source_type") or document.get("source_type") or "manual",
                "source_content_hash": version["content_hash"],
                "supplemental_text": version.get("content_text") or "",
                "created_by_user_id": actor_user.get("user_id"),
            }
        )
        self.event_repository.log(
            event_type="knowledge_document_version_restored",
            invoice_id=None,
            organization_id=organization_id,
            source="WIEDZA",
            status_before=None,
            status_after=None,
            decision_reason=f"Przywrocono wersje v{int(version_number)} dokumentu: {document['title']}.",
            actor=actor,
            details={
                "knowledge_document_id": knowledge_document_id,
                "title": document["title"],
                "knowledge_processing_job_id": job_id,
                "restored_from_version_number": int(version_number),
                "business_status": self._business_status_after_new_version(document),
            },
        )
        refreshed = self.knowledge_repository.get_by_id(knowledge_document_id, organization_id=organization_id)
        assert refreshed is not None
        return self._serialize_document(refreshed)

    def mark_document_official_version(
        self,
        *,
        organization_id: int,
        knowledge_document_id: int,
        version_number: int,
        actor_user: dict[str, Any],
        actor: str,
    ) -> dict[str, Any]:
        document = self.knowledge_repository.get_by_id(knowledge_document_id, organization_id=organization_id)
        if not document:
            raise KnowledgeError("Nie znaleziono dokumentu bazy wiedzy.")
        if str(document.get("lifecycle_status") or "active") == "deleted":
            raise KnowledgeError("Nie mozna oznaczyc wersji obowiazujacej dla usunietego dokumentu.")

        version = self.knowledge_repository.get_version_by_number(knowledge_document_id, int(version_number))
        if not version:
            raise KnowledgeError("Nie znaleziono wskazanej wersji dokumentu.")

        normalized_version_number = int(version["version_number"])
        previous_official_version = int(document.get("official_version_number") or 0)
        if previous_official_version == normalized_version_number:
            return self._serialize_document(document, include_audit=True, include_comments=True, include_full_content=True)

        marked_at = now_iso()
        self.knowledge_repository.update(
            knowledge_document_id,
            {
                "official_version_number": normalized_version_number,
                "official_version_marked_at": marked_at,
                "official_version_marked_by_user_id": actor_user.get("user_id"),
                "business_status": self._business_status_after_marking_official(document),
            },
        )
        refreshed = self.knowledge_repository.get_by_id(knowledge_document_id, organization_id=organization_id)
        assert refreshed is not None
        self.event_repository.log(
            event_type="knowledge_document_official_version_marked",
            invoice_id=None,
            organization_id=organization_id,
            source="WIEDZA",
            status_before=None,
            status_after=None,
            decision_reason=(
                f"Oznaczono wersje v{normalized_version_number} jako obowiazujaca dla dokumentu: {refreshed['title']}."
            ),
            actor=actor,
            details={
                "knowledge_document_id": knowledge_document_id,
                "title": refreshed["title"],
                "version_number": normalized_version_number,
                "previous_official_version_number": previous_official_version or None,
                "official_version_marked_by_user_id": actor_user.get("user_id"),
                "official_version_marked_at": marked_at,
                "previous_business_status": self._normalize_business_status(
                    document.get("business_status") or self._derive_business_status_from_document(document)
                ),
                "business_status": self._normalize_business_status(
                    refreshed.get("business_status") or self._derive_business_status_from_document(refreshed)
                ),
            },
        )
        return self._serialize_document(refreshed, include_audit=True, include_comments=True, include_full_content=True)

    def add_document_comment(
        self,
        *,
        organization_id: int,
        knowledge_document_id: int,
        note_text: str,
        actor_user: dict[str, Any],
        actor: str,
        version_number: int | None = None,
        annotation_kind: str = "comment",
        anchor_label: str | None = None,
        anchor_excerpt: str | None = None,
    ) -> dict[str, Any]:
        document = self.knowledge_repository.get_by_id(knowledge_document_id, organization_id=organization_id)
        if not document:
            raise KnowledgeError("Nie znaleziono dokumentu bazy wiedzy.")
        if str(document.get("lifecycle_status") or "active") == "deleted":
            raise KnowledgeError("Nie mozna dodawac komentarzy do usunietego dokumentu.")

        normalized_note_text = self._normalize_content_text(note_text or "")
        if not normalized_note_text:
            raise KnowledgeError("Wpisz tresc komentarza albo adnotacji.")

        normalized_annotation_kind = self._normalize_annotation_kind(annotation_kind)
        normalized_anchor_label = self._normalize_comment_anchor_text(anchor_label)
        normalized_anchor_excerpt = self._normalize_comment_anchor_text(anchor_excerpt, limit=220)

        target_version_number = self._parse_optional_positive_int(version_number)
        target_version = None
        if target_version_number is not None:
            target_version = self.knowledge_repository.get_version_by_number(knowledge_document_id, target_version_number)
            if not target_version:
                raise KnowledgeError("Nie znaleziono wskazanej wersji dokumentu dla komentarza.")
            target_version_number = int(target_version["version_number"])

        comment_id = self.knowledge_repository.create_comment(
            {
                "knowledge_document_id": knowledge_document_id,
                "organization_id": organization_id,
                "knowledge_document_version_id": (
                    int(target_version["knowledge_document_version_id"]) if target_version is not None else None
                ),
                "version_number": target_version_number,
                "annotation_kind": normalized_annotation_kind,
                "anchor_label": normalized_anchor_label,
                "anchor_excerpt": normalized_anchor_excerpt,
                "note_text": normalized_note_text,
                "created_by_user_id": actor_user.get("user_id"),
            }
        )

        self.event_repository.log(
            event_type="knowledge_document_comment_added",
            invoice_id=None,
            organization_id=organization_id,
            source="WIEDZA",
            status_before=None,
            status_after=None,
            decision_reason=f"Dodano wpis do dokumentu: {document['title']}.",
            actor=actor,
            details={
                "knowledge_document_id": knowledge_document_id,
                "title": document["title"],
                "knowledge_document_comment_id": comment_id,
                "version_number": target_version_number,
                "annotation_kind": normalized_annotation_kind,
                "anchor_label": normalized_anchor_label,
                "anchor_excerpt": normalized_anchor_excerpt,
            },
        )

        refreshed = self.knowledge_repository.get_by_id(knowledge_document_id, organization_id=organization_id)
        assert refreshed is not None
        return self._serialize_document(refreshed, include_audit=True, include_comments=True, include_full_content=True)

    def decide_document_workflow(
        self,
        *,
        organization_id: int,
        knowledge_document_id: int,
        action: str,
        reason: str,
        actor_user: dict[str, Any],
        actor: str,
        owner_user_id: Any = ...,
        reviewer_user_id: Any = ...,
        approver_user_id: Any = ...,
    ) -> dict[str, Any]:
        document = self.knowledge_repository.get_by_id(knowledge_document_id, organization_id=organization_id)
        if not document:
            raise KnowledgeError("Nie znaleziono dokumentu bazy wiedzy.")
        if str(document.get("lifecycle_status") or "active") != "active":
            raise KnowledgeError("Tylko aktywny dokument moze przejsc przez decyzje workflow.")

        normalized_action = self._normalize_decision_action(action)
        normalized_reason = self._normalize_content_text(reason or "")
        if not normalized_reason:
            raise KnowledgeError("Podaj krotki powod tej decyzji.")
        if not self._can_take_document_decision(document, actor_user=actor_user, action=normalized_action):
            raise KnowledgeError("To konto nie moze wykonac tej decyzji dla wskazanego dokumentu.")

        current_version_number = int(document.get("current_version_number") or 0)
        if normalized_action in {"send_for_review", "send_for_approval", "approve"} and current_version_number <= 0:
            raise KnowledgeError("Dokument nie ma jeszcze gotowej wersji do przekazania w obieg.")

        requested_owner = owner_user_id if owner_user_id is not ... else ...
        requested_reviewer = reviewer_user_id if reviewer_user_id is not ... else ...
        requested_approver = approver_user_id if approver_user_id is not ... else ...
        assignment_kwargs = {
            "owner_user_id": requested_owner,
            "reviewer_user_id": requested_reviewer,
            "approver_user_id": requested_approver,
        }
        if normalized_action == "send_for_review" and requested_reviewer is ... and not document.get("reviewer_user_id"):
            raise KnowledgeError("Wskaz osobe sprawdzajaca przed wyslaniem dokumentu do review.")
        if normalized_action == "send_for_approval" and requested_approver is ... and not document.get("approver_user_id"):
            raise KnowledgeError("Wskaz osobe akceptujaca przed przekazaniem dokumentu do akceptacji.")
        if normalized_action == "reassign" and all(value is ... for value in assignment_kwargs.values()):
            raise KnowledgeError("Wybierz przynajmniej jedna osobe do zmiany.")

        if any(value is not ... for value in assignment_kwargs.values()):
            document = self.update_document_metadata(
                organization_id=organization_id,
                knowledge_document_id=knowledge_document_id,
                actor_user=actor_user,
                actor=actor,
                owner_user_id=requested_owner,
                reviewer_user_id=requested_reviewer,
                approver_user_id=requested_approver,
            )

        previous_business_status = self._normalize_business_status(
            document.get("business_status") or self._derive_business_status_from_document(document)
        )

        if normalized_action == "send_for_review":
            self.update_document_metadata(
                organization_id=organization_id,
                knowledge_document_id=knowledge_document_id,
                actor_user=actor_user,
                actor=actor,
                business_status="do_sprawdzenia",
            )
        elif normalized_action == "send_for_approval":
            self.update_document_metadata(
                organization_id=organization_id,
                knowledge_document_id=knowledge_document_id,
                actor_user=actor_user,
                actor=actor,
                business_status="do_akceptacji",
            )
        elif normalized_action == "approve":
            self.mark_document_official_version(
                organization_id=organization_id,
                knowledge_document_id=knowledge_document_id,
                version_number=current_version_number,
                actor_user=actor_user,
                actor=actor,
            )
        elif normalized_action == "return_for_changes":
            self.update_document_metadata(
                organization_id=organization_id,
                knowledge_document_id=knowledge_document_id,
                actor_user=actor_user,
                actor=actor,
                business_status="roboczy",
            )

        comment_version_number = current_version_number if normalized_action == "approve" and current_version_number > 0 else None
        self.add_document_comment(
            organization_id=organization_id,
            knowledge_document_id=knowledge_document_id,
            note_text=normalized_reason,
            version_number=comment_version_number,
            actor_user=actor_user,
            actor=actor,
        )
        refreshed = self.knowledge_repository.get_by_id(knowledge_document_id, organization_id=organization_id)
        assert refreshed is not None
        next_business_status = self._normalize_business_status(
            refreshed.get("business_status") or self._derive_business_status_from_document(refreshed)
        )
        self.event_repository.log(
            event_type="knowledge_document_decision_taken",
            invoice_id=None,
            organization_id=organization_id,
            source="WIEDZA",
            status_before=previous_business_status,
            status_after=next_business_status,
            decision_reason=(
                f"{self.DECISION_ACTION_LABELS.get(normalized_action, normalized_action)} dla dokumentu "
                f"{refreshed['title']}: {normalized_reason}"
            ),
            actor=actor,
            details={
                "knowledge_document_id": knowledge_document_id,
                "title": refreshed["title"],
                "action": normalized_action,
                "action_label": self.DECISION_ACTION_LABELS.get(normalized_action, normalized_action),
                "reason": normalized_reason,
                "previous_business_status": previous_business_status,
                "business_status": next_business_status,
                "owner_user_id": refreshed.get("owner_user_id"),
                "owner_user_label": self._assignee_label(refreshed, "owner"),
                "reviewer_user_id": refreshed.get("reviewer_user_id"),
                "reviewer_user_label": self._assignee_label(refreshed, "reviewer"),
                "approver_user_id": refreshed.get("approver_user_id"),
                "approver_user_label": self._assignee_label(refreshed, "approver"),
                "decision_by_user_id": actor_user.get("user_id"),
            },
        )
        return self.get_document_detail(
            organization_id=organization_id,
            knowledge_document_id=knowledge_document_id,
            viewer_user_id=self._actor_user_id(actor_user),
        )

    def record_linked_task_created(
        self,
        *,
        organization_id: int,
        knowledge_document_id: int,
        task_id: int,
        task_title: str,
        actor_user: dict[str, Any],
        actor: str,
    ) -> dict[str, Any]:
        document = self.knowledge_repository.get_by_id(knowledge_document_id, organization_id=organization_id)
        if not document:
            raise KnowledgeError("Nie znaleziono dokumentu bazy wiedzy.")
        self.event_repository.log(
            event_type="knowledge_document_task_created",
            invoice_id=None,
            organization_id=organization_id,
            source="WIEDZA",
            status_before=None,
            status_after=None,
            decision_reason=f"Z dokumentu {document['title']} utworzono zadanie: {task_title}.",
            actor=actor,
            details={
                "knowledge_document_id": knowledge_document_id,
                "title": document["title"],
                "task_id": int(task_id),
                "task_title": task_title,
                "created_by_user_id": actor_user.get("user_id"),
            },
        )
        return self.get_document_detail(
            organization_id=organization_id,
            knowledge_document_id=knowledge_document_id,
            viewer_user_id=self._actor_user_id(actor_user),
        )

    def get_activity_feed(
        self,
        *,
        organization_id: int,
        viewer_user_id: int | None = None,
    ) -> dict[str, Any]:
        raw_events = self.event_repository.list_knowledge_activity(
            organization_id=organization_id,
            event_types=list(self.ACTIVITY_EVENT_TYPES),
            limit=self.ACTIVITY_FEED_LIMIT,
        )
        inbox_state = None
        last_seen_event_id = 0
        if viewer_user_id is not None:
            inbox_state = self.event_repository.get_module_inbox_state(
                user_id=int(viewer_user_id),
                organization_id=organization_id,
                module_key=self.MODULE_INBOX_KEY,
            )
            last_seen_event_id = int((inbox_state or {}).get("last_seen_event_id") or 0)
        items = [
            self._serialize_knowledge_activity_item(event, last_seen_event_id=last_seen_event_id)
            for event in raw_events
        ]
        unread_count = sum(1 for item in items if item.get("is_unread"))
        return {
            "items": items,
            "summary": {
                "event_count": len(items),
                "unread_count": unread_count,
                "last_seen_event_id": last_seen_event_id or None,
                "last_seen_at": (inbox_state or {}).get("last_seen_at"),
            },
        }

    def mark_activity_feed_seen(
        self,
        *,
        organization_id: int,
        viewer_user_id: int,
    ) -> dict[str, Any]:
        latest_events = self.event_repository.list_knowledge_activity(
            organization_id=organization_id,
            event_types=list(self.ACTIVITY_EVENT_TYPES),
            limit=1,
        )
        last_seen_event_id = int(latest_events[0]["id"]) if latest_events else None
        state = self.event_repository.mark_module_inbox_seen(
            user_id=int(viewer_user_id),
            organization_id=organization_id,
            module_key=self.MODULE_INBOX_KEY,
            last_seen_event_id=last_seen_event_id,
        )
        return {
            "module_key": self.MODULE_INBOX_KEY,
            "organization_id": organization_id,
            "last_seen_event_id": state.get("last_seen_event_id"),
            "last_seen_at": state.get("last_seen_at"),
            "unread_count": 0,
        }

    def record_document_download(
        self,
        *,
        organization_id: int,
        knowledge_document_id: int,
        actor_user: dict[str, Any],
        actor: str,
    ) -> None:
        document = self.knowledge_repository.get_by_id(knowledge_document_id, organization_id=organization_id)
        if not document:
            raise KnowledgeError("Nie znaleziono dokumentu do pobrania.")
        self.event_repository.log(
            event_type="knowledge_document_downloaded",
            invoice_id=None,
            organization_id=organization_id,
            source="WIEDZA",
            status_before=None,
            status_after=None,
            decision_reason=f"Pobrano dokument firmowy: {document['title']}.",
            actor=actor,
            details={
                "knowledge_document_id": knowledge_document_id,
                "file_name": document.get("file_name"),
                "lifecycle_status": document.get("lifecycle_status") or "active",
                "downloaded_by_user_id": actor_user.get("user_id"),
            },
        )

    def scan_all_folders(self, actor: str = "system") -> dict[str, Any]:
        results: list[dict[str, Any]] = []
        for organization in self.organization_repository.list_organizations(only_active=True):
            result = self.sync_folder(
                organization_id=int(organization["organization_id"]),
                actor_user={"user_id": None},
                actor=actor,
            )
            results.append(result)
        return {
            "organization_count": len(results),
            "queued_new": sum(int(item.get("queued_new") or 0) for item in results),
            "queued_updates": sum(int(item.get("queued_updates") or 0) for item in results),
            "unchanged_count": sum(int(item.get("unchanged_count") or 0) for item in results),
            "duplicate_count": sum(int(item.get("duplicate_count") or 0) for item in results),
            "similar_count": sum(int(item.get("similar_count") or 0) for item in results),
            "results": results,
        }

    def process_pending_jobs(self, limit: int = 3) -> dict[str, int]:
        processed_count = 0
        failed_count = 0
        for _ in range(max(1, int(limit))):
            job = self.knowledge_repository.get_next_pending_job()
            if not job:
                break
            document_id = int(job["knowledge_document_id"] or 0)
            self.knowledge_repository.mark_job_processing(int(job["knowledge_processing_job_id"]))
            if document_id:
                self.knowledge_repository.update(
                    document_id,
                    {
                        "processing_status": "processing",
                        "processing_error": None,
                        "processing_started_at": now_iso(),
                    },
                )
            try:
                self._process_job(job)
                processed_count += 1
            except Exception as error:
                failed_count += 1
                self.knowledge_repository.mark_job_failed(int(job["knowledge_processing_job_id"]), str(error))
                if document_id:
                    self.knowledge_repository.update(
                        document_id,
                        {
                            "processing_status": "error",
                            "processing_error": str(error),
                            "processing_started_at": None,
                        },
                    )
        return {
            "processed_count": processed_count,
            "failed_count": failed_count,
        }

    def reprocess_document(
        self,
        *,
        organization_id: int,
        knowledge_document_id: int,
        actor_user: dict[str, Any],
        actor: str,
    ) -> dict[str, Any]:
        document = self.knowledge_repository.get_by_id(knowledge_document_id, organization_id=organization_id)
        if not document:
            raise KnowledgeError("Nie znaleziono dokumentu bazy wiedzy.")
        if str(document.get("lifecycle_status") or "active") == "deleted":
            raise KnowledgeError("Nie mozna przetwarzac dokumentu oznaczonego jako usuniety.")
        self.knowledge_repository.update(
            knowledge_document_id,
            {
                "processing_status": "queued",
                "processing_error": None,
                "processing_started_at": None,
            },
        )
        job_id = self.knowledge_repository.create_job(
            {
                "organization_id": organization_id,
                "knowledge_document_id": knowledge_document_id,
                "job_type": "reprocess",
                "source_storage_key": document["file_storage_key"],
                "source_file_name": document["file_name"],
                "source_mime_type": document.get("mime_type"),
                "source_type": document.get("source_type") or "manual",
                "source_content_hash": document["content_hash"],
                "supplemental_text": "",
                "created_by_user_id": actor_user.get("user_id"),
            }
        )
        self.event_repository.log(
            event_type="knowledge_document_updated",
            invoice_id=None,
            organization_id=organization_id,
            source="WIEDZA",
            status_before=None,
            status_after=None,
            decision_reason=f"Ponownie dodano dokument do przetwarzania: {document['title']}.",
            actor=actor,
            details={
                "knowledge_document_id": knowledge_document_id,
                "knowledge_processing_job_id": job_id,
                "processing_status": "queued",
            },
        )
        refreshed = self.knowledge_repository.get_by_id(knowledge_document_id, organization_id=organization_id)
        assert refreshed is not None
        return self._serialize_document(refreshed)

    def answer_question(self, question: str, organization_id: int) -> dict[str, Any]:
        normalized_question = str(question or "").strip()
        if not normalized_question:
            raise KnowledgeError("Wpisz pytanie do bazy wiedzy.")

        organization = self._resolve_organization(organization_id)
        documents = self.knowledge_repository.list_documents(
            int(organization["organization_id"]),
            assistant_only=True,
        )
        active_documents = [item for item in documents if str(item.get("lifecycle_status") or "active") == "active"]
        ready_documents = [item for item in active_documents if item.get("processing_status") == "ready"]
        queued_documents = [item for item in active_documents if item.get("processing_status") in {"queued", "processing"}]
        if not ready_documents and queued_documents:
            self.process_pending_jobs(limit=max(5, len(queued_documents) * 4))
            documents = self.knowledge_repository.list_documents(
                int(organization["organization_id"]),
                assistant_only=True,
            )
            active_documents = [item for item in documents if str(item.get("lifecycle_status") or "active") == "active"]
            ready_documents = [item for item in active_documents if item.get("processing_status") == "ready"]
            queued_documents = [item for item in active_documents if item.get("processing_status") in {"queued", "processing"}]
        if not ready_documents and queued_documents:
            return {
                "question": normalized_question,
                "answer": "Dokumenty tej organizacji są jeszcze w trakcie przetwarzania. Poczekaj chwilę i spróbuj ponownie.",
                "matches": [],
                "organization_id": organization["organization_id"],
                "organization_name": organization["name"],
                "document_count": len(documents),
                "ready_document_count": 0,
                "pending_document_count": len(queued_documents),
            }
        if not ready_documents:
            return {
                "question": normalized_question,
                "answer": "Ta organizacja nie ma jeszcze gotowych dokumentów w bazie wiedzy.",
                "matches": [],
                "organization_id": organization["organization_id"],
                "organization_name": organization["name"],
                "document_count": 0,
                "ready_document_count": 0,
                "pending_document_count": len(queued_documents),
            }

        matches = self._search_documents(normalized_question, ready_documents)
        if not matches:
            return {
                "question": normalized_question,
                "answer": "Nie znalazłem jednoznacznej odpowiedzi w gotowych dokumentach tej organizacji. Spróbuj użyć bardziej konkretnych słów.",
                "matches": [],
                "organization_id": organization["organization_id"],
                "organization_name": organization["name"],
                "document_count": len(ready_documents),
                "ready_document_count": len(ready_documents),
                "pending_document_count": len(queued_documents),
            }

        answer_lines = [f"[{index}] {match.snippet}" for index, match in enumerate(matches[:3], start=1)]
        return {
            "question": normalized_question,
            "answer": "Na podstawie dokumentów tej organizacji:\n" + "\n".join(answer_lines),
            "matches": [
                {
                    "knowledge_document_id": match.document["knowledge_document_id"],
                    "title": match.document["title"],
                    "file_name": match.document["file_name"],
                    "file_link": match.document["file_link"],
                    "score": round(match.score, 2),
                    "snippet": match.snippet,
                    "updated_at": match.document.get("updated_at"),
                    "source_type": match.document.get("source_type") or "manual",
                    "version_number": int(match.document.get("current_version_number") or 0),
                    "citation_label": f"[{index}] {match.document['title']} | v{int(match.document.get('current_version_number') or 0)}",
                    "processing_status": match.document.get("processing_status") or "ready",
                    "last_processed_at": match.document.get("last_processed_at"),
                }
                for index, match in enumerate(matches[:5], start=1)
            ],
            "organization_id": organization["organization_id"],
            "organization_name": organization["name"],
            "document_count": len(ready_documents),
            "ready_document_count": len(ready_documents),
            "pending_document_count": len(queued_documents),
        }

    def _process_job(self, job: dict[str, Any]) -> None:
        document_id = int(job["knowledge_document_id"] or 0)
        if not document_id:
            raise KnowledgeError("Brakuje powiązanego dokumentu dla zadania przetwarzania.")

        document = self.knowledge_repository.get_by_id(document_id, organization_id=int(job["organization_id"]))
        if not document:
            raise KnowledgeError("Nie znaleziono dokumentu powiązanego z zadaniem przetwarzania.")

        raw_bytes = self._read_job_source_bytes(job["source_storage_key"])
        extracted_text, extraction_method = self._extract_text_with_method(
            raw_bytes,
            str(job["source_file_name"] or document["file_name"]),
            str(job.get("source_mime_type") or document.get("mime_type") or ""),
        )
        normalized_content = self._compose_document_content(extracted_text, str(job.get("supplemental_text") or ""))
        if not normalized_content.strip():
            raise KnowledgeError(
                "Nie udało się odczytać treści pliku. Dodaj dokument tekstowy, popraw skan albo uzupełnij opis dokumentu."
            )

        current_version_number = int(document.get("current_version_number") or 0)
        current_content = self._normalize_content_text(document.get("content_text") or "")
        should_create_version = (
            current_version_number == 0
            or current_content != normalized_content
            or str(document.get("content_hash") or "") != str(job["source_content_hash"])
        )
        next_version_number = current_version_number + 1 if should_create_version else current_version_number
        official_version_number = int(document.get("official_version_number") or 0)
        processed_at = now_iso()
        source_file_link = self.storage_service.build_public_link("knowledge", str(job["source_storage_key"]))

        update_fields = {
            "content_text": normalized_content,
            "content_hash": job["source_content_hash"],
            "char_count": len(normalized_content),
            "processing_status": "ready",
            "processing_error": None,
            "current_version_number": next_version_number,
            "last_processed_at": processed_at,
            "processing_started_at": None,
            "title": document["title"],
            "file_name": job["source_file_name"],
            "mime_type": job.get("source_mime_type") or document.get("mime_type"),
            "file_link": source_file_link,
            "file_storage_key": job["source_storage_key"],
            "source_type": job.get("source_type") or document.get("source_type") or "manual",
            "created_by_user_id": document.get("created_by_user_id"),
        }
        lifecycle_status = str(document.get("lifecycle_status") or "active")
        current_business_status = self._normalize_business_status(
            document.get("business_status") or self._derive_business_status_from_document(document)
        )
        if lifecycle_status == "archived":
            update_fields["business_status"] = "archiwalny"
        elif current_business_status not in self.BUSINESS_STATUS_LABELS:
            update_fields["business_status"] = self._derive_business_status_from_document(document)

        self.knowledge_repository.update(document_id, update_fields)

        if should_create_version:
            self.knowledge_repository.create_version(
                {
                    "knowledge_document_id": document_id,
                    "organization_id": int(job["organization_id"]),
                    "version_number": next_version_number,
                    "title": document["title"],
                    "file_name": job["source_file_name"],
                    "mime_type": job.get("source_mime_type") or document.get("mime_type"),
                    "file_link": source_file_link,
                    "file_storage_key": job["source_storage_key"],
                    "content_text": normalized_content,
                    "content_hash": job["source_content_hash"],
                    "char_count": len(normalized_content),
                    "source_type": job.get("source_type") or document.get("source_type") or "manual",
                    "created_by_user_id": document.get("created_by_user_id"),
                    "extraction_method": extraction_method,
                    "created_at": processed_at,
                }
            )

        self.knowledge_repository.mark_job_completed(int(job["knowledge_processing_job_id"]))
        self.event_repository.log(
            event_type="knowledge_document_updated",
            invoice_id=None,
            organization_id=int(job["organization_id"]),
            source="WIEDZA",
            status_before=None,
            status_after=None,
            decision_reason=f"Przetworzono dokument bazy wiedzy: {document['title']}.",
            actor="system",
            details={
                "knowledge_document_id": document_id,
                "knowledge_processing_job_id": job["knowledge_processing_job_id"],
                "version_number": next_version_number,
                "extraction_method": extraction_method,
                "char_count": len(normalized_content),
            },
        )
        self._refresh_document_relationships(document_id, int(job["organization_id"]))

    def _resolve_organization(self, organization_id: int) -> dict[str, Any]:
        organization = self.organization_repository.get_by_id(int(organization_id))
        if not organization:
            raise KnowledgeError("Wybrana organizacja nie istnieje.")
        if not organization.get("is_active"):
            raise KnowledgeError("Nie można pracować na organizacji oznaczonej jako nieaktywna.")
        return organization

    def _organization_folder_path(self, organization_slug: str) -> Path:
        return KNOWLEDGE_DIR / "organizacje" / str(organization_slug or "organizacja")

    def _iter_organization_files(self, folder_path: Path):
        for path in sorted(candidate for candidate in folder_path.rglob("*") if candidate.is_file()):
            relative = path.relative_to(folder_path)
            if relative.parts and relative.parts[0].lower() == "upload":
                continue
            yield path

    def _build_upload_relative_path(self, organization_slug: str, file_name: str, area: str = "upload") -> Path:
        return Path("organizacje") / str(organization_slug or "organizacja") / str(area or "upload") / now_iso()[:10] / file_name

    def _build_stored_file_name(self, file_name: str, raw_content: bytes) -> str:
        safe_name = self._sanitize_file_name(file_name)
        suffix = Path(safe_name).suffix
        stem = Path(safe_name).stem or "dokument"
        digest = hashlib.sha256(raw_content).hexdigest()[:12]
        return f"{stem}_{digest}{suffix or '.txt'}"

    def _validate_file_payload(self, file_name: str, file_bytes: bytes) -> None:
        if len(file_bytes or b"") > self.MAX_UPLOAD_BYTES:
            raise KnowledgeError(
                f"Plik przekracza limit {round(self.MAX_UPLOAD_BYTES / (1024 * 1024), 1)} MB dla jednego dokumentu."
            )
        if not str(file_name or "").strip():
            raise KnowledgeError("Brakuje nazwy pliku.")

    def _supports_text_extraction(self, file_name: str, mime_type: str | None = None) -> bool:
        suffix = Path(str(file_name or "")).suffix.lower()
        normalized_mime = str(mime_type or "")
        return (
            suffix in self.TEXT_EXTENSIONS
            or suffix in self.IMAGE_EXTENSIONS
            or suffix in {".docx", ".xlsx", ".pdf"}
            or normalized_mime.startswith("text/")
            or normalized_mime.startswith("image/")
        )

    def _build_storage_only_description(self, file_name: str, library_path: str) -> str:
        folder_label = self._format_library_path_label(library_path)
        return self._normalize_content_text(
            f"Plik firmowy do pobrania. Nazwa pliku: {file_name}. Folder: {folder_label}. "
            "Ten dokument nie ma automatycznej ekstrakcji tresci, wiec wyszukiwarka znajdzie go po nazwie, folderze i metadanych."
        )

    def _sanitize_file_name(self, value: str) -> str:
        normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value or "").strip())
        cleaned = normalized.strip("._")
        return cleaned or "dokument.txt"

    def _default_file_name(self, title: str) -> str:
        normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", str(title or "").strip().lower())
        cleaned = normalized.strip("._")
        return f"{cleaned or 'dokument'}.txt"

    def _ensure_text_extension(self, file_name: str) -> str:
        return file_name if Path(file_name).suffix else f"{file_name}.txt"

    def _normalize_content_text(self, value: str) -> str:
        normalized = re.sub(r"\r\n?", "\n", str(value or ""))
        normalized = re.sub(r"[ \t]+", " ", normalized)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized).strip()
        return normalized[: self.MAX_CONTENT_LENGTH]

    def _normalize_annotation_kind(self, value: str) -> str:
        return "annotation" if str(value or "").strip().lower() == "annotation" else "comment"

    def _normalize_comment_anchor_text(self, value: str | None, *, limit: int = 120) -> str | None:
        normalized = re.sub(r"\s+", " ", str(value or "").strip())
        if not normalized:
            return None
        return normalized[:limit].rstrip()

    def _parse_optional_positive_int(self, value: Any) -> int | None:
        if value in (None, "", False):
            return None
        try:
            normalized = int(value)
        except (TypeError, ValueError):
            raise KnowledgeError("Nieprawidlowy numer wersji.")
        if normalized <= 0:
            raise KnowledgeError("Numer wersji musi byc dodatni.")
        return normalized

    def _parse_assignment_user_id(self, value: Any) -> int | None:
        if value in (None, "", False):
            return None
        try:
            normalized = int(value)
        except (TypeError, ValueError):
            raise KnowledgeError("Nieprawidlowy uzytkownik przypisany do dokumentu.")
        if normalized <= 0:
            return None
        return normalized

    def _normalize_business_status(self, value: Any, *, strict: bool = False) -> str:
        normalized = str(value or "").strip().lower()
        if not normalized:
            return "roboczy"
        if normalized not in self.BUSINESS_STATUS_LABELS:
            if strict:
                raise KnowledgeError("Nieprawidlowy stan obiegu dokumentu.")
            return "roboczy"
        return normalized

    def _derive_business_status_from_document(self, document: dict[str, Any]) -> str:
        lifecycle_status = str(document.get("lifecycle_status") or "active")
        current_status = str(document.get("business_status") or "").strip().lower()
        if lifecycle_status == "archived":
            return "archiwalny"
        if lifecycle_status == "deleted" and current_status in self.BUSINESS_STATUS_LABELS:
            return current_status
        current_version_number = int(document.get("current_version_number") or 0)
        official_version_number = int(document.get("official_version_number") or 0)
        if current_version_number <= 0:
            return "roboczy"
        if official_version_number <= 0:
            return "do_akceptacji"
        if official_version_number < current_version_number:
            return "do_sprawdzenia"
        return "obowiazujacy"

    def _business_status_after_new_version(self, document: dict[str, Any]) -> str:
        if str(document.get("lifecycle_status") or "active") == "archived":
            return "archiwalny"
        if int(document.get("official_version_number") or 0) > 0:
            return "do_sprawdzenia"
        return "roboczy"

    def _business_status_after_marking_official(self, document: dict[str, Any]) -> str:
        if str(document.get("lifecycle_status") or "active") == "archived":
            return "archiwalny"
        return "obowiazujacy"

    def _restore_business_status(self, document: dict[str, Any]) -> str:
        previous_status = str(document.get("business_status_before_archive") or "").strip().lower()
        if previous_status in self.BUSINESS_STATUS_LABELS and previous_status != "archiwalny":
            return previous_status
        current_status = str(document.get("business_status") or "").strip().lower()
        if current_status in self.BUSINESS_STATUS_LABELS and current_status != "archiwalny":
            return current_status
        return self._derive_business_status_from_document({**document, "lifecycle_status": "active"})

    def _normalize_decision_action(self, value: Any) -> str:
        normalized = str(value or "").strip().lower()
        if normalized not in self.DECISION_ACTION_LABELS:
            raise KnowledgeError("Nieprawidlowa akcja decyzji dokumentowej.")
        return normalized

    def _actor_user_id(self, actor_user: dict[str, Any] | None) -> int | None:
        if not actor_user:
            return None
        return self._parse_optional_positive_int(actor_user.get("user_id"))

    def _actor_capabilities(self, actor_user: dict[str, Any] | None) -> set[str]:
        user_id = self._actor_user_id(actor_user)
        if not user_id:
            return set()
        return set(self.user_repository.list_capabilities(int(user_id)))

    def _is_document_manager(self, actor_user: dict[str, Any] | None, document: dict[str, Any]) -> bool:
        actor_role = str((actor_user or {}).get("role") or "").strip().lower()
        if actor_role in {"system_owner", "organization_admin"}:
            return True
        actor_user_id = self._actor_user_id(actor_user)
        if actor_user_id is None:
            return False
        if "knowledge.manage" in self._actor_capabilities(actor_user):
            return True
        document_org_id = int(document.get("organization_id") or 0)
        memberships = self.user_repository.list_memberships(int(actor_user_id))
        return any(
            int(item.get("organization_id") or 0) == document_org_id
            and str(item.get("role") or "").strip().lower() == "organization_admin"
            for item in memberships
        )

    def _can_take_document_decision(
        self,
        document: dict[str, Any],
        *,
        actor_user: dict[str, Any] | None,
        action: str,
    ) -> bool:
        if self._is_document_manager(actor_user, document):
            return True
        actor_user_id = self._actor_user_id(actor_user)
        if actor_user_id is None:
            return False
        owner_user_id = self._parse_optional_positive_int(document.get("owner_user_id"))
        reviewer_user_id = self._parse_optional_positive_int(document.get("reviewer_user_id"))
        approver_user_id = self._parse_optional_positive_int(document.get("approver_user_id"))
        if action == "send_for_review":
            return actor_user_id == owner_user_id
        if action == "send_for_approval":
            return actor_user_id in {owner_user_id, reviewer_user_id}
        if action == "approve":
            return actor_user_id in {owner_user_id, approver_user_id}
        if action == "return_for_changes":
            return actor_user_id in {owner_user_id, reviewer_user_id, approver_user_id}
        if action == "reassign":
            return actor_user_id == owner_user_id
        return False

    def _build_document_decision_actions(
        self,
        document: dict[str, Any],
        *,
        viewer_user_id: int | None,
        business_status: str,
        workflow_status: str,
    ) -> list[dict[str, Any]]:
        if viewer_user_id is None:
            return []
        viewer = self.user_repository.get_by_id(int(viewer_user_id))
        if not viewer:
            return []
        lifecycle_status = str(document.get("lifecycle_status") or "active")
        if lifecycle_status != "active" or workflow_status == "processing":
            return []
        actions: list[str] = []
        if business_status == "roboczy":
            actions.append("send_for_review")
        elif business_status == "do_sprawdzenia":
            actions.extend(["send_for_approval", "return_for_changes"])
        elif business_status == "do_akceptacji":
            actions.extend(["approve", "return_for_changes"])
        elif business_status == "obowiazujacy":
            actions.append("return_for_changes")
        if self._can_take_document_decision(document, actor_user=viewer, action="reassign"):
            actions.append("reassign")
        deduped_actions: list[str] = []
        for action in actions:
            if action in deduped_actions:
                continue
            if self._can_take_document_decision(document, actor_user=viewer, action=action):
                deduped_actions.append(action)
        return [
            {
                "code": action,
                "label": self.DECISION_ACTION_LABELS.get(action, action),
                "requires_reason": True,
                "required_assignments": (
                    ["reviewer_user_id"]
                    if action == "send_for_review"
                    else ["approver_user_id"]
                    if action == "send_for_approval"
                    else ["owner_user_id", "reviewer_user_id", "approver_user_id"]
                    if action == "reassign"
                    else []
                ),
                "hint": (
                    "Przed przekazaniem do sprawdzenia dokument musi miec wskazana osobe sprawdzajaca."
                    if action == "send_for_review"
                    else "Przed przekazaniem do akceptacji dokument musi miec wskazana osobe akceptujaca."
                    if action == "send_for_approval"
                    else "Ta decyzja pozwala tez jednoczesnie zmienic osoby odpowiedzialne za dokument."
                    if action == "reassign"
                    else "Powod decyzji zapisze sie w historii dokumentu i w feedzie aktywnosci."
                ),
            }
            for action in deduped_actions
        ]

    def _serialize_assignee(self, document: dict[str, Any], prefix: str) -> dict[str, Any]:
        user_id = self._parse_optional_positive_int(document.get(f"{prefix}_user_id"))
        login = document.get(f"{prefix}_login")
        display_name = document.get(f"{prefix}_display_name")
        label = (str(display_name or "").strip() or str(login or "").strip() or (f"uzytkownik #{user_id}" if user_id else None))
        return {
            "user_id": user_id,
            "login": login,
            "display_name": display_name,
            "label": label,
        }

    def _assignee_label(self, document: dict[str, Any], prefix: str) -> str | None:
        return self._serialize_assignee(document, prefix).get("label")

    def _compose_document_content(self, extracted_text: str, supplemental_text: str) -> str:
        normalized_extracted = self._normalize_content_text(extracted_text)
        normalized_supplemental = self._normalize_content_text(supplemental_text)
        if normalized_extracted and normalized_supplemental:
            return self._normalize_content_text(
                f"Skrócony opis dokumentu:\n{normalized_supplemental}\n\nTreść dokumentu:\n{normalized_extracted}"
            )
        return normalized_extracted or normalized_supplemental

    def _read_job_source_bytes(self, storage_key: str) -> bytes:
        try:
            file_path = self.storage_service.resolve_local_path("knowledge", storage_key)
        except StorageError as error:
            raise KnowledgeError("Nie udało się odnaleźć pliku źródłowego dokumentu.") from error
        if not file_path.exists() or not file_path.is_file():
            raise KnowledgeError("Plik źródłowy dokumentu nie istnieje już w magazynie.")
        return file_path.read_bytes()

    def _extract_text_with_method(self, file_bytes: bytes, file_name: str, mime_type: str | None) -> tuple[str, str]:
        suffix = Path(file_name).suffix.lower()
        if suffix in self.TEXT_EXTENSIONS or str(mime_type or "").startswith("text/"):
            return self._decode_text(file_bytes), "plain_text"
        if suffix == ".docx":
            return self._extract_docx_text(file_bytes), "docx"
        if suffix == ".xlsx":
            return self._extract_xlsx_text(file_bytes), "xlsx"
        if suffix == ".pdf":
            return self._extract_pdf_text(file_bytes), "pdf"
        if suffix in self.IMAGE_EXTENSIONS or str(mime_type or "").startswith("image/"):
            return self._extract_image_text(file_bytes, file_name), "ocr_image"
        return "", "unsupported"

    def _decode_text(self, file_bytes: bytes) -> str:
        for encoding in ("utf-8", "utf-8-sig", "cp1250", "latin-1"):
            try:
                return file_bytes.decode(encoding)
            except UnicodeDecodeError:
                continue
        return file_bytes.decode("utf-8", errors="ignore")

    def _extract_docx_text(self, file_bytes: bytes) -> str:
        try:
            with zipfile.ZipFile(BytesIO(file_bytes)) as archive:
                document_xml = archive.read("word/document.xml")
        except Exception:
            return ""

        try:
            root = ElementTree.fromstring(document_xml)
        except ElementTree.ParseError:
            return ""

        namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        fragments = [node.text or "" for node in root.findall(".//w:t", namespace)]
        return "\n".join(fragment for fragment in fragments if fragment.strip())

    def _extract_pdf_text(self, file_bytes: bytes) -> str:
        decoded = file_bytes.decode("latin-1", errors="ignore")
        sequences = re.findall(r"\(([^()]*)\)", decoded)
        candidate = "\n".join(sequence for sequence in sequences if len(sequence.strip()) >= 3) or decoded
        candidate = candidate.replace("\\n", "\n").replace("\\r", "\n")
        lines: list[str] = []
        for raw_line in re.split(r"[\r\n]+", candidate):
            cleaned = re.sub(r"\s+", " ", raw_line).strip()
            if len(cleaned) < 3:
                continue
            if re.fullmatch(r"[%/0-9 .,_-]+", cleaned):
                continue
            lines.append(cleaned)
        return "\n".join(lines[:800])

    def _extract_xlsx_text(self, file_bytes: bytes) -> str:
        try:
            with zipfile.ZipFile(BytesIO(file_bytes)) as archive:
                shared_strings = self._extract_xlsx_shared_strings(archive)
                sheet_names = sorted(
                    name for name in archive.namelist() if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
                )
                rows: list[str] = []
                for sheet_name in sheet_names:
                    rows.extend(self._extract_xlsx_sheet_rows(archive.read(sheet_name), shared_strings))
        except Exception:
            return ""

        cleaned_rows = [row for row in rows if row.strip()]
        return "\n".join(cleaned_rows[:800])

    def _extract_xlsx_shared_strings(self, archive: zipfile.ZipFile) -> list[str]:
        try:
            shared_xml = archive.read("xl/sharedStrings.xml")
        except KeyError:
            return []

        try:
            root = ElementTree.fromstring(shared_xml)
        except ElementTree.ParseError:
            return []

        namespace = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        values: list[str] = []
        for node in root.findall(".//x:si", namespace):
            fragments = [fragment.text or "" for fragment in node.findall(".//x:t", namespace)]
            values.append("".join(fragments).strip())
        return values

    def _extract_xlsx_sheet_rows(self, sheet_xml: bytes, shared_strings: list[str]) -> list[str]:
        try:
            root = ElementTree.fromstring(sheet_xml)
        except ElementTree.ParseError:
            return []

        namespace = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        rows: list[str] = []
        for row_node in root.findall(".//x:row", namespace):
            values: list[str] = []
            for cell in row_node.findall("x:c", namespace):
                value = self._extract_xlsx_cell_value(cell, namespace, shared_strings)
                if value:
                    values.append(value)
            if values:
                rows.append(" | ".join(values))
        return rows

    def _extract_xlsx_cell_value(
        self,
        cell: ElementTree.Element,
        namespace: dict[str, str],
        shared_strings: list[str],
    ) -> str:
        cell_type = cell.get("t") or ""
        if cell_type == "inlineStr":
            fragments = [fragment.text or "" for fragment in cell.findall(".//x:is//x:t", namespace)]
            return " ".join(fragment.strip() for fragment in fragments if fragment.strip())

        value_node = cell.find("x:v", namespace)
        if value_node is None or not (value_node.text or "").strip():
            return ""

        raw_value = value_node.text.strip()
        if cell_type == "s" and raw_value.isdigit():
            index = int(raw_value)
            return shared_strings[index].strip() if 0 <= index < len(shared_strings) else ""
        return raw_value

    def _extract_image_text(self, file_bytes: bytes, file_name: str) -> str:
        extracted = self.ocr_engine.extract_text(file_name, file_bytes)
        cleaned = self._normalize_content_text(extracted)
        if cleaned.startswith("Nie uda") and "OCR" in cleaned:
            return ""
        return cleaned

    def _set_document_lifecycle(
        self,
        *,
        organization_id: int,
        knowledge_document_id: int,
        lifecycle_status: str,
        actor_user: dict[str, Any],
        actor: str,
        event_type: str,
        reason_prefix: str,
    ) -> dict[str, Any]:
        document = self.knowledge_repository.get_by_id(knowledge_document_id, organization_id=organization_id)
        if not document:
            raise KnowledgeError("Nie znaleziono dokumentu bazy wiedzy.")

        timestamp = now_iso()
        fields: dict[str, Any] = {"lifecycle_status": lifecycle_status}
        if lifecycle_status == "archived":
            previous_business_status = self._normalize_business_status(
                document.get("business_status") or self._derive_business_status_from_document(document)
            )
            fields["archived_at"] = timestamp
            fields["archived_by_user_id"] = actor_user.get("user_id")
            fields["deleted_at"] = None
            fields["deleted_by_user_id"] = None
            fields["use_in_assistant"] = False
            fields["business_status_before_archive"] = (
                previous_business_status if previous_business_status != "archiwalny" else None
            )
            fields["business_status"] = "archiwalny"
        elif lifecycle_status == "deleted":
            fields["deleted_at"] = timestamp
            fields["deleted_by_user_id"] = actor_user.get("user_id")
            fields["processing_status"] = "ready"
            fields["processing_error"] = None
            fields["processing_started_at"] = None
        else:
            restored_business_status = self._restore_business_status(document)
            fields["archived_at"] = None
            fields["archived_by_user_id"] = None
            fields["deleted_at"] = None
            fields["deleted_by_user_id"] = None
            fields["business_status_before_archive"] = None
            fields["business_status"] = restored_business_status

        self.knowledge_repository.update(knowledge_document_id, fields)
        refreshed = self.knowledge_repository.get_by_id(knowledge_document_id, organization_id=organization_id)
        assert refreshed is not None
        self.event_repository.log(
            event_type=event_type,
            invoice_id=None,
            organization_id=organization_id,
            source="WIEDZA",
            status_before=document.get("lifecycle_status") or "active",
            status_after=lifecycle_status,
            decision_reason=f"{reason_prefix}: {refreshed['title']}.",
            actor=actor,
            details={
                "knowledge_document_id": knowledge_document_id,
                "previous_lifecycle_status": document.get("lifecycle_status") or "active",
                "lifecycle_status": lifecycle_status,
                "previous_business_status": self._normalize_business_status(
                    document.get("business_status") or self._derive_business_status_from_document(document)
                ),
                "business_status": self._normalize_business_status(
                    refreshed.get("business_status") or self._derive_business_status_from_document(refreshed)
                ),
                "updated_by_user_id": actor_user.get("user_id"),
            },
        )
        return self._serialize_document(refreshed)

    def _refresh_document_relationships(self, knowledge_document_id: int, organization_id: int) -> None:
        document = self.knowledge_repository.get_by_id(knowledge_document_id, organization_id=organization_id)
        if not document:
            return

        if str(document.get("lifecycle_status") or "active") == "deleted":
            self.knowledge_repository.update(
                knowledge_document_id,
                {
                    "duplicate_status": "none",
                    "duplicate_of_document_id": None,
                    "duplicate_score": 0,
                    "duplicate_reason": None,
                },
            )
            return

        content_hash = str(document.get("content_hash") or "").strip()
        if content_hash:
            exact_matches = self.knowledge_repository.find_by_content_hash(
                organization_id,
                content_hash,
                exclude_document_id=knowledge_document_id,
            )
            if exact_matches:
                reference = exact_matches[0]
                self.knowledge_repository.update(
                    knowledge_document_id,
                    {
                        "duplicate_status": "exact_duplicate",
                        "duplicate_of_document_id": reference["knowledge_document_id"],
                        "duplicate_score": 1.0,
                        "duplicate_reason": f"Dokument ma identyczny hash jak {reference['title']}.",
                    },
                )
                return

        if str(document.get("processing_status") or "") != "ready" or not str(document.get("content_text") or "").strip():
            self.knowledge_repository.update(
                knowledge_document_id,
                {
                    "duplicate_status": "none",
                    "duplicate_of_document_id": None,
                    "duplicate_score": 0,
                    "duplicate_reason": None,
                },
            )
            return

        best_match: dict[str, Any] | None = None
        best_score = 0.0
        for candidate in self.knowledge_repository.list_similarity_candidates(
            organization_id,
            exclude_document_id=knowledge_document_id,
            limit=20,
        ):
            score = self._document_similarity_score(document, candidate)
            if score > best_score:
                best_score = score
                best_match = candidate

        if best_match and best_score >= self.SIMILARITY_THRESHOLD:
            self.knowledge_repository.update(
                knowledge_document_id,
                {
                    "duplicate_status": "similar_version",
                    "duplicate_of_document_id": best_match["knowledge_document_id"],
                    "duplicate_score": round(best_score, 3),
                    "duplicate_reason": (
                        f"Dokument jest bardzo podobny do {best_match['title']} "
                        f"({round(best_score * 100)}% podobienstwa)."
                    ),
                },
            )
            return

        self.knowledge_repository.update(
            knowledge_document_id,
            {
                "duplicate_status": "none",
                "duplicate_of_document_id": None,
                "duplicate_score": 0,
                "duplicate_reason": None,
            },
        )

    def _document_similarity_score(self, document: dict[str, Any], candidate: dict[str, Any]) -> float:
        title_left = str(document.get("title") or "").lower()
        title_right = str(candidate.get("title") or "").lower()
        file_left = Path(str(document.get("file_name") or "")).stem.lower()
        file_right = Path(str(candidate.get("file_name") or "")).stem.lower()
        text_left = self._normalize_content_text(str(document.get("content_text") or ""))[:4000]
        text_right = self._normalize_content_text(str(candidate.get("content_text") or ""))[:4000]
        if not text_left or not text_right:
            return 0.0
        text_score = SequenceMatcher(None, text_left, text_right).ratio()
        title_score = SequenceMatcher(None, title_left, title_right).ratio() if title_left and title_right else 0.0
        file_score = SequenceMatcher(None, file_left, file_right).ratio() if file_left and file_right else 0.0
        folder_score = 1.0 if self._normalize_library_path(document.get("library_path") or "") == self._normalize_library_path(candidate.get("library_path") or "") else 0.0
        return max(
            text_score,
            (text_score * 0.75) + (title_score * 0.15) + (file_score * 0.05) + (folder_score * 0.05),
        )

    def _search_documents(self, question: str, documents: list[dict[str, Any]]) -> list[KnowledgeMatch]:
        question_tokens = self._tokenize(question)
        question_normalized = self._normalize_for_search(question)
        matches: list[KnowledgeMatch] = []

        for document in documents:
            best_score = 0.0
            best_snippet = ""
            for chunk in self._split_into_chunks(document.get("content_text") or ""):
                score = self._score_chunk(chunk, question_tokens, question_normalized)
                if score <= best_score:
                    continue
                best_score = score
                best_snippet = self._best_snippet(chunk, question_tokens)
            if best_score > 0 and best_snippet:
                matches.append(KnowledgeMatch(score=best_score, document=document, snippet=best_snippet))

        return sorted(matches, key=lambda item: (-item.score, item.document["title"]))[:5]

    def _split_into_chunks(self, text: str, max_length: int = 700) -> list[str]:
        normalized = self._normalize_content_text(text)
        if not normalized:
            return []
        paragraphs = [fragment.strip() for fragment in re.split(r"\n{2,}", normalized) if fragment.strip()]
        chunks: list[str] = []
        current = ""
        for paragraph in paragraphs:
            if len(paragraph) > max_length:
                if current:
                    chunks.append(current.strip())
                    current = ""
                for index in range(0, len(paragraph), max_length):
                    chunks.append(paragraph[index : index + max_length].strip())
                continue
            candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
            if len(candidate) > max_length and current:
                chunks.append(current.strip())
                current = paragraph
            else:
                current = candidate
        if current:
            chunks.append(current.strip())
        return chunks

    def _score_chunk(self, chunk: str, question_tokens: list[str], question_normalized: str) -> float:
        if not chunk.strip():
            return 0.0
        chunk_normalized = self._normalize_for_search(chunk)
        if not chunk_normalized:
            return 0.0
        chunk_tokens = self._tokenize(chunk)
        if not chunk_tokens:
            return 0.0

        chunk_counter = Counter(chunk_tokens)
        unique_hits = [token for token in dict.fromkeys(question_tokens) if token in chunk_counter]
        if not unique_hits and question_normalized not in chunk_normalized:
            return 0.0

        score = 0.0
        if question_normalized and question_normalized in chunk_normalized:
            score += 18.0
        score += sum(min(chunk_counter[token], 3) * (2.5 if len(token) >= 5 else 1.5) for token in unique_hits)
        if unique_hits and len(unique_hits) == len(dict.fromkeys(question_tokens)):
            score += 10.0
        return score

    def _best_snippet(self, chunk: str, question_tokens: list[str]) -> str:
        sentences = [
            re.sub(r"\s+", " ", sentence).strip()
            for sentence in re.split(r"(?<=[.!?])\s+|\n+", chunk)
            if sentence.strip()
        ]
        if not sentences:
            return chunk[:220].strip()

        scored = sorted(sentences, key=lambda sentence: self._sentence_score(sentence, question_tokens), reverse=True)
        return scored[0][:260].strip()

    def _sentence_score(self, sentence: str, question_tokens: list[str]) -> float:
        sentence_tokens = set(self._tokenize(sentence))
        hits = [token for token in question_tokens if token in sentence_tokens]
        return float(len(hits) * 3 + len(sentence))

    def _tokenize(self, text: str) -> list[str]:
        tokens = re.findall(r"[0-9A-Za-ząćęłńóśźż]{2,}", self._normalize_for_search(text))
        return [token for token in tokens if token not in self.STOPWORDS]

    def _normalize_for_search(self, text: str) -> str:
        normalized = re.sub(r"[^0-9A-Za-ząćęłńóśźż]+", " ", str(text or "").lower())
        return re.sub(r"\s+", " ", normalized).strip()

    def _build_document_summary(self, documents: list[dict[str, Any]]) -> dict[str, int]:
        summary = {
            "total": len(documents),
            "active": 0,
            "archived": 0,
            "deleted": 0,
            "queued": 0,
            "processing": 0,
            "ready": 0,
            "error": 0,
            "downloadable": 0,
            "assistant_enabled": 0,
            "exact_duplicates": 0,
            "similar_versions": 0,
            "folders": 0,
            "workflow_review_needed": 0,
            "workflow_official_missing": 0,
            "workflow_stable": 0,
            "business_roboczy": 0,
            "business_do_sprawdzenia": 0,
            "business_do_akceptacji": 0,
            "business_obowiazujacy": 0,
            "business_archiwalny": 0,
        }
        folder_paths: set[str] = set()
        for document in documents:
            lifecycle_status = str(document.get("lifecycle_status") or "active")
            if lifecycle_status in summary:
                summary[lifecycle_status] += 1
            status = str(document.get("processing_status") or "queued")
            if status in summary:
                summary[status] += 1
            if document.get("is_downloadable"):
                summary["downloadable"] += 1
            if document.get("use_in_assistant"):
                summary["assistant_enabled"] += 1
            if str(document.get("duplicate_status") or "none") == "exact_duplicate":
                summary["exact_duplicates"] += 1
            if str(document.get("duplicate_status") or "none") == "similar_version":
                summary["similar_versions"] += 1
            workflow_status = str(document.get("workflow_status") or "")
            if workflow_status == "review_needed":
                summary["workflow_review_needed"] += 1
            elif workflow_status == "official_missing":
                summary["workflow_official_missing"] += 1
            elif workflow_status == "stable":
                summary["workflow_stable"] += 1
            business_status = self._normalize_business_status(
                document.get("business_status") or self._derive_business_status_from_document(document)
            )
            if business_status:
                summary_key = f"business_{business_status}"
                if summary_key in summary:
                    summary[summary_key] += 1
            normalized_path = self._normalize_library_path(document.get("library_path") or "")
            if normalized_path:
                folder_paths.add(normalized_path)
        summary["folders"] = len(folder_paths)
        return summary

    def _build_folder_summary(self, documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, dict[str, Any]] = {}
        for document in documents:
            if not document.get("is_downloadable"):
                continue
            folder_path = self._normalize_library_path(document.get("library_path") or "")
            bucket = grouped.setdefault(
                folder_path,
                {
                    "path": folder_path,
                    "label": self._format_library_path_label(folder_path),
                    "document_count": 0,
                    "ready_count": 0,
                    "archived_count": 0,
                },
            )
            bucket["document_count"] += 1
            if str(document.get("processing_status") or "") == "ready":
                bucket["ready_count"] += 1
            if str(document.get("lifecycle_status") or "active") == "archived":
                bucket["archived_count"] += 1
        return sorted(grouped.values(), key=lambda item: (item["path"] != "", item["label"].lower()))

    def _build_activity_summary(
        self,
        documents: list[dict[str, Any]],
        *,
        unread_count: int,
        viewer_user_id: int | None = None,
    ) -> dict[str, int]:
        pending_review_count = sum(1 for item in documents if str(item.get("workflow_status") or "") in {"review_needed", "official_missing"})
        stable_count = sum(1 for item in documents if str(item.get("workflow_status") or "") == "stable")
        pending_decision_count = sum(
            1
            for item in documents
            if self._normalize_business_status(item.get("business_status")) in {"do_sprawdzenia", "do_akceptacji"}
        )
        awaiting_review_count = sum(
            1 for item in documents if self._normalize_business_status(item.get("business_status")) == "do_sprawdzenia"
        )
        awaiting_approval_count = sum(
            1 for item in documents if self._normalize_business_status(item.get("business_status")) == "do_akceptacji"
        )
        my_draft_count = 0
        my_review_count = 0
        my_approval_count = 0
        if viewer_user_id is not None:
            normalized_viewer_user_id = int(viewer_user_id)
            for item in documents:
                business_status = self._normalize_business_status(item.get("business_status"))
                if business_status == "roboczy" and int(item.get("owner_user_id") or 0) == normalized_viewer_user_id:
                    my_draft_count += 1
                if business_status == "do_sprawdzenia" and int(item.get("reviewer_user_id") or 0) == normalized_viewer_user_id:
                    my_review_count += 1
                if business_status == "do_akceptacji" and int(item.get("approver_user_id") or 0) == normalized_viewer_user_id:
                    my_approval_count += 1
        return {
            "unread_count": int(unread_count or 0),
            "pending_review_count": pending_review_count,
            "stable_count": stable_count,
            "pending_decision_count": pending_decision_count,
            "awaiting_review_count": awaiting_review_count,
            "awaiting_approval_count": awaiting_approval_count,
            "my_draft_count": my_draft_count,
            "my_review_count": my_review_count,
            "my_approval_count": my_approval_count,
            "my_attention_count": my_draft_count + my_review_count + my_approval_count,
        }

    def _serialize_document(
        self,
        document: dict[str, Any],
        *,
        version_limit: int | None = None,
        job_limit: int | None = None,
        include_audit: bool = False,
        include_comments: bool = False,
        include_full_content: bool = False,
        viewer_user_id: int | None = None,
    ) -> dict[str, Any]:
        content_text = str(document.get("content_text") or "").strip()
        snippet = content_text[:180].strip()
        if len(content_text) > 180:
            snippet = f"{snippet}..."
        content_preview = content_text[:900].strip()
        if len(content_text) > 900:
            content_preview = f"{content_preview}..."
        file_preview_kind = self._determine_file_preview_kind(
            str(document.get("file_name") or ""),
            str(document.get("mime_type") or ""),
        )
        versions = self.knowledge_repository.list_versions(
            int(document["knowledge_document_id"]),
            limit=self.DOCUMENT_LIST_VERSION_LIMIT if version_limit is None else version_limit,
        )
        recent_jobs = self.knowledge_repository.list_recent_jobs(
            int(document["knowledge_document_id"]),
            limit=self.DOCUMENT_LIST_JOB_LIMIT if job_limit is None else job_limit,
        )
        audit_events: list[dict[str, Any]] = []
        audit_summary = None
        if include_audit:
            raw_audit_events = self.event_repository.list_knowledge_document_logs(
                int(document["knowledge_document_id"]),
                organization_id=int(document["organization_id"]),
                limit=self.DETAIL_AUDIT_LIMIT,
            )
            audit_events = [self._serialize_document_audit_event(item) for item in raw_audit_events]
            audit_summary = self._build_document_audit_summary(audit_events)
        comments: list[dict[str, Any]] = []
        comment_summary = None
        version_comment_counts: dict[int, int] = {}
        if include_comments:
            raw_comments = self.knowledge_repository.list_comments(
                int(document["knowledge_document_id"]),
                limit=self.DETAIL_COMMENT_LIMIT,
            )
            comments = [self._serialize_document_comment(item) for item in raw_comments]
            comment_summary = self._build_document_comment_summary(comments)
            for item in comments:
                version_number = int(item.get("version_number") or 0)
                if version_number > 0:
                    version_comment_counts[version_number] = version_comment_counts.get(version_number, 0) + 1
        library_path = self._normalize_library_path(document.get("library_path") or "")
        current_version_number = int(document.get("current_version_number") or 0)
        official_version_number = int(document.get("official_version_number") or 0)
        business_status = self._normalize_business_status(
            document.get("business_status") or self._derive_business_status_from_document(document)
        )
        workflow_status = self._determine_document_workflow_status(
            lifecycle_status=str(document.get("lifecycle_status") or "active"),
            processing_status=str(document.get("processing_status") or "queued"),
            current_version_number=current_version_number,
            official_version_number=official_version_number,
        )
        owner = self._serialize_assignee(document, "owner")
        reviewer = self._serialize_assignee(document, "reviewer")
        approver = self._serialize_assignee(document, "approver")
        payload = {
            "knowledge_document_id": document["knowledge_document_id"],
            "organization_id": document["organization_id"],
            "organization_name": document.get("organization_name"),
            "organization_slug": document.get("organization_slug"),
            "title": document["title"],
            "file_name": document["file_name"],
            "mime_type": document.get("mime_type"),
            "file_link": document["file_link"],
            "file_storage_key": document["file_storage_key"],
            "char_count": int(document.get("char_count") or len(content_text)),
            "source_type": document.get("source_type") or "manual",
            "library_path": library_path,
            "library_path_label": self._format_library_path_label(library_path),
            "library_segments": library_path.split("/") if library_path else [],
            "is_downloadable": bool(document.get("is_downloadable", 1)),
            "use_in_assistant": bool(document.get("use_in_assistant", 1)),
            "lifecycle_status": str(document.get("lifecycle_status") or "active"),
            "archived_at": document.get("archived_at"),
            "archived_by_user_id": document.get("archived_by_user_id"),
            "deleted_at": document.get("deleted_at"),
            "deleted_by_user_id": document.get("deleted_by_user_id"),
            "duplicate_status": str(document.get("duplicate_status") or "none"),
            "duplicate_of_document_id": document.get("duplicate_of_document_id"),
            "duplicate_score": float(document.get("duplicate_score") or 0),
            "duplicate_reason": document.get("duplicate_reason"),
            "processing_status": document.get("processing_status") or "queued",
            "processing_error": document.get("processing_error"),
            "current_version_number": current_version_number,
            "official_version_number": official_version_number,
            "official_version_marked_at": document.get("official_version_marked_at"),
            "official_version_marked_by_user_id": document.get("official_version_marked_by_user_id"),
            "official_version_marked_by_login": document.get("official_version_marked_by_login"),
            "official_version_marked_by_display_name": document.get("official_version_marked_by_display_name"),
            "business_status": business_status,
            "business_status_label": self.BUSINESS_STATUS_LABELS.get(business_status, business_status),
            "owner_user_id": owner.get("user_id"),
            "owner_user_label": owner.get("label"),
            "reviewer_user_id": reviewer.get("user_id"),
            "reviewer_user_label": reviewer.get("label"),
            "approver_user_id": approver.get("user_id"),
            "approver_user_label": approver.get("label"),
            "responsibles": {
                "owner": owner,
                "reviewer": reviewer,
                "approver": approver,
            },
            "workflow_status": workflow_status,
            "workflow_status_label": self.WORKFLOW_STATUS_LABELS.get(workflow_status, workflow_status),
            "decision_actions": self._build_document_decision_actions(
                document,
                viewer_user_id=viewer_user_id,
                business_status=business_status,
                workflow_status=workflow_status,
            ),
            "last_processed_at": document.get("last_processed_at"),
            "processing_started_at": document.get("processing_started_at"),
            "snippet": snippet,
            "content_preview": content_preview,
            "has_text_preview": bool(content_text),
            "file_preview_kind": file_preview_kind,
            "created_at": document.get("created_at"),
            "updated_at": document.get("updated_at"),
            "created_by_login": document.get("created_by_login"),
            "created_by_display_name": document.get("created_by_display_name"),
            "versions": [
                {
                    "version_number": int(item["version_number"]),
                    "is_current": int(item["version_number"]) == current_version_number,
                    "is_official": official_version_number > 0
                    and int(item["version_number"]) == official_version_number,
                    "comment_count": version_comment_counts.get(int(item["version_number"]), 0),
                    "content_hash": item["content_hash"],
                    "char_count": int(item.get("char_count") or 0),
                    "source_type": item.get("source_type") or "manual",
                    "file_name": item.get("file_name"),
                    "mime_type": item.get("mime_type"),
                    "file_link": item.get("file_link"),
                    "extraction_method": item.get("extraction_method"),
                    "created_at": item.get("created_at"),
                    "snippet": (
                        f"{str(item.get('content_text') or '').strip()[:260]}..."
                        if len(str(item.get("content_text") or "").strip()) > 260
                        else str(item.get("content_text") or "").strip()
                    ),
                }
                for item in versions
            ],
            "recent_jobs": [
                {
                    "knowledge_processing_job_id": item["knowledge_processing_job_id"],
                    "job_type": item.get("job_type") or "ingest",
                    "status": item.get("status") or "pending",
                    "attempts": int(item.get("attempts") or 0),
                    "error_message": item.get("error_message"),
                    "created_at": item.get("created_at"),
                    "started_at": item.get("started_at"),
                    "finished_at": item.get("finished_at"),
                }
                for item in recent_jobs
            ],
        }
        if include_full_content:
            payload["content_text"] = content_text
        if include_audit:
            payload["audit_events"] = audit_events
            payload["audit_summary"] = audit_summary
        if include_comments:
            payload["comments"] = comments
            payload["comment_summary"] = comment_summary
        return payload

    def _determine_file_preview_kind(self, file_name: str, mime_type: str) -> str:
        suffix = Path(str(file_name or "")).suffix.lower()
        normalized_mime = str(mime_type or "").lower()
        if suffix == ".pdf" or normalized_mime == "application/pdf":
            return "pdf"
        if suffix in self.IMAGE_EXTENSIONS or normalized_mime.startswith("image/"):
            return "image"
        if suffix in self.TEXT_EXTENSIONS or normalized_mime.startswith("text/"):
            return "text"
        return "none"

    def _serialize_document_audit_event(self, event: dict[str, Any]) -> dict[str, Any]:
        details = self._parse_event_details(event.get("details"))
        event_type = str(event.get("event_type") or "")
        action_label = self.AUDIT_EVENT_LABELS.get(event_type, event_type.replace("_", " ").strip() or "Zdarzenie")
        highlights: list[dict[str, str]] = []

        def add_highlight(label: str, value: Any) -> None:
            normalized = self._format_audit_value(value)
            if normalized:
                highlights.append({"label": label, "value": normalized})

        if details.get("file_name"):
            add_highlight("Plik", details.get("file_name"))
        if details.get("library_path"):
            add_highlight("Folder", self._format_library_path_label(str(details.get("library_path") or "")))
        if details.get("version_number"):
            add_highlight("Wersja", f"v{int(details['version_number'])}")
        if details.get("previous_official_version_number"):
            add_highlight("Poprzednio obowiazywala", f"v{int(details['previous_official_version_number'])}")
        if details.get("restored_from_version_number"):
            add_highlight("Przywrocono z", f"v{int(details['restored_from_version_number'])}")
        if details.get("knowledge_processing_job_id"):
            add_highlight("Job", f"#{int(details['knowledge_processing_job_id'])}")
        if details.get("processing_status"):
            add_highlight("Pipeline", details.get("processing_status"))
        if details.get("lifecycle_status"):
            add_highlight("Stan", details.get("lifecycle_status"))
        if details.get("previous_lifecycle_status") and details.get("lifecycle_status"):
            add_highlight(
                "Zmiana stanu",
                f"{details['previous_lifecycle_status']} -> {details['lifecycle_status']}",
            )
        if details.get("business_status"):
            add_highlight(
                "Obieg",
                self.BUSINESS_STATUS_LABELS.get(str(details.get("business_status") or ""), details.get("business_status")),
            )
        if details.get("previous_business_status") and details.get("business_status"):
            add_highlight(
                "Zmiana obiegu",
                (
                    f"{self.BUSINESS_STATUS_LABELS.get(str(details['previous_business_status']), details['previous_business_status'])} -> "
                    f"{self.BUSINESS_STATUS_LABELS.get(str(details['business_status']), details['business_status'])}"
                ),
            )
        if details.get("owner_user_label"):
            add_highlight("Prowadzi", details.get("owner_user_label"))
        if details.get("reviewer_user_label"):
            add_highlight("Sprawdza", details.get("reviewer_user_label"))
        if details.get("approver_user_label"):
            add_highlight("Akceptuje", details.get("approver_user_label"))
        if "is_downloadable" in details:
            add_highlight("Biblioteka", "tak" if details.get("is_downloadable") else "nie")
        if "use_in_assistant" in details:
            add_highlight("Asystent", "tak" if details.get("use_in_assistant") else "nie")
        if details.get("extraction_method"):
            add_highlight("Ekstrakcja", details.get("extraction_method"))
        if details.get("annotation_kind"):
            add_highlight("Wpis", "adnotacja" if details.get("annotation_kind") == "annotation" else "komentarz")
        if details.get("anchor_label"):
            add_highlight("Zakres", details.get("anchor_label"))
        if details.get("action_label"):
            add_highlight("Decyzja", details.get("action_label"))
        if details.get("task_title"):
            add_highlight("Zadanie", details.get("task_title"))

        return {
            "event_id": int(event.get("id") or 0),
            "event_type": event_type,
            "action_label": action_label,
            "event_time": event.get("event_time"),
            "actor": event.get("actor") or "system",
            "message": event.get("decision_reason") or action_label,
            "status_before": event.get("status_before"),
            "status_after": event.get("status_after"),
            "organization_name": event.get("organization_name"),
            "organization_slug": event.get("organization_slug"),
            "is_download_event": event_type == "knowledge_document_downloaded",
            "highlights": highlights,
        }

    def _serialize_document_comment(self, comment: dict[str, Any]) -> dict[str, Any]:
        version_number = int(comment.get("version_number") or 0)
        annotation_kind = self._normalize_annotation_kind(comment.get("annotation_kind") or "comment")
        return {
            "knowledge_document_comment_id": int(comment.get("knowledge_document_comment_id") or 0),
            "knowledge_document_id": int(comment.get("knowledge_document_id") or 0),
            "knowledge_document_version_id": comment.get("knowledge_document_version_id"),
            "version_number": version_number or None,
            "is_version_comment": version_number > 0,
            "annotation_kind": annotation_kind,
            "annotation_kind_label": "Adnotacja" if annotation_kind == "annotation" else "Komentarz",
            "anchor_label": (str(comment.get("anchor_label") or "").strip() or None),
            "anchor_excerpt": (str(comment.get("anchor_excerpt") or "").strip() or None),
            "note_text": str(comment.get("note_text") or "").strip(),
            "created_at": comment.get("created_at"),
            "created_by_user_id": comment.get("created_by_user_id"),
            "created_by_login": comment.get("created_by_login"),
            "created_by_display_name": comment.get("created_by_display_name"),
            "author_label": comment.get("created_by_display_name")
            or comment.get("created_by_login")
            or "system",
            "target_label": f"Wersja v{version_number}" if version_number > 0 else "Dokument",
        }

    def _build_document_comment_summary(self, comments: list[dict[str, Any]]) -> dict[str, Any]:
        version_comments = [item for item in comments if item.get("is_version_comment")]
        document_comments = [item for item in comments if not item.get("is_version_comment")]
        return {
            "comment_count": len(comments),
            "version_comment_count": len(version_comments),
            "document_comment_count": len(document_comments),
            "last_comment_at": comments[0]["created_at"] if comments else None,
            "last_comment_author": comments[0]["author_label"] if comments else None,
        }

    def _determine_document_workflow_status(
        self,
        *,
        lifecycle_status: str,
        processing_status: str,
        current_version_number: int,
        official_version_number: int,
    ) -> str:
        if lifecycle_status == "deleted":
            return "deleted"
        if lifecycle_status == "archived":
            return "archived"
        if processing_status in {"queued", "processing"}:
            return "processing"
        if current_version_number <= 0:
            return "processing"
        if official_version_number <= 0:
            return "official_missing"
        if official_version_number < current_version_number:
            return "review_needed"
        return "stable"

    def _serialize_knowledge_activity_item(
        self,
        event: dict[str, Any],
        *,
        last_seen_event_id: int,
    ) -> dict[str, Any]:
        details = self._parse_event_details(event.get("details"))
        knowledge_document_id = self._parse_optional_positive_int(details.get("knowledge_document_id"))
        document = None
        if knowledge_document_id is not None and event.get("organization_id") is not None:
            document = self.knowledge_repository.get_by_id(
                int(knowledge_document_id),
                organization_id=int(event["organization_id"]),
            )
        serialized = self._serialize_document_audit_event(event)
        workflow_status = None
        if document:
            workflow_status = self._determine_document_workflow_status(
                lifecycle_status=str(document.get("lifecycle_status") or "active"),
                processing_status=str(document.get("processing_status") or "queued"),
                current_version_number=int(document.get("current_version_number") or 0),
                official_version_number=int(document.get("official_version_number") or 0),
            )
        business_status = None
        if document:
            business_status = self._normalize_business_status(
                document.get("business_status") or self._derive_business_status_from_document(document)
            )
        return {
            **serialized,
            "knowledge_document_id": knowledge_document_id,
            "document_title": (document or {}).get("title") or details.get("title"),
            "workflow_status": workflow_status,
            "workflow_status_label": self.WORKFLOW_STATUS_LABELS.get(workflow_status or "", workflow_status),
            "business_status": business_status,
            "business_status_label": self.BUSINESS_STATUS_LABELS.get(business_status or "", business_status),
            "is_unread": int(event.get("id") or 0) > int(last_seen_event_id or 0),
        }

    def _build_document_audit_summary(self, audit_events: list[dict[str, Any]]) -> dict[str, Any]:
        download_events = [item for item in audit_events if item.get("is_download_event")]
        change_events = [item for item in audit_events if not item.get("is_download_event")]
        return {
            "event_count": len(audit_events),
            "download_count": len(download_events),
            "change_count": len(change_events),
            "last_event_at": audit_events[0]["event_time"] if audit_events else None,
            "last_change_at": change_events[0]["event_time"] if change_events else None,
            "last_download_at": download_events[0]["event_time"] if download_events else None,
            "last_actor": audit_events[0]["actor"] if audit_events else None,
        }

    def _parse_event_details(self, raw_details: Any) -> dict[str, Any]:
        if isinstance(raw_details, dict):
            return raw_details
        if not raw_details:
            return {}
        try:
            parsed = json.loads(str(raw_details))
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _format_audit_value(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, bool):
            return "tak" if value else "nie"
        if isinstance(value, float):
            return f"{value:.2f}".rstrip("0").rstrip(".")
        return str(value).strip()

    def _serialize_watch_status(self, watch_status: dict[str, Any] | None) -> dict[str, Any]:
        status = dict(watch_status or {})
        last_scan_status = str(status.get("last_scan_status") or "idle")
        return {
            "enabled": bool(watch_status),
            "watch_mode": str(status.get("watch_mode") or "polling"),
            "last_scan_started_at": status.get("last_scan_started_at"),
            "last_scan_completed_at": status.get("last_scan_completed_at"),
            "last_scan_status": last_scan_status,
            "last_actor": status.get("last_actor"),
            "last_error": status.get("last_error"),
            "queued_new": int(status.get("queued_new") or 0),
            "queued_updates": int(status.get("queued_updates") or 0),
            "unchanged_count": int(status.get("unchanged_count") or 0),
            "skipped_count": int(status.get("skipped_count") or 0),
            "duplicate_count": int(status.get("duplicate_count") or 0),
            "similar_count": int(status.get("similar_count") or 0),
            "is_healthy": last_scan_status not in {"failed", "error"},
        }

    def _refresh_document_relationships(self, knowledge_document_id: int, organization_id: int) -> None:
        document = self.knowledge_repository.get_by_id(knowledge_document_id, organization_id=organization_id)
        if not document:
            return

        duplicate_status = "none"
        duplicate_of_document_id = None
        duplicate_score = 0.0
        duplicate_reason = None

        exact_duplicates = self.knowledge_repository.find_by_content_hash(
            organization_id,
            str(document.get("content_hash") or ""),
            exclude_document_id=knowledge_document_id,
        )
        if exact_duplicates:
            duplicate_status = "exact_duplicate"
            duplicate_of_document_id = int(exact_duplicates[0]["knowledge_document_id"])
            duplicate_score = 1.0
            duplicate_reason = f"Dokument ma identyczna zawartosc jak pozycja #{duplicate_of_document_id}."
        else:
            best_similar = self._find_best_similar_document(document, organization_id=organization_id)
            if best_similar is not None:
                duplicate_status = "similar_version"
                duplicate_of_document_id = int(best_similar["knowledge_document_id"])
                duplicate_score = float(best_similar["score"])
                duplicate_reason = (
                    f"Dokument jest bardzo podobny do pozycji #{duplicate_of_document_id} "
                    f"({round(duplicate_score * 100)}% zgodnosci)."
                )

        self.knowledge_repository.update(
            knowledge_document_id,
            {
                "duplicate_status": duplicate_status,
                "duplicate_of_document_id": duplicate_of_document_id,
                "duplicate_score": duplicate_score,
                "duplicate_reason": duplicate_reason,
            },
        )

    def _find_best_similar_document(
        self,
        document: dict[str, Any],
        *,
        organization_id: int,
    ) -> dict[str, Any] | None:
        base_text = self._normalize_content_text(str(document.get("content_text") or ""))
        if len(base_text) < 80:
            return None

        best_match: dict[str, Any] | None = None
        for candidate in self.knowledge_repository.list_similarity_candidates(
            organization_id,
            exclude_document_id=int(document["knowledge_document_id"]),
        ):
            candidate_text = self._normalize_content_text(str(candidate.get("content_text") or ""))
            if len(candidate_text) < 80:
                continue
            score = SequenceMatcher(None, base_text, candidate_text).ratio()
            if score < self.SIMILARITY_THRESHOLD:
                continue
            if best_match is None or score > float(best_match["score"]):
                best_match = {
                    "knowledge_document_id": int(candidate["knowledge_document_id"]),
                    "score": score,
                }
        return best_match

    def _normalize_library_path(self, value: str) -> str:
        text = str(value or "").replace("\\", "/").strip()
        text = re.sub(r"/{2,}", "/", text)
        text = text.strip("/")
        if not text:
            return ""
        segments = [segment.strip() for segment in text.split("/") if segment.strip() and segment.strip() not in {".", ".."}]
        return "/".join(segments)

    def _format_library_path_label(self, library_path: str) -> str:
        normalized = self._normalize_library_path(library_path)
        if not normalized:
            return "Bez folderu"
        return " / ".join(part.replace("_", " ").replace("-", " ").strip() or part for part in normalized.split("/"))

    def _library_path_from_relative_file(self, file_path: Path, folder_path: Path) -> str:
        relative_parent = file_path.relative_to(folder_path).parent
        if str(relative_parent) in {".", ""}:
            return ""
        return self._normalize_library_path(relative_parent.as_posix())
