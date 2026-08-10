# Operacyjne Centrum Automatyzacji — v1

## Cel i granice

Centrum pod adresem `/automatyzacje` jest wyłącznie odczytowym widokiem operacyjnym. Agreguje wiarygodny, trwały stan automatyzacji, ale nie uruchamia workerów, nie zmienia konfiguracji, nie ponawia runów i nie zastępuje mechanizmów wykonawczych.

W v1 zarejestrowany jest tylko `internal_notification_scheduler`. Jest to osobny, jawnie uruchamiany subsystem schedulerowy. Centrum nie przepina go do `automation_rules` i nie tworzy drugiego silnika wykonawczego.

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

## Świadomie odłożone źródła

- `automation_rules` i `automation_executions` pozostają istniejącym, niezależnym silnikiem event → actions. Nie mają jeszcze wspólnego kontraktu harmonogramu, następnego runu i bezpiecznej prezentacji błędów dla centrum.
- przypomnienia zadań mają rozdzielony outbox, próby i heartbeat zależny od runtime. Ich centralny kontrakt enabled wymaga jednocześnie jawnie włączonego `INVOICE_ENABLE_TELEGRAM_TASK_REMINDERS`, skonfigurowanego wysyłania Telegram oraz zgodnego providera organizacji. Flaga jest nadrzędnym kill switchem; sama obecność tokenu nie włącza mechanizmu;
- joby i watchery bazy wiedzy nie mają wspólnego, trwałego kontraktu enabled/next-run/history;
- importy e-mail i KSeF mają historie operacyjne, ale nie stanowią jednego skonfigurowanego kontraktu automatyzacji, a część stanu e-mail jest procesowa;
- samodzielne pętle i konfiguracja platformowa nie są raportowane, ponieważ bez dedykowanego źródła prawdy taki stan byłby mylący.

Dodanie tych źródeł wymaga najpierw spełnienia kontraktu adaptera. Nie wolno rozszerzać centrum przez odgadywanie stanu z logów ani przez dodawanie ukrytych write actions.

### Kontrakt runtime Task Reminders

`TaskReminderService` jest jednym źródłem prawdy dla statusu runtime. Przy wyłączonej fladze nie startują pętle scheduler/delivery, a bezpośrednie wywołania enqueue i process nie wykonują pracy. Status rozróżnia wyłączony gate, brak konfiguracji Telegram i nieobsługiwany provider organizacji; widoczność samego procesu pozostaje `unknown`.

Outbox i ograniczona historia attempts mogą w przyszłości zasilać read-only health. Heartbeat jest wyłącznie informacyjny: nie ma zdefiniowanego TTL i nie może być interpretowany jako dowód, że worker działa. Centrum nie powinno ujawniać payloadów, odbiorców ani surowych błędów i nie może dodawać retry lub run-now.

Adapter Task Reminders do Automation Operations Center wymaga tego kontraktu i będzie realizowany w osobnym etapie. Task Reminders nie są jeszcze zarejestrowane w Centrum ani przepięte do `automation_rules`.

## Bezpieczeństwo

Endpointy `/api/automations/operations` i `/api/automations/operations/{automation_key}` obsługują wyłącznie GET. Odbiorca zawsze wynika z zalogowanej sesji; parametr odbiorcy jest odrzucany. Zakres obcej organizacji zwraca bezpieczne `404`, a nie dane obcego tenant-a. Odpowiedź nie zawiera lease tokenów, stack trace, DSN, sekretów ani surowych payloadów.
