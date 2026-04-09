# Architektura MVP

## Cel

System ma być prostym panelem operacyjnym do obsługi faktur, ale zaprojektowanym tak, żeby później dało się go bezpiecznie rozbudować pod klientów i zespół.

## Warstwy

### `app/api`

Warstwa HTTP i API JSON. Odpowiada za:

- logowanie
- sesję użytkownika
- kontrolę uprawnień
- przekazanie żądań do serwisów
- blokadę dostępu do plików innych organizacji
- publiczny webhook Telegram do odbioru dokumentów

### `app/repositories`

Warstwa dostępu do danych. Repozytoria wykonują odczyt i zapis do bazy, bez logiki biznesowej.

Najważniejsze repozytoria:

- `organization_repository.py`
- `user_repository.py`
- `invoice_repository.py`
- `contractor_repository.py`
- `event_repository.py`

### `app/services`

Warstwa logiki biznesowej:

- `auth_service.py` - logowanie i konta
- `organization_service.py` - organizacje i zakres danych
- `invoice_service.py` - faktury, OCR, pliki, ręczna edycja
- `duplicate_detector.py` - reguły duplikatów
- `dashboard_service.py` - dane pulpitu
- `notification_service.py` - przygotowanie komunikatów o duplikatach

### `app/integrations`

Integracje testowe przygotowane do podmiany:

- `KSeF`
- `e-mail`
- `Telegram`
- `OCR`

Telegram ma już dwa tryby:

- `import testowy` z panelu
- prawdziwy `webhook`, który odbiera aktualizację od bota, pobiera plik i tworzy fakturę

### `static`

Panel webowy SPA po polsku:

- pulpit
- faktury
- kontrahenci
- historia systemu
- organizacje
- użytkownicy

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

Kontrahent jest unikalny w obrębie organizacji po:

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

Relacje podobieństwa i duplikatów między fakturami.

### `event_logs`

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

## Organizacje i zakres danych

To jest najważniejsza zasada architektury dla wersji klienckiej:

- użytkownik organizacji widzi tylko swoje dane
- administrator organizacji działa tylko w swojej organizacji
- administrator globalny może zarządzać wieloma organizacjami
- pliki i OCR są rozdzielone na poziomie katalogów organizacji

Zakres organizacji jest sprawdzany:

- przy listowaniu faktur
- przy pobieraniu szczegółów
- przy kontrahentach
- przy logach
- przy wyszukiwaniu
- przy imporcie
- przy otwieraniu plików z dysku

## Logika duplikatów

### Pewny duplikat

Jeżeli w tej samej organizacji istnieje już faktura z takim samym `ksef_number`, nowa faktura dostaje:

- `duplicate_type = pewny`
- `status = pewny_duplikat`

### Podejrzenie duplikatu

Jeżeli w tej samej organizacji zgadza się:

- `invoice_number`
- `issuer_nip`

to faktura dostaje:

- `duplicate_type = podejrzenie`
- `status = podejrzenie_duplikatu`

System nie blokuje faktury, tylko oznacza ją do ręcznej weryfikacji.

## Magazyn plików

Pliki są zapisywane osobno dla każdej organizacji.

Obecnie działa lokalny backend magazynu, ale zapis idzie już przez osobną warstwę usługową. To oznacza, że:

- aplikacja nie opiera się wyłącznie na zwykłych ścieżkach folderów
- każdy artefakt ma `storage_backend` i własny klucz magazynu
- późniejsza podmiana lokalnego dysku na zewnętrzny magazyn plików będzie prostsza

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

To daje dwie rzeczy:

- porządek na dysku
- prostszą kontrolę dostępu do plików

## Stack docelowy

W tym repozytorium działa MVP w `Pythonie`, ale docelowy kierunek rozwoju pozostaje:

- frontend: `React / Next.js`
- backend: `Node.js`
- baza: `PostgreSQL`
- ORM: `Prisma`

Najważniejsze jest to, że logika biznesowa jest już oddzielona od warstwy widoku, więc przejście na ten stack nie wymaga przepisywania reguł duplikatów i modelu danych od zera.

## Ułatwienia migracji

Projekt ma już przygotowane kilka rzeczy pod późniejsze przeniesienie:

- obsługuje standardowe `DATABASE_URL`
- może korzystać z wolumenu serwera jako domyślnego magazynu plików
- ma gotowy skrypt `migrate_sqlite_to_configured_db.py` do przeniesienia rekordów z lokalnej `SQLite` do docelowej bazy
