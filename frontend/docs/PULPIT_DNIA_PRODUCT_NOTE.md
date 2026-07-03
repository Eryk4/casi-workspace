# Pulpit dnia - produkt v1

Last checked: 2026-07-03

`Pulpit dnia` jest produktowym ekranem v1 w aktywnym froncie Next. Jest prawdziwym ekranem CASI, a nie pokazowka ani ekranem tymczasowym. Its product question is:

> Co dzisiaj wymaga mojej uwagi?

Ekran odpowiada na poranne pytanie wlasciciela lub osoby operacyjnej: czym trzeba zajac sie dzis najpierw. Jest deterministycznym, organizacyjnie zawezonym widokiem tylko do odczytu, skladanym z istniejacych zrodel danych.

## Scope

Route:

- `/pulpit-dnia`

Frontend module:

- `frontend/src/modules/daily-brief/`

Active frontend source of truth:

- `frontend/`

Legacy UI:

- `static/` remains legacy and is not used by this module.

## Data Sources

The first version uses existing read-only endpoints:

- `GET /api/dashboard?organization_id=...`
- `GET /api/tasks/focus?organization_id=...`
- `GET /api/work-items?organization_id=...&only_open=1&limit=100`
- `GET /api/invoices/verification-inbox?organization_id=...`
- `GET /api/billing/ledger/balances?organization_id=...`
- `GET /api/contractors?organization_id=...`
- `GET /api/knowledge/documents?organization_id=...`

Nie dodano nowego endpointu agregujacego, poniewaz obecne zrodla wystarczaja do wersji produktowej v1.

## Sections

The screen groups signals into:

- Najważniejsze dziś
- Sprawy pilne
- Faktury i finanse
- Kontrahenci
- Dokumenty
- Można odłożyć

Prioritization is deterministic and based on existing fields such as severity, priority, SLA state, invoice inbox sections, balance due, document status, and CRM freshness/contact gaps.

Sekcja `Najważniejsze dziś` jest celowo zbalansowana. It is not a pure score ranking, because one noisy domain could otherwise dominate the morning view. Current rules:

- maximum 7 items,
- maximum 2 invoice items,
- maximum 2 task/work-item items,
- maximum 1 finance item,
- maximum 1 CRM item,
- maximum 1 document item,
- maximum 1 other operational alert,
- first pass tries to include a mix of tasks, invoices, CRM, documents, finance, and other signals,
- second pass fills remaining slots by priority while respecting category limits.

Duplikaty i wyjatki faktur pozostaja widoczne w `Faktury i finanse`, ale tylko najsilniejsze sygnaly fakturowe moga wejsc do `Najważniejsze dziś`.

`Można odłożyć` pokazuje spokojniejsze sprawy: mniej pilne sprawy operacyjne, stabilnych kontrahentow, dokumenty bez blokady, przypomnienia niskiej pilnosci i stabilne rozliczenia. If there is truly nothing calm to show, the UI uses a product empty state instead of a technical error-like message.

## Scenariusz lokalnego sandboxu danych

`Pulpit dnia` is a real application screen. The current local data is a fictional sandbox used to verify the product experience safely before any real customer data is connected.

The local sandbox data should make the screen feel like a real morning review for a small operating company, not like a technical fixture.

For the CASI organization, the expected story is:

- the owner starts the day with a few operational decisions,
- one or two invoices need description or confirmation,
- contractor context matters because repeated suppliers and new suppliers appear in the inbox,
- documents such as delegation, onboarding, access, leave, and replacement procedures support the decisions,
- some reminders are urgent today, while calmer planning items can be moved to `Mozna odlozyc`.

For Misja Robotyka, the expected story is:

- the morning review combines class logistics, parent communication, instructor replacements, billing signals, and education-material invoices,
- urgent items should not be only invoices,
- billing and contractor signals should explain what needs attention without turning the page into a finance-only dashboard.

Seeded sandbox data should avoid user-facing labels such as `test item`, `temporary work item`, `sample`, `lorem ipsum`, and folder-derived document names like `folder ...`. Fictional data is fine, but it should sound like normal work a business owner or operations lead would actually recognize.

## Organization Scope

The screen requires an active organization.

Without selected organization it shows:

- `Wybierz organizację, aby zobaczyć Pulpit dnia`

The screen must not request organization-scoped operational data without `organization_id`.

## Read-only Contract

This module does not expose write actions.

It must not add:

- assign/snooze/close buttons,
- invoice comment forms,
- CRM note forms,
- document upload/edit/delete/OCR actions,
- status changes,
- workflow decisions,
- AI chat or generation actions.

Dozwolone interakcje to odswiezenie oraz linki do istniejacych modulow.

## Known Data Gaps

The first version intentionally avoids extra detail requests and backend changes. Therefore:

- CRM uses contractor list signals, not a full recent-note stream.
- Documents use list/dashboard status fields, not comments or version actions.
- Finance uses ledger balances, not bank import or matching write flows.
- Invoice signals use verification inbox and links to detail, not workflow decisions.
- Existing local databases seeded before the sandbox-data cleanup can still contain older titles dopoki lokalny sandbox danych nie zostanie swiadomie zresetowany i ponownie zasilony. This document describes the intended fresh sandbox scenario.

Przed normalnym uzyciem operacyjnym najwieksze ograniczenia to:

- stabilny read-only endpoint agregujacy, jesli agregacja po stronie frontendu okaze sie zbyt kosztowna lub zbyt rozproszona,
- client-specific sandbox scenarios that reflect the pilot customer's actual operating rhythm without using production data,
- better recent-activity signals for CRM notes, document changes, and invoice comments,
- jeszcze lepsze, wlascicielskie wyjasnienie, dlaczego dana sprawa trafila do `Najważniejsze dziś`.

If this view becomes request-heavy or needs richer cross-module signals, the next backend step should be a separate read-only endpoint such as:

- `GET /api/operations/today?organization_id=...`

That endpoint should be added only after live usage shows the current frontend-side aggregation is insufficient.

## Tests

Covered by:

- `frontend/scripts/test-daily-brief.js`
- `frontend/scripts/test-all.js`
- `python run_quality_checks.py --profile frontend-smoke`

Test modelowy sprawdza grupowanie, priorytetyzacje, blokade bez organizacji, kontrakt tylko do odczytu, linki, empty state, polskie etykiety sekcji i redakcje pol technicznych.
