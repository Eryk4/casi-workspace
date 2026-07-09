# Next Modules Status

Last checked: 2026-07-03

This document tracks the active Next.js frontend in `frontend/`. The legacy UI in `static/` is not the source of truth and is not covered here.

## Summary

- Active frontend source of truth: `frontend/`.
- Legacy frontend: `static/`, compatibility only.
- Main AppShell and organization selector exist.
- Organization context storage key: `casi.activeOrganizationId`.
- Standard frontend quality profile: `python run_quality_checks.py --profile frontend-smoke`.
- `frontend-smoke` runs `npm.cmd run typecheck`, `npm.cmd run test:models`, and `npm.cmd run build`.
- First low-risk write paths exist in Work Items, invoice comments, and additive CRM contractor notes.
- Current write paths and their tenant-scope/security status are tracked in `frontend/docs/WRITE_ACTIONS_STATUS.md`.
- CRM write readiness is documented in `frontend/docs/CRM_ACTIONS_READINESS.md`; CRM now has only one narrow write action in Next: adding a contractor note. Contractor master data remains read-only.
- `Pulpit dnia` is documented in `frontend/docs/PULPIT_DNIA_PRODUCT_NOTE.md` and is the first product v1 daily triage screen assembled from existing organization-scoped sources. Current local data is only a safe sandbox for development and verification.
- `Karta sprawy` is documented in `frontend/docs/WORK_ITEM_CONTEXT_PRODUCT_NOTE.md` and is the second product v1 read-only screen, available at `/work-items/[workItemId]`.
- `Centrum kontrahenta` is documented in `frontend/docs/CONTRACTOR_CENTER_PRODUCT_NOTE.md` and turns `/crm/[contractorId]` into a product v1 relationship view for contractor facts, invoices, open matters, documents, and CRM notes.
- `Centrum faktury` is documented in `frontend/docs/INVOICE_CENTER_PRODUCT_NOTE.md` and turns `/faktury/[invoiceId]` into a product v1 invoice context screen with contractor, matters, documents, comments, and sanitized system history.
- `Centrum dokumentu` is documented in `frontend/docs/DOCUMENT_CENTER_PRODUCT_NOTE.md` and turns `/dokumenty/[documentId]` into a product v1 read-only context screen for document profile, source trace, versions, comments, activity, and related matters.
- `Rozliczenia` is the canonical billing module. `/rozliczenia` is the product route and now hosts `Centrum rozliczeÄąâ€ž` product v1; `/kasa` is only a legacy redirect and must not be developed as a separate screen. V1 is a read-only foundation for a future full settlement module covering clients, students, families, payers, services, enrollments, pricing, discounts, periods, charges, payments, allocations, arrears, reminders, owner reports, and accounting export. The current services/enrollments, billing-period, payments/allocation, payment-detail, debts/overpayments, and billing work queue foundations are inferred from existing charges, models, invoices, contractors, transactions, matched payments, payer notes, payment operational statuses, and billing contact events. Billing now has four narrow additive write paths: payer notes, payment operational review status, billing work queue decisions, and billing contact draft/log events. The full target domain plan is documented in `docs/FULL_CLIENT_BILLING_DOMAIN_PLAN.md`.
- Environment and data safety rules are documented in `docs/ENVIRONMENT_AND_DATA_SAFETY.md`.

## Module Matrix

| Module | Route | Screen status | Live API | Requires organization | `organization_id` connected | Read-only | Write actions | Tests | Recommended next step |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Dashboard / Pulpit | `/pulpit` | Real operational dashboard | Yes, `GET /api/dashboard` | Yes | Yes | Yes | No | `test-dashboard.js` | Keep stable; use as org-scoped landing page. |
| Pulpit dnia | `/pulpit-dnia` | Product v1 daily triage screen with balanced top priorities | Yes, dashboard/tasks/work-items/invoices/billing/contractors/documents | Yes | Yes for all current sources | Yes | No | `test-daily-brief.js` | Keep stable as the first morning overview; add a read-only backend aggregator only if frontend-side aggregation becomes too request-heavy. |
| Faktury | `/faktury`, `/faktury/[invoiceId]` | Real invoice inbox and product v1 invoice center | Yes, invoice inbox/detail/comment endpoints plus existing Work Items list for related open matters | Yes | Yes | Mostly read-only; one additive comment form | Yes: add operator comment only | `test-invoices.js` | Keep comments stable; do not expose workflow decisions until state-specific UX and permissions are reviewed. |
| Work Items | `/work-items`, `/work-items/[workItemId]` | Real operational work queue and read-only case card | Yes, list/detail/action endpoints | Yes | Yes | List has write actions; case card is read-only | Yes on list only: assign to self, snooze, close | `test-work-items.js`, `test-work-item-detail.js` | Keep the case card stable; local sandbox seed now includes realistic Work Items for positive validation. Consider a read-only context endpoint only if existing detail payload is too thin. |
| Dokumenty / Knowledge | `/dokumenty`, `/dokumenty/[documentId]` | Real document list and product v1 document center | Yes, document list/detail endpoints plus existing Work Items list for context | Yes | Yes | Yes | No | `test-documents.js`, `test-document-detail.js` | Keep read-only; add a dedicated read-only context endpoint only if frontend-side relationship assembly becomes too thin or too request-heavy. |
| Rozliczenia | `/rozliczenia`, `/rozliczenia/okresy`, `/rozliczenia/wplaty`, `/rozliczenia/wplaty/[paymentId]`, `/rozliczenia/zaleglosci`, `/rozliczenia/sprawy`, `/rozliczenia/platnicy/[payerId]` | Product v1 billing center for money, payments, receivables, contractors, invoices, and related matters; includes payer/family/student foundation, balance explanations, payer detail, services/enrollments, billing-period view, payments/allocation foundation, payment detail, debts/overpayments decision center, read-only billing work queue, additive payer notes, and payment operational status | Yes, billing ledger balances, billing transactions, billing ledger matches, billing payers/students/charges/notes, payment review status, invoices, contractors, and Work Items | Yes | Yes for all current sources | Financial state is read-only; payer detail has one additive note form; payment detail has one additive operational status form; billing work queue has append-only handled/snoozed decisions; payer detail has contact draft/log events that do not send messages | Yes: add billing payer note, payment operational status, work queue decision, and billing contact event only | `test-billing.js`, `tests/test_billing_notes_http.py`, `tests/test_billing_payment_review_status_http.py` | Keep payer notes and payment operational status stable; do not expose payment imports, allocations, reminders, charge generation, or accounting exports until endpoint-specific UX, permissions, payload hardening, and live verification are complete. |
| Asystent Szefa | `/asystent-szefa` | Real read-only focus snapshot | Yes, `GET /api/tasks/focus` | Yes | Yes | Yes | No | `test-boss-assistant.js` | Keep read-only; live-verify org-scoped focus data with a global user. |
| Asystent Firmowy | `/asystent-firmowy` | Real read-only company context foundation | Yes, dashboard/documents/work-items/invoice inbox | Yes | Yes | Yes | No | `test-company-assistant.js` | Live-verify org-scoped empty/data states; do not add chat before agent contract exists. |
| CRM | `/crm`, `/crm/[contractorId]` | Real contractor catalog and product v1 contractor center | Yes, contractor list/detail/note endpoints plus existing Work Items list for related open matters | Yes | Yes | Contractor master data is read-only | Yes: add contractor note only | `test-crm.js`, `test-contractor-detail.js` | Live-verify the contractor center for two organizations; improve relationship data before adding new CRM actions. |
| Raporty | `/raporty` | Real aggregated read-only operational report | Yes, dashboard/work-items/documents/billing/contractors | Yes | Yes for all report sources | Yes | No | `test-reports.js` | Keep as verification surface for org scope; later add export only after BI/export contract. |
| Ustawienia | `/ustawienia` | Real read-only account/environment/org overview | Yes, session/meta/organizations/users | Not required for current read-only admin/account view | Not applicable | Yes | No | `test-settings.js` | Keep unblocked by active organization; add org scope only for future organization-specific edit screens. |

## Organization Scope Status

Modules with active organization connected:

- Dashboard / Pulpit
- Pulpit dnia
- Faktury
- Work Items
- Dokumenty / Knowledge, including read-only `Centrum dokumentu` at `/dokumenty/[documentId]`
- Rozliczenia, including product v1 `Centrum rozliczeĹ„` at `/rozliczenia`, payer detail at `/rozliczenia/platnicy/[payerId]`, billing periods at `/rozliczenia/okresy`, payments/allocation read-only view at `/rozliczenia/wplaty`, payment detail at `/rozliczenia/wplaty/[paymentId]`, debts/overpayments at `/rozliczenia/zaleglosci`, and the read-only work queue at `/rozliczenia/sprawy`
- CRM contractor master data
- Raporty
- Asystent Szefa
- Asystent Firmowy

Modules that should get organization scope next:

- None among current real modules.

Modules where active organization is intentionally not required right now:

- Ustawienia, because the current screen is a read-only account/session/environment/organizations overview. It should become organization-scoped only when it starts editing or displaying organization-specific settings.

## Read-only And Write Actions

Read-only screens:

- Dashboard / Pulpit
- Pulpit dnia
- Dokumenty / Knowledge, including read-only `Centrum dokumentu` at `/dokumenty/[documentId]`
- Rozliczenia, including product v1 `Centrum rozliczeĹ„` at `/rozliczenia`, payer detail at `/rozliczenia/platnicy/[payerId]`, billing periods at `/rozliczenia/okresy`, payments/allocation read-only view at `/rozliczenia/wplaty`, payment detail at `/rozliczenia/wplaty/[paymentId]`, debts/overpayments at `/rozliczenia/zaleglosci`, and the read-only work queue at `/rozliczenia/sprawy`
- Asystent Szefa
- Asystent Firmowy
- CRM
- Raporty
- Ustawienia

Screens with real write actions:

- Work Items list.
- Faktury, only the additive operator comment on invoice detail.
- CRM, only the additive contractor note on contractor detail.
- Rozliczenia, only the additive billing payer note on payer detail, additive contact draft/log event on payer detail, additive payment operational status on payment detail, and append-only billing work queue decision on `/rozliczenia/sprawy`.

Current Work Items write actions:

- `POST /api/work-items/{id}/assign`
- `POST /api/work-items/{id}/snooze`
- `POST /api/work-items/{id}/close`

The Work Item case card at `/work-items/[workItemId]` is read-only and does not expose these actions.

Current invoice write action:

- `POST /api/invoices/{id}/comments?organization_id=...`

Current CRM write action:

- `POST /api/contractors/{id}/notes?organization_id=...`

Current billing write actions:

- `POST /api/billing/payers/{payerId}/notes?organization_id=...`
- `POST /api/billing/payments/{paymentId}/review-status?organization_id=...`
- `POST /api/billing/work-queue/events?organization_id=...`
- `POST /api/billing/contact-events?organization_id=...`

Billing payer notes accept only `{ note_text }`, require active organization scope, do not change balances, charges, payments, allocations, reminders, imports, or accounting state, and system events store only note metadata.

Payment operational status accepts only `{ status, note_text? }`, requires active organization scope, stores an additive review event, does not change transactions, charges, matches, ledger entries, balances, imports, reminders, or accounting state, and system events store only status metadata plus note length.

Billing work queue decisions accept only `{ issue_key, issue_type, target_type, target_id, action, note_text? }`, require active organization scope, store append-only `handled`/`snoozed` events, and do not change transactions, charges, matches, ledger entries, balances, imports, reminders, task manager items, or accounting state.

Invoice decision helpers still exist in the frontend model/API layer and are covered by tests for `preview-ready` semantics. The product v1 invoice center does not render workflow decision buttons; only the additive operator comment form is visible.

## Placeholder Status

Current placeholder / blueprint screen:

- None in the main navigation.

Reusable placeholder component still exists:

- `frontend/src/modules/shared/ModulePlaceholder.tsx`

The placeholder component is retained only as a reusable fallback for future planned modules. It should not be treated as production behavior for current navigation items.

## Test Coverage

Frontend model runner:

- `frontend/scripts/test-all.js`

Covered tests:

- `test-dashboard.js`
- `test-daily-brief.js`
- `test-organization-context.js`
- `test-invoices.js`
- `test-work-items.js`
- `test-work-item-detail.js`
- `test-documents.js`
- `test-document-detail.js`
- `test-billing.js`
- `test-boss-assistant.js`
- `test-company-assistant.js`
- `test-crm.js`
- `test-contractor-detail.js`
- `test-reports.js`
- `test-settings.js`

Current frontend smoke command:

```bash
python run_quality_checks.py --profile frontend-smoke
```

## Recommended Next Small Steps

1. Keep `/pulpit-dnia` stable as product v1 and use it as the first morning overview during local sandbox verification.
2. For `Rozliczenia`, keep the family/payer/student, balance, services, payer-detail, period, payments/allocation, payment-detail views, additive payer notes, and payment operational status stable; do not add payment imports, allocation writes, reminders, period closing, charge generation, or exports before a separate endpoint-specific design.
3. Keep invoice comments as the only invoice write until workflow decision UX, permissions, and state-specific confirmations are reviewed.

Billing contact events accept only { payer_id, related_payment_id?, related_issue_key?, channel, contact_action, message_text?, note_text? }, require active organization scope, validate payer/payment scope, and do not send SMS/e-mail or change transactions, charges, matches, ledger entries, balances, imports, reminders, exports, or accounting state.

## Rozliczenia - centrum kontaktow rozliczeniowych

`/rozliczenia/kontakty` jest read-only centrum kontaktow rozliczeniowych. Korzysta z istniejacych wpisow kontaktowych, pokazuje przygotowane tresci, deklaracje platnosci, brak odpowiedzi i wpisy wymagajace ponownego kontaktu. Ekran nie dodaje nowych write actions, nie wysyla wiadomosci i nie zmienia danych finansowych.

## Rozliczenia — raport operacyjny

`/rozliczenia/raport` jest read-only raportem operacyjnym dla właściciela firmy. Zbiera zaległości, nadpłaty, wpłaty, sprawy i kontakty rozliczeniowe z istniejących danych organizacji. Nie jest dokumentem księgowym, nie generuje PDF/XLSX, nie wysyła wiadomości i nie zmienia finansów.
