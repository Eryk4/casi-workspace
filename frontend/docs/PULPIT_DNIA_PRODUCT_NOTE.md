# Dzisiaj w CASI — produkt v1

`/pulpit-dnia` jest domyślnym, operacyjnym ekranem startowym aktywnego frontendu Next.js. Stary `/pulpit` pozostaje dostępny jako osobny, szerszy pulpit.

## Zakres produktu

Ekran odpowiada na jedno pytanie: co wymaga uwagi dzisiaj w aktywnej organizacji? Pokazuje, w stałej kolejności DOM:

1. `Wymaga uwagi` — maksymalnie 3 bezpieczne sygnały z Automation Operations Center.
2. `Zadania` — maksymalnie 5 widocznych zadań po terminie, na dziś lub nadchodzących.
3. `Rozliczenia` — maksymalnie 3 aktywne następne kroki po terminie lub na dziś.
4. `Ostatnia aktywność` — maksymalnie 3 bezpieczne zdarzenia automatyzacji.

Nie ma tu widgetu powiadomień, write actions, automatycznego odświeżania ani szerokiego agregowania CRM, dokumentów, faktur i sald. Odświeżenie jest wyłącznie ręczne.

## Źródła i uprawnienia

Frontend korzysta tylko z istniejących read modeli:

- `GET /api/automations/operations` — `automation.read`;
- `GET /api/dashboard/today/tasks` — `work_items.read`;
- `GET /api/dashboard/today/billing` — `billing.read`;
- `GET /api/automations/operations/activity?limit=3` — `automation.read`.

Widoczność i same requesty wynikają z efektywnych capabilities bieżącej sesji. Frontend nie wnioskuje dostępu z nazwy roli. Brak capability oznacza brak sekcji i brak requestu. Typowa macierz daje cztery sekcje ownerowi/adminowi, trzy koordynatorowi, jedną operatorowi i żadnej gościowi.

## Bezpieczeństwo i odporność

- Każdy request ma jawny `organization_id` aktywnej organizacji.
- Zmiana organizacji natychmiast ukrywa poprzedni zakres.
- Każda sekcja ma własny stan loading/error/empty i osobny retry.
- Token wersji requestu odrzuca spóźnione odpowiedzi ze starej organizacji albo cofniętego capability.
- Błąd jednej sekcji nie usuwa danych pozostałych sekcji.
- Parsowane są wyłącznie jawne, wąskie kontrakty; linki muszą być bezpiecznymi ścieżkami wewnętrznymi.
- Ekran nie wykonuje zapisów i nie pokazuje technicznych payloadów ani sekretów.

## Nawigacja i responsywność

Nazwa w nawigacji to `Dzisiaj`, a `/` przekierowuje do `/pulpit-dnia`. Układ priorytetów pozostaje w tej samej kolejności semantycznej także po przejściu z dwóch kolumn do jednej przy szerokości 1024 px. Dla małych ekranów lista przechodzi do jednokolumnowego układu metadanych.

## Testy

- `test-today-dashboard.js` — kontrakty Tasks/Billing, capability matrix, źródła requestów, limit i kolejność sekcji, routing.
- `test-today-dashboard-dom.js` — pełny render, niezależny błąd i retry, zmiana organizacji, capability gating oraz responsywność.
- `test_today_dashboard_read_models.py` — backendowe read modele, ACL, izolacja organizacji, prywatność, read-only, limity i stabilne sortowanie.
