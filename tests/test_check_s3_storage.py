from __future__ import annotations

from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from unittest import TestCase
from uuid import UUID

from scripts import check_s3_storage


class StorageNotFoundError(Exception):
    pass


class FakeDeleteClient:
    def __init__(self) -> None:
        self.deleted: list[tuple[str, str]] = []

    def delete_object(self, *, Bucket: str, Key: str) -> None:
        self.deleted.append((Bucket, Key))


class FakeS3Service:
    bucket = "casi-private"

    def __init__(self, config: check_s3_storage.S3CheckConfig) -> None:
        self.config = config
        self.objects: dict[str, bytes] = {}
        self.client = FakeDeleteClient()

    def save_binary(self, artifact_type: str, relative_path: Path, content: bytes):
        storage_key = relative_path.as_posix()
        self.objects[storage_key] = content
        return type(
            "Artifact",
            (),
            {
                "storage_key": storage_key,
                "storage_backend": "s3",
                "public_link": f"/pliki/dokumenty/{storage_key}",
            },
        )()

    def read_binary(self, artifact_type: str, storage_key: str) -> bytes:
        if storage_key not in self.objects:
            raise StorageNotFoundError("missing")
        return self.objects[storage_key]

    def object_key(self, artifact_type: str, storage_key: str) -> str:
        return f"{self.config.prefix}/dokumenty/{storage_key}"

    def _client_or_raise(self):
        return self.client


def valid_env(**overrides: str) -> dict[str, str]:
    env = {
        "INVOICE_STORAGE_BACKEND": "s3",
        "INVOICE_S3_ENDPOINT_URL": "https://fra1.digitaloceanspaces.com",
        "INVOICE_S3_REGION": "fra1",
        "INVOICE_S3_BUCKET": "casi-private",
        "INVOICE_S3_ACCESS_KEY_ID": "test-access",
        "INVOICE_S3_SECRET_ACCESS_KEY": "super-secret-value",
        "INVOICE_S3_PREFIX": "casi/dev-test",
    }
    env.update(overrides)
    return env


class S3StorageCheckScriptTests(TestCase):
    def test_refuses_to_run_for_local_backend(self) -> None:
        with self.assertRaisesRegex(check_s3_storage.S3StorageCheckError, "INVOICE_STORAGE_BACKEND=s3"):
            check_s3_storage.validate_environment(valid_env(INVOICE_STORAGE_BACKEND="local"))

    def test_reports_missing_required_env_without_secret_values(self) -> None:
        env = valid_env(INVOICE_S3_BUCKET="", INVOICE_S3_SECRET_ACCESS_KEY="super-secret-value")
        with self.assertRaises(check_s3_storage.S3StorageCheckError) as context:
            check_s3_storage.validate_environment(env)

        message = str(context.exception)
        self.assertIn("INVOICE_S3_BUCKET", message)
        self.assertNotIn("super-secret-value", message)

    def test_refuses_production_like_prefix_by_default(self) -> None:
        with self.assertRaisesRegex(check_s3_storage.S3StorageCheckError, "produkcyjnie"):
            check_s3_storage.validate_environment(valid_env(INVOICE_S3_PREFIX="casi/prod"))

    def test_allows_production_like_prefix_only_with_explicit_override(self) -> None:
        config = check_s3_storage.validate_environment(
            valid_env(INVOICE_S3_PREFIX="casi/prod", INVOICE_ALLOW_S3_PROD_PREFIX_TEST="1")
        )
        self.assertEqual(config.prefix, "casi/prod")

    def test_build_test_storage_key_is_unique_and_safe(self) -> None:
        fixed_uuid = UUID("12345678-1234-5678-1234-567812345678")
        key = check_s3_storage.build_test_storage_key(
            datetime(2026, 5, 14, 9, 30, tzinfo=timezone.utc),
            uuid_factory=lambda: fixed_uuid,
        )
        self.assertEqual(
            key,
            "testy/storage-smoke/20260514T093000Z-12345678123456781234567812345678.txt",
        )

    def test_run_check_uses_fake_service_and_does_not_print_secret(self) -> None:
        env = valid_env()
        out = StringIO()
        services: list[FakeS3Service] = []

        def factory(config: check_s3_storage.S3CheckConfig) -> FakeS3Service:
            service = FakeS3Service(config)
            services.append(service)
            return service

        result = check_s3_storage.run_check(env=env, out=out, service_factory=factory)

        self.assertEqual(result, 0)
        output = out.getvalue()
        self.assertIn("CASI S3 storage integration check", output)
        self.assertIn("casi/dev-test", output)
        self.assertNotIn("super-secret-value", output)
        self.assertEqual(len(services), 1)
        self.assertEqual(len(services[0].objects), 1)
        saved_storage_key = next(iter(services[0].objects))
        self.assertTrue(saved_storage_key.startswith("testy/storage-smoke/"))
        self.assertFalse(saved_storage_key.startswith("casi/dev-test"))
        self.assertEqual(len(services[0].client.deleted), 1)
        deleted_bucket, deleted_key = services[0].client.deleted[0]
        self.assertEqual(deleted_bucket, "casi-private")
        self.assertTrue(deleted_key.startswith("casi/dev-test/dokumenty/testy/storage-smoke/"))
