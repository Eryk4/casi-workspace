# Panel Faktur Firmowych

Praktyczny panel operacyjny do zbierania i obsługi faktur z:

- `KSeF`
- `e-maila`
- `Telegrama` z `OCR`

Interfejs jest po polsku i nastawiony na szybkie działanie operacyjne, a nie na ozdobniki.

## Najważniejsze funkcje

- wspólna baza faktur
- logika duplikatów:
  - ten sam numer `KSeF` = pewny duplikat
  - ten sam `numer faktury + NIP wystawcy` = podejrzenie duplikatu
- statusy i ręczna weryfikacja
- kontrahenci i oznaczenie nowych kontrahentów
- historia zdarzeń
- konta użytkowników i logowanie `login + hasło`
- organizacje oddzielające dane klientów
- osobne foldery plików dla każdej organizacji

## Organizacje i bezpieczeństwo danych

System ma już fundament pod pracę z klientami:

- każda faktura, kontrahent, log i konto użytkownika może należeć do konkretnej organizacji
- administrator globalny może tworzyć i edytować organizacje
- użytkownik organizacji widzi tylko dane swojej organizacji
- duplikaty są wykrywane tylko w obrębie tej samej organizacji
- pliki dokumentów i OCR są rozdzielone do osobnych katalogów organizacji

Przykładowy układ plików:

```text
data/magazyn/dokumenty/organizacje/organizacja-domyslna/...
data/magazyn/dokumenty/organizacje/klient-beta/...
data/magazyn/ocr/organizacje/organizacja-domyslna/...
data/magazyn/ocr/organizacje/klient-beta/...
```

Dzięki temu po wejściu do folderów od razu widać pliki konkretnej organizacji, a nie jeden wymieszany katalog.

## Stack

Docelowo najlepszy kierunek rozwoju to:

- frontend: `React / Next.js`
- backend: `Node.js`
- baza: `PostgreSQL`
- ORM: `Prisma`

W tym repozytorium MVP zostało wykonane w:

- `Python 3`
- lekkim API JSON
- `SQLite` lokalnie
- architekturze przygotowanej pod `PostgreSQL`
- prostym panelu SPA w `HTML / CSS / JavaScript`

## Struktura projektu

```text
app/
  api/            HTTP i API JSON
  domain/         stale domenowe
  integrations/   integracje testowe i adaptery
  repositories/   dostep do danych
  services/       logika biznesowa
data/             baza i magazyn plikow
static/           panel webowy
tests/            testy
run.py            uruchomienie serwera
ARCHITECTURE.md   architektura i model danych
```

## Uruchomienie

Start aplikacji:

```bash
python run.py
```

Start pod serwer publiczny:

```bash
python run.py --host 0.0.0.0 --port 8000
```

Adres lokalny:

```text
http://127.0.0.1:8000
```

Przy pustej bazie system tworzy konto startowe:

```text
login: admin
haslo: Admin1234
```

Reset bazy i ponowny seed:

```bash
python run.py --reset
```

Jeśli nie chcesz wpisywać komend ręcznie, użyj gotowych plików z folderu:

```text
Komendy/
```

## Ułatwienia pod migrację i Railway

Projekt jest już przygotowany tak, żeby łatwiej było go przenieść później:

- jeśli ustawisz standardowe `DATABASE_URL`, aplikacja sama może użyć tej bazy jako docelowej
- jeśli Railway zamontuje wolumen przez `RAILWAY_VOLUME_MOUNT_PATH`, aplikacja potrafi użyć go jako domyślnego miejsca na pliki i lokalną `SQLite`
- zapis dokumentów i OCR przechodzi już przez wspólną warstwę magazynu plików, więc późniejsza podmiana lokalnego dysku na zewnętrzny magazyn będzie prostsza
- w bazie zapisywane są także `file_storage_key`, `ocr_storage_key` i `storage_backend`, więc migracja nie opiera się wyłącznie na starych linkach HTTP
- jest gotowy skrypt do przenoszenia danych z lokalnej `SQLite` do docelowej bazy

Migracja danych z lokalnej `SQLite` do obecnie skonfigurowanej bazy:

```bash
python migrate_sqlite_to_configured_db.py --source-sqlite data/invoice_ops.sqlite3 --reset-target
```

Po migracji trzeba jeszcze skopiować cały magazyn plików dokumentów i OCR.

## Wdrożenie na Railway

Projekt jest już przygotowany pod Railway:

- aplikacja słucha na `0.0.0.0` i porcie z `PORT`
- jest endpoint zdrowia `GET /health`
- konfiguracja Railway jest w pliku `railway.json`
- przy `PostgreSQL` demo seed jest domyślnie wyłączony

Najrozsądniejszy układ na start:

1. usługa aplikacji z tego repozytorium
2. osobna usługa `PostgreSQL` w tym samym projekcie Railway
3. wolumen pod pliki dokumentów i OCR

Najważniejsze zmienne środowiskowe dla aplikacji:

```text
INVOICE_DEFAULT_ADMIN_LOGIN=twoj_login_admina
INVOICE_DEFAULT_ADMIN_PASSWORD=twoje_mocne_haslo
INVOICE_SECURE_COOKIES=1
INVOICE_ENABLE_DEMO_SEED=0
RAILWAY_VOLUME_MOUNT_PATH=/data
```

Jeśli chcesz od razu włączyć Telegram:

```text
INVOICE_TELEGRAM_BOT_TOKEN=...
INVOICE_TELEGRAM_WEBHOOK_SECRET=...
```

Uwagi praktyczne:

- `DATABASE_URL` Railway zwykle udostępnia z usługi `PostgreSQL`, a aplikacja umie go użyć
- pliki dokumentów i OCR będą wtedy zapisywane w wolumenie, np. pod `/data/magazyn`
- zmienne administratora ustaw przed pierwszym produkcyjnym uruchomieniem, żeby nie zostać przy `admin / Admin1234`
- obecny układ z wolumenem jest dobry na start, ale przy większej skali warto później przenieść pliki do zewnętrznego magazynu

## Telegram webhook

Pierwszy prawdziwy przepływ Telegram jest już gotowy:

- bot wysyła aktualizację webhookiem do aplikacji
- aplikacja pobiera PDF albo zdjęcie z Telegrama
- zapisuje plik w folderze organizacji
- dopasowuje użytkownika po `ID użytkownika Telegram`
- tworzy fakturę w organizacji tego użytkownika

Do włączenia webhooka ustaw zmienne środowiskowe:

```text
INVOICE_TELEGRAM_BOT_TOKEN=...
INVOICE_TELEGRAM_WEBHOOK_SECRET=...
```

Po uruchomieniu serwer wypisze ścieżkę webhooka:

```text
/api/telegram/webhook/TWOJ_SEKRET
```

Pełny adres webhooka to wtedy na przykład:

```text
http://ADRES_SERWERA:8000/api/telegram/webhook/TWOJ_SEKRET
```

Ważne:

- konto użytkownika w systemie musi mieć wpisane `ID użytkownika Telegram`
- to konto musi być przypisane do organizacji
- na tym etapie OCR działa jeszcze jako warstwa testowa, ale sam odbiór dokumentu z Telegrama jest już prawdziwy

## Testy

```bash
python -m unittest discover -s tests -v
```

## Najważniejsze endpointy

- `GET /api/meta`
- `GET /api/session/current`
- `POST /api/session/login`
- `POST /api/session/logout`
- `GET /health`
- `GET /api/dashboard`
- `GET /api/invoices`
- `GET /api/invoices/{id}`
- `PATCH /api/invoices/{id}`
- `POST /api/invoices/{id}/actions/confirm-duplicate`
- `POST /api/invoices/{id}/actions/reject-duplicate`
- `GET /api/contractors`
- `GET /api/contractors/{id}`
- `GET /api/logs`
- `GET /api/search?q=...`
- `GET /api/organizations`
- `POST /api/organizations`
- `PATCH /api/organizations/{id}`
- `GET /api/users`
- `POST /api/users`
- `PATCH /api/users/{id}`
- `POST /api/import/KSeF`
- `POST /api/import/EMAIL`
- `POST /api/import/TELEGRAM`
- `POST /api/telegram/webhook/{sekret}`

## Integracje testowe i miejsca do podmiany

- prawdziwe API `KSeF`: `app/integrations/ksef_client.py`
- prawdziwy odbiór `e-maili`: `app/integrations/email_ingestion.py`
- prawdziwy bot `Telegram`: `app/integrations/telegram_bot.py`
- prawdziwy silnik `OCR`: `app/integrations/ocr_engine.py`

## Dalszy rozwój

- wdrożenie na centralnym serwerze z `PostgreSQL`
- prawdziwy bot `Telegram`
- prawdziwy import `KSeF`
- prawdziwy odbiór poczty
- kolejki zadań dla `OCR`
- frontend `React / Next.js`
