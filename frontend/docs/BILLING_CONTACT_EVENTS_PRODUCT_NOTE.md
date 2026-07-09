# Kontakt rozliczeniowy — draft & log v1

Ten etap dodaje pierwszy bezpieczny kontakt rozliczeniowy przy płatniku w module `Rozliczenia`.

## Cel

`Kontakt rozliczeniowy` ma pomóc operatorowi przygotować treść wiadomości albo zapisać ślad kontaktu z płatnikiem bez uruchamiania automatyzacji i bez zmiany finansów.

Ekran odpowiada na pytania:

- jaki kontakt przygotowano lub odnotowano,
- jakim kanałem miał się odbyć,
- czy była to treść robocza, rozmowa, brak odpowiedzi, obietnica wpłaty albo potrzeba ponowienia,
- kto i kiedy zapisał wpis,
- czy wpis dotyczył konkretnej wpłaty albo sprawy rozliczeniowej.

## API

Endpointy:

- `GET /api/billing/contact-events?organization_id=...`
- `POST /api/billing/contact-events?organization_id=...`

Dostępne filtry GET:

- `payer_id`,
- `payment_id`,
- `issue_key`,
- `limit`.

Payload POST przyjmuje tylko:

```json
{
  "payer_id": 1,
  "related_payment_id": 7,
  "related_issue_key": "payment:7:payer-only",
  "channel": "sms",
  "contact_action": "draft_prepared",
  "message_text": "Treść robocza do skopiowania",
  "note_text": "Opcjonalna notatka operatora"
}
```

Dozwolone kanały: `sms`, `email`, `phone`, `in_person`, `other`.

Dozwolone typy wpisu: `draft_prepared`, `contact_logged`, `no_answer`, `promised_payment`, `needs_followup`.

`message_text` ma limit 2000 znaków. `note_text` ma limit 1000 znaków. Backend odrzuca nadmiarowe pola.

## Bezpieczeństwo i scope

Endpoint wymaga aktywnego `organization_id`. Backend sprawdza, że płatnik należy do tej organizacji. Jeśli wpis dotyczy wpłaty, wpłata też musi należeć do tej samej organizacji.

Cross-organization POST ma zostać odrzucony i nie może utworzyć wpisu w złej organizacji.

Audit systemowy `billing_contact_event_added` zapisuje tylko metadane: id wpisu, płatnika, powiązaną wpłatę, kanał, typ wpisu oraz długości treści. Pełne `message_text` i `note_text` nie trafiają do details zdarzenia systemowego.

## UI

Sekcja `Kontakt rozliczeniowy` jest widoczna na `/rozliczenia/platnicy/{payerId}`.

UI pokazuje jasno:

> CASI Workspace nie wysyła tej wiadomości. Skopiuj treść i wyślij ją samodzielnie wybranym kanałem.

Dostępne są tylko:

- wybór kanału,
- wybór typu wpisu,
- robocza treść do skopiowania,
- wewnętrzna notatka,
- zapis wpisu kontaktowego,
- lista ostatnich kontaktów.

`/rozliczenia/sprawy` ma link `Przygotuj kontakt`, który prowadzi do szczegółu płatnika. Nie tworzy automatycznej akcji i nie wysyła wiadomości.

## Czego ten etap nie robi

Ten etap nie dodaje:

- wysyłki SMS,
- wysyłki e-mail,
- integracji Gmail,
- integracji SMS,
- automatycznych przypomnień,
- AI/LLM,
- naliczania opłat,
- importu przelewów,
- dopasowywania wpłat,
- korekt,
- księgowania,
- zmiany salda,
- zmiany statusu płatności.

## Następny bezpieczny krok

Po live-weryfikacji można rozważyć osobny widok `/rozliczenia/kontakty` jako read-only dziennik kontaktów. Nie powinien powstać przed potwierdzeniem, że lista kontaktów przy płatniku jest użyteczna i bezpieczna.

## Centrum kontaktow rozliczeniowych

Po etapie zapisu kontaktu dodano read-only widok `/rozliczenia/kontakty`. To centrum przegladu istniejacych wpisow kontaktowych w aktywnej organizacji. Ekran nie wysyla wiadomosci, nie tworzy przypomnien i nie zmienia finansow. Pokazuje przygotowane tresci, zapisane kontakty, deklaracje platnosci oraz wpisy wymagajace ponowienia kontaktu.
