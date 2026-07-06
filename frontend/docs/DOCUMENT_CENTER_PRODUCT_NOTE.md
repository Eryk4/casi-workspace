# Centrum dokumentu v1

`/dokumenty/[documentId]` jest produktowym ekranem v1 dla kontekstu dokumentu w aktywnym froncie Next.

## Pytanie Produktowe

Ekran odpowiada na pytanie: co to za dokument, do czego służy i z czym jest powiązany?

Nie jest to ekran zarządzania plikami ani workflow dokumentowego. Celem v1 jest bezpieczne zrozumienie kontekstu dokumentu bez wykonywania akcji zapisu.

## Dane

Ekran korzysta z istniejących read-only źródeł:

- `GET /api/knowledge/documents/{id}?organization_id=...` dla profilu dokumentu, wersji, komentarzy, aktywności i bezpiecznego skrótu treści.
- `GET /api/work-items?organization_id=...` dla wyprowadzenia powiązanych spraw, faktur i kontrahentów z metadanych istniejących Work Items.

Nie dodano nowego endpointu backendowego. Jeżeli w przyszłości relacje dokumentu staną się bogatsze albo koszt agregacji po stronie frontendu będzie zbyt duży, naturalnym następnym krokiem jest mały read-only endpoint kontekstowy, np. `GET /api/knowledge/documents/{id}/context?organization_id=...`.

## Sekcje Ekranu

- `Profil dokumentu`: status, przetwarzanie, powiązania, podstawowe metadane i powód uwagi.
- `Źródło i ślad dokumentu`: bezpieczny opis źródła, przetwarzania, pliku i skrótu treści.
- `Powiązane sprawy`: linki do `/work-items/{id}`, jeśli obecne dane wspierają relację.
- `Powiązane faktury`: linki do `/faktury/{id}`, jeśli relacja wynika z powiązanych spraw.
- `Powiązani kontrahenci`: linki do `/crm/{id}`, jeśli relacja wynika z powiązanych spraw albo faktur.
- `Wersje dokumentu`: lista wersji bez akcji restore ani mark official.
- `Komentarze i adnotacje`: istniejące komentarze dokumentu tylko do odczytu.
- `Aktywność dokumentu`: historia bez technicznych szczegółów.
- `Kontekst biznesowy`: krótkie wyjaśnienie, do czego dokument służy i co warto sprawdzić dalej.

## Świadomie Niedodane

W v1 nie dodano:

- uploadu,
- replace,
- edycji dokumentu,
- usuwania,
- restore version,
- mark official,
- bulk actions,
- OCR action,
- workflow dokumentowego,
- nowego formularza komentarza,
- AI/LLM,
- automatyzacji.

## Bezpieczeństwo

Ekran nie pokazuje lokalnych ścieżek, surowych kluczy plików, `data/magazyn`, `C:\Users`, tokenów, sekretów, connection stringów ani technicznych payloadów.

Plik i źródło są prezentowane jako bezpieczny ślad operacyjny, nie jako link do prywatnego storage.

## Ograniczenia v1

- Relacje z fakturami i kontrahentami są wyprowadzane z istniejących Work Items, więc mogą być puste mimo tego, że dokument ma biznesowe znaczenie.
- Faktury powiązane tylko przez intake bez `knowledge_document_id` nie są sztucznie linkowane.
- Brak nowego endpointu kontekstowego oznacza, że frontend wykonuje dodatkowy read-only request po Work Items.
- Ekran jest celowo read-only i nie zastępuje przyszłego workflow dokumentowego.

## Przed Użyciem Operacyjnym

Przed realnym użyciem operacyjnym trzeba doprecyzować:

- pełny model relacji dokument → faktura → kontrahent,
- politykę komentarzy/adnotacji dokumentowych,
- zasady podglądu i pobierania plików,
- uprawnienia do uploadu, replace, restore i mark official,
- audyt bezpieczeństwa storage i OCR.
