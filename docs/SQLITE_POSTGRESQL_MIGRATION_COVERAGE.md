# SQLite → PostgreSQL migration coverage

## Contract

This document is generated from the explicit canonical manifest in `app/data_migration_manifest.py`. The manifest is the only source of truth for one-time data migration coverage. It currently classifies all 78 application tables: 73 persistent tables are migrated and 5 runtime/environment-bound tables are deliberately recreated or discarded.

The migration copies database records only. It does not copy storage objects, seed data, create administrators, load `.env.local`, reset or truncate a target, or merge into a non-empty target.

## Complete table classification

| # | Source → target | Category | Migrated | Primary key | Dependencies | Explicit transforms | Verification / rebuild |
|---:|---|---|:---:|---|---|---|---|
| 1 | `organizations` → `organizations` | `A_business` | yes | `organization_id` | — | JSON semantic: module_shortcuts_json, communication_config_json, work_item_sla_policy_json; Boolean: email_integration_enabled, ksef_integration_enabled, is_active; Timestamp: shared_note_updated_at, email_last_checked_at, email_last_connection_tested_at, ksef_last_checked_at, ksef_last_connection_tested_at, ksef_correction_delegate_assigned_at, ksef_correction_delegate_expires_at, created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 2 | `users` → `users` | `A_business` | yes | `user_id` | organizations | JSON semantic: workspace_state_json; Boolean: telegram_reminders_enabled, can_upload_knowledge, is_active, browser_notifications_enabled; Timestamp: personal_note_updated_at, workspace_state_updated_at, last_login_at, created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 3 | `organization_memberships` → `organization_memberships` | `A_business` | yes | `organization_membership_id` | organizations, users | Boolean: is_primary; Timestamp: granted_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 4 | `organization_modules` → `organization_modules` | `A_business` | yes | `organization_module_id` | organizations, users | Timestamp: enabled_at | count+primary_keys+canonical_row_hash+relations |
| 5 | `user_capabilities` → `user_capabilities` | `A_business` | yes | `user_capability_id` | users | Timestamp: granted_at | count+primary_keys+canonical_row_hash+relations |
| 6 | `system_settings` → `system_settings` | `A_business` | yes | `system_setting_id` | users | Timestamp: created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 7 | `user_calendars` → `user_calendars` | `A_business` | yes | `user_calendar_id` | organizations, users | Boolean: is_active; Timestamp: created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 8 | `user_google_calendar_connections` → `user_google_calendar_connections` | `A_business` | yes | `user_google_calendar_connection_id` | users | Boolean: employee_visibility_confirmed; Timestamp: token_expires_at, employee_confirmation_at, approved_at, created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 9 | `user_calendar_assignments` → `user_calendar_assignments` | `A_business` | yes | `user_calendar_assignment_id` | user_calendars, users | Timestamp: created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 10 | `system_email_google_connections` → `system_email_google_connections` | `A_business` | yes | `system_email_google_connection_id` | users | Timestamp: token_expires_at, created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 11 | `tasks` → `tasks` | `A_business` | yes | `task_id` | organizations, user_calendars, users | JSON semantic: recurrence_weekdays; Timestamp: due_at, remind_at, recurrence_end_at, reminder_sent_at, reminder_last_attempt_at, external_calendar_synced_at, external_calendar_last_checked_at, external_calendar_remote_updated_at, completed_at, created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 12 | `task_visibility_users` → `task_visibility_users` | `A_business` | yes | `task_visibility_user_id` | organizations, tasks, users | Timestamp: created_at | count+primary_keys+canonical_row_hash+relations |
| 13 | `task_links` → `task_links` | `A_business` | yes | `task_link_id` | organizations, tasks, users | Timestamp: created_at | count+primary_keys+canonical_row_hash+relations |
| 14 | `task_notes` → `task_notes` | `A_business` | yes | `task_note_id` | organizations, tasks, users | JSON semantic: mentioned_user_ids; Timestamp: created_at | count+primary_keys+canonical_row_hash+relations |
| 15 | `task_checklist_items` → `task_checklist_items` | `A_business` | yes | `task_checklist_item_id` | organizations, tasks, users | Boolean: is_completed; Timestamp: completed_at, created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 16 | `task_templates` → `task_templates` | `A_business` | yes | `task_template_id` | organizations, users | JSON semantic: recurrence_weekdays, checklist_json; Boolean: is_active; Timestamp: created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 17 | `approval_requests` → `approval_requests` | `A_business` | yes | `approval_request_id` | organizations, users | JSON semantic: metadata_json; Timestamp: requested_at, decided_at, created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 18 | `task_attachments` → `task_attachments` | `A_business` | yes | `task_attachment_id` | organizations, tasks, users | Timestamp: created_at; Storage-key audit: file_link, file_storage_key | count+primary_keys+canonical_row_hash+relations |
| 19 | `task_history` → `task_history` | `B_operational_audit` | yes | `task_history_id` | organizations, tasks | JSON semantic: details; Timestamp: created_at | count+primary_keys+canonical_row_hash+relations |
| 20 | `work_items` → `work_items` | `A_business` | yes | `work_item_id` | organizations, users | JSON semantic: metadata_json; Decimal: priority_score; Timestamp: due_at, sla_deadline_at, sla_warning_at, reminder_sent_at, escalation_sent_at, resolved_at, last_sla_transition_at, created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 21 | `work_item_history` → `work_item_history` | `B_operational_audit` | yes | `work_item_history_id` | organizations, work_items | JSON semantic: details; Timestamp: created_at | count+primary_keys+canonical_row_hash+relations |
| 22 | `contractors` → `contractors` | `A_business` | yes | `contractor_id` | organizations | Boolean: is_new; Date: last_invoice_date; Timestamp: created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 23 | `contractor_notes` → `contractor_notes` | `A_business` | yes | `contractor_note_id` | contractors, organizations, users | Timestamp: created_at | count+primary_keys+canonical_row_hash+relations |
| 24 | `invoices` → `invoices` | `A_business` | yes | `id` | contractors, organizations, users | Decimal: gross_amount, ocr_confidence; Date: incoming_date, issue_date, sale_date; Timestamp: created_at, updated_at, ready_for_handoff_at, handed_off_at, closed_at, reopened_at; Storage-key audit: file_link, file_storage_key, ocr_storage_key | count+primary_keys+canonical_row_hash+relations |
| 25 | `invoice_relations` → `invoice_relations` | `A_business` | yes | `id` | invoices | Timestamp: created_at | count+primary_keys+canonical_row_hash+relations |
| 26 | `invoice_comments` → `invoice_comments` | `A_business` | yes | `invoice_comment_id` | invoices, organizations, users | Timestamp: created_at | count+primary_keys+canonical_row_hash+relations |
| 27 | `invoice_handoff_batches` → `invoice_handoff_batches` | `A_business` | yes | `invoice_handoff_batch_id` | organizations, users | Timestamp: created_at, exported_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 28 | `invoice_handoff_batch_items` → `invoice_handoff_batch_items` | `A_business` | yes | `invoice_handoff_batch_item_id` | invoice_handoff_batches, invoices | Timestamp: created_at | count+primary_keys+canonical_row_hash+relations |
| 29 | `invoice_ksef_field_overrides` → `invoice_ksef_field_overrides` | `A_business` | yes | `invoice_ksef_field_override_id` | approval_requests, invoices, organizations, users | Timestamp: created_at, updated_at, approved_at, rejected_at | count+primary_keys+canonical_row_hash+relations |
| 30 | `billing_schools` → `billing_schools` | `A_business` | yes | `billing_school_id` | organizations | Boolean: is_active; Timestamp: created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 31 | `billing_models` → `billing_models` | `A_business` | yes | `billing_model_id` | organizations | Decimal: monthly_rate_amount, semester_rate_amount, sibling_discount_amount, large_family_discount_amount; Boolean: contract_required, is_active; Timestamp: created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 32 | `billing_payers` → `billing_payers` | `A_business` | yes | `billing_payer_id` | organizations | Boolean: has_large_family_card, is_active; Timestamp: created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 33 | `billing_students` → `billing_students` | `A_business` | yes | `billing_student_id` | billing_models, billing_payers, billing_schools, organizations | Boolean: is_active; Timestamp: created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 34 | `billing_charge_batches` → `billing_charge_batches` | `A_business` | yes | `billing_charge_batch_id` | billing_models, organizations, users | Date: due_date; Timestamp: created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 35 | `billing_charges` → `billing_charges` | `A_business` | yes | `billing_charge_id` | billing_charge_batches, billing_models, billing_payers, billing_students, organizations | Decimal: unit_rate_amount, base_amount, intro_free_discount_amount, sibling_discount_amount, large_family_discount_amount, total_amount; Date: due_date; Timestamp: created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 36 | `billing_student_charge_state` → `billing_student_charge_state` | `A_business` | yes | `billing_student_charge_state_id` | billing_students, organizations | Decimal: sibling_discount_remaining_amount; Boolean: sibling_discount_initialized; Timestamp: created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 37 | `billing_payer_charge_state` → `billing_payer_charge_state` | `A_business` | yes | `billing_payer_charge_state_id` | billing_payers, organizations | Decimal: large_family_discount_remaining_amount; Boolean: large_family_discount_initialized; Timestamp: created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 38 | `billing_bank_accounts` → `billing_bank_accounts` | `A_business` | yes | `billing_bank_account_id` | organizations | Boolean: is_active; Timestamp: created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 39 | `billing_statement_imports` → `billing_statement_imports` | `A_business` | yes | `billing_statement_import_id` | billing_bank_accounts, organizations, users | Timestamp: imported_at, created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 40 | `billing_transactions` → `billing_transactions` | `A_business` | yes | `billing_transaction_id` | billing_bank_accounts, billing_statement_imports, organizations | JSON semantic: raw_data; Decimal: amount; Date: booking_date, value_date; Timestamp: created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 41 | `billing_payment_review_events` → `billing_payment_review_events` | `B_operational_audit` | yes | `billing_payment_review_event_id` | billing_transactions, organizations, users | Timestamp: created_at | count+primary_keys+canonical_row_hash+relations |
| 42 | `billing_work_queue_events` → `billing_work_queue_events` | `B_operational_audit` | yes | `billing_work_queue_event_id` | organizations, users | Timestamp: created_at | count+primary_keys+canonical_row_hash+relations |
| 43 | `billing_contact_events` → `billing_contact_events` | `B_operational_audit` | yes | `billing_contact_event_id` | billing_payers, billing_transactions, organizations, users | Timestamp: created_at | count+primary_keys+canonical_row_hash+relations |
| 44 | `billing_next_step_events` → `billing_next_step_events` | `B_operational_audit` | yes | `billing_next_step_event_id` | organizations, users | Date: planned_for; Timestamp: created_at | count+primary_keys+canonical_row_hash+relations |
| 45 | `billing_payment_matches` → `billing_payment_matches` | `A_business` | yes | `billing_payment_match_id` | billing_charges, billing_payers, billing_transactions, organizations, users | Decimal: matched_amount; Timestamp: matched_at | count+primary_keys+canonical_row_hash+relations |
| 46 | `billing_payer_ledger_entries` → `billing_payer_ledger_entries` | `B_operational_audit` | yes | `billing_payer_ledger_entry_id` | billing_charges, billing_payers, billing_transactions, organizations, users | Decimal: amount_delta, balance_after; Timestamp: created_at | count+primary_keys+canonical_row_hash+relations |
| 47 | `billing_notes` → `billing_notes` | `A_business` | yes | `billing_note_id` | billing_payers, organizations, users | Timestamp: created_at | count+primary_keys+canonical_row_hash+relations |
| 48 | `knowledge_documents` → `knowledge_documents` | `A_business` | yes | `knowledge_document_id` | organizations, users | Decimal: duplicate_score; Boolean: is_downloadable, use_in_assistant; Timestamp: created_at, updated_at, official_version_marked_at, last_processed_at, processing_started_at, archived_at, deleted_at, last_seen_in_folder_at; Storage-key audit: file_link, file_storage_key, library_path | count+primary_keys+canonical_row_hash+relations |
| 49 | `knowledge_document_versions` → `knowledge_document_versions` | `A_business` | yes | `knowledge_document_version_id` | knowledge_documents, organizations, users | Timestamp: created_at; Storage-key audit: file_link, file_storage_key | count+primary_keys+canonical_row_hash+relations |
| 50 | `knowledge_processing_jobs` → `knowledge_processing_jobs` | `B_operational_audit` | yes | `knowledge_processing_job_id` | knowledge_documents, organizations, users | Timestamp: started_at, finished_at, created_at, updated_at; Storage-key audit: source_storage_key | count+primary_keys+canonical_row_hash+relations |
| 51 | `knowledge_folder_watchers` → `knowledge_folder_watchers` | `B_operational_audit` | yes | `knowledge_folder_watcher_id` | organizations | Timestamp: last_scan_started_at, last_scan_completed_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 52 | `knowledge_document_comments` → `knowledge_document_comments` | `A_business` | yes | `knowledge_document_comment_id` | knowledge_document_versions, knowledge_documents, organizations, users | Timestamp: created_at | count+primary_keys+canonical_row_hash+relations |
| 53 | `intake_forms` → `intake_forms` | `A_business` | yes | `intake_form_id` | organizations, users | JSON semantic: field_schema_json; Boolean: is_public, allow_attachments; Timestamp: created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 54 | `intake_items` → `intake_items` | `A_business` | yes | `intake_item_id` | intake_forms, invoices, organizations, tasks, users | JSON semantic: metadata_json; Timestamp: due_at, last_activity_at, created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 55 | `intake_item_comments` → `intake_item_comments` | `A_business` | yes | `intake_item_comment_id` | intake_items, organizations, users | JSON semantic: mentioned_user_ids; Timestamp: created_at | count+primary_keys+canonical_row_hash+relations |
| 56 | `intake_item_history` → `intake_item_history` | `B_operational_audit` | yes | `intake_item_history_id` | intake_items, organizations | JSON semantic: details; Timestamp: created_at | count+primary_keys+canonical_row_hash+relations |
| 57 | `entity_attachments` → `entity_attachments` | `A_business` | yes | `entity_attachment_id` | organizations, users | Timestamp: created_at; Storage-key audit: file_link, file_storage_key | count+primary_keys+canonical_row_hash+relations |
| 58 | `saved_views` → `saved_views` | `A_business` | yes | `saved_view_id` | organizations, users | JSON semantic: view_state_json; Boolean: is_shared, is_default; Timestamp: created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 59 | `automation_rules` → `automation_rules` | `A_business` | yes | `automation_rule_id` | organizations, users | JSON semantic: conditions_json, actions_json; Boolean: is_active; Timestamp: last_run_at, created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 60 | `organization_whiteboard_events` → `organization_whiteboard_events` | `A_business` | yes | `whiteboard_event_id` | organizations, users | JSON semantic: payload_json; Timestamp: created_at | count+primary_keys+canonical_row_hash+relations |
| 61 | `event_logs` → `event_logs` | `B_operational_audit` | yes | `id` | invoices, organizations | JSON semantic: details; Timestamp: event_time | count+primary_keys+canonical_row_hash+relations |
| 62 | `automation_executions` → `automation_executions` | `B_operational_audit` | yes | `automation_execution_id` | automation_rules, event_logs, organizations | JSON semantic: input_json, result_json; Timestamp: executed_at | count+primary_keys+canonical_row_hash+relations |
| 63 | `email_import_runs` → `email_import_runs` | `B_operational_audit` | yes | `email_import_run_id` | organizations | JSON semantic: details; Timestamp: started_at, finished_at | count+primary_keys+canonical_row_hash+relations |
| 64 | `email_import_items` → `email_import_items` | `B_operational_audit` | yes | `email_import_item_id` | email_import_runs, invoices, organizations | Timestamp: created_at | count+primary_keys+canonical_row_hash+relations |
| 65 | `ksef_import_runs` → `ksef_import_runs` | `B_operational_audit` | yes | `ksef_import_run_id` | organizations | JSON semantic: details; Timestamp: started_at, finished_at | count+primary_keys+canonical_row_hash+relations |
| 66 | `ksef_import_items` → `ksef_import_items` | `B_operational_audit` | yes | `ksef_import_item_id` | invoices, ksef_import_runs, organizations | Date: issue_date; Timestamp: created_at | count+primary_keys+canonical_row_hash+relations |
| 67 | `task_reminder_outbox` → `task_reminder_outbox` | `B_operational_audit` | yes | `task_reminder_outbox_id` | organizations, tasks, users | JSON semantic: payload; Boolean: retryable; Timestamp: delivery_anchor_at, available_at, claimed_at, last_attempt_at, sent_at, created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 68 | `task_reminder_outbox_attempts` → `task_reminder_outbox_attempts` | `B_operational_audit` | yes | `task_reminder_outbox_attempt_id` | organizations, task_reminder_outbox, tasks | JSON semantic: details; Timestamp: attempted_at, created_at | count+primary_keys+canonical_row_hash+relations |
| 69 | `internal_notifications` → `internal_notifications` | `B_operational_audit` | yes | `internal_notification_id` | billing_next_step_events, organizations, users | Date: planned_for; Timestamp: created_at | count+primary_keys+canonical_row_hash+relations |
| 70 | `internal_notification_state_events` → `internal_notification_state_events` | `B_operational_audit` | yes | `internal_notification_state_event_id` | internal_notifications, organizations, users | Timestamp: created_at | count+primary_keys+canonical_row_hash+relations |
| 71 | `internal_notification_schedules` → `internal_notification_schedules` | `A_business` | yes | `internal_notification_schedule_id` | organizations, users | Timestamp: next_run_at_utc, created_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| 72 | `internal_notification_schedule_runs` → `internal_notification_schedule_runs` | `B_operational_audit` | yes | `internal_notification_schedule_run_id` | internal_notification_schedules, organizations, users | Date: scheduled_local_date, as_of_date; Timestamp: lease_expires_at_utc, next_attempt_at_utc, started_at, finished_at, created_at | count+primary_keys+canonical_row_hash+relations |
| 73 | `user_module_inbox_state` → `user_module_inbox_state` | `A_business` | yes | `user_module_inbox_state_id` | event_logs, organizations, users | Timestamp: last_seen_at, updated_at | count+primary_keys+canonical_row_hash+relations |
| — | `casi_schema_metadata` → `casi_schema_metadata` | `D_runtime_temporary` | no | `schema_key` | — | Timestamp: updated_at | Excluded: Techniczny znacznik wersji schematu jest tworzony przez schema bootstrap targetu. Rebuild: Uruchom python -m app.cli.database_migrate --apply na pustym targetcie. |
| — | `google_calendar_oauth_states` → `google_calendar_oauth_states` | `D_runtime_temporary` | no | `google_calendar_oauth_state_id` | users | Timestamp: expires_at, created_at | Excluded: Krotkozyjace tokeny state OAuth nie moga byc przenoszone miedzy srodowiskami. Rebuild: Rozpocznij nowy flow OAuth; rekordy wygasaja automatycznie. |
| — | `system_email_oauth_states` → `system_email_oauth_states` | `D_runtime_temporary` | no | `system_email_oauth_state_id` | users | Timestamp: expires_at, created_at | Excluded: Krotkozyjace tokeny state OAuth nie moga byc przenoszone miedzy srodowiskami. Rebuild: Rozpocznij nowy flow OAuth; rekordy wygasaja automatycznie. |
| — | `task_reminder_worker_heartbeats` → `task_reminder_worker_heartbeats` | `D_runtime_temporary` | no | `task_reminder_worker_heartbeat_id` | — | Timestamp: last_heartbeat_at, last_success_at, last_error_at, created_at, updated_at | Excluded: Heartbeat opisuje konkretny proces i host, a nie trwaly stan biznesowy. Rebuild: Jawnie uruchomiony worker utworzy nowy heartbeat. |
| — | `user_sessions` → `user_sessions` | `D_runtime_temporary` | no | `session_id` | users | Timestamp: created_at, last_seen_at, expires_at | Excluded: Sesje i hashe tokenow sa zwiazane ze srodowiskiem i nie powinny byc przenoszone. Rebuild: Uzytkownicy loguja sie ponownie w nowym srodowisku. |

## Classification decisions

- `A_business`: durable domain data, including organizations, users, documents, knowledge, tasks, decisions, billing, payment and ledger records, next-step histories, persistent notifications, schedules, and schedule runs.
- `B_operational_audit`: durable operational history and audit data, including imports, outbox attempts, automation executions, whiteboard events, and `event_logs`.
- `D_runtime_temporary`: only `casi_schema_metadata`, OAuth state tables, worker heartbeats, and environment-bound sessions. Schema metadata is recreated by the schema bootstrap; OAuth states are deliberately short-lived and users repeat authorization; heartbeats are process state; sessions are invalidated and users sign in again.
- No current table is classified as rebuildable (`C`) or legacy (`E`): without a certain deterministic rebuild or a separate retention decision, data is treated as durable.

## Explicit legacy source compatibility

The manifest narrowly supports the known pre-bootstrap SQLite shape without relaxing unknown schema differences: absent `internal_notifications`, `internal_notification_state_events`, `internal_notification_schedules`, and `internal_notification_schedule_runs` are treated as empty because a table that never existed cannot contain records; an absent historical `billing_next_step_events.parent_event_id` is read as `NULL`. Missing excluded runtime tables are not blockers. Every other absent table, missing/extra column, or unclassified table remains a blocking error. Physical SQLite column order is irrelevant because reads, canonical hashes, and parameterized inserts use the manifest's explicit column names and order.

## KSeF override integrity

`invoice_ksef_field_overrides` has two valid modes. A direct correction already approved by an authorized user has `approval_request_id = NULL` and `status = approved`. Every other correction is approval-linked: its non-NULL `approval_request_id` must identify an existing `approval_requests` row whose `organization_id` matches the override, whose `entity_type` is `invoice`, and whose `entity_id` matches `invoice_id`. The referenced invoice must also exist in the same organization.

The repository validates this invariant atomically before insert and does not allow a generic update to reparent an override. SQLite enables foreign keys for every application connection. Approval requests have no public delete path and the FK blocks direct deletion while linked history exists. Test resets drop overrides before approval requests so stale test rows cannot survive ID reuse. The migration plan independently treats orphaned or cross-context overrides as blockers.

A historical test database may contain five known stale fixture rows because an older reset script dropped approval requests but omitted overrides while SQLite FK enforcement was connection-local and disabled. The reviewed one-time cleanup is deletion of exactly override IDs `1`–`5`, only when they all reference missing approval ID `1` and all strict preconditions match. This procedure must first be tested on a binary copy. Running it on any original database requires separate explicit authorization.

## Type and identity rules

- Primary keys, foreign keys, organization and recipient IDs, event parents, append-only order, and original timestamps are retained.
- Booleans normalize only accepted boolean representations; money and decimal fields use `Decimal`, never float.
- JSON is compared semantically with stable key ordering. Invalid declared JSON blocks the source plan.
- Calendar dates such as `planned_for` remain `YYYY-MM-DD`. Zoned timestamps compare as the same UTC instant; historical naive timestamps retain their wall-clock text and are marked as naive for verification.
- BLOB values, where present, are compared through canonical base64. Empty strings and `NULL` remain distinct.
- PostgreSQL sequences are reset after all inserts using `pg_get_serial_sequence` and the migrated maximum ID.
- Composite keys are ordered and verified as complete tuples. Inserts use placeholders; manifest identifiers are allowlisted.

## Plan, apply, and verify

```text
python migrate_sqlite_to_configured_db.py plan --source-sqlite <copy.sqlite3> --output <plan.json>
python migrate_sqlite_to_configured_db.py apply --source-sqlite <copy.sqlite3> --output <apply.json>
python migrate_sqlite_to_configured_db.py verify --source-sqlite <copy.sqlite3> --output <verify.json>
```

`plan` opens the explicit SQLite source with `mode=ro`, `immutable=1`, and `query_only=ON`. It checks schema/manifest equality, `quick_check`, JSON, storage paths, foreign keys, tenant-sensitive domain relations, counts, keys, NULL counts, and canonical hashes. It reports no row payloads or secret configuration.

`apply` additionally requires an explicit PostgreSQL engine and DSN. It validates the target schema, refuses any non-empty persistent target, and copies all persistent tables in one target transaction. Any exception rolls the transaction back. Restart means recreating or clearing the disposable empty target through a separately controlled operation; the migrator never truncates or guesses a resume point.

`verify` is read-only on both sides and compares counts, exact primary-key sets, missing/extra IDs, per-row canonical hashes, and table canonical hashes. Source-side domain checks cover foreign keys, billing next-step parents, notification sources/states, and scheduler schedule/run ownership.

## Storage boundary

The data migration preserves portable storage keys and metadata but never moves files. Any Windows drive path, UNC path, or `file://` value in a declared storage column is a blocker reported only by table, column, and primary key. Such a value requires a separate reviewed transform; it is never rewritten automatically.

## Known limitations and staging gate

- A real PostgreSQL execution remains mandatory on a newly created disposable database before staging activation when no local PostgreSQL runtime or explicit test DSN is available.
- Runtime PostgreSQL validation must run schema migration, apply the synthetic fixture, verify every table, test post-reset sequence inserts, rerun verify, and then destroy only the explicitly disposable database.
- Files and S3-compatible storage migration are separate work. This tool has no incremental sync, CDC, two-way merge, or production rollback mechanism.
- Historical naive timestamps are intentionally not assigned an invented timezone.

## Adding a future table

1. Add equivalent explicit SQLite and PostgreSQL schema definitions and repository/domain tests.
2. Add exactly one `TableMigrationSpec` with category, columns, primary key, dependencies, order, transformations, verification, sequence decision, and storage-column audit.
3. If excluded, document a safe rebuild/re-authentication procedure and why no durable history is lost.
4. Add a representative fixture and type/relationship assertions.
5. Run `tests.test_data_migration_coverage`; an unclassified or column-mismatched table must fail.
6. Run migrator, schema migration, audit, staging preflight, billing, notifications, scheduler, HTTP, model, DOM, typecheck, and production build regressions.
7. Repeat source plan on a binary copy and the disposable PostgreSQL staging gate before connecting production.
