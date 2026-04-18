# PROMPT DLA KOLEJNYCH WATKOW (CASI Workspace)

Skopiuj calosc ponizej do nowego watku, jesli ten watek ma wspoltworzyc aplikacje.

---
Pracujesz nad aplikacja `CASI Workspace` i MUSISZ trzymac sie aktualnego kontraktu technicznego.

## 1) Priorytet srodowisk
- Produkcja (Railway): docelowo `PostgreSQL`.
- Lokalny szybki dev i testy: dopuszczony `SQLite`.
- Kod nie moze zakladac tylko jednego backendu bez uzgodnienia.

## 2) Komendy srodowiskowe (obowiazujace)
- `Komendy/01 - Uruchom lokalnie.bat` -> wymusza `SQLite` (dev local).
- `Komendy/03 - Reset danych demo.bat` -> reset `SQLite` local.
- `Komendy/04 - Uruchom testy.bat` -> testy na `SQLite`.
- `Komendy/07 - Uruchom na PostgreSQL.bat` -> wymusza `PostgreSQL` i uruchamia tryb docelowy.

## 3) Sprawdzanie zgodnosci local vs Railway
- Uzyj skryptu: `python compare_environment_parity.py --remote-base https://<twoj-adres-railway>`
- Raport ma pokazac:
  - roznice w `/api/meta` (klucze i wartosci),
  - `app_release_id`,
  - `database_label` i `db_engine`,
  - wersje assetow frontendu (`styles.css?v=...`, `workspace-shell.css?v=...`, `knowledge-overrides.css?v=...`).
- Nie koncz pracy, dopoki krytyczne roznice nie sa wyjasnione.

## 4) Wersjonowanie runtime (obowiazkowe)
- `app_release_id` ma byc obecne w `/api/meta`.
- UI ma pokazywac `app_release_id` w informacji systemowej.
- Przy wdrozeniu ustawiaj `INVOICE_APP_RELEASE_ID` (np. `2026-04-18.a`).

## 5) Stan UI i UX (nie cofaj)
- Interfejs dziala jako workspace z zakladkami/modulami (m.in. Pulpit, Faktury, Asystent Firmowy, Asystent Szefa, Kontrahenci itd.).
- Dodatkowo istnieja panele szybkie (quick workspace / quick calendar) oraz karuzela modulow.
- Nie wracac do starego jednolitego ukladu bez uzgodnienia.

## 6) Kryterium "dziala"
Zmiana jest uznana za gotowa tylko gdy:
1. `python -m unittest discover -s tests -v` przechodzi lokalnie (albo profile quality checks, jesli uzgodnione).
2. Lokalnie dziala podstawowy smoke: `/health`, `/api/meta`, logowanie, glowna nawigacja i kluczowe przyciski w zmienianym module.
3. Po wdrozeniu Railway porownanie parity nie pokazuje krytycznych rozjazdow.

## 7) Zakazy
- Nie usuwaj obslugi SQLite dla testow lokalnych bez jawnej decyzji.
- Nie dodawaj "tymczasowych" obejsc typu pomijanie initu bazy w normalnym starcie produkcyjnym.
- Nie mieszaj konfiguracji local/prod w jednym skrypcie startowym.

## 8) Co raportowac po kazdej wiekszej zmianie
- Jakie pliki zmieniono.
- Jak uruchamiac lokalnie (SQLite) i docelowo (PostgreSQL).
- Wynik testow i parity report.
- Co trzeba ustawic na Railway (env + release id).
---
