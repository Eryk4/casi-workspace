# Role użytkowników

## Proponowane role

### 1. Właściciel systemu
- Ma pełny dostęp do całego systemu.
- Widzi wszystkie organizacje i wszystkie dane.
- Zarządza organizacjami, użytkownikami, integracjami i ustawieniami globalnymi.

### 2. Administrator organizacji
- Ma pełny dostęp, ale tylko do swojej organizacji.
- Zarządza użytkownikami swojej organizacji.
- Ustawia kanał Telegram i inne ustawienia organizacji.

### 3. Koordynator
- Prowadzi pracę operacyjną w organizacji.
- Zarządza obiegiem faktur i zadań.
- Nie zarządza użytkownikami ani ustawieniami organizacji.

### 4. Operator
- Wykonuje codzienną pracę operacyjną.
- Dodaje i edytuje dane robocze.
- Może współdzielić zadania w obrębie swojej organizacji.
- Nie zarządza użytkownikami, organizacją ani integracjami.

### 5. Gość
- Ma wyłącznie podgląd danych, bez możliwości wprowadzania zmian.

## Macierz uprawnień

| Obszar / akcja | Właściciel systemu | Administrator organizacji | Koordynator | Operator | Gość |
|---|---|---|---|---|---|
| Widok wszystkich organizacji | tak | nie | nie | nie | nie |
| Widok swojej organizacji | tak | tak | tak | tak | tak |
| Tworzenie organizacji | tak | nie | nie | nie | nie |
| Edycja organizacji | tak | tylko swojej | nie | nie | nie |
| Dezaktywacja organizacji | tak | nie | nie | nie | nie |
| Tworzenie użytkowników | tak | tylko w swojej | nie | nie | nie |
| Edycja użytkowników | tak | tylko w swojej | nie | nie | nie |
| Reset / zmiana hasła użytkownika | tak | tylko w swojej | nie | nie | nie |
| Przypisanie `ID użytkownika Telegram` | tak | tylko w swojej | nie | nie | nie |
| Ustawienie `ID kanału Telegram` organizacji | tak | tylko w swojej | nie | nie | nie |
| Widok faktur | tak | tak | tak | tak | tak |
| Edycja danych faktury | tak | tak | tak | tak | nie |
| Zmiana statusu faktury | tak | tak | tak | tak | nie |
| Potwierdzenie duplikatu | tak | tak | tak | nie | nie |
| Oznaczenie faktury jako poprawnej | tak | tak | tak | nie | nie |
| Podgląd OCR i plików | tak | tak | tak | tak | tak |
| Widok kontrahentów | tak | tak | tak | tak | tak |
| Edycja kontrahentów | tak | tak | tak | tak | nie |
| Widok historii systemu | tak | tak | tak | tak | tak |
| Widok zadań | tak | tak | tak | tak | tak |
| Tworzenie i edycja zadań | tak | tak | tak | tak | nie |
| Rozdzielanie zadań innym osobom | tak | tak | tak | tak | nie |
| Zarządzanie integracjami | tak | tylko w swojej | nie | nie | nie |
| Dostęp do ustawień globalnych | tak | nie | nie | nie | nie |

## Rekomendacja praktyczna

- `Właściciel systemu`:
  dla Ciebie i ewentualnie Twojego wewnętrznego zespołu.
- `Administrator organizacji`:
  dla osoby zarządzającej po stronie klienta.
- `Koordynator`:
  dla osoby, która pilnuje procesu i podejmuje decyzje operacyjne.
- `Operator`:
  dla osób, które wprowadzają i obrabiają dokumenty.
- `Gość`:
  dla osób, które mają tylko wgląd.

## Najważniejsze założenie

- `Właściciel systemu` nie powinien być traktowany tak samo jak klientowy administrator.
- `Administrator organizacji` ma silne uprawnienia, ale tylko w obrębie swojej organizacji.
- `Koordynator` ma wpływ na proces, ale nie na strukturę systemu.
- `Operator` pracuje na danych, ale nie zarządza ludźmi ani konfiguracją.
- `Gość` niczego nie zmienia.
