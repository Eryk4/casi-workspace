# Modul rozliczen klientow

## Kierunek

Modul ma byc ogolnym modulem do rozliczania klientow organizacji, a nie tylko uczniow za zajecia.

`Uczen` jest tylko jednym z mozliwych typow klienta koncowego.

## Model poziomow

W aplikacji rozdzielamy 3 poziomy:

1. `Wlasciciel platformy / administrator globalny`
2. `Organizacja` - czyli Twoj klient korzystajacy z systemu
3. `Klient organizacji` - czyli klient koncowy tej organizacji

To oznacza:

- Ty zarzadzasz organizacjami
- kazda organizacja widzi tylko swoje dane
- kazda organizacja moze miec wlasna baze klientow do rozliczen
- klient koncowy nie jest organizacja systemowa, tylko rekordem wewnatrz organizacji

## Dlaczego nie uzywac `organizations` jako klientow koncowych

Tabela `organizations` jest granica bezpieczenstwa i separacji danych.

Nie powinna byc uzywana jednoczesnie jako:

- tenant systemu
- klient koncowy do rozliczen

Jesli pomieszamy te dwa poziomy, bardzo szybko powstanie problem z:

- uprawnieniami
- filtrowaniem danych
- raportami
- przyszlym panelem klienta

## Rekomendowany model domeny

Nowy modul powinien miec osobne encje biznesowe w ramach organizacji:

- `billing_customers`
- `billing_services`
- `billing_customer_agreements`
- `billing_periods`
- `billing_entries`
- `billing_documents`
- `billing_payments`

## Znaczenie encji

### `billing_customers`

Klient koncowy organizacji.

Przykladowe pola:

- `billing_customer_id`
- `organization_id`
- `customer_type` - np. `uczen`, `klient_indywidualny`, `firma`, `grupa`
- `full_name`
- `company_name`
- `email`
- `phone`
- `payment_identifier`
- `payment_identifier_type` - np. `telefon`, `kod_klienta`
- `external_code`
- `notes`
- `is_active`
- `created_at`
- `updated_at`

### `billing_services`

Definicje tego, co organizacja sprzedaje lub rozlicza.

Przykladowe pola:

- `billing_service_id`
- `organization_id`
- `name`
- `service_type` - np. `zajecia`, `abonament`, `pakiet`, `konsultacja`, `opieka`
- `unit_type` - np. `miesiac`, `spotkanie`, `godzina`, `pakiet`
- `default_price`
- `currency`
- `is_active`

### `billing_customer_agreements`

Powiazanie klienta z usluga i zasadami rozliczen.

Przykladowe pola:

- `billing_customer_agreement_id`
- `organization_id`
- `billing_customer_id`
- `billing_service_id`
- `billing_model` - `abonament`, `za_wykorzystanie`, `pakiet`, `mieszany`
- `price_amount`
- `billing_cycle` - np. `miesieczny`, `jednorazowy`, `rekordowy`
- `start_date`
- `end_date`
- `status`
- `notes`

### `billing_periods`

Okresy rozliczeniowe, z ktorych liczone sa naleznosci.

Przykladowe pola:

- `billing_period_id`
- `organization_id`
- `period_label`
- `date_from`
- `date_to`
- `status` - np. `otwarty`, `zamkniety`, `rozliczony`

### `billing_entries`

Pozycje naliczen lub zuzyc w danym okresie.

To moze byc np.:

- obecność na zajęciach
- nieobecność płatna
- abonament miesięczny
- dopłata
- rabat
- ręczna korekta

Przykladowe pola:

- `billing_entry_id`
- `organization_id`
- `billing_customer_id`
- `billing_service_id`
- `billing_customer_agreement_id`
- `billing_period_id`
- `entry_type`
- `quantity`
- `unit_price`
- `total_amount`
- `entry_date`
- `description`
- `source`
- `created_by_user_id`

### `billing_documents`

Dokument podsumowujacy rozliczenie klienta za okres.

Na start moze to byc dokument wewnetrzny lub wezwanie do zaplaty, a dopiero pozniej prawdziwa faktura/sprzedaz.

Przykladowe pola:

- `billing_document_id`
- `organization_id`
- `billing_customer_id`
- `billing_period_id`
- `document_number`
- `document_type`
- `status`
- `issue_date`
- `due_date`
- `total_amount`
- `currency`
- `notes`

### `billing_payments`

Ewidencja wplat klienta.

Przykladowe pola:

- `billing_payment_id`
- `organization_id`
- `billing_customer_id`
- `billing_document_id`
- `payment_date`
- `amount`
- `payment_method`
- `reference`
- `notes`

## Relacja z obecnym modulem faktur

Obecny modul `Faktury` obsluguje dokumenty kosztowe i kontrahentow po stronie zakupowej.

Nowy modul powinien obslugiwac strone przychodowa:

- klienci organizacji
- naleznosci
- rozliczenia
- wplaty

Dlatego nie warto mieszac tego z tabela `contractors`.

Najbezpieczniej utrzymac osobne byty:

- `contractors` dla dostawcow / wystawcow faktur kosztowych
- `billing_customers` dla klientow, ktorych organizacja rozlicza

## Rekomendacja dla MVP

Na start warto przyjac taki zakres:

1. baza klientow organizacji
2. definicje uslug
3. przypisanie klienta do uslugi i modelu rozliczen
4. pozycje rozliczeniowe
5. saldo klienta i historia wplat
6. lista naleznosci po organizacji

## Rekomendowane zalozenia startowe

Jesli nie ustalimy inaczej, bezpieczne zalozenia dla MVP sa takie:

- klient koncowy nie ma jeszcze swojego logowania do systemu
- organizacja rozlicza swoich klientow z poziomu panelu operatora
- dokument rozliczeniowy jest na start dokumentem wewnetrznym, nie pelna ksiegowa faktura sprzedazowa
- `uczen` jest tylko typem klienta lub kategoria uslugi, a nie osobnym modulem
- wplaty sa na start pobierane przez import wyciagow bankowych, a nie przez bezposrednie API bankowe
- numer telefonu moze byc uzywany jako `payment_identifier`, jesli to odpowiada realnej pracy organizacji

## Dostep do danych bankowych w MVP

MVP przyjmuje model:

- operator dodaje rachunek bankowy organizacji
- operator importuje wyciag w formacie `CSV`
- system zapisuje transakcje do wspolnej tabeli
- system pomija duplikaty przy ponownym imporcie tych samych pozycji

To daje:

- prostsze wdrozenie
- brak zaleznosci od integratorow open banking
- lepsza kontrole nad dopasowaniem wplat po numerze telefonu i tresci przelewu

## Nowe ustalenia domenowe dla zajec

Pojawil sie wazny przypadek specjalny: w module rozliczen dla zajec `platnikiem` nie jest samo dziecko, tylko `rodzic / opiekun / rodzina`.

To oznacza, ze numer telefonu w tytule przelewu identyfikuje zwykle `platnika`, a nie pojedyncze dziecko.

Jeden numer telefonu moze byc wspolny dla wiecej niz jednego dziecka, np. dla rodzenstwa.

W praktyce oznacza to tez, ze pojedynczy przelew moze pokrywac naraz raty lub semestry dla kilkorga dzieci z tej samej rodziny.

Dlatego model musi rozdzielac:

1. `platnika`
2. `uczestnika / dziecko / beneficjenta uslugi`
3. `umowe`
4. `harmonogram zajec`
5. `naliczenia`
6. `wplaty`

Wplata z wyciagu powinna byc wiec dopasowywana najpierw do `rodziny / platnika`, a dopiero potem rozdzielana na konkretne dzieci i naleznosci.

## Slownik szkol

Poniewaz organizacja pracuje w wielu szkolach, potrzebny jest osobny slownik szkol zamiast wpisywania ich recznie przy kazdym uczniu.

Rekomendowana encja:

- `billing_schools`

Przykladowe pola:

- `billing_school_id`
- `organization_id`
- `full_name`
- `short_name`
- `city`
- `notes`
- `is_active`

Skrot szkoly powinien byc uzywany w tabelach i filtrach, a pelna nazwa w formularzach i dokumentach.

## Rodziny i uczniowie

W praktyce operacyjnej glowny widok powinien byc `po uczniu`, bo to dziecko jest najczesciej punktem odniesienia dla operatora.

Jednoczesnie rozliczenia i wplaty musza byc trzymane `po rodzinie / platniku`, bo:

- jeden numer telefonu identyfikuje cala rodzine
- jedna wplata moze pokrywac kilka dzieci
- znizki typu rodzenstwo i KDR sa liczone na poziomie rodziny

Dlatego potrzebne sa osobne encje:

- `billing_payers`
- `billing_students`

### `billing_payers`

Przykladowe pola:

- `billing_payer_id`
- `organization_id`
- `display_name`
- `contact_phone`
- `payment_identifier`
- `email`
- `notes`
- `is_active`

### `billing_students`

Przykladowe pola:

- `billing_student_id`
- `organization_id`
- `billing_payer_id`
- `billing_school_id`
- `full_name`
- `lesson_day`
- `group_name`
- `notes`
- `is_active`

Na liscie uczniow warto pokazywac takze:

- skrot szkoly
- nazwe modelu rozliczen
- telefon rodziny
- ostatnia wplate rodziny: data i kwota

Ta ostatnia wplata jest wskaznikiem rodzinnym i nie musi oznaczac, ze cala kwota dotyczy tylko jednego dziecka.

## Modele rozliczen

Zamiast ustawiac stawki i zasady osobno przy kazdym uczniu, system powinien miec osobny slownik `billing_models`.

To pozwala raz skonfigurowac na poczatku roku np.:

- `26/27 Poniedzialek`
- `26/27 Wtorek`
- `26/27 Piatek`

Przykladowe pola:

- `billing_model_id`
- `organization_id`
- `name`
- `profile_type`
- `school_year`
- `lesson_day`
- `settlement_mode`
- `monthly_rate_amount`
- `semester_rate_amount`
- `sibling_discount_amount`
- `large_family_discount_amount`
- `intro_free_lessons_count`
- `contract_required`
- `notes`

Uczen moze miec przypisany model rozliczen, ale nie kazdy klient w systemie musi go miec.

## Rekomendowany model rodzinny

W warstwie biznesowej dla zajec rekomendowany jest taki uklad:

- `billing_customers`
- `billing_customer_relations`
- `billing_customer_agreements`
- `billing_schedule_terms`
- `billing_charges`
- `billing_payments`
- `billing_payment_allocations`

### `billing_customers`

Tabela pozostaje ogolna, ale rekord moze pelnic rozne role:

- `payer` - rodzic / opiekun / firma placaca
- `beneficiary` - dziecko lub inny odbiorca uslugi

Przykladowe dodatkowe pola:

- `customer_role`
- `billing_parent_customer_id` - dla powiazania dziecka z platnikiem
- `payment_identifier`
- `payment_identifier_type`

W praktyce dla szkoly robotyki:

- rodzic ma rekord `payer`
- dziecko ma rekord `beneficiary`
- dziecko wskazuje swojego platnika

## Umowa jako zrodlo prawdy

Ze wzgledu na realna praktyke i wystepujace bledy w recznych tabelach, zrodlem prawdy dla naliczen nie powinien byc sam globalny cennik.

Najbezpieczniej przyjac, ze zrodlem prawdy jest:

- podpisana umowa
- jej wybrany wariant platnosci
- harmonogram zajec przypisany do tej umowy
- zestaw ulg i wyjatkow zapisany przy tej umowie

To pozwala obsluzyc sytuacje, w ktorych:

- roznia sie stawki miedzy grupami
- ktos dolacza w trakcie roku
- pojawia sie darmowe zajecia
- operator daje dodatkowy rabat lub korekte

## Reguly rozliczen dla zajec

Na podstawie ustalen biznesowych przyjmujemy:

- `platnik` to zawsze rodzic / opiekun
- jeden numer telefonu moze byc powiazany z wieloma dziecmi
- pierwsze zajecia dla kazdego dziecka sa darmowe, takze przy dolaczeniu w trakcie roku
- dodatkowe darmowe zajecia moga byc przyznawane recznie, np. jako przeprosiny
- nieobecnosc dziecka jest platna
- zajecia odwolane przez organizacje sa nieplatne
- zajecia odwolane przez organizacje powinny dac sie oznaczyc jako `do odrobienia`

## Zmiany potrzebne w harmonogramie

Kazdy termin zajec powinien miec osobny rekord z polami pozwalajacymi oznaczyc:

- `scheduled`
- `free_for_all`
- `free_for_selected_customer`
- `cancelled_by_organization`
- `rescheduled`
- `makeup_term`

Przykladowe pola dla `billing_schedule_terms`:

- `billing_schedule_term_id`
- `organization_id`
- `billing_customer_agreement_id`
- `term_date`
- `school_year`
- `semester`
- `month_label`
- `is_chargeable`
- `is_intro_free`
- `is_manual_free`
- `is_cancelled`
- `rescheduled_from_term_id`
- `notes`

## Reguly cenowe do obslugi

System musi umiec obsluzyc co najmniej:

- platnosc `miesieczna`
- platnosc `semestralna`
- stawke bazowa zapisana w umowie
- zliczanie tylko zajec platnych
- rabaty rodzinne liczone na poziomie platnika
- rabaty jednorazowe liczone raz na rok

## Zapis ulg rodzinnych

Ustalone reguly biznesowe:

- zrodlem wplaty i identyfikatorem rodziny jest zwykle numer telefonu platnika
- znizka za rodzenstwo wynosi `-100 zl`
- przy platnosci semestralnej jest odejmowana od lacznej naleznosci dla kolejnego dziecka
- przy platnosci ratalnej jest odejmowana od pierwszej raty, a jesli to za malo, reszta przechodzi na druga rate
- karta duzej rodziny daje `-50 zl` na rodzine
- znizka z karty duzej rodziny jest odejmowana `raz w roku` na poczatku rozliczen

Te ulgi powinny byc zapisane jako osobne rekordy korekt, a nie tylko jako zmieniona cena koncowa.

Dzieki temu historia rozliczen pozostanie czytelna.

## Umowy i podpis elektroniczny

Modul powinien docelowo umiec:

1. wygenerowac umowe z szablonu
2. zapisac niezmienialny snapshot danych umowy
3. wyslac rodzicowi bezpieczny link do podgladu i podpisu
4. zapisac wynik podpisu, czas, adres IP i potwierdzenia
5. przechowac podpisany dokument i metadane w magazynie plikow

Przy podpisie trzeba rozroznic dwa poziomy:

- `forma dokumentowa`
- `forma elektroniczna rownowazna formie pisemnej`

Jesli celem jest odpowiednik podpisu wlasnorecznego w relacji prywatnej, modul powinien wspierac `kwalifikowany podpis elektroniczny`.

Jesli organizacja dopuszcza slabsza forme dla wybranych dokumentow, mozna dodatkowo wspierac `forme dokumentowa` z silnym sladem audytowym.

## Dane, ktore rodzic wybiera w umowie

W formularzu umowy rodzic powinien moc wskazac co najmniej:

- dane platnika
- numer telefonu kontaktowego
- numer telefonu uzywany jako identyfikator wplat
- dziecko lub dzieci objete umowa
- wariant platnosci: `miesieczna` albo `semestralna`
- zgody i oswiadczenia wymagane przez organizacje

## Rekomendacja wdrozeniowa

Najbezpieczniejsza kolejnosc prac:

1. model `platnik + dziecko + umowa + harmonogram`
2. generator naleznosci na podstawie podpisanej umowy
3. automatyczne dopasowanie wplat do platnika po numerze telefonu
4. reczne i automatyczne rozdzielanie wplaty na dzieci i naleznosci
5. generator umow PDF
6. integracja z podpisem elektronicznym
- mniejsze ryzyko na starcie
- latwiejsza obsluge wielu organizacji

## Obecny etap MVP

Na tym etapie system ma juz celowo `polautomatyczny generator naleznosci`.

Operator podaje:

- model rozliczen
- okres rozliczeniowy
- termin platnosci
- liczbe zajec w danym okresie

System wylicza potem:

- stawke jednostkowa z modelu
- darmowy start dziecka
- znizke rodzenstwa z przeniesieniem niewykorzystanej reszty na kolejny okres
- KDR liczone raz na rodzine w danym roku szkolnym

To jest rozwiazanie bezpieczniejsze niz pelna automatyzacja bez modulu harmonogramu i obecnosci, bo nie udaje wiedzy o liczbie zajec, gdy operator jeszcze jej nie skonfigurowal.

## Numer telefonu jako identyfikator platnosci

To jest sensowny model operacyjny dla MVP, ale warto traktowac go jako identyfikator platnosci, a nie glowny klucz rekordu klienta.

Najbezpieczniejszy wariant:

- klient ma wewnetrzne `billing_customer_id`
- klient moze miec `payment_identifier_type = telefon`
- klient ma znormalizowany `payment_identifier`, np. same cyfry numeru telefonu
- importer przelewow i silnik dopasowania szuka tego identyfikatora w tytule przelewu

To pozwala zachowac prostote obecnego sposobu pracy, a jednoczesnie nie zamyka drogi do przyszlego przejscia na osobne kody klientow.

## Najwazniejsza decyzja projektowa

MVP powinno byc budowane jako:

- `organizacje -> klienci organizacji -> uslugi -> naliczenia -> platnosci`

a nie jako:

- `organizacje -> uczniowie -> zajecia`

Drugi wariant bylby zbyt waski i szybko ograniczylby dalszy rozwoj.
