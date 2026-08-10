# Operacyjne Centrum Automatyzacji — v1

## Cel i granice

Centrum pod adresem `/automatyzacje` jest wyłącznie odczytowym widokiem operacyjnym. Agreguje wiarygodny, trwały stan automatyzacji, ale nie uruchamia workerów, nie zmienia konfiguracji, nie ponawia runów i nie zastępuje mechanizmów wykonawczych.

W v1 zarejestrowane są cztery natywne subsystemy: `internal_notification_scheduler`, `task_reminders`, `knowledge_processing` oraz `email_import`. Centrum nie przepina ich do `automation_rules` i nie tworzy drugiego silnika wykonawczego.

Identyfikatory techniczne i kod pozostają w języku angielskim. Warstwa prezentacyjna CASI Workspace używa języka polskiego.

| automation_key | Tytuł | Scope | Źródło konfiguracji | Źródło runów/historii | Źródło health | Runtime | Ustawienia | Status |
|---|---|---|---|---|---|---|---|---|
| `internal_notification_scheduler` | Automatyczne sprawdzanie powiadomień | organizacja + odbiorca | schedule settings | schedule runs | ostatni terminalny run | `unknown` | `/powiadomienia` | wdrożony |
| `task_reminders` | Przypomnienia zadań | organizacja + widoczność zadania | `TaskReminderService.runtime_contract()` | outbox + attempts | runtime gate, failed outbox i ostatnia próba | `unknown`; heartbeat historyczny | brak osobnego widoku | wdrożony read-only |
| `knowledge_processing` | Przetwarzanie bazy wiedzy | organizacja | subsystem nie ma kill-switcha; serwis jest zawsze dostępny | `knowledge_processing_jobs` + stan ostatniego skanu | ostatni terminalny job i jawny błąd skanu | `unknown`; watcher nie jest heartbeat'em | brak osobnego widoku | wdrożony read-only |
| `email_import` | Import e-maili | organizacja; jedna konfiguracja routingu na organizację | globalny `EMAIL_AUTOCHECK_ENABLED`, konfiguracja centralnej skrzynki i `organizations.email_integration_enabled` | `email_import_runs`; itemy wyłącznie jako agregaty | ostatni terminalny run i trwałe liczniki wyniku | `unknown`; pętla nie ma heartbeat/TTL/lease | `/ustawienia` | wdrożony read-only |

## Kontrakt adaptera

Każdy przyszły adapter musi mieć unikalny `automation_key` i dostarczać:

1. stabilny zakres organizacji oraz odbiorcy;
2. jawny stan konfiguracji (`enabled`, `disabled` albo `not_configured`);
3. deterministyczny stan zdrowia (`healthy`, `attention`, `never_run` albo `disabled`);
4. trwały harmonogram i następny termin, jeżeli istnieją;
5. trwałą, ograniczoną historię wykonań;
6. liczniki wyniku oraz prób bez surowych payloadów;
7. bezpiecznie zanonimizowane kody i podsumowania błędów;
8. bezpieczny wewnętrzny link do istniejących ustawień.

Lista na dashboardzie korzysta z jednego ograniczonego snapshotu na adapter. Historia jest pobierana dopiero na stronie szczegółów, maksymalnie 50 wpisów. Frontend nie stosuje pollingu; odświeżenie jest wyłącznie jawnym żądaniem GET.

## Znaczenie stanów schedulera

- `not_configured` / `disabled`: harmonogram nie istnieje;
- `disabled` / `disabled`: harmonogram istnieje, ale jest wyłączony;
- `enabled` / `never_run`: jest włączony, lecz brak zakończonego runu;
- `enabled` / `healthy`: ostatni zakończony run zakończył się sukcesem;
- `enabled` / `attention`: ostatni zakończony run zakończył się błędem.

Stan procesu workera jest prezentowany jako `unknown`. Aplikacja nie udaje monitoringu platformowego, crona ani działającego procesu, którego nie potrafi wiarygodnie zaobserwować.

## Knowledge Processing

`knowledge_processing_jobs` jest natywną kolejką przetwarzania źródeł dokumentów. Job powstaje po uploadzie, synchronizacji folderu, podmianie pliku, odtworzeniu wersji albo ręcznym reprocessie w istniejącym module wiedzy. Statusy trwałe to `pending`, `processing`, `completed` i `failed`. `attempts` rośnie przy rozpoczęciu pracy, ale obecna implementacja nie ma automatycznego retry ani dead-letter; `max_attempts` nie jest podstawą do prezentowania retry exhausted.

`knowledge_folder_watchers` przechowuje po jednym rekordzie ostatniego skanu dla organizacji. To historia skanu (`running`, `ok` albo `error`), a nie rejestr działającego procesu. Brak heartbeat'u, lease, TTL i SLA oznacza, że runtime zawsze jest `unknown`; Centrum nie pokazuje online/offline.

Health adaptera jest deterministyczny:

- `attention`, gdy ostatni terminalny job ma status `failed` albo ostatni skan ma jawny status błędu;
- `healthy`, gdy ostatni terminalny job ma status `completed` i ostatni skan nie ma błędu;
- `never_run`, gdy nie ma terminalnego joba i skan nie sygnalizuje błędu;
- `disabled` nie jest używany, ponieważ subsystem nie ma konfiguracji wyłączającej.

Dashboard pobiera stałą liczbę agregatów dla organizacji; nie pobiera historii i nie wykonuje N+1. Detail zwraca maksymalnie 50 jobów (domyślnie 20) i neutralny stan watchera. Odpowiedź nie zawiera nazw plików, storage keys, ścieżek folderów, treści dokumentów, OCR, tekstu ekstrakcji, promptów ani surowych payloadów. Błędy są sanowane wspólną funkcją Centrum.

Adapter nie skanuje folderów, nie przetwarza dokumentów i nie zmienia pipeline'u, retry, OCR, indeksowania ani storage. Nie udostępnia Retry, Reprocess, Run now, Scan now, enable/disable ani żadnej innej akcji zapisu.

`automation_rules` i `automation_executions` pozostają niezależnym silnikiem event → actions. Knowledge Processing nie jest przez niego wykonywany, a Centrum nie kopiuje jobów do `automation_executions`.

## Import e-maili

`email_import_runs` jest organizacyjną historią pojedynczych sprawdzeń centralnej skrzynki. Run może rozpocząć istniejąca ręczna akcja API albo automatyczna pętla uruchamiana w trybie `standalone`/`worker`. Trwałe statusy to `running`, `completed`, `completed_with_issues`, `no_new_documents` i `failed`. Brak nowych wiadomości jest prawidłowym sukcesem, a `completed_with_issues` wymaga uwagi.

`email_import_items` przechowuje wynik poszczególnych załączników: `imported`, `skipped_existing` albo `skipped_error`. Import nie ma własnego retry ani `max_attempts`. Deduplikacja następuje przed utworzeniem faktury przez organizacyjny `source_external_id`; źródło identyfikatora bazuje na wiadomości i załączniku. Centrum nie zmienia tych reguł.

Globalna flaga `EMAIL_AUTOCHECK_ENABLED` jest rzeczywistym kill-switchem pętli. Gotowość organizacji wymaga aktywnej organizacji, `email_integration_enabled` i skonfigurowanego adresu routingu, a gotowość systemu wymaga centralnego IMAP albo Google OAuth. Sama konfiguracja skrzynki nie włącza organizacji. Jeden tenant ma obecnie jedną konfigurację routingu korzystającą ze wspólnej skrzynki systemowej; nie istnieją tenantowe kolekcje wielu połączeń.

Health adaptera jest deterministyczny: wyłączona flaga daje `disabled`, brak konfiguracji daje `not_configured`/`disabled`, brak terminalnego runu daje `never_run`, `completed` i `no_new_documents` dają `healthy`, a `failed` i `completed_with_issues` dają `attention`. Pętla przechowuje wyłącznie procesowy stan ostatniego cyklu bez heartbeat, TTL i lease, dlatego `runtime_status` zawsze pozostaje `unknown`.

Dashboard pobiera stałą liczbę organizacyjnych agregatów i ostatni run. Detail pobiera domyślnie 20, maksymalnie 50 runów, bez pobierania itemów. API nie zwraca adresów, subject, body, Message-ID, nazw załączników, headers, credentials, tokenów, surowych `details`, payloadów ani stack trace. Historia itemów nie jest eksponowana; dostępne są tylko liczniki `imported`, `skipped_existing` i `skipped_error`. Błędy są mapowane na stałe, sanitarne komunikaty.

Importer e-mail nie jest wykonywany przez `automation_rules` ani `automation_executions`. Centrum nie kopiuje runów do generic automation engine i nie dodaje akcji import-now, retry, connect/disconnect ani enable/disable.

## Świadomie odłożone źródła

- `automation_rules` i `automation_executions` pozostają istniejącym, niezależnym silnikiem event → actions. Nie mają jeszcze wspólnego kontraktu harmonogramu, następnego runu i bezpiecznej prezentacji błędów dla centrum.
- import KSeF ma historię operacyjną, ale nie stanowi jeszcze pełnego kontraktu adaptera Centrum;
- samodzielne pętle i konfiguracja platformowa nie są raportowane, ponieważ bez dedykowanego źródła prawdy taki stan byłby mylący.

Dodanie tych źródeł wymaga najpierw spełnienia kontraktu adaptera. Nie wolno rozszerzać centrum przez odgadywanie stanu z logów ani przez dodawanie ukrytych write actions.

### Kontrakt runtime Task Reminders

`TaskReminderService` jest jednym źródłem prawdy dla statusu runtime. Przy wyłączonej fladze nie startują pętle scheduler/delivery, a bezpośrednie wywołania enqueue i process nie wykonują pracy. Status rozróżnia wyłączony gate, brak konfiguracji Telegram i nieobsługiwany provider organizacji; widoczność samego procesu pozostaje `unknown`.

Outbox i ograniczona historia attempts mogą w przyszłości zasilać read-only health. Heartbeat jest wyłącznie informacyjny: nie ma zdefiniowanego TTL i nie może być interpretowany jako dowód, że worker działa. Centrum nie powinno ujawniać payloadów, odbiorców ani surowych błędów i nie może dodawać retry lub run-now.

Adapter Task Reminders czyta wyłącznie natywne dane outbox/attempts. Nie pokazuje payloadu, treści zadania, identyfikatora Telegram odbiorcy ani surowych błędów. Heartbeat nie wpływa na health i jest prezentowany jedynie jako ostatni historyczny timestamp. Centrum nie udostępnia retry, run-now, enable/disable ani żadnego innego write path.

`automation_rules` i `automation_executions` pozostają niezależnym subsystemem event → actions; Task Reminders nie są przez niego wykonywane.

Piąty adapter musi otrzymać unikalny `automation_key`, zadeklarować scope i capabilities oraz dostarczyć read-only snapshot z deterministycznym health, limitowaną historią i sanitarnymi błędami. Musi udowodnić brak write podczas GET, izolację tenantów i brak N+1. Dodanie odbywa się wyłącznie w centralnym registry; nie wymaga modyfikowania istniejących adapterów, a frontend nie utrzymuje osobnej listy kluczy automatyzacji.

## Bezpieczeństwo

Endpointy `/api/automations/operations` i `/api/automations/operations/{automation_key}` obsługują wyłącznie GET. Odbiorca zawsze wynika z zalogowanej sesji; parametr odbiorcy jest odrzucany. Zakres obcej organizacji zwraca bezpieczne `404`, a nie dane obcego tenant-a. Odpowiedź nie zawiera lease tokenów, stack trace, DSN, sekretów ani surowych payloadów.
