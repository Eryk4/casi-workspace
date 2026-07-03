# PROMPT DLA KOLEJNYCH WĄTKÓW — CASI Workspace

Wersja: 2026-04-30  
Status: prompt startowy do kopiowania w nowe wątki współtworzące aplikację  
Charakter dokumentu: skrócony kontekst dla Codexa / nowego wątku

---

## Jak używać

Skopiuj całość poniżej do nowego wątku, jeśli ten wątek ma współtworzyć aplikację CASI Workspace.

---

Pracujesz nad aplikacją `CASI Workspace`.

To jest realna aplikacja operacyjna rozwijana etapami, a nie demo, makieta ani prowizorka.

Musisz trzymać się aktualnych zasad projektu, architektury, bezpieczeństwa i pracy między wątkami.

---

# 1. Repozytorium robocze

Pracujemy tylko w katalogu:

```text
C:\Users\erykl\OneDrive\Dokumenty\CASI Workspace
```

Zasady:

- nie analizuj, nie edytuj i nie twórz kodu poza tym katalogiem,
- jeśli terminal albo narzędzie startuje w innym miejscu, najpierw przejdź do katalogu CASI Workspace,
- traktuj to repozytorium jako źródło prawdy dla projektu.

---

# 2. Dokumenty obowiązkowe przed większą pracą

Przed większą zmianą przeczytaj albo uwzględnij:

1. `AGENTS.md` — główne zasady pracy dla Codexa i developerów.
2. `ARCHITECTURE.md` — architektura aplikacji i kierunek rozwoju.
3. `README.md` — opis projektu i instrukcja startowa.
4. `THREAD_STATE.md` — aktualny snapshot zasad.
5. Ostatnie wpisy z `THREAD_CHANGELOG.md` — ostatnie zmiany i decyzje.
6. Dokument modułowy, jeśli pracujesz nad konkretnym obszarem, np.:
   - `MODUL_ROZLICZEN_KLIENTOW.md`
   - `Role użytkowników.md`

Jeżeli dokumenty są sprzeczne, stosuj priorytet:

1. bezpośrednie polecenie użytkownika w aktualnym wątku,
2. `AGENTS.md`,
3. `ARCHITECTURE.md`,
4. dokument modułowy,
5. `README.md`,
6. `STARTER_WATKOW.md`,
7. `THREAD_STATE.md`,
8. `THREAD_CHANGELOG.md`.

Jeżeli sprzeczność dotyczy bezpieczeństwa, danych organizacji, uprawnień, produkcji albo migracji, zgłoś problem przed zmianą.

---

# 3. Tryb pracy i deploy

Domyślnie pracujemy lokalnie.

Bez wyraźnej komendy użytkownika:

- brak deployu,
- brak zmian produkcyjnych,
- brak migracji produkcyjnych,
- brak zmian sekretów produkcyjnych,
- brak pracy poza lokalnym repozytorium.

Deploy na Railway tylko po wyraźnej komendzie użytkownika, np.:

```text
wdroż na Railway
```

Railway jest jednym z możliwych kierunków wdrożenia, ale nie jest jedyną ani ostateczną platformą.

Możliwe kierunki infrastruktury:

- Railway,
- DigitalOcean,
- Fly.io,
- Google Cloud,
- Vercel,
- inne środowiska serwerowe.

---

# 4. Baza danych i środowiska

Aktualna implementacja działa głównie w Pythonie.

Lokalny szybki dev i testy:

```text
SQLite
```

Kierunek produkcyjny:

```text
PostgreSQL
```

Zasady:

- nie usuwaj obsługi SQLite dla lokalnych testów bez jawnej decyzji,
- nie przepisuj działającego backendu bez konkretnego powodu biznesowego albo technicznego,
- `DATABASE_URL` powinien pozostać wspierany,
- migracje i storage powinny być projektowane tak, aby późniejsza migracja była możliwa,
- kod nie powinien zakładać wyłącznie jednego backendu bez uzgodnienia.

---

# 5. Komendy środowiskowe

Obecne komendy pomocnicze:

```text
Komendy/01 - Uruchom lokalnie.bat
Komendy/03 - Reset danych demo.bat
Komendy/04 - Uruchom testy.bat
Komendy/07 - Uruchom na PostgreSQL.bat
```

Znaczenie:

- `01 - Uruchom lokalnie.bat` — lokalny start aplikacji,
- `03 - Reset danych demo.bat` — reset lokalnych danych demo,
- `04 - Uruchom testy.bat` — testy lokalne,
- `07 - Uruchom na PostgreSQL.bat` — uruchomienie w trybie PostgreSQL, jeśli środowisko jest skonfigurowane.

Nie mieszaj konfiguracji local/prod w jednym skrypcie startowym bez jasnego powodu.

---

# 6. Frontend

Obecny frontend:

```text
static/
```

Status:

- obecna działająca implementacja,
- frontend referencyjny,
- legacy / etap przejściowy.

Docelowy frontend produkcyjny:

```text
frontend/
```

Kierunek:

- React,
- Next.js,
- wspólny AppShell,
- centralna konfiguracja nawigacji,
- lewy sidebar jako główna nawigacja,
- topbar jako pasek kontekstowy,
- wspólne komponenty UI,
- modułowa struktura funkcji.

Zasady:

- nie mieszaj `static/` z docelowym frontendem `frontend/`,
- nie traktuj kosmetycznych zmian w `static/` jako finalnego redesignu,
- większy redesign traktuj jako pracę architektoniczną,
- nie wracaj do starego jednolitego układu bez uzgodnienia,
- nie udawaj redesignu, jeśli zmieniono tylko kafelki, odstępy albo kolory.

---

# 7. UI i UX — czego nie cofać

Interfejs działa jako workspace z modułami, między innymi:

- Pulpit,
- Faktury,
- Asystent Firmowy,
- Asystent Szefa,
- Kontrahenci,
- Organizacje,
- Użytkownicy,
- Rozliczenia klientów,
- Work Items i SLA.

Istnieją też elementy pomocnicze, takie jak szybkie panele, widoki robocze albo modułowe układy obecnego interfejsu.

Nie cofaj obecnego kierunku UI bez uzgodnienia.

Docelowo jednak najważniejszy jest produkcyjny frontend w `frontend/`, zgodny z AppShellem i centralną nawigacją.

---

# 8. Organizacje, role i bezpieczeństwo

System działa w modelu organizacji.

Zasada krytyczna:

```text
default deny
```

Jeżeli dostęp nie jest jasny, system powinien odmówić.

Każda akcja powinna sprawdzać:

- użytkownika albo aktora systemowego,
- organizację,
- rolę,
- capability,
- zakres danych.

Model dostępu:

```text
rola + capability + zakres organizacji
```

Szczególnie chronione dane:

- faktury,
- rozliczenia,
- wpłaty,
- wyciągi bankowe,
- dane dzieci,
- dane rodziców,
- dane płatników,
- dokumenty umów,
- pliki,
- OCR,
- logi,
- konfiguracja integracji,
- dane AI.

Nie sprawdzaj uprawnień tylko w UI. Backend/API musi egzekwować dostęp.

---

# 9. Automatyzacje, AI i koszty

Domyślna filozofia kontroli kosztów:

- nie wyłączać brutalnie funkcji, jeśli da się zmniejszyć intensywność pracy,
- preferować kolejki,
- preferować akcje na żądanie tam, gdzie to wystarczy,
- ograniczać częstotliwość automatyzacji zależnie od pakietu, kosztów i potrzeb,
- unikać niepotrzebnego ciągłego pollingowania.

KSeF w wersji bazowej może działać na żądanie, np.:

```text
Sprawdź KSeF teraz
```

Automatyczne sprawdzanie KSeF może być dodane później jako:

- funkcja wyższego pakietu,
- harmonogram dzienny,
- konfigurowalny job,
- funkcja premium.

AI i OCR powinny działać przez warstwę usługową, a nie być rozrzucone przypadkowo po kodzie.

DigitalOcean AI może być rozważany w przyszłości jako element infrastruktury AI, ale nie jest obecnie ostatecznym wyborem architektury.

---

# 10. Make.com i integracje

Make.com może być używany jako praktyczna warstwa integracji i automatyzacji.

Może wspierać:

- Telegram,
- e-mail,
- powiadomienia,
- integracje zewnętrzne,
- szybkie prototypowanie,
- automatyzacje specyficzne dla klienta.

Zasady:

- nie odrzucaj Make.com automatycznie,
- nie przenoś całej logiki biznesowej do Make.com,
- aplikacja powinna mieć własny stan i model danych,
- unikaj ręcznego duplikowania pełnych scenariuszy dla każdego klienta, jeśli aplikacja może obsłużyć logikę centralnie,
- integracje i automatyzacje powinny działać tylko w przyznanym zakresie,
- działania integracji powinny być widoczne w logach jako aktorzy systemowi.

---

# 11. Moduł rozliczeń

Moduł rozliczeń klientów ma być ogólnym modułem przychodowym dla organizacji.

Właściwy kierunek:

```text
organizacje -> klienci organizacji -> usługi -> umowy -> naliczenia -> płatności
```

Nie zawężać do:

```text
organizacje -> uczniowie -> zajęcia
```

Dla firm edukacyjnych system musi obsłużyć:

- płatników,
- rodziny,
- rodziców,
- dzieci,
- rodzeństwo,
- wspólne wpłaty,
- zniżki rodzinne,
- KDR,
- szkoły,
- grupy,
- umowy,
- naliczenia,
- alokacje wpłat.

Szczegóły są w:

```text
MODUL_ROZLICZEN_KLIENTOW.md
```

---

# 12. Sprawdzanie zgodności local vs Railway

Po zleconym deployu należy wykonać parity-check.

Podstawowa komenda:

```bash
python compare_environment_parity.py --remote-base https://<twoj-adres-railway>
```

Jeżeli wymagane jest porównanie release/assets, użyj odpowiednich flag zgodnie z README, np.:

```bash
python compare_environment_parity.py --remote-base https://<twoj-adres-railway> --require-same-release --require-same-assets
```

Raport powinien pokazać między innymi:

- różnice w `/api/meta`,
- `app_release_id`,
- `database_label`,
- `db_engine`,
- wersje assetów frontendu.

Bez zleconego deployu nie traktuj Railway jako obowiązkowego kroku.

---

# 13. Wersjonowanie runtime

`app_release_id` powinno być obecne w `/api/meta`.

UI powinno pokazywać `app_release_id` w informacji systemowej.

Przy wdrożeniu ustawiaj `INVOICE_APP_RELEASE_ID`, np.:

```text
2026-04-30.a
```

Po wdrożeniu należy upewnić się, że lokalny i zdalny release są zgodne, jeśli zadanie wymaga parity-check.

---

# 14. Kryterium „działa”

Zmiana jest gotowa tylko wtedy, gdy jest sprawdzona odpowiednio do zakresu.

Minimalnie należy jasno określić:

- co zmieniono,
- co sprawdzono,
- jakich testów użyto,
- czego nie sprawdzono,
- jakie są ryzyka.

Dla zwykłej pracy lokalnej preferowany smoke:

```bash
python run_quality_checks.py --profile smoke
```

Przed wdrożeniem:

```bash
python run_quality_checks.py --profile predeploy
```

Pełny test:

```bash
python run_quality_checks.py --profile full
```

Alternatywnie:

```bash
python -m unittest discover -s tests -v
```

Jeżeli testy nie zostały uruchomione, raport musi to jasno powiedzieć.

Nie wolno pisać, że testy przeszły, jeśli nie zostały uruchomione.

Po wdrożeniu Railway parity-check nie powinien pokazywać krytycznych rozjazdów, chyba że zostały świadomie wyjaśnione.

---

# 15. Zakazy bez wyraźnej decyzji

Nie rób bez wyraźnej decyzji użytkownika:

- deployu,
- migracji produkcyjnej,
- usunięcia danych,
- usunięcia obsługi SQLite,
- usunięcia istniejących endpointów,
- zmiany modelu uprawnień,
- przepisania całego backendu,
- przeniesienia całej logiki do Make.com,
- połączenia `static/` i `frontend/`,
- dodania nowego dostawcy AI jako trwałego wyboru,
- zmiany infrastruktury jako ostatecznej decyzji,
- wyłączenia ważnej funkcji zamiast zmniejszenia intensywności automatyzacji,
- dodawania tymczasowych obejść typu pomijanie normalnego initu bazy w starcie produkcyjnym,
- mieszania konfiguracji local/prod w jednym skrypcie startowym bez jasnego powodu.

---

# 16. Synchronizacja wątków

Przed większą pracą przeczytaj:

- `THREAD_STATE.md`,
- ostatnie wpisy z `THREAD_CHANGELOG.md`.

Po większej zmianie:

- dopisz wpis do `THREAD_CHANGELOG.md`,
- zaktualizuj `THREAD_STATE.md`, jeśli zmienił się realny stan zasad, architektury, modułu albo ważne ustalenie.

Najświeższy wpis w `THREAD_CHANGELOG.md` dodawaj na górze.

---

# 17. Co raportować po każdej większej zmianie

Raport powinien zawierać:

1. Zmienione pliki.
2. Co zrobiono.
3. Dlaczego tak.
4. Ryzyko i możliwe skutki uboczne.
5. Jak uruchamiać lokalnie.
6. Jak uruchamiać docelowo, jeśli dotyczy.
7. Jakie testy uruchomiono.
8. Wynik testów.
9. Czego nie sprawdzono.
10. Co trzeba ustawić na Railway lub innym serwerze, jeśli był deploy.
11. Wynik parity report, jeśli był deploy.
12. Co warto sprawdzić dalej.

Nie ukrywaj niepewności.

Jeżeli czegoś nie sprawdzono, napisz to wprost.

---

# 18. Najważniejsza myśl

CASI Workspace ma być budowane etapami, ale każdy etap powinien przybliżać aplikację do stabilnego produktu.

Nie budujemy prowizorki.

Nie komplikujemy przedwcześnie.

Chronimy dane organizacji.

Rozwijamy aplikację modułowo.

Pilnujemy kosztów automatyzacji.

Zostawiamy możliwość zmiany hostingu, storage, AI i integracji w przyszłości.