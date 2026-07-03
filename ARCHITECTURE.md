# Architektura CASI Workspace — wersja bazowa produktu

Wersja: 2026-04-29  
Status: aktualna architektura bazowa produktu  
Charakter dokumentu: opis architektury aplikacji i kierunku rozwoju

---

## Status dokumentu

Ten dokument opisuje architekturę aplikacji CASI Workspace w obecnym etapie oraz kierunek jej dalszego rozwoju.

CASI Workspace nie jest makietą, jednorazowym panelem ani projektem testowym. To realna aplikacja operacyjna rozwijana etapami.

Pierwsza wersja produktu może mieć ograniczony zakres funkcji, ale powinna być projektowana tak, aby mogła stać się fundamentem produkcyjnego systemu SaaS.

Ten dokument odpowiada na pytanie:

> Jak aplikacja jest zbudowana i w jakim kierunku ma się rozwijać?

Instrukcje pracy dla Codexa, zasady edycji kodu i sposób podejścia do projektu są opisane w `AGENTS.md`.

---

## Ważne rozróżnienie: obecne vs kierunkowe

Nie wszystkie elementy opisane w tym dokumencie muszą być już wdrożone.

Dokument opisuje trzy rodzaje informacji:

### 1. Obecna implementacja

Elementy, które już istnieją albo są częścią aktualnego działającego systemu.

### 2. Kierunek rozwoju

Elementy, które nie muszą być jeszcze wdrożone, ale powinny być brane pod uwagę przy rozwoju aplikacji.

### 3. Zasady architektoniczne

Reguły, które mają chronić projekt przed chaosem, utratą spójności, problemami bezpieczeństwa i trudną migracją w przyszłości.

Jeżeli Codex lub developer widzi element oznaczony jako kierunek rozwoju, nie powinien zakładać automatycznie, że dana tabela, funkcja albo moduł już istnieje w kodzie.

---

# 1. Cel systemu

CASI Workspace ma być praktycznym panelem operacyjnym dla firmy i klientów.

System ma pomagać w zarządzaniu:

- fakturami,
- dokumentami,
- zadaniami,
- wydarzeniami,
- przypomnieniami,
- notatkami,
- bazą wiedzy organizacji,
- rozliczeniami,
- automatyzacjami,
- przyszłymi modułami AI.

Obecny zakres wersji bazowej obejmuje:

- obsługę faktur,
- moduł `Asystent Szefa` do zadań, wydarzeń, przypomnień i notatek,
- moduł `Asystent Firmowy` do bazy wiedzy organizacji i odpowiadania na pytania na podstawie dokumentów,
- fundament pod moduł rozliczeń klientów z importem wyciągów bankowych.

Architektura ma pozwolić na bezpieczną rozbudowę pod:

- wielu użytkowników,
- wiele organizacji,
- klientów zewnętrznych,
- Telegram,
- Make.com,
- e-mail,
- KSeF,
- OCR,
- AI,
- wdrożenie serwerowe,
- przyszły model SaaS.

---

# 2. Pozycja w ekosystemie

CASI Workspace jest projektowane jako osobny produkt, ale gotowy do pracy w większym ekosystemie kilku aplikacji produktowych.

Oznacza to:

- własny frontend,
- własny UX,
- własną logikę domenową,
- własne moduły operacyjne,
- gotowość do wspólnego fundamentu dla kont, organizacji, ról, capability, sesji, storage i audit logu,
- brak sztucznego łączenia wszystkich przyszłych produktów w jedną zakładkę lub jeden wielki kombajn.

CASI Workspace może w przyszłości współdzielić część infrastruktury z innymi aplikacjami, ale samo powinno pozostać logicznie oddzielnym produktem.

---

# 3. Główne zasady architektury

Architektura CASI Workspace powinna wspierać:

- szybki rozwój działającego produktu,
- późniejszą rozbudowę bez przepisywania wszystkiego od zera,
- przejście na produkcyjny stack,
- rozbudowę o kolejne moduły,
- separację danych organizacji,
- kontrolę kosztów automatyzacji i AI,
- integracje zewnętrzne,
- audytowalność działań,
- łatwiejsze debugowanie błędów,
- możliwość późniejszej zmiany hostingu, storage lub dostawcy AI.

Najważniejsza zasada:

> Budujemy konkretną aplikację produkcyjną etapami. Wersja bazowa ma być prosta, ale nie prowizoryczna.

Nie należy przesadnie komplikować pierwszej wersji produktu, ale należy unikać rozwiązań, które tworzą oczywiste ślepe uliczki architektoniczne.

---

# 4. Aktualny stan i kierunek docelowy

## Aktualna implementacja

Status: obecna implementacja.

Obecna implementacja działa głównie w Pythonie.

Aktualna struktura opiera się na podziale na:

- API,
- repozytoria,
- serwisy,
- integracje,
- lokalny magazyn plików,
- obecny panel webowy w `static/`.

Ta implementacja jest działającym fundamentem produktu i źródłem obecnej logiki biznesowej.

## Kierunek docelowy

Status: kierunek rozwoju.

Docelowy kierunek rozwoju aplikacji może obejmować:

- frontend: `React / Next.js`,
- produkcyjny frontend w katalogu `frontend/`,
- bazę danych: `PostgreSQL`,
- uporządkowaną warstwę API,
- backend w `Node.js` albo dalszy rozwój backendu w `Pythonie`, zależnie od praktycznej decyzji technicznej,
- ORM lub warstwę dostępu do danych dobraną do wybranego backendu,
- zewnętrzny storage plików,
- kolejki zadań,
- system powiadomień,
- modułową warstwę AI i OCR.

Na ten moment najważniejsze nie jest sztywne przywiązanie do jednego stacku, tylko utrzymanie czystego podziału na:

- API,
- serwisy,
- repozytoria,
- integracje,
- frontend,
- storage,
- joby,
- logi.

---

# 5. Warstwy aplikacji

## `app/api`

Status: obecna implementacja / zasada architektoniczna.

Warstwa HTTP i API JSON.

Odpowiada za:

- logowanie,
- sesje użytkownika,
- kontrolę uprawnień,
- zakres organizacji,
- przekazywanie zadań do serwisów,
- blokadę dostępu do plików innych organizacji,
- endpointy dla modułów aplikacji,
- publiczny webhook Telegram dla faktur.

Główny punkt wejścia:

- `app/api/http_server.py`

Warstwa API nie powinna zawierać ciężkiej logiki biznesowej.

Jej rolą jest:

- przyjąć żądanie,
- sprawdzić dostęp,
- sprawdzić organizację,
- przekazać pracę do odpowiedniego serwisu,
- zwrócić odpowiedź klientowi.

---

## `app/repositories`

Status: obecna implementacja / zasada architektoniczna.

Warstwa dostępu do danych.

Repozytoria wykonują odczyt i zapis do bazy, ale nie powinny zawierać głównej logiki biznesowej.

Najważniejsze repozytoria:

- `organization_repository.py`
- `user_repository.py`
- `invoice_repository.py`
- `contractor_repository.py`
- `event_repository.py`
- `calendar_repository.py`
- `task_repository.py`
- `knowledge_repository.py`
- `billing_repository.py`

Zasada:

> Repozytorium wie, jak zapisać i odczytać dane, ale nie decyduje biznesowo, co te dane znaczą.

---

## `app/services`

Status: obecna implementacja / zasada architektoniczna.

Warstwa logiki biznesowej.

Serwisy odpowiadają za reguły działania systemu, przepływy, walidacje i decyzje biznesowe.

Najważniejsze serwisy:

- `auth_service.py` — logowanie i konta,
- `organization_service.py` — organizacje i zakres danych,
- `invoice_service.py` — faktury, OCR, pliki, ręczna edycja,
- `duplicate_detector.py` — reguły duplikatów,
- `dashboard_service.py` — dane pulpitu,
- `notification_service.py` — przygotowanie komunikatów o duplikatach,
- `calendar_service.py` — prywatne feedy Google Calendar i ustawienia przypomnień użytkownika,
- `task_service.py` — zadania, notatki, historia zmian,
- `knowledge_service.py` — baza wiedzy organizacji, pipeline importu, OCR, wersjonowanie i odpowiedzi z cytowaniami,
- `storage_service.py` — zapis i odczyt plików przez wspólną warstwę magazynu,
- `billing_service.py` — rachunki bankowe organizacji i import wyciągów CSV.

Zasada:

> Jeżeli coś jest regułą działania aplikacji, powinno mieszkać w serwisie, a nie bezpośrednio w widoku, API albo repozytorium.

---

## `app/integrations`

Status: obecna implementacja / kierunek rozwoju.

Warstwa integracji zewnętrznych.

Obecnie przygotowana głównie jako integracje testowe, wymienne lub rozwijane etapami:

- `KSeF`,
- `e-mail`,
- `Telegram`,
- `OCR`.

Telegram dla faktur ma dwa tryby:

- `import testowy` z panelu,
- prawdziwy `webhook`, który odbiera aktualizacje od bota, pobiera plik i tworzy fakturę.

Zasada:

> Integracje zewnętrzne powinny być możliwe do podmiany bez przepisywania całej logiki biznesowej.

---

## `static`

Status: obecna implementacja / frontend przejściowy.

Obecny frontend referencyjny / legacy frontend panelu webowego po polsku.

Obecnie obejmuje między innymi:

- pulpit,
- faktury,
- `Asystent Szefa`,
- `Asystent Firmowy`,
- kontrahentów,
- historię systemu,
- organizacje,
- użytkowników.

Ten katalog jest źródłem obecnego działania aplikacji, ale nie jest docelowym frontendem produkcyjnym.

`static/` należy traktować jako:

- działającą obecną implementację,
- źródło istniejących zachowań,
- punkt odniesienia dla logiki i UX,
- etap przejściowy przed produkcyjnym frontendem.

Nie należy mieszać `static/` z docelowym frontendem produkcyjnym.

---

## `frontend`

Status: kierunek docelowy.

Docelowy frontend produkcyjny powinien powstawać w katalogu `frontend/` jako aplikacja `React / Next.js`.

Docelowy frontend powinien mieć:

- wspólny AppShell,
- centralną konfigurację nawigacji,
- modułową strukturę funkcji,
- wspólne komponenty UI,
- czystą warstwę komunikacji z API,
- możliwość rozbudowy o kolejne moduły.

Legacy `static/` nie powinno być mieszane z produkcyjnym frontendem.

---

# 6. Frontend docelowy

Status: kierunek docelowy / zasada architektoniczna.

Docelowy frontend CASI Workspace powinien być zbudowany jako nowoczesna aplikacja SaaS.

Główne założenia:

- jeden wspólny AppShell,
- lewy sidebar jako główna nawigacja,
- topbar jako pasek kontekstowy,
- moduły renderowane w głównym obszarze treści,
- spójne komponenty UI,
- centralna konfiguracja nawigacji,
- gotowość na wiele modułów i uprawnienia.

Główne moduły kierunkowe:

- `Pulpit`,
- `Faktury`,
- `Asystent Szefa`,
- `Asystent Firmowy`,
- `Dokumenty`,
- `Kasa`,
- `CRM`,
- `Raporty`,
- `Ustawienia`.

Frontend powinien być projektowany tak, aby nowe moduły można było dodawać bez przepisywania całego układu aplikacji.

---

# 7. Model danych

## `organizations`

Status: obecna implementacja / fundament systemu.

Organizacje są podstawową jednostką separacji danych.

Pola:

- `organization_id`
- `name`
- `slug`
- `is_active`
- `created_at`
- `updated_at`

Zasada:

> Większość danych biznesowych powinna być przypisana do organizacji.

---

## `users`

Status: obecna implementacja.

Użytkownicy systemu.

Pola:

- `user_id`
- `login`
- `display_name`
- `telegram_user_id`
- `organization_id`
- `password_hash`
- `password_salt`
- `role`
- `telegram_reminders_enabled`
- `reminder_quiet_hours_start`
- `reminder_quiet_hours_end`
- `reminder_repeat_interval_minutes`
- `is_active`
- `last_login_at`
- `created_by_user_id`
- `created_at`
- `updated_at`

Obecna implementacja może zakładać jedną organizację dla użytkownika przez `users.organization_id`.

Docelowo, dla pełnego modelu SaaS, warto rozważyć osobną tabelę członkostwa użytkowników w organizacjach.

---

## `organization_memberships`

Status: kierunek rozwoju, niekoniecznie obecna implementacja.

Docelowa tabela członkostwa użytkowników w organizacjach.

Nie musi być wdrażana natychmiast, ale architektura nie powinna zamykać tej możliwości.

Przykładowe pola:

- `organization_membership_id`
- `organization_id`
- `user_id`
- `role`
- `is_active`
- `created_at`
- `updated_at`

Dzięki temu jeden użytkownik mógłby w przyszłości należeć do wielu organizacji z różnymi rolami i uprawnieniami.

---

## `user_capabilities`

Status: obecna implementacja / kierunek rozwoju.

Jawne uprawnienia do modułów i akcji, niezależne od samej roli.

Pola:

- `user_capability_id`
- `user_id`
- `capability_code`
- `granted_at`

Capability pozwalają precyzyjnie kontrolować dostęp do funkcji, na przykład:

- `knowledge.read`
- `knowledge.upload`
- `knowledge.sync`
- `knowledge.manage`
- `invoices.read`
- `invoices.manage`
- `tasks.read`
- `tasks.manage`
- `billing.read`
- `billing.manage`

---

## `user_calendars`

Status: obecna implementacja.

Nazwane kalendarze użytkownika do synchronizacji z Google Calendar przez prywatny adres `.ics`.

Pola:

- `user_calendar_id`
- `owner_user_id`
- `provider`
- `display_name`
- `description`
- `sync_token`
- `is_active`
- `created_at`
- `updated_at`

Przykłady nazwanych kalendarzy:

- `Firma A`
- `Firma B`
- `Rodzinny`
- `Prywatny`
- `Misja Robotyka`
- `CASI`

---

## `contractors`

Status: obecna implementacja.

Kontrahenci organizacji.

Pola:

- `contractor_id`
- `organization_id`
- `name`
- `nip`
- `email`
- `phone`
- `is_new`
- `last_invoice_date`
- `last_invoice_number`
- `invoice_count`
- `notes`
- `created_at`
- `updated_at`

Unikalność w obrębie organizacji:

- `organization_id + nip`

Kontrahenci powinni być wykorzystywani nie tylko jako książka adresowa, ale też jako pomoc w:

- rozpoznawaniu faktur,
- wykrywaniu duplikatów,
- historii współpracy,
- przyszłej automatyzacji płatności i kosztów.

---

## `invoices`

Status: obecna implementacja / kierunek rozwoju.

Główna tabela faktur.

Pola:

- `id`
- `organization_id`
- `incoming_date`
- `source`
- `authoritative_source`
- `file_name`
- `document_type`
- `invoice_number`
- `ksef_number`
- `issuer_nip`
- `issuer_name`
- `issue_date`
- `sale_date`
- `gross_amount`
- `currency`
- `status`
- `duplicate_type`
- `flag_reason`
- `contractor_id`
- `file_link`
- `ocr_link`
- `file_storage_key`
- `ocr_storage_key`
- `storage_backend`
- `source_external_id`
- `source_sender_name`
- `source_sender_id`
- `source_metadata`
- `invoice_hash`
- `ocr_raw_text`
- `ocr_confidence`
- `notes`
- `created_at`
- `updated_at`

Pole `source` oznacza źródło dodania rekordu, na przykład:

- `KSeF`,
- `EMAIL`,
- `TELEGRAM`,
- `UPLOAD`,
- `MANUAL`.

Pole `authoritative_source` oznacza źródło, które biznesowo jest nadrzędne dla danych faktury.

Przykład:

- faktura mogła zostać dodana z Telegrama,
- OCR odczytał dane z dokumentu,
- później KSeF zwrócił oficjalną wersję,
- źródłem nadrzędnym staje się `KSeF`.

---

## `invoice_relations`

Status: kierunek rozwoju, niekoniecznie obecna implementacja.

Relacje podobieństwa i duplikatów między fakturami.

Przykładowe zastosowania:

- pewny duplikat,
- podejrzenie duplikatu,
- podobna faktura,
- rekord wstępny połączony później z fakturą z KSeF.

Przyszłościowo tabela może zawierać:

- `invoice_relation_id`
- `organization_id`
- `source_invoice_id`
- `target_invoice_id`
- `relation_type`
- `confidence`
- `reason`
- `created_at`

---

## `event_logs`

Status: obecna implementacja / kierunek rozwoju.

Ogólna historia systemowa dla wielu modułów.

Obecnie może zawierać pola powiązane z fakturami, ale docelowo powinna obsługiwać wiele typów obiektów.

Pola obecne lub kierunkowe:

- `id`
- `organization_id`
- `event_time`
- `event_type`
- `entity_type`
- `entity_id`
- `invoice_id`
- `source`
- `status_before`
- `status_after`
- `decision_reason`
- `actor`
- `details`

Docelowo preferowane jest użycie:

- `entity_type`
- `entity_id`

zamiast powiązania logów tylko z `invoice_id`.

Przykłady `entity_type`:

- `invoice`,
- `task`,
- `knowledge_document`,
- `billing_transaction`,
- `organization`,
- `user`,
- `integration`.

`invoice_id` może zostać tymczasowo dla zgodności z obecną implementacją, ale ogólny kierunek to log systemowy obsługujący wiele modułów.

---

## `knowledge_documents`

Status: obecna implementacja / kierunek rozwoju.

Główny rejestr dokumentów bazy wiedzy organizacji.

Pola:

- `knowledge_document_id`
- `organization_id`
- `title`
- `file_name`
- `mime_type`
- `file_link`
- `file_storage_key`
- `content_text`
- `content_hash`
- `char_count`
- `source_type`
- `processing_status`
- `processing_error`
- `current_version_number`
- `last_processed_at`
- `processing_started_at`
- `created_by_user_id`
- `created_at`
- `updated_at`

---

## `knowledge_document_versions`

Status: obecna implementacja / kierunek rozwoju.

Historia kolejnych wersji treści dokumentu po przetworzeniu.

Pola:

- `knowledge_document_version_id`
- `knowledge_document_id`
- `organization_id`
- `version_number`
- `content_text`
- `content_hash`
- `char_count`
- `source_type`
- `extraction_method`
- `created_by_user_id`
- `created_at`

---

## `knowledge_processing_jobs`

Status: obecna implementacja / kierunek rozwoju.

Kolejka przetwarzania importu i ponownego przetwarzania dokumentów.

Pola:

- `knowledge_processing_job_id`
- `organization_id`
- `knowledge_document_id`
- `job_type`
- `status`
- `source_storage_key`
- `source_file_name`
- `source_mime_type`
- `source_type`
- `source_content_hash`
- `supplemental_text`
- `error_message`
- `attempts`
- `max_attempts`
- `created_by_user_id`
- `started_at`
- `finished_at`
- `created_at`
- `updated_at`

Statusy przetwarzania:

- `queued`
- `processing`
- `ready`
- `error`

---

## `tasks`

Status: obecna implementacja.

Główny obiekt modułu `Asystent Szefa`.

Pola:

- `task_id`
- `organization_id`
- `task_type`
- `visibility_scope`
- `owner_user_id`
- `title`
- `description`
- `status`
- `priority`
- `due_at`
- `remind_at`
- `assigned_user_id`
- `calendar_id`
- `calendar_duration_minutes`
- `created_by_user_id`
- `reminder_sent_at`
- `reminder_last_attempt_at`
- `reminder_last_error`
- `completed_at`
- `created_at`
- `updated_at`

Typy:

- `zadanie`
- `wydarzenie`
- `przypomnienie`
- `notatka`

Statusy:

- `nowe`
- `w_toku`
- `oczekuje`
- `zakonczone`
- `anulowane`

Priorytety:

- `niski`
- `normalny`
- `wysoki`
- `krytyczny`

---

## `task_notes`

Status: obecna implementacja.

Notatki do zadania.

Pola:

- `task_note_id`
- `task_id`
- `organization_id`
- `note_text`
- `created_by_user_id`
- `created_at`

---

## `task_history`

Status: obecna implementacja.

Historia zmian zadania.

Pola:

- `task_history_id`
- `task_id`
- `organization_id`
- `action_type`
- `actor`
- `message`
- `details`
- `created_at`

Zmiany w zadaniach powinny być zapisywane zarówno w `task_history`, jak i w ogólnym `event_logs`, jeżeli mają znaczenie systemowe.

---

## `task_shares`

Status: kierunek rozwoju, niekoniecznie obecna implementacja.

Tabela do udostępniania zadań, notatek, wydarzeń i przypomnień wybranym użytkownikom.

Nie musi być wdrożona natychmiast, ale jest potrzebna, jeżeli aplikacja ma obsługiwać udostępnianie wpisów konkretnym osobom.

Przykładowe pola:

- `task_share_id`
- `task_id`
- `organization_id`
- `user_id`
- `permission_level`
- `created_by_user_id`
- `created_at`

Przykłady `permission_level`:

- `read`
- `comment`
- `edit`

---

## `billing_bank_accounts`

Status: obecna implementacja / kierunek rozwoju.

Rachunki bankowe organizacji do importu wyciągów.

Pola:

- `billing_bank_account_id`
- `organization_id`
- `account_name`
- `bank_name`
- `iban`
- `currency`
- `is_active`
- `created_at`
- `updated_at`

---

## `billing_statement_imports`

Status: obecna implementacja / kierunek rozwoju.

Rejestr importów wyciągów bankowych.

Pola:

- `billing_statement_import_id`
- `organization_id`
- `billing_bank_account_id`
- `source_type`
- `source_file_name`
- `imported_by_user_id`
- `imported_at`
- `row_count`
- `imported_transaction_count`
- `skipped_transaction_count`
- `status`
- `notes`
- `created_at`
- `updated_at`

---

## `billing_transactions`

Status: obecna implementacja / kierunek rozwoju.

Znormalizowane transakcje z wyciągów bankowych.

Pola:

- `billing_transaction_id`
- `organization_id`
- `billing_bank_account_id`
- `billing_statement_import_id`
- `booking_date`
- `value_date`
- `amount`
- `currency`
- `direction`
- `counterparty_name`
- `counterparty_account`
- `title`
- `reference`
- `raw_data`
- `transaction_hash`
- `matched_status`
- `created_at`
- `updated_at`

Przyszłościowo transakcje będą mogły być dopasowywane do:

- klientów,
- należności,
- faktur,
- abonamentów,
- sald,
- dokumentów rozliczeniowych.

---

# 8. Organizacje i zakres danych

Status: zasada architektoniczna.

To jest jedna z najważniejszych zasad architektury dla wersji klienckiej.

Zasady:

- użytkownik organizacji widzi tylko swoje dane,
- administrator organizacji działa tylko w swojej organizacji,
- administrator globalny może zarządzać wieloma organizacjami,
- pliki i OCR są rozdzielone na poziomie katalogów lub kluczy organizacji,
- baza wiedzy, kolejka dokumentów i wersje dokumentów są odseparowane organizacjami,
- zadania, notatki i historia zadań są odseparowane organizacjami,
- faktury, kontrahenci i rozliczenia są odseparowane organizacjami.

Zakres organizacji powinien być sprawdzany:

- przy listowaniu faktur,
- przy pobieraniu szczegółów faktur,
- przy kontrahentach,
- przy logach,
- przy zadaniach,
- przy notatkach do zadań,
- przy dokumentach bazy wiedzy,
- przy pytaniach do Asystenta Firmowego,
- przy imporcie dokumentów,
- przy otwieraniu plików z dysku,
- przy imporcie wyciągów bankowych,
- przy integracjach zewnętrznych.

Zasada:

> Brak sprawdzenia organizacji to potencjalny błąd bezpieczeństwa.

---

# 9. Uprawnienia i capability

Status: obecna implementacja / kierunek rozwoju.

System używa ról, ale docelowo nie powinien opierać się wyłącznie na roli użytkownika.

Role są dobre do ogólnego poziomu dostępu, ale capability pozwalają precyzyjnie sterować funkcjami.

Przykład:

Użytkownik może być zwykłym pracownikiem, ale mieć dostęp tylko do:

- odczytu bazy wiedzy,
- dodawania zadań,
- przeglądania własnych przypomnień.

Inny użytkownik może mieć dostęp do:

- zarządzania fakturami,
- importu dokumentów,
- konfiguracji integracji,
- przeglądania logów.

Przyszłościowo capability mogą obsługiwać:

- moduły,
- akcje,
- limity,
- pakiety,
- funkcje premium,
- dostęp testowy.

---

# 10. Logika duplikatów faktur

Status: obecna implementacja / zasada biznesowa.

## Pewny duplikat

Jeżeli w tej samej organizacji istnieje już faktura z takim samym `ksef_number`, nowa faktura dostaje:

- `duplicate_type = pewny`
- `status = pewny_duplikat`

To jest duplikat wysokiej pewności.

Komunikat dla użytkownika powinien zawierać konkretny powód, na przykład:

- numer KSeF,
- ID istniejącej faktury,
- numer wiersza lub rekord źródłowy, jeżeli dotyczy.

---

## Podejrzenie duplikatu

Jeżeli w tej samej organizacji zgadza się:

- `invoice_number`
- `issuer_nip`

to faktura dostaje:

- `duplicate_type = podejrzenie`
- `status = podejrzenie_duplikatu`

System nie powinien automatycznie usuwać ani blokować takiej faktury.

Powinien oznaczyć ją do ręcznej weryfikacji i pokazać użytkownikowi powód.

---

## Przyszłościowe reguły podobieństwa

Status: kierunek rozwoju.

W przyszłości można dodać także reguły miękkiego podobieństwa, na przykład:

- podobna kwota,
- ten sam kontrahent,
- podobna data,
- podobny numer faktury,
- podobny plik,
- podobny hash dokumentu.

Takie reguły powinny być traktowane jako podejrzenie, a nie pewny duplikat.

---

# 11. Nadrzędność źródeł danych

Status: zasada biznesowa / kierunek rozwoju.

Źródła danych faktury mogą mieć różny poziom wiarygodności.

Ogólna zasada:

- `KSeF` jest źródłem nadrzędnym dla danych faktury,
- `EMAIL` i `TELEGRAM` mogą zapisać rekord wstępny i dokument źródłowy,
- `UPLOAD` i `MANUAL` mogą służyć do ręcznego dodawania lub uzupełniania danych,
- jeżeli później pojawi się dopasowana faktura z `KSeF`, system może zaktualizować istniejący rekord danymi z `KSeF`.

W rekordzie przechowywane jest `authoritative_source`, żeby było widać, które źródło wygrywa biznesowo.

Przykład:

- faktura dodana przez Telegram tworzy rekord wstępny,
- OCR odczytuje dane z dokumentu,
- później KSeF zwraca oficjalną wersję,
- rekord zostaje zaktualizowany,
- `authoritative_source = KSeF`.

---

# 12. KSeF i model sprawdzania faktur

Status: kierunek produktu / zasada kontroli kosztów.

Dla wersji bazowej produktu preferowany jest model sprawdzania KSeF na żądanie, o ile aktualne zadanie nie wymaga automatyzacji cyklicznej.

Założenie wersji bazowej:

- użytkownik może kliknąć przycisk typu `Sprawdź KSeF teraz`,
- system uruchamia sprawdzanie KSeF dopiero po akcji użytkownika,
- automatyczne sprawdzanie KSeF nie jest wymagane jako domyślne zachowanie pierwszej wersji produktu.

Automatyczne sprawdzanie KSeF może zostać dodane później jako:

- funkcja wyższego pakietu,
- zaplanowana automatyzacja raz dziennie,
- częstsza automatyzacja dla klientów premium,
- konfigurowalne zadanie w tle.

Nie należy zakładać, że KSeF musi być sprawdzany co godzinę od pierwszej wersji.

Ten model pomaga ograniczyć koszty i niepotrzebne operacje.

---

# 13. Kontrola kosztów automatyzacji

Status: zasada architektoniczna / zasada produktowa.

System nie powinien domyślnie zakładać, że każda automatyzacja działa stale i z wysoką częstotliwością.

Preferowany model kontroli kosztów:

- akcje na żądanie tam, gdzie to wystarczy,
- kolejki zadań dla operacji cięższych kosztowo,
- różne częstotliwości pracy zależnie od pakietu klienta,
- stopniowe zmniejszanie intensywności automatyzacji zamiast brutalnego wyłączania funkcji,
- możliwość opóźniania zadań niskiego priorytetu,
- statusy przetwarzania widoczne dla użytkownika,
- priorytetyzacja ważniejszych operacji.

Przykłady:

- KSeF w wersji bazowej może działać na przycisk,
- OCR może trafiać do kolejki,
- synchronizacja dokumentów może działać rzadziej dla tańszych pakietów,
- zadania niskiego priorytetu mogą być przetwarzane później,
- automatyczne sprawdzanie może działać raz dziennie zamiast stale.

Zasada:

> Lepiej stopniowo zmniejszać intensywność pracy systemu niż brutalnie wyłączać ważne funkcje.

---

# 14. Asystent Firmowy — logika produktu

Status: obecna implementacja / kierunek rozwoju.

Moduł wiedzy jest osobną funkcją produktową tej aplikacji i kandydatem do wspólnego fundamentu ekosystemu.

Najważniejsze elementy:

- oddzielna zakładka i osobny UX dla pracy na bazie wiedzy,
- osobna baza wiedzy dla każdej organizacji,
- capability zamiast samej roli,
- import plików do folderu organizacji albo przez formularz,
- asynchroniczna kolejka przetwarzania dokumentów,
- wersjonowanie treści dokumentu po każdym przetworzeniu,
- OCR dla obrazów,
- odczyt tekstu z `TXT`, `DOCX`, `XLSX`, `PDF`,
- odpowiedzi z cytowaniem dokumentu, wersji i linkiem do źródła.

Przykładowe capability:

- `knowledge.read`
- `knowledge.upload`
- `knowledge.sync`
- `knowledge.manage`

Statusy dokumentu:

- `queued`
- `processing`
- `ready`
- `error`

Asystent Firmowy powinien odpowiadać tylko na podstawie danych dostępnych dla danej organizacji i danego użytkownika.

---

# 15. AI i OCR

Status: kierunek rozwoju / zasada architektoniczna.

AI oraz OCR powinny być obsługiwane przez osobną warstwę usługową.

Aplikacja nie powinna zakładać na sztywno jednego dostawcy AI lub OCR.

Możliwe źródła i narzędzia:

- OpenAI,
- Make AI,
- zewnętrzne OCR,
- lokalne parsowanie dokumentów,
- przyszłościowo DigitalOcean AI lub inne usługi.

Preferencje:

- wywołania AI powinny przechodzić przez warstwę serwisów,
- prompt, model i provider powinny być konfigurowalne,
- kosztowne operacje AI powinny być możliwe do logowania,
- odpowiedzi Asystenta Firmowego powinny zawierać cytowania źródeł,
- system powinien zapisywać status przetwarzania dokumentów i błędy,
- AI nie powinno omijać kontroli uprawnień organizacji.

DigitalOcean AI może być w przyszłości rozważany jako element infrastruktury AI, ale nie jest obecnie ostatecznym wyborem architektury.

---

# 16. Asystent Szefa — logika produktu

Status: obecna implementacja / kierunek rozwoju.

Na obecnym etapie moduł zadań działa jako osobna część tej samej aplikacji, a nie osobna aplikacja.

Obsługiwane akcje:

- utworzenie zadania,
- zmiana typu,
- zmiana statusu,
- zmiana priorytetu,
- zmiana terminu,
- zmiana osoby przypisanej,
- zmiana zakresu widoczności wpisu,
- ustawienie osobnego terminu przypomnienia,
- przypisanie wpisu do jednego z nazwanych kalendarzy Google użytkownika,
- oznaczenie jako zakończone,
- dodanie notatki,
- historia zmian.

Najważniejsze zasady:

- zadanie zawsze należy do organizacji,
- wpis może być prywatny i widoczny tylko dla właściciela,
- wpis może być udostępniony wybranym osobom z tej samej organizacji,
- wpis może być widoczny dla całej organizacji,
- zadanie można przypisać tylko do aktywnego użytkownika tej samej organizacji,
- zadanie lub wydarzenie może mieć osobną godzinę przypomnienia,
- zadanie lub wydarzenie może być wpisane do prywatnego kalendarza Google wybranego przez użytkownika,
- przypomnienie nie może być ustawione później niż termin zadania,
- notatka do zadania należy do tej samej organizacji,
- zmiany są zapisywane w `task_history`,
- ważne zmiany mogą być zapisywane także w ogólnym `event_logs`.

---

# 17. Synchronizacja Google Calendar

Status: obecna implementacja / kierunek rozwoju.

Synchronizacja Google Calendar w obecnej wersji działa przez prywatne feedy `.ics`.

Założenia:

- każdy użytkownik może mieć kilka nazwanych kalendarzy,
- aplikacja generuje prywatny feed `.ics` dla każdego kalendarza,
- Google Calendar subskrybuje ten adres przez `Z adresu URL`,
- synchronizacja jest jednokierunkowa: `aplikacja -> Google Calendar`.

Przykłady kalendarzy:

- `Firma A`,
- `Firma B`,
- `Rodzinny`,
- `Misja Robotyka`,
- `CASI`.

Przyszłościowo można rozważyć głębszą integrację z Google Calendar API, ale obecny model `.ics` jest prostszy i wystarczający dla pierwszej wersji produktu.

---

# 18. Moduł rozliczeń i import wyciągów bankowych

Status: obecna implementacja / kierunek rozwoju.

Moduł rozliczeń jest fundamentem pod przyszłe zarządzanie płatnościami klientów.

Obecny zakres:

- rachunki bankowe organizacji,
- import wyciągów CSV,
- normalizacja transakcji,
- rejestr importów,
- przygotowanie pod dopasowanie wpłat.

Przyszłościowy zakres:

- baza klientów organizacji,
- identyfikator płatności klienta,
- dopasowanie wpłat z wyciągów do należności,
- saldo klienta,
- dokumenty rozliczeniowe,
- automatyczne wykrywanie nieopłaconych należności,
- powiadomienia o zaległościach,
- raporty płatności.

Na start identyfikatorem płatności może być na przykład numer telefonu lub inny prosty identyfikator w tytule przelewu.

---

# 19. Magazyn plików

Status: obecna implementacja / kierunek rozwoju.

Pliki są zapisywane osobno dla każdej organizacji.

Obecnie działa lokalny backend magazynu, ale zapis przechodzi przez osobną warstwę usługową.

To oznacza, że:

- aplikacja nie powinna opierać się wyłącznie na zwykłych ścieżkach folderów,
- każdy artefakt powinien mieć `storage_backend`,
- każdy artefakt powinien mieć własny klucz magazynu,
- późniejsza podmiana lokalnego dysku na zewnętrzny magazyn plików będzie prostsza.

Przykładowy układ:

```text
data/
  magazyn/
    dokumenty/
      organizacje/
        organizacja-domyslna/
          TELEGRAM/
          EMAIL/
          KSeF/
        klient-beta/
          TELEGRAM/
          EMAIL/
    ocr/
      organizacje/
        organizacja-domyslna/
        klient-beta/
```

Ten układ daje:

- porządek na dysku,
- prostszą kontrolę dostępu do plików,
- łatwiejszą przyszłą migrację na magazyn zewnętrzny,
- separację danych organizacji.

Przyszłościowo storage może zostać przeniesiony do zewnętrznej usługi, na przykład object storage.

---

# 20. Make.com i zewnętrzne automatyzacje

Status: obecna możliwość / kierunek rozwoju.

Make.com może być używany praktycznie jako warstwa integracji i automatyzacji.

Może obsługiwać:

- eksperymenty,
- workflow pierwszej wersji produktu,
- Telegram,
- e-mail,
- powiadomienia,
- integracje zewnętrzne,
- szybkie prototypowanie,
- automatyzacje specyficzne dla klienta.

Długoterminowa preferencja:

- aplikacja powinna posiadać własny model danych,
- aplikacja powinna posiadać ważne stany biznesowe,
- Make.com nie powinien być jedynym trwałym miejscem całej logiki biznesowej,
- należy unikać sytuacji, w której dla każdego klienta trzeba ręcznie duplikować pełny scenariusz Make, jeżeli aplikacja może obsłużyć to centralnie.

Make.com jest wartościowym narzędziem, szczególnie dla integracji i szybkiego rozwoju.

Nie należy go automatycznie odrzucać, ale też nie należy budować całego produktu tak, aby bez Make.com nie miał własnej logiki.

---

# 21. Infrastruktura i przenośność

Status: kierunek rozwoju / zasada architektoniczna.

Architektura aplikacji powinna pozwalać na wdrożenie na różnych platformach.

Możliwe kierunki infrastruktury:

- DigitalOcean,
- Fly.io,
- Google Cloud,
- Vercel,
- inne środowiska serwerowe.

Na tym etapie żadna platforma nie jest traktowana jako ostateczny wybór.

Zasady:

- logika biznesowa nie powinna być zależna od jednego dostawcy hostingu,
- integracje infrastrukturalne powinny być izolowane w warstwie konfiguracji, adapterów albo usług,
- aplikacja powinna korzystać ze standardowych zmiennych środowiskowych,
- magazyn plików powinien być możliwy do podmiany z lokalnego dysku na zewnętrzny storage,
- baza danych powinna być możliwa do migracji na PostgreSQL,
- decyzje o hostingu, AI i storage powinny być możliwe do ponownej oceny wraz ze zmianą cen, funkcji i skali.

Nie należy jednak przesadnie komplikować pierwszej wersji produktu tylko po to, żeby uniknąć każdej możliwej zależności od dostawcy.

Przenośność jest ważna, ale praktyczny rozwój produktu również jest ważny.

---

# 22. Baza danych i migracje

Status: obecna implementacja / kierunek rozwoju.

Obecna wersja może działać na lokalnej bazie, ale kierunek produkcyjny zakłada możliwość migracji na bazę serwerową.

Preferowany kierunek produkcyjny:

- PostgreSQL.

Projekt ma już przygotowane kilka rzeczy pod późniejsze przeniesienie:

- obsługuje standardowe `DATABASE_URL`,
- może korzystać z wolumenu serwera jako domyślnego magazynu plików,
- ma gotowy skrypt `migrate_sqlite_to_configured_db.py` do przeniesienia rekordów z lokalnej `SQLite` do docelowej bazy,
- ma wspólną warstwę magazynu plików zamiast twardego zapisu bezpośrednio po folderach,
- ma organizacyjny podział danych już w modelu i API.

Migracje powinny zachowywać:

- dane organizacji,
- faktury,
- kontrahentów,
- dokumenty,
- logi,
- zadania,
- historię zmian,
- użytkowników,
- capability,
- powiązania z plikami.

---

# 23. Logowanie, audyt i wyjaśnialność

Status: zasada architektoniczna / kierunek rozwoju.

CASI Workspace powinno być projektowane z myślą o logowaniu, audycie i wyjaśnianiu decyzji systemu.

Szczególnie ważne obszary:

- faktury,
- KSeF,
- OCR,
- AI,
- dokumenty,
- zadania,
- przypomnienia,
- importy,
- integracje,
- rozliczenia,
- zmiany statusów,
- błędy przetwarzania.

Zasady:

- ważne działania automatyczne powinny mieć zapisaną przyczynę,
- decyzje AI powinny mieć krótki powód, gdy ma to znaczenie,
- kosztowne operacje powinny być możliwe do zmierzenia,
- joby w tle powinny mieć statusy,
- błędy nie powinny znikać po cichu,
- logi powinny pomagać zrozumieć, co się wydarzyło.

Przykładowe informacje w logach:

- kto wykonał akcję,
- kiedy,
- czego dotyczyła,
- jaki był stan przed,
- jaki jest stan po,
- dlaczego system podjął daną decyzję,
- czy była to akcja użytkownika, AI, automatyzacji czy integracji.

---

# 24. Bezpieczeństwo i dane wrażliwe

Status: zasada architektoniczna.

System może przetwarzać dane wrażliwe biznesowo.

Przykłady:

- faktury,
- dane klientów,
- dane kontrahentów,
- dokumenty,
- e-maile,
- pliki,
- wyciągi bankowe,
- tokeny,
- klucze API,
- dane OAuth,
- dane osobowe,
- dane finansowe.

Zasady:

- nie przechowywać sekretów w kodzie frontendu,
- nie commitować sekretów do repozytorium,
- używać zmiennych środowiskowych lub bezpiecznej konfiguracji,
- separować dane organizacji,
- ograniczać logowanie treści wrażliwych,
- kontrolować dostęp do plików,
- sprawdzać organizację przy odczycie danych,
- unikać przypadkowego udostępniania danych między klientami.

Jeżeli nie wiadomo, czy dana informacja jest wrażliwa, należy traktować ją ostrożnie.

---

# 25. Powiadomienia

Status: kierunek rozwoju.

System powinien mieć możliwość rozwoju w kierunku ogólnej warstwy powiadomień.

Obecne i przyszłe kanały:

- panel aplikacji,
- Telegram,
- e-mail,
- przyszłościowo inne kanały.

Powiadomienia mogą dotyczyć:

- duplikatów faktur,
- błędów OCR,
- nowych dokumentów,
- zadań,
- przypomnień,
- zaległych płatności,
- zakończonych importów,
- błędów integracji,
- statusów jobów.

Długoterminowo warto dążyć do uogólnionego systemu powiadomień zamiast osobnej logiki dla każdego modułu.

---

# 26. Joby, kolejki i przetwarzanie w tle

Status: kierunek rozwoju / zasada architektoniczna.

Część operacji powinna być wykonywana asynchronicznie lub w tle.

Przykłady:

- OCR,
- przetwarzanie dokumentów,
- importy bankowe,
- synchronizacja danych,
- zapytania do KSeF,
- analiza AI,
- generowanie odpowiedzi z bazy wiedzy,
- wysyłka powiadomień,
- przypomnienia.

Zasady:

- job powinien mieć status,
- job powinien mieć liczbę prób,
- błędy powinny być zapisane,
- operacje powinny być możliwe do ponowienia,
- ciężkie operacje nie powinny blokować całej aplikacji,
- operacje powinny być możliwe do priorytetyzacji.

Przykładowe statusy jobów:

- `queued`
- `processing`
- `done`
- `error`
- `cancelled`

---

# 27. Wydajność i skalowalność

Status: zasada architektoniczna / kierunek rozwoju.

Aplikacja powinna być gotowa na wzrost liczby danych.

Obszary wymagające uwagi:

- listy faktur,
- dokumenty bazy wiedzy,
- logi,
- historia zadań,
- transakcje bankowe,
- importy,
- powiadomienia.

Preferencje:

- paginacja,
- filtrowanie,
- wyszukiwanie,
- indeksy w bazie,
- unikanie pobierania wszystkiego naraz,
- oddzielenie ciężkich operacji od głównego widoku,
- cache tam, gdzie ma sens,
- kolejki dla kosztownych operacji.

Nie trzeba wdrażać wszystkiego od razu, ale struktura nie powinna wymuszać pobierania ogromnych list bez ograniczeń.

---

# 28. Błędy i obsługa awarii

Status: zasada architektoniczna.

Błędy powinny być widoczne, zrozumiałe i możliwe do diagnozy.

Zasady:

- nie ukrywać błędów,
- pokazywać użytkownikowi prosty komunikat,
- zapisywać techniczne szczegóły w logach,
- nie ujawniać użytkownikowi sekretów ani danych technicznych, które nie są mu potrzebne,
- umożliwić ponowienie operacji,
- rozróżniać błędy użytkownika, integracji i systemu.

Przykład:

Błąd OCR powinien być widoczny jako status dokumentu i zapisany w logach, ale nie powinien powodować utraty pliku źródłowego.

---

# 29. Kolejność rozwoju produktu

Status: zasada praktyczna.

Nowe moduły powinny być dodawane w sposób, który nie psuje istniejącej struktury aplikacji.

Preferowana kolejność rozwoju:

1. Ustabilizować fundament aplikacji.
2. Uporządkować produkcyjny frontend w `frontend/`.
3. Utrzymać AppShell i centralną nawigację.
4. Dopilnować separacji organizacji.
5. Dopilnować poprawnego API i uprawnień.
6. Stabilizować istniejące moduły.
7. Dopiero potem dodawać kolejne duże moduły.

Nowe moduły powinny być dodawane dopiero wtedy, gdy nie psują spójności:

- AppShella,
- API,
- uprawnień,
- separacji organizacji,
- logiki danych,
- obsługi błędów.

Nie oznacza to blokowania rozwoju. Chodzi o to, żeby każdy nowy moduł wzmacniał produkt, a nie zwiększał chaos.

---

# 30. Czego nie robić na razie

Status: zasada praktyczna.

Na obecnym etapie nie należy komplikować projektu przez:

- pełny system multi-tenant enterprise, jeżeli nie jest potrzebny do aktualnego zadania,
- rozbudowany billing SaaS, zanim podstawowe moduły działają stabilnie,
- przepisywanie całego backendu tylko dlatego, że docelowo możliwy jest inny stack,
- dodawanie wielu providerów AI, zanim jeden przepływ działa dobrze,
- budowanie automatyzacji cyklicznych tam, gdzie wystarczy akcja na żądanie,
- rozbudowywanie wszystkich modułów naraz,
- tworzenie wielu konkurencyjnych systemów nawigacji,
- mieszanie legacy `static/` z docelowym frontendem `frontend/`,
- dodawanie nowych technologii bez jasnego powodu,
- przenoszenie całej logiki do Make.com, jeżeli aplikacja powinna posiadać własny stan i model danych.

Zasada:

> Nie budować prowizorki, ale też nie budować zbyt ciężkiej architektury przedwcześnie.

---

# 31. Co warto dodać w kolejnych etapach

Status: kierunek rozwoju.

Kolejne etapy rozwoju mogą obejmować:

- produkcyjny frontend w `frontend/`,
- podział frontendu na mniejsze pliki i moduły,
- AppShell i centralną nawigację,
- bazę klientów organizacji do rozliczeń,
- identyfikator płatności klienta,
- dopasowanie wpłat z wyciągów do należności klientów,
- saldo klienta,
- dokumenty rozliczeniowe,
- załączniki do zadań,
- widok kalendarzowy,
- przypomnienia uruchamiane w tle,
- integracje Make.com,
- integrację Telegram dla modułu zadań,
- uogólniony system powiadomień,
- kolejki zadań,
- statusy jobów,
- monitoring kosztów AI,
- lepsze logi audytowe,
- role i capability w panelu,
- feature flags,
- pakiety klientów,
- limity automatyzacji zależne od planu,
- migrację na PostgreSQL,
- zewnętrzny storage plików,
- deployment produkcyjny.

---

# 32. Zasada końcowa

CASI Workspace ma być rozwijane jako realny system operacyjny dla firm.

Architektura powinna być prosta tam, gdzie to możliwe, ale gotowa na rozbudowę tam, gdzie to ważne.

Najważniejsze cele architektury:

- jasny podział warstw,
- separacja organizacji,
- bezpieczne dane,
- modułowy frontend,
- kontrola kosztów automatyzacji,
- możliwość rozwoju AI,
- możliwość integracji z Make.com, Telegramem, e-mailem i KSeF,
- przenośność infrastruktury,
- gotowość do przyszłego SaaS,
- praktyczny rozwój bez przesadnego komplikowania pierwszej wersji produktu.

Najważniejsza myśl:

> CASI Workspace ma być budowane etapami, ale każdy etap powinien przybliżać aplikację do stabilnego produktu, a nie tworzyć tymczasową prowizorkę.