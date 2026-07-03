# DigitalOcean Prototype Readiness

Status: kontrolny audyt lokalny po pracach nad storage, migracja plikow, migratorem SQLite -> PostgreSQL i lokalnym testem PostgreSQL.

Ten dokument nie jest runbookiem deploya i nie oznacza gotowosci produkcyjnej.

Praktyczny runbook przyszlego prototypu App Platform znajduje sie w `docs/DIGITALOCEAN_APP_PLATFORM_RUNBOOK.md`. Runbook opisuje kolejnosc i decyzje wdrozeniowe, ale nie wykonuje deploya i nie tworzy `.do/app.yaml`.

Ten etap:

- nie wykonuje deploya,
- nie laczy sie z DigitalOcean,
- nie laczy sie z PostgreSQL,
- nie laczy sie z S3 ani Spaces,
- nie migruje danych,
- nie migruje plikow,
- nie zmienia logiki biznesowej.

## A. Aktualny status

Co jest przygotowane:

- Backend ma punkt startowy `run.py` z trybami `standalone`, `web`, `worker`.
- `Procfile` i `railway.json` zawieraja start command: `python run.py --mode standalone --host 0.0.0.0 --port $PORT`.
- Backend ma healthcheck `GET /health`.
- Storage ma wybor `INVOICE_STORAGE_BACKEND=local|s3`.
- `LocalStorageService` i `S3StorageService` implementuja wspolny kontrakt storage.
- `scripts/check_s3_storage.py` jest recznym testem S3/Spaces z zabezpieczeniem przed produkcyjnym prefiksem.
- `scripts/plan_storage_migration.py` przygotowuje lokalny dry-run migracji plikow `data/magazyn -> Spaces`.
- Migrator SQLite -> PostgreSQL obejmuje obecnie 57 z 67 tabel.
- Audyt migracji DB pokazuje `Blockers: 0`, `Warnings: 10`.
- Pozostale 10 tabel poza migratorem sa swiadomie sklasyfikowane jako import/audit history, OAuth state, heartbeat, outbox albo UI/read-state.
- `scripts/check_postgres_migration.py` jest przygotowany jako reczny test migratora na sztucznej SQLite i testowym PostgreSQL.
- `docker-compose.postgres-migration-test.yml` i `scripts/run_postgres_migration_check.ps1` sa przygotowane do lokalnego testu PostgreSQL.
- `run_quality_checks.py` ma profile `smoke`, `database-migration-audit`, `s3-integration`, `storage-migration-plan`, `postgres-migration-check` i inne profile kontrolne.
- `frontend/` jest docelowym frontendem Next.js/React, a `static/` jest legacy UI utrzymywanym tylko dla kompatybilnosci.

Co jest tylko zaplanowane:

- Realny prototyp na DigitalOcean App Platform.
- DigitalOcean Managed PostgreSQL jako testowe/prototypowe srodowisko.
- DigitalOcean Spaces jako prywatny storage plikow.
- Finalny runbook albo `.do/app.yaml`.
- Docelowy podzial App Platform na web, worker i frontend Next.js.
- Produkcyjna lista env/secrets.
- Produkcyjna migracja danych i plikow.

Co zostalo przetestowane lokalnie:

- Unit testy storage `local|s3`.
- Testy `check_s3_storage.py` bez prawdziwego bucketa.
- Dry-run planu migracji plikow.
- Audyt migracji SQLite -> PostgreSQL bez polaczenia z PostgreSQL.
- Testy migratora i klasyfikacji pozostalych tabel.
- Przygotowanie `postgres-migration-check` bez prawdziwego PostgreSQL.
- Pelny `smoke` byl wczesniej zielony, ale jest dlugi i nie byl uruchamiany w kazdym kroku.

Czego jeszcze nie udalo sie realnie zweryfikowac:

- Realnego `postgres-migration-check` na lokalnym/testowym PostgreSQL, bo Docker nie byl dostepny.
- Polaczenia z DigitalOcean Managed PostgreSQL.
- Polaczenia z prywatnym DigitalOcean Spaces.
- Rzeczywistej migracji plikow do Spaces.
- Rzeczywistej migracji danych produkcyjnych.
- Deploya backendu na DigitalOcean.
- Deploya frontendu Next.js na DigitalOcean.
- Zachowania background loops przy skalowaniu wiecej niz jednej instancji.

## B. Co jest gotowe

Healthcheck:

- `GET /health` istnieje i jest uzywany w `railway.json`.
- To jest dobry kandydat na healthcheck App Platform.

Start command:

- Obecny start command jest zgodny z PaaS-style runtime:
  `python run.py --mode standalone --host 0.0.0.0 --port $PORT`.
- `run.py` obsluguje rowniez `--mode web` i `--mode worker`, co daje droge do pozniejszego podzialu komponentow.

Storage:

- `INVOICE_STORAGE_BACKEND=local|s3` istnieje.
- `S3StorageService` uzywa S3-compatible API przez backend.
- `INVOICE_S3_PUBLIC_BASE_URL` jest zarezerwowane, ale nie sluzy jako domyslne obejscie uprawnien backendu.
- `S3StorageService.resolve_local_path()` odmawia lokalnej sciezki dla S3, co chroni przed mieszaniem storage lokalnego i obiektowego.

S3/Spaces test:

- `scripts/check_s3_storage.py` jest osobnym recznym testem.
- Wymaga `INVOICE_STORAGE_BACKEND=s3` i kompletu `INVOICE_S3_*`.
- Blokuje prefiksy wygladajace produkcyjnie, np. `casi/prod`, bez jawnej zgody.

Migracja plikow:

- `scripts/plan_storage_migration.py` generuje lokalny dry-run.
- Raport pokazuje storage keys, planowane object keys, severity i blockery.
- Dry-run nie laczy sie z DigitalOcean i nie wysyla plikow.

Migracja bazy:

- Lokalny audyt DB porownuje SQLite, PostgreSQL i `TABLE_ORDER`.
- Aktualny stan: `SQLite tables: 67`, `PostgreSQL tables: 67`, `Migrator tables: 57`, `Tables missing: 10`, `Blockers: 0`, `Warnings: 10`.
- Migrator nie migruje fizycznych plikow i nie uruchamia S3.
- `postgres-migration-check` jest przygotowany na sztucznej SQLite.

Quality profiles:

- `database-migration-audit` sprawdza audyt i migrator.
- `storage-migration-plan` sprawdza plan migracji plikow.
- `s3-integration` jest reczny i wymaga env S3.
- `postgres-migration-check` jest reczny i wymaga `CASI_TEST_POSTGRES_DATABASE_URL`.
- `smoke` jest oddzielony od recznych integracji i pozostaje lokalnym profilem regresji.

## C. Co nie jest jeszcze gotowe albo zweryfikowane

- Brak realnego testu PostgreSQL: `postgres-migration-check` nie zostal uruchomiony na prawdziwym PostgreSQL.
- Brak realnego testu DigitalOcean Spaces na prywatnym buckecie.
- Brak migracji plikow z `data/magazyn` do Spaces.
- Brak testu z DigitalOcean Managed PostgreSQL.
- Brak `.do/app.yaml`.
- Brak finalnego runbooka App Platform.
- Brak realnego deploya backendu.
- Brak decyzji, czy prototyp startuje jako `standalone`, czy jako osobne komponenty `web` i `worker`.
- Brak finalnej decyzji routingu backend/frontend, zwlaszcza kiedy `frontend/` ma przejac UI, a `static/` pozostac tylko legacy fallbackiem.
- Brak produkcyjnej listy env/secrets.
- Brak decyzji, ktore background loops powinny dzialac w prototypie.
- Brak potwierdzenia, ze wszystkie istotne flow aplikacji dzialaja na PostgreSQL.

## D. Blockery przed lokalnym prototypem PostgreSQL

Glowny praktyczny blocker:

- Docker albo inny lokalny testowy PostgreSQL nie jest jeszcze uruchomiony w srodowisku, w ktorym wykonywano ostatni test.

Przed lokalnym prototypem PostgreSQL trzeba:

- uruchomic Docker Desktop albo inny lokalny PostgreSQL,
- uruchomic `scripts/run_postgres_migration_check.ps1`,
- potwierdzic, ze `postgres-migration-check` przechodzi na bazie `casi_migration_test`,
- nie uzywac `DATABASE_URL` ani `INVOICE_DATABASE_URL` jako celu tego testu,
- zachowac test jako migracje sztucznej SQLite, nie prawdziwej bazy uzytkownika.

## E. Blockery przed prototypem na DigitalOcean

Przed pierwszym prototypem na DigitalOcean trzeba minimum:

- uruchomic lokalny/testowy `postgres-migration-check`,
- uruchomic reczny test prywatnego bucketa Spaces z prefiksem `casi/dev-test`,
- zdecydowac, czy App Platform ma miec jeden komponent `standalone`, czy osobne `web` i `worker`,
- przygotowac App Platform runbook/spec bez sekretow w repo,
- przygotowac liste env dla backendu, storage, cookies, lokalnego sandbox seed, DB i integracji,
- nie uzywac lokalnego filesystemu jako trwalego storage w App Platform,
- zdecydowac, jak `frontend/` Next bedzie serwowany wzgledem backendu API,
- zostawic `railway.json` jako fallback/legacy do czasu swiadomego przelaczenia.

## F. Ryzyka

- DigitalOcean App Platform nie moze byc traktowana jako trwaly dysk. `data/magazyn` w kontenerze jest niewlasciwym miejscem na pliki produkcyjne.
- Background loops w `standalone` moga sie dublowac przy skalowaniu poziomym.
- Worker i web moga wymagac rozdzielenia albo mechanizmu koordynacji.
- Spaces/S3 musi pozostac prywatne, a dostep do plikow powinien byc kontrolowany przez backend.
- OAuth/tokeny sa danymi wrazliwymi i nie powinny trafiac do logow, frontendu ani raportow.
- Pozostale 10 tabel poza migratorem nie blokuje prototypu, ale trzeba swiadomie zaakceptowac ich brak albo odbudowe.
- Import history `email_import_*` i `ksef_import_*` moze byc potrzebna przed produkcyjna migracja, nawet jesli nie blokuje prototypu.
- `smoke` jest dlugi, wiec trzeba uruchamiac go z odpowiednim limitem czasu i nie mylic timeoutu z sukcesem.
- `static/` nadal moze byc serwowane przez backend dla kompatybilnosci, ale nie jest source of truth UI.
- Domyslne konto admina i lokalny sandbox seed musza byc wylaczone albo zmienione przed jakimkolwiek realnym srodowiskiem z danymi.

## G. Minimalna kolejnosc nastepnych krokow

1. Uruchomic Docker Desktop i `postgres-migration-check`.
2. Uruchomic test prywatnego DigitalOcean Spaces z prefiksem `casi/dev-test`.
3. Przygotowac runbook DigitalOcean App Platform bez deploya.
4. Przygotowac `.do/app.yaml` dopiero po decyzji o komponentach.
5. Wykonac probny deploy techniczny backendu na pustej bazie/testowym srodowisku.
6. Dopiero potem myslec o migracji danych i plikow.

## H. Czego nie robic jeszcze

- Nie robic produkcyjnego deploya.
- Nie migrowac prawdziwych danych.
- Nie migrowac plikow do Spaces.
- Nie uzywac produkcyjnego `DATABASE_URL`.
- Nie usuwac Railway config.
- Nie ruszac `static/`.
- Nie laczyc migracji bazy z migracja plikow.
- Nie traktowac prototypu jako produkcji.
- Nie dodawac `.do/app.yaml` przed decyzja o komponentach.
- Nie wrzucac sekretow do repo.
- Nie traktowac lokalnego filesystemu App Platform jako storage.
