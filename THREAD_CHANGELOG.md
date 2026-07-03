# THREAD_CHANGELOG

## 2026-04-30 23:10 (Europe/Warsaw) - Frontend: bezpieczne podpiecie akcji faktur w szczegole

- Zakres watku:
  - podpiecie istniejacych akcji faktur do UI szczegolu pojedynczej faktury
  - zachowanie pojedynczego kontekstu faktury, bez akcji masowych
  - dodanie potwierdzen, stanu wysylania, blokady podwojnego klikniecia i odswiezenia danych po sukcesie

- Zmienione pliki:
  - frontend/scripts/test-invoices.js
  - frontend/src/modules/invoices/InvoiceDetailPage.tsx
  - frontend/src/modules/invoices/decisionModel.ts
  - frontend/src/modules/invoices/invoicesModel.ts
  - THREAD_CHANGELOG.md

- Co zmieniono:
  - Panel decyzji w `InvoiceDetailPage.tsx` pokazuje akcje dla jednej aktualnie otwartej faktury.
  - Podpieto akcje: `confirm-duplicate`, `reject-duplicate`, `mark-ready`, `handoff`, `undo-last`, `reopen`, `close`.
  - Klikniecie akcji otwiera modal potwierdzenia; dopiero potwierdzenie wykonuje zapis przez `invoiceApi.submitAction()`.
  - Modal pokazuje numer faktury, kontrahenta i opis skutku akcji.
  - Akcje wymagajace danych zbieraja je przed wysylka: `handoff`/`mark-ready` wymagaja celu przekazania, `reopen`/`close` wymagaja powodu.
  - Dodano `submitting`, blokade przyciskow podczas wysylania, ochrone przed podwojnym submittem oraz kontrolowany sukces/blad.
  - Po sukcesie nie ma optymistycznej aktualizacji; widok pobiera szczegol faktury ponownie z API.
  - `401` z akcji nadal przechodzi przez globalny mechanizm sesji w `apiRequest()`.

- Testy, ktore przeszly:
  - `npm.cmd run test:invoices`
  - `npm.cmd run test:dashboard`
  - `npm.cmd run typecheck`
  - `npm.cmd run lint`
  - `npm.cmd run build`

- Co pokrywaja regresje faktur:
  - brak podwojnego requestu przy szybkim drugim submitcie
  - stan `submitting`
  - refresh danych po sukcesie
  - kontrolowany blad po bledzie API
  - wymagane potwierdzenie dla ryzykownych akcji
  - globalny event sesji przy `401`

- Czego celowo nie ruszano:
  - `backend/`
  - `static/`
  - deployu
  - globalnego UI i AppShell
  - akcji masowych

- Ryzyko/skutki uboczne:
  - srednie funkcjonalnie, bo UI potrafi juz wykonac realne mutacje faktur po potwierdzeniu.
  - przed szerszym uzyciem warto przejsc recznie kazda akcje na danych testowych z roznymi rolami i stanami workflow.
  - kolejny etap powinien dodac bardziej precyzyjne uprawnienia/visibility akcji po stronie frontendu na podstawie danych sesji albo kontraktu backendu, bez polegania wylacznie na `403`.

---

## 2026-04-30 19:58 (Europe/Warsaw) - Frontend: szkielet akcji decyzyjnych faktur

- Zakres watku:
  - przygotowanie kontrolowanej warstwy pod przyszle akcje decyzyjne faktur
  - dopasowanie frontendu do istniejacych endpointow backendu bez edycji backendu
  - brak podpinania mutujacych przyciskow w UI

- Zmienione pliki:
  - frontend/scripts/test-invoices.js
  - frontend/src/modules/invoices/api.ts
  - frontend/src/modules/invoices/invoicesModel.ts
  - frontend/src/modules/invoices/types.ts
  - THREAD_CHANGELOG.md

- Co zmieniono:
  - Dodano typy `InvoiceActionKind`, `InvoiceActionPayload`, `InvoiceActionRequest` i `InvoiceActionResult`.
  - Dodano endpoint builder `invoiceActionEndpoint()` oraz `invoiceApi.submitAction()` dla istniejacych akcji: `confirm-duplicate`, `reject-duplicate`, `mark-ready`, `handoff`, `undo-last`, `reopen`, `close`.
  - Dodano definicje akcji w modelu: etykieta, ton, wymagany powod, wymagany cel przekazania i komunikat sukcesu.
  - Dodano `buildInvoiceActionRequest()`, ktory waliduje payload przed mutacja i nie wysyla pustych danych jako decyzji.
  - Dodano kontrolowane mapowanie bledow akcji faktur, w tym `401`, `403`, `5xx`, problem sieci i zly kontrakt odpowiedzi.
  - Rozszerzono `test:invoices` o akcje bez payloadu, akcje z payloadem, walidacje wymaganych pol oraz globalny event sesji przy `401`.
  - Potwierdzono, ze `InvoicesPage.tsx` i `InvoiceDetailPage.tsx` nie importuja jeszcze helperow mutujacych, wiec UI nadal niczego nie zapisuje po samym wejsciu na widok.

- Testy, ktore przeszly:
  - `npm.cmd run test:invoices`
  - `npm.cmd run test:dashboard`
  - `npm.cmd run typecheck`
  - `npm.cmd run lint`
  - `npm.cmd run build`

- Czego celowo nie ruszano:
  - `backend/`
  - `static/`
  - deployu
  - globalnego UI i AppShell
  - widocznych przyciskow wykonujacych mutacje w UI

- Ryzyko/skutki uboczne:
  - niskie; dodano nieuzywany jeszcze przez UI kontrakt frontendu i testy.
  - nastepny etap podpinania przyciskow musi dodac potwierdzenia, stan `submitting`, refresh szczegolu po sukcesie i blokade podwojnego klikniecia.

---

## 2026-04-30 19:51 (Europe/Warsaw) - Frontend: domkniecie read-only szczegolu faktury

- Zakres watku:
  - domkniecie `/faktury/[invoiceId]` tym samym wzorcem co pulpit i lista faktur
  - przeniesienie przygotowania danych szczegolu faktury z komponentu strony do modelu
  - dodanie regresji dla read-only odczytu `/api/invoices/{id}`

- Zmienione pliki:
  - frontend/scripts/test-invoices.js
  - frontend/src/modules/invoices/InvoiceDetailPage.tsx
  - frontend/src/modules/invoices/api.ts
  - frontend/src/modules/invoices/invoicesModel.ts
  - THREAD_CHANGELOG.md

- Co zmieniono:
  - `InvoiceDetailPage.tsx` renderuje UI i wywoluje `invoiceApi.detail()`, a przygotowanie tytulu, faktow, historii i stanow przeniesiono do `invoicesModel.ts`.
  - Dodano kontrolowane komunikaty dla `401`, `403`, `5xx`, problemu sieci i zlego kontraktu szczegolu faktury.
  - `frontend/src/modules/invoices/api.ts` eksportuje `invoiceDetailEndpoint()` i `readInvoiceDetail()`, aby kontrakt szczegolu byl testowalny.
  - `test:invoices` sprawdza teraz takze sukces szczegolu faktury, zly kontrakt, `401` przez globalny mechanizm sesji oraz brak requestow zapisujacych dane.

- Testy, ktore przeszly:
  - `npm.cmd run test:invoices`
  - `npm.cmd run test:dashboard`
  - `npm.cmd run typecheck`
  - `npm.cmd run lint`
  - `npm.cmd run build`

- Czego celowo nie ruszano:
  - `backend/`
  - `static/`
  - deployu
  - globalnego UI i AppShell
  - akcji mutujacych faktury

- Ryzyko/skutki uboczne:
  - niskie; zmiana porzadkuje read-only widok szczegolu i dodaje regresje bez zmiany kontraktu backendu.
  - nastepny etap akcji decyzyjnych faktur powinien miec osobne endpointy, potwierdzenia i testy mutacji.

---

## 2026-04-30 19:44 (Europe/Warsaw) - Frontend: audyt spójnosci modeli dashboard/faktury

- Zakres watku:
  - techniczny przeglad spójnosci `dashboardModel.ts` i `invoicesModel.ts`
  - wzmocnienie regresji bez redesignu i bez zmian backendu
  - minimalna deduplikacja wspolnych typow widoku danych

- Zmienione pliki:
  - frontend/scripts/test-dashboard.js
  - frontend/src/lib/api.ts
  - frontend/src/lib/types.ts
  - frontend/src/modules/dashboard/dashboardModel.ts
  - frontend/src/modules/invoices/invoicesModel.ts
  - THREAD_CHANGELOG.md

- Co zmieniono:
  - Dodano wspolne typy `DataViewStatus`, `DataViewErrorState` i `ApiRequestMethod` w `frontend/src/lib/types.ts`.
  - `dashboardModel.ts` i `invoicesModel.ts` uzywaja tego samego wzorca statusu i error state.
  - Dodano jawne stale endpointow i read-only guard dla dashboardu, analogicznie do faktur.
  - Wzmocniono `test:dashboard` o sprawdzenie, ze `/api/dashboard` idzie jako `GET`, bez `body`, oraz ze `401` emituje globalne zdarzenie sesji.
  - Potwierdzono, ze strony modulow nie wykonuja bezposrednich `fetch()` i komunikacja idzie przez `frontend/src/lib/api.ts`.

- Wnioski z audytu:
  - Wzorzec jest spójny: komponent strony odpowiada za render, model za przygotowanie danych i mapowanie stanow.
  - `401` jest globalnie sygnalizowane w `apiRequest()` przez `casi:auth-required`; modele tylko dobieraja lokalny, ludzki komunikat bledu.
  - Nie ma fallbackow ani mockow udajacych prawdziwe dane produkcyjne.
  - Testy chronia kontrakt danych, empty state, `401`, zly kontrakt i brak przypadkowych mutacji; nie sa tylko testami tekstow UI.

- Testy, ktore przeszly:
  - `npm.cmd run test:dashboard`
  - `npm.cmd run test:invoices`
  - `npm.cmd run typecheck`
  - `npm.cmd run lint`
  - `npm.cmd run build`

- Czego celowo nie ruszano:
  - `backend/`
  - `static/`
  - deployu
  - globalnego UI i AppShell
  - wiekszej abstrakcji dla modulow

- Ryzyko/skutki uboczne:
  - niskie; zmiany dotycza typow wspolnych, modeli i testow.
  - kolejne moduly moga kopiowac ten wzorzec, ale akcje mutujace powinny dostac osobny, jawny model i osobne regresje.

---

## 2026-04-30 16:26 (Europe/Warsaw) - Frontend: regresje i model dla `/faktury`

- Zakres watku:
  - techniczne domkniecie widoku `/faktury` bez redesignu
  - wydzielenie logiki kontraktu i stanow widoku faktur z komponentu strony
  - dodanie regresji dla realnego, niemutujacego odczytu `/api/invoices/verification-inbox`

- Zmienione pliki:
  - frontend/package.json
  - frontend/scripts/test-invoices.js
  - frontend/src/modules/invoices/InvoicesPage.tsx
  - frontend/src/modules/invoices/invoicesModel.ts
  - THREAD_CHANGELOG.md

- Co zmieniono:
  - Dodano `invoicesModel.ts` dla interpretacji danych inboxu, stanow pustych, bledow API i formatowania kwot.
  - `InvoicesPage.tsx` zostawiono jako warstwe renderujaca UI i wywolujaca `api.invoiceVerificationInbox()`.
  - Dodano `npm.cmd run test:invoices`.
  - Test faktur sprawdza poprawny odczyt z `/api/invoices/verification-inbox`, pusty inbox, `401`, `403`, `500`, zly kontrakt API oraz brak akcji zapisujacych dane.
  - Potwierdzono, ze helper faktur wykonuje tylko `GET`, bez `body` i bez mutacji.

- Testy, ktore przeszly:
  - `npm.cmd run test:dashboard`
  - `npm.cmd run test:invoices`
  - `npm.cmd run typecheck`
  - `npm.cmd run lint`
  - `npm.cmd run build`

- Czego celowo nie ruszano:
  - `backend/`
  - `static/`
  - deployu
  - globalnego redesignu UI
  - architektury AppShell

- Ryzyko/skutki uboczne:
  - niskie; zmiana porzadkuje warstwe frontendu i dodaje regresje bez rozszerzania funkcji biznesowych.
  - widok nadal jest niemutujacy; akcje decyzyjne faktur wymagaja osobnego, kontrolowanego etapu.

---

## 2026-04-30 11:55 (Europe/Warsaw) - Frontend: testy pulpitu, inbox faktur i sesja

- Zakres watku:
  - zabezpieczenie `DashboardPage` testowalnym modelem i regresjami
  - podpiecie kolejnego realnego endpointu w produkcyjnym frontendzie
  - globalny, kontrolowany sygnal wygaslej sesji w AppShell/Topbar

- Zmienione pliki:
  - frontend/package.json
  - frontend/scripts/test-dashboard.js
  - frontend/src/app/globals.css
  - frontend/src/layouts/AppShell.tsx
  - frontend/src/layouts/Topbar.tsx
  - frontend/src/lib/api.ts
  - frontend/src/lib/types.ts
  - frontend/src/modules/dashboard/DashboardPage.tsx
  - frontend/src/modules/dashboard/dashboardModel.ts
  - frontend/src/modules/invoices/InvoicesPage.tsx
  - THREAD_CHANGELOG.md

- Co zmieniono:
  - Wyciagnieto logike pulpitu do `dashboardModel.ts`.
  - Dodano `npm.cmd run test:dashboard` bez instalowania nowych bibliotek.
  - Testy pokrywaja `401`, poprawny snapshot, zly kontrakt API i realne wartosci `0` w KPI.
  - `api.ts` emituje zdarzenie `casi:auth-required` przy `401`.
  - `AppShell`/`Topbar` pokazuje globalny komunikat `Sesja wygasla`, gdy dowolny fetch API dostanie `401`.
  - Dodano typowany kontrakt `InvoiceVerificationInbox`.
  - `/faktury` pokazuje pierwszy realny, niemutujacy widok z `/api/invoices/verification-inbox`.
  - Widok faktur uzywa istniejacych komponentow `PageHeader`, `LoadingState`, `ErrorState`, `EmptyState`, `Card`, `Table`, `StatusBadge`.

- Ryzyko/skutki uboczne:
  - niskie/srednie; `/faktury` przestal byc placeholderem i wykonuje runtime fetch do API.
  - brak akcji zapisu lub modyfikacji danych.
  - globalny komunikat sesji pojawia sie dopiero po `401` z warstwy `api.ts`.

- Co sprawdzic lokalnie:
  - `npm.cmd run test:dashboard`
  - `npm.cmd run typecheck`
  - `npm.cmd run lint`
  - `npm.cmd run build`
  - lokalny `next start` po czystym buildzie
  - headless Edge: `/faktury` z sesja pokazuje realne faktury z inboxu
  - headless Edge: `/pulpit` bez sesji pokazuje komunikat sesji i nie pokazuje kart KPI

- Co sprawdzic na Railway:
  - brak, nie zlecono deployu.

---

## 2026-04-30 02:24 (Europe/Warsaw) - Dev: tymczasowe zniesienie limitu urzadzen

- Zakres watku:
  - tymczasowe zniesienie limitu 3 aktywnych urzadzen na konto w lokalnym developingu
  - zachowanie produkcyjnego domyslu `3` w kodzie aplikacji

- Zmienione pliki:
  - app/config.py
  - app/services/auth_service.py
  - .env.local
  - THREAD_CHANGELOG.md

- Co zmieniono:
  - Dodano konfiguracje `INVOICE_MAX_ACTIVE_DEVICES_PER_ACCOUNT`.
  - Wartosc `0` oznacza brak limitu aktywnych urzadzen.
  - Domyslna wartosc w kodzie pozostaje `3`.
  - Lokalnie w `.env.local` ustawiono `INVOICE_MAX_ACTIVE_DEVICES_PER_ACCOUNT=0`.
  - Komunikat bledu limitu uzywa teraz skonfigurowanej liczby urzadzen.

- Ryzyko/skutki uboczne:
  - lokalnie mozna tworzyc wiecej sesji dla jednego konta, co jest wygodne do developmentu.
  - przed produkcyjnym uzyciem nalezy usunac lokalny override albo ustawic `INVOICE_MAX_ACTIVE_DEVICES_PER_ACCOUNT=3`.

- Co sprawdzic lokalnie:
  - `INVOICE_MAX_ACTIVE_DEVICES_PER_ACCOUNT=3 python -m unittest tests.test_auth_service.AuthServiceTests.test_same_account_allows_at_most_three_devices tests.test_auth_service.AuthServiceTests.test_relogin_on_same_device_reuses_device_slot`
  - `INVOICE_MAX_ACTIVE_DEVICES_PER_ACCOUNT=3 python -m unittest tests.http_server_test_methods.HttpServerTestMethods.test_session_current_exposes_workspace_state_and_device_context`
  - lokalny backend po restarcie loguje `admin` / `Admin1234` mimo przekroczonego wczesniej limitu
  - `/api/dashboard` z nowa sesja zwraca `200`

- Co sprawdzic na Railway:
  - brak, nie zlecono deployu.

---

## 2026-04-30 02:12 (Europe/Warsaw) - Frontend: male kroki produkcyjne dla pulpitu

- Zakres watku:
  - kilka bezpiecznych krokow wdrozeniowych wokol pulpitu i kontraktu danych
  - bez zmian w backendzie, static i deployu

- Zmienione pliki:
  - frontend/src/lib/api.ts
  - frontend/src/lib/types.ts
  - frontend/src/modules/dashboard/DashboardPage.tsx
  - THREAD_CHANGELOG.md

- Co zmieniono:
  - Dodano `ApiContractError`, zeby blad kontraktu API nie byl mieszany ze zwyklym bledem sieci.
  - Doprecyzowano typ `DashboardAlertCategory`.
  - Zamieniono techniczna kolumne endpointow na uzytkowe `Zrodlo`.
  - Filtry alertow w pulpicie zaczely realnie filtrowac dane zamiast byc statycznymi przyciskami.
  - Usunieto martwy przycisk `Plan migracji` z `DashboardPage`.

- Ryzyko/skutki uboczne:
  - niskie; zmiany sa lokalne dla pulpitu i warstwy API frontendu.
  - odpowiedz z nieznana kategoria alertu moze nie przejsc przez obecny typ frontendu, jesli backend doda nowa kategorie bez aktualizacji kontraktu.

- Co sprawdzic lokalnie:
  - `npm.cmd run typecheck`
  - `npm.cmd run lint`
  - `npm.cmd run build`
  - lokalny `next start` wstal na `http://127.0.0.1:3000`
  - `/pulpit` zwraca `200`
  - `/api/dashboard` bez cookie zwraca `401`

- Uwagi:
  - proba utworzenia nowej sesji testowej trafila w limit backendu: konto ma maksymalnie 3 jednoczesne urzadzenia.
  - nie czyszczono sesji i nie zmieniano backendu.

- Co sprawdzic na Railway:
  - brak, nie zlecono deployu.

---

## 2026-04-30 01:58 (Europe/Warsaw) - Frontend: kontrakt zalogowanego `/api/dashboard`

- Zakres watku:
  - audyt sciezki zalogowanego uzytkownika dla `/api/dashboard` i `DashboardPage`
  - doprecyzowanie kontraktu danych pulpitu po stronie frontendu

- Zmienione pliki:
  - frontend/src/lib/api.ts
  - frontend/src/lib/types.ts
  - frontend/src/modules/dashboard/DashboardPage.tsx
  - THREAD_CHANGELOG.md

- Co zmieniono:
  - `api.dashboard()` waliduje, czy odpowiedz ma ksztalt `DashboardSnapshot`, zanim trafi do `DashboardPage`.
  - `DashboardSnapshot.cards` i glowne listy snapshotu sa teraz wymagane w typach frontendu.
  - Zera w KPI sa traktowane jako realne wartosci z backendu, jezeli przyszly w poprawnym snapshotcie.
  - `EmptyState` pozostaje tylko dla udanego odczytu bez danych do pokazania, a nie dla `401`, `403` albo bledow backendu.
  - Doprecyzowano komunikat bledu sieci/API i usunieto techniczny tekst o mocku z widocznego UI pulpitu.

- Ryzyko/skutki uboczne:
  - niskie; zmiany dotycza tylko warstwy API frontendu, typow i renderowania pulpitu.
  - odpowiedz `/api/dashboard` niezgodna z kontraktem pokaze kontrolowany blad zamiast udawac prawdziwy pulpit.

- Co sprawdzic lokalnie:
  - `npm.cmd run typecheck`
  - `npm.cmd run lint`
  - `npm.cmd run build`
  - login lokalny `admin` / `Admin1234`, potem `GET /api/dashboard` z cookie zwraca `200` i pola `DashboardSnapshot`
  - headless Edge na `/pulpit` z sesja pokazuje realne KPI z API, a bez sesji pokazuje komunikat o sesji bez kart KPI

- Co sprawdzic na Railway:
  - brak, nie zlecono deployu.

---

Wspólny dziennik zmian między wątkami.

## Zasady

- Najświeższy wpis dodawaj na górę.
- Nie edytuj starych wpisów bez wyraźnego powodu.
- Każdy wpis powinien mieć:
  - datę i czas (Europe/Warsaw)
  - zakres wątku
  - zmienione pliki
  - co zmieniono
  - ryzyko/skutki uboczne
  - co sprawdzić lokalnie
  - co sprawdzić na Railway lub innym serwerze, jeśli deploy był zlecony

---

## 2026-04-30 01:40 (Europe/Warsaw) - Frontend: produkcyjna obsługa błędów `/api/dashboard`

- Zakres wątku:
  - mały audyt i korekta zachowania pulpitu po odpowiedziach `/api/dashboard`
  - rozdzielenie braku sesji, braku uprawnień, błędów backendu i pustego snapshotu

- Zmienione pliki:
  - frontend/src/modules/dashboard/DashboardPage.tsx
  - THREAD_CHANGELOG.md

- Co zmieniono:
  - Usunięto fallbackowe dane z runtime pulpitu.
  - `401` pokazuje osobny komunikat `Sesja wygasla` / `Zaloguj sie ponownie`.
  - `403` pokazuje osobny komunikat braku dostępu.
  - błędy `5xx` pokazują osobny komunikat błędu backendu.
  - sukces `200` bez danych pokazuje `EmptyState`, a nie mockowe rekordy.
  - dane KPI, alerty, przypomnienia i kolejka wiedzy renderują się tylko po poprawnym snapshotcie z backendu.

- Ryzyko/skutki uboczne:
  - niskie; zmiana dotyczy wyłącznie zachowania `DashboardPage` w produkcyjnym frontendzie.
  - bez zalogowanej sesji pulpit nie pokazuje już tymczasowych danych migracyjnych.

- Co sprawdzić lokalnie:
  - `npm.cmd run typecheck`
  - `npm.cmd run lint`
  - `npm.cmd run build`
  - `GET http://127.0.0.1:8000/api/dashboard` bez cookie zwraca `401`
  - headless Edge na `http://127.0.0.1:3000/pulpit` bez sesji pokazuje `Sesja wygasla` i nie pokazuje fallbackowego wiersza `Faktury do weryfikacji`

- Co sprawdzić na Railway:
  - brak, nie zlecono deployu.

---

## 2026-04-30 01:30 (Europe/Warsaw) - Frontend: podpięcie `/api/dashboard` do pulpitu

- Zakres wątku:
  - podłączenie pierwszego realnego endpointu backendu do produkcyjnego frontendu
  - zachowanie bezpiecznego fallbacku, gdy użytkownik nie ma sesji albo backend zwraca błąd

- Zmienione pliki:
  - frontend/src/lib/api.ts
  - frontend/src/lib/types.ts
  - frontend/src/modules/dashboard/DashboardPage.tsx
  - THREAD_CHANGELOG.md

- Co zmieniono:
  - `api.dashboard()` zwraca teraz typowany `DashboardSnapshot`.
  - Dodano typy dla kart pulpitu, alertów operacyjnych, przypomnień, kolejki wiedzy i zdarzeń.
  - `DashboardPage` stał się komponentem klienckim i pobiera dane z `/api/dashboard` przez istniejącą warstwę `frontend/src/lib/api.ts`.
  - Dodano stany `loading`, `error` i `ready`.
  - Przy braku sesji lub błędzie API pulpit pokazuje komunikat oraz fallback migracyjny zamiast pustego ekranu.
  - KPI pulpitu korzystają z `cards` z backendu, a tabela operacyjna z `operational_alerts`, jeśli są dostępne.
  - Panel boczny pokazuje `active_reminders` i `knowledge_queue`, gdy backend je zwróci.

- Ryzyko/skutki uboczne:
  - niskie/średnie; zmiana dotyczy frontendu i pierwszego runtime fetchu do backendu.
  - endpoint `/api/dashboard` wymaga autoryzacji, więc bez zalogowanej sesji widoczny będzie fallback i komunikat 401.
  - nie zmieniono backendu ani kontraktu API.

- Co sprawdzić lokalnie:
  - `npm.cmd run typecheck`
  - `npm.cmd run lint`
  - `npm.cmd run build`
  - `http://127.0.0.1:3000/pulpit` zwraca 200 po restarcie lokalnego `next start`
  - po zalogowaniu w aplikacji warto sprawdzić, czy karty i alerty pokazują realne dane organizacji

- Co sprawdzić na Railway:
  - brak, nie zlecono deployu.

---

## 2026-04-30 01:08 (Europe/Warsaw) - Frontend: pulpit operacyjny, Rozliczenia i Work Items

- Zakres wątku:
  - kontynuacja prac nad produkcyjnym frontendem w `frontend/`
  - wzmocnienie istniejącego AppShella i centralnej nawigacji bez mieszania z legacy `static/`
  - dodanie pierwszego bardziej konkretnego widoku pulpitu oraz brakujących modułów kierunkowych

- Zmienione pliki:
  - frontend/src/config/navigation.ts
  - frontend/src/app/globals.css
  - frontend/src/app/rozliczenia/page.tsx
  - frontend/src/app/work-items/page.tsx
  - frontend/src/modules/dashboard/DashboardPage.tsx
  - frontend/src/modules/billing/BillingPage.tsx
  - frontend/src/modules/work-items/WorkItemsPage.tsx
  - frontend/src/components/ui/PageHeader.tsx
  - frontend/src/components/ui/StatusBadge.tsx
  - frontend/src/components/ui/EmptyState.tsx
  - frontend/src/components/ui/FilterBar.tsx
  - frontend/src/components/ui/LoadingState.tsx
  - frontend/src/components/ui/ErrorState.tsx
  - THREAD_CHANGELOG.md

- Co zmieniono:
  - Dodano moduł `Rozliczenia` w centralnej nawigacji oraz trasę `/rozliczenia`.
  - Dodano moduł `Work Items` w centralnej nawigacji oraz trasę `/work-items`.
  - Rozszerzono typ nawigacji o pola przygotowane pod przyszłe `requiredCapabilities` i `featureFlag`.
  - Zamieniono generyczny placeholder pulpitu na pierwszy operacyjny widok migracyjny z KPI, filtrem, tabelą sygnałów i panelem kolejnych kroków.
  - Dodano bazowe komponenty UI: `PageHeader`, `StatusBadge`, `EmptyState`, `FilterBar`, `LoadingState`, `ErrorState`.
  - Włączono widoczność nagłówka modułu w `ModulePlaceholder`, bo wcześniej `.module-toolbar` był ukryty przez CSS.

- Ryzyko/skutki uboczne:
  - niskie/średnie; zmiana dotyczy wyłącznie produkcyjnego frontendu w `frontend/`.
  - nowe widoki używają statycznych danych migracyjnych i nie zmieniają kontraktów backendu.
  - nie podpięto jeszcze realnych danych runtime z API.

- Co sprawdzić lokalnie:
  - `npm.cmd run typecheck`
  - `npm.cmd run lint`
  - `npm.cmd run build`
  - `http://127.0.0.1:3000/pulpit`
  - `http://127.0.0.1:3000/rozliczenia`
  - `http://127.0.0.1:3000/work-items`

- Co sprawdzić na Railway:
  - brak, nie zlecono deployu.

---

## 2026-04-30 00:25 (Europe/Warsaw) - Aktualizacja dokumentacji projektowej i zasad pracy między wątkami

- Zakres wątku:
  - uporządkowanie dokumentacji projektowej CASI Workspace po nowych ustaleniach o architekturze, frontendzie, DigitalOcean/DigitalOcean AI, kosztach automatyzacji, KSeF, Make.com, rozliczeniach klientów, rolach i capability
  - doprecyzowanie, że CASI Workspace jest realną aplikacją produktową rozwijaną etapami, a nie makietą ani prowizorką
  - ujednolicenie kontekstu dla przyszłych wątków i pracy Codexa

- Zmienione pliki:
  - AGENTS.md
  - ARCHITECTURE.md
  - README.md
  - MODUL_ROZLICZEN_KLIENTOW.md
  - Role użytkowników.md
  - STARTER_WATKOW.md
  - THREAD_CHANGELOG.md

- Co zmieniono:
  - Zaktualizowano `AGENTS.md` jako główny plik zasad pracy dla Codexa i developerów.
  - Doprecyzowano, że finalny frontend produkcyjny ma powstawać w `frontend/`, a `static/` jest obecną działającą implementacją / legacy frontendem referencyjnym.
  - Dodano zasady pracy bez deployu: domyślnie praca lokalna, deploy tylko po wyraźnej komendzie użytkownika.
  - Uporządkowano kierunek architektury w `ARCHITECTURE.md`: aplikacja ma być budowana jako realny produkt etapami, z zachowaniem separacji organizacji, modułowości, bezpieczeństwa i gotowości do rozwoju.
  - Zaktualizowano `README.md`, aby był praktycznym opisem projektu i instrukcją startową, a nie pełnym dokumentem architektonicznym.
  - Doprecyzowano podejście do infrastruktury: Railway jest jednym z możliwych kierunków, ale nie jest jedyną ani ostateczną platformą; w przyszłości można rozważać DigitalOcean, Fly.io, Google Cloud, Vercel i inne środowiska.
  - Dodano zasadę unikania niepotrzebnego vendor lock-in, ale bez przesadnego komplikowania pierwszej wersji produktu.
  - Dodano kontekst DigitalOcean AI jako możliwej przyszłej opcji infrastruktury AI, bez traktowania jej jako obecnie wybranego rozwiązania.
  - Doprecyzowano filozofię kontroli kosztów automatyzacji: zamiast brutalnie wyłączać funkcje, preferować kolejki, rzadsze sprawdzanie, akcje na żądanie, priorytety i limity zależne od pakietu.
  - Dopisano kierunek dla KSeF: w wersji bazowej preferowany model na żądanie, np. przycisk `Sprawdź KSeF teraz`; automatyczne sprawdzanie może być funkcją późniejszą, premium albo konfigurowalną.
  - Uporządkowano dokument `MODUL_ROZLICZEN_KLIENTOW.md`: moduł rozliczeń ma być ogólnym modułem przychodowym dla organizacji, a nie wąskim modułem tylko dla uczniów.
  - Doprecyzowano model rozliczeń: `organizacje -> klienci organizacji -> usługi -> umowy -> naliczenia -> płatności`.
  - Zachowano obsługę rodzin, płatników, dzieci, rodzeństwa, szkół, wspólnych wpłat, KDR, zniżek rodzinnych i alokacji wpłat przez model `billing_customers + role + relacje + profile`.
  - Zaktualizowano `Role użytkowników.md`: model dostępu opiera się na roli, capability, zakresie organizacji i zasadzie `default deny`.
  - Dodano aktora `System / Integracja` dla workerów, schedulerów, webhooków, importerów, AI, OCR, Make.com, Telegrama, e-maila i KSeF.
  - Doprecyzowano, że automatyzacje i integracje powinny działać tylko w przyznanym zakresie i być widoczne w logach.
  - Zaktualizowano `STARTER_WATKOW.md` jako szybki plik startowy dla nowych wątków.
  - Dodano zasady czytania `AGENTS.md`, `ARCHITECTURE.md`, `README.md`, `THREAD_STATE.md` i ostatnich wpisów z `THREAD_CHANGELOG.md` przed większą pracą.
  - Doprecyzowano raport po zmianie: zmienione pliki, co zrobiono, ryzyko, testy, czego nie sprawdzono i co ewentualnie sprawdzić na serwerze.

- Ryzyko/skutki uboczne:
  - niskie, bo zmiany dotyczą dokumentacji i zasad pracy, a nie kodu aplikacji.
  - średnie organizacyjnie: dokumentacja może opisywać część kierunków rozwoju, które nie są jeszcze wdrożone w kodzie.
  - przyszłe wątki powinny rozróżniać obecną implementację od kierunku docelowego.
  - Codex może wymagać sprawdzenia aktualnego kodu przed założeniem, że dana tabela, endpoint albo moduł już istnieje.
  - Po wklejeniu dokumentów warto upewnić się, że bloki Markdown nie zawierają technicznych atrybutów typu `id="..."`.

- Co sprawdzić lokalnie:
  - czy wszystkie zaktualizowane pliki zostały zapisane w repozytorium w katalogu `C:\Users\erykl\OneDrive\Dokumenty\CASI Workspace`.
  - czy pliki Markdown poprawnie się wyświetlają.
  - czy w blokach kodu Markdown nie zostały przypadkowo wklejone atrybuty typu `id="..."`.
  - czy `AGENTS.md`, `ARCHITECTURE.md`, `README.md`, `MODUL_ROZLICZEN_KLIENTOW.md`, `Role użytkowników.md` i `STARTER_WATKOW.md` są ze sobą spójne.
  - czy przyszłe wątki zaczynają od odczytu `THREAD_STATE.md` i ostatnich wpisów z `THREAD_CHANGELOG.md`.

- Co sprawdzić na Railway:
  - brak, nie zlecono deployu.

---

## 2026-04-19 15:43 (Europe/Warsaw) - Work Items: kolejne 5 kroków (polityka SLA + workload + filtry/sortowanie)

- Zakres wątku:
  - realizacja kolejnych 5 kroków rozwoju modułu `work_items` po etapie summary/bulk/reopen/search

- Zmienione pliki:
  - app/db.py
  - app/repositories/organization_repository.py
  - app/repositories/work_item_repository.py
  - app/services/work_item_service.py
  - app/api/http_server.py
  - tests/test_work_item_service.py
  - tests/test_work_item_http.py
  - README.md
  - THREAD_CHANGELOG.md

- Co zmieniono:
  - Dodano politykę SLA per organizacja (`organizations.work_item_sla_policy_json`) z domyślną konfiguracją i walidacją.
  - Dodano endpointy:
    - `GET /api/work-items/sla-policy`
    - `POST /api/work-items/sla-policy`
    - `GET /api/work-items/workload`
  - Wprowadzono automatyczne wyliczanie terminu SLA na podstawie polityki przy tworzeniu i ponownym otwieraniu pozycji pracy, gdy termin SLA nie jest podany jawnie.
  - Rozszerzono listowanie `GET /api/work-items` o filtry:
    - `unassigned_only`
    - `due_overdue_only`
    - `sla_overdue_only`
    - oraz sortowanie `sort_by` + `sort_dir`.
  - Dodano agregację obciążenia zespołu per przypisany użytkownik, w tym koszyk `Nieprzypisane`.
  - Dodano indeksy pod nowe scenariusze zapytań: `due_at`, `organization_id + assigned_user_id + status`.
  - Rozszerzono testy service/API oraz dokumentację README.

- Ryzyko/skutki uboczne:
  - niskie/średnie; nowa polityka SLA per organizacja zmienia domyślne terminy SLA przy tworzeniu/ponownym otwieraniu pozycji.
  - przy niestandardowych klientach API warto zweryfikować, czy nie zakładają stałego `sla_warning_minutes=120`.

- Co sprawdzić lokalnie:
  - odczyt i zapis polityki SLA przez `/api/work-items/sla-policy`
  - automatyczne uzupełnianie `sla_deadline_at` i `sla_warning_minutes` dla nowych work itemów
  - wynik `/api/work-items/workload` dla przypadków przypisanych i nieprzypisanych
  - nowe filtry i sortowanie listy `/api/work-items`

- Co sprawdzić na Railway:
  - brak, nie zlecono deployu.

---

## 2026-04-19 15:31 (Europe/Warsaw) - Work Items: kolejne 5 kroków ulepszeń (SLA + operacje + search)

- Zakres wątku:
  - realizacja 5 kolejnych kroków rozwoju modułu `work_items`
  - domknięcie diagnostyki i poprawka SQL dla endpointu podsumowań

- Zmienione pliki:
  - app/repositories/work_item_repository.py
  - app/services/work_item_service.py
  - app/api/http_server.py
  - app/services/search_service.py
  - app/bootstrap.py
  - README.md
  - tests/test_work_item_service.py
  - tests/test_work_item_http.py
  - tests/test_search_work_items.py
  - THREAD_CHANGELOG.md

- Co zmieniono:
  - Dodano podsumowania operacyjne SLA dla `work_items` (`/api/work-items/summary`), w tym liczniki statusów/SLA, overdue i listę `top_risk`.
  - Dodano operacje masowe (`/api/work-items/bulk`) dla akcji: assign, snooze, escalate, close, reopen.
  - Dodano osobną akcję ponownego otwarcia rekordu (`/api/work-items/{id}/reopen`).
  - Rozszerzono warstwę serwisową o `get_summary`, `bulk_apply`, `reopen_work_item`.
  - Zintegrowano `work_items` z globalnym wyszukiwaniem i mapowaniem grup wyników.
  - Zaktualizowano README o nowe endpointy i opis SLA.
  - Naprawiono błąd parametryzacji SQL w `work_item_repository.summary`, oddzielne parametry dla zapytań `summary` i `top_risk`.

- Ryzyko/skutki uboczne:
  - niskie/średnie; rozszerzony został kontrakt API i logika wyszukiwania, co może ujawnić brakujące uprawnienia w niestandardowych integracjach klienckich.
  - testy wyszukiwarki wymagają uruchamiania sekwencyjnego na wspólnej lokalnej bazie SQLite; równolegle uruchomione procesy testowe mogą kolidować.

- Co sprawdzić lokalnie:
  - `GET /api/work-items/summary` zwraca poprawne liczniki i `top_risk`.
  - `POST /api/work-items/bulk` poprawnie modyfikuje wiele rekordów i respektuje scope organizacji.
  - `POST /api/work-items/{id}/reopen` zmienia status/SLA i dodaje historię.
  - globalna wyszukiwarka zwraca grupę `work_items` dla zapytań SLA.

- Co sprawdzić na Railway:
  - brak, nie zlecono deployu.

---

## 2026-04-19 01:29 (Europe/Warsaw) - Naprawa rozwijania menu nagłówka (`...` i `WS`)

- Zakres wątku:
  - naprawa obsługi kliknięć w przełącznikach menu nagłówka

- Zmienione pliki:
  - static/app.js
  - static/index.html
  - static/styles.css
  - static/sw.js
  - static/whiteboard.js
  - THREAD_CHANGELOG.md

- Co zmieniono:
  - W obsłudze globalnych kliknięć dodano bezpieczne mapowanie `event.target` na element nadrzędny, gdy klik trafia w węzły tekstowe.
  - Dzięki temu przyciski `...` i `WS` poprawnie otwierają panele menu także przy kliknięciu bezpośrednio w tekst.
  - Podpięto obsługę kliknięć bezpośrednio do przycisków `#topbar-more-toggle` i `#profile-menu-toggle`, bez zależności od delegacji na `document`.
  - Dodano fallback obsługi `pointerdown` na tych przyciskach i deduplikację `click` po `pointerdown`, aby menu otwierało się także wtedy, gdy przeglądarka anuluje klasyczny `click`.
  - Wydzielono niezależny mechanizm podpinania przełączników menu nagłówka (`podlaczPrzelacznikiMenuNaglowka`) i uruchomiono go na samym początku `podepnijZdarzenia`, aby menu działało nawet przy częściowej awarii dalszej inicjalizacji eventów.
  - Dodano awaryjny listener `document.pointerdown` (capture), który sprawdza położenie kliknięcia względem prostokątów przycisków menu i otwiera odpowiedni panel nawet przy nietypowym przechwytywaniu zdarzeń przez warstwy UI.
  - Dodano bufor czasowy po przełączeniu menu (`ignorujKlikPoPrzelaczeniuMenuNaglowkaDo`), aby globalny handler `click` nie zamykał panelu natychmiast po otwarciu przy niestandardowej sekwencji pointer/click.
  - Podbito wersję skryptu `app.js` w `index.html` do `v=20260419e`, aby wymusić pobranie nowego bundla mimo cache service workera.
  - W `whiteboard.js` poprawiono normalizację `event.target` dla globalnych zdarzeń `pointerdown`, aby tekst klikany wewnątrz przycisków był traktowany jak element-przycisk, bez niechcianego `preventDefault`.
  - Podbito wersję skryptu `whiteboard.js` w `index.html` do `v=20260419a`, aby wymusić pobranie nowej wersji.
  - W `styles.css` włączono `pointer-events: auto` dla `topbar-user-chip` i podbito wersję arkusza do `v=20260419a`.
  - Podbito nazwę cache service workera do `casi-workspace-shell-v4`, aby wymusić odświeżenie cache aplikacji shell.

- Ryzyko/skutki uboczne:
  - niskie; zmiana dotyczy głównie obsługi zdarzeń kliknięcia i pointer events w menu nagłówka.

- Co sprawdzić lokalnie:
  - kliknięcie w `...` otwiera/zamyka panel organizacji.
  - kliknięcie w `WS` otwiera/zamyka panel sesji.
  - kliknięcie poza panelem zamyka otwarte menu.

- Co sprawdzić na Railway:
  - brak, nie zlecono deployu.

---

## 2026-04-18 18:45 (Europe/Warsaw) - Inicjalizacja governance wątków

- Zakres wątku:
  - uporządkowanie zasad między wątkami

- Zmienione pliki:
  - STARTER_WATKOW.md
  - THREAD_STATE.md
  - THREAD_CHANGELOG.md

- Co zmieniono:
  - Dodano centralny starter dla wątków.
  - Dodano snapshot aktualnych zasad.
  - Dodano wspólny dziennik zmian.

- Ryzyko/skutki uboczne:
  - wątki, które nie dostaną polecenia odczytu plików, mogą pracować po starych założeniach.

- Co sprawdzić lokalnie:
  - czy nowe wątki zaczynają od odczytu trzech plików i potwierdzają zasady.

- Co sprawdzić na Railway:
  - brak, nie zlecono deployu.
