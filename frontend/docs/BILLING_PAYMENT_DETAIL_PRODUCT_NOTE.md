# Szczegół wpłaty v1

`/rozliczenia/wplaty/{paymentId}` jest read-only ekranem pojedynczej widocznej wpłaty w module `Rozliczenia`.

W obecnym modelu `paymentId` oznacza `billing_transaction_id`. To jest techniczny identyfikator transakcji używany wyłącznie do routingu; UI nie pokazuje go użytkownikowi jako biznesowego numeru wpłaty.

## Cel ekranu

Ekran odpowiada na pytania:

- jaka wpłata jest widoczna,
- jaka jest kwota i data,
- czy znamy płatnika,
- czy wpłata jest przypisana do konkretnego naliczenia,
- czy jest widoczna tylko przy płatniku,
- czy wymaga późniejszego wyjaśnienia.

## Źródła danych

Widok korzysta wyłącznie z istniejących endpointów read-only:

- `GET /api/billing/transactions`,
- `GET /api/billing/ledger/matches`,
- `GET /api/billing/charges`,
- `GET /api/billing/payers`,
- `GET /api/billing/students`.

Nie dodano nowego endpointu backendowego, tabeli ani migracji.

## Co pokazuje

Jeśli wpłata ma match z `billing_charge_id`, ekran pokazuje naliczenie, usługę, osobę lub klienta firmowego, okres i kwotę przypisaną.

Jeśli wpłata ma match tylko z płatnikiem, ekran pokazuje płatnika i jasno mówi, że wpłata nie jest przypisana do konkretnego naliczenia ani okresu.

Jeśli wpłata nie ma jasnego przypisania, ekran pokazuje neutralny stan `Do wyjaśnienia` i nie zgaduje płatnika, naliczenia ani okresu.

## Czego ekran nie robi

Ekran nie:

- dodaje wpłat,
- importuje przelewów,
- dopasowuje wpłat,
- zmienia przypisania,
- rozlicza naliczeń,
- księguje,
- zmienia salda,
- dodaje notatek,
- wysyła przypomnień.

To jest mapa obecnych danych, a nie workflow płatności.

## Ograniczenia

- Okres jest pokazywany tylko przez powiązane naliczenie.
- Wpłata przypisana tylko do płatnika nie jest automatycznie przypisywana do okresu.
- Jedna wpłata może mieć kilka przypisań, jeśli obecne dane zawierają kilka matchy.
- Pełne przypisywanie wpłat, podział kwot, korekty i importy bankowe wymagają osobnego etapu.
