from __future__ import annotations

import os
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping, TextIO


REQUIRED_ENV = (
    "INVOICE_STORAGE_BACKEND",
    "INVOICE_S3_ENDPOINT_URL",
    "INVOICE_S3_REGION",
    "INVOICE_S3_BUCKET",
    "INVOICE_S3_ACCESS_KEY_ID",
    "INVOICE_S3_SECRET_ACCESS_KEY",
    "INVOICE_S3_PREFIX",
)
ALLOW_PROD_PREFIX_ENV = "INVOICE_ALLOW_S3_PROD_PREFIX_TEST"
DEFAULT_TEST_ARTIFACT_TYPE = "document"


class S3StorageCheckError(RuntimeError):
    pass


@dataclass(frozen=True)
class S3CheckConfig:
    endpoint_url: str
    region: str
    bucket: str
    access_key_id: str
    secret_access_key: str
    prefix: str


def _clean(value: str | None) -> str:
    return str(value or "").strip()


def is_production_like_prefix(prefix: str) -> bool:
    normalized = _clean(prefix).strip("/").lower()
    if normalized in {"prod", "production", "casi/prod", "casi/production"}:
        return True
    return (
        normalized.startswith("prod/")
        or normalized.startswith("production/")
        or normalized.endswith("/prod")
        or normalized.endswith("/production")
        or "/prod/" in normalized
        or "/production/" in normalized
    )


def validate_environment(env: Mapping[str, str]) -> S3CheckConfig:
    backend = _clean(env.get("INVOICE_STORAGE_BACKEND")).lower()
    if backend != "s3":
        raise S3StorageCheckError(
            "Ten test wymaga INVOICE_STORAGE_BACKEND=s3. "
            "Nie uruchamiam integracji S3 dla innego backendu."
        )

    missing = [name for name in REQUIRED_ENV if not _clean(env.get(name))]
    if missing:
        raise S3StorageCheckError(
            "Brakuje wymaganych zmiennych dla testu S3: " + ", ".join(missing) + "."
        )

    prefix = _clean(env.get("INVOICE_S3_PREFIX")).strip("/")
    if is_production_like_prefix(prefix) and _clean(env.get(ALLOW_PROD_PREFIX_ENV)) != "1":
        raise S3StorageCheckError(
            "INVOICE_S3_PREFIX wyglada produkcyjnie. "
            f"Uzyj testowego prefiksu, np. casi/dev-test, albo ustaw {ALLOW_PROD_PREFIX_ENV}=1."
        )

    return S3CheckConfig(
        endpoint_url=_clean(env.get("INVOICE_S3_ENDPOINT_URL")),
        region=_clean(env.get("INVOICE_S3_REGION")),
        bucket=_clean(env.get("INVOICE_S3_BUCKET")),
        access_key_id=_clean(env.get("INVOICE_S3_ACCESS_KEY_ID")),
        secret_access_key=str(env.get("INVOICE_S3_SECRET_ACCESS_KEY") or ""),
        prefix=prefix,
    )


def build_test_storage_key(now: datetime | None = None, uuid_factory: Callable[[], uuid.UUID] = uuid.uuid4) -> str:
    current = now or datetime.now(timezone.utc)
    timestamp = current.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"testy/storage-smoke/{timestamp}-{uuid_factory().hex}.txt"


def build_test_payload(storage_key: str) -> bytes:
    created_at = datetime.now(timezone.utc).isoformat()
    return (
        "CASI Workspace S3 storage smoke test\n"
        f"storage_key={storage_key}\n"
        f"created_at={created_at}\n"
    ).encode("utf-8")


def _prepare_storage_import_environment(env: Mapping[str, str]) -> None:
    if not _clean(env.get("INVOICE_DATABASE_URL")) and not _clean(env.get("DATABASE_URL")):
        os.environ.setdefault("INVOICE_DB_ENGINE", "sqlite")
        os.environ.setdefault("INVOICE_DATABASE_URL", "")
        os.environ.setdefault("DATABASE_URL", "")


def build_s3_storage_service(config: S3CheckConfig):
    _prepare_storage_import_environment(os.environ)
    from app.services.storage_service import S3StorageService

    return S3StorageService(
        endpoint_url=config.endpoint_url,
        region=config.region,
        bucket=config.bucket,
        access_key_id=config.access_key_id,
        secret_access_key=config.secret_access_key,
        prefix=config.prefix,
    )


def _is_storage_not_found(error: Exception) -> bool:
    return error.__class__.__name__ == "StorageNotFoundError"


def cleanup_test_object(service, artifact_type: str, storage_key: str, out: TextIO) -> None:
    object_key = service.object_key(artifact_type, storage_key)
    try:
        client = service._client_or_raise()
        client.delete_object(Bucket=service.bucket, Key=object_key)
    except Exception as error:
        print(f"[WARN] Nie udalo sie usunac obiektu testowego: {type(error).__name__}.", file=out)
        return
    print(f"[OK] Usunieto obiekt testowy: {object_key}", file=out)


def run_check(
    env: Mapping[str, str] | None = None,
    out: TextIO = sys.stdout,
    service_factory: Callable[[S3CheckConfig], object] | None = None,
) -> int:
    env = os.environ if env is None else env
    config = validate_environment(env)
    storage_key = build_test_storage_key()
    payload = build_test_payload(storage_key)
    service = service_factory(config) if service_factory else build_s3_storage_service(config)

    print("[START] CASI S3 storage integration check", file=out)
    print(f"[INFO] endpoint={config.endpoint_url}", file=out)
    print(f"[INFO] region={config.region}", file=out)
    print(f"[INFO] bucket={config.bucket}", file=out)
    print(f"[INFO] prefix={config.prefix}", file=out)
    print(f"[INFO] logical_storage_key={storage_key}", file=out)

    artifact = service.save_binary(DEFAULT_TEST_ARTIFACT_TYPE, Path(storage_key), payload)
    if config.prefix and artifact.storage_key.startswith(config.prefix):
        raise S3StorageCheckError("Logiczny storage_key nie moze zawierac INVOICE_S3_PREFIX.")
    if artifact.storage_key != storage_key:
        raise S3StorageCheckError("Logiczny storage_key rozni sie od testowego storage key.")

    physical_key = service.object_key(DEFAULT_TEST_ARTIFACT_TYPE, artifact.storage_key)
    expected_prefix = f"{config.prefix}/dokumenty/" if config.prefix else "dokumenty/"
    if not physical_key.startswith(expected_prefix):
        raise S3StorageCheckError("Fizyczny klucz obiektu nie uzywa oczekiwanego INVOICE_S3_PREFIX.")
    print(f"[OK] Zapisano obiekt testowy: {physical_key}", file=out)

    downloaded = service.read_binary(DEFAULT_TEST_ARTIFACT_TYPE, artifact.storage_key)
    if downloaded != payload:
        raise S3StorageCheckError("Pobrana tresc rozni sie od wyslanej.")
    print("[OK] Pobrano obiekt testowy i potwierdzono zgodnosc tresci.", file=out)

    missing_key = storage_key.replace(".txt", "-missing.txt")
    try:
        service.read_binary(DEFAULT_TEST_ARTIFACT_TYPE, missing_key)
    except Exception as error:
        if not _is_storage_not_found(error):
            raise
    else:
        raise S3StorageCheckError("Odczyt brakujacego obiektu nie zakonczyl sie StorageNotFoundError.")
    print("[OK] Brakujacy obiekt zwraca oczekiwany blad not-found.", file=out)

    cleanup_test_object(service, DEFAULT_TEST_ARTIFACT_TYPE, artifact.storage_key, out)
    print("[OK] CASI S3 storage integration check zakonczony.", file=out)
    return 0


def main() -> int:
    try:
        return run_check()
    except S3StorageCheckError as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 2
    except Exception as error:
        print(f"[ERROR] Nieoczekiwany blad testu S3: {type(error).__name__}.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
