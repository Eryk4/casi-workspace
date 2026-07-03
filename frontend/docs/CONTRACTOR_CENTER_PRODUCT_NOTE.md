# Centrum kontrahenta Product Note

Last checked: 2026-07-03

`/crm/[contractorId]` is the product v1 contractor center in the active Next.js frontend. It is a normal business screen, not a demo or a raw API preview.

## Purpose

The screen answers one operational question:

> What do we currently know about this contractor, and what matters around this relationship?

It should help an owner or operator quickly understand:

- who the contractor is,
- whether there are open operational matters,
- which invoices are connected,
- whether there are related documents,
- what recent CRM notes say,
- whether the relationship needs attention today.

## Data Sources

The screen uses existing organization-scoped sources:

- `GET /api/contractors/{contractorId}?organization_id=...` for contractor master data, invoices, linked tasks, and notes.
- `GET /api/work-items?organization_id=...&only_open=1&limit=100` for open Work Items related through existing metadata.

No new backend endpoint was added for this v1.

## Sections

The screen renders:

- `Profil kontrahenta` - core contractor facts and organization context.
- `Podsumowanie relacji` - counts and short risk signal.
- `Sprawy do uwagi` - related open Work Items with links to `/work-items/{id}`.
- `Faktury i rozliczenia` - related invoices with links to `/faktury/{id}`.
- `Dokumenty` - documents inferred from related Work Item metadata with links to `/dokumenty/{id}`.
- `Notatki CRM` - existing additive CRM note form and existing notes.
- `Kontekst biznesowy` - short interpretation of the relationship and screen boundaries.

## Write Scope

The contractor master data remains read-only.

The only write action visible on this screen is the already existing additive CRM note:

- `POST /api/contractors/{contractorId}/notes?organization_id=...`
- payload: `{ "note_text": "..." }`

The screen does not expose:

- contractor create/edit/delete,
- import,
- CRM pipeline,
- status changes,
- automation,
- AI/LLM actions,
- invoice workflow changes.

## Safety

The screen must not expose:

- secrets or tokens,
- connection strings,
- raw JSON or payloads,
- local file paths,
- `data/magazyn`,
- `storage_key`,
- technical event details.

If any source is missing optional relationship data, the UI should show a normal empty state instead of technical copy.

## Current Limitations

- Related documents are inferred only from Work Item metadata. There is no dedicated contractor-document relation endpoint yet.
- Related Work Items are resolved in the frontend from the existing list endpoint. If this becomes too heavy, a later read-only backend relation endpoint may be justified.
- Historical relationship activity is still limited to available notes, invoices, and linked tasks.
- The screen is not a CRM pipeline and should not be used to edit contractor master data.

## Next Safe Step

Live-verify `/crm/[contractorId]` for at least two organizations with realistic sandbox data. If relationships are too thin, improve sandbox data first before adding new backend contracts.
