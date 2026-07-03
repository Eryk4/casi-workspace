# Moduł rozliczeń klientów

Wersja: 2026-04-29  
Status: kierunek domenowy i architektura modułu rozliczeń  
Charakter dokumentu: opis produktu, modelu danych i kolejności wdrożenia

---

## Status dokumentu

Ten dokument opisuje kierunek rozwoju modułu rozliczeń klientów w CASI Workspace.

Moduł rozliczeń nie powinien być projektowany jako wąski moduł tylko dla uczniów, zajęć albo jednej firmy edukacyjnej.

Ma to być ogólny moduł do rozliczania klientów organizacji, który może obsłużyć różne branże, a jednocześnie dobrze wspierać przypadek szkoły robotyki, rodzin, rodzeństwa, płatników, uczniów, zniżek i wpłat zbiorczych.

`Uczeń` jest jednym z możliwych typów klienta końcowego albo beneficjenta usługi, ale nie powinien być jedynym fundamentem całego modelu.

Najważniejsze rozróżnienie:

- ogólny model techniczny powinien być oparty o `billing_customers`,
- przypadek ucznia, rodzica i rodziny powinien być obsłużony przez role, relacje i profile,
- główny widok operacyjny dla firmy edukacyjnej może nadal być widokiem „po uczniu”,
- rozliczenia i wpłaty powinny być prowadzone głównie „po płatniku / rodzinie”.

---

# 1. Główna decyzja projektowa

Moduł powinien być budowany jako:

```text
organizacje -> klienci organizacji -> usługi -> umowy -> naliczenia -> płatności
```

a nie jako:

```text
organizacje -> uczniowie -> zajęcia
```

Drugi wariant byłby zbyt wąski i szybko ograniczyłby dalszy rozwój produktu.

Najważniejsza zasada:

> Moduł rozliczeń ma być ogólny, ale musi dobrze obsługiwać przypadek zajęć, rodzin, dzieci, płatników, szkół i rabatów.

---

# 2. Model poziomów

W aplikacji rozdzielamy trzy poziomy:

1. `Właściciel platformy / administrator globalny`
2. `Organizacja` — klient korzystający z systemu
3. `Klient organizacji` — klient końcowy tej organizacji

To oznacza:

- właściciel platformy zarządza organizacjami,
- każda organizacja widzi tylko swoje dane,
- każda organizacja może mieć własną bazę klientów do rozliczeń,
- klient końcowy nie jest organizacją systemową,
- klient końcowy jest rekordem wewnątrz organizacji.

Przykład:

- CASI jest właścicielem platformy,
- Misja Robotyka albo inna firma jest organizacją,
- rodzic, dziecko, firma albo klient indywidualny są klientami organizacji.

---

# 3. Dlaczego nie używać `organizations` jako klientów końcowych

Tabela `organizations` jest granicą bezpieczeństwa i separacji danych.

Nie powinna być używana jednocześnie jako:

- tenant systemu,
- klient końcowy do rozliczeń.

Jeżeli pomieszamy te dwa poziomy, szybko powstaną problemy z:

- uprawnieniami,
- filtrowaniem danych,
- raportami,
- przyszłym panelem klienta,
- bezpieczeństwem danych,
- rozdzieleniem danych między firmami.

Zasada:

> `organizations` służy do separacji danych organizacji, a `billing_customers` do rozliczania klientów końcowych tej organizacji.

---

# 4. Relacja z modułem faktur

Obecny moduł `Faktury` obsługuje głównie dokumenty kosztowe i kontrahentów po stronie zakupowej.

Moduł rozliczeń klientów powinien obsługiwać stronę przychodową:

- klientów organizacji,
- należności,
- rozliczenia,
- wpłaty,
- salda,
- dokumenty rozliczeniowe.

Dlatego nie należy mieszać tego z tabelą `contractors`.

Najbezpieczniejszy podział:

- `contractors` — dostawcy, wystawcy faktur kosztowych, kontrahenci zakupowi,
- `billing_customers` — klienci, których organizacja rozlicza,
- `billing_payments` — wpłaty od klientów organizacji,
- `billing_charges` — naliczenia dla klientów organizacji.

---

# 5. Ogólny model domeny

Rekomendowany model powinien składać się z następujących encji:

- `billing_customers`
- `billing_customer_relations`
- `billing_customer_profiles`
- `billing_schools`
- `billing_services`
- `billing_models`
- `billing_customer_agreements`
- `billing_periods`
- `billing_schedule_terms`
- `billing_charges`
- `billing_adjustments`
- `billing_documents`
- `billing_payments`
- `billing_payment_allocations`
- `billing_bank_accounts`
- `billing_statement_imports`
- `billing_transactions`

Nie wszystkie encje muszą powstać od razu.

Moduł powinien być rozwijany etapami, ale bez zamykania drogi do pełnego modelu.

Ważne:

> Usunięcie osobnych tabel `billing_payers` i `billing_students` jako głównego modelu nie oznacza rezygnacji z rozliczania rodzin i uczniów. Płatnik i uczeń nadal istnieją, ale jako role, relacje i profile w ogólnym modelu `billing_customers`. Dzięki temu system obsługuje rodziny, rodzeństwo i szkoły, a jednocześnie nie zamyka się wyłącznie na branżę edukacyjną.

---

# 6. `billing_customers`

Tabela `billing_customers` przechowuje klientów końcowych organizacji.

To jest ogólna tabela, która może przechowywać różne typy klientów:

- rodzic / opiekun,
- dziecko / uczestnik zajęć,
- klient indywidualny,
- firma,
- grupa,
- instytucja,
- inny beneficjent usługi.

Przykładowe pola:

- `billing_customer_id`
- `organization_id`
- `customer_role`
- `customer_type`
- `display_name`
- `full_name`
- `company_name`
- `email`
- `phone`
- `payment_identifier`
- `payment_identifier_type`
- `external_code`
- `notes`
- `is_active`
- `created_at`
- `updated_at`

Przykładowe wartości `customer_role`:

- `payer` — płatnik, np. rodzic, opiekun, firma płacąca,
- `beneficiary` — odbiorca usługi, np. dziecko albo uczestnik,
- `both` — klient jest jednocześnie płatnikiem i odbiorcą usługi.

Przykładowe wartości `customer_type`:

- `rodzic`
- `opiekun`
- `uczen`
- `klient_indywidualny`
- `firma`
- `grupa`
- `instytucja`

Zasada:

> Jeden ogólny model klienta jest lepszy niż osobny, sztywny moduł tylko dla uczniów.

Przykład dla rodzeństwa:

```text
Rodzina Kowalskich / Mama / Tata = billing_customer z rolą payer

Dziecko 1 = billing_customer z rolą beneficiary
Dziecko 2 = billing_customer z rolą beneficiary
Dziecko 3 = billing_customer z rolą beneficiary
```

Czyli rodzina, rodzic albo opiekun jest płatnikiem, a dzieci są beneficjentami usługi.

---

# 7. `billing_customer_relations`

Tabela relacji między klientami organizacji.

Jest potrzebna, bo w praktyce jeden płatnik może być powiązany z wieloma odbiorcami usługi.

Przykład:

- rodzic płaci za jedno dziecko,
- rodzic płaci za kilkoro dzieci,
- firma płaci za pracowników,
- organizacja płaci za grupę uczestników.

Przykładowe pola:

- `billing_customer_relation_id`
- `organization_id`
- `parent_customer_id`
- `child_customer_id`
- `relation_type`
- `is_primary`
- `created_at`
- `updated_at`

Przykładowe wartości `relation_type`:

- `parent_child`
- `payer_beneficiary`
- `guardian_child`
- `company_employee`
- `group_member`

Dla szkoły robotyki:

- rodzic ma rekord `payer`,
- dziecko ma rekord `beneficiary`,
- relacja łączy dziecko z rodzicem jako płatnikiem.

Przykład:

```text
Rodzina Kowalskich -> Jan Kowalski
Rodzina Kowalskich -> Anna Kowalska
Rodzina Kowalskich -> Piotr Kowalski
```

To pozwala obsłużyć rodzeństwo, wspólne wpłaty, zniżki rodzinne i saldo rodzinne.

---

# 8. `billing_customer_profiles`

Tabela profili rozszerzających dane klienta zależnie od branży lub typu klienta.

Nie wszystkie dane powinny trafiać do głównej tabeli `billing_customers`, bo wtedy tabela szybko stanie się zbyt szeroka.

Dla branży edukacyjnej można użyć profilu ucznia.

Przykładowe pola:

- `billing_customer_profile_id`
- `organization_id`
- `billing_customer_id`
- `profile_type`
- `billing_school_id`
- `lesson_day`
- `group_name`
- `school_year`
- `notes`
- `created_at`
- `updated_at`

Przykładowe wartości `profile_type`:

- `student`
- `company_client`
- `individual_client`
- `group_member`

Dla ucznia warto przechowywać:

- szkołę,
- grupę,
- dzień zajęć,
- rok szkolny,
- informacje organizacyjne.

Główny widok operacyjny w firmie edukacyjnej może być nadal „po uczniu”, ale rozliczenia i wpłaty powinny być powiązane z płatnikiem.

---

# 9. `billing_schools`

Słownik szkół.

Ponieważ organizacja może pracować w wielu szkołach, potrzebny jest osobny słownik szkół zamiast wpisywania ich ręcznie przy każdym uczniu.

Przykładowe pola:

- `billing_school_id`
- `organization_id`
- `full_name`
- `short_name`
- `city`
- `notes`
- `is_active`
- `created_at`
- `updated_at`

Zasady:

- skrót szkoły powinien być używany w tabelach i filtrach,
- pełna nazwa szkoły powinna być używana w formularzach, dokumentach i raportach,
- szkoła należy do organizacji.

---

# 10. `billing_services`

Tabela usług sprzedawanych lub rozliczanych przez organizację.

Przykładowe pola:

- `billing_service_id`
- `organization_id`
- `name`
- `service_type`
- `unit_type`
- `default_price`
- `currency`
- `is_active`
- `created_at`
- `updated_at`

Przykładowe wartości `service_type`:

- `zajecia`
- `abonament`
- `pakiet`
- `konsultacja`
- `opieka`
- `usluga_jednorazowa`
- `inne`

Przykładowe wartości `unit_type`:

- `miesiac`
- `semestr`
- `spotkanie`
- `godzina`
- `pakiet`
- `sztuka`

Zasada:

> Usługa opisuje, co organizacja sprzedaje, ale konkretna cena dla klienta powinna wynikać z umowy lub modelu rozliczeń.

---

# 11. `billing_models`

Słownik modeli rozliczeń.

Model rozliczeń pozwala skonfigurować typowe zasady raz, zamiast ustawiać wszystko ręcznie przy każdym kliencie.

Dla szkoły robotyki można mieć na przykład:

- `26/27 Poniedziałek`
- `26/27 Wtorek`
- `26/27 Piątek`
- `26/27 Grupa pokazowa`
- `26/27 Kurs semestralny`

Przykładowe pola:

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
- `is_active`
- `created_at`
- `updated_at`

Przykładowe wartości `settlement_mode`:

- `miesieczny`
- `semestralny`
- `jednorazowy`
- `za_wykorzystanie`
- `pakiet`
- `mieszany`

Zasada:

> `billing_models` to szablon zasad, ale źródłem prawdy dla konkretnego klienta powinna być umowa.

---

# 12. `billing_customer_agreements`

Umowa lub aktywne przypisanie klienta do usługi.

To jedna z najważniejszych encji modułu.

Umowa powinna być źródłem prawdy dla naliczeń.

Przykładowe pola:

- `billing_customer_agreement_id`
- `organization_id`
- `payer_customer_id`
- `beneficiary_customer_id`
- `billing_service_id`
- `billing_model_id`
- `billing_model_snapshot`
- `billing_model`
- `price_amount`
- `billing_cycle`
- `payment_variant`
- `start_date`
- `end_date`
- `status`
- `contract_required`
- `contract_document_id`
- `notes`
- `created_at`
- `updated_at`

Przykładowe wartości `billing_model`:

- `abonament`
- `za_wykorzystanie`
- `pakiet`
- `mieszany`

Przykładowe wartości `billing_cycle`:

- `miesieczny`
- `semestralny`
- `jednorazowy`
- `rekordowy`

Przykładowe wartości `payment_variant`:

- `miesieczna`
- `semestralna`
- `jednorazowa`

## Umowa jako źródło prawdy

Ze względu na realną praktykę i możliwe błędy w ręcznych tabelach, źródłem prawdy dla naliczeń nie powinien być sam globalny cennik.

Najbezpieczniej przyjąć, że źródłem prawdy jest:

- podpisana lub zatwierdzona umowa,
- wybrany wariant płatności,
- harmonogram zajęć przypisany do umowy,
- zestaw ulg i wyjątków zapisany przy umowie,
- snapshot warunków z momentu zawarcia umowy.

To pozwala obsłużyć sytuacje, w których:

- różnią się stawki między grupami,
- klient dołącza w trakcie roku,
- pojawiają się darmowe zajęcia,
- operator daje dodatkowy rabat lub korektę,
- zasady cennika zmieniają się w czasie, ale stara umowa zachowuje swoje warunki.

---

# 13. `billing_periods`

Okresy rozliczeniowe, z których liczone są należności.

Przykładowe pola:

- `billing_period_id`
- `organization_id`
- `period_label`
- `date_from`
- `date_to`
- `school_year`
- `semester`
- `status`
- `created_at`
- `updated_at`

Przykładowe statusy:

- `otwarty`
- `zamkniety`
- `rozliczony`
- `anulowany`

Przykłady okresów:

- `Wrzesień 2026`
- `Październik 2026`
- `Semestr 1 2026/2027`
- `Rok szkolny 2026/2027`

---

# 14. `billing_schedule_terms`

Terminy zajęć lub świadczenia usługi.

Ta tabela jest szczególnie ważna dla zajęć edukacyjnych, ale może też obsłużyć inne branże, gdzie usługa jest realizowana w terminach.

Przykładowe pola:

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
- `cancelled_by`
- `rescheduled_from_term_id`
- `makeup_for_term_id`
- `notes`
- `created_at`
- `updated_at`

Przykładowe statusy lub flagi:

- `scheduled`
- `free_for_all`
- `free_for_selected_customer`
- `cancelled_by_organization`
- `rescheduled`
- `makeup_term`

Zasady dla zajęć:

- pierwsze zajęcia dziecka mogą być darmowe,
- dodatkowe darmowe zajęcia mogą być przyznane ręcznie,
- nieobecność dziecka jest płatna,
- zajęcia odwołane przez organizację są niepłatne,
- zajęcia odwołane przez organizację mogą być oznaczone jako `do odrobienia`.

---

# 15. `billing_charges`

Naliczenia dla klienta.

To tabela pozycji, które tworzą należność.

Przykłady naliczeń:

- abonament miesięczny,
- rata semestralna,
- płatne zajęcia,
- nieobecność płatna,
- dopłata,
- ręczna korekta,
- opłata jednorazowa.

Przykładowe pola:

- `billing_charge_id`
- `organization_id`
- `payer_customer_id`
- `beneficiary_customer_id`
- `billing_service_id`
- `billing_customer_agreement_id`
- `billing_period_id`
- `billing_schedule_term_id`
- `charge_type`
- `quantity`
- `unit_price`
- `gross_amount`
- `currency`
- `charge_date`
- `due_date`
- `description`
- `source`
- `status`
- `created_by_user_id`
- `created_at`
- `updated_at`

Przykładowe wartości `charge_type`:

- `monthly_fee`
- `semester_fee`
- `lesson_fee`
- `manual_charge`
- `correction`
- `extra_fee`

Przykładowe statusy:

- `draft`
- `open`
- `partially_paid`
- `paid`
- `cancelled`

W przypadku zajęć:

- `payer_customer_id` wskazuje rodzica, opiekuna albo rodzinę,
- `beneficiary_customer_id` wskazuje dziecko lub uczestnika,
- dzięki temu jedna rodzina może mieć kilka naliczeń dla różnych dzieci.

---

# 16. `billing_adjustments`

Osobne rekordy korekt, rabatów i ulg.

Ulgi nie powinny być zapisywane tylko jako zmieniona cena końcowa, ponieważ wtedy historia rozliczeń staje się nieczytelna.

Przykładowe pola:

- `billing_adjustment_id`
- `organization_id`
- `payer_customer_id`
- `beneficiary_customer_id`
- `billing_charge_id`
- `billing_customer_agreement_id`
- `billing_period_id`
- `adjustment_type`
- `amount`
- `currency`
- `reason`
- `applies_once`
- `school_year`
- `created_by_user_id`
- `created_at`

Przykładowe wartości `adjustment_type`:

- `sibling_discount`
- `large_family_discount`
- `manual_discount`
- `manual_correction`
- `intro_free_lesson`
- `organization_cancelled_lesson`

Zasada:

> Rabaty, ulgi i korekty powinny mieć osobny ślad, żeby było wiadomo, dlaczego klient ma zapłacić mniej albo więcej.

---

# 17. `billing_documents`

Dokument podsumowujący rozliczenie klienta za okres.

Na start może to być dokument wewnętrzny, zestawienie, informacja do zapłaty albo wezwanie do zapłaty.

Nie musi to być od razu pełna księgowa faktura sprzedażowa.

Przykładowe pola:

- `billing_document_id`
- `organization_id`
- `payer_customer_id`
- `billing_period_id`
- `document_number`
- `document_type`
- `status`
- `issue_date`
- `due_date`
- `total_amount`
- `paid_amount`
- `remaining_amount`
- `currency`
- `file_storage_key`
- `storage_backend`
- `notes`
- `created_at`
- `updated_at`

Przykładowe wartości `document_type`:

- `internal_statement`
- `payment_notice`
- `invoice_draft`
- `sales_invoice`
- `correction`

Przykładowe statusy:

- `draft`
- `issued`
- `sent`
- `partially_paid`
- `paid`
- `cancelled`

---

# 18. `billing_payments`

Ewidencja wpłat klienta.

Wpłata powinna być przypisana przede wszystkim do płatnika, a dopiero później rozdzielana na konkretne dzieci, usługi lub należności.

Przykładowe pola:

- `billing_payment_id`
- `organization_id`
- `payer_customer_id`
- `payment_date`
- `amount`
- `currency`
- `payment_method`
- `reference`
- `source`
- `billing_transaction_id`
- `matched_status`
- `notes`
- `created_at`
- `updated_at`

Przykładowe wartości `payment_method`:

- `bank_transfer`
- `cash`
- `card`
- `blik`
- `other`

Przykładowe wartości `matched_status`:

- `unmatched`
- `matched_to_payer`
- `partially_allocated`
- `allocated`
- `needs_review`

Przykład:

```text
Wpłata 1 200 zł -> Rodzina Kowalskich
```

To jeszcze nie oznacza, że cała kwota dotyczy jednego dziecka. Dopiero alokacje pokazują, jak wpłata została rozdzielona.

---

# 19. `billing_payment_allocations`

Rozdzielenie wpłaty na konkretne należności.

Jest to potrzebne, bo jedna wpłata może pokrywać:

- jedno dziecko,
- kilkoro dzieci,
- kilka okresów,
- kilka dokumentów,
- zaległości i bieżące należności jednocześnie.

Przykładowe pola:

- `billing_payment_allocation_id`
- `organization_id`
- `billing_payment_id`
- `billing_charge_id`
- `billing_document_id`
- `payer_customer_id`
- `beneficiary_customer_id`
- `allocated_amount`
- `currency`
- `allocation_method`
- `created_by_user_id`
- `created_at`

Przykładowe wartości `allocation_method`:

- `automatic`
- `manual`
- `suggested_by_system`

Zasada:

> Sama wpłata mówi, że pieniądze przyszły. Alokacja mówi, którą należność ta wpłata spłaciła.

Przykład:

```text
Wpłata 1 200 zł -> Rodzina Kowalskich

Alokacja 1: 600 zł -> Jan Kowalski -> Semestr 1
Alokacja 2: 600 zł -> Anna Kowalska -> Semestr 1
```

---

# 20. Rachunki bankowe i import wyciągów

Moduł rozliczeń powinien korzystać z prostego i bezpiecznego modelu importu wyciągów bankowych.

Na start przyjmujemy model:

- operator dodaje rachunek bankowy organizacji,
- operator importuje wyciąg w formacie `CSV`,
- system zapisuje transakcje do wspólnej tabeli,
- system pomija duplikaty przy ponownym imporcie tych samych pozycji,
- system próbuje dopasować wpłaty do płatników.

Ten model daje:

- prostsze wdrożenie,
- brak zależności od integratorów open banking,
- lepszą kontrolę nad dopasowaniem wpłat,
- łatwiejsze debugowanie błędów,
- możliwość pracy półautomatycznej.

## `billing_bank_accounts`

Rachunki bankowe organizacji.

Przykładowe pola:

- `billing_bank_account_id`
- `organization_id`
- `account_name`
- `bank_name`
- `iban`
- `currency`
- `is_active`
- `created_at`
- `updated_at`

## `billing_statement_imports`

Rejestr importów wyciągów bankowych.

Przykładowe pola:

- `billing_statement_import_id`
- `organization_id`
- `billing_bank_account_id`
- `source_type`
- `source_file_name`
- `imported_by_user_id`
- `imported_at`
- `row_count`
- `imported_transaction_count`
- `skipped_transaction_count`
- `status`
- `notes`
- `created_at`
- `updated_at`

## `billing_transactions`

Znormalizowane transakcje z wyciągów bankowych.

Przykładowe pola:

- `billing_transaction_id`
- `organization_id`
- `billing_bank_account_id`
- `billing_statement_import_id`
- `booking_date`
- `value_date`
- `amount`
- `currency`
- `direction`
- `counterparty_name`
- `counterparty_account`
- `title`
- `reference`
- `raw_data`
- `transaction_hash`
- `matched_status`
- `created_at`
- `updated_at`

Zasada:

> Transakcja bankowa nie jest jeszcze rozliczoną wpłatą. Dopiero po dopasowaniu może utworzyć lub zasilić `billing_payment`.

---

# 21. Numer telefonu jako identyfikator płatności

Numer telefonu jest sensownym identyfikatorem operacyjnym dla szkoły robotyki i podobnych firm, ale nie powinien być głównym kluczem rekordu klienta.

Najbezpieczniejszy wariant:

- klient ma wewnętrzne `billing_customer_id`,
- klient może mieć `payment_identifier_type = telefon`,
- klient ma znormalizowany `payment_identifier`, np. same cyfry numeru telefonu,
- importer przelewów i silnik dopasowania szuka tego identyfikatora w tytule przelewu.

To pozwala zachować prostotę obecnego sposobu pracy, a jednocześnie nie zamyka drogi do przyszłego przejścia na:

- osobne kody klienta,
- indywidualne identyfikatory płatności,
- mikrorachunki,
- integrację z płatnościami online,
- panel klienta końcowego.

Zasada:

> Telefon może identyfikować płatność, ale nie powinien być technicznym ID klienta.

---

# 22. Dopasowanie wpłat

Wpłata z wyciągu powinna być dopasowywana w kilku krokach.

Rekomendowana kolejność:

1. Dopasowanie po znormalizowanym identyfikatorze płatności.
2. Dopasowanie po numerze telefonu w tytule przelewu.
3. Dopasowanie po nazwie płatnika.
4. Dopasowanie po kwocie i otwartych należnościach.
5. Oznaczenie jako `needs_review`, jeżeli system nie ma pewności.

Dla zajęć dzieci:

- numer telefonu zwykle identyfikuje rodzinę lub płatnika,
- jeden numer telefonu może dotyczyć kilkorga dzieci,
- jedna wpłata może pokrywać kilka należności,
- system nie powinien automatycznie przypisywać całej wpłaty do jednego dziecka, gdy płatnik ma więcej dzieci.

Zasada:

> Najpierw dopasuj wpłatę do płatnika, potem rozdziel ją na należności.

---

# 23. Specjalny przypadek: zajęcia, rodziny i uczniowie

Dla zajęć edukacyjnych ważne jest rozdzielenie:

1. płatnika,
2. uczestnika / dziecka / beneficjenta usługi,
3. umowy,
4. harmonogramu zajęć,
5. naliczeń,
6. wpłat.

W module rozliczeń dla zajęć płatnikiem nie jest samo dziecko, tylko najczęściej:

- rodzic,
- opiekun,
- rodzina,
- firma płacąca.

Jeden płatnik może być powiązany z wieloma dziećmi.

Jedna wpłata może pokrywać:

- ratę jednego dziecka,
- raty kilkorga dzieci,
- semestr jednego dziecka,
- semestr kilku dzieci,
- zaległości i bieżące należności.

Dlatego główny widok operacyjny może być „po uczniu”, ale rozliczenia powinny być liczone i dopasowywane „po płatniku”.

---

# 24. Widok operacyjny dla szkoły robotyki

W praktyce operator często myśli po uczniu, nie po płatniku.

Dlatego widok uczniów powinien pokazywać:

- imię i nazwisko ucznia,
- skrót szkoły,
- grupę,
- dzień zajęć,
- model rozliczeń,
- płatnika,
- telefon rodziny,
- status umowy,
- saldo płatnika,
- ostatnią wpłatę rodziny,
- najbliższą należność,
- status rozliczenia.

Ważne:

Ostatnia wpłata rodziny jest informacją o płatniku i nie musi oznaczać, że cała kwota dotyczy tylko jednego dziecka.

---

# 25. Reguły rozliczeń dla zajęć

Na podstawie ustaleń biznesowych dla zajęć przyjmujemy:

- płatnik to najczęściej rodzic / opiekun / rodzina,
- jeden numer telefonu może być powiązany z wieloma dziećmi,
- pierwsze zajęcia dla każdego dziecka są darmowe, także przy dołączeniu w trakcie roku,
- dodatkowe darmowe zajęcia mogą być przyznawane ręcznie, np. jako przeprosiny,
- nieobecność dziecka jest płatna,
- zajęcia odwołane przez organizację są niepłatne,
- zajęcia odwołane przez organizację powinny dać się oznaczyć jako `do odrobienia`,
- płatność może być miesięczna albo semestralna,
- stawka bazowa powinna wynikać z umowy albo jej snapshotu,
- rabaty rodzinne powinny być liczone na poziomie płatnika,
- rabaty jednorazowe powinny być widoczne jako korekty.

Te reguły powinny być konfigurowalne, a nie twardo zakodowane na stałe w logice aplikacji.

---

# 26. Ulgi rodzinne i KDR

Ustalone reguły biznesowe dla zajęć:

- źródłem wpłaty i identyfikatorem rodziny jest zwykle numer telefonu płatnika,
- zniżka za rodzeństwo wynosi `-100 zł`,
- przy płatności semestralnej zniżka jest odejmowana od łącznej należności dla kolejnego dziecka,
- przy płatności ratalnej zniżka jest odejmowana od pierwszej raty, a gdy to za mało, reszta przechodzi na drugą ratę,
- karta dużej rodziny daje `-50 zł` na rodzinę,
- zniżka z karty dużej rodziny jest odejmowana raz w roku na początku rozliczeń.

Ważne:

Te wartości powinny być traktowane jako ustawienia organizacji albo modelu rozliczeń, nie jako stałe techniczne zapisane na sztywno w kodzie.

Ulgi powinny być zapisywane jako osobne rekordy `billing_adjustments`, a nie tylko jako zmieniona cena końcowa.

Dzięki temu historia rozliczeń pozostaje czytelna.

---

# 27. Półautomatyczny generator należności

Na obecnym etapie najbezpieczniejszy jest półautomatyczny generator należności.

Operator podaje:

- model rozliczeń,
- okres rozliczeniowy,
- termin płatności,
- liczbę zajęć w danym okresie.

System wylicza potem:

- stawkę jednostkową z modelu,
- darmowy start dziecka,
- zniżkę rodzeństwa,
- przeniesienie niewykorzystanej reszty zniżki na kolejny okres,
- KDR liczone raz na rodzinę w danym roku szkolnym,
- należność dla płatnika,
- należność dla konkretnego beneficjenta.

To jest bezpieczniejsze niż pełna automatyzacja bez gotowego modułu harmonogramu i obecności, ponieważ system nie udaje wiedzy o liczbie zajęć, jeżeli operator jeszcze jej nie skonfigurował.

Zasada:

> Najpierw półautomatyczne, kontrolowane naliczanie. Pełna automatyzacja dopiero po stabilnym harmonogramie i regułach obecności.

---

# 28. Umowy i podpis elektroniczny

Moduł powinien docelowo umożliwiać pracę z umowami.

Kierunek rozwoju:

1. wygenerowanie umowy z szablonu,
2. zapisanie niezmienialnego snapshotu danych umowy,
3. wysłanie rodzicowi lub klientowi bezpiecznego linku do podglądu,
4. zebranie akceptacji lub podpisu,
5. zapisanie czasu, adresu IP i potwierdzeń,
6. przechowanie dokumentu i metadanych w magazynie plików.

Ważne:

Kwestie prawne związane z podpisem elektronicznym, formą dokumentową, podpisem kwalifikowanym i równoważnością z podpisem własnoręcznym powinny zostać osobno zweryfikowane prawnie przed wdrożeniem produkcyjnym.

Na poziomie architektury aplikacja powinna być gotowa do przechowywania:

- szablonu umowy,
- snapshotu danych,
- wygenerowanego PDF,
- statusu podpisu,
- metadanych podpisu,
- historii zdarzeń,
- linku do pliku w storage.

---

# 29. Dane wybierane w umowie

W formularzu umowy klient lub rodzic powinien móc wskazać co najmniej:

- dane płatnika,
- numer telefonu kontaktowego,
- numer telefonu używany jako identyfikator wpłat,
- dziecko lub dzieci objęte umową,
- usługę,
- model rozliczeń,
- wariant płatności: `miesieczna` albo `semestralna`,
- zgody i oświadczenia wymagane przez organizację.

Po zatwierdzeniu umowy system powinien zapisać snapshot warunków, żeby późniejsze zmiany cennika nie zmieniały historycznej umowy.

---

# 30. Rekomendowany zakres wersji bazowej produktu

Na start warto przyjąć taki zakres:

1. baza klientów organizacji,
2. płatnik i beneficjent jako role klienta,
3. relacje między płatnikiem a beneficjentem,
4. słownik szkół,
5. definicje usług,
6. modele rozliczeń,
7. przypisanie klienta do usługi i modelu rozliczeń,
8. półautomatyczne naliczanie należności,
9. saldo płatnika,
10. historia wpłat,
11. import wyciągów bankowych CSV,
12. dopasowanie wpłat do płatnika po identyfikatorze,
13. ręczne rozdzielanie wpłaty na należności,
14. lista należności po organizacji.

Nie trzeba na start wdrażać:

- pełnego panelu klienta końcowego,
- pełnego podpisu elektronicznego,
- pełnej automatyzacji harmonogramu,
- pełnej integracji z bankiem przez API,
- księgowej faktury sprzedażowej,
- wszystkich wariantów rabatów dla każdej branży.

---

# 31. Rekomendowana kolejność wdrożenia

Najbezpieczniejsza kolejność prac:

1. Model `płatnik + beneficjent + relacja`.
2. Słownik szkół i profil ucznia.
3. Definicje usług.
4. Modele rozliczeń.
5. Umowa / przypisanie klienta do usługi.
6. Półautomatyczny generator należności.
7. Import wyciągów bankowych CSV.
8. Dopasowanie wpłat do płatnika po numerze telefonu lub identyfikatorze.
9. Ręczne rozdzielanie wpłaty na dzieci i należności.
10. Saldo płatnika.
11. Historia rozliczeń.
12. Dokumenty rozliczeniowe.
13. Generator umów PDF.
14. Integracja z podpisem elektronicznym.
15. Pełniejsza automatyzacja harmonogramu i obecności.
16. Przyszły panel klienta końcowego.

Ta kolejność ogranicza ryzyko i pozwala wcześniej uzyskać działającą wartość biznesową.

---

# 32. Czego nie robić na start

Na obecnym etapie nie warto:

- budować modułu tylko pod uczniów,
- używać `organizations` jako klientów końcowych,
- mieszać `contractors` z klientami rozliczanymi,
- opierać technicznego ID klienta na numerze telefonu,
- zakładać, że jedna wpłata dotyczy zawsze jednego dziecka,
- kodować rabatów na sztywno bez możliwości konfiguracji,
- budować pełnej automatyzacji bez stabilnego modelu harmonogramu,
- budować pełnego panelu rodzica zanim operator ma sprawny panel rozliczeń,
- wdrażać integracji bankowej API, gdy CSV wystarczy na start,
- generować księgowych faktur sprzedażowych, gdy na start wystarczy dokument wewnętrzny lub zestawienie.

Zasada:

> Najpierw stabilne rozliczenia operacyjne, potem automatyzacja i formalne dokumenty.

---

# 33. Najważniejsze zasady bezpieczeństwa danych

Moduł rozliczeń będzie przetwarzał dane wrażliwe biznesowo i osobowe.

Należy szczególnie uważać na:

- dane dzieci,
- dane rodziców,
- numery telefonów,
- adresy e-mail,
- płatności,
- wyciągi bankowe,
- tytuły przelewów,
- dokumenty umów,
- historię rozliczeń.

Zasady:

- każdy rekord musi należeć do organizacji,
- użytkownik organizacji widzi tylko dane swojej organizacji,
- import wyciągów musi być przypisany do organizacji,
- wpłaty muszą być dopasowywane tylko w obrębie organizacji,
- dokumenty i umowy powinny być przechowywane przez warstwę storage,
- logi nie powinny bez potrzeby ujawniać pełnych danych wrażliwych,
- dostęp do modułu powinien być kontrolowany przez role i capability.

Przykładowe capability:

- `billing.read`
- `billing.manage_customers`
- `billing.manage_services`
- `billing.generate_charges`
- `billing.import_bank_statements`
- `billing.manage_payments`
- `billing.manage_documents`
- `billing.admin`

---

# 34. Raporty i widoki

Docelowo moduł powinien mieć kilka podstawowych widoków.

## Widok klientów

Dla ogólnego modułu:

- lista klientów,
- typ klienta,
- rola klienta,
- status,
- saldo,
- ostatnia wpłata,
- najbliższa należność.

## Widok uczniów

Dla firm edukacyjnych:

- uczeń,
- szkoła,
- grupa,
- dzień zajęć,
- płatnik,
- telefon płatnika,
- model rozliczeń,
- saldo rodziny,
- ostatnia wpłata,
- status umowy.

## Widok płatników

- płatnik,
- telefon,
- e-mail,
- liczba powiązanych beneficjentów,
- saldo,
- suma zaległości,
- ostatnia wpłata.

## Widok należności

- okres,
- płatnik,
- beneficjent,
- usługa,
- kwota,
- termin płatności,
- status,
- źródło naliczenia.

## Widok wpłat

- data,
- płatnik,
- kwota,
- tytuł przelewu,
- status dopasowania,
- alokacje,
- źródło.

## Widok importów bankowych

- data importu,
- rachunek,
- plik,
- liczba transakcji,
- liczba nowych transakcji,
- liczba pominiętych duplikatów,
- status.

---

# 35. Zasada końcowa

Moduł rozliczeń klientów ma być uniwersalnym modułem przychodowym dla organizacji.

Ma obsługiwać prostą sytuację:

```text
klient -> usługa -> należność -> wpłata
```

ale musi też obsługiwać bardziej realną sytuację:

```text
płatnik -> kilka dzieci / beneficjentów -> kilka umów -> kilka należności -> jedna lub wiele wpłat
```

Najważniejsze decyzje:

- nie mieszać organizacji z klientami końcowymi,
- nie mieszać kontrahentów kosztowych z klientami przychodowymi,
- płatnik i beneficjent to różne role,
- rodzina, rodzic albo opiekun mogą być płatnikiem,
- uczeń albo dziecko może być beneficjentem usługi,
- jeden płatnik może mieć wielu beneficjentów,
- jedna wpłata może pokrywać wielu beneficjentów i wiele należności,
- telefon może być identyfikatorem płatności, ale nie głównym ID klienta,
- umowa lub przypisanie klienta do usługi powinno być źródłem prawdy,
- rabaty i korekty powinny mieć własne rekordy,
- wpłaty powinny być najpierw dopasowane do płatnika, a potem rozdzielane na należności,
- moduł ma być ogólny, ale dobrze obsługiwać przypadek szkoły robotyki.