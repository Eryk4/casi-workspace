# Remaining Database Migration Tables

Ten dokument jest lokalnym mini-audytem pozostalych tabel nieobjetych migratorem SQLite -> PostgreSQL.

To nie jest migracja danych. Ten etap nie laczy sie z PostgreSQL, DigitalOcean, S3 ani Google API i nie modyfikuje lokalnej bazy uzytkownika.

## Aktualny stan

```text
SQLite tables: 67
PostgreSQL tables: 67
Migrator tables: 57
Tables missing from migrator: 10
Blockers: 0
Warnings: 10
Errors: 0
```

Migrator obejmuje juz pakiety:

- organization access core,
- tasks and workflow core,
- invoice operations core,
- billing core,
- knowledge/document core,
- intake/attachments core,
- automation core,
- calendar/integration core,
- whiteboard core,
- ui/state core.

`organization_whiteboard_events` zostalo dodane jako `whiteboard core`. `saved_views` zostalo dodane jako `ui/state core`, poniewaz przechowuje zapisane widoki, filtry i konfiguracje UI uzytkownikow/organizacji.

## Pelna lista brakujacych tabel

```text
email_import_items
email_import_runs
google_calendar_oauth_states
ksef_import_items
ksef_import_runs
system_email_oauth_states
task_reminder_outbox
task_reminder_outbox_attempts
task_reminder_worker_heartbeats
user_module_inbox_state
```

## Klasyfikacja tabel

| Tabela | Klasyfikacja | Severity audytu | Modul | Dane klienta | Dane wrazliwe | Odtwarzalna | Blokuje prototyp PostgreSQL | Rekomendowany pakiet |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `email_import_runs` | `should_migrate` | `warning` | email import | tak | tak | nie | nie | import audit history |
| `email_import_items` | `should_migrate` | `warning` | email import | tak | tak | nie | nie | import audit history |
| `ksef_import_runs` | `should_migrate` | `warning` | KSeF import | tak | tak | nie | nie | import audit history |
| `ksef_import_items` | `should_migrate` | `warning` | KSeF import | tak | tak | nie | nie | import audit history |
| `task_reminder_outbox` | `can_rebuild` | `warning` | task reminders | tak | tak | tak | nie | task reminder operational state |
| `task_reminder_outbox_attempts` | `can_skip_for_prototype` | `warning` | task reminders | nie | nie | nie | nie | task reminder operational state |
| `task_reminder_worker_heartbeats` | `can_rebuild` | `warning` | task reminders | nie | nie | tak | nie | none |
| `google_calendar_oauth_states` | `can_rebuild` | `warning` | Google Calendar OAuth | nie | tak | tak | nie | none |
| `system_email_oauth_states` | `can_rebuild` | `warning` | system email OAuth | nie | tak | tak | nie | none |
| `user_module_inbox_state` | `can_rebuild` | `warning` | module inbox | nie | nie | tak | nie | user state cleanup |

## Szczegoly decyzji

### `email_import_runs` i `email_import_items`

Tabele przechowuja historie importow e-mail i pozycje importu. Dane obejmuja adresy skrzynek, nadawcow, odbiorcow, tematy, nazwy zalacznikow, zewnetrzne identyfikatory i powiazania z fakturami.

- Zaleznosci: `organizations`, `invoices`, `email_import_runs` dla pozycji.
- Zawiera dane biznesowe klienta: tak.
- Zawiera dane wrazliwe: tak, maile i metadane wiadomosci.
- Moze byc odtworzona: nie wiarygodnie, chyba ze ponownie przetwarzamy skrzynki.
- Brak blokuje prototyp PostgreSQL: nie, faktury sa juz w migratorze.
- Decyzja: `should_migrate` jako pakiet historii/audytu importow, ale nie jako blocker prototypu.

### `ksef_import_runs` i `ksef_import_items`

Tabele przechowuja historie importow KSeF i pozycje importu, w tym identyfikator firmy, srodowisko, numery KSeF, numery faktur, NIP wystawcy i powiazania z fakturami.

- Zaleznosci: `organizations`, `invoices`, `ksef_import_runs` dla pozycji.
- Zawiera dane biznesowe klienta: tak.
- Zawiera dane wrazliwe: tak, identyfikatory dokumentow/faktur i NIP.
- Moze byc odtworzona: nie wiarygodnie bez ponownego importu i ryzyka rozjazdu historii.
- Brak blokuje prototyp PostgreSQL: nie, jesli faktury i statusy sa przeniesione.
- Decyzja: `should_migrate` jako pakiet historii/audytu importow.

### `task_reminder_outbox`, `task_reminder_outbox_attempts`, `task_reminder_worker_heartbeats`

Tabele przechowuja operacyjny stan przypomnien, historie prob wysylki i heartbeat workerow.

- Zaleznosci: `organizations`, `tasks`, `users`, `task_reminder_outbox` dla prob.
- Zawiera dane biznesowe klienta: outbox moze zawierac payload przypomnienia i Telegram ID.
- Zawiera dane wrazliwe: outbox tak, proby/heartbeat zwykle nie.
- Moze byc odtworzona: outbox i heartbeat zwykle tak, z aktualnych zadan i workerow; historia prob nie.
- Brak blokuje prototyp PostgreSQL: nie.
- Decyzja: `task_reminder_outbox` = `can_rebuild`; `task_reminder_outbox_attempts` = `can_skip_for_prototype`; `task_reminder_worker_heartbeats` = `can_rebuild`.

### `google_calendar_oauth_states` i `system_email_oauth_states`

Tabele przechowuja tymczasowe tokeny `state_token` dla flow OAuth.

- Zaleznosci: `users` dla Google Calendar i opcjonalny `created_by_user_id` dla system email.
- Zawiera dane biznesowe klienta: nie.
- Zawiera dane wrazliwe: tak, tymczasowe tokeny OAuth i `login_hint`.
- Moze byc odtworzona: tak, przez nowe rozpoczecie flow OAuth.
- Brak blokuje prototyp PostgreSQL: nie.
- Decyzja: `can_rebuild`; nie rekomenduje migrowac jako dane stale.

### `user_module_inbox_state`

Tabela przechowuje stan przeczytania/ostatnio widzianych zdarzen dla uzytkownika w module.

- Zaleznosci: `users`, `organizations`.
- Zawiera dane biznesowe klienta: nie.
- Zawiera dane wrazliwe: nie.
- Moze byc odtworzona: tak, przez reset stanu widocznosci.
- Brak blokuje prototyp PostgreSQL: nie.
- Decyzja: `can_rebuild`.

## Realne blockery

Audyt po `ui/state core` nie wskazuje juz blockerow:

```text
Blockers: 0
```

Dla prototypowego uruchomienia PostgreSQL pozostale tabele nie musza blokowac startu, jezeli swiadomie akceptujemy odbudowe stanow tymczasowych oraz odlozenie historii importow.

## Rekomendowana kolejnosc dalszych krokow

1. Kontrolny audyt gotowosci migratora przed realnym testem PostgreSQL.
2. Opcjonalny pakiet `import audit history`: `email_import_runs`, `email_import_items`, `ksef_import_runs`, `ksef_import_items`.
3. Opcjonalny pakiet `task reminder operational state`: `task_reminder_outbox`, ewentualnie `task_reminder_outbox_attempts`.
4. Nie migrowac domyslnie, tylko odbudowac: `google_calendar_oauth_states`, `system_email_oauth_states`, `task_reminder_worker_heartbeats`, `user_module_inbox_state`.

## Wniosek

Po dodaniu `ui/state core` migrator nie ma juz blockerow wedlug lokalnego audytu. Nadal nie oznacza to automatycznej gotowosci do produkcyjnej migracji: przed prawdziwa migracja potrzebny jest osobny test PostgreSQL, decyzja w sprawie historii importow i jasne potraktowanie stanow tymczasowych jako odbudowywalnych.
