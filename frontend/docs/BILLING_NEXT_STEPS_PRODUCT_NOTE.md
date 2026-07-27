# Plan następnego kroku rozliczeniowego — planned i completed v1

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
- UI pozwala oznaczyć aktywny krok przy sprawie albo płatniku jako wykonany.
- Zakończenie dopisuje osobny event `completed` z `parent_event_id` wskazującym konkretny `planned`; nie edytuje ani nie usuwa wcześniejszego wpisu.
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
- Event audytowy zapisuje metadane, `parent_event_id` i długości tekstów, nie pełne `note_text`.
- Dozwolony zapis obejmuje wyłącznie `billing_next_step_events` oraz sanitarny wpis w `event_logs`.
- Akcja nie zmienia `billing_transactions`, `billing_charges`, `billing_payment_matches`, `billing_payer_ledger_entries` ani sald.

## UI

`/rozliczenia/sprawy`:

- formularz `Dodaj następny krok`,
- sekcja `Następne kroki`,
- sekcja `Ostatnio wykonane kroki`.
- aktywny krok ma pojedynczą akcję `Oznacz jako wykonany` z blokadą ponownego wysłania podczas zapisu.

`/rozliczenia/platnicy/{payerId}`:

- sekcja `Następny krok`,
- aktywne kroki płatnika,
- formularz dodania kroku,
- akcja `Oznacz jako wykonany` przy aktywnym kroku,
- copy: `Ten krok nie zmienia salda, wpłat ani naliczeń. Nie tworzy automatycznego przypomnienia.`

`/rozliczenia/wplaty/{paymentId}`:

- mała read-only sekcja aktywnych kroków powiązanych z wpłatą.
- brak przycisku zakończenia i innych write actions.

## Bieżący stan kroku

Historia pozostaje append-only. Każdy nowy `completed` musi wskazywać dokładnie jeden wcześniejszy `planned` przez `parent_event_id`. Frontend uznaje `planned` za zakończony wyłącznie wtedy, gdy istnieje event `completed` wskazujący jego ID.

Nie wolno wnioskować relacji na podstawie celu, typu, tytułu, notatki ani `planned_for`. Dwa identyczne kroki pozostają osobnymi historiami. Starsze eventy `completed` bez `parent_event_id` są pokazywane wyłącznie jako historyczne, niepowiązane wpisy i nie zamykają automatycznie żadnego `planned`.

Backend wymaga rodzica z tej samej organizacji i tego samego celu, odrzuca rodzica innego niż `planned` oraz drugie zakończenie tego samego eventu. Unikalny indeks na `parent_event_id` zabezpiecza także równoczesną próbę podwójnego zakończenia.

Ten etap nie dodaje `snoozed` do UI i nie wprowadza dziedziczenia `work_queue_issue → payment`.

Nie dodano `/rozliczenia/kroki`. Zbiorczy widok kroków może być osobnym etapem, jeśli workflow będzie używany wystarczająco często.

## Następny bezpieczny krok

Po live-weryfikacji `completed` warto osobno rozważyć `snoozed` w UI albo read-only widok zbiorczy `/rozliczenia/kroki`. Nie należy jeszcze dodawać kalendarza, przypomnień, wysyłki wiadomości ani automatyzacji.
