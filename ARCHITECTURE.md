# Architektura MVP

## Cel

System ma byc prostym panelem operacyjnym dla firmy i klientow. Obecnie obejmuje dwa glowne obszary:

- obsluge faktur
- modul `Asystent Szefa` do zadan, wydarzen, przypomnien i notatek

Architektura ma pozwolic na bezpieczna rozbudowe pod zespol, klientow, Telegram, Make i wdrozenie serwerowe.

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
- `task_repository.py`

### `app/services`

Warstwa logiki biznesowej:

- `auth_service.py` - logowanie i konta
- `organization_service.py` - organizacje i zakres danych
- `invoice_service.py` - faktury, OCR, pliki, reczna edycja
- `duplicate_detector.py` - reguly duplikatow
- `dashboard_service.py` - dane pulpitu
- `notification_service.py` - przygotowanie komunikatow o duplikatach
- `task_service.py` - zadania, notatki, historia zmian
- `storage_service.py` - zapis i odczyt plikow przez wspolna warstwe magazynu

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
- `is_active`
- `last_login_at`
- `created_by_user_id`
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

### `tasks`

Glowny obiekt modulu `Asystent Szefa`.

- `task_id`
- `organization_id`
- `task_type`
- `title`
- `description`
- `status`
- `priority`
- `due_at`
- `assigned_user_id`
- `created_by_user_id`
- `completed_at`
- `created_at`
- `updated_at`

Typy:

- `zadanie`
- `wydarzenie`
- `przypomnienie`

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

## Organizacje i zakres danych

To jest najwazniejsza zasada architektury dla wersji klienckiej:

- uzytkownik organizacji widzi tylko swoje dane
- administrator organizacji dziala tylko w swojej organizacji
- administrator globalny moze zarzadzac wieloma organizacjami
- pliki i OCR sa rozdzielone na poziomie katalogow organizacji
- zadania, notatki i historia zadan sa rowniez odseparowane organizacjami

Zakres organizacji jest sprawdzany:

- przy listowaniu faktur
- przy pobieraniu szczegolow faktur
- przy kontrahentach
- przy logach
- przy zadaniach
- przy notatkach do zadan
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

## Asystent Szefa - logika MVP

Na obecnym etapie modul zadan dziala jako osobna czesc tej samej aplikacji, a nie osobna aplikacja.

Obslugiwane akcje:

- utworzenie zadania
- zmiana typu, statusu, priorytetu, terminu i osoby przypisanej
- ustawienie osobnego terminu przypomnienia
- oznaczenie jako zakonczone
- dodanie notatki
- historia zmian

Najwazniejsze zasady:

- zadanie zawsze nalezy do organizacji
- zadanie mozna przypisac tylko do aktywnego uzytkownika tej samej organizacji
- zadanie lub wydarzenie moze miec osobna godzine przypomnienia
- przypomnienie nie moze byc ustawione pozniej niz termin zadania
- notatka do zadania rowniez nalezy do tej samej organizacji
- zmiany sa zapisywane jednoczesnie w `task_history` i w ogolnym `event_logs`

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

- zalaczniki do zadan
- widok kalendarzowy
- przypomnienia uruchamiane w tle
- integracje `Make`
- integracje `Telegram` dla modulu zadan
- uogolniony system powiadomien
- podzial frontendu na mniejsze pliki
