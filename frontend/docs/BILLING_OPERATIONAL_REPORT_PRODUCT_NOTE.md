# Raport rozliczeniowy — read-only v1

Trasa: `/rozliczenia/raport`

`Raport rozliczeniowy` jest operacyjnym, read-only podsumowaniem stanu rozliczeń wybranej organizacji. Ma dać właścicielowi firmy jedno miejsce do sprawdzenia zaległości, nadpłat, wpłat wymagających wyjaśnienia, spraw rozliczeniowych i kontaktów z płatnikami.

## Co pokazuje

- sumę zaległości i liczbę płatników z zaległością,
- sumę nadpłat i liczbę płatników z nadpłatą,
- wpłaty przypisane do naliczeń, tylko do płatnika albo wymagające wyjaśnienia,
- aktywne, odłożone i obsłużone sprawy rozliczeniowe,
- kontakty wymagające ponownego działania,
- listę `Najważniejsze do sprawdzenia`,
- tekstowy `Raport do skopiowania` do ręcznego użycia w notatkach.

## Zakres bezpieczeństwa

Raport nie jest dokumentem księgowym. Nie zmienia danych, nie zmienia sald, nie przypisuje wpłat, nie rozstrzyga nadpłat i nie generuje plików. CASI Workspace nie wysyła tego raportu.

Dozwolone są tylko:

- odświeżenie danych,
- linki do istniejących ekranów rozliczeń,
- ręczne zaznaczenie i skopiowanie tekstu raportu.

## Źródła danych

Widok korzysta z istniejących read-only danych organizacji:

- salda płatników,
- płatnicy i osoby objęte rozliczeniem,
- naliczenia,
- transakcje i widoczne przypisania wpłat,
- statusy operacyjne wpłat,
- sprawy rozliczeniowe,
- kontakty rozliczeniowe.

Nie dodano backendu, endpointu agregującego, migracji ani seedów.

## Ograniczenia

Raport pokazuje aktualny stan danych organizacji. Nie filtruje jeszcze po okresie, bo obecny model okresów nie wystarcza do uczciwego raportu okresowego dla wszystkich wpłat. Okresy są pokazywane jako kontekst tam, gdzie wynikają z naliczeń lub bezpiecznych przypisań.

Przyszłe PDF, XLSX, wysyłka wiadomości albo oficjalny eksport księgowy mogą być osobnymi etapami po audycie kontraktu, uprawnień, zakresu danych i tenant isolation. Nie są częścią tej wersji.
