from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.config import (
    DOCUMENTS_DIR,
    DOCUMENTS_ROUTE_PREFIX,
    KNOWLEDGE_DIR,
    KNOWLEDGE_ROUTE_PREFIX,
    OCR_DIR,
    OCR_ROUTE_PREFIX,
    WHITEBOARD_DIR,
    WHITEBOARD_ROUTE_PREFIX,
)


class StorageError(ValueError):
    pass


@dataclass(frozen=True)
class StoredArtifact:
    storage_backend: str
    storage_key: str
    public_link: str


class StorageService(Protocol):
    backend_name: str

    def save_binary(self, artifact_type: str, relative_path: Path, content: bytes) -> StoredArtifact:
        ...

    def save_text(self, artifact_type: str, relative_path: Path, content: str) -> StoredArtifact:
        ...

    def build_public_link(self, artifact_type: str, storage_key: str) -> str:
        ...

    def resolve_local_path(self, artifact_type: str, storage_key: str) -> Path:
        ...

    def route_prefix(self, artifact_type: str) -> str:
        ...


class LocalStorageService:
    backend_name = "lokalny"

    def save_binary(self, artifact_type: str, relative_path: Path, content: bytes) -> StoredArtifact:
        target = self._resolve_target(artifact_type, relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_bytes(content)
        return StoredArtifact(
            storage_backend=self.backend_name,
            storage_key=relative_path.as_posix(),
            public_link=self.build_public_link(artifact_type, relative_path.as_posix()),
        )

    def save_text(self, artifact_type: str, relative_path: Path, content: str) -> StoredArtifact:
        target = self._resolve_target(artifact_type, relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text(content, encoding="utf-8")
        return StoredArtifact(
            storage_backend=self.backend_name,
            storage_key=relative_path.as_posix(),
            public_link=self.build_public_link(artifact_type, relative_path.as_posix()),
        )

    def build_public_link(self, artifact_type: str, storage_key: str) -> str:
        return f"{self.route_prefix(artifact_type)}{storage_key.lstrip('/')}"

    def resolve_local_path(self, artifact_type: str, storage_key: str) -> Path:
        relative = Path(storage_key.lstrip("/"))
        return self._resolve_target(artifact_type, relative)

    def route_prefix(self, artifact_type: str) -> str:
        if artifact_type == "document":
            return DOCUMENTS_ROUTE_PREFIX
        if artifact_type == "ocr":
            return OCR_ROUTE_PREFIX
        if artifact_type == "knowledge":
            return KNOWLEDGE_ROUTE_PREFIX
        if artifact_type == "whiteboard":
            return WHITEBOARD_ROUTE_PREFIX
        raise StorageError(f"Nieznany typ artefaktu: {artifact_type}")

    def root_dir(self, artifact_type: str) -> Path:
        if artifact_type == "document":
            return DOCUMENTS_DIR
        if artifact_type == "ocr":
            return OCR_DIR
        if artifact_type == "knowledge":
            return KNOWLEDGE_DIR
        if artifact_type == "whiteboard":
            return WHITEBOARD_DIR
        raise StorageError(f"Nieznany typ artefaktu: {artifact_type}")

    def _resolve_target(self, artifact_type: str, relative_path: Path) -> Path:
        root = self.root_dir(artifact_type).resolve()
        target = (root / relative_path).resolve()
        try:
            target.relative_to(root)
        except ValueError as error:
            raise StorageError("Nieprawidłowa ścieżka magazynu plików.") from error
        return target
