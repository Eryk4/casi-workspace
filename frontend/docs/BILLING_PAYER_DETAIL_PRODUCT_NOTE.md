# Szczegół płatnika v1

`/rozliczenia/platnicy/{payerId}` jest read-only ekranem kontekstu płatnika w module `Rozliczenia`.

## Cel ekranu

Ekran ma odpowiedzieć na pytania:

- kto jest płatnikiem,
- za kogo płaci,
- jakie usługi są objęte rozliczeniem,
- z czego wynika saldo,
- jakie naliczenia i widoczne wpłaty są dostępne,
- czy istnieją powiązane faktury albo sprawy operacyjne.

`Płatnik` jest pojęciem nadrzędnym. Rodzina jest tylko jednym z typów płatnika, gdy jedna osoba lub grupa rozliczeniowa płaci za uczniów lub rodzeństwo.

## Źródła danych

Ekran korzysta z istniejących, organizacyjnie scoped źródeł read-only:

- `GET /api/billing/ledger/balances?organization_id=...`,
- `GET /api/billing/payers?organization_id=...`,
- `GET /api/billing/students?organization_id=...`,
- `GET /api/billing/charges?organization_id=...`,
- `GET /api/invoices?organization_id=...`,
- `GET /api/contractors?organization_id=...`,
- `GET /api/work-items?organization_id=...&only_open=1&limit=100`,
- `GET /api/billing/payers/{payerId}/notes?organization_id=...`.

Nie dodano nowego endpointu backendowego. Relacje są składane deterministycznie po stronie frontendu z dostępnych danych.

## Zakres v1

Ekran pokazuje:

- profil płatnika,
- osoby objęte rozliczeniem,
- usługi do opłacenia, w tym typ usługi, okres, status, liczbę naliczeń i źródło danych,
- wyjaśnienie salda,
- naliczenia,
- ostatnią widoczną wpłatę, jeśli jest dostępna,
- powiązane faktury, jeśli można je bezpiecznie ustalić,
- powiązane sprawy, jeśli można je bezpiecznie ustalić,
- kontekst biznesowy,
- notatki rozliczeniowe operatora.

Ekran jest w pełni read-only. Dozwolone są tylko odświeżenie danych i linki do istniejących modułów.

Etap `Usługi i zapisy — read-only foundation` doprecyzowuje sekcję `Usługi do opłacenia`. Dane są wywnioskowane z obecnych naliczeń, modeli rozliczeń i faktur. Widok nie udaje pełnego modelu zapisów, kontraktów ani cenników; pokazuje tylko to, co da się bezpiecznie odczytać z aktualnych danych.

Etap `Wpłaty i przypisania — read-only foundation` ma osobny widok `/rozliczenia/wplaty`. Szczegół płatnika nadal pokazuje widoczne informacje o jednym płatniku, a osobny widok wpłat wyjaśnia, czy wpłata jest przy naliczeniu, tylko przy płatniku czy wymaga późniejszego wyjaśnienia.

## Czego v1 nie robi

Ekran nie wykonuje:

- dodawania płatności,
- naliczania opłat,
- importu przelewów,
- dopasowywania wpłat,
- korekt,
- przypomnień,
- księgowania,
- edycji płatnika,
- edycji ucznia,
- usuwania danych.

Dozwolona akcja v1:

- dodanie notatki rozliczeniowej operatora do p?atnika.

Notatka jest addytywna, wymaga aktywnej organizacji, przyjmuje wy??cznie pole `note_text`, ma limit 2000 znak?w i nie loguje pe?nej tre?ci w zdarzeniu systemowym. Historia systemowa zapisuje tylko metadane: identyfikator notatki, p?atnika i d?ugo?? tre?ci.

## Ograniczenia

- Lista wpłat jest ograniczona do danych widocznych w obecnym read-only modelu. Jeżeli backend udostępnia tylko ostatnią wpłatę w saldzie, ekran pokazuje właśnie tę informację.
- `/rozliczenia/wplaty` pokazuje szerszy read-only obraz wpłat i obecnych przypisań, ale nadal nie wykonuje dopasowania ani księgowania.
- Powiązania faktur i spraw zależą od obecnych danych referencyjnych oraz tekstowych. Jeśli relacja nie jest jednoznaczna, ekran pokazuje pusty stan zamiast zgadywać.
- Ekran nie zastępuje pełnego silnika rozliczeniowego ani księgowości.
- Sekcja usług nie jest jeszcze pełnym rejestrem zapisów. Pełne zapisy, cenniki, historia statusów i naliczenia będą osobnym etapem.

## Następny bezpieczny krok

Po live-weryfikacji warto rozważyć osobny read-only kontrakt backendowy dla usług/zapisów tylko wtedy, gdy frontendowa inferencja z naliczeń okaże się zbyt płytka. Nadal bez importów, płatności i akcji zapisu.

## Etap: Kontakt rozliczeniowy — draft & log v1

Szczegół płatnika ma teraz addytywną sekcję `Kontakt rozliczeniowy`. Operator może przygotować treść do samodzielnego skopiowania albo zapisać ślad kontaktu z płatnikiem. CASI Workspace nie wysyła tej wiadomości i nie integruje się w tym etapie z SMS, e-mailem, Gmailem ani automatyzacją przypomnień.

Kontakt rozliczeniowy zapisuje rekord w `billing_contact_events`, wymaga aktywnego `organization_id`, sprawdza płatnika i opcjonalną wpłatę w tej samej organizacji, a systemowy audit zapisuje tylko metadane oraz długości treści. Pełna treść wiadomości i notatki nie jest kopiowana do details zdarzenia.

Ten etap nie zmienia salda, naliczeń, wpłat, dopasowań, statusów, importów, przypomnień ani księgowania. To nadal kontrolowany fundament operacyjny, a nie workflow wysyłki.

## Powiazanie z centrum kontaktow

Szczegol platnika prowadzi do `/rozliczenia/kontakty`, gdzie mozna przejrzec wszystkie kontakty rozliczeniowe w aktywnej organizacji. Szczegol platnika pozostaje miejscem zapisu pojedynczego kontaktu, a centrum kontaktow jest tylko read-only przegladem.
