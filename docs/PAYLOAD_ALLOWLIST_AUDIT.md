# Payload Allowlist Audit

Last checked: 2026-07-02

This audit maps mutating backend routes in `app/api/http_server.py` and checks whether JSON payloads are constrained by an explicit allowlist of accepted fields.

This is a risk map only. It does not approve broad payload refactors, workflow changes, deployment changes, or new UI actions.

## Summary

Detected mutating handlers in `http_server.py`:

| Category | Count |
| --- | ---: |
| Total mutating route handlers | 118 |
| `POST` handlers | 91 |
| `PATCH` handlers | 18 |
| `DELETE` handlers | 9 |
| Handlers that read JSON or multipart payload | 83 |
| JSON handlers with explicit field allowlist | 23 |
| JSON handlers without explicit field allowlist | 57 |
| Multipart/upload handlers | 3 |
| No-JSON action/delete handlers | 32 |
| Fallback handlers | 3 |

Currently allowlisted JSON write paths:

| Method | Path | Module | Accepted fields | Regression coverage |
| --- | --- | --- | --- | --- |
| `POST` | `/api/invoices/{id}/comments` | Invoices | `note_text` | `tests.test_http_server_invoices` |
| `POST` | `/api/contractors/{id}/notes` | CRM | `note_text` | `tests.test_http_server_system` |
| `POST` | `/api/work-items/{id}/assign` | Work Items | `assigned_user_id` | `tests.test_work_item_http` |
| `POST` | `/api/work-items/{id}/snooze` | Work Items | `mode` | `tests.test_work_item_http` |
| `POST` | `/api/work-items/{id}/close` | Work Items | `reason` | `tests.test_work_item_http` |
| `POST` | `/api/support/requests/{id}/comments` | Support | `note_text`, `parent_comment_id` | `tests.test_support_center_http` |
| `POST` | `/api/intake/items/{id}/comments` | Intake | `note_text`, `parent_comment_id` | `tests.test_support_center_http` |
| `POST` | `/api/tasks/{id}/notes` / `/comments` | Tasks | `note_text`, `parent_note_id`, `note_kind` | `tests.test_task_http` |
| `POST` | `/api/knowledge/documents/{id}/comments` | Knowledge | `note_text`, `version_number`, `annotation_kind`, `anchor_label`, `anchor_excerpt` | `tests.test_http_server_access` |
| `POST` | `/api/work-items/sla/sweep` | Work Items | `limit` | `tests.test_work_item_http` |
| `POST` | `/api/work-items/{id}/escalate` | Work Items | `assigned_user_id` | `tests.test_work_item_http` |
| `POST` | `/api/work-items/{id}/reopen` | Work Items | `status`, `reason`, `due_at`, `sla_deadline_at`, `sla_warning_minutes`, `sla_warning_at` | `tests.test_work_item_http` |
| `POST` | `/api/user-reminder-preferences` | Reminders | `telegram_reminders_enabled`, `browser_notifications_enabled`, `quiet_hours_start`, `quiet_hours_end`, `repeat_interval_minutes` | `tests.test_http_server_system` |
| `PATCH` | `/api/organization-shared-note` | Notes | `shared_note_text` | `tests.test_http_server_system` |
| `PATCH` | `/api/user-personal-note` | Notes | `personal_note_text` | `tests.test_http_server_system` |
| `POST` | `/api/tasks/{id}/snooze-reminder` | Tasks/reminders | `mode` | `tests.test_task_http` |
| `POST` | `/api/knowledge/documents/{id}/restore-version` | Knowledge | `version_number` | `tests.test_http_server_access` |
| `POST` | `/api/knowledge/documents/{id}/mark-official-version` | Knowledge | `version_number` | `tests.test_http_server_access` |
| `POST` | `/api/tasks/{id}/checklist` | Tasks | `item_text` | `tests.test_task_http` |
| `POST` | `/api/user-calendars` | Calendar | `display_name`, `description`, `provider`, `calendar_kind`, `linked_organization_id`, `default_duration_minutes`, `is_active`, `external_calendar_id` | `tests.test_calendar_service`, `tests.test_calendar_http` |
| `PATCH` | `/api/user-calendars/{id}` | Calendar | `display_name`, `description`, `provider`, `calendar_kind`, `linked_organization_id`, `default_duration_minutes`, `is_active`, `external_calendar_id` | `tests.test_calendar_service`, `tests.test_calendar_http` |
| `POST` | `/api/dashboard/views` | Dashboard views | `module_key`, `view_name`, `view_slug`, `description`, `view_state`, `view_state_json`, `is_shared`, `is_default` | `tests.test_http_server_invoices` |
| `PATCH` | `/api/dashboard/views/{id}` | Dashboard views | `module_key`, `view_name`, `view_slug`, `description`, `view_state`, `view_state_json`, `is_shared`, `is_default` | `tests.test_http_server_invoices` |

## Side-Effect GET Routes

These are not JSON payload allowlist issues, but they are side-effectful or externally stateful GET-style callbacks and should remain out of broad payload hardening:

| Method | Path | Module | Risk | Note |
| --- | --- | --- | --- | --- |
| `GET` | `/api/google-calendar/oauth/callback` | Google Calendar integration | medium | OAuth callback may persist connection state. Review separately with OAuth state/CSRF rules. |
| `GET` | `/api/email/oauth/callback` | Email integration | medium | OAuth callback may persist connection state. Review separately with OAuth state/CSRF rules. |

## JSON Write Inventory

### High-Risk JSON Endpoints Without Explicit Allowlist

These should not be hardened casually. They affect invoices, workflow, billing, organizations, users, documents, or integrations and need endpoint-specific tests before any validation change.

| Method | Path | Module | Current payload behavior | Risk | Recommended next step |
| --- | --- | --- | --- | --- | --- |
| `PATCH` | `/api/invoices/{id}` | Invoices | Broad invoice update payload | high | Separate design: enumerate supported update fields and workflow side effects. |
| `POST` | `/api/invoices/actions/batch` | Invoices | `invoice_ids`, `action`, action-specific fields | high | Separate batch-action contract audit before any allowlist. |
| `POST` | `/api/invoices/{id}/actions/mark-ready` | Invoices | Decision/workflow payload | high | Separate workflow action hardening with state-specific tests. |
| `POST` | `/api/invoices/{id}/actions/handoff` | Invoices | Handoff target/note payload | high | Separate workflow action hardening; do not bundle with comments. |
| `POST` | `/api/invoices/{id}/actions/reopen` | Invoices | Reopen reason/status payload | high | Separate workflow action hardening. |
| `POST` | `/api/invoices/{id}/actions/close` | Invoices | Close reason payload | high | Separate workflow action hardening. |
| `POST` | `/api/invoice-handoff-batches` | Invoices | Batch export/handoff payload | high | Separate handoff/export audit. |
| `POST` | `/api/billing/ledger/matches` | Billing | Payment match payload | high | Add targeted tests before allowlist; financial side effects. |
| `POST` | `/api/billing/charges/generate` | Billing | Charge generation payload | high | Separate billing safety audit. |
| `POST` | `/api/billing/statements/import-csv` | Billing | CSV import payload | high | Treat as import path; validate separately. |
| `POST` | `/api/organizations` | Organizations | Organization creation payload | high | Separate admin settings contract. |
| `PATCH` | `/api/organizations/{id}` | Organizations | Organization update payload | high | Separate admin settings contract. |
| `POST` | `/api/users` | Users | User creation payload | high | Separate identity/permissions audit. |
| `PATCH` | `/api/users/{id}` | Users | User update payload | high | Separate identity/permissions audit. |
| `POST` | `/api/knowledge/documents` | Knowledge | Document create/upload payload | high | Upload/document contract audit; includes file/content fields. |
| `POST` | `/api/knowledge/documents/bulk` | Knowledge | Bulk document action payload | high | Separate bulk action contract. |
| `POST` | `/api/knowledge/documents/{id}/replace` | Knowledge | Replacement upload payload | high | Multipart/upload-specific validation. |
| `PATCH` | `/api/knowledge/documents/{id}` | Knowledge | Document metadata/workflow update payload | high | Separate document metadata contract. |
| `POST` | `/api/knowledge/documents/{id}/decision` | Knowledge | Approval/reviewer decision payload | high | Separate workflow action hardening. |
| `POST` | `/api/tasks` | Tasks | Task creation payload | high | Separate task creation contract audit. |
| `PATCH` | `/api/tasks/{id}` | Tasks | Task update payload | high | Separate task update contract audit. |
| `POST` | `/api/tasks/{id}/attachments` | Tasks | Attachment payload | high | Upload/attachment audit. |
| `POST` | `/api/approvals` | Approvals | Approval request payload | high | Separate approval workflow contract. |
| `POST` | `/api/approvals/{id}/approve` | Approvals | Approval decision payload | high | Separate approval workflow hardening. |
| `POST` | `/api/approvals/{id}/reject` | Approvals | Approval decision payload | high | Separate approval workflow hardening. |
| `POST` | `/api/approvals/{id}/attachments` | Approvals | Attachment payload | high | Attachment-specific validation. |
| `POST` | `/api/automation/rules` | Automation | Automation rule payload | high | Separate automation safety audit. |
| `PATCH` | `/api/automation/rules/{id}` | Automation | Automation rule update payload | high | Separate automation safety audit. |
| `PATCH` | `/api/system/communication-settings` | System settings | Communication settings payload | high | Separate settings contract; may affect integrations. |

### Medium-Risk JSON Endpoints Without Explicit Allowlist

These are narrower than the high-risk group but still need targeted tests before changing validation.

| Method | Path | Module | Current payload behavior | Risk | Recommended next step |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/api/session/login` | Auth | Login/password payload | medium | Add excess-field rejection only after login clients are checked. |
| `POST` | `/api/google-calendar/connect` | Calendar integration | Connection payload | medium | OAuth/integration audit. |
| `POST` | `/api/google-calendar/assignments` | Calendar integration | Assignment payload | medium | Add allowlist after checking current UI/API clients. |
| `POST` | `/api/email/google/connect` | Email integration | Connect/login hint payload | medium | OAuth/integration audit. |
| `POST` | `/api/task-templates` | Tasks | Template creation payload | medium | Separate template contract. |
| `POST` | `/api/task-templates/{id}/apply` | Tasks | Template apply payload | medium | Separate template contract. |
| `PATCH` | `/api/task-templates/{id}` | Tasks | Template update payload | medium | Separate template contract. |
| `POST` | `/api/support/requests` | Support | Support request payload | medium | Candidate after support contract review. |
| `POST` | `/api/support/requests/{id}/attachments` | Support | Attachment payload | medium | Attachment-specific validation. |
| `POST` | `/api/intake/forms` | Intake | Form creation payload | medium | Separate intake form contract. |
| `PATCH` | `/api/intake/forms/{id}` | Intake | Form update payload | medium | Separate intake form contract. |
| `POST` | `/api/intake/items` | Intake | Intake item payload | medium | Separate intake item contract. |
| `PATCH` | `/api/intake/items/{id}` | Intake | Intake item update payload | medium | Separate intake item contract. |
| `POST` | `/api/intake/items/{id}/attachments` | Intake | Attachment payload | medium | Attachment-specific validation. |
| `POST` | `/api/knowledge/ask` | Knowledge/assistant | Question payload | medium | AI/query contract audit. |
| `POST` | `/api/knowledge/documents/{id}/tasks` | Knowledge/tasks | Linked entities payload | medium | Separate linked entity contract. |
| `POST` | `/api/whiteboard/events` | Whiteboard | Strokes/events payload | medium | Separate whiteboard contract. |
| `POST` | `/api/whiteboard/images` | Whiteboard | Multipart/image metadata payload | medium | Multipart validation. |
| `PATCH` | `/api/whiteboard/images/{id}` | Whiteboard | Image metadata payload | medium | Candidate after whiteboard model review. |
| `POST` | `/api/work-items` | Work Items | Work item creation payload | medium | Candidate after Work Item create UI contract review. |
| `PATCH` | `/api/work-items/{id}` | Work Items | Work item update payload | medium | Broad update; separate design. |
| `POST` | `/api/work-items/bulk` | Work Items | Bulk action payload | medium | Separate bulk action contract. |
| `POST` | `/api/work-items/sla-policy` | Work Items | SLA policy payload | medium | Separate policy contract. |
| `POST` | `/api/tasks/parse-natural` | Tasks | Natural language command payload | medium | AI/parser contract audit. |
| `PATCH` | `/api/session/workspace-state` | Session | Workspace state payload | medium | Broad structured UI state; review separately. |

### Lower-Risk or No-JSON Mutating Routes

These handlers do not read JSON payload in the current implementation, so payload allowlist is not the primary concern. They still need ordinary permission, CSRF/session, path ID, and side-effect tests.

| Method | Path group | Module | Risk | Note |
| --- | --- | --- | --- | --- |
| `POST` | `/api/session/logout` | Auth | low | No JSON payload. |
| `POST` | `/api/google-calendar/connections/{id}/approve` / `reject` | Calendar integration | medium | No JSON payload; external connection state. |
| `POST` | `/api/email/google/disconnect` | Email integration | medium | No JSON payload; external connection state. |
| `POST` | `/api/google-calendar/disconnect` | Calendar integration | medium | No JSON payload; external connection state. |
| `POST` | `/api/tasks/reminders/dispatch` | Reminders | medium | No JSON payload; operational side effect. |
| `POST` | `/api/tasks/reminders/outbox/{id}/retry` | Reminders | medium | No JSON payload; operational side effect. |
| `POST` | `/api/automation/rules/{id}/run` | Automation | medium | No JSON payload; execution side effect. |
| `POST` | `/api/knowledge/sync` | Knowledge | medium | No JSON payload; background sync. |
| `POST` | `/api/knowledge/activity/mark-seen` | Knowledge | low | No JSON payload. |
| `POST` | `/api/knowledge/documents/{id}/reprocess` | Knowledge | medium | No JSON payload; processing side effect. |
| `POST` | `/api/knowledge/documents/{id}/archive` / `restore` | Knowledge | medium | No JSON payload; document state changes. |
| `POST` | `/api/whiteboard/actions/clear` | Whiteboard | medium | No JSON payload; destructive action. |
| `POST` | `/api/organizations/{id}/actions/test-email-connection` / `test-ksef-connection` | Integrations | medium | No JSON payload; external test action. |
| `POST` | `/api/organizations/{id}/actions/check-email` / `check-ksef` | Integrations | high | No JSON payload; may import/update operational data. |
| `POST` | `/api/tasks/{id}/send-reminder` / `sync-calendar` / `check-calendar` | Tasks/integrations | medium | No JSON payload; external/notification side effects. |
| `POST` | `/api/invoices/{id}/actions/confirm-duplicate` / `undo-last` / `reject-duplicate` | Invoices | high | No JSON payload but workflow mutation. |
| `POST` | `/api/import/{...}` | Import/test tools | medium | No JSON payload in this branch; review separately. |
| `DELETE` | Google Calendar assignments, user calendars, dashboard views, automation rules, intake forms, knowledge documents | Multiple | medium/high by domain | No JSON payload; path ID and permissions matter. |

## Allowlist Status by Module

| Module | Status |
| --- | --- |
| Active Next Work Items actions | allowlisted for assign/snooze/close |
| Backend-only small Work Items actions | allowlisted for SLA sweep, escalate, and reopen |
| Small note/settings/preferences endpoints | allowlisted for shared note, personal note, and reminder preferences |
| Active Next invoice comments | allowlisted |
| Active Next CRM contractor notes | allowlisted |
| Invoice workflow actions | not allowlisted; high-risk workflow surface |
| Billing writes | not allowlisted; high-risk financial surface |
| Organizations/users/settings | not allowlisted; high-risk admin surface |
| Knowledge/documents writes | mostly not allowlisted; upload/workflow surface |
| Tasks broader writes | not allowlisted; medium/high depending on endpoint |
| Small task reminder action | allowlisted for snooze-reminder |
| Small task checklist action | allowlisted for additive checklist item creation |
| User calendars | allowlisted for user-owned create/update calendar payloads |
| Dashboard views | allowlisted for top-level saved view payload fields; nested `view_state` schema remains intentionally broad |
| Support/intake comments | allowlisted for additive comments |
| Task notes/comments | allowlisted for additive notes and replies |
| Knowledge document comments | allowlisted for comments and annotation metadata |
| Knowledge version actions | allowlisted for restore/mark official version number payloads |
| Dashboard/automation/whiteboard writes | not allowlisted; review per module |

## Missing Regression Tests

Known allowlisted paths have regression coverage. Most other JSON writes do not currently have extra-field rejection tests because they do not yet reject extra fields.

Do not add broad tests expecting rejection before each endpoint contract is reviewed.

## Recommended Hardening Order

1. **Task template contracts after separate review**
   - `POST /api/task-templates`
   - `PATCH /api/task-templates/{id}`
   - `POST /api/task-templates/{id}/apply`

2. **Dashboard view nested state schema review**
   - Optional deeper validation for `view_state` / `view_state_json` after product schema is stable.

3. **Broader Work Items contracts after separate review**
   - `POST /api/work-items`
   - `PATCH /api/work-items/{id}`
   - `POST /api/work-items/bulk`
   - `POST /api/work-items/sla-policy`

Do not start with invoice workflow, billing, user/admin settings, batch actions, imports, uploads, or OAuth/integration paths.

## Explicit Non-Goals

- No workflow changes.
- No new UI actions.
- No new endpoints.
- No broad validation framework refactor.
- No migrations.
- No DigitalOcean, S3, PostgreSQL runtime, deploy, or `static/` changes.
