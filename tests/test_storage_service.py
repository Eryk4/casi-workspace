from __future__ import annotations

import os
from io import BytesIO
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

os.environ.setdefault("INVOICE_DB_ENGINE", "sqlite")
os.environ.setdefault("INVOICE_DATABASE_URL", "")
os.environ.setdefault("DATABASE_URL", "")
os.environ.setdefault("INVOICE_STORAGE_BACKEND", "local")

from app.bootstrap import build_storage_service
from app.config import normalize_storage_backend
from app.services.storage_service import (
    LocalStorageService,
    S3StorageService,
    StorageError,
    StorageNotFoundError,
)


class FakeS3Client:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], dict[str, object]] = {}

    def put_object(self, **kwargs):
        self.objects[(kwargs["Bucket"], kwargs["Key"])] = kwargs
        return {"ETag": "fake"}

    def get_object(self, **kwargs):
        stored = self.objects.get((kwargs["Bucket"], kwargs["Key"]))
        if stored is None:
            raise FakeClientError("NoSuchKey")
        return {"Body": BytesIO(stored["Body"])}


class FakeClientError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.response = {"Error": {"Code": code}}


class StorageBackendSelectionTests(TestCase):
    def test_local_is_default_backend_name(self) -> None:
        self.assertEqual(normalize_storage_backend(None), "local")
        self.assertEqual(normalize_storage_backend(""), "local")

    def test_build_storage_service_uses_local_backend(self) -> None:
        storage = build_storage_service("local")
        self.assertIsInstance(storage, LocalStorageService)

    def test_build_storage_service_defaults_to_local_backend(self) -> None:
        storage = build_storage_service()
        self.assertIsInstance(storage, LocalStorageService)

    def test_build_storage_service_uses_s3_backend(self) -> None:
        sentinel = object()
        with patch("app.bootstrap.S3StorageService", return_value=sentinel) as constructor:
            self.assertIs(build_storage_service("s3"), sentinel)
        constructor.assert_called_once_with()

    def test_build_storage_service_rejects_invalid_backend(self) -> None:
        with self.assertRaisesRegex(StorageError, "INVOICE_STORAGE_BACKEND"):
            build_storage_service("ftp")


class S3StorageServiceTests(TestCase):
    def build_service(self) -> tuple[S3StorageService, FakeS3Client]:
        client = FakeS3Client()
        service = S3StorageService(
            endpoint_url="https://fra1.digitaloceanspaces.com",
            region="fra1",
            bucket="casi-private",
            access_key_id="test-access",
            secret_access_key="test-secret",
            prefix="casi/prod",
            client=client,
        )
        return service, client

    def test_object_key_uses_prefix_and_artifact_root(self) -> None:
        service, _client = self.build_service()
        self.assertEqual(
            service.object_key("document", "organizacje/casi/faktura.pdf"),
            "casi/prod/dokumenty/organizacje/casi/faktura.pdf",
        )
        self.assertEqual(
            service.object_key("ocr", Path("organizacje/casi/ocr.txt").as_posix()),
            "casi/prod/ocr/organizacje/casi/ocr.txt",
        )

    def test_object_key_does_not_duplicate_existing_artifact_root(self) -> None:
        service, _client = self.build_service()
        self.assertEqual(
            service.object_key("document", "dokumenty/organizacje/casi/faktura.pdf"),
            "casi/prod/dokumenty/organizacje/casi/faktura.pdf",
        )

    def test_save_and_read_binary_use_s3_client_without_public_link_bypass(self) -> None:
        service, client = self.build_service()
        artifact = service.save_binary("document", Path("organizacje/casi/faktura.pdf"), b"pdf-bytes")

        self.assertEqual(artifact.storage_backend, "s3")
        self.assertEqual(artifact.storage_key, "organizacje/casi/faktura.pdf")
        self.assertEqual(artifact.public_link, "/pliki/dokumenty/organizacje/casi/faktura.pdf")
        self.assertIn(("casi-private", "casi/prod/dokumenty/organizacje/casi/faktura.pdf"), client.objects)
        self.assertEqual(service.read_binary("document", artifact.storage_key), b"pdf-bytes")

    def test_save_text_writes_utf8_text_object(self) -> None:
        service, client = self.build_service()
        artifact = service.save_text("knowledge", Path("organizacje/casi/notatka.txt"), "tresc")

        stored = client.objects[("casi-private", "casi/prod/wiedza/organizacje/casi/notatka.txt")]
        self.assertEqual(stored["Body"], b"tresc")
        self.assertEqual(stored["ContentType"], "text/plain; charset=utf-8")
        self.assertEqual(artifact.public_link, "/pliki/wiedza/organizacje/casi/notatka.txt")

    def test_read_missing_object_raises_storage_not_found(self) -> None:
        service, _client = self.build_service()
        with self.assertRaises(StorageNotFoundError):
            service.read_binary("document", "organizacje/casi/brak.pdf")

    def test_invalid_storage_key_rejects_parent_traversal(self) -> None:
        service, _client = self.build_service()
        with self.assertRaises(StorageError):
            service.object_key("document", "../secret.txt")

    def test_s3_configuration_requires_core_values(self) -> None:
        with self.assertRaisesRegex(StorageError, "INVOICE_S3_ENDPOINT_URL"):
            S3StorageService(
                endpoint_url="",
                region="fra1",
                bucket="",
                access_key_id="",
                secret_access_key="",
                client=FakeS3Client(),
            )
