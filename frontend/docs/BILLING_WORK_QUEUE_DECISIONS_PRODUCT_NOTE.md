# Decyzje spraw rozliczeniowych — write v1

Trasa produktu: `/rozliczenia/sprawy`.

Ten etap dodaje jedną wąską akcję operacyjną dla listy spraw rozliczeniowych:

- `Obsłużona`,
- `Odłożona`.

Decyzja jest append-only i zapisuje rekord w `billing_work_queue_events`. Nie nadpisuje sprawy, nie usuwa historii i nie zmienia danych źródłowych, z których kolejka jest wyliczana.

## Co ta akcja oznacza

`Obsłużona` oznacza tylko, że operator zajął się konkretną pozycją z kolejki pracy i nie chce jej widzieć w sekcji `Najpierw zrób`.

`Odłożona` oznacza tylko, że operator świadomie odkłada sprawę na później. Nie tworzy przypomnienia, zadania, terminu ani automatyzacji.

## Czego ta akcja nie robi

Decyzja sprawy rozliczeniowej nie jest operacją finansową. Nie zmienia:

- salda,
- wpłat,
- naliczeń,
- dopasowań wpłat,
- ledgeru płatnika,
- statusu operacyjnego wpłaty,
- przypisania wpłaty,
- nadpłaty,
- okresu rozliczeniowego.

Nie wysyła e-maili, SMS-ów, przypomnień ani nie tworzy zadań w task managerze.

## API

Endpointy:

- `GET /api/billing/work-queue/events?organization_id=...`
- `POST /api/billing/work-queue/events?organization_id=...`

Payload POST przyjmuje tylko:

```json
{
  "issue_key": "payment:65:unexplained:wplata-do-wyjasnienia",
  "issue_type": "Wpłata do wyjaśnienia",
  "target_type": "payment",
  "target_id": 65,
  "action": "handled",
  "note_text": "Opcjonalna notatka operatora"
}
```

`note_text` jest opcjonalne, trimowane i ograniczone do 1000 znaków. Backend odrzuca nadmiarowe pola.

## Scope i bezpieczeństwo

Backend wymaga `organization_id` przez write scope. Dla targetów weryfikowalnych:

- `payment` musi istnieć w tej samej organizacji,
- `payer` musi istnieć w tej samej organizacji.

Cross-org POST ma zostać odrzucony i nie może utworzyć eventu w złej organizacji.

Audit systemowy `billing_work_queue_event_added` zapisuje tylko metadane: id eventu, typ sprawy, target, akcję i długość notatki. Pełna treść notatki nie jest kopiowana do event details.

## UI

`/rozliczenia/sprawy` pokazuje:

- aktywne sprawy w sekcjach roboczych,
- `Odłożone sprawy`,
- `Ostatnio obsłużone`.

Sprawy oznaczone jako `Obsłużona` albo `Odłożona` nie trafiają do `Najpierw zrób`. Sukces w UI pojawia się dopiero po odpowiedzi backendu i odświeżeniu danych.

## Relacja ze statusem wpłaty

To nie jest ten sam mechanizm co status operacyjny wpłaty. Status wpłaty mówi o samej wpłacie, np. `Do wyjaśnienia` albo `Sprawdzone`. Decyzja sprawy mówi tylko, co operator zrobił z konkretną pozycją w kolejce pracy.

Zmiana decyzji sprawy nie zmienia automatycznie statusu wpłaty.

## Relacja z kontaktem rozliczeniowym

Decyzja sprawy rozliczeniowej i kontakt rozliczeniowy to dwa różne mechanizmy. Decyzja `Obsłużona` lub `Odłożona` porządkuje kolejkę pracy. Kontakt rozliczeniowy zapisuje roboczą treść albo ślad kontaktu przy płatniku.

Żaden z tych mechanizmów nie zmienia salda, naliczeń, dopasowań, przypisań wpłat, przypomnień ani księgowania.
