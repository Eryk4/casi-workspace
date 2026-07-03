# CRM Notes Backend Readiness

Last checked: 2026-07-02

This document tracks the backend foundation for the safest first CRM write action: an additive note on a contractor. The backend table, repository/service, HTTP endpoint, SQLite -> PostgreSQL migrator support, and Next contractor detail form are implemented.

## Current State

The active Next.js CRM module keeps contractor master data read-only and now exposes one additive note form on contractor detail:

- `GET /api/contractors?organization_id=...`
- `GET /api/contractors/{contractorId}?organization_id=...`, now including `notes`
- `POST /api/contractors/{contractorId}/notes?organization_id=...`, used by `/crm/{contractorId}`

The backend has internal contractor mutations through `ContractorRepository.create(...)`, `ContractorRepository.update(...)`, and `ContractorRepository.refresh_invoice_stats(...)`, but those are used by invoice ingestion/update flows and are not public CRM write actions.

## Does A Contractor Notes Table Exist?

Yes. `contractor_notes` exists as an additive table.

The previous audit checked names and patterns including:

- `contractor_notes`
- `contractor_comments`
- `crm_notes`
- `contact_notes`
- existing comment/note patterns such as `invoice_comments`, `knowledge_document_comments`, and `task_notes`

The existing `contractors.notes` column remains a single contractor field and is not used by the new note endpoint. Contractor notes are appended to `contractor_notes` and do not mutate contractor master data.

## Existing Patterns To Reuse

The closest existing backend pattern is invoice comments:

- schema: `invoice_comments`
- repository methods: `InvoiceRepository.add_comment(...)`, `InvoiceRepository.list_comments(...)`
- service method: `InvoiceService.add_invoice_comment(...)`
- HTTP route: `POST /api/invoices/{invoiceId}/comments?organization_id=...`
- response: `201` with the created comment

Knowledge document comments and task notes show similar additive patterns, but invoice comments are the best match for a business-detail screen with operator notes.

## Implemented API Contract

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
  "author_user_id": 1,
  "author_user_name": "Operator",
  "author_user_role": "operator",
  "created_at": "2026-07-02T12:00:00"
}
```

Error responses:

- `400` when `note_text` is empty or longer than the accepted limit.
- `401` when the user is not authenticated.
- `403` when the user has no access/write permission for the organization.
- `404` when the contractor does not exist in the selected organization.

## Implemented Minimal Schema

Use an additive table instead of mutating `contractors.notes`.

SQLite:

```sql
CREATE TABLE IF NOT EXISTS contractor_notes (
    contractor_note_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    contractor_id INTEGER NOT NULL,
    author_user_id INTEGER NOT NULL,
    note_text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (contractor_id) REFERENCES contractors(contractor_id) ON DELETE CASCADE,
    FOREIGN KEY (author_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_contractor_notes_contractor_id
    ON contractor_notes(contractor_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_contractor_notes_organization_id
    ON contractor_notes(organization_id);
```

PostgreSQL:

```sql
CREATE TABLE IF NOT EXISTS contractor_notes (
    contractor_note_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    contractor_id BIGINT NOT NULL,
    author_user_id BIGINT NOT NULL,
    note_text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    CONSTRAINT fk_contractor_notes_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_contractor_notes_contractor
        FOREIGN KEY (contractor_id) REFERENCES contractors(contractor_id) ON DELETE CASCADE,
    CONSTRAINT fk_contractor_notes_author
        FOREIGN KEY (author_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_contractor_notes_contractor_id
    ON contractor_notes(contractor_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_contractor_notes_organization_id
    ON contractor_notes(organization_id);
```

`updated_at` and `deleted_at` are intentionally omitted for the first version. The first action should only add notes. Edit/delete can be planned later if a clear audit model exists.

## Implemented Backend Changes

Implemented files:

- `app/db.py`: SQLite/PostgreSQL schema and ensure function for `contractor_notes`.
- `app/repositories/contractor_repository.py`: `add_note(...)` and `list_notes(...)`.
- `app/services/invoice_service.py`: `add_contractor_note(...)` and contractor detail notes.
- `app/api/http_server.py`: `POST /api/contractors/{contractorId}/notes`.
- `migrate_sqlite_to_configured_db.py`: `contractor_notes` in `TABLE_ORDER`, `ORDER_COLUMNS`, and `POSTGRES_SEQUENCES`.
- `tests/http_server_test_methods.py`: HTTP coverage for success, invalid payloads, no session, and organization access.
- `tests/invoice_test_methods.py`: service coverage for additivity and no invoice/billing side effects.
- `tests/test_sqlite_to_configured_db_migrator.py`: migrator coverage for the new table.
- `scripts/audit_database_migration.py`: `contractor_notes` classified as critical operational data.
- `docs/DATABASE_MIGRATION_AUDIT.md`: current counts updated after adding the table.
- `frontend/docs/CRM_ACTIONS_READINESS.md`: state updated after backend implementation.

## Security And Business Rules

The endpoint must enforce:

- contractor must exist in the selected organization,
- global users must pass `organization_id`,
- user must have organization access,
- write permission should use the same conservative write-scope pattern as other small write actions,
- `note_text` must be trimmed,
- empty `note_text` must be rejected,
- maximum length should be 2000 characters unless backend standards choose a stricter limit,
- note text must not be logged as secret/debug output,
- adding a note must not update contractor master fields,
- adding a note must not update invoices,
- adding a note must not update billing/ledger records,
- adding a note must not send email, trigger AI, or call external services.

## Required Tests

Backend tests cover:

- successful `POST /api/contractors/{id}/notes?organization_id=...` returns `201`,
- payload is only `{ "note_text": "..." }`,
- note is visible in contractor detail or via a dedicated read path,
- empty note returns `400`,
- too long note returns `400`,
- missing session returns `401`,
- missing/invalid organization scope is rejected through existing write-scope handling,
- user from another organization cannot add the note,
- contractor from another organization is protected by organization scope,
- adding a note does not change contractor fields,
- adding a note does not change invoice records,
- adding a note does not change billing records,
- migrator includes `contractor_notes` in order after `contractors`, `organizations`, and `users`,
- database migration audit remains green after the table is added.

Frontend tests now cover request payload, organization scope, validation, loading/error/success behavior, and the no-false-success path for the CRM detail form.

## Risk Assessment

Adding `contractor_notes` is low-risk because it is implemented as a strictly additive table and endpoint.

Remaining risks:

- accidentally mutating `contractors.notes` instead of appending to `contractor_notes`,
- leaking notes across organizations,
- expanding from additive notes into contractor master-data edits before separate permission and audit rules exist.

## Safe Implementation Order

1. Backend foundation: complete.
2. Backend checks and database migration audit: complete.
3. Next UI form on `/crm/{contractorId}`: complete.
4. Frontend model tests for request payload, organization scope, and no false success: complete.
5. Live verification in the browser after UI implementation: next step.

## What Not To Do Yet

Do not implement in the next CRM step:

- contractor create/edit/delete,
- editing notes,
- deleting notes,
- CRM pipeline,
- contact import,
- follow-up automation,
- AI summaries,
- invoice linking,
- billing changes,
- external notifications.

## Readiness Decision

The backend note action is ready for a small Next UI step. The future UI must stay limited to adding an operator note on contractor detail and must not introduce edit/delete, pipeline, automation, import, invoice linking, or broader CRM workflows.
