# STARTER WĄTKÓW — CASI Workspace

Wersja: 2026-04-29  
Status: plik startowy dla nowych i aktualnych wątków pracy nad CASI Workspace  
Charakter dokumentu: szybkie przypomnienie zasad pracy, kontekstu projektu i raportowania zmian

---

## Cel pliku

Ten plik służy jako szybki start dla nowych wątków z Codexem albo innym narzędziem pomagającym rozwijać aplikację.

Nie zastępuje:

- `AGENTS.md`,
- `ARCHITECTURE.md`,
- `README.md`,
- dokumentów modułowych.

Ten plik ma przypomnieć najważniejsze zasady przed rozpoczęciem pracy.

---

# 1. Repozytorium robocze

Pracujemy tylko w katalogu:

```text
C:\Users\erykl\OneDrive\Dokumenty\CASI Workspace
```

Zasady:

nie analizuj, nie edytuj i nie twórz kodu poza tym katalogiem,
jeżeli terminal, narzędzie albo wątek startuje w innym katalogu, najpierw przejdź do katalogu CASI Workspace,
traktuj to repozytorium jako źródło prawdy dla projektu.

# 2. Najważniejsze dokumenty do przeczytania

Przed większą pracą przeczytaj albo uwzględnij:

AGENTS.md — jak pracować nad projektem,
ARCHITECTURE.md — jak aplikacja jest zbudowana i w jakim kierunku ma się rozwijać,
README.md — praktyczny opis projektu i uruchomienie,
THREAD_STATE.md — aktualny stan wątku/projektu,
ostatnie wpisy z THREAD_CHANGELOG.md — ostatnie zmiany i decyzje.

Przy pracy nad konkretnym modułem sprawdź też odpowiedni dokument, na przykład:

MODUL_ROZLICZEN_KLIENTOW.md,
Role użytkowników.md.

# 3. Priorytet dokumentów

Jeżeli dokumenty są sprzeczne, stosuj tę kolejność:

Bezpośrednie polecenie użytkownika w aktualnym wątku.
AGENTS.md.
ARCHITECTURE.md.
Dokument modułowy, na przykład MODUL_ROZLICZEN_KLIENTOW.md.
README.md.
THREAD_STATE.md.
THREAD_CHANGELOG.md.

Jeżeli sprzeczność dotyczy bezpieczeństwa, danych organizacji, uprawnień albo produkcji, zatrzymaj się i zgłoś problem.

# 4. Charakter projektu

CASI Workspace nie jest demo, makietą ani jednorazowym panelem.

To realna aplikacja operacyjna rozwijana etapami.

Najważniejsze zasady:

nie budować prowizorki,
nie komplikować przedwcześnie,
rozwijać aplikację modułowo,
chronić separację organizacji,
nie psuć działającej logiki biznesowej,
zostawić możliwość rozwoju, migracji i zmiany infrastruktury,
traktować frontend, backend, dane i automatyzacje jako części jednego produktu.

# 5. Frontend

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

nie mieszać static/ z docelowym frontendem frontend/,
nie traktować kosmetycznych zmian w static/ jako finalnego redesignu,
większy redesign traktować jako pracę architektoniczną, nie tylko zmianę kolorów i kafelków.

# 6. Backend, baza i migracje

Obecna implementacja działa głównie w Pythonie.

Lokalnie dopuszczone jest:

SQLite

Kierunek produkcyjny:

PostgreSQL

Zasady:

nie usuwać obsługi SQLite dla lokalnych testów bez wyraźnej decyzji,
nie przepisywać działającego backendu tylko dlatego, że w przyszłości możliwy jest inny stack,
DATABASE_URL powinien pozostać wspierany,
migracje i storage powinny być projektowane tak, aby późniejsza migracja była możliwa.

# 7. Deploy i produkcja

Domyślnie pracujemy lokalnie.

Nie wdrażaj na Railway ani na żadną inną platformę bez wyraźnej komendy użytkownika.

Dla Railway komenda użytkownika może brzmieć na przykład:

wdroż na Railway

Bez wyraźnej komendy:

brak deployu,
brak zmian produkcyjnych,
brak zmian w środowisku produkcyjnym,
brak uruchamiania migracji produkcyjnych,
brak modyfikowania produkcyjnych sekretów.

Railway jest obecnie jednym z możliwych kierunków wdrożenia, ale nie jest jedyną ani ostateczną platformą.

Inne możliwe kierunki:

DigitalOcean,
Fly.io,
Google Cloud,
Vercel,
inne środowiska serwerowe.

# 8. Organizacje i bezpieczeństwo danych

To jest zasada krytyczna.

Każda akcja powinna sprawdzać:

użytkownika albo aktora systemowego,
organizację,
uprawnienia,
capability,
zakres danych.

Użytkownik organizacji nie może widzieć danych innej organizacji.

Dotyczy to szczególnie:

faktur,
kontrahentów,
zadań,
dokumentów,
bazy wiedzy,
rozliczeń,
wpłat,
wyciągów bankowych,
danych dzieci,
danych rodziców,
plików,
OCR,
logów.

Zasada:

default deny

Jeżeli dostęp nie jest jasny, system powinien odmówić.

# 9. Role i capability

CASI używa modelu:

rola + capability + zakres organizacji

Rola określa ogólną odpowiedzialność użytkownika.

Capability określa konkretną funkcję albo akcję.

Nie zakładaj, że sama rola wystarcza do każdej operacji.

Szczególnie ostrożnie traktuj:

rozliczenia,
import wyciągów bankowych,
dane dzieci,
dane rodziców,
dokumenty umów,
konfigurację integracji,
AI,
logi techniczne,
dane wrażliwe.

# 10. Automatyzacje, AI i koszty

Domyślna filozofia kontroli kosztów:

nie wyłączać brutalnie funkcji, jeśli da się zmniejszyć intensywność pracy,
preferować kolejki,
preferować akcje na żądanie tam, gdzie to wystarczy,
ograniczać częstotliwość automatyzacji zależnie od pakietu, kosztów i potrzeb,
unikać niepotrzebnego ciągłego pollingowania.

KSeF w wersji bazowej może działać na żądanie, na przykład:

Sprawdź KSeF teraz

Automatyczne sprawdzanie KSeF może być dodane później jako:

funkcja wyższego pakietu,
harmonogram dzienny,
konfigurowalny job,
funkcja premium.

AI i OCR powinny działać przez warstwę usługową, a nie być rozrzucone przypadkowo po kodzie.

DigitalOcean AI może być rozważany w przyszłości, ale nie jest obecnie ostatecznym wyborem architektury.

# 11. Make.com i integracje

Make.com może być używany praktycznie jako warstwa integracji i automatyzacji.

Może wspierać:

Telegram,
e-mail,
powiadomienia,
integracje zewnętrzne,
szybkie prototypowanie,
automatyzacje specyficzne dla klienta.

Zasady:

nie odrzucać Make.com automatycznie,
nie przenosić całej logiki biznesowej do Make.com, jeśli aplikacja powinna mieć własny stan i model danych,
unikać modelu, w którym dla każdego klienta trzeba ręcznie duplikować pełny scenariusz, jeśli aplikacja może obsłużyć to centralnie.

# 12. Moduł rozliczeń

Moduł rozliczeń klientów ma być ogólnym modułem przychodowym dla organizacji.

Nie budować go wyłącznie jako modułu uczniów.

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

Szczegóły są opisane w:

MODUL_ROZLICZEN_KLIENTOW.md

# 13. Praca z kodem

Przed zmianami:

sprawdź aktualną strukturę,
ustal, czy plik należy do static/, frontend/, backendu, testów czy dokumentacji,
nie zmieniaj losowo wielu plików bez potrzeby,
nie usuwaj działającej logiki bez powodu,
nie zmieniaj pól bazy, API, migracji ani integracji bez zrozumienia skutków.

Przy większych zmianach:

najpierw napraw fundament,
potem moduły,
potem UI,
na końcu kosmetyka.

Nie udawaj redesignu, jeśli zmieniono tylko kafelki, odstępy albo kolory.

# 14. Testy

Po zmianach dobierz testy do zakresu pracy.

Podstawowe komendy:

python run_quality_checks.py --profile smoke

Przed wdrożeniem:

python run_quality_checks.py --profile predeploy

Pełny test:

python run_quality_checks.py --profile full

Albo:

python -m unittest discover -s tests -v

Jeżeli nie uruchomiono testów, raport musi to jasno powiedzieć.

Nie pisać „testy przeszły”, jeśli nie zostały uruchomione.

# 15. Synchronizacja wątków

Przed większą pracą przeczytaj:

THREAD_STATE.md,
ostatnie wpisy z THREAD_CHANGELOG.md.

Po większej zmianie:

dopisz wpis do THREAD_CHANGELOG.md,
zaktualizuj THREAD_STATE.md, jeśli zmienił się realny stan projektu, architektury, modułu albo ważne ustalenie.

Nie aktualizuj changeloga dla zupełnie drobnych zmian, jeśli użytkownik tego nie oczekuje.

# 16. Raport po zmianie

Po wykonaniu pracy przygotuj krótki raport.

Raport powinien zawierać:

Zmienione pliki.
Co zrobiono.
Dlaczego tak.
Ryzyko i możliwe skutki uboczne.
Co sprawdzono lokalnie.
Jakie testy uruchomiono.
Czego nie sprawdzono.
Co warto sprawdzić dalej.
Co sprawdzić na Railway albo innym serwerze — tylko jeśli był zlecony deploy.

Nie ukrywaj niepewności.

Jeżeli czegoś nie sprawdzono, napisz to wprost.

# 17. Gdy zadanie jest niejasne

Jeżeli zadanie jest niejasne:

nie zgaduj losowo,
zaproponuj rozsądne założenie,
zapytaj o doprecyzowanie, jeśli decyzja może mieć duży wpływ,
przy małych rzeczach możesz przyjąć bezpieczne założenie i je opisać.

Jeżeli zadanie dotyczy danych, bezpieczeństwa, produkcji, migracji albo kosztownych automatyzacji, lepiej zatrzymać się i wyjaśnić założenia.

# 18. Czego nie robić bez wyraźnej decyzji

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

# 19. Najważniejsza myśl

CASI Workspace ma być budowane etapami, ale każdy etap powinien przybliżać aplikację do stabilnego produktu.

Nie budujemy prowizorki.

Nie komplikujemy przedwcześnie.

Chronimy dane organizacji.

Rozwijamy aplikację modułowo.

Pilnujemy kosztów automatyzacji.

Zostawiamy możliwość zmiany hostingu, storage, AI i integracji w przyszłości.
