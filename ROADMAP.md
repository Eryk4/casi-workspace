# ROADMAP — CASI Workspace

Wersja: 2026-04-30  

Status: aktualna mapa rozwoju produktu  

Charakter dokumentu: kolejność prac, priorytety, decyzje odłożone i rzeczy, których na razie nie robić

---

## Cel dokumentu

Ten dokument określa kierunek rozwoju CASI Workspace.

Nie jest to lista marzeń ani przypadkowy backlog.

To mapa kolejności prac, która ma pomóc rozwijać aplikację jako realny produkt operacyjny, a nie jako zbiór przypadkowych modułów.

CASI Workspace ma być budowane etapami, ale każdy etap powinien przybliżać system do stabilnej aplikacji produkcyjnej.

Najważniejsza zasada:

> Najpierw stabilny fundament, potem kolejne moduły i automatyzacje.

---

# 1. Główna strategia rozwoju

CASI Workspace powinno być rozwijane według kolejności:

1. Stabilizacja fundamentu aplikacji.

2. Produkcyjny frontend w `frontend/`.

3. Uporządkowanie API, uprawnień i separacji organizacji.

4. Stabilizacja obecnych modułów.

5. Rozbudowa modułu rozliczeń klientów.

6. Integracje i automatyzacje.

7. AI i Asystent Firmowy.

8. Wdrożenie produkcyjne i skalowanie.

9. Pakiety, limity, monitoring kosztów i funkcje premium.

Nie należy rozwijać wszystkiego naraz.

Nie należy dodawać dużych modułów, jeśli podstawowe fundamenty są niestabilne.

---

# 2. Priorytet 1 — stabilizacja fundamentu

Najważniejszy pierwszy obszar to stabilny fundament aplikacji.

Obejmuje:

- repozytorium,

- strukturę folderów,

- uruchamianie lokalne,

- testy,

- bazę danych,

- migracje,

- API,

- logowanie,

- sesje,

- organizacje,

- użytkowników,

- role,

- capability,

- separację danych,

- storage plików,

- obsługę błędów,

- logi.

Cel:

> Aplikacja powinna być przewidywalna, uruchamialna, testowalna i bezpieczna na poziomie organizacji.

## Zadania

- Utrzymać obsługę lokalnego SQLite do szybkiego developmentu i testów.

- Utrzymać kierunek produkcyjny na PostgreSQL.

- Nie usuwać `DATABASE_URL`.

- Uporządkować migracje i skrypty uruchomieniowe.

- Upewnić się, że wszystkie główne rekordy biznesowe mają `organization_id`.

- Upewnić się, że API sprawdza organizację i uprawnienia.

- Utrzymać zasadę `default deny`.

- Uporządkować logi dla działań użytkowników i aktorów systemowych.

- Dbać, aby testy smoke i predeploy były łatwe do uruchomienia.

## Czego nie robić teraz

- Nie przepisywać całego backendu bez konkretnego powodu.

- Nie usuwać SQLite tylko dlatego, że produkcyjnie planowany jest PostgreSQL.

- Nie mieszać danych organizacji.

- Nie opierać bezpieczeństwa wyłącznie na frontendzie.

- Nie traktować obecnej aplikacji jako jednorazowej makiety.

---

# 3. Priorytet 2 — produkcyjny frontend w `frontend/`

Obecny frontend w `static/` jest działającą implementacją i punktem odniesienia.

Docelowy frontend produkcyjny powinien powstawać w:

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

- modułowa struktura funkcji,

- czysta warstwa komunikacji z API.

Cel:

> Zbudować produkcyjny frontend, który będzie łatwy do rozwijania o nowe moduły, zamiast ciągle poprawiać stary układ w `static/`.

## Zadania

- Utworzyć lub uporządkować katalog `frontend/`.

- Zbudować wspólny AppShell.

- Zbudować centralny config nawigacji.

- Przygotować podstawowe komponenty UI.

- Przygotować layout dla modułów.

- Przepisać najważniejsze widoki etapami.

- Najpierw przenieść strukturę i logikę, potem dopiero dopieszczać wygląd.

- Nie mieszać kodu `static/` i `frontend/`.

## Kolejność migracji widoków

Rekomendowana kolejność:

1. Pulpit.

2. Faktury.

3. Asystent Szefa.

4. Asystent Firmowy.

5. Kontrahenci.

6. Organizacje i użytkownicy.

7. Rozliczenia klientów.

8. Work Items i SLA.

9. Ustawienia.

## Czego nie robić teraz

- Nie udawać redesignu przez same kolory, kafelki i odstępy.

- Nie tworzyć osobnego layoutu dla każdego modułu.

- Nie robić finalnego frontendu w `static/`, jeśli celem jest `frontend/`.

- Nie usuwać starego frontendu, dopóki nowy nie zastąpi go bezpiecznie.

---

# 4. Priorytet 3 — API, role, capability i organizacje

Aplikacja ma działać w modelu wielu organizacji.

Każda akcja powinna respektować:

```text

rola + capability + zakres organizacji

```

Cel:

> Użytkownik widzi i zmienia tylko to, do czego ma prawo w swojej organizacji.

## Zadania

- Uporządkować sprawdzanie organizacji w API.

- Uporządkować capability dla modułów.

- Dodać brakujące capability dla rozliczeń, AI, integracji i logów.

- Rozdzielić zwykłych użytkowników od aktorów systemowych.

- Dbać o logowanie ważnych akcji.

- W przyszłości przygotować model `organization_memberships`, jeśli jeden użytkownik ma należeć do wielu organizacji.

## Szczególnie chronione obszary

- faktury,

- pliki,

- OCR,

- dokumenty,

- baza wiedzy,

- rozliczenia,

- wpłaty,

- wyciągi bankowe,

- dane dzieci,

- dane rodziców,

- umowy,

- konfiguracja integracji,

- dane AI.

## Czego nie robić teraz

- Nie dawać operatorowi domyślnie pełnego dostępu.

- Nie udostępniać rozliczeń bez osobnego capability.

- Nie pozwalać AI omijać uprawnień.

- Nie robić wyjątków bezpieczeństwa tylko dlatego, że jest szybciej.

---

# 5. Priorytet 4 — stabilizacja obecnych modułów

Zanim powstaną kolejne duże moduły, trzeba ustabilizować obecne.

Obecne kluczowe moduły:

- Faktury.

- Asystent Szefa.

- Asystent Firmowy.

- Kontrahenci.

- Organizacje.

- Użytkownicy.

- Work Items i SLA.

- Rozliczenia klientów — fundament.

Cel:

> Obecne moduły powinny być stabilne, zrozumiałe i gotowe do dalszej rozbudowy.

## Faktury

Kierunek:

- wspólna baza faktur,

- wiele źródeł,

- KSeF jako źródło nadrzędne,

- wykrywanie duplikatów,

- statusy,

- OCR,

- pliki,

- kontrahenci,

- logi.

Priorytety:

- poprawność statusów,

- przejrzyste powody duplikatów,

- jednoznaczna historia zdarzeń,

- brak mieszania danych organizacji,

- możliwość późniejszego spięcia z KSeF, e-mailem i Telegramem.

## Asystent Szefa

Kierunek:

- zadania,

- wydarzenia,

- przypomnienia,

- notatki,

- historia zmian,

- kalendarze,

- udostępnianie,

- przypisania,

- przyszłe automatyzacje Telegram / e-mail / Make.

Priorytety:

- stabilny model zadań,

- widoczność prywatna i organizacyjna,

- historia zmian,

- przypomnienia,

- prosty i szybki workflow.

## Asystent Firmowy

Kierunek:

- baza wiedzy organizacji,

- dokumenty,

- OCR,

- wersjonowanie,

- odpowiedzi z cytowaniami,

- capability,

- separacja organizacji.

Priorytety:

- kontrola dostępu,

- cytowania źródeł,

- statusy przetwarzania,

- błędy widoczne dla użytkownika,

- przyszły monitoring kosztów AI.

## Work Items i SLA

Kierunek:

- operacyjny triage,

- priorytety,

- SLA,

- eskalacje,

- obciążenie zespołu,

- akcje masowe.

Priorytety:

- czytelne statusy,

- dobre filtry,

- dobre sortowanie,

- historia działań,

- nieprzeciążanie UI.

---

# 6. Priorytet 5 — moduł rozliczeń klientów

Moduł rozliczeń klientów powinien być ogólnym modułem przychodowym dla organizacji.

Nie może być zawężony tylko do uczniów.

Właściwy kierunek:

```text

organizacje -> klienci organizacji -> usługi -> umowy -> naliczenia -> płatności

```

Nie zawężać do:

```text

organizacje -> uczniowie -> zajęcia

```

Cel:

> Zbudować moduł rozliczeń, który obsłuży klientów, płatników, dzieci, rodziny, wpłaty, naliczenia i dokumenty rozliczeniowe.

## Zakres wersji bazowej

Na start warto wdrożyć:

1. Klienci organizacji.

2. Role klienta: płatnik i beneficjent.

3. Relacje płatnik-beneficjent.

4. Słownik szkół.

5. Usługi.

6. Modele rozliczeń.

7. Umowy lub przypisania do usług.

8. Półautomatyczne generowanie należności.

9. Import wyciągów CSV.

10. Dopasowanie wpłat do płatnika.

11. Ręczne alokowanie wpłat.

12. Saldo płatnika.

13. Historia wpłat i należności.

## Szczególnie ważne dla szkoły robotyki

System musi obsłużyć:

- rodziny,

- rodziców,

- płatników,

- dzieci,

- rodzeństwo,

- wspólne wpłaty,

- zniżkę za rodzeństwo,

- KDR,

- szkoły,

- grupy,

- różne modele płatności,

- płatności miesięczne i semestralne,

- darmowe pierwsze zajęcia,

- ręczne korekty.

## Czego nie robić teraz

- Nie budować modułu tylko pod uczniów.

- Nie traktować numeru telefonu jako technicznego ID klienta.

- Nie zakładać, że jedna wpłata dotyczy jednego dziecka.

- Nie mieszać klientów przychodowych z kontrahentami kosztowymi.

- Nie wdrażać od razu pełnego panelu rodzica, jeśli operator nie ma jeszcze sprawnego panelu.

- Nie wdrażać integracji bankowej API, jeśli CSV wystarczy na start.

---

# 7. Priorytet 6 — integracje i automatyzacje

Integracje mają wspierać aplikację, ale nie powinny zastępować jej modelu danych.

Obszary integracji:

- e-mail,

- Telegram,

- KSeF,

- Make.com,

- Google Calendar,

- OCR,

- AI,

- przyszłe płatności online,

- przyszły storage zewnętrzny.

Cel:

> Integracje mają zasilać system danymi i akcjami, ale aplikacja powinna zachować własny stan i logikę biznesową.

## KSeF

W wersji bazowej preferowany model:

```text

Sprawdź KSeF teraz

```

Automatyczne sprawdzanie KSeF może być później:

- funkcją wyższego pakietu,

- harmonogramem dziennym,

- konfigurowalnym jobem,

- funkcją premium.

## E-mail

Kierunek:

- ręczne sprawdzanie skrzynki,

- test połączenia,

- opcjonalne cykliczne sprawdzanie,

- import dokumentów,

- status importu,

- logi importu.

## Telegram

Kierunek:

- przesyłanie faktur,

- przesyłanie dokumentów,

- przyszłe zadania,

- przypomnienia,

- komunikaty zwrotne,

- webhook z kontrolą organizacji.

## Make.com

Kierunek:

- używać praktycznie,

- nie odrzucać,

- nie budować całego produktu wyłącznie na Make,

- unikać ręcznego duplikowania pełnych scenariuszy dla każdego klienta,

- traktować Make jako warstwę integracji i automatyzacji.

## Czego nie robić teraz

- Nie uruchamiać stałego pollingowania, jeśli wystarczy akcja na żądanie.

- Nie budować pełnej automatyzacji bez statusów, logów i możliwości ponowienia.

- Nie ukrywać błędów integracji.

- Nie dawać integracjom globalnego dostępu bez potrzeby.

---

# 8. Priorytet 7 — AI i Asystent Firmowy

AI ma być używane tam, gdzie daje realną wartość.

Nie powinno być przypadkowo rozrzucone po kodzie.

Cel:

> AI powinno działać przez kontrolowaną warstwę usługową, z kontrolą kosztów, dostępów, źródeł i logów.

## Kierunek

- AI przez warstwę usługową.

- OCR przez warstwę usługową.

- Prompt, model i provider w przewidywalnym miejscu.

- Możliwość monitorowania kosztów.

- Odpowiedzi z cytowaniami.

- Brak dostępu do dokumentów spoza organizacji.

- Możliwość zmiany lub dodania providera w przyszłości.

## Możliwe źródła

- OpenAI,

- Make AI,

- lokalne parsowanie dokumentów,

- zewnętrzny OCR,

- przyszłościowo DigitalOcean AI lub inne usługi.

DigitalOcean AI nie jest obecnie ostatecznym wyborem architektury. Jest możliwą opcją do ponownej weryfikacji w przyszłości.

## Czego nie robić teraz

- Nie uzależniać całej aplikacji od jednego providera AI.

- Nie pozwalać AI omijać uprawnień.

- Nie robić odpowiedzi bez źródeł tam, gdzie wymagane są cytowania.

- Nie uruchamiać kosztownych operacji bez statusów i logów.

- Nie budować wielu providerów AI, zanim jeden przepływ działa stabilnie.

---

# 9. Priorytet 8 — deployment i infrastruktura

Aplikacja powinna być gotowa do wdrożenia serwerowego, ale nie powinna być sztywno przywiązana do jednej platformy.

Możliwe kierunki:

- Railway,

- DigitalOcean,

- Fly.io,

- Google Cloud,

- Vercel,

- inne środowiska serwerowe.

Cel:

> Zachować możliwość wdrożenia i migracji bez przepisywania całego produktu.

## Kierunek

- PostgreSQL jako preferowana baza produkcyjna.

- Możliwość lokalnego SQLite do dev/testów.

- Standardowe zmienne środowiskowe.

- `DATABASE_URL`.

- Storage możliwy do podmiany.

- Wolumen na start, object storage później.

- Healthcheck.

- Release ID.

- Parity local vs serwer po deployu.

## Czego nie robić teraz

- Nie traktować Railway jako jedynego wyboru na zawsze.

- Nie traktować DigitalOcean jako ostatecznego wyboru bez ponownej weryfikacji.

- Nie komplikować infrastruktury przedwcześnie.

- Nie robić deployu bez wyraźnej komendy użytkownika.

- Nie uruchamiać migracji produkcyjnych bez decyzji.

---

# 10. Priorytet 9 — pakiety, limity i monetyzacja

CASI Workspace powinno być gotowe na przyszłe pakiety klientów.

Nie trzeba wdrażać pełnego systemu billingowego SaaS od razu, ale architektura nie powinna tego blokować.

Kierunek:

- pakiety klientów,

- limity automatyzacji,

- limity AI,

- limity storage,

- częstotliwość sprawdzania KSeF,

- liczba użytkowników,

- liczba organizacji,

- dostęp do modułów,

- funkcje premium,

- monitoring kosztów.

Filozofia kosztów:

> Najpierw zmniejszać intensywność pracy systemu, a dopiero na końcu wyłączać funkcje.

Przykłady:

- tańszy pakiet: KSeF na żądanie,

- wyższy pakiet: KSeF raz dziennie,

- premium: częstsza automatyzacja,

- tańszy pakiet: dłuższa kolejka OCR,

- wyższy pakiet: szybsze przetwarzanie.

---

# 11. Decyzje odłożone na później

Te decyzje nie muszą być zamykane teraz:

- Ostateczny hosting produkcyjny.

- Ostateczny backend: Node.js czy dalszy rozwój Pythona.

- Ostateczny ORM.

- Ostateczny provider AI.

- Ostateczny storage plików.

- Pełny model multi-tenant z `organization_memberships`.

- Pełny panel klienta końcowego.

- Pełna integracja bankowa API.

- Pełny podpis elektroniczny.

- Pełne automatyczne sprawdzanie KSeF.

- Pełne pakiety i rozliczanie klientów SaaS.

- Pełny marketplace aplikacji lub większy ekosystem kilku produktów.

Zasada:

> Nie zamykać dużych decyzji za wcześnie, jeśli nie są potrzebne do najbliższego etapu.

---

# 12. Czego nie robić teraz

Na obecnym etapie nie należy:

- budować wszystkiego naraz,

- przepisywać całego backendu bez powodu,

- usuwać SQLite,

- mieszać `static/` i `frontend/`,

- traktować kosmetyki jako redesignu,

- przenosić całej logiki do Make.com,

- robić automatyzacji bez statusów i logów,

- ignorować organizacji i uprawnień,

- uruchamiać deployu bez komendy,

- budować pełnego enterprise multi-tenant przedwcześnie,

- budować pełnego systemu płatności SaaS przed stabilizacją modułów,

- robić wielu providerów AI, zanim podstawowy przepływ działa,

- zamykać się na jednego dostawcę infrastruktury,

- dodawać modułów, które psują spójność AppShella, API albo danych.

---

# 13. Kryteria gotowości większej zmiany

Większa zmiana powinna mieć:

- jasny zakres,

- listę zmienionych plików,

- opis, co zmieniono,

- opis ryzyka,

- informację, co sprawdzono,

- informację, czego nie sprawdzono,

- testy dobrane do zakresu,

- aktualizację dokumentacji, jeśli zmieniła się architektura lub zasady,

- wpis w `THREAD_CHANGELOG.md`, jeśli zmiana jest istotna.

Nie pisać, że coś działa, jeśli nie zostało sprawdzone.

---

# 14. Najbliższa rekomendowana kolejność prac

Najbardziej rozsądna kolejność na teraz:

1. Upewnić się, że dokumentacja projektowa jest spójna.

2. Wyczyścić pliki Markdown z technicznych atrybutów typu `id="..."`, jeśli gdzieś zostały wklejone.

3. Przejrzeć `AGENTS.md`, czy finalny frontend w `frontend/` jest opisany jako twarda zasada.

4. Ustalić pierwszy konkretny etap prac nad `frontend/`.

5. Zbudować AppShell i centralną nawigację w `frontend/`.

6. Przenieść pierwszy prosty widok do nowego frontendu.

7. Nie ruszać produkcji bez komendy.

8. Nie zaczynać wielu dużych modułów naraz.

9. Równolegle dopracowywać moduł rozliczeń tylko w zakresie wersji bazowej.

10. Pilnować testów smoke po większych zmianach.

---

# 15. Zasada końcowa

CASI Workspace ma być prawdziwą aplikacją operacyjną dla firm.

Ma być rozwijane etapami, ale z myśleniem o produkcie, bezpieczeństwie i przyszłej skali.

Najważniejsze:

- stabilny fundament,

- produkcyjny frontend,

- separacja organizacji,

- role i capability,

- modułowość,

- kontrola kosztów automatyzacji,

- sensowny moduł rozliczeń,

- integracje bez chaosu,

- AI z kontrolą dostępu i kosztów,

- infrastruktura bez niepotrzebnego vendor lock-in,

- rozwój bez prowizorki i bez przesadnego komplikowania.

