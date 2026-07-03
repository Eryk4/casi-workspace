# Invoice Actions Readiness

Status: first safe invoice write implemented. The Next UI now exposes only the additive operator comment action; all workflow/status invoice decisions remain preview/read-only.

## Goal

This document reviews the mutating invoice endpoints that already exist in the backend and tracks the first small invoice write action implemented in Next.js.

The current Next invoice module already has:

- organization-scoped invoice inbox,
- organization-scoped invoice detail,
- links from inbox rows to invoice detail,
- read-only decision preview with the existing `preview-ready` semantics,
- one active additive invoice write: operator comment on invoice detail.

## Existing Mutating Invoice Endpoints

| Endpoint | Scope | Payload | What it changes | Reversible | Accounting impact | Permission model | Backend tests | First UI action readiness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `POST /api/invoices/{id}/comments?organization_id=...` | Uses `_resolve_data_scope`, accepts `organization_id` query param. | `{ "note_text": string, "parent_comment_id"?: number }` | Adds an invoice comment and logs `invoice_comment_added`. Does not change invoice status, workflow state, amounts, contractor, KSeF data, or handoff state. | Not currently delete/edit reversible, but low-risk additive audit trail. | No direct accounting or payment effect. | Requires authenticated write-capable user through the POST handler path; service also requires logged-in actor user. | HTTP test: `test_invoice_comment_endpoint_adds_comment_and_detail_contains_it`. Service test: `test_invoice_comment_is_added_and_visible_in_detail`. | Recommended first action. |
| `POST /api/invoices/{id}/actions/mark-ready?organization_id=...` | Uses `_resolve_data_scope`, accepts `organization_id`. | `{ "handoff_target"?: string, "handoff_note"?: string }` | Sets `workflow_state=gotowa_do_przekazania`, ready metadata, handoff target/note, logs `invoice_ready_for_handoff`, syncs operational artifacts. | Yes through `undo-last` when latest reversible event is ready. | Indirect operational/accounting workflow impact because it says invoice is ready for handoff. | Requires invoice workflow management permission via `_can_manage_invoice_workflow`. | HTTP test: `test_invoice_mark_ready_action_endpoint_sets_workflow`. Service tests cover ready/handoff/reopen and undo. | Not first. More meaningful workflow state change. |
| `POST /api/invoices/{id}/actions/undo-last?organization_id=...` | Uses `_resolve_data_scope`, accepts `organization_id`. | No payload. | Reverts latest supported workflow decision (`ready`, `handoff`, `close`, `reopen`) and logs `invoice_workflow_undone`. | It is itself a reversal, but only safe when backend exposes available undo. | Can alter operational workflow state; may affect handoff/closed metadata. | Permission is derived from workflow undo availability and role. | HTTP test: `test_invoice_undo_last_action_endpoint_reverts_workflow`. Service tests cover undo of ready and handoff. | Not first. Should appear only after UI clearly shows the exact action being reverted. |
| `POST /api/invoices/{id}/actions/handoff?organization_id=...` | Uses `_resolve_data_scope`, accepts `organization_id`. | `{ "handoff_target"?: string, "handoff_note"?: string }` | Sets `workflow_state=przekazana`, handoff metadata, may set ready metadata, logs `invoice_handed_off`, syncs operational artifacts. | Reversible with `undo-last` or `reopen`, depending state and role. | Higher risk: moves invoice to handoff stage and can influence accounting operations. | Requires decision-capable role. Operators are rejected. | HTTP tests: `test_invoice_handoff_action_requires_decision_role`, `test_invoice_handoff_and_reopen_actions_change_workflow`. Service tests cover workflow. | Not first. Requires stronger UX and confirmation. |
| `POST /api/invoices/{id}/actions/reopen?organization_id=...` | Uses `_resolve_data_scope`, accepts `organization_id`. | `{ "reason": string }` | Sets `workflow_state=w_pracy`, reopen metadata/reason, logs `invoice_reopened`, syncs operational artifacts. | Can be followed by later workflow actions, but changes official workflow state. | Medium/high operational impact; reopens already handed-off or closed invoice. | Requires decision-capable workflow role. | HTTP test through `test_invoice_handoff_and_reopen_actions_change_workflow`. Service tests cover reopen. | Not first. Needs clear reason form and history context. |
| `POST /api/invoices/{id}/actions/close?organization_id=...` | Uses `_resolve_data_scope`, accepts `organization_id`. | `{ "reason"?: string }` | Sets `workflow_state=zamknieta`, closed metadata/reason, logs `invoice_closed`, syncs operational artifacts including linked intake items. | Reversible only through supported workflow undo/reopen patterns. | High operational/accounting impact; closes invoice circulation. | Requires decision-capable workflow role and valid state. | HTTP test: `test_invoice_close_action_updates_workflow`. Service test: `test_invoice_can_be_closed_after_handoff_and_keeps_closed_metadata`. | Not first. Too final for first write action. |
| `POST /api/invoices/{id}/actions/confirm-duplicate?organization_id=...` | Uses `_resolve_data_scope`, accepts `organization_id`. | No payload. | Sets `status=pewny_duplikat`, `duplicate_type=pewny`, flag reason, logs `duplicate_confirmed`. | Can be countered by reject/mark-correct, but this changes invoice classification. | Medium/high risk: duplicate status can affect processing decisions. | Requires role in `INVOICE_DECISION_ROLES`. Operator rejected. | HTTP test covers role rejection and coordinator success. Service duplicate tests exist. | Not first. Sensitive classification decision. |
| `POST /api/invoices/{id}/actions/reject-duplicate?organization_id=...` | Uses `_resolve_data_scope`, accepts `organization_id`. | No payload. | Calls `mark_correct`: sets `status=poprawna`, `duplicate_type=brak`, deletes duplicate relations, logs `duplicate_rejected`. | Not trivially reversible because duplicate relations are deleted. | Medium/high risk: changes duplicate classification and relation graph. | Requires role in `INVOICE_DECISION_ROLES`. | Covered by duplicate/service regression tests; less directly visible in HTTP list than confirm. | Not first. Destructive relation cleanup makes it poor as first UI action. |
| `PATCH /api/invoices/{id}?organization_id=...` | Requires write role, uses `_resolve_data_scope`, accepts `organization_id`. | Broad partial invoice fields. Special handling for KSeF authoritative fields, assignee, contractor, amount, metadata. | Can update many invoice fields, create/refresh contractor, change assignment, recalculate hashes, apply duplicate flags, log `invoice_updated` and assignment events. | Depends on field; no generic safe undo. | Potentially high: can alter core invoice data, amount, contractor, KSeF correction flow. | Requires write role; service validates selected fields. | Service tests cover assignment and KSeF-protected changes; HTTP coverage exists for broad PATCH behavior. | Not first. Too broad for a small safe action. |
| `POST /api/invoices/actions/batch?organization_id=...` | Uses `_resolve_data_scope`, accepts optional `organization_id`; legacy tests also cover no explicit org for default session. | `{ "invoice_ids": number[], "action": "mark-verification" | "confirm-duplicate" | "mark-correct" }` | Applies status/duplicate actions to multiple invoices. | Partially reversible by later manual actions, but batch changes are broad. | Medium/high because it can classify many invoices at once. | Authenticated write flow; underlying handlers validate actions. | HTTP test: `test_invoice_batch_action_endpoint_updates_multiple_invoices`. | Not first. Batch operation is intentionally out of scope. |
| `POST /api/invoice-handoff-batches?organization_id=...` | Uses `_resolve_data_scope`, accepts `organization_id`. | `{ "invoice_ids": number[], "handoff_target"?: string, "note"?: string }` | Creates handoff batch; may mark invoices ready and hand them off; creates batch/items and logs `invoice_handoff_batch_created`. | Not simple; individual workflow actions may be undoable, batch remains. | High operational impact; creates a package for handoff/export. | Requires decision-capable workflow role. | HTTP test: `test_invoice_handoff_batch_endpoints_create_detail_and_export`. Service test covers create/export. | Not first. Multi-invoice workflow operation. |
| `GET /api/invoice-handoff-batches/{id}/export?organization_id=...` | Uses `_resolve_data_scope`, accepts `organization_id`. | No body. | Exports CSV and marks batch status as exported. Even though it is GET, it has a mutating side effect. | Not obviously reversible. | High operational impact; export status changes and external handoff semantics are implied. | Requires decision-capable workflow role in service. | HTTP test covers export and exported status. | Do not implement as an early UI action; also consider changing to POST later. |

## Risk Notes

- `comment` is the only clearly small additive write. It does not move workflow, does not change invoice status, does not affect amounts, does not call KSeF/OCR/e-mail, and does not send anything outside the system.
- `mark-ready`, `handoff`, `reopen`, `close`, and `undo-last` are real workflow operations. They are tested, but they need stronger confirmation UX, state-specific availability, and history context before exposing in Next.
- `confirm-duplicate` and `reject-duplicate` are classification decisions. `reject-duplicate` deletes duplicate relations through `mark_correct`, so it is not a good first action.
- `PATCH /api/invoices/{id}` is too broad for a first action. A later UI should use narrow helpers/contracts rather than exposing generic invoice patching.
- Batch actions and handoff batches must stay out of the first UI action because they can affect multiple invoices and operational handoff state.
- The export endpoint currently mutates state through `GET`. It should not be surfaced as a casual action before the contract is revisited.

## Recommended First Next Action

Implemented first invoice write action:

`Add invoice comment`

Backend contract:

```http
POST /api/invoices/{invoiceId}/comments?organization_id={activeOrganizationId}
Content-Type: application/json

{
  "note_text": "Short operator note",
  "parent_comment_id": optionalNumber
}
```

Expected success:

- HTTP `201`, created comment object.
- Invoice detail subsequently includes the comment in `comments`.
- History includes `invoice_comment_added`.
- Next clears the textarea only after backend confirmation and refreshes invoice detail.

Expected errors:

- `400` for empty comment, missing invoice, invalid parent comment, or validation errors.
- `401` if session is missing/expired through common auth handling.
- `403` if organization scope is not allowed by `_resolve_data_scope` or role access.
- `404` only if route/id parsing fails before service validation.

## Why This Is Safest

- Additive only: it appends a note instead of changing invoice facts or workflow state.
- Clear user value: operators can leave context after reviewing a detail view.
- Easy success model: show the new comment only after backend returns `201`, then refresh detail.
- Easy failure model: keep text in the form and show the existing invoice error area.
- Existing backend and service tests already cover comment creation and detail visibility.
- No KSeF, e-mail, OCR, S3, billing, payment, or external integration is involved.

## Still Do Not Implement Yet

Do not expose these as casual invoice write actions yet:

- confirm duplicate,
- reject duplicate,
- mark ready,
- handoff,
- reopen,
- close,
- undo last,
- batch actions,
- handoff batch create/export,
- generic PATCH invoice edit.

## UI Implementation Conditions

The implemented `Add invoice comment` flow must keep these guardrails:

1. Keep the detail page organization-scoped and require active `organization_id`.
2. Add a narrow frontend helper instead of using generic action plumbing.
3. Add per-form loading state and prevent double-submit.
4. Do not clear the textarea until the backend confirms success.
5. Refresh invoice detail after success so comments/history come from backend.
6. Show backend errors without pretending success.
7. Add model/regression tests for endpoint, payload, loading/error/success, read-only fallback when no organization is selected, and no workflow/status mutation.
8. Do not add edit/delete comments in the same step.

## Current Next UI Notes

- Operator comments are displayed separately from system history on the invoice detail.
- System history still shows `invoice_comment_added` as an audit event.
- The comment text itself comes from backend `comments`, not from raw debug payloads.
- Document/OCR trace avoids exposing raw local paths and storage keys in the invoice detail UI.
