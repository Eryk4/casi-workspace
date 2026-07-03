# Role użytkowników

Wersja: 2026-04-29  
Status: model ról, uprawnień i capability dla CASI Workspace  
Charakter dokumentu: zasady dostępu użytkowników, organizacji, modułów, danych i automatyzacji

---

## Status dokumentu

Ten dokument opisuje model ról użytkowników w CASI Workspace.

Role nie powinny być jedynym mechanizmem uprawnień.

Docelowy model powinien łączyć:

- role,
- capability,
- zakres organizacji,
- typ użytkownika,
- logi audytowe,
- przyszłe pakiety,
- funkcje premium,
- aktorów systemowych, takich jak integracje, workery i automatyzacje.

Najważniejsza zasada:

> Rola określa ogólną odpowiedzialność użytkownika, a capability określa konkretne funkcje, do których użytkownik ma dostęp.

Druga najważniejsza zasada:

> Jeżeli użytkownik albo aktor systemowy nie ma wyraźnie przyznanego dostępu przez rolę, capability i zakres organizacji, system powinien odmówić dostępu.

To oznacza model `default deny`.

Domyślnie dostęp jest zablokowany, a dopiero rola, capability i zakres organizacji pozwalają wykonać akcję.

---

# 1. Główna zasada bezpieczeństwa

Każda akcja w systemie powinna sprawdzać trzy rzeczy:

1. Kim jest użytkownik albo aktor systemowy.
2. Do jakiej organizacji należy dana akcja lub rekord.
3. Czy użytkownik ma rolę albo capability pozwalające wykonać tę akcję.

Nie wystarczy sprawdzać dostępu tylko w frontendzie.

Uprawnienia muszą być egzekwowane po stronie backendu/API.

Zasada:

> Frontend może ukrywać przyciski, ale backend musi blokować niedozwolone akcje.

---

# 2. Rola vs capability

## Rola

Rola określa ogólny poziom odpowiedzialności użytkownika.

Przykłady ról:

- Właściciel systemu,
- Administrator organizacji,
- Koordynator,
- Operator,
- Gość.

Rola odpowiada na pytanie:

> Jaką funkcję pełni ta osoba w systemie?

## Capability

Capability to konkretne uprawnienie do funkcji lub akcji.

Przykłady capability:

- `invoices.read`
- `invoices.update`
- `billing.import_bank_statements`
- `knowledge.upload`
- `tasks.assign`
- `integrations.manage_telegram`

Capability odpowiada na pytanie:

> Co dokładnie ta osoba może zrobić?

## Relacja między rolą i capability

Rola może dawać domyślny zestaw uprawnień, ale capability może go doprecyzować.

Capability może:

- rozszerzyć dostęp użytkownika,
- ograniczyć dostęp użytkownika,
- nadać dostęp tylko do wybranego modułu,
- nadać dostęp tylko do wybranej akcji,
- różnicować użytkowników z tą samą rolą.

Przykład:

Dwóch operatorów może mieć tę samą rolę `Operator`, ale różne capability.

Operator A może mieć:

- `tasks.read`
- `tasks.update`
- `invoices.read`

Operator B może mieć:

- `tasks.read`
- `tasks.update`
- `billing.import_bank_statements`

Dzięki temu nie trzeba tworzyć osobnej roli dla każdego wariantu pracy.

Zasada:

> Role powinny być proste i zrozumiałe, a szczegóły dostępu powinny być kontrolowane przez capability.

---

# 3. Zakres organizacji

Uprawnienia użytkownika zawsze muszą być sprawdzane razem z zakresem organizacji.

To oznacza:

- użytkownik organizacji widzi tylko dane swojej organizacji,
- administrator organizacji zarządza tylko swoją organizacją,
- koordynator działa tylko w swojej organizacji,
- operator działa tylko w swojej organizacji,
- gość widzi tylko dane swojej organizacji,
- właściciel systemu ma możliwość działania globalnego, ale powinien używać jej ostrożnie i tylko w uzasadnionych przypadkach.

Zasada:

> Capability bez sprawdzenia organizacji nie wystarcza.

Przykład:

Użytkownik może mieć capability `invoices.read`, ale to nie oznacza, że może czytać faktury wszystkich organizacji.

Może czytać tylko faktury w zakresie swojej organizacji, chyba że jest właścicielem systemu albo ma specjalny globalny zakres administracyjny.

---

# 4. Poziomy użytkowników

W CASI Workspace rozdzielamy kilka podstawowych poziomów dostępu.

## 1. Właściciel systemu

Najwyższy poziom dostępu.

Przeznaczony dla właściciela platformy CASI i ewentualnie zaufanego wewnętrznego zespołu technicznego.

Może:

- zarządzać całą platformą,
- widzieć listę wszystkich organizacji,
- tworzyć organizacje,
- edytować organizacje,
- dezaktywować organizacje,
- zarządzać użytkownikami globalnie,
- zarządzać ustawieniami globalnymi,
- zarządzać integracjami globalnymi,
- diagnozować problemy techniczne,
- zarządzać wdrożeniami i konfiguracją systemu,
- wykonywać operacje administracyjne między organizacjami.

Ważne:

Właściciel systemu technicznie może mieć dostęp globalny, ale dostęp do danych konkretnej organizacji powinien być używany ostrożnie, tylko w uzasadnionych sytuacjach, na przykład:

- obsługa techniczna,
- diagnostyka błędu,
- wsparcie klienta,
- migracja danych,
- audyt bezpieczeństwa,
- naprawa incydentu.

Dostęp właściciela systemu do danych organizacji powinien być możliwy do zalogowania w historii lub audycie.

Właściciel systemu nie powinien być traktowany tak samo jak administrator organizacji klienta.

---

## 2. Administrator organizacji

Najwyższy poziom dostępu w obrębie jednej organizacji.

Przeznaczony dla osoby zarządzającej po stronie klienta.

Może:

- widzieć dane swojej organizacji,
- zarządzać użytkownikami swojej organizacji,
- zarządzać ustawieniami swojej organizacji,
- zarządzać integracjami organizacji,
- zarządzać modułami w obrębie organizacji,
- przeglądać logi organizacji,
- kontrolować dostęp pracowników organizacji,
- nadawać role i capability w swojej organizacji, jeżeli system to umożliwia.

Nie może:

- widzieć danych innych organizacji,
- tworzyć globalnych organizacji poza swoim zakresem,
- zmieniać ustawień globalnych platformy,
- zarządzać użytkownikami innych organizacji,
- omijać globalnych zasad bezpieczeństwa platformy.

Administrator organizacji ma silne uprawnienia, ale tylko w obrębie swojej organizacji.

---

## 3. Koordynator

Rola operacyjna z możliwością pilnowania procesu.

Przeznaczona dla osoby, która odpowiada za przepływ pracy, decyzje operacyjne i kontrolę zadań.

Może:

- prowadzić pracę operacyjną,
- zarządzać obiegiem faktur,
- zarządzać zadaniami,
- rozdzielać zadania,
- podejmować decyzje procesowe,
- potwierdzać lub odrzucać duplikaty,
- nadzorować statusy,
- przeglądać historię działań,
- nadzorować pracę operatorów,
- obsługiwać rozliczenia, jeżeli ma odpowiednie capability.

Nie powinien domyślnie:

- zarządzać użytkownikami,
- zmieniać ustawień organizacji,
- zarządzać integracjami,
- zmieniać ustawień globalnych,
- mieć dostępu do wszystkich danych wrażliwych bez potrzeby.

Koordynator ma wpływ na proces, ale nie powinien zarządzać strukturą systemu.

---

## 4. Operator

Rola do codziennej pracy operacyjnej.

Przeznaczona dla osoby, która wprowadza dane, obrabia dokumenty i wykonuje bieżące zadania.

Może:

- dodawać i edytować dane robocze,
- dodawać faktury,
- edytować faktury w zakresie operacyjnym,
- dodawać kontrahentów,
- obsługiwać zadania,
- dodawać notatki,
- importować dokumenty, jeśli ma odpowiednie capability,
- współdzielić zadania w obrębie organizacji, jeśli ma odpowiednie uprawnienie,
- pracować w module rozliczeń, jeśli ma odpowiednie capability.

Nie powinien domyślnie:

- zarządzać użytkownikami,
- zmieniać ustawień organizacji,
- zarządzać integracjami,
- zmieniać reguł systemowych,
- podejmować decyzji administracyjnych,
- importować wyciągów bankowych bez osobnego capability,
- widzieć danych dzieci, rodziców, płatników i umów bez potrzeby.

Operator pracuje na danych, ale nie zarządza ludźmi ani konfiguracją.

---

## 5. Gość

Rola tylko do podglądu.

Przeznaczona dla osób, które mają mieć wgląd w dane bez możliwości ich zmiany.

Może:

- przeglądać dane, do których ma dostęp,
- otwierać wybrane widoki,
- sprawdzać statusy,
- czytać dokumenty, jeśli ma capability,
- korzystać z ograniczonego widoku raportowego, jeśli ma dostęp.

Nie może:

- edytować danych,
- dodawać danych,
- zmieniać statusów,
- zarządzać użytkownikami,
- zarządzać integracjami,
- wykonywać operacji automatycznych,
- uruchamiać importów,
- zatwierdzać decyzji procesowych.

Gość nie powinien niczego zmieniać.

---

## 6. System / Integracja

To nie jest zwykły użytkownik ludzki.

To aktor systemowy używany przez:

- worker,
- scheduler,
- Make.com,
- Telegram webhook,
- e-mail importer,
- KSeF importer,
- OCR,
- AI,
- joby w tle,
- automatyzacje.

Aktor systemowy może wykonywać akcje tylko w przyznanym zakresie.

Przykłady:

- import e-mail działa tylko dla organizacji, która ma skonfigurowaną integrację e-mail,
- Telegram webhook zapisuje dokument tylko do organizacji rozpoznanej po użytkowniku albo kanale,
- worker przypomnień wysyła przypomnienia tylko dla zadań z danej organizacji,
- AI odpowiada tylko na podstawie dokumentów, do których dany użytkownik lub organizacja ma dostęp.

Aktor systemowy powinien być widoczny w logach.

Przykładowe wartości aktora w logach:

- `system`
- `worker`
- `scheduler`
- `telegram_webhook`
- `email_importer`
- `ksef_importer`
- `ocr_engine`
- `ai_assistant`
- `make_integration`

Zasada:

> Automatyzacje, integracje i workery powinny być traktowane jako osobni aktorzy systemowi w logach i powinny działać tylko w przyznanym zakresie.

---

# 5. Przykładowe capability

## Organizacje i administracja

- `organizations.read`
- `organizations.create`
- `organizations.update`
- `organizations.deactivate`
- `users.read`
- `users.create`
- `users.update`
- `users.reset_password`
- `settings.organization.manage`
- `settings.global.manage`

## Faktury

- `invoices.read`
- `invoices.create`
- `invoices.update`
- `invoices.change_status`
- `invoices.confirm_duplicate`
- `invoices.reject_duplicate`
- `invoices.view_files`
- `invoices.view_ocr`
- `invoices.import_ksef`
- `invoices.import_email`
- `invoices.import_telegram`

## Kontrahenci

- `contractors.read`
- `contractors.create`
- `contractors.update`

## Asystent Szefa

- `tasks.read`
- `tasks.create`
- `tasks.update`
- `tasks.assign`
- `tasks.share`
- `tasks.complete`
- `tasks.manage_all`
- `tasks.view_history`
- `tasks.manage_reminders`

## Asystent Firmowy

- `knowledge.read`
- `knowledge.upload`
- `knowledge.sync`
- `knowledge.manage`
- `knowledge.ask`

## Rozliczenia klientów

- `billing.read`
- `billing.manage_customers`
- `billing.manage_services`
- `billing.manage_models`
- `billing.generate_charges`
- `billing.import_bank_statements`
- `billing.manage_payments`
- `billing.allocate_payments`
- `billing.manage_documents`
- `billing.view_sensitive_data`
- `billing.admin`

## Work Items i SLA

- `work_items.read`
- `work_items.create`
- `work_items.update`
- `work_items.assign`
- `work_items.bulk_actions`
- `work_items.manage_sla_policy`
- `work_items.view_workload`

## Logi i audyt

- `logs.read`
- `logs.read_sensitive`
- `audit.read`
- `audit.export`

## Integracje

- `integrations.read`
- `integrations.manage_email`
- `integrations.manage_telegram`
- `integrations.manage_ksef`
- `integrations.manage_google`
- `integrations.manage_make`

## AI i automatyzacje

- `ai.use`
- `ai.manage_prompts`
- `ai.view_usage`
- `ai.manage_provider_settings`
- `automation.run_manual`
- `automation.manage_schedules`
- `automation.view_jobs`
- `automation.retry_jobs`

---

# 6. Macierz ról — ogólny dostęp

| Obszar / akcja | Właściciel systemu | Administrator organizacji | Koordynator | Operator | Gość | System / Integracja |
|---|---|---|---|---|---|---|
| Widok wszystkich organizacji | tak | nie | nie | nie | nie | nie |
| Widok swojej organizacji | tak | tak | tak | tak | tak | tylko zakres techniczny |
| Tworzenie organizacji | tak | nie | nie | nie | nie | nie |
| Edycja organizacji | tak | tylko swojej | nie | nie | nie | nie |
| Dezaktywacja organizacji | tak | nie | nie | nie | nie | nie |
| Ustawienia globalne | tak | nie | nie | nie | nie | nie |
| Ustawienia swojej organizacji | tak | tak | nie | nie | nie | nie |
| Tworzenie użytkowników | tak | tylko w swojej | nie | nie | nie | nie |
| Edycja użytkowników | tak | tylko w swojej | nie | nie | nie | nie |
| Reset hasła użytkownika | tak | tylko w swojej | nie | nie | nie | nie |
| Przypisanie ID Telegram użytkownika | tak | tylko w swojej | nie | nie | nie | nie |
| Ustawienie ID kanału Telegram organizacji | tak | tylko w swojej | nie | nie | nie | nie |
| Zarządzanie integracjami | tak | tylko w swojej | nie | nie | nie | tylko własna integracja |
| Wgląd techniczny do logów | tak | opcjonalnie | nie | nie | nie | tylko własne akcje |

---

# 7. Macierz ról — faktury i kontrahenci

| Obszar / akcja | Właściciel systemu | Administrator organizacji | Koordynator | Operator | Gość | System / Integracja |
|---|---|---|---|---|---|---|
| Widok faktur | tak | tak | tak | tak | tak | tylko technicznie |
| Dodanie faktury | tak | tak | tak | tak | nie | tak, jeśli integracja ma zakres |
| Edycja danych faktury | tak | tak | tak | tak | nie | tylko w ramach importu |
| Zmiana statusu faktury | tak | tak | tak | tak | nie | tylko automatyczne statusy |
| Potwierdzenie duplikatu | tak | tak | tak | opcjonalnie przez capability | nie | nie |
| Oznaczenie faktury jako poprawnej | tak | tak | tak | opcjonalnie przez capability | nie | nie |
| Podgląd OCR | tak | tak | tak | tak | opcjonalnie | tylko technicznie |
| Podgląd plików faktury | tak | tak | tak | tak | opcjonalnie | tylko technicznie |
| Import KSeF | tak | tak | opcjonalnie | opcjonalnie | nie | tak, jeśli skonfigurowany |
| Import e-mail | tak | tak | opcjonalnie | opcjonalnie | nie | tak, jeśli skonfigurowany |
| Import Telegram | tak | tak | opcjonalnie | opcjonalnie | nie | tak, jeśli skonfigurowany |
| Widok kontrahentów | tak | tak | tak | tak | tak | tylko technicznie |
| Edycja kontrahentów | tak | tak | tak | tak | nie | opcjonalnie przy imporcie |

---

# 8. Macierz ról — Asystent Szefa

| Obszar / akcja | Właściciel systemu | Administrator organizacji | Koordynator | Operator | Gość | System / Integracja |
|---|---|---|---|---|---|---|
| Widok zadań | tak | tak | tak | tak | tak | tylko technicznie |
| Tworzenie zadań | tak | tak | tak | tak | nie | opcjonalnie z integracji |
| Edycja własnych zadań | tak | tak | tak | tak | nie | nie |
| Edycja wszystkich zadań w organizacji | tak | tak | tak | opcjonalnie | nie | nie |
| Rozdzielanie zadań innym osobom | tak | tak | tak | tak / opcjonalnie | nie | opcjonalnie |
| Zmiana statusu zadania | tak | tak | tak | tak | nie | opcjonalnie |
| Dodawanie notatek | tak | tak | tak | tak | nie | opcjonalnie |
| Widok historii zadania | tak | tak | tak | tak | opcjonalnie | tylko technicznie |
| Zarządzanie przypomnieniami innych osób | tak | tak | tak | nie / opcjonalnie | nie | worker przypomnień |

---

# 9. Macierz ról — Asystent Firmowy

| Obszar / akcja | Właściciel systemu | Administrator organizacji | Koordynator | Operator | Gość | System / Integracja |
|---|---|---|---|---|---|---|
| Zadawanie pytań do bazy wiedzy | tak | tak | tak | tak | opcjonalnie | nie jako użytkownik |
| Czytanie dokumentów wiedzy | tak | tak | tak | tak | opcjonalnie | tylko technicznie |
| Upload dokumentów | tak | tak | tak | opcjonalnie | nie | opcjonalnie z integracji |
| Synchronizacja folderu wiedzy | tak | tak | opcjonalnie | nie / opcjonalnie | nie | tak, jeśli skonfigurowana |
| Ponowne przetwarzanie dokumentu | tak | tak | opcjonalnie | nie / opcjonalnie | nie | tak, jeśli job ma zakres |
| Zarządzanie bazą wiedzy | tak | tak | nie / opcjonalnie | nie | nie | nie |
| Odczyt dokumentów spoza organizacji | tylko uzasadniona administracja | nie | nie | nie | nie | nie |

---

# 10. Macierz ról — rozliczenia klientów

| Obszar / akcja | Właściciel systemu | Administrator organizacji | Koordynator | Operator | Gość | System / Integracja |
|---|---|---|---|---|---|---|
| Widok rozliczeń | tak | tak | tak | opcjonalnie | opcjonalnie | tylko technicznie |
| Widok klientów organizacji | tak | tak | tak | tak | opcjonalnie | tylko technicznie |
| Widok danych dzieci | tak | tak | tak | opcjonalnie | opcjonalnie | tylko technicznie |
| Widok danych płatników | tak | tak | tak | opcjonalnie | nie / opcjonalnie | tylko technicznie |
| Edycja klientów organizacji | tak | tak | tak | opcjonalnie | nie | nie |
| Zarządzanie usługami | tak | tak | opcjonalnie | nie | nie | nie |
| Zarządzanie modelami rozliczeń | tak | tak | opcjonalnie | nie | nie | nie |
| Generowanie należności | tak | tak | tak | opcjonalnie | nie | opcjonalnie jako job |
| Import wyciągów bankowych | tak | tak | opcjonalnie | opcjonalnie przez capability | nie | tak, jeśli integracja ma zakres |
| Widok wyciągów bankowych | tak | tak | opcjonalnie | opcjonalnie przez capability | nie | tylko technicznie |
| Dopasowanie wpłat | tak | tak | tak | opcjonalnie | nie | tak, jeśli job ma zakres |
| Ręczne rozdzielanie wpłat | tak | tak | tak | opcjonalnie | nie | nie |
| Dokumenty rozliczeniowe | tak | tak | tak | opcjonalnie | nie | opcjonalnie |
| Dokumenty umów | tak | tak | opcjonalnie | opcjonalnie | nie / opcjonalnie | tylko technicznie |
| Administracja modułem rozliczeń | tak | tak | nie | nie | nie | nie |

---

# 11. Macierz ról — Work Items i SLA

| Obszar / akcja | Właściciel systemu | Administrator organizacji | Koordynator | Operator | Gość | System / Integracja |
|---|---|---|---|---|---|---|
| Widok spraw | tak | tak | tak | tak | opcjonalnie | tylko technicznie |
| Tworzenie spraw | tak | tak | tak | tak | nie | opcjonalnie |
| Edycja spraw | tak | tak | tak | tak | nie | opcjonalnie |
| Przypisywanie spraw | tak | tak | tak | opcjonalnie | nie | opcjonalnie |
| Akcje masowe | tak | tak | tak | opcjonalnie | nie | nie |
| Eskalacje | tak | tak | tak | opcjonalnie | nie | opcjonalnie |
| Zarządzanie polityką SLA | tak | tak | opcjonalnie | nie | nie | nie |
| Widok obciążenia zespołu | tak | tak | tak | opcjonalnie | nie | nie |

---

# 12. Macierz ról — logi i audyt

| Obszar / akcja | Właściciel systemu | Administrator organizacji | Koordynator | Operator | Gość | System / Integracja |
|---|---|---|---|---|---|---|
| Widok historii systemu | tak | tak | tak | tak | opcjonalnie | tylko własne akcje |
| Widok logów technicznych | tak | opcjonalnie | nie | nie | nie | tylko własne akcje |
| Widok logów audytowych organizacji | tak | tak | opcjonalnie | nie | nie | tylko własne akcje |
| Eksport logów | tak | opcjonalnie | nie | nie | nie | nie |
| Widok danych wrażliwych w logach | tak, ostrożnie | opcjonalnie | nie | nie | nie | nie |
| Logowanie automatyzacji | tak | tak w swojej organizacji | opcjonalnie | nie | nie | tak |

---

# 13. Rekomendowane role w praktyce

## Właściciel systemu

Dla:

- właściciela CASI,
- zaufanego zespołu technicznego,
- osób odpowiedzialnych za platformę.

Powinien być używany ostrożnie, bo ma dostęp globalny.

W praktyce ta rola powinna być rzadka.

---

## Administrator organizacji

Dla:

- właściciela firmy klienta,
- osoby zarządzającej po stronie klienta,
- kierownika organizacji.

To główna rola dla klienta, który zarządza własną organizacją w systemie.

---

## Koordynator

Dla:

- osoby pilnującej procesu,
- kierownika biura,
- osoby decyzyjnej operacyjnie,
- osoby odpowiedzialnej za faktury, zadania i rozliczenia.

Koordynator ma wpływ na proces, ale nie powinien zarządzać strukturą systemu.

---

## Operator

Dla:

- pracownika biurowego,
- osoby dodającej dokumenty,
- osoby obsługującej zadania,
- osoby wykonującej codzienną pracę operacyjną.

Operator pracuje na danych, ale nie zarządza ludźmi ani konfiguracją.

---

## Gość

Dla:

- księgowej,
- osoby tylko do podglądu,
- zewnętrznego konsultanta,
- członka zespołu bez prawa edycji.

Gość nie powinien zmieniać danych.

---

## System / Integracja

Dla:

- workerów,
- schedulerów,
- webhooków,
- importerów,
- OCR,
- AI,
- Make.com,
- Telegrama,
- e-maila,
- KSeF.

Aktor systemowy nie powinien mieć ludzkiego panelu pracy.

Powinien działać wyłącznie w technicznym zakresie, który jest mu potrzebny.

---

# 14. Dane szczególnie wrażliwe

Nie wszystkie dane w systemie mają ten sam poziom wrażliwości.

Szczególnie chronione powinny być:

- dane dzieci,
- dane rodziców,
- dane płatników,
- wyciągi bankowe,
- tytuły przelewów,
- dokumenty umów,
- dokumenty zawierające dane osobowe,
- klucze API,
- tokeny OAuth,
- konfiguracja integracji,
- logi z pełnymi danymi technicznymi,
- dokumenty klientów organizacji.

Zasada:

> Dostęp do danych szczególnie wrażliwych powinien wymagać osobnego capability albo świadomej decyzji administracyjnej.

Przykład:

Użytkownik może mieć dostęp do listy uczniów, ale nie musi mieć dostępu do:

- wyciągów bankowych,
- pełnych danych płatników,
- dokumentów umów,
- historii płatności,
- danych rozliczeniowych całej rodziny.

---

# 15. Zasady dla danych dzieci i rozliczeń

Moduł rozliczeń może przetwarzać dane dzieci, rodziców, płatności i umów.

Dlatego dostęp do rozliczeń powinien być bardziej ostrożny niż dostęp do zwykłych zadań.

Zasady:

- nie każdy operator musi widzieć rozliczenia,
- nie każdy operator musi importować wyciągi bankowe,
- nie każdy operator powinien widzieć pełne dane płatników,
- nie każdy użytkownik z widokiem uczniów powinien mieć widok płatności,
- dostęp do dokumentów umów powinien być kontrolowany,
- widok uczniów może być dostępny szerzej niż widok pełnych rozliczeń,
- import bankowy powinien wymagać osobnego capability,
- ręczne rozdzielanie wpłat powinno wymagać osobnego capability,
- widok danych dzieci powinien być ograniczony do osób, które realnie ich potrzebują.

---

# 16. Zasady dla AI i Asystenta Firmowego

Dostęp do Asystenta Firmowego powinien respektować organizację i capability.

Zasady:

- użytkownik może pytać tylko o dokumenty swojej organizacji,
- AI nie może omijać uprawnień,
- upload dokumentów powinien wymagać capability,
- zarządzanie dokumentami powinno wymagać wyższego capability,
- odpowiedzi AI powinny cytować źródła,
- użytkownik nie powinien zobaczyć dokumentów, do których nie ma dostępu,
- automatyczne przetwarzanie dokumentów powinno działać tylko w zakresie danej organizacji,
- logi AI powinny pozwalać zrozumieć, kto zadał pytanie i na podstawie jakich dokumentów powstała odpowiedź.

Zasada:

> AI jest częścią systemu uprawnień, nie obejściem systemu uprawnień.

---

# 17. Zasady dla integracji i automatyzacji

Integracje i automatyzacje powinny mieć własny ograniczony zakres działania.

Dotyczy to między innymi:

- Make.com,
- Telegrama,
- e-maila,
- KSeF,
- OCR,
- AI,
- Google Calendar,
- workerów,
- schedulerów.

Zasady:

- integracja nie powinna działać globalnie, jeśli ma obsługiwać jedną organizację,
- webhook powinien rozpoznawać organizację i użytkownika,
- importer e-mail powinien działać tylko dla skonfigurowanej organizacji,
- KSeF powinien importować dane tylko w ramach właściwej organizacji,
- AI powinno korzystać tylko z dokumentów dostępnych w danym zakresie,
- worker powinien zapisywać w logach, co zrobił i dlaczego,
- automatyzacja nie powinna mieć większych uprawnień niż potrzebuje.

Zasada:

> Automatyzacja powinna mieć minimalny potrzebny dostęp, a jej działania powinny być logowane.

---

# 18. Przyszły model członkostwa w wielu organizacjach

Obecna implementacja może zakładać jedną organizację użytkownika przez `users.organization_id`.

Docelowo warto rozważyć model, w którym jeden użytkownik może należeć do wielu organizacji.

Wtedy potrzebna będzie tabela typu `organization_memberships`.

Przykładowe pola:

- `organization_membership_id`
- `organization_id`
- `user_id`
- `role`
- `is_active`
- `created_at`
- `updated_at`

Capability mogą być wtedy przypisane:

- globalnie do użytkownika,
- do członkostwa w konkretnej organizacji,
- do konkretnego modułu w organizacji,
- do konkretnego pakietu klienta.

Nie trzeba wdrażać tego natychmiast, ale architektura nie powinna zamykać tej możliwości.

---

# 19. Rekomendowany model techniczny

Na start można utrzymać prosty model:

- `users.role`
- `users.organization_id`
- `user_capabilities`

Docelowo można przejść do modelu:

- `users`
- `organizations`
- `organization_memberships`
- `role_templates`
- `capabilities`
- `membership_capabilities`
- `system_actors`
- `integration_scopes`

Nie należy jednak komplikować tego przedwcześnie.

Zasada:

> Najpierw prosty model ról i capability, potem pełny model członkostwa, jeśli będzie potrzebny.

---

# 20. Minimalny model decyzyjny dla API

Każdy endpoint API powinien działać według podobnej logiki:

1. Sprawdź, czy użytkownik albo aktor systemowy jest uwierzytelniony.
2. Sprawdź, czy zna swój zakres organizacji.
3. Sprawdź, czy żądany rekord należy do tej organizacji.
4. Sprawdź, czy użytkownik ma rolę lub capability do danej akcji.
5. Jeżeli dostęp nie jest jasny, odmów.
6. Zaloguj ważne akcje, szczególnie administracyjne, finansowe, AI i integracyjne.

Zasada:

> Brak pewności oznacza brak dostępu.

---

# 21. Czego nie robić

Nie należy:

- traktować administratora organizacji jak właściciela całej platformy,
- dawać wszystkim użytkownikom roli właściciela systemu,
- opierać całego bezpieczeństwa tylko na frontendzie,
- sprawdzać uprawnień tylko w UI,
- pomijać sprawdzania organizacji w API,
- pozwalać operatorowi domyślnie na wszystko,
- mieszać danych wielu organizacji w jednym widoku bez jasnego powodu,
- dawać dostępu do rozliczeń bankowych bez osobnej decyzji,
- dawać dostępu do danych dzieci bez potrzeby,
- dawać automatyzacjom dostępu globalnego bez potrzeby,
- pozwalać AI odpowiadać na podstawie dokumentów spoza organizacji użytkownika,
- zakładać, że skoro użytkownik widzi moduł, to może wykonać każdą akcję w module,
- trzymać sekretów integracji w frontendzie,
- ujawniać pełnych danych wrażliwych w logach bez potrzeby.

---

# 22. Zasada końcowa

Role w CASI Workspace powinny być proste i zrozumiałe.

Capability powinny dawać elastyczność.

Zakres organizacji powinien chronić dane klientów.

Aktorzy systemowi powinni być ograniczeni i widoczni w logach.

Najważniejsze decyzje:

- `Właściciel systemu` ma możliwość dostępu globalnego, ale powinien używać jej ostrożnie i w uzasadnionych sytuacjach.
- `Administrator organizacji` ma silne uprawnienia tylko w swojej organizacji.
- `Koordynator` pilnuje procesu.
- `Operator` wykonuje codzienną pracę.
- `Gość` tylko ogląda dane.
- `System / Integracja` wykonuje automatyczne akcje w ograniczonym zakresie.
- Capability doprecyzowują dostęp do modułów i akcji.
- Każda akcja musi sprawdzać organizację.
- Każda akcja musi sprawdzać uprawnienia.
- Domyślnie brak dostępu jest bezpieczniejszy niż domyślny dostęp.
- Dane rozliczeniowe, bankowe, dzieci, rodziców, płatników i dokumenty powinny być szczególnie chronione.

Najważniejsza myśl:

> Bezpieczeństwo CASI Workspace opiera się na połączeniu roli, capability, zakresu organizacji i logowania ważnych działań.