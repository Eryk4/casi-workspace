# CRM Actions Readiness

Last checked: 2026-07-02

This audit covers the active Next.js frontend in `frontend/` and the existing backend CRM/contractor API. The first CRM write action is now implemented in the Next UI: an additive contractor note form on `/crm/{contractorId}`. The backend foundation for the note endpoint is documented in `docs/CRM_NOTES_BACKEND_READINESS.md`.

## Current CRM Surface

CRM currently has a real read-only list and contractor detail:

- `GET /api/contractors?organization_id=...`
- `GET /api/contractors/{contractorId}?organization_id=...`, including additive notes
- `POST /api/contractors/{contractorId}/notes?organization_id=...`, wired to the contractor detail UI

The read routes are organization-scoped through the backend data-scope resolver and are already used by the Next CRM screens. The note write endpoint is organization-scoped through the backend write-scope resolver and the Next UI calls it only with an active organization.

## Existing Mutating CRM / Contractor Endpoints

One public additive CRM note endpoint now exists. It is intentionally narrow and does not mutate contractor master data.

| Endpoint | Status | `organization_id` | Payload | Database effect | Risk as first CRM action |
| --- | --- | --- | --- | --- | --- |
| `POST /api/contractors/{id}/notes` | Implemented in backend and wired to Next UI | Required query param for global/multi-org scope | `{ "note_text": "..." }` only | Inserts into `contractor_notes` | Implemented first CRM action; keep additive and narrow. |
| `POST /api/contractors/{id}/comments` | Not implemented | Not applicable | Not applicable | None | Cannot be used until backend contract and tests exist. |
| `PATCH /api/contractors/{id}` | Not implemented as public HTTP API | Not applicable | Not applicable | None through HTTP | Do not expose broad contractor edits as the first CRM write. |
| `POST /api/contractors` | Not implemented as public HTTP API | Not applicable | Not applicable | None through HTTP | Do not expose contractor creation before validation, duplicate, and permission rules are reviewed. |

## Internal Contractor Mutations

The backend does mutate contractor records internally, but not through a direct CRM endpoint:

- `ContractorRepository.create(...)` can create a contractor.
- `ContractorRepository.update(...)` can update contractor fields.
- `ContractorRepository.refresh_invoice_stats(...)` updates invoice counters and latest invoice metadata.
- `InvoiceService` calls these paths while creating or updating invoices and while syncing invoice-derived contractor data.

These are not safe first CRM actions for the Next UI because they are coupled to invoice ingestion/editing, invoice statistics, and business master data.

## Risk Assessment

Direct contractor create/edit/delete is not recommended as the first CRM write because it can affect master data used by invoices, reporting, search, linked tasks, and future billing flows.

Invoice-derived contractor mutation is also not a CRM action. It belongs to invoice ingestion and invoice correction workflows, not a low-risk CRM UI step.

The additive contractor note endpoint is now the only safe CRM write action in Next. Broader contractor mutation remains too risky for the next CRM step.

## Recommendation

The implemented first CRM UI action is an additive contractor note/comment using the backend contract:

```http
POST /api/contractors/{contractorId}/notes?organization_id={activeOrganizationId}
Content-Type: application/json

{
  "note_text": "Krotka notatka operatora"
}
```

Success response:

```http
201 Created
```

```json
{
  "contractor_note_id": 1,
  "contractor_id": 31,
  "organization_id": 1,
  "note_text": "Krotka notatka operatora",
  "created_at": "2026-07-02T12:00:00",
  "author_user_id": 1,
  "author_user_name": "Operator",
  "author_user_role": "operator"
}
```

Expected errors:

- `400` for empty or too long note text.
- `401` for missing session.
- `403` for missing organization access or missing write permission.
- `404` for contractor not found in the selected organization.

## Backend And Frontend Tests

Backend coverage exists for:

- successful note creation with `organization_id`,
- empty note rejection,
- organization isolation,
- missing session rejection,
- note visibility in contractor detail,
- no mutation of contractor master fields, invoices, billing, or status.

Frontend model coverage exists for:

- `organization_id` in the note request,
- payload limited to `{ "note_text": "..." }`,
- empty note rejection,
- missing organization rejection,
- 2000 character limit,
- loading/error/success submitter behavior,
- no false success without backend confirmation,
- no create/edit/delete/import/pipeline CRM actions.

## What Not To Implement Yet

Do not implement these as the first CRM write:

- contractor create,
- contractor edit,
- contractor delete,
- contractor import,
- CRM pipeline,
- contact history automation,
- invoice linking,
- status changes,
- email follow-up,
- AI-generated CRM actions.

## UI Conditions Before Implementation

The Next UI now:

- show the form only with an active organization,
- send only `{ "note_text": "..." }`,
- include `organization_id` as a query param,
- block empty notes,
- use a reasonable text length limit matching backend validation,
- show loading/error/success locally around the form,
- clear the field only after backend confirmation,
- refresh contractor detail after backend confirmation,
- avoid false success without backend confirmation.
