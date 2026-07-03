# CASI Workspace

Wersja: 2026-04-29  
Status: aktualny opis projektu i instrukcja startowa

CASI Workspace to praktyczna aplikacja operacyjna dla firm.

System ma pomagaÄ‡ w codziennej pracy z:

- fakturami,
- dokumentami,
- zadaniami,
- wydarzeniami,
- przypomnieniami,
- bazÄ… wiedzy organizacji,
- rozliczeniami klientĂłw,
- automatyzacjami,
- przyszĹ‚ymi moduĹ‚ami AI.

To nie jest demo ani makieta. Projekt jest rozwijany jako realna aplikacja produktowa budowana etapami.

---

## GĹ‚Ăłwne dokumenty projektu

NajwaĹĽniejsze pliki opisujÄ…ce projekt:

- `AGENTS.md` â€” zasady pracy dla Codexa i developerĂłw,
- `ARCHITECTURE.md` â€” architektura aplikacji, model danych i kierunek rozwoju,
- `README.md` â€” praktyczny opis projektu, uruchomienie i najwaĹĽniejsze informacje,
- `docs/ENVIRONMENT_AND_DATA_SAFETY.md` - zasady pracy z lokalnym sandboxem danych, backupami i resetem,
- `MODUL_ROZLICZEN_KLIENTOW.md` â€” szczegĂłĹ‚y moduĹ‚u rozliczeĹ„ klientĂłw,
- `Role uĹĽytkownikĂłw.md` â€” role, uprawnienia i zasady dostÄ™pu.

JeĹĽeli pojawi siÄ™ konflikt miÄ™dzy dokumentami:

1. `AGENTS.md` okreĹ›la, jak pracowaÄ‡ nad projektem.
2. `ARCHITECTURE.md` okreĹ›la, jak aplikacja jest zbudowana i w jakim kierunku ma siÄ™ rozwijaÄ‡.
3. `README.md` jest skrĂłtem operacyjnym i instrukcjÄ… startowÄ….

---

## Pozycja w ekosystemie

CASI Workspace jest osobnym produktem, ale powinno byÄ‡ gotowe do pracy w wiÄ™kszym ekosystemie kilku aplikacji produktowych.

Oznacza to:

- osobny frontend,
- osobny UX,
- osobnÄ… logikÄ™ domenowÄ…,
- gotowoĹ›Ä‡ do wspĂłlnego fundamentu dla kont, organizacji, rĂłl, capability, sesji, storage i audit logu,
- brak sztucznego Ĺ‚Ä…czenia wszystkich przyszĹ‚ych produktĂłw w jednÄ… wielkÄ… aplikacjÄ™.

---

## Obecny zakres aplikacji

Obecna wersja produktu obejmuje kilka gĹ‚Ăłwnych obszarĂłw.

### Faktury

System obsĹ‚uguje:

- wspĂłlnÄ… bazÄ™ faktur z wielu ĹşrĂłdeĹ‚,
- faktury z KSeF, e-maila, Telegrama, uploadu i ĹşrĂłdeĹ‚ rÄ™cznych,
- statusy faktur,
- rÄ™cznÄ… weryfikacjÄ™,
- kontrahentĂłw,
- oznaczanie nowych kontrahentĂłw,
- historiÄ™ zdarzeĹ„,
- pliki ĹşrĂłdĹ‚owe,
- OCR,
- separacjÄ™ danych organizacji.

Logika duplikatĂłw:

- ten sam numer `KSeF` w tej samej organizacji oznacza pewny duplikat,
- ten sam `numer faktury + NIP wystawcy` oznacza podejrzenie duplikatu,
- system powinien pokazywaÄ‡ konkretny powĂłd wykrycia duplikatu.

NadrzÄ™dnoĹ›Ä‡ ĹşrĂłdeĹ‚:

- `KSeF` jest ĹşrĂłdĹ‚em nadrzÄ™dnym dla danych faktury,
- `EMAIL`, `TELEGRAM`, `UPLOAD` i `MANUAL` mogÄ… tworzyÄ‡ rekordy wstÄ™pne,
- jeĹĽeli pĂłĹşniej pojawi siÄ™ dopasowana faktura z `KSeF`, dane z `KSeF` mogÄ… wygraÄ‡ biznesowo,
- pole `authoritative_source` wskazuje ĹşrĂłdĹ‚o nadrzÄ™dne.

---

### Asystent Szefa

ModuĹ‚ `Asystent Szefa` sĹ‚uĹĽy do pracy z:

- zadaniami,
- wydarzeniami,
- przypomnieniami,
- notatkami,
- historiÄ… zmian.

ObsĹ‚ugiwane elementy:

- tworzenie zadania w organizacji,
- prywatne wpisy uĹĽytkownika,
- moĹĽliwoĹ›Ä‡ widocznoĹ›ci dla caĹ‚ej organizacji,
- moĹĽliwoĹ›Ä‡ kierunkowego udostÄ™pniania wybranym osobom,
- przypisanie zadania do uĹĽytkownika z tej samej organizacji,
- terminy `data + godzina`,
- osobna data i godzina przypomnienia,
- statusy,
- priorytety,
- notatki do zadania,
- historia zmian,
- filtrowanie po typie, statusie, priorytecie, osobie i terminie,
- widok aktywnych przypomnieĹ„ na pulpicie.

Typy wpisĂłw:

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

Zakres widocznoĹ›ci:

- `prywatne`
- `wybrane_osoby`
- `organizacja`

---

### Google Calendar

Obecny model synchronizacji Google Calendar jest prosty i stabilny.

ZaĹ‚oĹĽenia:

- kaĹĽdy uĹĽytkownik moĹĽe mieÄ‡ kilka nazwanych kalendarzy,
- aplikacja generuje prywatny adres `.ics` dla kaĹĽdego kalendarza,
- adres `.ics` moĹĽna dodaÄ‡ w Google Calendar przez `Inne kalendarze -> Z adresu URL`,
- synchronizacja dziaĹ‚a jednokierunkowo: `aplikacja -> Google Calendar`.

WaĹĽne ograniczenia:

- zmiany zrobione bezpoĹ›rednio w Google Calendar nie wracajÄ… jeszcze do aplikacji,
- Google odĹ›wieĹĽa subskrybowane kalendarze we wĹ‚asnym tempie,
- aktualizacja w Google Calendar nie zawsze jest natychmiastowa.

---

### Asystent Firmowy

ModuĹ‚ `Asystent Firmowy` sĹ‚uĹĽy do pracy z bazÄ… wiedzy organizacji.

ObsĹ‚ugiwane elementy:

- osobna zakĹ‚adka `Asystent Firmowy`,
- oddzielna baza wiedzy dla kaĹĽdej organizacji,
- import plikĂłw przez formularz,
- synchronizacja folderu organizacji,
- kolejka przetwarzania dokumentĂłw,
- statusy dokumentĂłw,
- wersjonowanie dokumentĂłw,
- odpowiedzi z cytowaniem dokumentu, wersji i linkiem do ĹşrĂłdĹ‚a,
- uprawnienia per uĹĽytkownik.

ObsĹ‚ugiwane formaty kierunkowe:

- `TXT`,
- `DOCX`,
- `XLSX`,
- `PDF`,
- obrazy z OCR.

Statusy dokumentĂłw:

- `queued`
- `processing`
- `ready`
- `error`

Capability:

- `knowledge.read`
- `knowledge.upload`
- `knowledge.sync`
- `knowledge.manage`

---

### Rozliczenia klientĂłw

Repozytorium ma fundament pod moduĹ‚ rozliczeĹ„ klientĂłw organizacji.

Obecny zakres:

- rachunki bankowe przypisane do organizacji,
- rejestr importĂłw wyciÄ…gĂłw CSV,
- normalizacja transakcji bankowych,
- pomijanie duplikatĂłw przy ponownym imporcie tych samych pozycji,
- przygotowanie pod dopasowanie wpĹ‚at po identyfikatorze klienta z tytuĹ‚u przelewu.

Kierunek rozwoju:

- baza klientĂłw organizacji,
- identyfikator pĹ‚atnoĹ›ci klienta,
- dopasowanie wpĹ‚at z wyciÄ…gĂłw do naleĹĽnoĹ›ci,
- saldo klienta,
- dokumenty rozliczeniowe,
- powiadomienia o zalegĹ‚oĹ›ciach,
- raporty pĹ‚atnoĹ›ci.

---

### Work Items i SLA

ModuĹ‚ `Work Items i SLA` sĹ‚uĹĽy do operacyjnego triage i kontroli pilnych spraw.

ObsĹ‚uguje miÄ™dzy innymi:

- statusy spraw,
- priorytety,
- score priorytetu,
- etap SLA,
- ostrzeĹĽenia SLA,
- eskalacje,
- akcje pojedyncze i masowe,
- ryzyka SLA,
- politykÄ™ SLA per organizacja,
- analitykÄ™ obciÄ…ĹĽenia zespoĹ‚u,
- filtry i sortowanie.

---

## Organizacje i bezpieczeĹ„stwo danych

System ma fundament pod pracÄ™ z klientami i wieloma organizacjami.

Zasady:

- kaĹĽda faktura naleĹĽy do organizacji,
- kaĹĽdy kontrahent naleĹĽy do organizacji,
- kaĹĽde zadanie naleĹĽy do organizacji,
- kaĹĽdy dokument bazy wiedzy naleĹĽy do organizacji,
- logi sÄ… powiÄ…zane z organizacjÄ…,
- uĹĽytkownik organizacji widzi tylko dane swojej organizacji,
- administrator globalny moĹĽe zarzÄ…dzaÄ‡ wieloma organizacjami,
- duplikaty faktur sÄ… wykrywane tylko w obrÄ™bie tej samej organizacji,
- dokumenty i OCR sÄ… rozdzielone do osobnych katalogĂłw lub kluczy organizacji,
- baza wiedzy, wersje dokumentĂłw i kolejka przetwarzania sÄ… trzymane osobno dla kaĹĽdej organizacji.

PrzykĹ‚adowy ukĹ‚ad plikĂłw:

```text
data/magazyn/dokumenty/organizacje/organizacja-domyslna/...
data/magazyn/dokumenty/organizacje/klient-beta/...
data/magazyn/ocr/organizacje/organizacja-domyslna/...
data/magazyn/ocr/organizacje/klient-beta/...
```

---

## Frontend

Aktualny docelowy frontend aplikacji znajduje sie w katalogu:

```text
frontend/
```

`frontend/` (Next.js/React) jest jedynym aktywnym miejscem rozwoju UI.

Legacy frontend znajduje sie w katalogu:

```text
static/
```

`static/` to warstwa legacy utrzymywana czasowo dla kompatybilnosci obecnego deployu backendu.

Kierunek rozwoju UI:

- `React`,
- `Next.js`,
- wspolny AppShell,
- centralna konfiguracja nawigacji,
- lewy sidebar jako glowna nawigacja,
- topbar jako pasek kontekstowy,
- wspolne komponenty UI,
- modulowa struktura funkcji,
- czysta warstwa komunikacji z API.

Nie nalezy mieszac legacy `static/` z docelowym frontendem `frontend/`.

Doprecyzowanie source of truth frontendu:

- `frontend/` = aktualny docelowy frontend (Next.js/React),
- `static/` = legacy UI utrzymywany tymczasowo dla kompatybilnosci backendu,
- legacy static mozna wylaczyc flaga `CASI_SERVE_LEGACY_STATIC=0`,
- nie wylaczaj legacy static na produkcji, dopoki deploy nie obsluguje `frontend/` jako glownego UI.

## Stack technologiczny

### Obecna implementacja

Obecnie repozytorium dziaĹ‚a gĹ‚Ăłwnie na:

- `Python 3`,
- lekkim API JSON,
- `SQLite` lokalnie,
- panelu SPA w `HTML / CSS / JavaScript`,
- lokalnym magazynie plikĂłw,
- strukturze przygotowanej pod pĂłĹşniejszÄ… migracjÄ™.

### Kierunek produkcyjny

Kierunek rozwoju moĹĽe obejmowaÄ‡:

- frontend: `React / Next.js`,
- baza danych: `PostgreSQL`,
- uporzÄ…dkowana warstwa API,
- backend w `Node.js` albo dalszy rozwĂłj backendu w `Pythonie`,
- ORM lub warstwa dostÄ™pu do danych dobrana do wybranego backendu,
- zewnÄ™trzny storage plikĂłw,
- kolejki zadaĹ„,
- moduĹ‚owa warstwa AI i OCR.

Na tym etapie waĹĽniejsze od sztywnego wyboru jednego stacku jest utrzymanie dobrego podziaĹ‚u na:

- API,
- serwisy,
- repozytoria,
- integracje,
- frontend,
- storage,
- joby,
- logi.

Sama moĹĽliwoĹ›Ä‡ przyszĹ‚ej migracji na inny backend nie oznacza, ĹĽe naleĹĽy teraz przepisywaÄ‡ dziaĹ‚ajÄ…cy backend bez konkretnego powodu biznesowego lub technicznego.

---

## Struktura projektu

```text
app/
  api/             HTTP i API JSON
  domain/          staĹ‚e domenowe
  integrations/    integracje i adaptery
  repositories/    dostÄ™p do danych
  services/        logika biznesowa

data/              baza lokalna i magazyn plikĂłw
static/            legacy frontend (tymczasowa kompatybilnosc deployu)
frontend/          aktywny source of truth UI (React / Next.js)
tests/             testy
Komendy/           gotowe pliki .bat do uruchamiania i testĂłw

run.py             uruchomienie serwera
ARCHITECTURE.md    architektura i model danych
AGENTS.md          instrukcje pracy dla Codexa
README.md          opis projektu i instrukcja startowa
```

---

## Uruchomienie lokalne

Start aplikacji:

```bash
python run.py
```

Tryb peĹ‚ny z webem, schedulerem i workerem w jednym procesie:

```bash
python run.py --mode standalone
```

Sam panel webowy ze schedulowaniem przypomnieĹ„:

```bash
python run.py --mode web
```

Osobny worker:

```bash
python run.py --mode worker
```

Start pod dostÄ™p z innego komputera w tej samej sieci:

```bash
python run.py --host 0.0.0.0 --port 8000
```

Adres lokalny:

```text
http://127.0.0.1:8000
```

Przy pustej lokalnej bazie system moĹĽe utworzyÄ‡ konto startowe:

```text
login: admin
haslo: Admin1234
```

To konto sĹ‚uĹĽy tylko do lokalnego startu i testĂłw. W Ĺ›rodowisku produkcyjnym dane administratora naleĹĽy ustawiÄ‡ przez zmienne Ĺ›rodowiskowe przed pierwszym uruchomieniem.

Reset bazy i ponowny seed:

```bash
python run.py --reset
```

Reset/reseed jest przeznaczony wylacznie dla lokalnego sandboxu danych. Nie uruchamiaj go na bazie z prawdziwymi danymi, stagingu, produkcji ani zdalnej bazie PostgreSQL.

Od teraz reset wymaga jawnego potwierdzenia lokalnego sandboxu:

```powershell
$env:CASI_ALLOW_LOCAL_SANDBOX_RESET = "1"
python run.py --reset
Remove-Item Env:\CASI_ALLOW_LOCAL_SANDBOX_RESET
```

Guardrail blokuje reset, jezeli aktywne jest `DATABASE_URL`, `INVOICE_DATABASE_URL`, silnik inny niz SQLite albo sciezka SQLite poza `data/`. Przed resetem istniejacej lokalnej bazy wykonywany jest backup w:

```text
data/backup/reset/
```

Zasady bezpieczenstwa srodowisk i backupu sa opisane w `docs/ENVIRONMENT_AND_DATA_SAFETY.md`.

### Git i lokalne dane

Nie commituj lokalnych danych ani sekretow:

- `.env`, `.env.local` i prywatnych `.env.*`,
- lokalnej bazy `data/*.sqlite3`,
- backupow `data/backup/` i `data/backups/`,
- lokalnego storage `data/magazyn/`,
- logow,
- `.next/`, `node_modules/`, cache i venv.

Do repozytorium moga trafic tylko szablony env bez sekretow, np. `.env.example` i `.env.local.example`.

Przenoszac projekt na inny komputer, przenos kod przez Git, a prywatne env, lokalny sandbox danych i ewentualne backupy kopiuj poza historia Git. Prawdziwe dane klientow i backupy produkcyjne musza zawsze pozostac poza repozytorium.

Gotowe skrĂłty znajdujÄ… siÄ™ w folderze:

```text
Komendy/
```

---

## Testy

PeĹ‚ny zestaw testĂłw:

```bash
python -m unittest discover -s tests -v
```

Szybki zestaw do codziennej pracy:

```bash
python run_quality_checks.py --profile smoke
```

Kontrola aktywnego frontendu Next:

```bash
python run_quality_checks.py --profile frontend-smoke
```

Profil `frontend-smoke` uruchamia w katalogu `frontend/`:

- `npm.cmd run typecheck`,
- `npm.cmd run test:models`,
- `npm.cmd run build`.

Ten profil dotyczy docelowego frontendu `frontend/` (Next.js/React). Legacy `static/` nie jest rozwijane ani sprawdzane tym profilem.

Aktualny status modulow Next, zakres `organization_id`, tryb read-only i najblizsze kroki sa opisane w `frontend/docs/NEXT_MODULES_STATUS.md`.

GĹ‚Ăłwna kontrola przed wdroĹĽeniem:

```bash
python run_quality_checks.py --profile predeploy
```

PeĹ‚ny test caĹ‚ego repozytorium:

```bash
python run_quality_checks.py --profile full
```

Gotowe skrĂłty w folderze `Komendy/`:

```text
Komendy/19 - Testy smoke.bat
Komendy/20 - Kontrola przed deployem.bat
Komendy/21 - Pelny test discover.bat
```

Wybrane pakiety testĂłw:

```text
tests/test_http_server_system.py
tests/test_http_server_integrations.py
tests/test_http_server_invoices.py
tests/test_http_server_access.py
tests/test_http_server_telegram.py
tests/test_task_service.py
tests/test_task_commands.py
tests/test_task_http.py
tests/test_invoice_duplicates.py
tests/test_invoice_review_and_ksef.py
tests/test_invoice_collaboration.py
tests/test_calendar_service.py
tests/test_calendar_google.py
tests/test_calendar_http.py
tests/test_search_access.py
tests/test_search_descriptive.py
```

---

## E-mail organizacji

KaĹĽda organizacja moĹĽe mieÄ‡ ustawienia skrzynki e-mail.

W panelu moĹĽna ustawiÄ‡ miÄ™dzy innymi:

- adres skrzynki organizacji,
- opcjonalnego dozwolonego nadawcÄ™,
- opcjonalnÄ… frazÄ™ w temacie,
- test poĹ‚Ä…czenia,
- rÄ™czne sprawdzenie e-maila.

Po klikniÄ™ciu `Testuj poĹ‚Ä…czenie` system:

- Ĺ‚Ä…czy siÄ™ ze skrzynkÄ… przez `IMAP`,
- nie importuje dokumentĂłw,
- pokazuje, czy logowanie, folder i podstawowy odczyt wiadomoĹ›ci dziaĹ‚ajÄ…,
- zapisuje wynik ostatniego testu poĹ‚Ä…czenia.

Po klikniÄ™ciu `SprawdĹş e-mail` system:

- sprawdza skrzynkÄ™ przez `IMAP`,
- importuje nowe pasujÄ…ce dokumenty,
- pomija znane wiadomoĹ›ci,
- zapisuje wynik ostatniego sprawdzenia,
- zapisuje rejestr importu.

PrzykĹ‚adowe zmienne dla IMAP:

```text
INVOICE_EMAIL_IMAP_HOST=imap.gmail.com
INVOICE_EMAIL_IMAP_PORT=993
INVOICE_EMAIL_IMAP_USERNAME=twoja_skrzynka@twojadomena.pl
INVOICE_EMAIL_IMAP_PASSWORD=twoje_haslo_aplikacji_google
INVOICE_EMAIL_IMAP_FOLDER=INBOX
INVOICE_EMAIL_IMAP_USE_SSL=1
INVOICE_EMAIL_FETCH_LIMIT=100
```

Opcjonalne automatyczne sprawdzanie e-maila:

```text
INVOICE_EMAIL_AUTOCHECK_ENABLED=1
INVOICE_EMAIL_AUTOCHECK_SECONDS=300
```

DomyĹ›lnie warto preferowaÄ‡ rÄ™czne lub kontrolowane sprawdzanie, jeĹĽeli czÄ™ste automatyczne sprawdzanie nie jest potrzebne.

---

## Google Workspace OAuth dla e-maila

System ma przygotowany kierunek pod Google Workspace OAuth dla centralnej skrzynki.

Ten tryb przydaje siÄ™, gdy:

- chcesz odejĹ›Ä‡ od rÄ™cznego trzymania hasĹ‚a aplikacji,
- chcesz mieÄ‡ centralnÄ… skrzynkÄ™ dla wielu organizacji,
- chcesz przygotowaÄ‡ bardziej produkcyjny model integracji.

Wymagane zmienne:

```text
INVOICE_PUBLIC_BASE_URL=https://twoj-publiczny-adres
INVOICE_EMAIL_GOOGLE_CLIENT_ID=...
INVOICE_EMAIL_GOOGLE_CLIENT_SECRET=...
```

WaĹĽne:

- `INVOICE_PUBLIC_BASE_URL` musi byÄ‡ publicznym adresem HTTPS,
- bez publicznego HTTPS nie da siÄ™ poprawnie zakoĹ„czyÄ‡ autoryzacji Google,
- lokalnie najproĹ›ciej zaczÄ…Ä‡ od IMAP, a OAuth doĹ‚Ä…czyÄ‡ pĂłĹşniej.

---

## Telegram webhook dla faktur

Telegram moĹĽe sĹ‚uĹĽyÄ‡ do przesyĹ‚ania faktur i dokumentĂłw.

PrzepĹ‚yw:

- bot wysyĹ‚a aktualizacje webhookiem do aplikacji,
- aplikacja pobiera PDF albo zdjÄ™cie z Telegrama,
- dokument zapisuje siÄ™ w organizacji przypisanej po `ID uĹĽytkownika Telegram` albo `ID kanaĹ‚u Telegram`,
- OCR prĂłbuje odczytaÄ‡ treĹ›Ä‡,
- system wyciÄ…ga numer faktury, NIP, daty, kwotÄ™ i walutÄ™,
- zapisuje plik w folderze organizacji,
- tworzy fakturÄ™ w organizacji uĹĽytkownika,
- jeĹĽeli OCR nie odczyta kluczowych pĂłl, faktura trafia do weryfikacji.

Zmienne Ĺ›rodowiskowe:

```text
INVOICE_TELEGRAM_BOT_TOKEN=...
INVOICE_TELEGRAM_WEBHOOK_SECRET=...
```

ĹšcieĹĽka webhooka:

```text
/api/telegram/webhook/TWOJ_SEKRET
```

WaĹĽne:

- konto uĹĽytkownika w systemie musi mieÄ‡ wpisane `ID uĹĽytkownika Telegram`,
- konto musi byÄ‡ przypisane do organizacji,
- jeĹĽeli organizacja ma ustawione `ID kanaĹ‚u Telegram`, system moĹĽe rozpoznaÄ‡ organizacjÄ™ po czacie.

---

## OCR

OCR dziaĹ‚a w trybach zaleĹĽnych od dostÄ™pnej konfiguracji.

Tryby:

- `tesseract` â€” jeĹĽeli na komputerze lub serwerze jest dostÄ™pny lokalny `Tesseract OCR`,
- `fallback` â€” jeĹĽeli plik ma czytelnÄ… warstwÄ™ tekstowÄ…, system prĂłbuje odczytaÄ‡ tekst bez peĹ‚nego OCR.

Opcjonalne zmienne:

```text
INVOICE_TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
INVOICE_OCR_LANGUAGE=pol+eng
```

Uwagi:

- zdjÄ™cia i skany wymagajÄ… lokalnego `Tesseract`, ĹĽeby OCR byĹ‚ skuteczny,
- tekstowe PDF-y mogÄ… zostaÄ‡ odczytane nawet bez `Tesseract`,
- w pulpicie aplikacji widaÄ‡ status dziaĹ‚ania OCR.

---

## KSeF

KSeF jest traktowany jako nadrzÄ™dne ĹşrĂłdĹ‚o danych faktury.

Kierunek produktu:

- w wersji bazowej KSeF moĹĽe dziaĹ‚aÄ‡ na ĹĽÄ…danie przez przycisk typu `SprawdĹş KSeF teraz`,
- automatyczne sprawdzanie KSeF nie musi byÄ‡ domyĹ›lnym zachowaniem,
- automatyzacja moĹĽe zostaÄ‡ dodana pĂłĹşniej jako funkcja wyĹĽszego pakietu, harmonogram dzienny lub konfigurowalny job.

Celem jest ograniczenie kosztĂłw i unikanie niepotrzebnego ciÄ…gĹ‚ego sprawdzania.

---

## WdroĹĽenie serwerowe i migracje

Projekt jest przygotowywany pod wdroĹĽenie serwerowe.

MoĹĽliwe kierunki infrastruktury:

- Railway,
- DigitalOcean,
- Fly.io,
- Google Cloud,
- Vercel,
- inne Ĺ›rodowiska serwerowe.

Ĺ»aden dostawca nie jest traktowany jako ostateczny wybĂłr na zawsze.

Projekt wspiera:

- `DATABASE_URL`,
- lokalny lub serwerowy storage,
- moĹĽliwoĹ›Ä‡ uĹĽycia wolumenu,
- migracjÄ™ z lokalnej `SQLite`,
- pĂłĹşniejszÄ… migracjÄ™ na `PostgreSQL`.

Migracja danych z lokalnej `SQLite` do skonfigurowanej bazy:

```bash
python migrate_sqlite_to_configured_db.py --source-sqlite data/invoice_ops.sqlite3 --reset-target
```

Po migracji trzeba jeszcze skopiowaÄ‡ magazyn plikĂłw dokumentĂłw i OCR.

---

## Railway

Projekt ma przygotowanie pod Railway, ale Railway nie jest jedynym moĹĽliwym kierunkiem wdroĹĽenia.

Obecne przygotowanie obejmuje:

- nasĹ‚uchiwanie na `0.0.0.0`,
- port z `PORT`,
- tryb `standalone`,
- endpoint zdrowia `GET /health`,
- konfiguracjÄ™ w `railway.json`,
- moĹĽliwoĹ›Ä‡ uĹĽycia PostgreSQL,
- moĹĽliwoĹ›Ä‡ uĹĽycia wolumenu pod pliki.

PrzykĹ‚adowe zmienne produkcyjne:

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

PrzykĹ‚adowy flow lokal -> serwer:

1. Uruchom szybkie testy:

```bash
python run_quality_checks.py --profile smoke
```
Kontrola aktywnego frontendu Next:

```bash
python run_quality_checks.py --profile frontend-smoke
```

Profil `frontend-smoke` uruchamia w katalogu `frontend/`:

- `npm.cmd run typecheck`,
- `npm.cmd run test:models`,
- `npm.cmd run build`.

Ten profil dotyczy docelowego frontendu `frontend/` (Next.js/React). Legacy `static/` nie jest rozwijane ani sprawdzane tym profilem.

2. Przed wdroĹĽeniem uruchom kontrolÄ™ predeploy:

```bash
python run_quality_checks.py --profile predeploy
```

3. Ustaw release id z aktualnego commita:

```bash
python sync_release_id.py
```

4. WdrĂłĹĽ aktualnÄ… wersjÄ™.

5. PorĂłwnaj Ĺ›rodowisko lokalne i zdalne:

```bash
python compare_environment_parity.py --remote-base https://<twoj-adres> --require-same-release --require-same-assets
```

---

## Pliki lokalnej konfiguracji

Lokalnie aplikacja moĹĽe czytaÄ‡:

```text
.env.local
data/local.env
```

PrzykĹ‚adowo moĹĽna skopiowaÄ‡:

```text
.env.local.example -> .env.local
```

WaĹĽne:

- pliki lokalne sÄ… prywatne,
- nie powinny trafiaÄ‡ do repozytorium,
- moĹĽna tam trzymaÄ‡ dane IMAP, OCR i inne lokalne sekrety,
- zmienne ustawione bezpoĹ›rednio w systemie majÄ… pierwszeĹ„stwo.

---

## NajwaĹĽniejsze endpointy

Wybrane endpointy:

```text
GET  /health
GET  /api/meta
GET  /api/session/current
POST /api/session/login
POST /api/session/logout

GET  /api/dashboard

GET  /api/invoices
GET  /api/invoices/{id}
PATCH /api/invoices/{id}
POST /api/invoices/{id}/actions/confirm-duplicate
POST /api/invoices/{id}/actions/reject-duplicate

GET  /api/tasks
GET  /api/tasks/{id}
POST /api/tasks
PATCH /api/tasks/{id}
POST /api/tasks/{id}/notes
POST /api/tasks/reminders/dispatch

GET  /api/work-items
GET  /api/work-items/summary
GET  /api/work-items/sla-policy
GET  /api/work-items/workload
POST /api/work-items
PATCH /api/work-items/{id}
POST /api/work-items/bulk

GET  /api/contractors
GET  /api/logs
GET  /api/search?q=...

GET  /api/organizations
POST /api/organizations
PATCH /api/organizations/{id}

GET  /api/users
POST /api/users
PATCH /api/users/{id}

GET  /api/knowledge/documents
POST /api/knowledge/documents
POST /api/knowledge/sync
POST /api/knowledge/documents/{id}/reprocess
POST /api/knowledge/ask

POST /api/import/KSeF
POST /api/import/EMAIL
POST /api/import/TELEGRAM
POST /api/telegram/webhook/{sekret}
```

PeĹ‚ny i aktualny stan endpointĂłw najlepiej weryfikowaÄ‡ w kodzie `app/api`.

---

## Integracje i miejsca do podmiany

NajwaĹĽniejsze pliki integracji:

```text
app/integrations/ksef_client.py
app/integrations/email_ingestion.py
app/integrations/telegram_bot.py
app/integrations/ocr_engine.py
```

Zasada:

Integracje powinny byÄ‡ wymienne i nie powinny mieszaÄ‡ siÄ™ bezpoĹ›rednio z logikÄ… biznesowÄ… moduĹ‚Ăłw.

---

## Kierunek dalszego rozwoju

NajwaĹĽniejsze kolejne kierunki:

- produkcyjny frontend `React / Next.js` w `frontend/`,
- wspĂłlny AppShell,
- centralna nawigacja,
- lepszy podziaĹ‚ frontendu na moduĹ‚y,
- stabilizacja API,
- migracja na PostgreSQL,
- zewnÄ™trzny storage plikĂłw,
- kolejki zadaĹ„,
- monitoring kosztĂłw AI,
- ogĂłlny system powiadomieĹ„,
- rozbudowa moduĹ‚u rozliczeĹ„ klientĂłw,
- integracja Telegram dla zadaĹ„,
- lepsze logi audytowe,
- role i capability w panelu,
- feature flags,
- pakiety klientĂłw,
- limity automatyzacji zaleĹĽne od planu,
- wdroĹĽenie produkcyjne.

---

## Zasada koĹ„cowa

CASI Workspace ma byÄ‡ rozwijane jako realna aplikacja operacyjna dla firm.

NajwaĹĽniejsze zasady:

- nie budowaÄ‡ prowizorki,
- nie komplikowaÄ‡ przedwczeĹ›nie,
- chroniÄ‡ separacjÄ™ danych organizacji,
- utrzymywaÄ‡ czytelny podziaĹ‚ warstw,
- rozwijaÄ‡ aplikacjÄ™ moduĹ‚owo,
- kontrolowaÄ‡ koszty automatyzacji,
- zostawiÄ‡ moĹĽliwoĹ›Ä‡ zmiany hostingu, storage i dostawcy AI,
- kaĹĽdy etap powinien przybliĹĽaÄ‡ projekt do stabilnego produktu.




