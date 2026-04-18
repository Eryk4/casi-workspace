# Architektura MVP

## Cel

System ma byc prostym panelem operacyjnym dla firmy i klientow. Obecnie obejmuje trzy glowne obszary:

- obsluge faktur
- modul `Asystent Szefa` do zadan, wydarzen, przypomnien i notatek
- modul `Asystent Firmowy` do bazy wiedzy organizacji i odpowiadania na pytania na podstawie dokumentow
- fundament pod modul rozliczen klientow z importem wyciagow bankowych

Architektura ma pozwolic na bezpieczna rozbudowe pod zespol, klientow, Telegram, Make i wdrozenie serwerowe.

## Pozycja W Ekosystemie

Ta aplikacja jest projektowana jako osobny produkt, ale gotowy do pracy w wiekszym ekosystemie dwoch aplikacji produktowych.

To oznacza:

- wlasny frontend, UX i logike domenowa dla tego produktu
- gotowosc do wspolnego fundamentu dla kont, organizacji, rol, capability, sesji, storage i audit logu
- brak sztucznego laczenia wszystkiego w jedna zakladke lub jeden kombajn

## Warstwy

### `app/api`

Warstwa HTTP i API JSON. Odpowiada za:

- logowanie
- sesje uzytkownika
- kontrole uprawnien
- zakres organizacji
- przekazanie zadan do serwisow
- blokade dostepu do plikow innych organizacji
- publiczny webhook Telegram dla faktur

Glowny punkt wejscia:

- `app/api/http_server.py`

### `app/repositories`

Warstwa dostepu do danych. Repozytoria wykonuja odczyt i zapis do bazy bez logiki biznesowej.

Najwazniejsze repozytoria:

- `organization_repository.py`
- `user_repository.py`
- `invoice_repository.py`
- `contractor_repository.py`
- `event_repository.py`
- `calendar_repository.py`
- `task_repository.py`
- `knowledge_repository.py`
- `billing_repository.py`

### `app/services`

Warstwa logiki biznesowej:

- `auth_service.py` - logowanie i konta
- `organization_service.py` - organizacje i zakres danych
- `invoice_service.py` - faktury, OCR, pliki, reczna edycja
- `duplicate_detector.py` - reguly duplikatow
- `dashboard_service.py` - dane pulpitu
- `notification_service.py` - przygotowanie komunikatow o duplikatach
- `calendar_service.py` - prywatne feedy Google Calendar i ustawienia przypomnien uzytkownika
- `task_service.py` - zadania, notatki, historia zmian
- `knowledge_service.py` - baza wiedzy organizacji, pipeline importu, OCR, wersjonowanie i odpowiedzi z cytowaniami
- `storage_service.py` - zapis i odczyt plikow przez wspolna warstwe magazynu
- `billing_service.py` - rachunki bankowe organizacji i import wyciagow CSV

### `app/integrations`

Integracje testowe przygotowane do podmiany:

- `KSeF`
- `e-mail`
- `Telegram`
- `OCR`

Telegram dla faktur ma juz dwa tryby:

- `import testowy` z panelu
- prawdziwy `webhook`, ktory odbiera aktualizacje od bota, pobiera plik i tworzy fakture

### `static`

Panel webowy SPA po polsku:

- pulpit
- faktury
- `Asystent Szefa`
- `Asystent Firmowy`
- kontrahenci
- historia systemu
- organizacje
- uzytkownicy

## Model danych

### `organizations`

- `organization_id`
- `name`
- `slug`
- `is_active`
- `created_at`
- `updated_at`

### `users`

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

### `user_capabilities`

Jawne uprawnienia do modulow, niezalezne od samej roli.

- `user_capability_id`
- `user_id`
- `capability_code`
- `granted_at`

### `user_calendars`

Nazwane kalendarze uzytkownika do synchronizacji z Google Calendar przez prywatny adres `.ics`.

- `user_calendar_id`
- `owner_user_id`
- `provider`
- `display_name`
- `description`
- `sync_token`
- `is_active`
- `created_at`
- `updated_at`

### `contractors`

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

Unikalnosc w obrebie organizacji:

- `organization_id + nip`

### `invoices`

- `id`
- `organization_id`
- `incoming_date`
- `source`
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

### `invoice_relations`

Relacje podobienstwa i duplikatow miedzy fakturami.

### `event_logs`

Ogolna historia systemowa dla wielu modulow:

- `id`
- `organization_id`
- `event_time`
- `event_type`
- `invoice_id`
- `source`
- `status_before`
- `status_after`
- `decision_reason`
- `actor`
- `details`

### `knowledge_documents`

Glowny rejestr dokumentow bazy wiedzy organizacji.

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

### `knowledge_document_versions`

Historia kolejnych wersji tresci dokumentu po przetworzeniu.

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

### `knowledge_processing_jobs`

Kolejka przetwarzania importu i ponownego przetwarzania dokumentow.

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

### `tasks`

Glowny obiekt modulu `Asystent Szefa`.

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

### `task_notes`

Notatki do zadania:

- `task_note_id`
- `task_id`
- `organization_id`
- `note_text`
- `created_by_user_id`
- `created_at`

### `task_history`

Historia zmian zadania:

- `task_history_id`
- `task_id`
- `organization_id`
- `action_type`
- `actor`
- `message`
- `details`
- `created_at`

### `billing_bank_accounts`

Rachunki bankowe organizacji do importu wyciagow.

- `billing_bank_account_id`
- `organization_id`
- `account_name`
- `bank_name`
- `iban`
- `currency`
- `is_active`
- `created_at`
- `updated_at`

### `billing_statement_imports`

Rejestr importow wyciagow bankowych.

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

### `billing_transactions`

Znormalizowane transakcje z wyciagow bankowych.

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

## Organizacje i zakres danych

To jest najwazniejsza zasada architektury dla wersji klienckiej:

- uzytkownik organizacji widzi tylko swoje dane
- administrator organizacji dziala tylko w swojej organizacji
- administrator globalny moze zarzadzac wieloma organizacjami
- pliki i OCR sa rozdzielone na poziomie katalogow organizacji
- baza wiedzy, kolejka dokumentow i wersje dokumentow sa odseparowane organizacjami
- zadania, notatki i historia zadan sa rowniez odseparowane organizacjami

Zakres organizacji jest sprawdzany:

- przy listowaniu faktur
- przy pobieraniu szczegolow faktur
- przy kontrahentach
- przy logach
- przy zadaniach
- przy notatkach do zadan
- przy dokumentach bazy wiedzy
- przy pytaniach do asystenta firmowego
- przy imporcie
- przy otwieraniu plikow z dysku

## Logika duplikatow faktur

### Pewny duplikat

Jezeli w tej samej organizacji istnieje juz faktura z takim samym `ksef_number`, nowa faktura dostaje:

- `duplicate_type = pewny`
- `status = pewny_duplikat`

### Podejrzenie duplikatu

Jezeli w tej samej organizacji zgadza sie:

- `invoice_number`
- `issuer_nip`

to faktura dostaje:

- `duplicate_type = podejrzenie`
- `status = podejrzenie_duplikatu`

System nie blokuje faktury, tylko oznacza ja do recznej weryfikacji.

## Nadrzednosc zrodel danych

- `KSeF` jest zrodlem nadrzednym dla danych faktury.
- `EMAIL` i `TELEGRAM` moga zapisac rekord wstepny i dokument zrodlowy.
- Jezeli pozniej pojawi sie dopasowana faktura z `KSeF`, system aktualizuje istniejacy rekord danymi z `KSeF`.
- W rekordzie przechowywane jest `authoritative_source`, zeby bylo widac, ktore zrodlo wygrywa biznesowo.

## Asystent Firmowy - logika MVP

Modul wiedzy jest osobna funkcja produktowa tej aplikacji i zarazem kandydatem do wspolnego fundamentu ekosystemu.

Najwazniejsze elementy:

- oddzielna zakladka i osobny UX dla pracy na bazie wiedzy
- osobna baza wiedzy dla kazdej organizacji
- capability zamiast samej roli:
  - `knowledge.read`
  - `knowledge.upload`
  - `knowledge.sync`
  - `knowledge.manage`
- import plikow do folderu organizacji albo przez formularz
- asynchroniczna kolejka przetwarzania dokumentow
- statusy dokumentu:
  - `queued`
  - `processing`
  - `ready`
  - `error`
- wersjonowanie tresci dokumentu po kazdym przetworzeniu
- OCR dla obrazow i odczyt tekstu z `TXT`, `DOCX`, `XLSX`, `PDF`
- odpowiedzi z cytowaniem dokumentu, wersji i linkiem do zrodla

## Asystent Szefa - logika MVP

Na obecnym etapie modul zadan dziala jako osobna czesc tej samej aplikacji, a nie osobna aplikacja.

Obslugiwane akcje:

- utworzenie zadania
- zmiana typu, statusu, priorytetu, terminu i osoby przypisanej
- zmiana zakresu widocznosci wpisu
- ustawienie osobnego terminu przypomnienia
- przypisanie wpisu do jednego z nazwanych kalendarzy Google uzytkownika
- oznaczenie jako zakonczone
- dodanie notatki
- historia zmian

Najwazniejsze zasady:

- zadanie zawsze nalezy do organizacji
- wpis jest domyslnie prywatny i widzi go tylko wlasciciel
- wpis mozna udostepnic wybranym osobom z tej samej organizacji
- wpis mozna tez oznaczyc jako widoczny dla calej organizacji
- zadanie mozna przypisac tylko do aktywnego uzytkownika tej samej organizacji
- zadanie lub wydarzenie moze miec osobna godzine przypomnienia
- zadanie lub wydarzenie moze byc wpisane do prywatnego kalendarza Google wybranego przez uzytkownika
- przypomnienie nie moze byc ustawione pozniej niz termin zadania
- notatka do zadania rowniez nalezy do tej samej organizacji
- zmiany sa zapisywane jednoczesnie w `task_history` i w ogolnym `event_logs`

Synchronizacja Google Calendar w obecnej wersji:

- kazdy uzytkownik moze miec kilka nazwanych kalendarzy, na przyklad `Firma A`, `Firma B`, `Rodzinny`
- aplikacja generuje prywatny feed `.ics` dla kazdego kalendarza
- Google Calendar subskrybuje ten adres przez `Z adresu URL`
- synchronizacja jest jednokierunkowa `aplikacja -> Google Calendar`

## Magazyn plikow

Pliki sa zapisywane osobno dla kazdej organizacji.

Obecnie dziala lokalny backend magazynu, ale zapis idzie juz przez osobna warstwe uslugowa. To oznacza, ze:

- aplikacja nie opiera sie wylacznie na zwyklych sciezkach folderow
- kazdy artefakt ma `storage_backend` i wlasny klucz magazynu
- pozniejsza podmiana lokalnego dysku na zewnetrzny magazyn plikow bedzie prostsza

Przykladowy uklad:

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

To daje:

- porzadek na dysku
- prostsza kontrole dostepu do plikow
- latwiejsza przyszla migracje na magazyn zewnetrzny

## Stack docelowy

W tym repozytorium dziala MVP w `Pythonie`, ale docelowy kierunek rozwoju pozostaje:

- frontend: `React / Next.js`
- backend: `Node.js`
- baza: `PostgreSQL`
- ORM: `Prisma`

Najwazniejsze jest to, ze logika biznesowa jest juz oddzielona od warstwy widoku, wiec przejscie na ten stack nie wymaga przepisywania modelu danych od zera.

## Ulatwienia migracji

Projekt ma juz przygotowane kilka rzeczy pod pozniejsze przeniesienie:

- obsluguje standardowe `DATABASE_URL`
- moze korzystac z wolumenu serwera jako domyslnego magazynu plikow
- ma gotowy skrypt `migrate_sqlite_to_configured_db.py` do przeniesienia rekordow z lokalnej `SQLite` do docelowej bazy
- ma wspolna warstwe magazynu plikow zamiast twardego zapisu bezposrednio po folderach
- ma organizacyjny podzial danych juz w modelu i API

## Co warto dodac w kolejnych etapach

- baze klientow organizacji do rozliczen
- identyfikator platnosci klienta, na start np. numer telefonu w tytule przelewu
- dopasowanie wplat z wyciagow do naleznosci klientow
- saldo klienta i dokumenty rozliczeniowe
- zalaczniki do zadan
- widok kalendarzowy
- przypomnienia uruchamiane w tle
- integracje `Make`
- integracje `Telegram` dla modulu zadan
- uogolniony system powiadomien
- podzial frontendu na mniejsze pliki
