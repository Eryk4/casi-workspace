# Pulpit Dnia Product Note

Last checked: 2026-07-03

`Pulpit dnia` is a read-only operational view in the active Next frontend. Its product question is:

> Co dzisiaj wymaga mojej uwagi?

This screen is not an AI agent, not a workflow engine, and not a write surface. It is a deterministic daily triage view assembled from existing organization-scoped read APIs.

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

No new backend aggregation endpoint was added because the existing endpoints are enough for the first read-only version.

## Sections

The screen groups signals into:

- Najwazniejsze dzis
- Sprawy pilne
- Faktury i finanse
- Kontrahenci
- Dokumenty
- Mozna odlozyc

Prioritization is deterministic and based on existing fields such as severity, priority, SLA state, invoice inbox sections, balance due, document status, and CRM freshness/contact gaps.

The `Najwazniejsze dzis` section is intentionally balanced. It is not a pure score ranking, because one noisy domain could otherwise dominate the morning view. Current rules:

- maximum 7 items,
- maximum 2 invoice items,
- maximum 2 task/work-item items,
- maximum 1 finance item,
- maximum 1 CRM item,
- maximum 1 document item,
- maximum 1 other operational alert,
- first pass tries to include a mix of tasks, invoices, CRM, documents, finance, and other signals,
- second pass fills remaining slots by priority while respecting category limits.

Invoice duplicates and invoice exceptions remain visible in `Faktury i finanse`, but only the strongest invoice signals can enter `Najwazniejsze dzis`.

`Mozna odlozyc` tries to surface low-urgency work items, stable contractors, calm documents, low-priority reminders, and settled billing signals. If there is truly nothing calm to show, the UI uses a product empty state instead of a technical error-like message.

## Local Sandbox Scenario

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

- `Wybierz organizacje, aby zobaczyc Pulpit dnia`

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

Allowed interactions are navigation links to existing module screens and refresh.

## Known Data Gaps

The first version intentionally avoids extra detail requests and backend changes. Therefore:

- CRM uses contractor list signals, not a full recent-note stream.
- Documents use list/dashboard status fields, not comments or version actions.
- Finance uses ledger balances, not bank import or matching write flows.
- Invoice signals use verification inbox and links to detail, not workflow decisions.
- Existing local databases seeded before the sandbox-data cleanup can still contain older titles until the local sandbox database is reset/reseeded. This document describes the intended fresh sandbox scenario.

Before a real pilot, the biggest remaining product gaps are:

- a stable read-only backend aggregation endpoint if frontend-side aggregation becomes too chatty,
- client-specific sandbox scenarios that reflect the pilot customer's actual operating rhythm without using production data,
- better recent-activity signals for CRM notes, document changes, and invoice comments,
- a clear owner-facing explanation for why each item landed in `Najwazniejsze dzis`.

If this view becomes request-heavy or needs richer cross-module signals, the next backend step should be a separate read-only endpoint such as:

- `GET /api/operations/today?organization_id=...`

That endpoint should be added only after live usage shows the current frontend-side aggregation is insufficient.

## Tests

Covered by:

- `frontend/scripts/test-daily-brief.js`
- `frontend/scripts/test-all.js`
- `python run_quality_checks.py --profile frontend-smoke`

The model test checks grouping, prioritization, organization blocking, read-only contract, links, empty state, and technical-field redaction.
