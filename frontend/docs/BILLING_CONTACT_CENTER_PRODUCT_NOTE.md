# Centrum kontaktow rozliczeniowych v1

Trasa: `/rozliczenia/kontakty`.

Ten etap dodaje read-only centrum kontaktow rozliczeniowych dla wybranej organizacji. Ekran zbiera istniejace wpisy kontaktowe zapisane przy platnikach i pomaga operatorowi zobaczyc, co bylo przygotowane, odnotowane albo wymaga ponownego sprawdzenia.

## Co pokazuje ekran

- podsumowanie wszystkich kontaktow w organizacji,
- przygotowane tresci do recznego uzycia poza CASI,
- deklaracje platnosci,
- kontakty bez odpowiedzi,
- wpisy wymagajace ponownego kontaktu,
- historie kontaktow z filtrowaniem po kanale, typie wpisu i platniku,
- linki do szczegolu platnika, szczegolu wplaty i spraw rozliczeniowych.

## Zakres read-only

Ekran nie wysyla SMS, e-maili ani przypomnien. Nie dodaje platnosci, nie dopasowuje wplat, nie zmienia sald, nie zmienia naliczen i nie tworzy automatyzacji. Jedyne dozwolone elementy interaktywne to odswiezenie danych, filtry lokalne i linki do istniejacych tras.

## Zrodlo danych

Widok korzysta z istniejacego endpointu:

`GET /api/billing/contact-events?organization_id=...`

Dane sa zawsze pobierane w scope aktywnej organizacji. Przy zmianie organizacji frontend czysci poprzedni snapshot, zeby nie pokazac kontaktow z poprzedniego tenant scope.

## Ograniczenia

- przygotowana tresc nie oznacza, ze CASI wyslal wiadomosc,
- deklaracja platnosci nie oznacza dodania wplaty,
- wpis `brak odpowiedzi` albo `wymaga ponownego kontaktu` nie tworzy automatycznego przypomnienia,
- ekran nie jest jeszcze systemem kampanii, windykacji ani obslugi wysylek.

## Warunki przed kolejnymi etapami

Kolejne kroki, takie jak wysylka wiadomosci, przypomnienia albo automatyzacje kontaktu, wymagaja osobnego kontraktu, uprawnien, limitow, audit trail, tenant-isolation testow i live-weryfikacji.
