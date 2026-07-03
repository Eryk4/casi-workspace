# Database Migration Audit

Ten dokument opisuje lokalny audyt gotowosci migracji danych SQLite -> PostgreSQL dla CASI Workspace.

To jest audyt, nie migracja.

Audyt:

- nie laczy sie z PostgreSQL,
- nie wymaga DigitalOcean,
- nie wymaga sekretow,
- nie wykonuje migracji danych,
- nie modyfikuje lokalnej bazy uzytkownika,
- analizuje deklaracje schematow i liste tabel w migratorze.

## Uruchomienie

```powershell
python scripts/audit_database_migration.py
```

Raporty lokalne:

```text
reports/database_migration_audit.json
reports/database_migration_audit.md
```

Profil quality check:

```powershell
python run_quality_checks.py --profile database-migration-audit
```

Ten profil uruchamia testy audytu, testy zakresu migratora i sam audyt. Nie laczy sie z PostgreSQL i nie wykonuje migracji.

## Co sprawdza audyt

Audyt porownuje:

- tabele zadeklarowane dla SQLite w `app/db.py`,
- tabele zadeklarowane dla PostgreSQL w `app/db.py`,
- tabele wymienione w `TABLE_ORDER` w `migrate_sqlite_to_configured_db.py`,
- tabele pomijane przez migrator,
- roznice SQLite-only i PostgreSQL-only,
- potencjalnie niebezpieczna kolejnosc migracji wzgledem zaleznosci foreign key.

## Aktualny stan migratora

Po rozszerzeniach `organization access core`, `tasks and workflow core`, `invoice operations core`, `crm notes backend`, `billing core`, `knowledge/document core`, `intake/attachments core`, `automation core`, `calendar/integration core`, `whiteboard core` oraz `ui/state core` migrator obejmuje 58 tabel.

Aktualny wynik audytu po etapie ui/state core:

```text
SQLite tables: 68
PostgreSQL tables: 68
Migrator tables: 58
Tables missing from migrator: 10
blocker: 0
warning: 10
error: 0
info: 0
```

## Etap 1: organization access core

Dodano:

```text
organization_memberships
organization_modules
user_capabilities
system_settings
```

Wybrano je, bo sa bezposrednio zwiazane z dostepem uzytkownika do organizacji, wlaczonymi modulami i ustawieniami systemowymi.

## Etap 2: tasks and workflow core

Dodano:

```text
user_calendars
tasks
task_visibility_users
task_links
task_notes
task_checklist_items
task_templates
approval_requests
task_attachments
task_history
work_items
work_item_history
```

Pakiet obejmuje podstawowy operacyjny workflow CASI: zadania, widocznosc zadan, notatki, checklisty, zalaczniki, historie, wnioski approval oraz ogolne work items.

`user_calendars` dodano jako minimalna twarda zaleznosc, poniewaz `tasks.calendar_id` ma foreign key do `user_calendars`.

## Etap 3: invoice operations core

Dodano:

```text
invoice_comments
invoice_handoff_batches
invoice_handoff_batch_items
invoice_ksef_field_overrides
```

Pakiet zachowuje operacyjny kontekst faktur poza sama tabela `invoices`: komentarze, partie przekazania, pozycje handoffu oraz korekty pol KSeF powiazane z approval workflow.

## Etap 4: billing core

Dodano:

```text
billing_schools
billing_models
billing_payers
billing_students
billing_charge_batches
billing_charges
billing_student_charge_state
billing_payer_charge_state
billing_bank_accounts
billing_statement_imports
billing_transactions
billing_payment_matches
billing_payer_ledger_entries
```

Pakiet jest wazny, bo zachowuje rdzen rozliczen: szkoly/modele, platnikow, uczniow, naliczenia, stany rabatow, rachunki bankowe, importy wyciagow, transakcje, dopasowania platnosci i ledger platnika.

Z listy kandydatow billing core nie pominieto zadnej tabeli. Zaleznosci sa zachowane: slowniki i platnicy sa przed uczniami, batch przed charges, charges i transakcje przed payment matches oraz ledgerem, a statement imports przed transactions.

## Etap 5: knowledge/document core

Dodano:

```text
knowledge_documents
knowledge_document_versions
knowledge_processing_jobs
knowledge_folder_watchers
knowledge_document_comments
```

Pakiet jest wazny, bo zachowuje rdzen bazy wiedzy i dokumentow: metadane dokumentow, wersje, komentarze, obserwowane foldery oraz kolejke przetwarzania wiedzy.

Ten etap migruje tylko rekordy bazodanowe i metadane, np. `file_link`, `file_storage_key`, `content_text` oraz hashe. Nie migruje fizycznych plikow z `data/magazyn`, nie uruchamia S3/DigitalOcean Spaces i nie dotyka `scripts/plan_storage_migration.py`. Migracja plikow pozostaje osobnym etapem opisanym w `docs/STORAGE_MIGRATION_PLAN.md`.

Z listy kandydatow knowledge/document core nie pominieto zadnej tabeli. Zaleznosci sa zachowane: `knowledge_documents` jest przed wersjami, jobami i komentarzami, a `knowledge_document_versions` jest przed komentarzami, ktore moga wskazywac na wersje dokumentu.

## Etap 6: intake/attachments core

Dodano:

```text
intake_forms
intake_items
intake_item_comments
intake_item_history
entity_attachments
```

Pakiet jest wazny, bo zachowuje rdzen przyjmowania spraw i formularzy: definicje formularzy, zgloszenia intake, komentarze, historie oraz metadane zalacznikow powiazanych z encjami.

Ten etap migruje tylko rekordy bazodanowe i metadane. `entity_attachments` zawiera m.in. `file_link`, `file_storage_key` i `storage_backend`, ale migrator bazy przenosi tylko te pola jako rekord DB. Nie kopiuje fizycznych plikow, nie przenosi obiektow storage, nie uruchamia S3/DigitalOcean Spaces i nie dotyka `scripts/plan_storage_migration.py`. Migracja plikow pozostaje osobnym etapem opisanym w `docs/STORAGE_MIGRATION_PLAN.md`.

Z listy kandydatow intake/attachments core nie pominieto zadnej tabeli. Zaleznosci sa zachowane: `intake_forms` jest przed `intake_items`, a `intake_items` jest przed komentarzami i historia. `entity_attachments` jest generyczna tabela metadanych zalacznikow i nie ma foreign key do konkretnej encji poza `organizations` i `users`, dlatego jest migrowana w tym pakiecie jako metadane, bez migracji plikow.

## Etap 7: automation core

Dodano:

```text
automation_rules
automation_executions
```

Pakiet jest wazny, bo zachowuje podstawowe definicje automatyzacji oraz historie ich wykonan. Bez tych tabel po migracji baza nie mialaby informacji o aktywnych regulach, warunkach, akcjach, liczbie wykonan i wynikach ostatnich uruchomien automatyzacji.

Z listy kandydatow automation core nie pominieto zadnej tabeli. Zaleznosci sa zachowane: `automation_rules` jest przed `automation_executions`, a obie tabele sa po `organizations`; `automation_rules` jest rowniez po `users`, bo zawiera `created_by_user_id`.

## Etap 8: calendar/integration core

Dodano:

```text
user_google_calendar_connections
user_calendar_assignments
system_email_google_connections
```

Pakiet jest wazny, bo zachowuje przypisania kalendarzy uzytkownikow oraz podstawowe polaczenia integracyjne Google Calendar i systemowej poczty Google. Bez tych tabel po migracji baza nie mialaby informacji o tym, ktory uzytkownik ma przypisany kalendarz, ani o zapisanych polaczeniach integracyjnych wymagajacych ponownej kontroli bezpieczenstwa.

Z listy kandydatow calendar/integration core nie pominieto zadnej tabeli. Zaleznosci sa zachowane: `user_calendar_assignments` jest po `users` i `user_calendars`, `user_google_calendar_connections` jest po `users`, a `system_email_google_connections` jest po `users`.

Uwaga bezpieczenstwa: `user_google_calendar_connections` i `system_email_google_connections` zawieraja pola takie jak `access_token`, `refresh_token`, `token_expires_at`, `google_email` i `scope`. Ten etap nie wykonuje prawdziwej migracji danych i nie laczy sie z Google API. Przyszla realna migracja tych tabel musi traktowac tokeny/OAuth jako dane wrazliwe, nie logowac ich wartosci i wymagac osobnej decyzji operacyjnej.

## Etap 9: whiteboard core

Dodano:

```text
organization_whiteboard_events
```

Pakiet jest wazny, bo zachowuje chronologiczna historie zdarzen tablicy organizacji. Tabela zawiera `payload_json`, typ zdarzenia, organizacje, opcjonalnego autora i etykiete aktora. Migrator przenosi rekordy bazy bez interpretowania albo zmiany struktury payloadu.

Zaleznosci sa zachowane: `organization_whiteboard_events` jest po `organizations` oraz po `users`, bo zawiera `created_by_user_id`.

## Etap 10: ui/state core

Dodano:

```text
saved_views
```

Pakiet jest wazny, bo zachowuje zapisane widoki, filtry i stan UI dla organizacji oraz uzytkownikow. Tabela zawiera `view_state_json`, `module_key`, slug, nazwe widoku i flagi udostepnienia/defaultu. Migrator przenosi rekordy bazy bez interpretowania albo zmiany znaczenia konfiguracji UI.

Zaleznosci sa zachowane: `saved_views` jest po `organizations` oraz po `users`, bo zawiera `created_by_user_id`.

## Severity

Audyt uzywa poziomow:

- `info`: informacja, bez ryzyka migracyjnego,
- `warning`: wymaga decyzji lub moze byc odtworzone/pominiete w prototypie,
- `error`: problem audytu lub niespojnosc wymagajaca naprawy,
- `blocker`: blokuje pelna migracje danych SQLite -> PostgreSQL.

Przyklad:

- pominiete tabele biznesowe sa `blocker` dla pelnej migracji danych; po etapie `ui/state core` audyt nie wykrywa juz blockerow,
- stany tymczasowe lub odtwarzalne, np. OAuth state albo worker heartbeat, sa `warning`,
- konflikt kolejnosci migracji wzgledem zaleznosci jest `blocker`.

## Czy migrator wymaga dalszego rozszerzenia

Nie jako blocker przed pierwszym kontrolowanym testem na tymczasowym PostgreSQL.
Tak tylko wtedy, gdy przed produkcyjna migracja chcemy przeniesc pelna historie importow i wszystkie odtwarzalne stany operacyjne.

Obecny migrator obejmuje juz bazowy dostep organizacyjny, rdzen zadan/workflow, operacyjny obieg faktur, billing core, knowledge/document core, intake/attachments core, automation core, calendar/integration core, whiteboard core oraz ui/state core. Nadal nie obejmuje wszystkich aktualnych tabel operacyjnych aplikacji. To nadal nie oznacza gotowosci do produkcyjnej migracji PostgreSQL bez osobnego testu na prawdziwej bazie.

Szczegolowy mini-audyt pozostalych tabel znajduje sie w `docs/DATABASE_MIGRATION_REMAINING_TABLES.md`. Dokument rozdziela pozostale tabele na `must_migrate`, `should_migrate`, `can_rebuild`, `can_skip_for_prototype` oraz `unknown_requires_review`, z osobna rekomendacja ostatnich malych pakietow migratora.

## Przed kontrolowanym testem PostgreSQL

Audyt nie wskazuje juz blockerow, wiec migrator jest gotowy do pierwszego kontrolowanego testu na tymczasowym PostgreSQL. Ten test powinien byc wykonany bez produkcyjnego deploya, bez migracji plikow i bez laczenia z DigitalOcean.

Przed produkcyjna migracja trzeba nadal zdecydowac, ktore pozostale tabele:

- powinny byc migrowane jako historia importow,
- moga byc odtworzone po starcie aplikacji,
- moga zostac swiadomie pominiete w prototypie,
- zawieraja sekrety/tokeny i wymagaja szczegolnej ostroznosci.

Rekomendowany nastepny krok to kontrolowany test migracji na tymczasowym PostgreSQL. Osobny, swiadomy pakiet `import audit history` dla `email_import_runs`, `email_import_items`, `ksef_import_runs`, `ksef_import_items` moze byc wykonany pozniej, jesli przed produkcja chcemy zachowac pelna historie importow. Pozostale brakujace tabele sa obecnie klasyfikowane jako operacyjne/odtwarzalne warningi.

Instrukcja bezpiecznego testu technicznego znajduje sie w `docs/POSTGRES_MIGRATION_TEST.md`. Test uzywa sztucznej SQLite, wymaga osobnego `CASI_TEST_POSTGRES_DATABASE_URL` i nie uzywa `DATABASE_URL` ani `INVOICE_DATABASE_URL` jako fallbacku.

Lokalne uruchomienie testowego PostgreSQL mozna przygotowac przez `docker-compose.postgres-migration-test.yml` oraz `scripts/run_postgres_migration_check.ps1`. To srodowisko jest wylacznie testowe i nie ma zwiazku z DigitalOcean, S3 ani produkcyjnym deployem.

DigitalOcean Managed PostgreSQL pozostaje osobnym pozniejszym etapem. Ten audyt nie tworzy bazy i nie laczy sie z DigitalOcean.
