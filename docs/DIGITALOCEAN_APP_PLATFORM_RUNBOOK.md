# DigitalOcean App Platform Runbook

Status: praktyczny runbook przyszlego prototypu CASI Workspace na DigitalOcean App Platform.

Ten dokument opisuje plan. Deploy nie zostal jeszcze wykonany.

Ten etap nie:

- tworzy `.do/app.yaml`,
- laczy sie z DigitalOcean,
- laczy sie z PostgreSQL,
- laczy sie z S3/Spaces,
- migruje danych,
- migruje plikow,
- zmienia frontendu,
- zmienia logiki biznesowej.

## A. Cel prototypu

Celem jest techniczny prototyp CASI Workspace na DigitalOcean, ktory pozwoli sprawdzic:

- uruchomienie backendu Python na App Platform,
- polaczenie backendu z PostgreSQL,
- uzycie prywatnego object storage przez S3-compatible API,
- podstawowy healthcheck i logowanie,
- minimalna konfiguracje env/secrets,
- kierunek podzialu backend/frontend/worker.

To nie jest:

- produkcja,
- finalne srodowisko klienta,
- migracja prawdziwych danych,
- migracja prawdziwych plikow,
- ostateczna architektura kosztowa,
- finalny deploy frontendu Next.js.

## B. Architektura docelowego prototypu

Rekomendowany wariant prototypu:

- Backend Python jako komponent DigitalOcean App Platform.
- PostgreSQL jako DigitalOcean Managed PostgreSQL.
- Spaces jako prywatny object storage, dostepny przez backend i `S3StorageService`.
- Frontend Next.js z `frontend/` jako osobny komponent App Platform albo osobny pozniejszy etap.
- Railway zostaje jako legacy/fallback do czasu stabilizacji DigitalOcean.
- `static/` zostaje legacy/fallback i nie jest source of truth UI.

Minimalny wariant pierwszego technicznego backend deploya:

- Jeden backend component.
- Pusta albo testowa baza PostgreSQL.
- `INVOICE_ENABLE_DEMO_SEED=0`.
- `INVOICE_STORAGE_BACKEND=s3`, ale dopiero po pozytywnym tescie prywatnego Spaces.
- Healthcheck `/health`.
- Brak migracji prawdziwych danych.
- Brak migracji plikow.

Docelowy wariant po stabilizacji:

- Backend `web` jako osobny komponent.
- Backend `worker` jako osobny komponent.
- Frontend Next.js jako osobny komponent z rootem `frontend/`.
- PostgreSQL jako managed database.
- Spaces jako prywatny storage.
- Jasne publiczne URL-e i API base URL.

## C. Decyzja web/worker

Obecny `run.py` ma trzy tryby:

- `standalone` - web i background loops w jednym procesie,
- `web` - tylko serwer HTTP,
- `worker` - tylko petle tla.

Problem:

- `standalone` jest najprostszy dla prototypu.
- `standalone` uruchamia web, email scheduler, task reminder scheduler, reminder delivery worker i knowledge pipeline w jednym procesie.
- Przy skalowaniu poziomym App Platform moze uruchomic wiecej niz jedna replike.
- Wiele replik `standalone` moze zdublowac background loops.

Rekomendacja:

- Pierwszy techniczny deploy moze zaczac jako jeden proces `standalone`, tylko jesli skala to jedna replika i jasno akceptujemy ryzyko.
- Jesli prototyp ma dzialac stabilniej albo dluzej, rozdzielic komponenty na `web` i `worker`.
- Przy rozdzieleniu komponentow App Platform healthcheck powinien dotyczyc komponentu web.
- Worker powinien miec osobna obserwowalnosc w logach i przez endpointy/system health.

## D. Start command

Obecny Railway-style command:

```bash
python run.py --mode standalone --host 0.0.0.0 --port $PORT
```

Mozliwy backend command dla pierwszego App Platform prototypu:

```bash
python run.py --mode standalone --host 0.0.0.0 --port $PORT
```

Wariant web-only:

```bash
python run.py --mode web --host 0.0.0.0 --port $PORT
```

Wariant worker-only:

```bash
python run.py --mode worker
```

Nie ustawiaj tego jeszcze w DigitalOcean. To sa komendy do przyszlego runbooka/spec.

## E. Healthcheck

Backend ma endpoint:

```text
GET /health
```

App Platform powinno sprawdzac:

```text
/health
```

Nie zmieniac endpointu w tym kroku.

Dodatkowy endpoint aplikacyjny:

```text
GET /api/system/health
```

Ten endpoint jest bardziej aplikacyjny i moze wymagac kontekstu uzytkownika/organizacji, wiec do App Platform healthcheck lepszy jest prosty `/health`.

## F. Env/secrets checklist

Nie wpisywac prawdziwych wartosci do repo.

### Baza

- [ ] `INVOICE_DB_ENGINE=postgresql`
- [ ] `DATABASE_URL=<managed-postgres-url>` albo `INVOICE_DATABASE_URL=<managed-postgres-url>`
- [ ] `INVOICE_DB_INIT_MAX_RETRIES=<np. 6>`
- [ ] `INVOICE_DB_INIT_RETRY_SLEEP_SECONDS=<np. 2>`

### Storage

- [ ] `INVOICE_STORAGE_BACKEND=s3`
- [ ] `INVOICE_S3_ENDPOINT_URL=<spaces-endpoint>`
- [ ] `INVOICE_S3_REGION=<region>`
- [ ] `INVOICE_S3_BUCKET=<private-bucket>`
- [ ] `INVOICE_S3_ACCESS_KEY_ID=<secret>`
- [ ] `INVOICE_S3_SECRET_ACCESS_KEY=<secret>`
- [ ] `INVOICE_S3_PREFIX=<np. casi/dev-test dla prototypu>`
- [ ] `INVOICE_S3_PUBLIC_BASE_URL=` zostawic puste, chyba ze powstanie kontrolowany model publicznych URL-i.

### Bezpieczenstwo

- [ ] `INVOICE_SECURE_COOKIES=1`
- [ ] `INVOICE_ENABLE_DEMO_SEED=0`
- [ ] `INVOICE_ENABLE_TEST_IMPORTS=0`
- [ ] `INVOICE_DEFAULT_ADMIN_LOGIN=<zmienione>`
- [ ] `INVOICE_DEFAULT_ADMIN_PASSWORD=<silne haslo startowe lub procedura bootstrap>`
- [ ] `INVOICE_SHOW_DEFAULT_LOGIN_HINT=0`
- [ ] `INVOICE_SESSION_COOKIE_NAME=<stabilna-nazwa>`
- [ ] `INVOICE_SESSION_DURATION_HOURS=<wartosc>`
- [ ] `INVOICE_MAX_ACTIVE_DEVICES_PER_ACCOUNT=<wartosc>`
- [ ] `CASI_SERVE_LEGACY_STATIC=1` tylko jesli backend nadal ma serwowac legacy UI; docelowo po frontend deploy mozna rozwazyc `0`.

### Publiczny URL

- [ ] `INVOICE_PUBLIC_BASE_URL=https://<publiczny-adres>`

Wymagane dla Google OAuth i email OAuth callbacks.

### Integracje opcjonalne

Telegram:

- [ ] `INVOICE_TELEGRAM_BOT_TOKEN=<secret>`
- [ ] `INVOICE_TELEGRAM_WEBHOOK_SECRET=<secret>`
- [ ] `INVOICE_ENABLE_TELEGRAM_TASK_REMINDERS=0|1`

Slack:

- [ ] `INVOICE_SLACK_BOT_TOKEN=<secret>`
- [ ] `INVOICE_SLACK_SIGNING_SECRET=<secret>`

Google OAuth:

- [ ] `INVOICE_GOOGLE_CLIENT_ID=<secret>`
- [ ] `INVOICE_GOOGLE_CLIENT_SECRET=<secret>`

Email/IMAP:

- [ ] `INVOICE_EMAIL_IMAP_HOST=<host>`
- [ ] `INVOICE_EMAIL_IMAP_PORT=<port>`
- [ ] `INVOICE_EMAIL_IMAP_USERNAME=<secret>`
- [ ] `INVOICE_EMAIL_IMAP_PASSWORD=<secret>`
- [ ] `INVOICE_EMAIL_IMAP_FOLDER=INBOX`
- [ ] `INVOICE_EMAIL_IMAP_USE_SSL=1`
- [ ] `INVOICE_EMAIL_AUTOCHECK_ENABLED=0` na pierwszym prototypie, chyba ze swiadomie testujemy worker.
- [ ] `INVOICE_EMAIL_AUTOCHECK_SECONDS=<wartosc>`

Email Google OAuth:

- [ ] `INVOICE_EMAIL_GOOGLE_CLIENT_ID=<secret>`
- [ ] `INVOICE_EMAIL_GOOGLE_CLIENT_SECRET=<secret>`

OCR:

- [ ] `INVOICE_TESSERACT_CMD=<path albo puste>`
- [ ] `INVOICE_OCR_LANGUAGE=pol+eng`

KSeF/import:

- [ ] `INVOICE_KSEF_FETCH_LIMIT=<wartosc>`
- [ ] inne sekrety KSeF dopiero po osobnej decyzji integracyjnej.

Background loops:

- [ ] `INVOICE_TASK_REMINDER_POLL_SECONDS=<wartosc>`
- [ ] `INVOICE_TASK_REMINDER_WORKER_POLL_SECONDS=<wartosc>`
- [ ] `INVOICE_TASK_REMINDER_RETRY_MINUTES=<wartosc>`
- [ ] `INVOICE_TASK_REMINDER_PROCESSING_TIMEOUT_MINUTES=<wartosc>`
- [ ] `INVOICE_TASK_REMINDER_MAX_ATTEMPTS=<wartosc>`
- [ ] `INVOICE_KNOWLEDGE_PIPELINE_POLL_SECONDS=<wartosc>`
- [ ] `INVOICE_KNOWLEDGE_FOLDER_SCAN_SECONDS=<wartosc>`

## G. Co musi byc zrobione przed deployem

- [ ] Realny `postgres-migration-check` na lokalnym/testowym PostgreSQL.
- [ ] Test prywatnego Spaces z prefiksem `casi/dev-test`.
- [ ] Decyzja `standalone` vs `web`/`worker`.
- [ ] Decyzja frontend/backend routing.
- [ ] Lista env i sekretow bez wartosci w repo.
- [ ] Potwierdzenie, ze App Platform nie uzywa lokalnego filesystemu jako trwalego storage.
- [ ] `python run_quality_checks.py --profile database-migration-audit`.
- [ ] `python -m unittest tests.test_storage_service -v`.
- [ ] `python -m unittest tests.test_check_postgres_migration -v`.
- [ ] `python run_quality_checks.py --profile smoke` z odpowiednio dlugim timeoutem, jesli przed deployem mamy potwierdzac szersza regresje.
- [ ] Decyzja, czy `static/` ma byc jeszcze serwowane przez backend w prototypie.

## H. Plan pierwszego technicznego deploya

Nie wykonywac w tym kroku. To jest przyszla kolejnosc:

1. Przygotowac testowy PostgreSQL.
2. Przetestowac migrator na tymczasowym PostgreSQL.
3. Przetestowac Spaces na sztucznym pliku.
4. Przygotowac App Platform app recznie.
5. Wdrozyc backend na pustej/testowej bazie.
6. Sprawdzic `/health`.
7. Sprawdzic podstawowe logowanie/metadane.
8. Dopiero potem myslec o frontendzie, migracji plikow i migracji danych.

## I. Czego nie robic

- Nie robic produkcyjnego deploya.
- Nie migrowac prawdziwych danych.
- Nie migrowac plikow.
- Nie uzywac `local` filesystemu jako storage produkcyjnego.
- Nie usuwac `railway.json`.
- Nie usuwac `Procfile`.
- Nie ruszac `static/`.
- Nie uzywac produkcyjnego `DATABASE_URL` w testach.
- Nie laczyc testu PostgreSQL, Spaces i deploya w jednym kroku.
- Nie tworzyc `.do/app.yaml` przed decyzja o komponentach.
- Nie wpisywac sekretow do repo.
- Nie traktowac prototypu jako produkcji.

## J. Checklisty operacyjne

### Przed PostgreSQL

- [ ] Docker Desktop albo lokalny PostgreSQL dziala.
- [ ] Baza testowa nazywa sie `casi_migration_test` albo zawiera `test/tmp/local`.
- [ ] `CASI_TEST_POSTGRES_DATABASE_URL` jest ustawione tylko dla testu.
- [ ] `DATABASE_URL` i `INVOICE_DATABASE_URL` nie sa uzywane jako fallback testu.
- [ ] `python run_quality_checks.py --profile postgres-migration-check` przechodzi.

### Przed Spaces

- [ ] Bucket jest prywatny.
- [ ] Prefiks testowy to np. `casi/dev-test`.
- [ ] `INVOICE_STORAGE_BACKEND=s3`.
- [ ] Wszystkie `INVOICE_S3_*` sa ustawione jako sekrety/env, nie w repo.
- [ ] `python run_quality_checks.py --profile s3-integration` przechodzi.

### Przed App Platform

- [ ] Wybrano `standalone` albo `web`/`worker`.
- [ ] Ustalono root/backend command.
- [ ] Ustalono healthcheck `/health`.
- [ ] Przygotowano liste env/secrets.
- [ ] Ustalono, czy `frontend/` jest osobnym komponentem teraz czy pozniej.
- [ ] Nie przygotowywano `.do/app.yaml` bez decyzji o komponentach.

### Po pierwszym deployu

- [ ] `/health` zwraca OK.
- [ ] Logi startu nie pokazuja sekretow.
- [ ] `INVOICE_ENABLE_DEMO_SEED=0`.
- [ ] `INVOICE_SECURE_COOKIES=1`.
- [ ] Storage backend to `s3`, jesli prototyp ma testowac pliki.
- [ ] Podstawowe logowanie dziala.
- [ ] `/api/meta` albo inne podstawowe metadane dzialaja.
- [ ] Nie ma zapisu trwalych plikow do lokalnego filesystemu jako jedynego storage.

### Przed jakakolwiek migracja danych

- [ ] Prototyp PostgreSQL dziala na pustej/testowej bazie.
- [ ] Prototyp Spaces dziala na sztucznym pliku.
- [ ] Jest decyzja o pozostalych 10 tabelach poza migratorem.
- [ ] Jest osobny plan migracji plikow.
- [ ] Jest backup lokalnej SQLite i storage.
- [ ] Jest plan rollbacku.
- [ ] Smoke/testy maja wystarczajacy timeout.

## K. Otwarte decyzje

- Czy prototyp zaczyna jako `standalone`.
- Kiedy rozdzielic `web` i `worker`.
- Czy frontend Next.js wdrazac od razu, czy po backendowym prototypie.
- Jak ustawic domene i `INVOICE_PUBLIC_BASE_URL`.
- Jak frontend ma wskazywac backend API.
- Ktore integracje wylaczyc w pierwszym prototypie.
- Czy email autocheck ma byc wylaczony na pierwszym deployu.
- Jak obsluzyc OCR/Tesseract na App Platform.
- Czy knowledge folder scan ma dzialac w App Platform, czy pozostac lokalnym mechanizmem dev.
- Czy pozostale 10 tabel poza migratorem zostaja pominiete/odbudowane w prototypie.
- Kiedy przygotowac `.do/app.yaml`.

## Kiedy przygotowac `.do/app.yaml`

Nie tworzyc `.do/app.yaml` przed decyzja o:

- liczbie komponentow,
- `standalone` vs `web`/`worker`,
- routingu frontend/backend,
- env/secrets,
- storage backend,
- sposobie testowania PostgreSQL i Spaces.

`.do/app.yaml` powinien byc osobnym, malym krokiem po pozytywnym lokalnym PostgreSQL check i po tescie prywatnego Spaces.
