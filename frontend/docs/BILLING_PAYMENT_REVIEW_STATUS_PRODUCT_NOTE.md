# Status operacyjny wpłaty — write v1

`/rozliczenia/wplaty/{paymentId}` ma pierwszy wąski zapis dotyczący wpłaty: status operacyjny.

To nie jest dopasowanie płatności, księgowanie, import, korekta ani zmiana salda. Status jest wewnętrzną, addytywną adnotacją operatora, która pomaga oznaczyć, co trzeba sprawdzić przy widocznej wpłacie.

## Kontrakt API

- `GET /api/billing/payments/{paymentId}/review-status?organization_id=...`
- `POST /api/billing/payments/{paymentId}/review-status?organization_id=...`

Payload zapisu:

```json
{
  "status": "needs_review",
  "note_text": "Krótka notatka operatora"
}
```

`note_text` jest opcjonalne i ma limit 1000 znaków.

Dozwolone statusy:

- `needs_review` — do wyjaśnienia,
- `checked` — sprawdzone,
- `waiting_for_contact` — czeka na kontakt,
- `waiting_for_payment` — czeka na wpłatę,
- `do_not_auto_match` — nie ruszać automatycznie.

Endpoint odrzuca nadmiarowe pola payloadu.

## Gwarancje bezpieczeństwa

Status operacyjny:

- wymaga aktywnego `organization_id`,
- jest zapisywany wyłącznie dla wpłaty należącej do tej organizacji,
- nie zmienia `billing_transactions`,
- nie zmienia `billing_charges`,
- nie zmienia `billing_payment_matches`,
- nie zmienia `billing_payer_ledger_entries`,
- nie zmienia salda płatnika,
- nie uruchamia importu, dopasowania, przypomnienia ani eksportu.

Historia systemowa zapisuje tylko metadane: identyfikator zdarzenia, identyfikator wpłaty, status i długość notatki. Pełny tekst notatki nie trafia do event details.

## Model danych

Statusy są addytywne i przechowywane w `billing_payment_review_events`.

Tabela jest częścią schematu SQLite/PostgreSQL i migratora SQLite → configured DB. Reset lokalnego sandboxu czyści tę tabelę razem z pozostałymi danymi rozliczeniowymi.

## UI

Na szczególe wpłaty użytkownik widzi:

- aktualny status operacyjny,
- opcjonalną notatkę,
- krótką historię zmian statusu,
- formularz wyboru statusu i notatki.

Sukces pojawia się dopiero po odpowiedzi backendu i odświeżeniu szczegółu wpłaty. Brak aktywnej organizacji blokuje zapis przed requestem.

## Czego nadal nie ma

Ten etap nie dodaje:

- dodawania wpłat,
- importu przelewów,
- automatycznego lub ręcznego dopasowania,
- zmiany przypisania,
- naliczania,
- korekt,
- przypomnień,
- księgowania,
- statusów finansowych.

To jest bezpieczny status operacyjny, a nie workflow płatności.

## Wykorzystanie w sprawach rozliczeniowych

`/rozliczenia/sprawy` używa ostatnich statusów operacyjnych wpłat jako sygnału do kolejki pracy. Do tego służy read-only agregat `GET /api/billing/payment-review-statuses?organization_id=...`, który zwraca ostatni status wpłat w ramach jednej organizacji.

Agregat nie zapisuje danych i nie zmienia transakcji, naliczeń, dopasowań, sald ani historii finansowej. Dzięki niemu ekran spraw rozliczeniowych nie musi odpytywać osobno każdej wpłaty.
