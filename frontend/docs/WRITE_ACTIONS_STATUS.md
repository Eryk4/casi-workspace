# Write Actions Status

Last checked: 2026-07-02

This document tracks the current write actions exposed by the active Next.js frontend in `frontend/`. The legacy UI in `static/` is not covered and must not be extended.

No new write action should be added until the existing paths below stay green in frontend model tests, targeted backend tests, and live tenant-scope checks.

## Summary

- Current write surfaces: Work Items, invoice operator comments, CRM contractor notes, billing payer notes, billing payment operational review status, billing work queue decisions, and billing contact draft/log events.
- Every active write path is organization-scoped.
- The frontend blocks writes without an active organization before calling the API.
- The backend resolves write scope server-side and rejects missing/invalid organization scope.
- UI success is only shown after backend confirmation.
- No current write path should send data to external systems, KSeF, email, AI, or S3. Billing payer notes, payment operational status, work queue decisions, and billing contact draft/log events are internal-only and do not change financial state or send messages.
- Active Next write paths listed below have explicit payload allowlists.
- Broader backend mutating endpoints are tracked separately in `docs/PAYLOAD_ALLOWLIST_AUDIT.md` before any future hardening.
- Backend-only additive comments/notes for support, intake, tasks, and knowledge documents now also reject extra JSON fields, but they are not promoted as active Next write actions by this document.
- Backend-only small Work Items actions now reject extra JSON fields for SLA sweep, manual escalation, and reopen; they are still not active Next UI actions.
- Backend-only small note/settings/preferences endpoints now reject extra JSON fields for shared organization note, personal note, and reminder preferences; they are still not active Next module write actions.
- Backend-only task reminder snooze now rejects extra JSON fields and accepts only `mode`; it is still not an active Next UI write action.
- Backend-only Knowledge version actions now reject extra JSON fields for restore-version and mark-official-version; they accept only `version_number` and are still not active Next UI write actions.
- Backend-only task checklist creation now rejects extra JSON fields and accepts only `item_text`; it is still not an active Next UI write action.
- Backend-only user calendar create/update now reject extra JSON fields and accept only explicit calendar profile fields; they are still not active Next UI write actions.
- Backend-only dashboard saved views now reject extra top-level JSON fields for create/update; nested `view_state` remains intentionally broad and is still not active Next UI write work.

## Current Write Paths

| Area | Endpoint | Frontend screen | Payload | Organization scope | UI success model | Backend isolation | Tests |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Work Items | `POST /api/work-items/{id}/assign?organization_id=...` | `/work-items` | `{ "assigned_user_id": number }` | Required by active organization context | Per-row loading; local state updates only from backend response | `_resolve_write_scope`; service reads item by `work_item_id` and `organization_id` | `test-work-items.js`, `tests/test_work_item_http.py`, `tests/test_work_item_service.py` |
| Work Items | `POST /api/work-items/{id}/snooze?organization_id=...` | `/work-items` | `{ "mode": "1h" }` or `{ "mode": "1d" }` | Required by active organization context | Per-row loading; local state updates only from backend response | `_resolve_write_scope`; service reads item by `work_item_id` and `organization_id` | `test-work-items.js`, `tests/test_work_item_http.py`, `tests/test_work_item_service.py` |
| Work Items | `POST /api/work-items/{id}/close?organization_id=...` | `/work-items` | `{ "reason": string }` | Required by active organization context | Per-row loading; local state updates only from backend response | `_resolve_write_scope`; service reads item by `work_item_id` and `organization_id` | `test-work-items.js`, `tests/test_work_item_http.py`, `tests/test_work_item_service.py` |
| Faktury | `POST /api/invoices/{id}/comments?organization_id=...` | `/faktury/{invoiceId}` | `{ "note_text": string }` | Required by active organization context | Form loading; detail refreshes after backend response | `_resolve_write_scope`; service reads invoice by `invoice_id` and `organization_id` | `test-invoices.js`, `tests/http_server_test_methods.py`, `tests/invoice_test_methods.py` |
| CRM | `POST /api/contractors/{id}/notes?organization_id=...` | `/crm/{contractorId}` | `{ "note_text": string }` | Required by active organization context | Form loading; detail refreshes after backend response | `_resolve_write_scope`; service reads contractor by `contractor_id` and `organization_id` | `test-contractor-detail.js`, `tests/http_server_test_methods.py` |
| Rozliczenia | `POST /api/billing/payers/{payerId}/notes?organization_id=...` | `/rozliczenia/platnicy/{payerId}` | `{ "note_text": string }` | Required by active organization context | Form loading; detail refreshes after backend response | `_resolve_write_scope`; service reads payer by `billing_payer_id` and `organization_id`; no balance/charge/payment/match mutation | `test-billing.js`, `tests/test_billing_notes_http.py` |
| Rozliczenia | `POST /api/billing/payments/{paymentId}/review-status?organization_id=...` | `/rozliczenia/wplaty/{paymentId}` | `{ "status": string, "note_text"?: string }` | Required by active organization context | Form loading; detail refreshes after backend response | `_resolve_write_scope`; service reads incoming transaction by `billing_transaction_id` and `organization_id`; no transaction/charge/match/ledger/balance mutation | `test-billing.js`, `tests/test_billing_payment_review_status_http.py` |
| Rozliczenia | `POST /api/billing/work-queue/events?organization_id=...` | `/rozliczenia/sprawy` | `{ "issue_key": string, "issue_type": string, "target_type": string, "target_id"?: number, "action": "handled" | "snoozed", "note_text"?: string }` | Required by active organization context | Form loading; queue refreshes after backend response | `_resolve_write_scope`; service validates `payment` and `payer` targets by organization; no transaction/charge/match/ledger/balance mutation | `test-billing.js`, `tests/test_billing_work_queue_events_http.py` |
| Rozliczenia | `POST /api/billing/contact-events?organization_id=...` | `/rozliczenia/platnicy/{payerId}` | `{ "payer_id": number, "related_payment_id"?: number, "related_issue_key"?: string, "channel": string, "contact_action": string, "message_text"?: string, "note_text"?: string }` | Required by active organization context | Form loading; payer detail refreshes after backend response | `_resolve_write_scope`; service validates payer and optional payment by organization; no transaction/charge/match/ledger/balance mutation and no external sending | `test-billing.js`, `tests/test_billing_contact_events_http.py` |

## Tenant Isolation Status

### Work Items

- Frontend calls assign/snooze/close only when `selectedOrganizationId` is present.
- Backend uses `_resolve_write_scope`.
- Service methods fetch work items through `WorkItemRepository.get_by_id(..., organization_id=...)`.
- Regression coverage includes cross-organization HTTP checks for assign, snooze, and close.
- HTTP endpoints reject extra payload fields:
  - assign accepts only `assigned_user_id`,
  - snooze accepts only `mode`,
  - close accepts only `reason`.
- Current expected result for wrong organization scope: no mutation and `404` for item-specific actions.

### Invoice Comments

- Frontend blocks comment submit without active organization.
- Backend requires write scope before calling `InvoiceService.add_invoice_comment`.
- Service fetches the invoice by `invoice_id` and `organization_id`.
- Comment text persists in `invoice_comments` and appears in invoice detail.
- HTTP endpoint accepts only `{ "note_text": "..." }`; extra fields such as `organization_id`, `invoice_id`, `author_user_id`, `created_at`, or `role` are rejected with `400`.
- Event history records `invoice_comment_id` and `note_length`, not the full `note_text`.
- Invoice detail responses redact legacy `invoice_comment_added` event details that may still contain old `note_text` values in local data.
- Regression coverage checks that global admins cannot add invoice comments without `organization_id`, and that an invoice from another organization cannot be commented through the wrong scope.

### CRM Contractor Notes

- Frontend blocks note submit without active organization.
- Backend requires write scope and accepts only `{ "note_text": "..." }`.
- Service fetches the contractor by `contractor_id` and `organization_id`.
- Live verification confirmed that CASI contractor notes do not appear under Misja Robotyka and vice versa.


### Billing Payer Notes

- Frontend blocks note submit without active organization.
- Backend requires write scope and accepts only `{ "note_text": "..." }`.
- Service fetches the payer by `billing_payer_id` and `organization_id`.
- The note persists in `billing_notes` and appears in payer detail after refresh.
- Event history records `billing_note_id`, `billing_payer_id`, and `note_length`, not the full `note_text`.
- The endpoint must not change balances, charges, payment matches, transactions, ledger entries, imports, reminders, exports, or accounting state.

### Billing Payment Operational Status

- Frontend blocks status submit without active organization.
- Backend requires write scope and accepts only `status` plus optional `note_text`.
- Allowed statuses are `needs_review`, `checked`, `waiting_for_contact`, `waiting_for_payment`, and `do_not_auto_match`.
- Service fetches the incoming payment transaction by `billing_transaction_id` and `organization_id`.
- The status persists in `billing_payment_review_events` and appears on payment detail after refresh.
- Event history records `billing_payment_review_event_id`, `billing_transaction_id`, `status`, and `note_length`, not the full `note_text`.
- The endpoint must not change balances, charges, payment matches, transactions, ledger entries, imports, reminders, exports, or accounting state.
- Wrong organization scope returns not found/forbidden style behavior without creating a review event.

### Billing Work Queue Decisions

- Frontend blocks decision submit without active organization.
- Backend requires write scope and accepts only `issue_key`, `issue_type`, `target_type`, `target_id`, `action`, and optional `note_text`.
- Allowed actions are `handled` and `snoozed`.
- For `target_type=payment`, service fetches the transaction by `billing_transaction_id` and `organization_id`.
- For `target_type=payer`, service fetches the payer by `billing_payer_id` and `organization_id`.
- The decision persists in `billing_work_queue_events` and is used only to move the issue out of `Najpierw zr?b` into `Od?o?one sprawy` or `Ostatnio obs?u?one`.
- Event history records `billing_work_queue_event_id`, issue metadata, action, target metadata, and `note_length`, not the full `note_text`.
- The endpoint must not change balances, charges, payment matches, transactions, ledger entries, imports, reminders, task manager items, exports, or accounting state.
- `Obs?u?ona` does not mean settled. `Od?o?ona` does not create a reminder.

### Backend-Only Additive Comments/Notes

These paths are not active Next write actions yet, but they were hardened as small additive comment/note endpoints:

- Support request comments accept only `note_text` and `parent_comment_id`.
- Intake item comments accept only `note_text` and `parent_comment_id`.
- Task notes/comments accept only `note_text`, `parent_note_id`, and `note_kind`.
- Knowledge document comments accept only `note_text`, `version_number`, `annotation_kind`, `anchor_label`, and `anchor_excerpt`.

They remain backend/API surfaces until a separate product decision promotes any of them into the active Next UI.

### Backend-Only Small Work Items Actions

These paths are not active Next write actions yet, but they were hardened as small Work Items endpoints:

- SLA sweep accepts only `limit`.
- Manual escalation accepts only `assigned_user_id`.
- Reopen accepts only `status`, `reason`, `due_at`, `sla_deadline_at`, `sla_warning_minutes`, and `sla_warning_at`.

Broader Work Items writes remain out of scope for this document update: create, broad update, bulk actions, and SLA policy updates need separate endpoint-specific contracts before any future UI exposure.

### Backend-Only Note/Settings/Preferences

These paths are not active Next module write actions yet, but they were hardened as small note/settings/preferences endpoints:

- Organization shared note accepts only `shared_note_text`.
- User personal note accepts only `personal_note_text`.
- User reminder preferences accept only `telegram_reminders_enabled`, `browser_notifications_enabled`, `quiet_hours_start`, `quiet_hours_end`, and `repeat_interval_minutes`.

Broader settings/state writes remain out of scope: session workspace state is a structured UI state payload, and system communication settings can affect integration secrets.

### Backend-Only Task Reminder Action

This path is not an active Next write action yet, but it was hardened as a small reminder endpoint:

- Task reminder snooze accepts only `mode`.

Broader task writes remain out of scope: task create, broad task PATCH, task templates, visibility, attachments, and calendar/external notification actions need separate endpoint-specific contracts.

### Backend-Only Task Checklist Action

This path is not an active Next write action yet, but it was hardened as a small additive checklist endpoint:

- Add task checklist item accepts only `item_text`.

The backend still resolves organization/user scope through the manager assistant task scope and reads the task through the task service before creating the checklist item and history event. Task create, broad task PATCH, task visibility, task templates, attachments, and checklist update/delete flows remain out of scope.

### Backend-Only User Calendar Actions

These paths are not active Next write actions yet, but they were hardened as user-owned calendar profile endpoints:

- Create user calendar accepts only `display_name`, `description`, `provider`, `calendar_kind`, `linked_organization_id`, `default_duration_minutes`, `is_active`, and `external_calendar_id`.
- Update user calendar accepts only `display_name`, `description`, `provider`, `calendar_kind`, `linked_organization_id`, `default_duration_minutes`, `is_active`, and `external_calendar_id`.

The backend still derives `owner_user_id` from the authenticated user and reads updates through `get_by_id_for_owner`, so clients cannot set another `user_id`, inject Google OAuth tokens, or update another user's calendar through these endpoints. Google Calendar OAuth/connect, external availability logic, assignments, and task scheduling remain out of scope.

### Backend-Only Dashboard Saved Views

These paths are not active Next write actions yet, but they were hardened with a top-level payload allowlist:

- Create dashboard view accepts only `module_key`, `view_name`, `view_slug`, `description`, `view_state`, `view_state_json`, `is_shared`, and `is_default`.
- Update dashboard view accepts only `module_key`, `view_name`, `view_slug`, `description`, `view_state`, `view_state_json`, `is_shared`, and `is_default`.

The backend still derives `organization_id` from write scope and `created_by_user_id` from the authenticated user. Update/delete look up the saved view by `saved_view_id` and `organization_id`, so clients cannot move a view to another organization or set another owner through payload fields. Deep validation of nested `view_state` is intentionally left for a separate product-schema step.

### Backend-Only Knowledge Version Actions

These paths are not active Next write actions yet, but they were hardened as narrow version-number endpoints:

- Restore document version accepts only `version_number`.
- Mark official document version accepts only `version_number`.

The backend still resolves organization write scope, reads the document by `knowledge_document_id` and `organization_id`, and resolves the target version by number for that same document. Uploads, replacements, document metadata PATCH, decisions, bulk actions, OCR, and storage paths remain out of scope for this hardening.

## Data Exposure Checks

Current frontend and backend hardening rules:

- Do not log operator note/comment text as debug output.
- Do not expose storage keys, local paths, `C:\Users\...`, `data/magazyn`, secrets, tokens, connection strings, or raw debug payloads in UI.
- Keep payloads minimal and action-specific.
- Keep invoice comments, CRM notes, billing payer notes, and billing payment operational status additive; they must not mutate invoice totals, invoice workflow, contractor master data, balances, charges, payment matches, KSeF, OCR, email, or AI flows.

## Live Verification Notes

- Invoice comment live check: passed; comment persisted and returned after reload.
- CRM note live check: passed; note persisted and returned after reload.
- CRM note tenant isolation live check: passed for `CASI` contractor `13` and `Misja Robotyka` contractor `9`.
- Work Items live check: passed previously with active organization; backend regression tests now cover wrong-scope HTTP mutations.
- Billing payment operational status backend regression: passed; tests cover payload allowlist, wrong organization scope, no financial side effects, and sanitized event metadata.

## Remaining Risks

- Work Items has additional backend write endpoints outside the current Next UI (`create`, broad update, `bulk`, SLA policy). They are not exposed as active Next write actions in this document.
- Invoice workflow decision helpers still exist in the frontend model and tests, but `Centrum faktury` does not render workflow decision buttons. Do not expose them as writes until state-specific confirmations, permissions, and tenant tests are reviewed.
- CRM contractor create/edit/delete/import/pipeline are still not implemented in Next and should remain blocked until separate contracts and tests exist.

## Do Not Implement Yet

- Invoice workflow decisions, handoff, duplicate actions, mark-ready, close/reopen, batch actions.
- Contractor create/edit/delete/import/pipeline.
- Work Item bulk actions in Next.
- AI agent actions, automations, email sending, KSeF writes, OCR triggers, S3/Spaces writes.

## Recommended Next Checks

1. Keep this document updated whenever a write path is added or promoted from preview to active UI.
2. Add a live tenant-isolation pass for Work Items and invoice comments before adding more writes.
3. Review backend-only write endpoints separately before exposing any of them in Next.


## Rozliczenia

`/rozliczenia` hosts `Centrum rozliczeń` product v1 and remains read-only. `/kasa` is only a legacy redirect. No billing write actions, payment matching, bank statement import, posting, export, or charge generation are exposed in Next.

### Billing Contact Events

- Frontend blocks contact submit without active organization.
- Backend requires write scope and accepts only `payer_id`, optional `related_payment_id`, optional `related_issue_key`, `channel`, `contact_action`, optional `message_text`, and optional `note_text`.
- Allowed channels are `sms`, `email`, `phone`, `in_person`, and `other`.
- Allowed actions are `draft_prepared`, `contact_logged`, `no_answer`, `promised_payment`, and `needs_followup`.
- `message_text` is limited to 2000 characters and `note_text` to 1000 characters.
- The endpoint validates payer scope and optional payment scope by organization.
- The endpoint must not change balances, charges, payment matches, transactions, ledger entries, imports, reminders, exports, or accounting state.
- Audit details store metadata and text lengths, not the full message or note.
- UI copy states that CASI Workspace does not send the message; the operator must copy and send it manually outside the app.

## Rozliczenia - centrum kontaktow rozliczeniowych

`/rozliczenia/kontakty` nie dodaje nowej akcji zapisu. Jest read-only przegladem kontaktow zapisanych wczesniej na szczegole platnika. Formularz kontaktu pozostaje na `/rozliczenia/platnicy/{payerId}` i nadal nie wysyla wiadomosci ani nie zmienia finansow.
