# Kontrolny test migracji SQLite -> PostgreSQL

Ten dokument opisuje pierwszy techniczny test migratora SQLite -> PostgreSQL dla CASI Workspace.

To nie jest produkcyjna migracja danych.

## Cel

Test sprawdza, czy obecny migrator potrafi przeniesc maly, sztuczny zestaw danych z tymczasowej SQLite do jawnie wskazanej testowej bazy PostgreSQL.

Skrypt:

- tworzy sztuczna baze SQLite w katalogu tymczasowym,
- wypelnia ja reprezentatywnymi danymi testowymi,
- resetuje wylacznie zwalidowana testowa baze PostgreSQL,
- uruchamia istniejacy migrator na sztucznej SQLite,
- sprawdza liczbe rekordow w reprezentatywnych tabelach,
- sprawdza podstawowe relacje, np. organizacja -> uzytkownik -> zadanie -> komentarz/zalacznik,
- sprawdza reset sekwencji PostgreSQL,
- nie uzywa lokalnej bazy uzytkownika,
- nie dotyka `data/magazyn`,
- nie uzywa S3,
- nie uzywa DigitalOcean.

## Wymagany env

Skrypt wymaga osobnej zmiennej:

```powershell
$env:CASI_TEST_POSTGRES_DATABASE_URL="postgresql://postgres:<HASLO>@localhost:5432/casi_migration_test"
```

Nie wpisuj prawdziwych sekretow do dokumentacji, commita ani logow.

Skrypt nigdy nie uzywa jako fallbacku:

- `DATABASE_URL`,
- `INVOICE_DATABASE_URL`.

Powod: te zmienne moga wskazywac przyszla, stagingowa albo produkcyjna baze.

## Zabezpieczenia

`scripts/check_postgres_migration.py` odmawia dzialania, jesli:

- `CASI_TEST_POSTGRES_DATABASE_URL` nie jest ustawione,
- URL nie uzywa `postgresql://` albo `postgres://`,
- URL nie zawiera hosta,
- nazwa bazy nie zawiera `test`, `tmp`, `local` albo `casi_migration_test`,
- host wyglada jak DigitalOcean Managed Database, Railway albo produkcyjna infrastruktura,
- skrypt nie moze bezpiecznie zwalidowac celu.

Skrypt redaguje URL w komunikatach i nie wypisuje hasla.

## Uruchomienie w Windows PowerShell

Najwygodniejsza lokalna sciezka uzywa izolowanego Docker Compose:

```powershell
.\scripts\run_postgres_migration_check.ps1
```

Ten skrypt:

- uruchamia tylko testowy PostgreSQL z `docker-compose.postgres-migration-test.yml`,
- uzywa bazy `casi_migration_test`,
- uzywa testowego uzytkownika `casi_test`,
- ustawia tylko `CASI_TEST_POSTGRES_DATABASE_URL`,
- nie ustawia `DATABASE_URL`,
- nie ustawia `INVOICE_DATABASE_URL`,
- nie montuje lokalnej bazy aplikacji,
- nie montuje `data/magazyn`,
- po tescie zatrzymuje kontener, chyba ze podasz `-KeepContainer`.

Opcje:

```powershell
.\scripts\run_postgres_migration_check.ps1 -KeepContainer
.\scripts\run_postgres_migration_check.ps1 -SkipDockerStart
```

`-SkipDockerStart` zaklada, ze testowy PostgreSQL juz dziala i jest dostepny pod URL ustawianym przez skrypt.

## Reczne uruchomienie bez Dockera

Przyklad z placeholderem:

```powershell
$env:CASI_TEST_POSTGRES_DATABASE_URL="postgresql://postgres:<HASLO>@localhost:5432/casi_migration_test"
python run_quality_checks.py --profile postgres-migration-check
```

Mozna tez uruchomic sam skrypt:

```powershell
$env:CASI_TEST_POSTGRES_DATABASE_URL="postgresql://postgres:<HASLO>@localhost:5432/casi_migration_test"
python scripts/check_postgres_migration.py
```

Manualnie utworz lokalna baze testowa, np.:

```powershell
createdb casi_migration_test
$env:CASI_TEST_POSTGRES_DATABASE_URL="postgresql://postgres:<HASLO>@localhost:5432/casi_migration_test"
python run_quality_checks.py --profile postgres-migration-check
```

Nie uzywaj `DATABASE_URL` ani `INVOICE_DATABASE_URL` jako celu tego testu.

## Sprzatanie Docker Compose

Zatrzymanie testowego kontenera:

```powershell
docker compose -f docker-compose.postgres-migration-test.yml down
```

Usuniecie kontenera i testowego wolumenu:

```powershell
docker compose -f docker-compose.postgres-migration-test.yml down -v
```

Wolumen `casi_postgres_migration_test_data` zawiera tylko dane testowej bazy PostgreSQL tworzonej dla tego checka.

## Kiedy nie uruchamiac

Nie uruchamiaj tego testu, jesli:

- nie masz pewnosci, ze PostgreSQL jest lokalny albo testowy,
- baza nie jest przeznaczona do resetowania,
- URL wskazuje DigitalOcean, Railway albo produkcje,
- chcesz migrowac prawdziwe dane uzytkownika,
- chcesz migrowac pliki,
- chcesz testowac S3 albo DigitalOcean Spaces.

## Pozytywny wynik

Pozytywny wynik oznacza tylko, ze obecny migrator przeszedl techniczny test na sztucznych danych i testowej bazie PostgreSQL.

Nie oznacza to jeszcze:

- gotowosci do produkcyjnej migracji,
- gotowosci do deploya,
- gotowosci do DigitalOcean,
- przeniesienia realnych plikow,
- przeniesienia pelnej historii importow.

Pelna produkcyjna migracja bedzie osobnym etapem po pozytywnych testach technicznych, decyzji o pozostalych tabelach oraz osobnym planie migracji plikow.
