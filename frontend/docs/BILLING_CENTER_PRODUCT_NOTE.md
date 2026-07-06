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
- `GET /api/invoices?organization_id=...`,
- `GET /api/contractors?organization_id=...`,
- `GET /api/work-items?organization_id=...&only_open=1&limit=100`.

Nie dodano nowego endpointu agregującego. Jeśli agregacja po stronie frontendu stanie się zbyt ciężka albo dane relacyjne będą zbyt płytkie, następnym krokiem powinien być osobny, read-only kontrakt backendowy dla centrum rozliczeń.

## Zakres v1

Ekran jest w pełni read-only. Dozwolone są tylko:

- odświeżenie danych,
- linki do istniejących modułów: Faktury, CRM, Work Items i Pulpit dnia.

W obecnym zakresie ekran pokazuje też fundament `Rodziny, uczniowie i płatnicy`. Jest to warstwa read-only oparta o istniejące dane `billing_payers` i `billing_students`: kto jest płatnikiem, za których uczniów odpowiada, czy występuje rodzeństwo oraz czy klient jest rodziną ucznia czy klientem firmowym.

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
- nie prowadzi pełnego salda klienta, ucznia ani rodziny,
- nie generuje należności,
- nie dopasowuje przelewów,
- nie importuje wyciągów bankowych,
- nie dodaje ręcznych płatności,
- nie obsługuje płatności częściowych jako workflow,
- nie przenosi nadpłat między okresami,
- nie wysyła przypomnień,
- nie zastępuje księgowości,
- nie wykonuje operacji finansowych ani eksportów.

## Przed realnym użyciem operacyjnym

Przed traktowaniem widoku jako źródła decyzji finansowych potrzebne są:

- live-weryfikacja na lokalnym sandboxie danych dla minimum dwóch organizacji,
- przegląd, czy salda ledgeru są kompletne i aktualne,
- decyzja, czy kolejny krok ma być read-only wyjaśnieniem naliczeń i sald, czy osobną migracją docelowych encji rodzin/płatników/uczniów,
- decyzja, czy centrum rozliczeń potrzebuje dedykowanego read-only endpointu,
- osobny audyt przed jakąkolwiek akcją zapisu w rozliczeniach.
