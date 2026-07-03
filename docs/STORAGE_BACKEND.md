# CASI Storage Backend

CASI Workspace supports two storage backends for documents, invoices, OCR files, knowledge files, whiteboard uploads, and other stored artifacts.

## Backends

### `local`

`INVOICE_STORAGE_BACKEND=local` is the default mode.

Files are stored under the local `STORAGE_ROOT`, which defaults to:

```text
data/magazyn
```

This mode is intended for local development and tests. It preserves the previous application behavior.

### `s3`

`INVOICE_STORAGE_BACKEND=s3` stores files in an S3-compatible object store such as DigitalOcean Spaces.

The application keeps the existing logical storage keys, for example:

```text
organizacje/casi/faktura.pdf
organizacje/casi/ocr.txt
dokumenty/organizacje/casi/faktura.pdf
```

For S3, the physical object key also includes:

- optional `INVOICE_S3_PREFIX`,
- artifact root such as `dokumenty`, `ocr`, `wiedza`, or `tablica`,
- the existing logical storage key.

Example:

```text
INVOICE_S3_PREFIX=casi/prod
artifact=document
storage_key=organizacje/casi/faktura.pdf

object_key=casi/prod/dokumenty/organizacje/casi/faktura.pdf
```

If an older logical key already starts with the artifact root, such as `dokumenty/...`, the S3 object key does not duplicate that root. `INVOICE_S3_PREFIX` is used only for the physical object key in the bucket and is not stored in the logical `storage_key`.

## Required Environment Variables

```text
INVOICE_STORAGE_BACKEND=s3
INVOICE_S3_ENDPOINT_URL=https://fra1.digitaloceanspaces.com
INVOICE_S3_REGION=fra1
INVOICE_S3_BUCKET=casi-private
INVOICE_S3_ACCESS_KEY_ID=...
INVOICE_S3_SECRET_ACCESS_KEY=...
INVOICE_S3_PREFIX=casi/prod
```

Optional:

```text
INVOICE_S3_PUBLIC_BASE_URL=
```

`INVOICE_S3_PUBLIC_BASE_URL` is reserved for future controlled use. It is not used as a default way to bypass backend permissions.

## DigitalOcean Spaces Example

```text
INVOICE_STORAGE_BACKEND=s3
INVOICE_S3_ENDPOINT_URL=https://fra1.digitaloceanspaces.com
INVOICE_S3_REGION=fra1
INVOICE_S3_BUCKET=casi-private
INVOICE_S3_ACCESS_KEY_ID=<spaces-access-key>
INVOICE_S3_SECRET_ACCESS_KEY=<spaces-secret-key>
INVOICE_S3_PREFIX=casi/prod
```

The bucket for CASI documents, invoices, OCR output, and client files should be private.

## Reczny test integracyjny DigitalOcean Spaces

Repozytorium zawiera osobny, recznie uruchamiany test dla prywatnego bucketa DigitalOcean Spaces / S3-compatible storage:

```powershell
python scripts/check_s3_storage.py
```

Ten test nie jest czescia domyslnego profilu:

```powershell
python run_quality_checks.py --profile smoke
```

Mozna go uruchomic rowniez przez osobny profil quality check:

```powershell
python run_quality_checks.py --profile s3-integration
```

Wymagane zmienne srodowiskowe dla testu:

```powershell
$env:INVOICE_STORAGE_BACKEND="s3"
$env:INVOICE_S3_ENDPOINT_URL="https://fra1.digitaloceanspaces.com"
$env:INVOICE_S3_REGION="fra1"
$env:INVOICE_S3_BUCKET="<private-test-bucket>"
$env:INVOICE_S3_ACCESS_KEY_ID="<spaces-access-key>"
$env:INVOICE_S3_SECRET_ACCESS_KEY="<spaces-secret-key>"
$env:INVOICE_S3_PREFIX="casi/dev-test"
```

Zalecany prefiks testowy to:

```text
casi/dev-test
```

Skrypt tworzy sztuczny plik testowy pod logicznym kluczem w stylu:

```text
testy/storage-smoke/<timestamp>-<uuid>.txt
```

Nastepnie zapisuje go przez `S3StorageService`, pobiera przez ten sam kontrakt, porownuje tresc, sprawdza blad dla brakujacego obiektu i probuje usunac testowy obiekt z bucketa. Nie uzywa prawdziwych faktur, dokumentow klientow ani danych OCR.

Skrypt odmawia uruchomienia, jesli:

- `INVOICE_STORAGE_BACKEND` nie jest ustawione na `s3`,
- brakuje wymaganych zmiennych S3,
- `INVOICE_S3_PREFIX` wyglada produkcyjnie, np. `casi/prod`.

Test prefiksu produkcyjnego mozna wymusic tylko swiadomie:

```powershell
$env:INVOICE_ALLOW_S3_PROD_PREFIX_TEST="1"
```

Nie jest to zalecane dla zwyklego testu przygotowawczego. Bezpieczniejszy jest oddzielny prefiks testowy, np. `casi/dev-test`.

Skrypt nie wypisuje sekretow do konsoli i nie zapisuje sekretow w repozytorium. Bucket uzywany do dokumentow, faktur, OCR i plikow klientow powinien pozostac prywatny, a backend powinien kontrolowac dostep do plikow. Ten test nie wykonuje migracji danych z `data/magazyn` i nie jest deployem aplikacji.

## Dry-run plan migracji lokalnego storage

Przed prawdziwa migracja plikow do DigitalOcean Spaces mozna wygenerowac lokalny plan migracji:

```powershell
python scripts/plan_storage_migration.py
```

Skrypt domyslnie skanuje lokalny storage `data/magazyn` i zapisuje raporty:

```text
reports/storage_migration_plan.json
reports/storage_migration_plan.md
```

To jest tylko dry-run / raport. Skrypt:

- nie laczy sie z DigitalOcean,
- nie wymaga sekretow,
- nie wysyla plikow do S3,
- nie usuwa ani nie przenosi lokalnych plikow,
- nie zmienia storage keys w bazie.

Logiczny `storage_key` w raporcie nie zawiera `INVOICE_S3_PREFIX`. Planowany techniczny `s3_object_key` jest pokazany osobno w formacie:

```text
<prefix>/<storage_key>
```

Jesli prefix nie jest ustawiony, raport przyjmuje bezpieczna wartosc domyslna:

```text
casi/dev-test
```

Osobny profil quality check:

```powershell
python run_quality_checks.py --profile storage-migration-plan
```

Szczegoly: `docs/STORAGE_MIGRATION_PLAN.md`.

Raport rozdziela problemy wedlug severity: `info`, `warning`, `error`, `blocker`. Informacyjne duplikaty SHA256 nie blokuja migracji, jezeli docelowe storage keys sa unikalne. Konflikt `storage_key` albo sciezka z `..` sa blockerami.

Markdown raportu ukrywa pelny lokalny `storage_root` i pokazuje sciezki wzgledne, zeby nie publikowac prywatnych sciezek typu `C:\Users\...`.

## Access Control

The backend remains responsible for file access control.

Routes such as:

```text
/pliki/dokumenty/...
/pliki/ocr/...
/pliki/wiedza/...
/pliki/tablica/...
```

still check the authenticated user and organization path before returning a file. In `s3` mode, the backend reads the object and streams the bytes back to the caller after that permission check. This avoids exposing invoices, OCR, or customer documents through public object URLs.

Storage errors returned to HTTP callers are intentionally generic. Responses should not expose local filesystem paths, bucket names, endpoints, or credentials.

## App Platform Warning

DigitalOcean App Platform does not provide persistent local filesystem storage for application containers. Do not treat `data/magazyn` inside App Platform as durable storage.

Use:

- DigitalOcean Managed PostgreSQL for database state,
- DigitalOcean Spaces or another S3-compatible object storage for files.

## What This Stage Does Not Do

This stage does not:

- deploy the application to DigitalOcean,
- migrate existing files from `data/magazyn` to Spaces,
- create a DigitalOcean Spaces bucket,
- test against a real DigitalOcean bucket,
- migrate production SQLite data to PostgreSQL,
- redesign or change the frontend.

Folder-based knowledge sync still scans a local folder. It can remain useful for local development, but a production-grade App Platform setup should use uploads or a future object-storage-aware import flow instead of relying on persistent local folders.

Other known local-filesystem dependencies that remain by design at this stage:

- `KNOWLEDGE_DIR` is used by folder-based knowledge sync and local sandbox seed folder examples.
- `DOCUMENTS_DIR` and `OCR_DIR` are still referenced by legacy/local tests that assert physical files exist in local mode.
- `STORAGE_ROOT`, `BACKUPS_DIR`, and local directory creation remain for local development and for non-App-Platform environments.
- temporary files used by OCR are still local process temp files, which is acceptable because they are not durable storage.

The main backend file-serving path no longer requires `resolve_local_path()`; it reads through the shared storage contract after authorization.
