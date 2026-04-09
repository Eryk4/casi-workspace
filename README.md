# Panel Operacyjny Firmy

Praktyczna aplikacja webowa do pracy operacyjnej. System laczy dwa obszary:

- obsluge faktur firmowych
- modul `Asystent Szefa` do zadan, wydarzen, terminow i notatek

Projekt jest przygotowany tak, zeby dalo sie go dalej rozwijac pod klientow, zespol i wdrozenie serwerowe.

## Co juz dziala

### Faktury

- wspolna baza faktur z wielu zrodel
- logika duplikatow:
  - ten sam numer `KSeF` = pewny duplikat
  - ten sam `numer faktury + NIP wystawcy` = podejrzenie duplikatu
- statusy i reczna weryfikacja
- kontrahenci i oznaczenie nowych kontrahentow
- historia zdarzen
- konta uzytkownikow i logowanie `login + haslo`
- organizacje oddzielajace dane klientow
- osobne foldery plikow dla kazdej organizacji
- przygotowanie pod Telegram, OCR, e-mail i KSeF

### Asystent Szefa - MVP

- lista zadan, wydarzen i przypomnien
- tworzenie zadania w organizacji
- przypisanie do uzytkownika z tej samej organizacji
- terminy `data + godzina`
- osobna data i godzina przypomnienia dla zadania lub wydarzenia
- statusy i priorytety
- notatki do zadania
- historia zmian zadania
- filtrowanie po typie, statusie, priorytecie, osobie i terminie
- widok aktywnych przypomnien na pulpicie
- osobna zakladka `Asystent Szefa` w tym samym panelu

## Organizacje i bezpieczenstwo danych

System ma fundament pod prace z klientami:

- kazda faktura, kontrahent, log, zadanie i konto uzytkownika nalezy do konkretnej organizacji
- administrator globalny moze tworzyc i edytowac organizacje
- uzytkownik organizacji widzi tylko dane swojej organizacji
- duplikaty faktur sa wykrywane tylko w obrebie tej samej organizacji
- dokumenty i OCR sa rozdzielone do osobnych katalogow organizacji

Przykladowy uklad plikow:

```text
data/magazyn/dokumenty/organizacje/organizacja-domyslna/...
data/magazyn/dokumenty/organizacje/klient-beta/...
data/magazyn/ocr/organizacje/organizacja-domyslna/...
data/magazyn/ocr/organizacje/klient-beta/...
```

## Stack

Docelowy kierunek rozwoju:

- frontend: `React / Next.js`
- backend: `Node.js`
- baza: `PostgreSQL`
- ORM: `Prisma`

Obecne MVP w repozytorium:

- `Python 3`
- lekkie API JSON
- `SQLite` lokalnie
- architektura przygotowana pod `PostgreSQL`
- panel SPA w `HTML / CSS / JavaScript`

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
Komendy/          gotowe pliki .bat do uruchamiania i migracji
run.py            uruchomienie serwera
ARCHITECTURE.md   architektura i model danych
```

## Uruchomienie

Start aplikacji:

```bash
python run.py
```

Start pod dostep z innego komputera w tej samej sieci:

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

Jesli nie chcesz wpisywac komend recznie, uzyj plikow z folderu:

```text
Komendy/
```

## Seed demonstracyjny

Reset danych demo tworzy przykladowe rekordy:

- poprawna fakture
- pewny duplikat po numerze `KSeF`
- podejrzenie duplikatu po `numerze faktury + NIP`
- nowego kontrahenta
- przykladowe zadania w module `Asystent Szefa`

## Moduly i widoki

- `Pulpit`
- `Faktury`
- `Asystent Szefa`
- `Kontrahenci`
- `Historia systemu`
- `Organizacje`
- `Uzytkownicy`

## Asystent Szefa - zakres MVP

Typy wpisow:

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

Na tym etapie modul nie ma jeszcze:

- zalacznikow do zadan
- widoku kalendarzowego
- integracji z Make
- integracji z Telegramem dla zadan
- automatycznych przypomnien w tle przez Telegram / e-mail / Make

To jest cel kolejnych etapow.

## Ulatwienia pod migracje i Railway

Projekt jest przygotowany tak, zeby latwiej bylo go przeniesc:

- jesli ustawisz `DATABASE_URL`, aplikacja sama moze uzyc tej bazy jako docelowej
- jesli Railway zamontuje wolumen przez `RAILWAY_VOLUME_MOUNT_PATH`, aplikacja umie uzyc go jako domyslnego miejsca na pliki
- zapis dokumentow i OCR przechodzi przez wspolna warstwe magazynu plikow
- w bazie sa zapisywane `file_storage_key`, `ocr_storage_key` i `storage_backend`
- jest gotowy skrypt do przenoszenia danych z lokalnej `SQLite` do docelowej bazy

Migracja danych z lokalnej `SQLite` do obecnie skonfigurowanej bazy:

```bash
python migrate_sqlite_to_configured_db.py --source-sqlite data/invoice_ops.sqlite3 --reset-target
```

Po migracji trzeba jeszcze skopiowac magazyn plikow dokumentow i OCR.

## Wdrozenie na Railway

Projekt jest przygotowany pod Railway:

- aplikacja slucha na `0.0.0.0` i porcie z `PORT`
- jest endpoint zdrowia `GET /health`
- konfiguracja Railway jest w pliku `railway.json`
- przy `PostgreSQL` demo seed jest domyslnie wylaczony

Najrozsadniejszy uklad na start:

1. usluga aplikacji z tego repozytorium
2. osobna usluga `PostgreSQL` w tym samym projekcie Railway
3. osobny wolumen dla uslugi `web` pod pliki dokumentow i OCR

Najwazniejsze zmienne srodowiskowe:

```text
DATABASE_URL=...
INVOICE_DEFAULT_ADMIN_LOGIN=twoj_login_admina
INVOICE_DEFAULT_ADMIN_PASSWORD=twoje_mocne_haslo
INVOICE_SECURE_COOKIES=1
INVOICE_ENABLE_DEMO_SEED=0
INVOICE_ENABLE_TEST_IMPORTS=0
INVOICE_SHOW_DEFAULT_LOGIN_HINT=0
RAILWAY_VOLUME_MOUNT_PATH=/data
```

Jesli chcesz wlaczyc Telegram dla faktur:

```text
INVOICE_TELEGRAM_BOT_TOKEN=...
INVOICE_TELEGRAM_WEBHOOK_SECRET=...
```

Uwagi praktyczne:

- `postgres-volume` nalezy do bazy i nie zastapi wolumenu dla aplikacji
- dokumenty i OCR aplikacji powinny byc trzymane w osobnym wolumenie uslugi `web`
- zmienne administratora ustaw przed pierwszym produkcyjnym uruchomieniem
- obecny uklad z wolumenem jest dobry na start, ale przy wiekszej skali warto pozniej przeniesc pliki do zewnetrznego magazynu

## Telegram webhook dla faktur

Pierwszy prawdziwy przeplyw Telegram jest juz gotowy:

- bot wysyla aktualizacje webhookiem do aplikacji
- aplikacja pobiera PDF albo zdjecie z Telegrama
- zapisuje plik w folderze organizacji
- dopasowuje uzytkownika po `ID uzytkownika Telegram`
- tworzy fakture w organizacji tego uzytkownika

Do wlaczenia webhooka ustaw:

```text
INVOICE_TELEGRAM_BOT_TOKEN=...
INVOICE_TELEGRAM_WEBHOOK_SECRET=...
```

Sciezka webhooka:

```text
/api/telegram/webhook/TWOJ_SEKRET
```

Wazne:

- konto uzytkownika w systemie musi miec wpisane `ID uzytkownika Telegram`
- to konto musi byc przypisane do organizacji
- OCR dla faktur jest na tym etapie jeszcze warstwa testowa

## Testy

```bash
python -m unittest discover -s tests -v
```

## Najwazniejsze endpointy

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
- `GET /api/tasks`
- `GET /api/tasks/{id}`
- `GET /api/tasks/users`
- `POST /api/tasks`
- `PATCH /api/tasks/{id}`
- `POST /api/tasks/{id}/notes`
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
- prawdziwy odbior `e-maili`: `app/integrations/email_ingestion.py`
- prawdziwy bot `Telegram`: `app/integrations/telegram_bot.py`
- prawdziwy silnik `OCR`: `app/integrations/ocr_engine.py`

## Dalszy rozwoj

- zalaczniki do zadan
- widok kalendarzowy
- przypomnienia i automatyczne akcje w tle
- integracje `Make` i `Telegram` dla modulu zadan
- prawdziwy bot `Telegram` dla faktur
- prawdziwy import `KSeF`
- prawdziwy odbior poczty
- frontend `React / Next.js`
