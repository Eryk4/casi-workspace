# Plan następnego kroku rozliczeniowego — write v1

Trasy:

- `/rozliczenia/sprawy`
- `/rozliczenia/platnicy/{payerId}`
- `/rozliczenia/wplaty/{paymentId}` jako mała lista read-only aktywnych kroków

## Cel

`Następny krok` to ręczny plan pracy operatora przy rozliczeniach. Ma odpowiedzieć na pytanie: co człowiek chce zrobić dalej przy płatniku, wpłacie albo sprawie rozliczeniowej.

Przykłady:

- zadzwonić do płatnika,
- sprawdzić, czy wpłata przyszła,
- poczekać na odpowiedź,
- wyjaśnić, którego ucznia dotyczy wpłata,
- sprawdzić nadpłatę przed kolejnym okresem.

## Zakres v1

- Nowa tabela `billing_next_step_events`.
- Endpoint `GET /api/billing/next-step-events?organization_id=...`.
- Endpoint `POST /api/billing/next-step-events?organization_id=...`.
- Model append-only: każdy wpis jest osobnym eventem.
- UI pozwala dodać krok przy sprawie rozliczeniowej i przy płatniku.
- Szczegół wpłaty pokazuje aktywne kroki powiązane z wpłatą.

## Czego ten etap nie robi

- Nie dodaje płatności.
- Nie importuje przelewów.
- Nie dopasowuje wpłat.
- Nie zmienia salda.
- Nie zmienia naliczeń.
- Nie księguje.
- Nie rozlicza nadpłat.
- Nie wysyła SMS ani e-maila.
- Nie tworzy automatycznego przypomnienia.
- Nie tworzy wpisu w kalendarzu.
- Nie jest AI ani automatyzacją.

Pole `planned_for` jest tylko informacją dla człowieka. Nie uruchamia harmonogramu, kalendarza ani przypomnienia.

## Bezpieczeństwo i izolacja

- Każdy request wymaga `organization_id`.
- Backend waliduje scope organizacji dla płatnika, wpłaty i kontaktu.
- Cross-org POST dla płatnika lub wpłaty z innej organizacji jest odrzucany.
- Cross-org GET zwraca tylko kroki aktywnej organizacji.
- Event audytowy zapisuje metadane i długości tekstów, nie pełne `note_text`.
- Akcja nie zmienia `billing_transactions`, `billing_charges`, `billing_payment_matches`, `billing_payer_ledger_entries` ani sald.

## UI

`/rozliczenia/sprawy`:

- formularz `Dodaj następny krok`,
- sekcja `Następne kroki`,
- sekcja `Ostatnio wykonane kroki`.

`/rozliczenia/platnicy/{payerId}`:

- sekcja `Następny krok`,
- aktywne kroki płatnika,
- formularz dodania kroku,
- copy: `Ten krok nie zmienia salda, wpłat ani naliczeń. Nie tworzy automatycznego przypomnienia.`

`/rozliczenia/wplaty/{paymentId}`:

- mała read-only sekcja aktywnych kroków powiązanych z wpłatą.

Nie dodano `/rozliczenia/kroki`. Zbiorczy widok kroków może być osobnym etapem, jeśli workflow będzie używany wystarczająco często.

## Następny bezpieczny krok

Po live-weryfikacji warto rozważyć append-only eventy `completed` i `snoozed` w UI albo osobny read-only widok zbiorczy `/rozliczenia/kroki`. Nie należy jeszcze dodawać kalendarza, przypomnień, wysyłki wiadomości ani automatyzacji.
