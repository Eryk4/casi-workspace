# Zaległości i nadpłaty — read-only centrum decyzyjne

Trasa: `/rozliczenia/zaleglosci`

Ten ekran jest read-only widokiem decyzyjnym w module `Rozliczenia`. Ma pomóc właścicielowi firmy szybko zobaczyć, kto ma zaległość, kto ma nadpłatę i które rozliczenia wymagają wyjaśnienia.

## Cel

Ekran odpowiada na pytania:

- kto ma zaległość,
- kto ma nadpłatę,
- gdzie są wpłaty do sprawdzenia,
- które salda wymagają rozmowy z płatnikiem,
- gdzie kliknąć dalej: płatnik, wpłaty albo okresy.

## Źródła danych

Widok korzysta wyłącznie z istniejących read-only źródeł organizacyjnych:

- `GET /api/billing/ledger/balances?organization_id=...`,
- `GET /api/billing/payers?organization_id=...`,
- `GET /api/billing/students?organization_id=...`,
- `GET /api/billing/charges?organization_id=...`,
- `GET /api/billing/ledger/matches?organization_id=...`,
- `GET /api/billing/transactions?organization_id=...`,
- `GET /api/billing/payers/{payerId}/notes?organization_id=...` dla płatników z niezerowym saldem.

Nie dodano backendu, endpointu ani migracji.

## Jak model liczy wartości

- Zaległość płatnika wynika z dodatniego `balance_due`.
- Nadpłata wynika z ujemnego `balance_due`.
- Rozliczony na zero oznacza saldo bliskie `0` w obecnym ledgerze.
- Ostatnia wpłata pochodzi z widocznych pól ostatniej wpłaty na płatniku albo saldzie.
- Okresy, usługi i osoby są pokazywane tylko wtedy, gdy wynikają z `billing_charges` i `billing_students`.
- Wpłaty przypisane tylko do płatnika są wykrywane przez `billing_payment_matches` bez `billing_charge_id`.
- Wpłaty bez jasnego przypisania są sygnałem do wyjaśnienia, ale widok nie przypisuje ich samodzielnie.

Model nie liczy dni po terminie, jeśli nie ma wiarygodnego terminu płatności dla decyzji operacyjnej.

## Sekcje

- karty podsumowania,
- `Najpilniejsze sprawy`,
- `Zaległości`,
- `Nadpłaty`,
- `Do wyjaśnienia`,
- `Kontekst biznesowy`.

## Czego ekran nie robi

Ekran nie wykonuje żadnej operacji finansowej. W szczególności nie:

- dodaje płatności,
- importuje przelewów,
- dopasowuje wpłat,
- zmienia przypisań,
- zmienia salda,
- rozlicza nadpłat,
- zwraca nadpłat,
- wysyła przypomnień,
- tworzy zadań,
- księguje,
- edytuje ani usuwa danych.

Dozwolone są tylko linki, powrót i odświeżenie.

## Ograniczenia

Widok jest uczciwą mapą aktualnych danych. Jeśli wpłata jest widoczna tylko przy płatniku, ekran pokazuje ją jako sprawę do sprawdzenia, ale nie przypisuje jej do naliczenia ani okresu.

Nadpłata nie jest automatycznie przenoszona ani zwracana. To wymaga osobnego, kontrolowanego workflow i osobnej decyzji produktowej.

## Następny bezpieczny krok

Po live-weryfikacji tego ekranu najbezpieczniejszym kolejnym krokiem jest decyzja, czy potrzebny jest osobny read-only agregat backendowy dla rozliczeń. Write actions dotyczące dopasowań, importu, przypomnień albo rozliczania nadpłat powinny pozostać poza zakresem do czasu osobnego audytu kontraktu, uprawnień i tenant isolation.
