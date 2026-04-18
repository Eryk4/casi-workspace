# Panel Operacyjny Firmy

Praktyczna aplikacja webowa do pracy operacyjnej. System laczy dwa obszary:

- obsluge faktur firmowych
- modul `Asystent Szefa` do zadan, wydarzen, terminow i notatek
- modul `Asystent Firmowy` do bazy wiedzy organizacji i odpowiadania na pytania na podstawie dokumentow

Repozytorium ma tez juz fundament pod kolejny obszar:

- modul rozliczen klientow organizacji z importem wyciagow bankowych

Projekt jest przygotowany tak, zeby dalo sie go dalej rozwijac pod klientow, zespol i wdrozenie serwerowe.

## Pozycja W Ekosystemie

Ta aplikacja pozostaje osobnym produktem, ale jest przygotowywana do pracy w wiekszym ekosystemie dwoch aplikacji produktowych.

W praktyce oznacza to:

- osobny frontend, UX i logike domenowa dla tego produktu
- gotowosc do wspolnego fundamentu dla kont, organizacji, rol, capability, sesji, storage i audit logu
- brak sztucznego laczenia wszystkiego w jedna mega-aplikacje

## Co juz dziala

### Faktury

- wspolna baza faktur z wielu zrodel
- logika duplikatow:
  - ten sam numer `KSeF` = pewny duplikat
  - ten sam `numer faktury + NIP wystawcy` = podejrzenie duplikatu
- nadrzednosc zrodel danych:
  - `KSeF` jest zrodlem nadrzednym dla danych faktury
  - `e-mail` i `Telegram` moga utworzyc rekord wstepny, ale przy dopasowaniu do `KSeF` dane z `KSeF` wygrywaja
  - w szczegolach faktury pokazywane jest `zrodlo nadrzedne`
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
- domyslnie prywatne wpisy uzytkownika
- mozliwosc udostepnienia wpisu wybranym osobom albo calej organizacji
- przypisanie do uzytkownika z tej samej organizacji
- terminy `data + godzina`
- osobna data i godzina przypomnienia dla zadania lub wydarzenia
- kilka nazwanych kalendarzy Google na uzytkownika, na przyklad `Firma A`, `Firma B` albo `Rodzinny`
- wybor kalendarza Google przy zapisie zadania albo wydarzenia
- eksport do Google Calendar przez prywatny adres URL `.ics`
- ustawienia przypomnien uzytkownika: cisza nocna i ponowienie co X minut
- statusy i priorytety
- notatki do zadania
- historia zmian zadania
- filtrowanie po typie, statusie, priorytecie, osobie i terminie
- widok aktywnych przypomnien na pulpicie
- automatyczne przypomnienia Telegram wysylane przez outbox i worker w tle, z widocznym statusem kolejki i recznym uruchomieniem ponownego przebiegu
- osobna zakladka `Asystent Szefa` w tym samym panelu

### Asystent Firmowy - baza wiedzy

- osobna zakladka `Asystent Firmowy`
- oddzielna baza wiedzy dla kazdej organizacji
- import plikow przez formularz i synchronizacje folderu organizacji
- obslugiwane formaty: `TXT`, `DOCX`, `XLSX`, `PDF`, obrazy z OCR
- asynchroniczna kolejka przetwarzania dokumentow
- statusy dokumentow: `queued`, `processing`, `ready`, `error`
- wersjonowanie dokumentow po kazdym przetworzeniu
- odpowiedzi z cytowaniem dokumentu, wersji i linkiem do zrodla
- uprawnienia per uzytkownik:
  - `knowledge.read`
  - `knowledge.upload`
  - `knowledge.sync`
  - `knowledge.manage`

### Rozliczenia klientow - fundament

- rachunki bankowe przypisane do organizacji
- rejestr importow wyciagow CSV
- normalizacja transakcji bankowych do wspolnej tabeli
- pomijanie duplikatow przy ponownym imporcie tych samych pozycji
- przygotowanie pod dopasowanie wplat po identyfikatorze klienta z tytulu przelewu

## Organizacje i bezpieczenstwo danych

System ma fundament pod prace z klientami:

- kazda faktura, kontrahent, log, zadanie i konto uzytkownika nalezy do konkretnej organizacji
- administrator globalny moze tworzyc i edytowac organizacje
- uzytkownik organizacji widzi tylko dane swojej organizacji
- duplikaty faktur sa wykrywane tylko w obrebie tej samej organizacji
- dokumenty i OCR sa rozdzielone do osobnych katalogow organizacji
- baza wiedzy, wersje dokumentow i kolejka przetwarzania sa trzymane osobno dla kazdej organizacji

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

Tryb pelny z webem, schedulerm i workerem w jednym procesie:

```bash
python run.py --mode standalone
```

Sam panel webowy ze schedulowaniem przypomnien:

```bash
python run.py --mode web
```

Osobny worker do dostarczania przypomnien:

```bash
python run.py --mode worker
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

## Testy

Pelny zestaw testow nadal uruchamiasz tak:

```bash
python -m unittest discover -s tests -v
```

Warstwa HTTP zostala rozbita na mniejsze paczki:

- `tests/test_http_server_system.py`
- `tests/test_http_server_integrations.py`
- `tests/test_http_server_invoices.py`
- `tests/test_http_server_access.py`
- `tests/test_http_server_telegram.py`

To ulatwia szybsze sprawdzanie zmian bez odpalania calego repo przy kazdej poprawce.
Mozesz tez skorzystac z gotowych plikow:

- `Komendy/13 - Testy HTTP.bat`
- `Komendy/14 - Testy HTTP szybkie.bat`

Najwieksze pakiety domenowe tez zostaly rozbite:

- zadania:
  - `tests/test_task_service.py`
  - `tests/test_task_commands.py`
  - `tests/test_task_http.py`
- faktury:
  - `tests/test_invoice_duplicates.py`
  - `tests/test_invoice_review_and_ksef.py`
  - `tests/test_invoice_collaboration.py`
- kalendarze:
  - `tests/test_calendar_service.py`
  - `tests/test_calendar_google.py`
  - `tests/test_calendar_http.py`
- wyszukiwanie:
  - `tests/test_search_access.py`
  - `tests/test_search_descriptive.py`

Do codziennej pracy sa gotowe tez osobne komendy:

- `Komendy/15 - Testy zadan.bat`
- `Komendy/16 - Testy faktur.bat`
- `Komendy/17 - Testy kalendarzy.bat`
- `Komendy/18 - Testy wyszukiwania.bat`

Dodatkowo repo ma juz uporzadkowane profile testowe:

- `python run_quality_checks.py --profile smoke`
  - szybki i sensowny zestaw do codziennej pracy
- `python run_quality_checks.py --profile predeploy`
  - glowna kontrola przed wdrozeniem
- `python run_quality_checks.py --profile full`
  - pelne `unittest discover` dla calego repo

Te same profile sa dostepne tez z folderu `Komendy/`:

- `Komendy/19 - Testy smoke.bat`
- `Komendy/20 - Kontrola przed deployem.bat`
- `Komendy/21 - Pelny test discover.bat`

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
- `Asystent Firmowy`
- `Rozliczenia klientow` - fundament backendowy pod dalsza rozbudowe

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

Zakres widocznosci:

- `prywatne`
- `wybrane_osoby`
- `organizacja`

Na tym etapie modul nie ma jeszcze:

- zalacznikow do zadan
- widoku kalendarzowego
- integracji z Make
- integracji z Telegramem dla zadan
- pelnej synchronizacji dwukierunkowej z Google Calendar
- automatycznych przypomnien w tle przez Telegram / e-mail / Make

To jest cel kolejnych etapow.

## Google Calendar - jak to dziala teraz

Obecny model jest celowo prosty i stabilny:

- kazdy uzytkownik moze zalozyc kilka wlasnych kalendarzy i nazwac je po swojemu
- aplikacja generuje dla kazdego kalendarza prywatny adres `.ics`
- ten adres dodajesz w Google Calendar przez `Inne kalendarze -> Z adresu URL`
- zadania i wydarzenia przypisane do wybranego kalendarza pojawiaja sie potem w Google Calendar

Wazne ograniczenia obecnej wersji:

- to jest synchronizacja jednokierunkowa `aplikacja -> Google Calendar`
- zmiany zrobione bezposrednio w Google Calendar nie wracaja jeszcze do aplikacji
- Google odswieza subskrybowane kalendarze we wlasnym tempie, wiec aktualizacja nie zawsze jest natychmiastowa

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
- startuje w trybie `standalone`, czyli panel HTTP i petle tla ida w jednym procesie
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

### Proces lokal -> Railway (spojna wersja)

Rekomendowany, powtarzalny flow:

1. uruchamiaj szybkie testy codzienne:

```bash
python run_quality_checks.py --profile smoke
```

2. przed wdrozeniem uruchom pelna kontrole predeploy:

```bash
python run_quality_checks.py --profile predeploy
```

3. ustaw release id z aktualnego commita lokalnie:

```bash
python sync_release_id.py
```

4. ustaw te sama wartosc `INVOICE_APP_RELEASE_ID` na Railway i wdroz `main`.

5. po wdrozeniu porownaj parity local vs Railway:

```bash
python compare_environment_parity.py --remote-base https://<twoj-adres-railway> --require-same-release --require-same-assets
```

Na Windows masz tez gotowe skróty:

- `Komendy/23 - Ustaw release id z commita.bat`
- `Komendy/24 - Parity local vs Railway.bat`

Lokalnie najwygodniej nie wpisywac tego za kazdym razem recznie, tylko skopiowac:

```text
.env.local.example -> .env.local
```

System automatycznie czyta lokalne pliki:

- `.env.local`
- `data/local.env`

Wazne:

- te pliki sa prywatne i nie trafiaja do repo
- zwykle wystarczy wpisac tam dane `IMAP`, `OCR` albo inne lokalne sekrety
- zmienne ustawione bezposrednio w systemie dalej maja pierwszenstwo

## E-mail organizacji

Kazda organizacja ma teraz w panelu:

- adres skrzynki organizacji
- opcjonalnego dozwolonego nadawce
- opcjonalna fraze w temacie
- przycisk `Testuj polaczenie`
- przycisk `Sprawdz e-mail`

Po kliknieciu `Testuj polaczenie`:

- system laczy sie ze skrzynka przez `IMAP`
- nie importuje dokumentow
- pokazuje, czy logowanie, folder i podstawowy odczyt wiadomosci dzialaja
- zapisuje wynik ostatniego testu polaczenia w organizacji

Po kliknieciu `Sprawdz e-mail`:

- system sprawdza skrzynke przez `IMAP`
- importuje na raz wszystkie nowe pasujace dokumenty
- pokazuje, ile nowych faktur wpadlo
- pomija juz znane wiadomosci
- zapisuje wynik ostatniego sprawdzenia w organizacji
- zapisuje pelny rejestr importu: tryb reczny albo automatyczny, liczbe sprawdzonych wiadomosci, zalaczniki i powody pominiec

Jesli chcesz wlaczyc automat co kilka minut, dopisz tez:

```text
INVOICE_EMAIL_AUTOCHECK_ENABLED=1
INVOICE_EMAIL_AUTOCHECK_SECONDS=300
```

To uruchamia cykliczne sprawdzanie wszystkich aktywnych organizacji, ktore maja:

- wlaczona integracje e-mail
- ustawiony adres odbiorcy
- globalnie skonfigurowany `IMAP`

Reczny przycisk `Sprawdz e-mail` nadal zostaje jako awaryjny i diagnostyczny.

Do lokalnego podpiecia skrzynki uzupelnij w `.env.local`:

```text
INVOICE_EMAIL_IMAP_HOST=imap.gmail.com
INVOICE_EMAIL_IMAP_PORT=993
INVOICE_EMAIL_IMAP_USERNAME=twoja_skrzynka@twojadomena.pl
INVOICE_EMAIL_IMAP_PASSWORD=twoje_haslo_aplikacji_google
INVOICE_EMAIL_IMAP_FOLDER=INBOX
INVOICE_EMAIL_IMAP_USE_SSL=1
INVOICE_EMAIL_FETCH_LIMIT=100
```

Dla wygody masz tez gotowe pliki:

- `Komendy\08 - Otworz ustawienia e-mail.bat`
- `Komendy\09 - Test polaczenia e-mail.bat`
- `Komendy\10 - Sprawdz gotowosc e-mail.bat`
- `Komendy\11 - Konfigurator e-mail.bat`
- `Komendy\12 - Sprawdz gotowosc Google OAuth e-mail.bat`

Dla Google Workspace / Gmail zwykle potrzebujesz hasla aplikacji Google, a nie zwyklego hasla do konta.

Na start najprostszy jest klasyczny IMAP z haslem aplikacji. To wystarcza do lokalnego testu i pierwszego wdrozenia.

Rownolegle system ma juz przygotowany tryb Google Workspace OAuth dla centralnej skrzynki. Ten tryb przydaje sie, gdy:

- chcesz odejsc od recznego trzymania hasla aplikacji
- chcesz miec jedna centralna skrzynke dla wielu organizacji
- chcesz przygotowac bardziej produkcyjny model pod przyszly ekosystem

Do Google OAuth potrzebujesz dodatkowo:

```text
INVOICE_PUBLIC_BASE_URL=https://twoj-publiczny-adres
INVOICE_EMAIL_GOOGLE_CLIENT_ID=...
INVOICE_EMAIL_GOOGLE_CLIENT_SECRET=...
```

Wazne:

- `INVOICE_PUBLIC_BASE_URL` musi byc publicznym adresem HTTPS
- bez publicznego HTTPS nie zakonczysz autoryzacji Google
- lokalnie mozesz wiec najpierw testowac IMAP, a OAuth dolaczyc pozniej

`09 - Test polaczenia e-mail.bat` robi suchy test: laczy sie ze skrzynka, sprawdza folder i pokazuje, ile dokumentow system widzi jako nowe jeszcze przed kliknieciem `Sprawdz e-mail` w panelu.
`10 - Sprawdz gotowosc e-mail.bat` sprawdza caly stan modulu: konfiguracje e-mail, organizacje gotowe do importu oraz stan Google Workspace OAuth.
`11 - Konfigurator e-mail.bat` prowadzi krok po kroku przez wpisanie ustawien Google Workspace / IMAP, automatu i podstawowych pol OAuth i zapisuje je do `.env.local`.
`12 - Sprawdz gotowosc Google OAuth e-mail.bat` sprawdza osobno, czy publiczny adres i klient Google sa juz gotowe do przycisku `Polacz Google Workspace`.


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
- dokument zapisuje sie w organizacji przypisanej po `ID uzytkownika Telegram` albo `ID kanalu Telegram`
- OCR probuje odczytac tresc lokalnie i wyciagnac numer faktury, NIP, daty, kwote i walute
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
- jesli organizacja ma ustawione `ID kanalu Telegram`, system moze tez rozpoznac organizacje po czacie
- jesli OCR nie odczyta kluczowych pol, faktura trafia automatycznie do `weryfikacji`

### Lokalny OCR

OCR dziala teraz w dwoch trybach:

- `tesseract` - jesli na komputerze lub serwerze jest dostepny lokalny `Tesseract OCR`
- `fallback` - jesli plik ma czytelna warstwe tekstowa, system sprobuje odczytac tekst bez pelnego OCR

Opcjonalne zmienne srodowiskowe:

```text
INVOICE_TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
INVOICE_OCR_LANGUAGE=pol+eng
```

Uwagi praktyczne:

- zdjecia i skany z Telegrama wymagaja lokalnego `Tesseract`, zeby OCR byl naprawde skuteczny
- tekstowe PDF-y potrafia zostac odczytane nawet bez `Tesseract`
- w pulpicie aplikacji widac, czy OCR dziala jako `lokalny silnik aktywny`, czy tylko `tryb awaryjny`

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
- `GET /api/tasks/reminders/status`
- `POST /api/tasks`
- `POST /api/tasks/reminders/dispatch`
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
- `GET /api/knowledge/documents`
- `POST /api/knowledge/documents`
- `POST /api/knowledge/sync`
- `POST /api/knowledge/documents/{id}/reprocess`
- `POST /api/knowledge/ask`
- `POST /api/import/KSeF`
- `POST /api/import/EMAIL`
- `POST /api/import/TELEGRAM`
- `POST /api/telegram/webhook/{sekret}`

## Integracje testowe i miejsca do podmiany

- prawdziwe API `KSeF`: `app/integrations/ksef_client.py`
- prawdziwy odbior `e-maili`: `app/integrations/email_ingestion.py`
- prawdziwy bot `Telegram`: `app/integrations/telegram_bot.py`
- lokalny silnik `OCR` z parserem pol: `app/integrations/ocr_engine.py`

## Dalszy rozwoj

- zalaczniki do zadan
- widok kalendarzowy
- przypomnienia i automatyczne akcje w tle
- integracje `Make` i `Telegram` dla modulu zadan
- prawdziwy bot `Telegram` dla faktur
- prawdziwy import `KSeF`
- produkcyjne wdrozenie centralnej skrzynki Google Workspace z OAuth
- frontend `React / Next.js`
