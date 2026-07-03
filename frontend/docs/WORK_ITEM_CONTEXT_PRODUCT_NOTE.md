# Karta sprawy - produkt v1

Last checked: 2026-07-03

`Karta sprawy` jest drugim ekranem produktowym v1 w aktywnym froncie Next. To normalny ekran CASI, nie pokazówka. Odpowiada na pytanie:

> O co dokładnie chodzi w tej sprawie i z czym jest powiązana?

## Zakres

Route:

- `/work-items/[workItemId]`

Frontend module:

- `frontend/src/modules/work-items/`

Backend contract used:

- `GET /api/work-items/{id}?organization_id=...`

Nie dodano nowego endpointu backendowego. Ekran korzysta z istniejącego read-only detailu Work Items.

## Co pokazuje ekran

Ekran pokazuje:

- tytuł sprawy,
- opis,
- status,
- priorytet,
- SLA i termin,
- właściciela,
- organizację,
- źródło,
- powód, dlaczego sprawa wymaga uwagi,
- powiązaną fakturę, kontrahenta, dokumenty lub zadania, jeśli istnieją w odpowiedzi API,
- bezpieczną historię systemową.

Jeżeli backend nie zwraca powiązań, ekran pokazuje produktowe stany puste. Nie pokazuje technicznych braków ani surowych danych.

## Linki

Wejścia do karty:

- tytuł sprawy na liście `/work-items`,
- pozycje Work Items w `/pulpit-dnia`, jeśli mają `work_item_id`.

Linki wychodzące prowadzą tylko do istniejących tras:

- `/faktury/{id}`,
- `/crm/{id}`,
- `/dokumenty/{id}`,
- `/asystent-szefa`,
- `/work-items`.

## Read-only contract

Karta sprawy jest w pełni read-only.

Dozwolone:

- odświeżenie widoku,
- powrót do listy,
- linki do istniejących modułów.

Niedozwolone na tym ekranie:

- przypisz,
- odłóż,
- zamknij,
- edytuj,
- usuń,
- skomentuj,
- zmień status,
- akcje bulk,
- automatyzacje,
- AI/LLM.

Istniejące akcje Work Items pozostają na liście `/work-items` i nie zostały rozszerzone przez ten krok.

## Organizacja i bezpieczeństwo danych

Ekran wymaga aktywnej organizacji.

Bez aktywnej organizacji pokazuje:

- `Wybierz organizację, aby zobaczyć kartę sprawy`

Frontend nie pobiera szczegółu sprawy bez `organization_id`.

Ekran nie może pokazywać:

- `storage_key`,
- `data/magazyn`,
- `C:\Users`,
- tokenów,
- sekretów,
- connection stringów,
- raw JSON,
- technicznych payloadów.

Historia systemowa jest mapowana na bezpieczne etykiety i opis. Surowe `details` z backendu nie są renderowane.

## Lokalny sandbox danych

Lokalny sandbox danych zawiera teraz realistyczne Work Items dla organizacji CASI i Misja Robotyka, żeby dało się sprawdzić pozytywny scenariusz `/work-items/{workItemId}` bez ręcznego tworzenia spraw.

Seed tworzy sprawy przez istniejący `WorkItemService`, nie przez ręczny SQL. Dzięki temu zachowane są:

- obecny schemat `work_items`,
- historia `work_item_history`,
- zakres organizacji,
- metadane powiązań do faktur, kontrahentów i dokumentów, jeśli takie rekordy istnieją w sandboxie.

To są bezpieczne dane robocze lokalnego sandboxu. Nie są produkcyjnymi danymi klienta i nie zmieniają kontraktu aplikacji.

## Ograniczenia v1

Obecny endpoint Work Items zwraca podstawowe dane sprawy, historię oraz `metadata`. Nie wykonuje pełnego joinu do faktur, CRM i dokumentów.

Dlatego:

- jeśli `source_type`, `source_id` albo `metadata` pozwalają zidentyfikować powiązanie, ekran pokazuje link do modułu docelowego,
- jeśli pełnych danych powiązania nie ma, ekran pokazuje czytelny empty state,
- nie dodano agregującego endpointu kontekstu sprawy.

Jeżeli dalsze użycie pokaże, że karta sprawy wymaga bogatszego kontekstu, osobnym krokiem warto rozważyć read-only endpoint, np.:

- `GET /api/work-items/{id}/context?organization_id=...`

Taki endpoint powinien zwracać tylko bezpieczne pola biznesowe i nie zmieniać workflow.

## Testy

Covered by:

- `frontend/scripts/test-work-item-detail.js`
- `frontend/scripts/test-work-items.js`
- `frontend/scripts/test-daily-brief.js`
- `frontend/scripts/test-all.js`
- `python run_quality_checks.py --profile frontend-smoke`

Test modelowy sprawdza mapowanie headera, relacje, historię, brak organizacji, brak akcji zapisu, brak pól technicznych i poprawne linki.
