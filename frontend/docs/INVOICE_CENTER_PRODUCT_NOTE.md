# Centrum faktury v1

Status: product v1 screen on `/faktury/{invoiceId}`.

`Centrum faktury` is a real CASI business screen, not a demo or a workflow mockup. Its purpose is to let an operator understand one invoice in context before deciding what should happen next in the business process.

## Problem Solved

The invoice inbox shows what needs attention, but a single invoice needs more context:

- who the contractor is,
- whether the invoice has comments or operational signals,
- which Work Items or tasks are connected,
- whether there are related documents,
- what the system history says without exposing technical payloads.

`Centrum faktury` consolidates that context in one place.

## Current Data Sources

The screen uses existing organization-scoped read paths:

- `GET /api/invoices/{invoiceId}?organization_id=...` for invoice detail, contractor context, linked tasks, document intake items, comments, history, and safe document trace.
- `GET /api/work-items?organization_id=...` for related open Work Items when metadata links them to the invoice.

No backend endpoint was added for this step. A future read-only relation endpoint may be justified only if the frontend aggregation becomes too heavy or too incomplete.

## Screen Sections

- `Profil faktury` - headline summary, amount, contractor, and basic invoice facts.
- `Podsumowanie relacji` - workflow/status context shown as read-only information.
- `Kontrahent` - contractor facts and a link to `/crm/{contractorId}` when a contractor is known.
- `Sprawy do uwagi` - related Work Items with links to `/work-items/{workItemId}`.
- `Zadania i kontekst operacyjny` - linked task context returned by the invoice detail endpoint.
- `Dokumenty` - related document/intake context with links to `/dokumenty/{documentId}` only when a safe document id exists.
- `Komentarz operatora` - the existing additive operator comment form.
- `Komentarze operatora` - comments displayed separately from system history.
- `Historia systemowa` - sanitized system history without full comment text, raw payloads, storage keys, or local paths.
- `Kontekst biznesowy` - short deterministic signals explaining what the invoice means now.

## Write Scope

The screen remains read-only except for the existing low-risk additive write:

```http
POST /api/invoices/{invoiceId}/comments?organization_id=...
```

Payload:

```json
{ "note_text": "Krótka notatka operatora" }
```

This action does not change invoice amount, status, workflow, KSeF data, OCR data, duplicate state, handoff state, contractor master data, billing, or external integrations.

The screen intentionally does not expose:

- mark-ready,
- handoff,
- close/reopen,
- duplicate decision actions,
- PATCH invoice editing,
- batch actions,
- KSeF/OCR/export flows.

## Safety Rules

The UI must not show:

- `storage_key`,
- `data/magazyn`,
- local paths such as `C:\Users\...`,
- secrets,
- tokens,
- connection strings,
- raw JSON or technical payloads.

System history should explain what happened without duplicating full operator comment text. Operator comments belong in the comments section.

## Limitations

- Related Work Items are resolved from the existing Work Items list and metadata.
- Related document links are shown only when the invoice detail payload contains a safe document id.
- The screen does not implement workflow decisions yet.
- The screen does not replace a future invoice approval UX.

## Next Safe Steps

1. Live-verify `/faktury/{invoiceId}` for at least two organizations after the next local sandbox refresh.
2. Keep operator comments as the only invoice write until workflow decision permissions and UX are reviewed.
3. Consider a read-only invoice context endpoint only if relation aggregation from existing endpoints becomes too costly or incomplete.
