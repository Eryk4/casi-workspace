# Okres rozliczeniowy v1

`/rozliczenia/okresy` jest read-only ekranem okresów rozliczeniowych w module `Rozliczenia`.

## Cel ekranu

Ekran ma odpowiedzieć na pytanie:

- jak wygląda rozliczenie za wybrany miesiąc, semestr albo inny widoczny okres,
- którzy płatnicy mają dopłatę, nadpłatę albo rozliczony okres,
- za jakie usługi naliczono opłaty,
- które pozycje wymagają uwagi właściciela firmy.

To jest widok informacyjny. Nie zamyka okresu, nie generuje naliczeń i nie zastępuje księgowości.

## Źródła danych

Widok korzysta wyłącznie z istniejących, organizacyjnie scoped źródeł read-only:

- `GET /api/billing/ledger/balances?organization_id=...`,
- `GET /api/billing/payers?organization_id=...`,
- `GET /api/billing/students?organization_id=...`,
- `GET /api/billing/charges?organization_id=...`,
- `GET /api/billing/ledger/matches?organization_id=...`.

Nie dodano nowego endpointu backendowego. Okresy są wywnioskowane z obecnych `billing_charges.period_label`, a widoczne wpłaty są liczone tylko z dopasowań płatności powiązanych z konkretnymi naliczeniami.

Ważne ograniczenie: część wpłat może być widoczna przy płatniku, ale bez relacji do konkretnego naliczenia. Taka wpłata nie jest przypisywana do okresu w tym widoku, bo frontend nie powinien zgadywać, którego miesiąca, semestru albo turnusu dotyczy.

## Zakres v1

Ekran pokazuje:

- listę okresów dostępnych w danych,
- podsumowanie wybranego okresu,
- płatników w okresie,
- osoby objęte rozliczeniem,
- usługi w okresie,
- naliczone kwoty,
- widoczne wpłaty,
- saldo okresu,
- dopłaty, nadpłaty i rozliczone pozycje,
- krótkie powody, dlaczego dana pozycja wymaga uwagi,
- kontekst biznesowy i ograniczenia danych.

Ekran jest w pełni read-only. Dozwolone są tylko odświeżenie danych, wybór okresu i linki do istniejących modułów.

## Czego v1 nie robi

Ekran nie wykonuje:

- generowania naliczeń,
- zamykania okresu,
- importu przelewów,
- dopasowywania płatności,
- korekt,
- przypomnień,
- księgowania,
- eksportu,
- edycji usług,
- edycji zapisów,
- edycji płatników,
- żadnych write actions.

## Ograniczenia

- Okres jest obecnie etykietą z istniejących naliczeń, a nie pełnym obiektem domenowym `billing_period`.
- Widoczne wpłaty są liczone tylko wtedy, gdy dopasowanie płatności wskazuje konkretne naliczenie.
- Brak nadpłaty albo rozliczonej pozycji w okresie nie oznacza automatycznie, że płatnik globalnie nie ma wpłat. Może oznaczać, że wpłata jest widoczna przy płatniku, ale nie jest jeszcze przypisana do naliczeń tego okresu.
- Nieobsłużone, nieprzypisane albo częściowo przypisane wpłaty wymagają osobnego etapu pełnego workflow płatności.
- Pełne rozliczenie okresowe wymaga późniejszego modelu `payment_allocation` albo równoważnego przypisania płatności do naliczeń.
- Widok usług jest wywnioskowany z naliczeń i modeli rozliczeń. Nie jest jeszcze pełnym rejestrem zapisów, umów ani cenników.
- Ekran nie przenosi nadpłat między okresami i nie podejmuje decyzji finansowych.

## Następny bezpieczny krok

Po live-weryfikacji okresów warto utrzymać moduł jako read-only i dopiero osobno zaprojektować pełny model okresu rozliczeniowego, jeśli obecne etykiety okresów okażą się niewystarczające. Przypisywanie wpłat do okresów powinno być osobnym etapem przed importami, automatycznym dopasowaniem i zamykaniem okresów. Write paths dla płatności, importów, dopasowań i zamykania okresu wymagają osobnego audytu kontraktu, uprawnień, izolacji organizacyjnej i UX.
