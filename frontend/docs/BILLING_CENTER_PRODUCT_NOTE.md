# Centrum rozliczeń v1

`/rozliczenia` jest kanonicznym ekranem produktu dla obszaru pieniędzy, płatności i zaległości. `/kasa` nie jest osobnym modułem produktu; pozostaje tylko legacy redirectem do `/rozliczenia`.

## Cel ekranu

Centrum rozliczeń ma odpowiedzieć właścicielowi firmy na pytanie: „jak wygląda sytuacja pieniędzy, płatności i zaległości?”. Widok jest szybkim, porannym przeglądem finansowym, a nie pełnym systemem księgowym.

Ekran pokazuje:

- ogólną sytuację sald i należności,
- pozycje wymagające uwagi,
- faktury w kontekście płatności,
- kontrahentów powiązanych z rozliczeniami,
- sprawy operacyjne, które mogą wpływać na płatności,
- ostatnie wpłaty widoczne w rozliczeniach,
- krótki kontekst biznesowy.

## Źródła danych

Wersja v1 korzysta wyłącznie z istniejących read-only endpointów organizacyjnych:

- `GET /api/billing/ledger/balances?organization_id=...`,
- `GET /api/billing/payers?organization_id=...`,
- `GET /api/billing/students?organization_id=...`,
- `GET /api/billing/charges?organization_id=...`,
- `GET /api/invoices?organization_id=...`,
- `GET /api/contractors?organization_id=...`,
- `GET /api/work-items?organization_id=...&only_open=1&limit=100`.

Nie dodano nowego endpointu agregującego. Jeśli agregacja po stronie frontendu stanie się zbyt ciężka albo dane relacyjne będą zbyt płytkie, następnym krokiem powinien być osobny, read-only kontrakt backendowy dla centrum rozliczeń.

## Zakres v1

Ekran jest w pełni read-only. Dozwolone są tylko:

- odświeżenie danych,
- linki do istniejących modułów: Faktury, CRM, Work Items i Pulpit dnia.

W obecnym zakresie ekran pokazuje też fundament `Rodziny, uczniowie i płatnicy`. Jest to warstwa read-only oparta o istniejące dane `billing_payers` i `billing_students`: kto jest płatnikiem, za których uczniów odpowiada, czy występuje rodzeństwo oraz czy klient jest rodziną ucznia czy klientem firmowym.

Etap `Read-only wyjaśnienie naliczeń i sald` dodaje sekcję `Skąd wynika saldo`. Sekcja pokazuje naliczone kwoty, widoczne wpłaty, różnicę, nadpłatę albo dopłatę oraz kilka najważniejszych pozycji wpływających na saldo. To nadal jest wyjaśnienie informacyjne, a nie pełny silnik naliczeń, księgowanie ani workflow płatności.

Etap `Szczegół płatnika — read-only v1` dodaje trasę `/rozliczenia/platnicy/{payerId}`. Widok rozwija dane jednego płatnika: osoby objęte rozliczeniem, usługi, naliczenia, ostatnią widoczną wpłatę oraz powiązane faktury i sprawy, bez dodawania akcji finansowych.

Etap `Usługi i zapisy — read-only foundation` dodaje sekcję `Usługi i zapisy`. Usługi są widoczne przez naliczenia, modele rozliczeń i faktury, bez pełnego modelu kontraktów, zapisów ani cenników. Ekran pokazuje nazwę usługi, typ, płatnika, osobę objętą rozliczeniem, okres, status i źródło danych. Część danych jest wywnioskowana z naliczeń, co jest jawnie oznaczone w UI.

Etap `Okres rozliczeniowy — read-only v1` dodaje trasę `/rozliczenia/okresy`. Widok odpowiada na pytanie, jak wygląda rozliczenie za konkretny okres: którzy płatnicy mają dopłatę, nadpłatę albo rozliczony okres, jakie usługi zostały naliczone i które pozycje wymagają uwagi. Okresy są wywnioskowane z obecnych naliczeń i dopasowanych wpłat, bez dodawania pełnego obiektu okresu rozliczeniowego.

Widok okresu nie przypisuje globalnych wpłat płatnika do okresu, jeśli nie ma relacji z konkretnym naliczeniem. Dzięki temu ekran nie udaje nadpłaty ani rozliczenia okresu bez danych. Pełne przypisywanie wpłat do okresów wymaga osobnego modelu alokacji płatności.

Etap `Wpłaty i przypisania — read-only foundation` dodaje trasę `/rozliczenia/wplaty`. Widok pokazuje istniejące wpłaty, ich obecne przypisanie do naliczenia, przypisanie tylko do płatnika albo brak jasnego przypisania. Nadal nie importuje przelewów, nie zmienia dopasowań, nie księguje i nie wykonuje operacji finansowych.

Ekran nie wykonuje:

- importu wyciągów,
- dopasowywania wpłat,
- generowania naliczeń,
- księgowania,
- eksportu,
- edycji płatników,
- żadnych write actions.

## Ograniczenia

- Salda płatników pochodzą z istniejącego ledgeru i nie zastępują pełnej księgowości.
- Rodziny i uczniowie są pokazani przez kompatybilny model nad istniejącymi tabelami, bez nowych tras szczegółu i bez edycji relacji.
- Usługi i zapisy są w tej wersji odczytywane z istniejących modeli, naliczeń i faktur. To nie jest jeszcze pełny model umów, zapisów, cenników ani zmian statusów.
- Okresy rozliczeniowe są w tej wersji wywnioskowane z `period_label` w naliczeniach. To nie jest jeszcze pełny model zamykania okresu, przenoszenia nadpłat ani rozliczeń międzyokresowych.
- Wpłaty bez relacji z konkretnym naliczeniem pozostają informacją przy płatniku, ale nie są zaliczane jako wpłata danego okresu.
- Wyjaśnienie salda korzysta z istniejących naliczeń i sald. Jeśli brakuje szczegółowych naliczeń, ekran pokazuje bezpieczny empty state zamiast udawać pełną dokładność księgową.
- Powiązania faktur, kontrahentów i spraw są budowane deterministycznie z dostępnych danych. Nie używają AI ani ukrytej automatyzacji.
- Historia pokazuje tylko bezpieczne, wysokopoziomowe informacje o ostatnich wpłatach. Nie pokazuje technicznych szczegółów bankowych, storage keys ani payloadów.
- `/kasa` nie powinno być używane w nowych linkach, dokumentacji produktowej ani nawigacji.

## Docelowy zakres pełnego modułu rozliczeń

Docelowo `Rozliczenia` powinny obsługiwać pełny obszar klientów, uczniów, rodzin i płatników. V1 jest fundamentem informacyjnym, ale nie zamyka tego zakresu.

Pełny projekt domeny jest opisany w `docs/FULL_CLIENT_BILLING_DOMAIN_PLAN.md`. Ten dokument należy traktować jako kierunek dla przyszłych etapów, a nie jako zakres wdrożony w `Centrum rozliczeń v1`.

Przyszły pełny moduł powinien uwzględnić:

- uczniów, klientów firmowych i beneficjentów usług,
- rodziców i płatników,
- rodziny jako grupy rozliczeniowe,
- rodzeństwo oraz kilka dzieci pod jednym płatnikiem,
- możliwość kilku płatników dla jednego ucznia, jeśli produktowo będzie to potrzebne,
- usługi i zapisy: zajęcia cykliczne, kursy, półkolonie, warsztaty, abonamenty i usługi jednorazowe,
- cenniki, indywidualne ceny, korekty cen i zniżki, w tym zniżki za rodzeństwo albo kolejny rok,
- naliczenia miesięczne, semestralne, roczne i proporcjonalne,
- należności, nadpłaty, zaległości oraz historię zmian salda,
- płatności częściowe, pomyłki w kwotach i nieznane przelewy,
- import przelewów i kontrolowane dopasowanie płatności,
- powiązania z fakturami sprzedażowymi, kosztowymi i eksportem księgowym,
- przypomnienia i miękką windykację pod kontrolą człowieka,
- raporty właściciela: przychody, zaległości, nadpłaty, płynność i ryzyka finansowe,
- eksport księgowy po osobnym audycie kontraktu i uprawnień.

## Czego v1 jeszcze nie robi

`Centrum rozliczeń v1` nie powinno sugerować, że pełny moduł jest już gotowy. W obecnym zakresie ekran:

- nie nalicza opłat uczniom,
- pokazuje rodziny, uczniów, płatników i rodzeństwo tylko w trybie read-only,
- pokazuje usługi i zapisy tylko jako read-only fundament wywnioskowany z obecnych danych,
- pokazuje okresy rozliczeniowe tylko jako read-only widok wywnioskowany z obecnych naliczeń i dopasowanych wpłat,
- pokazuje wpłaty i przypisania tylko jako read-only kontrolę istniejących danych,
- wyjaśnia saldo tylko na podstawie obecnych danych read-only,
- nie prowadzi pełnego modelu usług, zapisów, umów ani cenników,
- nie prowadzi pełnego docelowego salda klienta, ucznia ani rodziny,
- nie generuje należności,
- nie dopasowuje przelewów,
- nie importuje wyciągów bankowych,
- nie dodaje ręcznych płatności,
- nie obsługuje płatności częściowych jako workflow,
- nie przenosi nadpłat między okresami,
- nie zamyka okresów rozliczeniowych,
- nie wysyła przypomnień,
- nie zastępuje księgowości,
- nie wykonuje operacji finansowych ani eksportów.

## Przed realnym użyciem operacyjnym

Przed traktowaniem widoku jako źródła decyzji finansowych potrzebne są:

- live-weryfikacja na lokalnym sandboxie danych dla minimum dwóch organizacji,
- przegląd, czy salda ledgeru są kompletne i aktualne,
- decyzja, czy kolejny krok ma być osobnym read-only widokiem naliczeń, czy dedykowanym agregatem backendowym dla rozliczeń,
- decyzja, czy centrum rozliczeń potrzebuje dedykowanego read-only endpointu,
- osobny audyt przed jakąkolwiek akcją zapisu w rozliczeniach.

Etap `Szczegół wpłaty — read-only v1` dodaje trasę `/rozliczenia/wplaty/{paymentId}`. Widok korzysta z istniejących transakcji, matchy, naliczeń, płatników i uczniów. Nie dodaje backendu, nie wykonuje dopasowania, nie księguje i nie zmienia salda. Pełne przypisywanie wpłat pozostaje osobnym etapem przed importami i automatyzacją.
