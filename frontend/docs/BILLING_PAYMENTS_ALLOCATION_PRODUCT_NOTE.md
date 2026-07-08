# Wpłaty i przypisania v1

`/rozliczenia/wplaty` jest read-only ekranem kontroli widocznych wpłat w module `Rozliczenia`.

Ekran odpowiada na pytania:

- jakie wpłaty są widoczne w wybranej organizacji,
- które wpłaty można bezpiecznie powiązać z konkretnym naliczeniem,
- które wpłaty są widoczne tylko przy płatniku,
- które wpłaty wymagają późniejszego wyjaśnienia,
- dlaczego nie każda wpłata może być uczciwie pokazana w okresie rozliczeniowym.

## Źródła danych

Widok korzysta wyłącznie z istniejących, organizacyjnie scoped źródeł read-only:

- `GET /api/billing/transactions`,
- `GET /api/billing/ledger/matches`,
- `GET /api/billing/charges`,
- `GET /api/billing/payers`,
- `GET /api/billing/students`.

Nie dodano nowego endpointu backendowego, migracji ani tabeli.

## Co pokazuje v1

Ekran rozdziela wpłaty na trzy grupy:

- `Wpłaty przypisane do naliczeń` - mają relację z konkretnym naliczeniem, więc mogą być pokazane przy okresie.
- `Wpłaty przypisane tylko do płatnika` - są widoczne przy płatniku, ale nie mają relacji z konkretnym naliczeniem.
- `Wpłaty wymagające wyjaśnienia` - są widoczne jako wpływ, ale nie mają wystarczającego kontekstu do uczciwego przypisania.

To jest fundament informacyjny. Nie jest jeszcze workflow importu przelewów, automatycznego dopasowania ani księgowania.

## Read-only

Ekran jest w pełni read-only. Dozwolone są tylko:

- odświeżenie danych,
- link do centrum rozliczeń,
- link do okresów rozliczeniowych,
- link do szczegółu płatnika, jeśli płatnik jest znany.

Nie ma akcji:

- dodaj wpłatę,
- importuj przelew,
- dopasuj wpłatę,
- zmień przypisanie,
- zaksięguj,
- skoryguj,
- usuń.

## Ograniczenia

- Wpłata trafia do okresu tylko wtedy, gdy istnieje bezpieczna relacja z konkretnym naliczeniem.
- Wpłata widoczna tylko przy płatniku nie jest automatycznie przypisywana do okresu.
- Widok nie przenosi nadpłat między okresami.
- Widok nie rozdziela jednej wpłaty na wiele usług, faktur ani naliczeń poza relacjami już obecnymi w danych.
- Pełne rozliczenie płatności wymaga późniejszego modelu `payment_allocation` albo równoważnego kontraktu przypisania wpłat do naliczeń.

## Następny bezpieczny krok

Po live-weryfikacji `/rozliczenia/wplaty` najbezpieczniejszy kolejny krok to nadal read-only: dopracowanie listy naliczeń albo osobny projekt modelu alokacji płatności. Importy, automatyczne dopasowanie, ręczne przypisywanie i księgowanie wymagają osobnego audytu kontraktu, uprawnień, izolacji organizacyjnej i UX.

## Szczegół wpłaty

Etap `Szczegół wpłaty — read-only v1` dodaje trasę `/rozliczenia/wplaty/{paymentId}`. Lista `/rozliczenia/wplaty` linkuje do szczegółu tylko wtedy, gdy istnieje stabilny identyfikator transakcji. W obecnym modelu `paymentId` oznacza `billing_transaction_id`, ale UI nie pokazuje technicznego ID użytkownikowi.

Szczegół wpłaty nie dopasowuje przelewów, nie księguje i nie zmienia salda. Pokazuje tylko widoczną wpłatę oraz jej obecne przypisanie: do naliczenia, tylko do płatnika albo do późniejszego wyjaśnienia.

Etap `Status operacyjny wpłaty — write v1` dodaje na szczególe wpłaty jedną addytywną adnotację operatora. Status operacyjny nie zmienia przypisania, salda, naliczeń ani historii finansowej; służy tylko do oznaczenia, co trzeba sprawdzić przy widocznej wpłacie.
