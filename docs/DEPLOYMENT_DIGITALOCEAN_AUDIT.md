# Audyt wdrozenia CASI Workspace na DigitalOcean

Data audytu: 2026-05-14  
Zakres: analiza przygotowania CASI Workspace do wdrozenia na DigitalOcean App Platform, DigitalOcean Managed PostgreSQL i DigitalOcean Spaces / S3-compatible object storage.  
Status: dokument planistyczny. Nie zmienia logiki biznesowej ani kodu aplikacji.

Aktualna checklist gotowosci do przyszlego prototypu znajduje sie w `docs/DIGITALOCEAN_PROTOTYPE_READINESS.md`. Praktyczny runbook przyszlego App Platform prototypu znajduje sie w `docs/DIGITALOCEAN_APP_PLATFORM_RUNBOOK.md`. Ten starszy audyt zachowuje historie decyzji; w razie roznic statusowych traktuj dokument readiness i runbook jako aktualny obraz przygotowania prototypu.

## Zrodla w repozytorium

- `Procfile` - obecna komenda produkcyjna zgodna z Railway.
- `railway.json` - konfiguracja deployu Railway.
- `run.py` - glowny punkt startowy backendu, tryby `standalone`, `web`, `worker`.
- `app/config.py` - konfiguracja env, baza danych, storage lokalny, legacy static.
- `app/db.py` - obsluga SQLite/PostgreSQL i inicjalizacja schematu.
- `migrate_sqlite_to_configured_db.py` - migracja danych z SQLite do aktualnie skonfigurowanej bazy.
- `app/services/storage_service.py` - obecna abstrakcja storage i implementacje `LocalStorageService` oraz `S3StorageService`.
- `app/bootstrap.py` - skladanie serwisow; aktualnie wybiera storage przez `INVOICE_STORAGE_BACKEND=local|s3`.
- `app/api/http_server.py` - endpoint `/health`, legacy static, trasy plikow `/pliki/...`.
- `frontend/` - docelowy frontend Next.js/React.
- `static/` - legacy frontend utrzymywany tymczasowo dla kompatybilnosci.
- `run_quality_checks.py` - profile testow `smoke`, `predeploy`, `full`.
- `README.md`, `ARCHITECTURE.md`, `AGENTS.md` - zasady architektury, wdrozenia i frontend source of truth.

## Zrodla DigitalOcean

- App Platform App Spec: https://docs.digitalocean.com/products/app-platform/reference/app-spec/
- App Platform storage limits: https://docs.digitalocean.com/products/app-platform/details/limits/
- App Platform data storage: https://docs.digitalocean.com/products/app-platform/how-to/store-data/
- App Platform health checks: https://docs.digitalocean.com/products/app-platform/how-to/manage-health-checks/
- DigitalOcean Spaces: https://www.digitalocean.com/products/object-storage

## A. Aktualny stan wdrozenia

Backend startuje lokalnie przez:

```bash
python run.py
python run.py --mode standalone
python run.py --mode web
python run.py --mode worker
```

`run.py` domyslnie uzywa `--host 127.0.0.1`, `--port 8000` i `--mode standalone`. W trybie `standalone` uruchamia HTTP oraz petle tla: email scheduler, przypomnienia i pipeline bazy wiedzy.

Konfiguracja produkcyjna Railway jest bardzo prosta:

```bash
python run.py --mode standalone --host 0.0.0.0 --port $PORT
```

Ta komenda wystepuje w `Procfile` i `railway.json`. To jest dobry punkt wyjscia dla DigitalOcean App Platform, bo aplikacja potrafi sluchac na `0.0.0.0` i uzyc portu z env.

Health endpoint istnieje w `app/api/http_server.py`:

```text
GET /health -> {"ok": true}
```

Obecny backend moze nadal serwowac legacy frontend z `static/`, jesli `CASI_SERVE_LEGACY_STATIC` jest wlaczone. `README.md`, `ARCHITECTURE.md` i `AGENTS.md` jasno wskazuja jednak, ze docelowym frontendem produkcyjnym jest `frontend/`, a `static/` to warstwa legacy.

## B. Co jest zalezne od Railway

Zaleznosci jawne:

- `railway.json` zawiera builder `RAILPACK`, start command, healthcheck `/health`, retry policy.
- `Procfile` ma start command dla Railway-like runtime.
- `app/config.py` czyta `RAILWAY_VOLUME_MOUNT_PATH` i uzywa go jako domyslnego miejsca dla SQLite oraz `data/magazyn`, jesli zmienna istnieje.
- `app/config.py` czyta `RAILWAY_GIT_COMMIT_SHA` jako fallback dla `INVOICE_APP_RELEASE_ID`.
- `README.md` ma osobna sekcje `Railway` z przykladowymi env, w tym `RAILWAY_VOLUME_MOUNT_PATH=/data`.

To nie blokuje DigitalOcean. Nalezy jednak traktowac Railway jako legacy/fallback i nie usuwac konfiguracji od razu. Najbezpieczniej dopisac pozniej dokumentacje, ze `railway.json` zostaje tymczasowo jako fallback, a nowym kanonicznym kierunkiem deployu jest DigitalOcean.

## C. Co blokuje wdrozenie na DigitalOcean

Current status 2026-06-02: ponizszy blok zachowuje historyczny kontekst sprzed dodania `INVOICE_STORAGE_BACKEND=local|s3`. `app/bootstrap.py` wybiera juz storage backend przez env, a `S3StorageService` istnieje. Nadal aktualne pozostaje ryzyko, ze App Platform nie moze byc traktowana jako trwaly lokalny filesystem, a realny test prywatnego Spaces nie zostal jeszcze wykonany. Aktualna checklist znajduje sie w `docs/DIGITALOCEAN_PROTOTYPE_READINESS.md`.

Najwiekszy realny blokujacy temat to persistent storage plikow.

DigitalOcean App Platform nie zapewnia trwalego lokalnego filesystemu i nie wspiera wolumenow dla aplikacji. Lokalny filesystem kontenera jest efemeryczny i powinien sluzyc tylko do danych tymczasowych. To ma bezposredni konflikt z obecnym `LocalStorageService`, ktory zapisuje dokumenty, OCR, wiedze i pliki tablicy na dysk lokalny.

Blokery lub ryzyka przed produkcyjnym wdrozeniem:

- Historyczne, superseded: `app/bootstrap.py` zawsze tworzy `LocalStorageService()`, bez wyboru backendu storage przez env. Aktualnie wybiera `local|s3`.
- Historyczne, superseded: `app/services/storage_service.py` ma protokol `StorageService`, ale tylko lokalna implementacje. Aktualnie istnieje tez `S3StorageService`.
- `app/api/http_server.py` pobiera pliki przez `resolve_local_path()` i `read_bytes()`, wiec zaklada lokalny plik przy serwowaniu `/pliki/...`.
- `app/services/knowledge_service.py` ma miejsca zalezne od lokalnej sciezki, np. `file_path.relative_to(KNOWLEDGE_DIR)` oraz `resolve_local_path("knowledge", storage_key)`.
- `app/demo_seed.py` pisze do `KNOWLEDGE_DIR`, co w produkcji z object storage powinno byc ograniczone lub zaadaptowane.
- Jesli wdrozymy backend na App Platform bez zmiany storage, uploady i pliki beda nietrwale po deployu/restartach.

Nie jest to blokada calej migracji, ale jest blokada dla bezpiecznej produkcji.

## D. Co trzeba zmienic dla DigitalOcean App Platform

Minimalnie dla backendu:

- dodac `.do/app.yaml` albo przygotowac najpierw dokument `DEPLOYMENT_DIGITALOCEAN.md` z reczna konfiguracja App Platform;
- ustawic backend service z komenda:

```bash
python run.py --mode standalone --host 0.0.0.0 --port $PORT
```

- ustawic health check na `/health`;
- ustawic env produkcyjne, w szczegolnosci `INVOICE_DB_ENGINE=postgresql`, `DATABASE_URL` lub `INVOICE_DATABASE_URL`, `INVOICE_SECURE_COOKIES=1`, `INVOICE_ENABLE_DEMO_SEED=0`;
- nie polegac na lokalnym `data/` w App Platform;
- ustalic, czy background loop zostaje w `standalone`, czy pozniej rozdzielamy `web` i `worker`.

Rekomendacja dla struktury komponentow:

- Etap 1: backend jako jeden service, z legacy static tylko jako fallback, bez traktowania `static/` jako finalnego UI.
- Etap 2: frontend Next.js jako osobny service w tym samym App Platform app, z rootem `frontend/`.
- Etap 3: backend API i frontend jako dwa komponenty z jasnymi trasami/domenami; frontend korzysta z `CASI_API_BASE_URL` albo wewnetrznego/publicznego adresu backendu.

Obecna struktura repo nadaje sie do App Platform, ale raczej jako multi-component app:

- backend Python z rootu repo,
- frontend Next.js z `frontend/`.

Nie rekomenduje laczenia migracji infrastruktury z redesignem frontendu. `frontend/` powinien pozostac source of truth, a `static/` zostac legacy/fallback do czasu pelnego przelaczenia ruchu.

## E. Co trzeba zmienic dla PostgreSQL

Stan obecny jest obiecujacy:

- `requirements.txt` zawiera `psycopg[binary]>=3.2,<4`.
- `app/config.py` domyslnie ustawia `INVOICE_DB_ENGINE` na `postgresql`.
- `app/config.py` czyta `INVOICE_DATABASE_URL` albo `DATABASE_URL`.
- `app/db.py` ma osobne `SQLITE_SCHEMA` i `POSTGRES_SCHEMA`.
- `app/db.py` otwiera PostgreSQL przez `psycopg` albo `psycopg2`.
- `initialize_database()` ma retry env: `INVOICE_DB_INIT_MAX_RETRIES`, `INVOICE_DB_INIT_RETRY_SLEEP_SECONDS`.
- `migrate_sqlite_to_configured_db.py` istnieje i przenosi wybrane tabele z SQLite do skonfigurowanej bazy.

Do sprawdzenia przed produkcja:

- migrator `migrate_sqlite_to_configured_db.py` przenosi tylko wybrane tabele z `TABLE_ORDER`; obecna baza ma wiecej tabel niz lista w migratorze, np. zadania, billing, wiedza, whiteboard, komentarze, importy, OAuth, ustawienia systemowe. To oznacza, ze migracja danych produkcyjnych nie jest jeszcze kompletna.
- Testy domyslnie wymuszaja SQLite w `run_quality_checks.py`, wiec przed finalnym deployem warto dodac lub uruchomic osobny smoke test PostgreSQL.
- Nalezy potwierdzic zgodnosc wszystkich repozytoriow z PostgreSQL, zwlaszcza zapytan z `?`, konwersji bool/int i operacji na datach. `DatabaseConnection._translate_query()` pomaga, ale to nie zastepuje testu na prawdziwym PostgreSQL.

Minimalny plan PostgreSQL:

1. Utworzyc DigitalOcean Managed PostgreSQL.
2. Ustawic `INVOICE_DB_ENGINE=postgresql`.
3. Ustawic `DATABASE_URL` albo `INVOICE_DATABASE_URL`.
4. Uruchomic aplikacje na pustej bazie i sprawdzic `initialize_database()`.
5. Dodac/uruchomic smoke test z prawdziwym PostgreSQL przed migracja danych.
6. Dopiero potem migrowac dane z SQLite, rozszerzajac migrator, jesli trzeba przeniesc wiecej niz podstawowe tabele.

## F. Co trzeba zmienic dla DigitalOcean Spaces / S3-compatible storage

Obecny storage:

- `app/config.py` definiuje `STORAGE_ROOT` oraz katalogi:
  - `DOCUMENTS_DIR = STORAGE_ROOT / "dokumenty"`
  - `OCR_DIR = STORAGE_ROOT / "ocr"`
  - `KNOWLEDGE_DIR = STORAGE_ROOT / "wiedza"`
  - `WHITEBOARD_DIR = STORAGE_ROOT / "tablica"`
  - `BACKUPS_DIR = STORAGE_ROOT / "backup"`
- Jesli `RAILWAY_VOLUME_MOUNT_PATH` istnieje, domyslny storage idzie pod ten katalog.
- W przeciwnym razie storage idzie do `data/magazyn`.
- `data/magazyn` ma obecnie podkatalogi `dokumenty`, `ocr`, `wiedza`, `tablica`, `backup` oraz strukture `organizacje/<slug>`.

Obecny kod ma dobra podstawe, bo istnieje protokol `StorageService`. Brakuje jednak adaptera object storage.

Minimalna zmiana architektoniczna:

- dodac konfiguracje `INVOICE_STORAGE_BACKEND=local|s3`;
- dodac adapter `S3StorageService` / `ObjectStorageService` implementujacy obecny `StorageService`;
- w `app/bootstrap.py` wybierac storage backend przez env;
- dodac env dla S3-compatible storage:
  - `INVOICE_STORAGE_BACKEND=s3`
  - `INVOICE_S3_ENDPOINT_URL`
  - `INVOICE_S3_REGION`
  - `INVOICE_S3_BUCKET`
  - `INVOICE_S3_ACCESS_KEY_ID`
  - `INVOICE_S3_SECRET_ACCESS_KEY`
  - opcjonalnie `INVOICE_S3_PUBLIC_BASE_URL`
  - opcjonalnie `INVOICE_S3_PREFIX`
- zmienic serwowanie `/pliki/...`, bo obecnie `app/api/http_server.py` czyta lokalny plik przez `resolve_local_path()`.

Najbezpieczniejszy model pobierania plikow:

- prywatne obiekty w Spaces,
- backend sprawdza uprawnienia tak jak dzisiaj w `_can_access_storage_path()`,
- backend generuje signed URL albo streamuje plik z object storage,
- link publiczny nie powinien omijac kontroli organizacji, jesli plik zawiera dane klienta.

Wazna uwaga: samo wrzucenie plikow do publicznego bucketa byloby zbyt ryzykowne dla faktur, OCR i dokumentow organizacji.

## G. Wymagane zmienne srodowiskowe

Minimum produkcyjne:

```text
INVOICE_DB_ENGINE=postgresql
DATABASE_URL=...
# albo
INVOICE_DATABASE_URL=...

INVOICE_DEFAULT_ADMIN_LOGIN=...
INVOICE_DEFAULT_ADMIN_PASSWORD=...
INVOICE_SECURE_COOKIES=1
INVOICE_ENABLE_DEMO_SEED=0
INVOICE_ENABLE_TEST_IMPORTS=0
INVOICE_SHOW_DEFAULT_LOGIN_HINT=0
INVOICE_PUBLIC_BASE_URL=https://...
INVOICE_APP_RELEASE_ID=...
CASI_SERVE_LEGACY_STATIC=1
```

Zmienne bazy / startu:

```text
PORT=<ustawiane przez App Platform>
INVOICE_DB_CONNECT_TIMEOUT_SECONDS=10
INVOICE_DB_INIT_MAX_RETRIES=6
INVOICE_DB_INIT_RETRY_SLEEP_SECONDS=2
```

Docelowe zmienne storage S3/Spaces, do dodania w implementacji:

```text
INVOICE_STORAGE_BACKEND=s3
INVOICE_S3_ENDPOINT_URL=https://<region>.digitaloceanspaces.com
INVOICE_S3_REGION=<region>
INVOICE_S3_BUCKET=<bucket>
INVOICE_S3_ACCESS_KEY_ID=...
INVOICE_S3_SECRET_ACCESS_KEY=...
INVOICE_S3_PREFIX=casi
INVOICE_S3_PUBLIC_BASE_URL=
```

Zmienne integracji opcjonalne:

```text
INVOICE_EMAIL_IMAP_HOST=...
INVOICE_EMAIL_IMAP_PORT=993
INVOICE_EMAIL_IMAP_USERNAME=...
INVOICE_EMAIL_IMAP_PASSWORD=...
INVOICE_EMAIL_IMAP_FOLDER=INBOX
INVOICE_EMAIL_IMAP_USE_SSL=1
INVOICE_EMAIL_FETCH_LIMIT=100
INVOICE_EMAIL_AUTOCHECK_ENABLED=0
INVOICE_EMAIL_AUTOCHECK_SECONDS=300

INVOICE_GOOGLE_CLIENT_ID=...
INVOICE_GOOGLE_CLIENT_SECRET=...
INVOICE_EMAIL_GOOGLE_CLIENT_ID=...
INVOICE_EMAIL_GOOGLE_CLIENT_SECRET=...

INVOICE_TELEGRAM_BOT_TOKEN=...
INVOICE_TELEGRAM_WEBHOOK_SECRET=...
INVOICE_SLACK_BOT_TOKEN=...
INVOICE_SLACK_SIGNING_SECRET=...

INVOICE_OCR_LANGUAGE=pol+eng
INVOICE_TESSERACT_CMD=...

INVOICE_ENABLE_TELEGRAM_TASK_REMINDERS=1
INVOICE_TASK_REMINDER_POLL_SECONDS=60
INVOICE_TASK_REMINDER_WORKER_POLL_SECONDS=15
INVOICE_TASK_REMINDER_RETRY_MINUTES=15
INVOICE_TASK_REMINDER_PROCESSING_TIMEOUT_MINUTES=10
INVOICE_TASK_REMINDER_MAX_ATTEMPTS=5

INVOICE_KNOWLEDGE_PIPELINE_POLL_SECONDS=20
INVOICE_KNOWLEDGE_FOLDER_SCAN_SECONDS=120
```

Frontend:

```text
CASI_API_BASE_URL=https://<backend-url>
```

Legacy/Railway fallback, nie jako docelowy DigitalOcean setup:

```text
RAILWAY_VOLUME_MOUNT_PATH=/data
RAILWAY_GIT_COMMIT_SHA=...
```

## H. Minimalny bezpieczny plan migracji krok po kroku

1. Zachowac `railway.json` i `Procfile` jako fallback, oznaczajac w dokumentacji Railway jako legacy/deprecated.
2. Przygotowac `DEPLOYMENT_DIGITALOCEAN.md` z recznym runbookiem albo `.do/app.yaml` dla App Platform.
3. Utworzyc DigitalOcean Managed PostgreSQL.
4. Uruchomic backend na DigitalOcean App Platform na pustej PostgreSQL, z `INVOICE_ENABLE_DEMO_SEED=0`, `INVOICE_SECURE_COOKIES=1`, health check `/health`.
5. Dodac test/smoke dla PostgreSQL albo uruchomic istniejace testy na tymczasowej bazie PostgreSQL.
6. Wprowadzic adapter S3-compatible storage za obecnym `StorageService`.
7. Zmienic serwowanie `/pliki/...`, aby dzialalo z object storage po sprawdzeniu uprawnien.
8. Utworzyc DigitalOcean Spaces bucket z prywatnym dostepem i kluczami ograniczonymi do bucketa.
9. Przetestowac upload, pobieranie dokumentu, OCR, wiedze firmowa, tablice i zalaczniki z object storage.
10. Rozszerzyc migrator danych, jesli trzeba przeniesc komplet danych, nie tylko tabele z obecnego `TABLE_ORDER`.
11. Przeniesc dane SQLite do PostgreSQL.
12. Przeniesc `data/magazyn` do Spaces z zachowaniem kluczy odpowiadajacych obecnym storage keys.
13. Uruchomic smoke/predeploy:
    - `python run_quality_checks.py --profile smoke`
    - `python run_quality_checks.py --profile predeploy`
    - frontend: `npm.cmd run typecheck`, `npm.cmd run build` w `frontend/`
14. Wdrozyc backend i frontend jako komponenty App Platform.
15. Ustawic `INVOICE_PUBLIC_BASE_URL` na finalny HTTPS.
16. Porownac lokalne i zdalne srodowisko przez `compare_environment_parity.py`.
17. Dopiero po stabilizacji przelaczyc ruch produkcyjny.

## I. Ryzyka techniczne

- Utrata plikow: najwieksze ryzyko, jesli App Platform zostanie uruchomione z lokalnym `data/magazyn`.
- Niepelna migracja danych: `migrate_sqlite_to_configured_db.py` nie obejmuje wszystkich tabel obecnej aplikacji.
- Uprawnienia do plikow: object storage musi zachowac kontrole organizacji; publiczne linki do faktur/OCR moga ujawnic dane klientow.
- Background loops w jednym procesie: `standalone` jest proste, ale przy skalowaniu poziomym moze uruchomic kilka schedulerow naraz. Docelowo warto rozdzielic `web` i `worker` albo dodac blokady/koordynacje.
- Frontend/backend routing: `frontend/next.config.js` zaklada `CASI_API_BASE_URL`; przy App Platform trzeba jasno ustawic URL backendu albo routing komponentow.
- Tesseract/OCR: lokalny `INVOICE_TESSERACT_CMD` nie przenosi sie automatycznie na App Platform; OCR skanow moze wymagac pakietu systemowego, kontenera albo uslugi zewnetrznej.
- Sekrety: `.env.local` jest lokalny i nie moze byc zrodlem konfiguracji produkcyjnej; sekrety musza trafic do env DigitalOcean.
- Legacy static: backend nadal moze serwowac `static/`; nie nalezy tego mylic z finalnym frontendem.
- Brak `doctl`/automatyzacji deployu w repo: obecnie nie ma `.do/app.yaml`, wiec deploy trzeba opisac albo dodac spec.

## J. Rekomendacja

Nie rekomenduje od razu robic finalnego produkcyjnego przelaczenia tylko przez skopiowanie konfiguracji Railway na DigitalOcean.

Najrozsadniejsza kolejnosc:

1. Najpierw przygotowac DigitalOcean PostgreSQL i uruchomic backend na pustej bazie jako techniczny smoke test.
2. Rownolegle zaprojektowac i dodac adapter S3-compatible storage za istniejacym `StorageService`.
3. Dopiero po storage i bazie robic migracje danych i plikow.
4. Frontend wdrazac jako osobny komponent Next.js w `frontend/`, bez ruszania `static/` poza utrzymaniem fallbacku.

Krotka odpowiedz decyzyjna:

- Aktualny backend mozna wdrozyc testowo na App Platform szybko.
- Produkcyjnie trzeba najpierw uporzadkowac storage i potwierdzic PostgreSQL.
- Najwieksza praca to nie DigitalOcean jako taki, tylko bezpieczne przejscie z lokalnego filesystemu na object storage bez naruszenia dostepu do faktur, OCR i dokumentow organizacji.

## Czy potrzebny jest `.do/app.yaml`

Tak, ale najlepiej po decyzji o strukturze komponentow.

Opcje:

- Najpierw `docs/DEPLOYMENT_DIGITALOCEAN.md` jako runbook bez ryzyka zbyt wczesnego zamrozenia konfiguracji.
- Potem `.do/app.yaml`, gdy ustalimy:
  - czy backend i frontend sa dwoma komponentami w jednej App Platform app,
  - czy worker jest osobnym komponentem,
  - jakie sa finalne nazwy env i routingu,
  - czy storage S3 jest juz zaimplementowany.

Nie trzeba usuwac `railway.json`. Bezpieczniej zostawic go jako fallback do czasu udanego wdrozenia na DigitalOcean.

## Aktualizacja 2026-05-14: etap storage

Przygotowano techniczna warstwe storage pod DigitalOcean Spaces / S3-compatible object storage:

- dodano wybor backendu przez `INVOICE_STORAGE_BACKEND=local|s3`;
- `local` pozostaje domyslnym trybem developerskim;
- dodano adapter `S3StorageService` za istniejacym kontraktem `StorageService`;
- dodano konfiguracje `INVOICE_S3_ENDPOINT_URL`, `INVOICE_S3_REGION`, `INVOICE_S3_BUCKET`, `INVOICE_S3_ACCESS_KEY_ID`, `INVOICE_S3_SECRET_ACCESS_KEY`, `INVOICE_S3_PREFIX`;
- trasy `/pliki/...` nadal sprawdzaja uprawnienia backendu przed wydaniem pliku i nie uzywaja publicznych URL-i jako obejscia kontroli dostepu;
- `INVOICE_S3_PREFIX` jest uzywany tylko jako techniczny prefiks obiektu w buckecie, nie jako czesc logicznego `storage_key`;
- glowny profil `smoke` zostal oddzielony od legacy static compatibility check, poniewaz `static/` jest warstwa fallback, a nie docelowym frontendem produkcyjnym;
- legacy static compatibility check jest dostepny jako `python run_quality_checks.py --profile legacy-static`; obecnie sygnalizuje rozjazd `static/index.html` z dawnym oczekiwaniem testu na `default-login-hint`;
- szczegoly konfiguracji opisuje `docs/STORAGE_BACKEND.md`.

Nadal pozostaje do zrobienia przed produkcyjnym deployem:

- utworzenie prywatnego bucketa DigitalOcean Spaces;
- test na prawdziwym buckecie i prawdziwych kluczach ustawionych w env, bez zapisywania sekretow w repo;
- migracja istniejacych plikow z `data/magazyn` do Spaces z zachowaniem storage keys;
- decyzja, czy folder-based knowledge sync ma pozostac tylko lokalny, czy dostac osobny object-storage-aware import flow;
- naprawa albo swiadome utrzymanie osobnego legacy static compatibility check dla `static/index.html`;
- test PostgreSQL na DigitalOcean Managed PostgreSQL;
- finalny runbook albo `.do/app.yaml`.

## Aktualizacja 2026-05-14: reczny test Spaces

Przygotowano kontrolowany, recznie uruchamiany test integracyjny dla prywatnego bucketa DigitalOcean Spaces / S3-compatible storage:

- `scripts/check_s3_storage.py` zapisuje sztuczny plik testowy przez `S3StorageService`, pobiera go, porownuje tresc, sprawdza brakujacy obiekt i probuje usunac obiekt testowy;
- test wymaga `INVOICE_STORAGE_BACKEND=s3` oraz kompletu zmiennych `INVOICE_S3_*`;
- zalecany prefiks testowy to `casi/dev-test`;
- skrypt blokuje prefiksy wygladajace produkcyjnie, np. `casi/prod`, chyba ze swiadomie ustawiono `INVOICE_ALLOW_S3_PROD_PREFIX_TEST=1`;
- test nie jest czescia domyslnego `smoke` i mozna go uruchomic osobno przez `python run_quality_checks.py --profile s3-integration`;
- test nie wykonuje deploya, nie migruje danych i nie uzywa prawdziwych faktur, OCR ani dokumentow klientow.

Po pozytywnym tescie na prawdziwym prywatnym buckecie nadal pozostaje osobny etap migracji plikow z `data/magazyn` do Spaces oraz testy z DigitalOcean Managed PostgreSQL przed produkcyjnym deployem.

## H. Lokalny audyt migracji SQLite -> PostgreSQL

Dodano osobny, lokalny audyt gotowosci migracji bazy:

```powershell
python run_quality_checks.py --profile database-migration-audit
```

Audyt uruchamia `scripts/audit_database_migration.py`, porownuje tabele SQLite/PostgreSQL z `app/db.py` z lista `TABLE_ORDER` w `migrate_sqlite_to_configured_db.py` i zapisuje lokalne raporty w `reports/database_migration_audit.*`.

To nie jest migracja danych, nie laczy sie z DigitalOcean Managed PostgreSQL i nie wymaga sekretow. Aktualny wynik wskazuje, ze migrator obejmuje tylko waski zestaw tabel i musi zostac rozszerzony przed pelna migracja danych na PostgreSQL.

### Aktualizacja migratora: organization access core

Pierwszy maly pakiet rozszerzenia migratora SQLite -> PostgreSQL obejmuje tylko tabele dostepu organizacyjnego:

- `organization_memberships`,
- `organization_modules`,
- `user_capabilities`,
- `system_settings`.

Po tym kroku migrator obejmuje 11 tabel, a lokalny audyt pokazuje 56 tabel nadal poza migratorem oraz 45 blockerow dla pelnej migracji danych. To nadal nie oznacza gotowosci do produkcyjnej migracji PostgreSQL; kolejnym bezpiecznym pakietem powinny byc tabele zadan i workflow.

### Aktualizacja migratora: tasks and workflow core

Drugi maly pakiet rozszerzenia migratora SQLite -> PostgreSQL obejmuje rdzen zadan i workflow:

- `user_calendars` jako minimalna zaleznosc `tasks.calendar_id`,
- `tasks`,
- `task_visibility_users`,
- `task_links`,
- `task_notes`,
- `task_checklist_items`,
- `task_templates`,
- `approval_requests`,
- `task_attachments`,
- `task_history`,
- `work_items`,
- `work_item_history`.

Po tym kroku migrator obejmuje 23 tabele, a lokalny audyt pokazuje 44 tabele nadal poza migratorem oraz 33 blockery dla pelnej migracji danych. To nadal nie oznacza gotowosci do produkcyjnej migracji PostgreSQL; kolejnym bezpiecznym pakietem powinny byc tabele obiegu faktur poza bazowa tabela `invoices`.

### Aktualizacja migratora: invoice operations core

Trzeci maly pakiet rozszerzenia migratora SQLite -> PostgreSQL obejmuje operacyjny obieg faktur poza bazowa tabela `invoices`:

- `invoice_comments`,
- `invoice_handoff_batches`,
- `invoice_handoff_batch_items`,
- `invoice_ksef_field_overrides`.

Po tym kroku migrator obejmuje 27 tabel, a lokalny audyt pokazuje 40 tabel nadal poza migratorem oraz 29 blockerow dla pelnej migracji danych. To nadal nie oznacza gotowosci do produkcyjnej migracji PostgreSQL; kolejnym bezpiecznym pakietem powinny byc tabele billing/rozliczenia core po osobnym sprawdzeniu zaleznosci.

### Aktualizacja migratora: billing core

Kolejny kontrolowany pakiet rozszerzenia migratora SQLite -> PostgreSQL obejmuje billing/rozliczenia core:

- `billing_schools`,
- `billing_models`,
- `billing_payers`,
- `billing_students`,
- `billing_charge_batches`,
- `billing_charges`,
- `billing_student_charge_state`,
- `billing_payer_charge_state`,
- `billing_bank_accounts`,
- `billing_statement_imports`,
- `billing_transactions`,
- `billing_payment_matches`,
- `billing_payer_ledger_entries`.

Po tym kroku migrator obejmuje 40 tabel, a lokalny audyt pokazuje 27 tabel nadal poza migratorem oraz 16 blockerow dla pelnej migracji danych. To nadal nie oznacza gotowosci do produkcyjnej migracji PostgreSQL; kolejnym bezpiecznym pakietem powinien byc knowledge/document core albo intake/attachments, po osobnym sprawdzeniu zaleznosci.

### Aktualizacja migratora: knowledge/document core

Kolejny kontrolowany pakiet rozszerzenia migratora SQLite -> PostgreSQL obejmuje knowledge/document core:

- `knowledge_documents`,
- `knowledge_document_versions`,
- `knowledge_processing_jobs`,
- `knowledge_folder_watchers`,
- `knowledge_document_comments`.

Po tym kroku migrator obejmuje 45 tabel, a lokalny audyt pokazuje 22 tabele nadal poza migratorem oraz 12 blockerow dla pelnej migracji danych. To nadal nie oznacza gotowosci do produkcyjnej migracji PostgreSQL.

Ten pakiet migruje tylko rekordy bazodanowe i metadane dokumentow/wiedzy. Nie przenosi fizycznych plikow z `data/magazyn`, nie uruchamia S3/DigitalOcean Spaces i nie zastapuje osobnego planu migracji storage opisanego w `docs/STORAGE_MIGRATION_PLAN.md`.

Kolejnym bezpiecznym pakietem powinien byc intake/attachments core albo automation core, po osobnym sprawdzeniu zaleznosci i bez laczenia tego z realnym testem PostgreSQL lub DigitalOcean.

### Aktualizacja migratora: intake/attachments core

Kolejny kontrolowany pakiet rozszerzenia migratora SQLite -> PostgreSQL obejmuje intake/attachments core:

- `intake_forms`,
- `intake_items`,
- `intake_item_comments`,
- `intake_item_history`,
- `entity_attachments`.

Po tym kroku migrator obejmuje 50 tabel, a lokalny audyt pokazuje 17 tabel nadal poza migratorem oraz 7 blockerow dla pelnej migracji danych. To nadal nie oznacza gotowosci do produkcyjnej migracji PostgreSQL.

Ten pakiet migruje tylko rekordy bazodanowe formularzy, zgloszen, komentarzy, historii i metadanych zalacznikow. `entity_attachments` zawiera storage metadata, np. `file_link`, `file_storage_key` i `storage_backend`, ale fizyczne pliki nadal musza byc migrowane osobnym procesem storage. Ten etap nie uruchamia S3/DigitalOcean Spaces i nie zastapuje `docs/STORAGE_MIGRATION_PLAN.md`.

Kolejnym bezpiecznym pakietem powinien byc automation core albo calendar/integration core, po osobnym sprawdzeniu zaleznosci i bez laczenia tego z realnym testem PostgreSQL lub DigitalOcean.

### Aktualizacja migratora: automation core

Kolejny kontrolowany pakiet rozszerzenia migratora SQLite -> PostgreSQL obejmuje automation core:

- `automation_rules`,
- `automation_executions`.

Po tym kroku migrator obejmuje 52 tabele, a lokalny audyt pokazuje 15 tabel nadal poza migratorem oraz 5 blockerow dla pelnej migracji danych. To nadal nie oznacza gotowosci do produkcyjnej migracji PostgreSQL.

Ten pakiet migruje tylko rekordy bazodanowe definicji automatyzacji i historii wykonan. Nie zmienia logiki biznesowej automatyzacji, nie uruchamia automatyzacji i nie laczy sie z DigitalOcean, S3 ani PostgreSQL.

Kolejnym bezpiecznym pakietem powinien byc calendar/integration core albo osobny pakiet `saved_views` / whiteboard core, po sprawdzeniu zaleznosci i bez laczenia tego z realnym testem PostgreSQL lub DigitalOcean.

### Aktualizacja migratora: calendar/integration core

Kolejny kontrolowany pakiet rozszerzenia migratora SQLite -> PostgreSQL obejmuje calendar/integration core:

- `user_google_calendar_connections`,
- `user_calendar_assignments`,
- `system_email_google_connections`.

Po tym kroku migrator obejmuje 55 tabel, a lokalny audyt pokazuje 12 tabel nadal poza migratorem oraz 2 blockery dla pelnej migracji danych. To nadal nie oznacza gotowosci do produkcyjnej migracji PostgreSQL.

Ten pakiet migruje tylko rekordy bazodanowe przypisan kalendarzy i zapisanych polaczen integracyjnych. Tabele integracyjne moga zawierac wartosci wrazliwe, np. `access_token`, `refresh_token`, `google_email` i zakresy OAuth. Ten etap nie wykonuje migracji danych, nie laczy sie z Google API i nie loguje wartosci tokenow. Przyszla realna migracja tych tabel musi miec osobna kontrole sekretow/OAuth.

Kolejnym bezpiecznym pakietem powinien byc `saved_views` albo whiteboard core, po sprawdzeniu zaleznosci i bez laczenia tego z realnym testem PostgreSQL lub DigitalOcean.

### Aktualizacja migratora: whiteboard core

Kolejny kontrolowany pakiet rozszerzenia migratora SQLite -> PostgreSQL obejmuje whiteboard core:

- `organization_whiteboard_events`.

Po tym kroku migrator obejmuje 56 tabel, a lokalny audyt pokazuje 11 tabel nadal poza migratorem oraz 1 blocker dla pelnej migracji danych. To nadal nie oznacza gotowosci do produkcyjnej migracji PostgreSQL.

Ten pakiet migruje tylko rekordy bazodanowe zdarzen tablicy organizacji. `payload_json` jest przenoszony jako wartosc rekordu bez interpretowania albo zmiany logiki whiteboard.

Kolejnym bezpiecznym pakietem powinien byc `saved_views` jako UI/state core, po sprawdzeniu zaleznosci i bez laczenia tego z realnym testem PostgreSQL lub DigitalOcean.

### Aktualizacja migratora: ui/state core

Kolejny kontrolowany pakiet rozszerzenia migratora SQLite -> PostgreSQL obejmuje ui/state core:

- `saved_views`.

Po pozniejszym dodaniu backendowego fundamentu notatek CRM migrator obejmuje 58 tabel, a lokalny audyt pokazuje 10 tabel nadal poza migratorem oraz 0 blockerow dla pelnej migracji danych. To nadal nie oznacza gotowosci do produkcyjnej migracji PostgreSQL bez osobnego testu na prawdziwej bazie.

Ten pakiet migruje tylko rekordy bazodanowe zapisanych widokow i filtrow UI. `view_state_json` jest przenoszony jako wartosc rekordu bez interpretowania albo zmiany logiki UI.

Kolejnym bezpiecznym krokiem powinien byc pierwszy kontrolowany test migracji na tymczasowym PostgreSQL, bez produkcyjnego deploya, bez migracji plikow i bez laczenia z DigitalOcean. Osobny pakiet historii importow moze zostac wykonany pozniej, jesli przed produkcja chcemy zachowac pelna historie importow.

Kontrolny test techniczny jest opisany w `docs/POSTGRES_MIGRATION_TEST.md` i uruchamiany profilem `postgres-migration-check`. Test wymaga osobnego `CASI_TEST_POSTGRES_DATABASE_URL`, tworzy sztuczna SQLite i nie uzywa DigitalOcean, S3, `DATABASE_URL` ani `INVOICE_DATABASE_URL` jako domyslnego celu.
