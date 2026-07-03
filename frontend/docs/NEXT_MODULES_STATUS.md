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
- Environment and data safety rules are documented in `docs/ENVIRONMENT_AND_DATA_SAFETY.md`.

## Module Matrix

| Module | Route | Screen status | Live API | Requires organization | `organization_id` connected | Read-only | Write actions | Tests | Recommended next step |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Dashboard / Pulpit | `/pulpit` | Real operational dashboard | Yes, `GET /api/dashboard` | Yes | Yes | Yes | No | `test-dashboard.js` | Keep stable; use as org-scoped landing page. |
| Pulpit dnia | `/pulpit-dnia` | Product v1 daily triage screen with balanced top priorities | Yes, dashboard/tasks/work-items/invoices/billing/contractors/documents | Yes | Yes for all current sources | Yes | No | `test-daily-brief.js` | Keep stable as the first morning overview; add a read-only backend aggregator only if frontend-side aggregation becomes too request-heavy. |
| Faktury | `/faktury`, `/faktury/[invoiceId]` | Real invoice inbox, detail preview, and operator comments | Yes, invoice inbox/detail/comment endpoints | Yes | Yes | Mostly read-only; one additive comment form | Yes: add operator comment only | `test-invoices.js` | Keep comments stable; do not expose workflow decisions until state-specific UX and permissions are reviewed. |
| Work Items | `/work-items` | Real operational work queue | Yes, `GET /api/work-items` and action endpoints | Yes | Yes | No | Yes: assign to self, snooze, close | `test-work-items.js` | Live-verify more tenant cases and then consider one next low-risk action. |
| Dokumenty / Knowledge | `/dokumenty`, `/dokumenty/[documentId]` | Real read-only document list and detail | Yes, document list/detail endpoints | Yes | Yes | Yes | No | `test-documents.js`, `test-document-detail.js` | Keep read-only until upload/edit/storage contracts are reviewed. |
| Kasa | `/kasa` | Real read-only billing ledger view via shared component | Yes, `GET /api/billing/ledger/balances` | Yes | Yes | Yes | No | `test-billing.js` | Keep paired with Rozliczenia; no write actions before import/matching contracts are reviewed. |
| Rozliczenia | `/rozliczenia` | Real read-only billing ledger view via shared component | Yes, `GET /api/billing/ledger/balances` | Yes | Yes | Yes | No | `test-billing.js` | Same as Kasa; next step should be contract audit before any payment action. |
| Asystent Szefa | `/asystent-szefa` | Real read-only focus snapshot | Yes, `GET /api/tasks/focus` | Yes | Yes | Yes | No | `test-boss-assistant.js` | Keep read-only; live-verify org-scoped focus data with a global user. |
| Asystent Firmowy | `/asystent-firmowy` | Real read-only company context foundation | Yes, dashboard/documents/work-items/invoice inbox | Yes | Yes | Yes | No | `test-company-assistant.js` | Live-verify org-scoped empty/data states; do not add chat before agent contract exists. |
| CRM | `/crm`, `/crm/[contractorId]` | Real contractor catalog and detail with additive notes | Yes, contractor list/detail/note endpoints | Yes | Yes | Contractor master data is read-only | Yes: add contractor note only | `test-crm.js`, `test-contractor-detail.js` | Live-verify note form; do not expose edit/delete/import/pipeline before separate contract audits. |
| Raporty | `/raporty` | Real aggregated read-only operational report | Yes, dashboard/work-items/documents/billing/contractors | Yes | Yes for all report sources | Yes | No | `test-reports.js` | Keep as verification surface for org scope; later add export only after BI/export contract. |
| Ustawienia | `/ustawienia` | Real read-only account/environment/org overview | Yes, session/meta/organizations/users | Not required for current read-only admin/account view | Not applicable | Yes | No | `test-settings.js` | Keep unblocked by active organization; add org scope only for future organization-specific edit screens. |

## Organization Scope Status

Modules with active organization connected:

- Dashboard / Pulpit
- Pulpit dnia
- Faktury
- Work Items
- Dokumenty / Knowledge
- Kasa
- Rozliczenia
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
- Dokumenty / Knowledge
- Kasa
- Rozliczenia
- Asystent Szefa
- Asystent Firmowy
- CRM
- Raporty
- Ustawienia

Screens with real write actions:

- Work Items.
- Faktury, only the additive operator comment on invoice detail.
- CRM, only the additive contractor note on contractor detail.

Current Work Items write actions:

- `POST /api/work-items/{id}/assign`
- `POST /api/work-items/{id}/snooze`
- `POST /api/work-items/{id}/close`

Current invoice write action:

- `POST /api/invoices/{id}/comments?organization_id=...`

Current CRM write action:

- `POST /api/contractors/{id}/notes?organization_id=...`

Invoice decision helpers exist in the frontend model/API layer, but the visible invoice decision UI remains preview/read-only and does not submit workflow/status decisions from the screen.

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
2. Keep invoice comments as the only invoice write until workflow decision UX, permissions, and state-specific confirmations are reviewed.
3. Continue live-verifying organization-scoped screens after each small write addition, especially global-user and stale `casi.activeOrganizationId` cases.
