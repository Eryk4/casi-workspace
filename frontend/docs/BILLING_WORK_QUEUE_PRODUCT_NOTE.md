# Sprawy rozliczeniowe — v1

Trasa: `/rozliczenia/sprawy`

`Sprawy rozliczeniowe` to operacyjny widok pracy w module `Rozliczenia`. Dane finansowe pozostaj? read-only, ale ekran ma jedn? w?sk? akcj? zapisu: append-only decyzj? operatora `Obs?u?ona` albo `Od?o?ona`. Ma odpowiedzieć na pytanie: co warto dziś sprawdzić w rozliczeniach i gdzie kliknąć dalej.

## Cel

Widok zbiera sygnały z istniejących danych:

- zaległości,
- nadpłaty,
- wpłaty przypisane tylko do płatnika,
- wpłaty bez jasnego przypisania,
- statusy operacyjne wpłat,
- notatki rozliczeniowe płatnika.

Ekran nie zastępuje modułów szczegółowych. Porządkuje kolejność pracy i odsyła do płatnika, szczegółu wpłaty, wpłat albo zaległości.

## Źródła danych

Frontend korzysta z istniejących read-only źródeł rozliczeń oraz z jednego wąskiego agregatu statusów operacyjnych:

- `GET /api/billing/ledger/balances?organization_id=...`,
- `GET /api/billing/payers?organization_id=...`,
- `GET /api/billing/students?organization_id=...`,
- `GET /api/billing/charges?organization_id=...`,
- `GET /api/billing/ledger/matches?organization_id=...`,
- `GET /api/billing/transactions?organization_id=...`,
- `GET /api/billing/payment-review-statuses?organization_id=...`,
- `GET /api/billing/payers/{payerId}/notes?organization_id=...` dla płatników z widocznym saldem.

Agregat statusów jest read-only, organizacyjnie scoped i zwraca tylko ostatni status operacyjny widocznych wpłat w danej organizacji. Nie zmienia transakcji, naliczeń, dopasowań, sald ani historii finansowej.

## Typy spraw

Model buduje sprawy deterministycznie:

- `Wpłata do wyjaśnienia`,
- `Czeka na kontakt`,
- `Czeka na wpłatę`,
- `Nie ruszać automatycznie`,
- `Nadpłata do decyzji`,
- `Zaległość do sprawdzenia`,
- `Sprawdzone` jako osobna sekcja, nie jako pilne zadanie.

Priorytety to `Wysoki`, `Średni` i `Niski`. Status `Sprawdzone` nie trafia do sekcji `Najpierw zrób`.

## Sekcje ekranu

- podsumowanie liczby spraw,
- `Najpierw zrób`,
- `Wpłaty do wyjaśnienia`,
- `Płatnicy do kontaktu`,
- `Nadpłaty do decyzji`,
- `Ostatnio sprawdzone`,
- linki do innych widoków rozliczeń,
- kontekst biznesowy.

## Zakres read-only

Ekran pozwala tylko przejść dalej albo odświeżyć dane. Nie wykonuje żadnej operacji finansowej.

Nie dodaje płatności, nie importuje przelewów, nie dopasowuje wpłat, nie zmienia przypisania, nie zmienia salda, nie rozlicza nadpłat, nie wysyła przypomnień, nie tworzy zadań, nie edytuje i nie usuwa danych.

Status operacyjny wpłaty pozostaje edytowany wyłącznie na szczególe wpłaty. Ten ekran tylko wykorzystuje go jako sygnał do pracy człowieka.

## Ograniczenia

Widok nie liczy dni po terminie, jeśli dane nie dają wiarygodnego terminu. Nie zgaduje okresu dla wpłat bez powiązania z naliczeniem. Nie rozstrzyga, co zrobić z nadpłatą. To pozostaje osobnym, kontrolowanym workflow w przyszłości.

## Następny bezpieczny krok

Po live-weryfikacji warto utrzymać ekran jako centrum pracy read-only. Kolejne write actions w rozliczeniach powinny przechodzić osobny audyt tenant isolation, payload allowlist, uprawnień i live-checku.
