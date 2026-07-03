from __future__ import annotations

from dataclasses import dataclass
import mimetypes
from pathlib import Path
from typing import Any, Protocol

from app.config import (
    DOCUMENTS_DIR,
    DOCUMENTS_ROUTE_PREFIX,
    KNOWLEDGE_DIR,
    KNOWLEDGE_ROUTE_PREFIX,
    OCR_DIR,
    OCR_ROUTE_PREFIX,
    S3_ACCESS_KEY_ID,
    S3_BUCKET,
    S3_ENDPOINT_URL,
    S3_PREFIX,
    S3_REGION,
    S3_SECRET_ACCESS_KEY,
    WHITEBOARD_DIR,
    WHITEBOARD_ROUTE_PREFIX,
)


class StorageError(ValueError):
    pass


class StorageNotFoundError(StorageError):
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

    def read_binary(self, artifact_type: str, storage_key: str) -> bytes:
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

    def read_binary(self, artifact_type: str, storage_key: str) -> bytes:
        target = self.resolve_local_path(artifact_type, storage_key)
        if not target.exists() or not target.is_file():
            raise StorageNotFoundError("Plik nie istnieje w lokalnym magazynie.")
        return target.read_bytes()

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
            raise StorageError("Nieprawidlowa sciezka magazynu plikow.") from error
        return target


class S3StorageService:
    backend_name = "s3"

    def __init__(
        self,
        *,
        endpoint_url: str = S3_ENDPOINT_URL,
        region: str = S3_REGION,
        bucket: str = S3_BUCKET,
        access_key_id: str = S3_ACCESS_KEY_ID,
        secret_access_key: str = S3_SECRET_ACCESS_KEY,
        prefix: str = S3_PREFIX,
        client: Any | None = None,
    ) -> None:
        self.endpoint_url = endpoint_url.strip()
        self.region = region.strip()
        self.bucket = bucket.strip()
        self.access_key_id = access_key_id.strip()
        self.secret_access_key = secret_access_key
        self.prefix = prefix.strip().strip("/")
        self._client = client
        self._validate_configuration()

    def save_binary(self, artifact_type: str, relative_path: Path, content: bytes) -> StoredArtifact:
        storage_key = self._normalize_storage_key(relative_path.as_posix())
        self._client_or_raise().put_object(
            Bucket=self.bucket,
            Key=self.object_key(artifact_type, storage_key),
            Body=content,
            ContentType=mimetypes.guess_type(storage_key)[0] or "application/octet-stream",
        )
        return StoredArtifact(
            storage_backend=self.backend_name,
            storage_key=storage_key,
            public_link=self.build_public_link(artifact_type, storage_key),
        )

    def save_text(self, artifact_type: str, relative_path: Path, content: str) -> StoredArtifact:
        storage_key = self._normalize_storage_key(relative_path.as_posix())
        self._client_or_raise().put_object(
            Bucket=self.bucket,
            Key=self.object_key(artifact_type, storage_key),
            Body=content.encode("utf-8"),
            ContentType="text/plain; charset=utf-8",
        )
        return StoredArtifact(
            storage_backend=self.backend_name,
            storage_key=storage_key,
            public_link=self.build_public_link(artifact_type, storage_key),
        )

    def build_public_link(self, artifact_type: str, storage_key: str) -> str:
        return f"{self.route_prefix(artifact_type)}{storage_key.lstrip('/')}"

    def read_binary(self, artifact_type: str, storage_key: str) -> bytes:
        normalized_key = self._normalize_storage_key(storage_key)
        try:
            response = self._client_or_raise().get_object(
                Bucket=self.bucket,
                Key=self.object_key(artifact_type, normalized_key),
            )
        except Exception as error:
            if self._looks_like_missing_object(error):
                raise StorageNotFoundError("Plik nie istnieje w magazynie S3.") from error
            raise StorageError("Nie udalo sie odczytac pliku z magazynu S3.") from error

        body = response.get("Body")
        if body is None:
            return b""
        try:
            return body.read()
        finally:
            close = getattr(body, "close", None)
            if callable(close):
                close()

    def resolve_local_path(self, artifact_type: str, storage_key: str) -> Path:
        raise StorageError("Magazyn S3 nie udostepnia lokalnej sciezki pliku.")

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

    def object_key(self, artifact_type: str, storage_key: str) -> str:
        artifact_root = self._artifact_root(artifact_type)
        normalized_key = self._storage_key_without_artifact_root(artifact_root, storage_key)
        parts = [
            part
            for part in (self.prefix, artifact_root, normalized_key)
            if part
        ]
        return "/".join(parts)

    def _client_or_raise(self):
        if self._client is not None:
            return self._client
        try:
            import boto3
        except ImportError as error:
            raise StorageError(
                "Brakuje biblioteki boto3 wymaganej dla INVOICE_STORAGE_BACKEND=s3."
            ) from error
        self._client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name=self.region or None,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
        )
        return self._client

    def _validate_configuration(self) -> None:
        missing = []
        if not self.endpoint_url:
            missing.append("INVOICE_S3_ENDPOINT_URL")
        if not self.bucket:
            missing.append("INVOICE_S3_BUCKET")
        if not self.access_key_id:
            missing.append("INVOICE_S3_ACCESS_KEY_ID")
        if not self.secret_access_key:
            missing.append("INVOICE_S3_SECRET_ACCESS_KEY")
        if missing:
            raise StorageError(
                "Brakuje konfiguracji S3 dla INVOICE_STORAGE_BACKEND=s3: "
                + ", ".join(missing)
                + "."
            )

    def _artifact_root(self, artifact_type: str) -> str:
        if artifact_type == "document":
            return "dokumenty"
        if artifact_type == "ocr":
            return "ocr"
        if artifact_type == "knowledge":
            return "wiedza"
        if artifact_type == "whiteboard":
            return "tablica"
        raise StorageError(f"Nieznany typ artefaktu: {artifact_type}")

    def _normalize_storage_key(self, storage_key: str) -> str:
        normalized = storage_key.replace("\\", "/").lstrip("/")
        parts = [part for part in normalized.split("/") if part not in {"", "."}]
        if any(part == ".." for part in parts):
            raise StorageError("Nieprawidlowa sciezka magazynu plikow.")
        return "/".join(parts)

    def _storage_key_without_artifact_root(self, artifact_root: str, storage_key: str) -> str:
        normalized_key = self._normalize_storage_key(storage_key)
        prefix = f"{artifact_root}/"
        if normalized_key == artifact_root:
            return ""
        if normalized_key.startswith(prefix):
            return normalized_key.removeprefix(prefix)
        return normalized_key

    def _looks_like_missing_object(self, error: Exception) -> bool:
        response = getattr(error, "response", None)
        if not isinstance(response, dict):
            return False
        code = str(response.get("Error", {}).get("Code") or "").lower()
        return code in {"nosuchkey", "404", "notfound", "no such key"}
