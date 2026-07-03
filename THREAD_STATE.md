# THREAD_STATE

Aktualny snapshot zasad pracy dla CASI Workspace.

Wersja: 2026-04-30  
Status: aktualny stan zasad między wątkami  
Charakter dokumentu: krótki snapshot najważniejszych zasad pracy

---

## 1. Repozytorium robocze

Pracujemy tylko w katalogu:

```text
C:\Users\erykl\OneDrive\Dokumenty\CASI Workspace
```

Zasady:

nie analizować, nie edytować i nie tworzyć kodu poza tym katalogiem,
jeśli terminal, Codex albo inne narzędzie startuje w innym miejscu, najpierw przejść do katalogu CASI Workspace,
to repozytorium jest źródłem prawdy dla projektu.

## 2. Charakter projektu

CASI Workspace nie jest demo, makietą ani jednorazowym panelem.

To realna aplikacja operacyjna rozwijana etapami.

Najważniejsze zasady:

nie budować prowizorki,
nie komplikować przedwcześnie,
rozwijać aplikację modułowo,
chronić separację organizacji,
nie psuć działającej logiki biznesowej,
zostawiać możliwość migracji i rozwoju,
kontrolować koszty automatyzacji.

## 3. Najważniejsze dokumenty

Przed większą pracą należy uwzględnić:

AGENTS.md — główne zasady pracy dla Codexa i developerów,
ARCHITECTURE.md — architektura aplikacji i kierunek rozwoju,
README.md — opis projektu i instrukcja startowa,
STARTER_WATKOW.md — szybki starter dla nowych wątków,
THREAD_STATE.md — aktualny snapshot zasad,
THREAD_CHANGELOG.md — wspólny dziennik zmian między wątkami.

Przy pracy nad konkretnym obszarem sprawdzić też dokument modułowy, np.:

MODUL_ROZLICZEN_KLIENTOW.md,
Role użytkowników.md.

## 4. Priorytet dokumentów

Jeżeli dokumenty są sprzeczne, stosować kolejność:

Bezpośrednie polecenie użytkownika w aktualnym wątku.
AGENTS.md.
ARCHITECTURE.md.
Dokument modułowy.
README.md.
STARTER_WATKOW.md.
THREAD_STATE.md.
THREAD_CHANGELOG.md.

Jeżeli sprzeczność dotyczy bezpieczeństwa, danych organizacji, uprawnień, produkcji albo migracji, zgłosić problem przed zmianą.

## 5. Tryb pracy

Domyślnie pracujemy lokalnie.

Bez wyraźnej komendy użytkownika:

brak deployu,
brak zmian produkcyjnych,
brak migracji produkcyjnych,
brak zmian sekretów produkcyjnych,
brak pracy poza lokalnym repozytorium.

Deploy na Railway tylko po wyraźnej komendzie użytkownika, np.:

wdroż na Railway

Railway jest jednym z możliwych kierunków wdrożenia, ale nie jest jedyną ani ostateczną platformą.

Możliwe kierunki infrastruktury:

Railway,
DigitalOcean,
Fly.io,
Google Cloud,
Vercel,
inne środowiska serwerowe.

## 6. Frontend

Obecny frontend:

static/

Status:

obecna działająca implementacja,
frontend referencyjny,
legacy / etap przejściowy.

Docelowy frontend produkcyjny:

frontend/

Kierunek:

React,
Next.js,
wspólny AppShell,
centralna konfiguracja nawigacji,
lewy sidebar jako główna nawigacja,
topbar jako pasek kontekstowy,
wspólne komponenty UI,
modułowa struktura funkcji.

Zasady:

nie mieszać static/ z frontend/,
nie traktować kosmetycznych zmian w static/ jako finalnego redesignu,
większy redesign traktować jako pracę architektoniczną.

## 7. Backend i baza danych

Obecna implementacja działa głównie w Pythonie.

Lokalny szybki dev/testy:

SQLite

Kierunek produkcyjny:

PostgreSQL

Zasady:

nie usuwać obsługi SQLite dla lokalnych testów bez jawnej decyzji,
nie przepisywać działającego backendu bez konkretnego powodu biznesowego lub technicznego,
DATABASE_URL powinien pozostać wspierany,
migracje i storage powinny być projektowane tak, aby późniejsza migracja była możliwa.

## 8. Local vs Railway

Po zleconym deployu należy wykonać parity-check.

Przykład:

python compare_environment_parity.py --remote-base https://<url-railway>

Jeżeli wymagane jest porównanie release/assets, użyć odpowiednich flag zgodnie z README.

Bez zleconego deployu nie sprawdzać Railway jako obowiązkowego kroku.

## 9. Organizacje, role i bezpieczeństwo

System działa w modelu organizacji.

Zasada krytyczna:

default deny

Jeżeli dostęp nie jest jasny, system powinien odmówić.

Każda akcja powinna sprawdzać:

użytkownika albo aktora systemowego,
organizację,
rolę,
capability,
zakres danych.

Model dostępu:

rola + capability + zakres organizacji

Szczególnie chronione dane:

faktury,
rozliczenia,
wpłaty,
wyciągi bankowe,
dane dzieci,
dane rodziców,
dane płatników,
dokumenty umów,
pliki,
OCR,
logi,
konfiguracja integracji,
dane AI.

## 10. Automatyzacje, AI i koszty

Domyślna filozofia kontroli kosztów:

nie wyłączać brutalnie funkcji, jeśli da się zmniejszyć intensywność pracy,
preferować kolejki,
preferować akcje na żądanie tam, gdzie to wystarczy,
ograniczać częstotliwość automatyzacji zależnie od pakietu, kosztów i potrzeb,
unikać niepotrzebnego ciągłego pollingowania.

KSeF w wersji bazowej może działać na żądanie, np.:

Sprawdź KSeF teraz

Automatyczne sprawdzanie KSeF może być dodane później jako:

funkcja wyższego pakietu,
harmonogram dzienny,
konfigurowalny job,
funkcja premium.

DigitalOcean AI może być rozważany w przyszłości jako element infrastruktury AI, ale nie jest obecnie ostatecznym wyborem architektury.

## 11. Make.com i integracje

Make.com może być używany jako praktyczna warstwa integracji i automatyzacji.

Zasady:

nie odrzucać Make.com automatycznie,
nie przenosić całej logiki biznesowej do Make.com,
aplikacja powinna mieć własny stan i model danych,
unikać ręcznego duplikowania pełnych scenariuszy dla każdego klienta, jeśli aplikacja może obsłużyć logikę centralnie.

Integracje i automatyzacje powinny działać tylko w przyznanym zakresie i być widoczne w logach jako aktorzy systemowi.

## 12. Moduł rozliczeń

Moduł rozliczeń klientów ma być ogólnym modułem przychodowym dla organizacji.

Właściwy kierunek:

organizacje -> klienci organizacji -> usługi -> umowy -> naliczenia -> płatności

Nie zawężać do:

organizacje -> uczniowie -> zajęcia

Dla firm edukacyjnych system musi obsłużyć:

płatników,
rodziny,
rodziców,
dzieci,
rodzeństwo,
wspólne wpłaty,
zniżki rodzinne,
KDR,
szkoły,
grupy,
umowy,
naliczenia,
alokacje wpłat.

Szczegóły są w:

MODUL_ROZLICZEN_KLIENTOW.md

## 13. Synchronizacja wątków

Przed większą pracą przeczytać:

THREAD_STATE.md,
ostatnie wpisy z THREAD_CHANGELOG.md.

Po większej zmianie:

dopisać wpis do THREAD_CHANGELOG.md,
zaktualizować THREAD_STATE.md, jeśli zmienił się realny stan zasad, architektury, modułu lub ważne ustalenie.

Najświeższy wpis w THREAD_CHANGELOG.md dodawać na górze.

## 14. Raport po zmianie

Po większej zmianie raport powinien zawierać:

Zmienione pliki.
Co zrobiono.
Dlaczego tak.
Ryzyko/skutki uboczne.
Co sprawdzono lokalnie.
Jakie testy uruchomiono.
Czego nie sprawdzono.
Co warto sprawdzić dalej.
Co sprawdzić na Railway lub innym serwerze — tylko jeśli był zlecony deploy.

Nie pisać, że testy przeszły, jeśli nie zostały uruchomione.

## 15. Testy

Podstawowy szybki test:

python run_quality_checks.py --profile smoke

Przed wdrożeniem:

python run_quality_checks.py --profile predeploy

Pełny test:

python run_quality_checks.py --profile full

Alternatywnie:

python -m unittest discover -s tests -v

Dobór testów powinien zależeć od zakresu zmiany.

## 16. Czego nie robić bez wyraźnej decyzji

Nie robić bez wyraźnej decyzji użytkownika:

deployu,
migracji produkcyjnej,
usunięcia danych,
usunięcia obsługi SQLite,
usunięcia istniejących endpointów,
zmiany modelu uprawnień,
przepisania całego backendu,
przeniesienia całej logiki do Make.com,
połączenia static/ i frontend/,
dodania nowego dostawcy AI jako trwałego wyboru,
zmiany infrastruktury jako ostatecznej decyzji,
wyłączenia ważnej funkcji zamiast zmniejszenia intensywności automatyzacji.

## 17. Najważniejsza myśl

CASI Workspace ma być budowane etapami, ale każdy etap powinien przybliżać aplikację do stabilnego produktu.

Nie budujemy prowizorki.

Nie komplikujemy przedwcześnie.

Chronimy dane organizacji.

Rozwijamy aplikację modułowo.

Pilnujemy kosztów automatyzacji.

Zostawiamy możliwość zmiany hostingu, storage, AI i integracji w przyszłości.
