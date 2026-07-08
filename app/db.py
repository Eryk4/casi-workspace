from __future__ import annotations

import os
import sqlite3
import time
from contextlib import contextmanager
from typing import Any, Iterable

from app.config import DATABASE_URL, SQLITE_DB_PATH, DB_ENGINE, ensure_directories
from app.domain.constants import (
    COORDINATOR_ROLE,
    GUEST_ROLE,
    KNOWLEDGE_MANAGE_CAPABILITY,
    KNOWLEDGE_UPLOAD_CAPABILITY,
    KNOWLEDGE_SYNC_CAPABILITY,
    OPERATOR_ROLE,
    ORGANIZATION_ADMIN_ROLE,
    SYSTEM_OWNER_ROLE,
    default_capabilities_for_role,
)
from app.utils import now_iso

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover - zależne od środowiska uruchomieniowego
    psycopg = None
    dict_row = None

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:  # pragma: no cover - zależne od środowiska uruchomieniowego
    psycopg2 = None
    RealDictCursor = None




SQLITE_SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS organizations (
    organization_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    module_shortcuts_json TEXT NOT NULL DEFAULT '{}',
    communication_provider TEXT NOT NULL DEFAULT 'telegram',
    communication_config_json TEXT NOT NULL DEFAULT '{}',
    shared_note_text TEXT NOT NULL DEFAULT '',
    shared_note_updated_at TEXT,
    shared_note_updated_by_user_id INTEGER,
    telegram_chat_id TEXT,
    telegram_chat_name TEXT,
    email_inbox_address TEXT,
    email_allowed_sender TEXT,
    email_subject_keyword TEXT,
    email_integration_enabled INTEGER NOT NULL DEFAULT 0,
    email_last_checked_at TEXT,
    email_last_check_status TEXT,
    email_last_connection_tested_at TEXT,
    email_last_connection_status TEXT,
    ksef_company_identifier TEXT,
    ksef_environment TEXT,
    ksef_integration_enabled INTEGER NOT NULL DEFAULT 0,
    ksef_last_checked_at TEXT,
    ksef_last_check_status TEXT,
    ksef_last_connection_tested_at TEXT,
    ksef_last_connection_status TEXT,
    ksef_correction_delegate_user_id INTEGER,
    ksef_correction_delegate_assigned_at TEXT,
    ksef_correction_delegate_expires_at TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS contractors (
    contractor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER,
    name TEXT NOT NULL,
    nip TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    is_new INTEGER NOT NULL DEFAULT 1,
    last_invoice_date TEXT,
    last_invoice_number TEXT,
    invoice_count INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_contractors_org_nip ON contractors(organization_id, nip);

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    login TEXT NOT NULL UNIQUE,
    display_name TEXT,
    telegram_user_id TEXT UNIQUE,
    telegram_reminders_enabled INTEGER NOT NULL DEFAULT 1,
    reminder_quiet_hours_start TEXT,
    reminder_quiet_hours_end TEXT,
    reminder_repeat_interval_minutes INTEGER NOT NULL DEFAULT 0,
    organization_id INTEGER,
    password_hash TEXT NOT NULL,
    password_salt TEXT NOT NULL,
    role TEXT NOT NULL,
    can_upload_knowledge INTEGER,
    personal_note_text TEXT NOT NULL DEFAULT '',
    personal_note_updated_at TEXT,
    workspace_state_json TEXT,
    workspace_state_updated_at TEXT,
    workspace_state_device_id TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    last_login_at TEXT,
    created_by_user_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id),
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE INDEX IF NOT EXISTS idx_users_login ON users(login);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_telegram_user_id ON users(telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_users_organization_id ON users(organization_id);

CREATE TABLE IF NOT EXISTS user_calendars (
    user_calendar_id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id INTEGER NOT NULL,
    provider TEXT NOT NULL DEFAULT 'google_ics',
    display_name TEXT NOT NULL,
    calendar_kind TEXT NOT NULL DEFAULT 'inne',
    linked_organization_id INTEGER,
    default_duration_minutes INTEGER NOT NULL DEFAULT 60,
    description TEXT,
    sync_token TEXT NOT NULL UNIQUE,
    external_calendar_id TEXT,
    external_calendar_name TEXT,
    external_calendar_timezone TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (linked_organization_id) REFERENCES organizations(organization_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_user_calendars_owner_display_name ON user_calendars(owner_user_id, display_name);
CREATE INDEX IF NOT EXISTS idx_user_calendars_owner_user_id ON user_calendars(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_user_calendars_linked_organization_id ON user_calendars(linked_organization_id);
CREATE INDEX IF NOT EXISTS idx_user_calendars_external_calendar_id ON user_calendars(external_calendar_id);

CREATE TABLE IF NOT EXISTS user_google_calendar_connections (
    user_google_calendar_connection_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    google_email TEXT,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_expires_at TEXT NOT NULL,
    scope TEXT,
    employee_visibility_confirmed INTEGER NOT NULL DEFAULT 0,
    employee_confirmation_at TEXT,
    approval_status TEXT NOT NULL DEFAULT 'pending_approval',
    approved_by_user_id INTEGER,
    approved_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (approved_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_google_calendar_connections_user_id
    ON user_google_calendar_connections(user_id);
CREATE INDEX IF NOT EXISTS idx_user_google_calendar_connections_approval_status
    ON user_google_calendar_connections(approval_status);

CREATE TABLE IF NOT EXISTS user_calendar_assignments (
    user_calendar_assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    user_calendar_id INTEGER NOT NULL,
    assigned_by_user_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (user_calendar_id) REFERENCES user_calendars(user_calendar_id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_calendar_assignments_user_calendar_id
    ON user_calendar_assignments(user_calendar_id);
CREATE INDEX IF NOT EXISTS idx_user_calendar_assignments_assigned_by_user_id
    ON user_calendar_assignments(assigned_by_user_id);

CREATE TABLE IF NOT EXISTS google_calendar_oauth_states (
    google_calendar_oauth_state_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    state_token TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_google_calendar_oauth_states_state_token
    ON google_calendar_oauth_states(state_token);
CREATE INDEX IF NOT EXISTS idx_google_calendar_oauth_states_expires_at
    ON google_calendar_oauth_states(expires_at);

CREATE TABLE IF NOT EXISTS user_sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    device_id TEXT,
    device_label TEXT,
    ip_address TEXT,
    user_agent TEXT,
    created_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_device_id ON user_sessions(device_id);

CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER,
    incoming_date TEXT NOT NULL,
    source TEXT NOT NULL,
    file_name TEXT NOT NULL,
    document_type TEXT,
    invoice_number TEXT,
    ksef_number TEXT,
    issuer_nip TEXT,
    issuer_name TEXT,
    issue_date TEXT,
    sale_date TEXT,
    gross_amount REAL,
    currency TEXT NOT NULL DEFAULT 'PLN',
    status TEXT NOT NULL,
    duplicate_type TEXT NOT NULL DEFAULT 'brak',
    flag_reason TEXT,
    contractor_id INTEGER,
    file_link TEXT,
    file_storage_key TEXT,
    ocr_link TEXT,
    ocr_storage_key TEXT,
    storage_backend TEXT,
    source_external_id TEXT,
    source_sender_name TEXT,
    source_sender_id TEXT,
    source_metadata TEXT,
    invoice_hash TEXT NOT NULL UNIQUE,
    ocr_raw_text TEXT,
    ocr_confidence REAL,
    assigned_user_id INTEGER,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (contractor_id) REFERENCES contractors(contractor_id),
    FOREIGN KEY (assigned_user_id) REFERENCES users(user_id),
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE INDEX IF NOT EXISTS idx_invoices_ksef_number ON invoices(ksef_number);
CREATE INDEX IF NOT EXISTS idx_invoices_number_nip ON invoices(invoice_number, issuer_nip);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_source ON invoices(source);
CREATE INDEX IF NOT EXISTS idx_invoices_organization_id ON invoices(organization_id);
CREATE INDEX IF NOT EXISTS idx_invoices_assigned_user_id ON invoices(assigned_user_id);

CREATE TABLE IF NOT EXISTS tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    task_type TEXT NOT NULL,
    visibility_scope TEXT NOT NULL DEFAULT 'prywatne',
    owner_user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,
    priority TEXT NOT NULL,
    due_at TEXT,
    remind_at TEXT,
    recurrence_pattern TEXT NOT NULL DEFAULT 'brak',
    recurrence_interval INTEGER NOT NULL DEFAULT 1,
    recurrence_weekdays TEXT,
    recurrence_end_at TEXT,
    recurrence_series_id TEXT,
    recurrence_parent_task_id INTEGER,
    reminder_sent_at TEXT,
    reminder_last_attempt_at TEXT,
    reminder_last_error TEXT,
    assigned_user_id INTEGER,
    calendar_id INTEGER,
    calendar_duration_minutes INTEGER NOT NULL DEFAULT 60,
    external_calendar_event_id TEXT,
    external_calendar_event_url TEXT,
    external_calendar_synced_at TEXT,
    external_calendar_sync_error TEXT,
    external_calendar_sync_state TEXT,
    external_calendar_sync_message TEXT,
    external_calendar_last_checked_at TEXT,
    external_calendar_last_check_error TEXT,
    external_calendar_remote_updated_at TEXT,
    external_calendar_remote_etag TEXT,
    external_calendar_last_sync_source TEXT,
    created_by_user_id INTEGER NOT NULL,
    completed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (owner_user_id) REFERENCES users(user_id),
    FOREIGN KEY (assigned_user_id) REFERENCES users(user_id),
    FOREIGN KEY (calendar_id) REFERENCES user_calendars(user_calendar_id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_tasks_organization_id ON tasks(organization_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_due_at ON tasks(due_at);
CREATE INDEX IF NOT EXISTS idx_tasks_remind_at ON tasks(remind_at);
CREATE INDEX IF NOT EXISTS idx_tasks_reminder_sent_at ON tasks(reminder_sent_at);
CREATE INDEX IF NOT EXISTS idx_tasks_reminder_last_attempt_at ON tasks(reminder_last_attempt_at);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_user_id ON tasks(assigned_user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_owner_user_id ON tasks(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_visibility_scope ON tasks(visibility_scope);
CREATE INDEX IF NOT EXISTS idx_tasks_calendar_id ON tasks(calendar_id);
CREATE INDEX IF NOT EXISTS idx_tasks_external_calendar_event_id ON tasks(external_calendar_event_id);
CREATE INDEX IF NOT EXISTS idx_tasks_recurrence_pattern ON tasks(recurrence_pattern);
CREATE INDEX IF NOT EXISTS idx_tasks_recurrence_series_id ON tasks(recurrence_series_id);

CREATE TABLE IF NOT EXISTS task_visibility_users (
    task_visibility_user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    organization_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_task_visibility_users_unique ON task_visibility_users(task_id, user_id);
CREATE INDEX IF NOT EXISTS idx_task_visibility_users_task_id ON task_visibility_users(task_id);
CREATE INDEX IF NOT EXISTS idx_task_visibility_users_user_id ON task_visibility_users(user_id);

CREATE TABLE IF NOT EXISTS task_links (
    task_link_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    organization_id INTEGER NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    created_by_user_id INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_task_links_unique ON task_links(task_id, entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_task_links_entity ON task_links(organization_id, entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_task_links_task_id ON task_links(task_id);

CREATE TABLE IF NOT EXISTS task_notes (
    task_note_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    organization_id INTEGER NOT NULL,
    parent_note_id INTEGER,
    note_kind TEXT NOT NULL DEFAULT 'comment',
    note_text TEXT NOT NULL,
    mentioned_user_ids TEXT,
    mentioned_user_names TEXT,
    created_by_user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (parent_note_id) REFERENCES task_notes(task_note_id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_task_notes_task_id ON task_notes(task_id);
CREATE INDEX IF NOT EXISTS idx_task_notes_parent_note_id ON task_notes(parent_note_id);

CREATE TABLE IF NOT EXISTS task_checklist_items (
    task_checklist_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    organization_id INTEGER NOT NULL,
    item_text TEXT NOT NULL,
    item_order INTEGER NOT NULL DEFAULT 0,
    is_completed INTEGER NOT NULL DEFAULT 0,
    completed_at TEXT,
    completed_by_user_id INTEGER,
    created_by_user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (completed_by_user_id) REFERENCES users(user_id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_task_checklist_items_task_id ON task_checklist_items(task_id);
CREATE INDEX IF NOT EXISTS idx_task_checklist_items_task_order ON task_checklist_items(task_id, item_order);

CREATE TABLE IF NOT EXISTS task_templates (
    task_template_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    template_name TEXT NOT NULL,
    template_description TEXT,
    task_type TEXT NOT NULL DEFAULT 'zadanie',
    priority TEXT NOT NULL DEFAULT 'normalny',
    visibility_scope TEXT NOT NULL DEFAULT 'prywatne',
    due_offset_minutes INTEGER,
    reminder_offset_minutes INTEGER,
    recurrence_pattern TEXT NOT NULL DEFAULT 'brak',
    recurrence_interval INTEGER NOT NULL DEFAULT 1,
    recurrence_weekdays TEXT,
    recurrence_end_offset_minutes INTEGER,
    calendar_duration_minutes INTEGER NOT NULL DEFAULT 60,
    checklist_json TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_by_user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_task_templates_org_active ON task_templates(organization_id, is_active);
CREATE INDEX IF NOT EXISTS idx_task_templates_org_name ON task_templates(organization_id, template_name);

CREATE TABLE IF NOT EXISTS approval_requests (
    approval_request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    requested_by_user_id INTEGER NOT NULL,
    requested_user_id INTEGER,
    approve_status TEXT,
    reject_status TEXT,
    metadata_json TEXT,
    requested_at TEXT NOT NULL,
    decided_by_user_id INTEGER,
    decided_at TEXT,
    decision_reason TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (requested_by_user_id) REFERENCES users(user_id),
    FOREIGN KEY (requested_user_id) REFERENCES users(user_id),
    FOREIGN KEY (decided_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_approval_requests_org_status
    ON approval_requests(organization_id, status);
CREATE INDEX IF NOT EXISTS idx_approval_requests_entity
    ON approval_requests(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_approval_requests_requested_user
    ON approval_requests(requested_user_id);

CREATE TABLE IF NOT EXISTS invoice_ksef_field_overrides (
    invoice_ksef_field_override_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    invoice_id INTEGER NOT NULL,
    approval_request_id INTEGER,
    field_name TEXT NOT NULL,
    source_value TEXT,
    local_value TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    requested_by_user_id INTEGER,
    approved_by_user_id INTEGER,
    rejected_by_user_id INTEGER,
    request_reason TEXT,
    decision_reason TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    approved_at TEXT,
    rejected_at TEXT,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (invoice_id) REFERENCES invoices(id),
    FOREIGN KEY (approval_request_id) REFERENCES approval_requests(approval_request_id),
    FOREIGN KEY (requested_by_user_id) REFERENCES users(user_id),
    FOREIGN KEY (approved_by_user_id) REFERENCES users(user_id),
    FOREIGN KEY (rejected_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_invoice_ksef_overrides_invoice_status
    ON invoice_ksef_field_overrides(invoice_id, status);
CREATE INDEX IF NOT EXISTS idx_invoice_ksef_overrides_request
    ON invoice_ksef_field_overrides(approval_request_id);

CREATE TABLE IF NOT EXISTS task_attachments (
    task_attachment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    organization_id INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    mime_type TEXT,
    file_size INTEGER NOT NULL DEFAULT 0,
    file_link TEXT NOT NULL,
    file_storage_key TEXT NOT NULL,
    storage_backend TEXT NOT NULL DEFAULT 'lokalny',
    uploaded_by_user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (uploaded_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_task_attachments_task_id ON task_attachments(task_id);
CREATE INDEX IF NOT EXISTS idx_task_attachments_org_id ON task_attachments(organization_id);

CREATE TABLE IF NOT EXISTS task_history (
    task_history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    organization_id INTEGER NOT NULL,
    action_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    message TEXT NOT NULL,
    details TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE INDEX IF NOT EXISTS idx_task_history_task_id ON task_history(task_id);

CREATE TABLE IF NOT EXISTS work_items (
    work_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'manual',
    source_id INTEGER,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'nowe',
    priority_level TEXT NOT NULL DEFAULT 'normalny',
    priority_score REAL NOT NULL DEFAULT 0,
    assigned_user_id INTEGER,
    created_by_user_id INTEGER NOT NULL,
    updated_by_user_id INTEGER,
    due_at TEXT,
    sla_deadline_at TEXT,
    sla_warning_minutes INTEGER NOT NULL DEFAULT 120,
    sla_warning_at TEXT,
    sla_stage TEXT NOT NULL DEFAULT 'on_track',
    reminder_sent_at TEXT,
    escalation_sent_at TEXT,
    resolved_at TEXT,
    last_sla_transition_at TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (assigned_user_id) REFERENCES users(user_id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id),
    FOREIGN KEY (updated_by_user_id) REFERENCES users(user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_work_items_org_source
    ON work_items(organization_id, source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_work_items_org_status
    ON work_items(organization_id, status);
CREATE INDEX IF NOT EXISTS idx_work_items_org_priority_score
    ON work_items(organization_id, priority_score);
CREATE INDEX IF NOT EXISTS idx_work_items_org_sla_deadline
    ON work_items(organization_id, sla_deadline_at);
CREATE INDEX IF NOT EXISTS idx_work_items_org_sla_stage
    ON work_items(organization_id, sla_stage);
CREATE INDEX IF NOT EXISTS idx_work_items_assigned_user_id
    ON work_items(assigned_user_id);

CREATE TABLE IF NOT EXISTS work_item_history (
    work_item_history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_item_id INTEGER NOT NULL,
    organization_id INTEGER NOT NULL,
    action_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    message TEXT NOT NULL,
    details TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (work_item_id) REFERENCES work_items(work_item_id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE INDEX IF NOT EXISTS idx_work_item_history_item_id
    ON work_item_history(work_item_id);
CREATE INDEX IF NOT EXISTS idx_work_item_history_org_id
    ON work_item_history(organization_id);

CREATE TABLE IF NOT EXISTS task_reminder_outbox (
    task_reminder_outbox_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    task_id INTEGER NOT NULL,
    delivery_channel TEXT NOT NULL,
    delivery_key TEXT NOT NULL,
    delivery_anchor_at TEXT NOT NULL,
    recipient_user_id INTEGER NOT NULL,
    recipient_telegram_user_id TEXT NOT NULL,
    available_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    retryable INTEGER NOT NULL DEFAULT 1,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    claimed_at TEXT,
    claimed_by TEXT,
    last_attempt_at TEXT,
    last_error TEXT,
    sent_at TEXT,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (recipient_user_id) REFERENCES users(user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_task_reminder_outbox_unique
    ON task_reminder_outbox(task_id, delivery_channel, delivery_key);
CREATE INDEX IF NOT EXISTS idx_task_reminder_outbox_status_available
    ON task_reminder_outbox(status, available_at);
CREATE INDEX IF NOT EXISTS idx_task_reminder_outbox_org_status
    ON task_reminder_outbox(organization_id, status);
CREATE INDEX IF NOT EXISTS idx_task_reminder_outbox_task_id
    ON task_reminder_outbox(task_id);

CREATE TABLE IF NOT EXISTS task_reminder_outbox_attempts (
    task_reminder_outbox_attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_reminder_outbox_id INTEGER NOT NULL,
    organization_id INTEGER NOT NULL,
    task_id INTEGER NOT NULL,
    delivery_channel TEXT NOT NULL,
    attempt_no INTEGER NOT NULL,
    outcome TEXT NOT NULL,
    attempted_at TEXT NOT NULL,
    worker_name TEXT NOT NULL,
    error_message TEXT,
    details TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (task_reminder_outbox_id) REFERENCES task_reminder_outbox(task_reminder_outbox_id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_task_reminder_outbox_attempts_outbox_id
    ON task_reminder_outbox_attempts(task_reminder_outbox_id);
CREATE INDEX IF NOT EXISTS idx_task_reminder_outbox_attempts_task_id
    ON task_reminder_outbox_attempts(task_id);
CREATE INDEX IF NOT EXISTS idx_task_reminder_outbox_attempts_org_id
    ON task_reminder_outbox_attempts(organization_id);

CREATE TABLE IF NOT EXISTS task_reminder_worker_heartbeats (
    task_reminder_worker_heartbeat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_name TEXT NOT NULL UNIQUE,
    worker_role TEXT NOT NULL,
    process_id INTEGER,
    state TEXT NOT NULL DEFAULT 'idle',
    last_heartbeat_at TEXT NOT NULL,
    last_success_at TEXT,
    last_error_at TEXT,
    last_error_message TEXT,
    cycles_completed INTEGER NOT NULL DEFAULT 0,
    processed_total INTEGER NOT NULL DEFAULT 0,
    sent_total INTEGER NOT NULL DEFAULT 0,
    failed_total INTEGER NOT NULL DEFAULT 0,
    deferred_total INTEGER NOT NULL DEFAULT 0,
    retrying_total INTEGER NOT NULL DEFAULT 0,
    skipped_total INTEGER NOT NULL DEFAULT 0,
    queue_total INTEGER NOT NULL DEFAULT 0,
    queue_due INTEGER NOT NULL DEFAULT 0,
    queue_failed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_task_reminder_worker_heartbeats_role
    ON task_reminder_worker_heartbeats(worker_role);
CREATE INDEX IF NOT EXISTS idx_task_reminder_worker_heartbeats_state
    ON task_reminder_worker_heartbeats(state);
CREATE INDEX IF NOT EXISTS idx_task_reminder_worker_heartbeats_heartbeat_at
    ON task_reminder_worker_heartbeats(last_heartbeat_at);

CREATE TABLE IF NOT EXISTS billing_schools (
    billing_school_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    full_name TEXT NOT NULL,
    short_name TEXT NOT NULL,
    city TEXT,
    notes TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_schools_org_full_name
    ON billing_schools(organization_id, full_name);
CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_schools_org_short_name
    ON billing_schools(organization_id, short_name);
CREATE INDEX IF NOT EXISTS idx_billing_schools_org
    ON billing_schools(organization_id);

CREATE TABLE IF NOT EXISTS billing_models (
    billing_model_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    profile_type TEXT NOT NULL DEFAULT 'education_student',
    school_year TEXT NOT NULL,
    lesson_day TEXT,
    settlement_mode TEXT NOT NULL,
    monthly_rate_amount REAL,
    semester_rate_amount REAL,
    sibling_discount_amount REAL NOT NULL DEFAULT 100,
    large_family_discount_amount REAL NOT NULL DEFAULT 50,
    intro_free_lessons_count INTEGER NOT NULL DEFAULT 1,
    contract_required INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_models_org_name
    ON billing_models(organization_id, name);
CREATE INDEX IF NOT EXISTS idx_billing_models_org
    ON billing_models(organization_id);

CREATE TABLE IF NOT EXISTS billing_payers (
    billing_payer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    display_name TEXT,
    contact_phone TEXT NOT NULL,
    payment_identifier TEXT NOT NULL,
    has_large_family_card INTEGER NOT NULL DEFAULT 0,
    email TEXT,
    notes TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_payers_org_payment_identifier
    ON billing_payers(organization_id, payment_identifier);
CREATE INDEX IF NOT EXISTS idx_billing_payers_org
    ON billing_payers(organization_id);

CREATE TABLE IF NOT EXISTS billing_students (
    billing_student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    billing_payer_id INTEGER NOT NULL,
    billing_school_id INTEGER,
    billing_model_id INTEGER,
    full_name TEXT NOT NULL,
    lesson_day TEXT,
    family_billing_order INTEGER NOT NULL DEFAULT 1,
    group_name TEXT,
    notes TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (billing_payer_id) REFERENCES billing_payers(billing_payer_id),
    FOREIGN KEY (billing_school_id) REFERENCES billing_schools(billing_school_id),
    FOREIGN KEY (billing_model_id) REFERENCES billing_models(billing_model_id)
);

CREATE INDEX IF NOT EXISTS idx_billing_students_org
    ON billing_students(organization_id);
CREATE INDEX IF NOT EXISTS idx_billing_students_payer
    ON billing_students(billing_payer_id);
CREATE INDEX IF NOT EXISTS idx_billing_students_school
    ON billing_students(billing_school_id);
CREATE INDEX IF NOT EXISTS idx_billing_students_model
    ON billing_students(billing_model_id);

CREATE TABLE IF NOT EXISTS billing_charge_batches (
    billing_charge_batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    billing_model_id INTEGER NOT NULL,
    school_year TEXT NOT NULL,
    period_type TEXT NOT NULL,
    period_label TEXT NOT NULL,
    due_date TEXT NOT NULL,
    lesson_count INTEGER NOT NULL DEFAULT 0,
    generated_by_user_id INTEGER,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (billing_model_id) REFERENCES billing_models(billing_model_id),
    FOREIGN KEY (generated_by_user_id) REFERENCES users(user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_charge_batches_org_model_period
    ON billing_charge_batches(organization_id, billing_model_id, period_label);
CREATE INDEX IF NOT EXISTS idx_billing_charge_batches_org
    ON billing_charge_batches(organization_id);
CREATE INDEX IF NOT EXISTS idx_billing_charge_batches_model
    ON billing_charge_batches(billing_model_id);

CREATE TABLE IF NOT EXISTS billing_charges (
    billing_charge_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    billing_charge_batch_id INTEGER NOT NULL,
    billing_model_id INTEGER NOT NULL,
    billing_student_id INTEGER NOT NULL,
    billing_payer_id INTEGER NOT NULL,
    school_year TEXT NOT NULL,
    period_label TEXT NOT NULL,
    due_date TEXT NOT NULL,
    lesson_count INTEGER NOT NULL DEFAULT 0,
    unit_rate_amount REAL NOT NULL,
    base_amount REAL NOT NULL,
    intro_free_discount_amount REAL NOT NULL DEFAULT 0,
    sibling_discount_amount REAL NOT NULL DEFAULT 0,
    large_family_discount_amount REAL NOT NULL DEFAULT 0,
    total_amount REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'otwarta',
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (billing_charge_batch_id) REFERENCES billing_charge_batches(billing_charge_batch_id),
    FOREIGN KEY (billing_model_id) REFERENCES billing_models(billing_model_id),
    FOREIGN KEY (billing_student_id) REFERENCES billing_students(billing_student_id),
    FOREIGN KEY (billing_payer_id) REFERENCES billing_payers(billing_payer_id)
);

CREATE INDEX IF NOT EXISTS idx_billing_charges_org
    ON billing_charges(organization_id);
CREATE INDEX IF NOT EXISTS idx_billing_charges_batch
    ON billing_charges(billing_charge_batch_id);
CREATE INDEX IF NOT EXISTS idx_billing_charges_model
    ON billing_charges(billing_model_id);
CREATE INDEX IF NOT EXISTS idx_billing_charges_student
    ON billing_charges(billing_student_id);
CREATE INDEX IF NOT EXISTS idx_billing_charges_payer
    ON billing_charges(billing_payer_id);

CREATE TABLE IF NOT EXISTS billing_student_charge_state (
    billing_student_charge_state_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    billing_student_id INTEGER NOT NULL,
    school_year TEXT NOT NULL,
    intro_free_lessons_remaining INTEGER NOT NULL DEFAULT 0,
    sibling_discount_remaining_amount REAL NOT NULL DEFAULT 0,
    sibling_discount_initialized INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (billing_student_id) REFERENCES billing_students(billing_student_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_student_charge_state_org_student_year
    ON billing_student_charge_state(organization_id, billing_student_id, school_year);

CREATE TABLE IF NOT EXISTS billing_payer_charge_state (
    billing_payer_charge_state_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    billing_payer_id INTEGER NOT NULL,
    school_year TEXT NOT NULL,
    large_family_discount_remaining_amount REAL NOT NULL DEFAULT 0,
    large_family_discount_initialized INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (billing_payer_id) REFERENCES billing_payers(billing_payer_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_payer_charge_state_org_payer_year
    ON billing_payer_charge_state(organization_id, billing_payer_id, school_year);

CREATE TABLE IF NOT EXISTS billing_bank_accounts (
    billing_bank_account_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    account_name TEXT NOT NULL,
    bank_name TEXT,
    iban TEXT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'PLN',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_bank_accounts_org_iban
    ON billing_bank_accounts(organization_id, iban);
CREATE INDEX IF NOT EXISTS idx_billing_bank_accounts_org
    ON billing_bank_accounts(organization_id);

CREATE TABLE IF NOT EXISTS billing_statement_imports (
    billing_statement_import_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    billing_bank_account_id INTEGER NOT NULL,
    source_type TEXT NOT NULL,
    source_file_name TEXT,
    imported_by_user_id INTEGER,
    imported_at TEXT NOT NULL,
    row_count INTEGER NOT NULL DEFAULT 0,
    imported_transaction_count INTEGER NOT NULL DEFAULT 0,
    skipped_transaction_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (billing_bank_account_id) REFERENCES billing_bank_accounts(billing_bank_account_id),
    FOREIGN KEY (imported_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_billing_statement_imports_org
    ON billing_statement_imports(organization_id);
CREATE INDEX IF NOT EXISTS idx_billing_statement_imports_account
    ON billing_statement_imports(billing_bank_account_id);

CREATE TABLE IF NOT EXISTS billing_transactions (
    billing_transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    billing_bank_account_id INTEGER NOT NULL,
    billing_statement_import_id INTEGER,
    booking_date TEXT NOT NULL,
    value_date TEXT,
    amount REAL NOT NULL,
    currency TEXT NOT NULL DEFAULT 'PLN',
    direction TEXT NOT NULL,
    counterparty_name TEXT,
    counterparty_account TEXT,
    title TEXT,
    reference TEXT,
    raw_data TEXT,
    transaction_hash TEXT NOT NULL,
    matched_status TEXT NOT NULL DEFAULT 'nieprzypisana',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (billing_bank_account_id) REFERENCES billing_bank_accounts(billing_bank_account_id),
    FOREIGN KEY (billing_statement_import_id) REFERENCES billing_statement_imports(billing_statement_import_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_transactions_unique
    ON billing_transactions(organization_id, billing_bank_account_id, transaction_hash);
CREATE INDEX IF NOT EXISTS idx_billing_transactions_org
    ON billing_transactions(organization_id);
CREATE INDEX IF NOT EXISTS idx_billing_transactions_account
    ON billing_transactions(billing_bank_account_id);
CREATE INDEX IF NOT EXISTS idx_billing_transactions_booking_date
    ON billing_transactions(booking_date DESC);

CREATE TABLE IF NOT EXISTS billing_payment_matches (
    billing_payment_match_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    billing_transaction_id INTEGER NOT NULL,
    billing_payer_id INTEGER NOT NULL,
    billing_charge_id INTEGER,
    matched_amount REAL NOT NULL,
    match_status TEXT NOT NULL DEFAULT 'dopasowana',
    match_reason TEXT,
    matched_by_user_id INTEGER,
    matched_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (billing_transaction_id) REFERENCES billing_transactions(billing_transaction_id) ON DELETE CASCADE,
    FOREIGN KEY (billing_payer_id) REFERENCES billing_payers(billing_payer_id),
    FOREIGN KEY (billing_charge_id) REFERENCES billing_charges(billing_charge_id),
    FOREIGN KEY (matched_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_billing_payment_matches_org
    ON billing_payment_matches(organization_id);
CREATE INDEX IF NOT EXISTS idx_billing_payment_matches_transaction
    ON billing_payment_matches(billing_transaction_id);
CREATE INDEX IF NOT EXISTS idx_billing_payment_matches_payer
    ON billing_payment_matches(billing_payer_id);

CREATE TABLE IF NOT EXISTS billing_payer_ledger_entries (
    billing_payer_ledger_entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    billing_payer_id INTEGER NOT NULL,
    billing_charge_id INTEGER,
    billing_transaction_id INTEGER,
    entry_kind TEXT NOT NULL,
    amount_delta REAL NOT NULL,
    balance_after REAL NOT NULL,
    note TEXT,
    created_by_user_id INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (billing_payer_id) REFERENCES billing_payers(billing_payer_id),
    FOREIGN KEY (billing_charge_id) REFERENCES billing_charges(billing_charge_id),
    FOREIGN KEY (billing_transaction_id) REFERENCES billing_transactions(billing_transaction_id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_billing_payer_ledger_entries_org
    ON billing_payer_ledger_entries(organization_id);
CREATE INDEX IF NOT EXISTS idx_billing_payer_ledger_entries_payer
    ON billing_payer_ledger_entries(billing_payer_id);
CREATE INDEX IF NOT EXISTS idx_billing_payer_ledger_entries_created_at
    ON billing_payer_ledger_entries(created_at DESC);

CREATE TABLE IF NOT EXISTS billing_notes (
    billing_note_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    billing_payer_id INTEGER NOT NULL,
    author_user_id INTEGER NOT NULL,
    note_type TEXT NOT NULL DEFAULT 'operator_note',
    note_text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (billing_payer_id) REFERENCES billing_payers(billing_payer_id) ON DELETE CASCADE,
    FOREIGN KEY (author_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_billing_notes_payer
    ON billing_notes(billing_payer_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_billing_notes_org
    ON billing_notes(organization_id);

CREATE TABLE IF NOT EXISTS billing_payment_review_events (
    billing_payment_review_event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    billing_transaction_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    note_text TEXT,
    created_by_user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (billing_transaction_id) REFERENCES billing_transactions(billing_transaction_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_billing_payment_review_events_transaction
    ON billing_payment_review_events(billing_transaction_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_billing_payment_review_events_org
    ON billing_payment_review_events(organization_id);

CREATE TABLE IF NOT EXISTS billing_work_queue_events (
    billing_work_queue_event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    issue_key TEXT NOT NULL,
    issue_type TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id INTEGER,
    action TEXT NOT NULL,
    note_text TEXT,
    created_by_user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_billing_work_queue_events_org
    ON billing_work_queue_events(organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_billing_work_queue_events_issue
    ON billing_work_queue_events(organization_id, issue_key, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_billing_work_queue_events_target
    ON billing_work_queue_events(organization_id, target_type, target_id);

CREATE TABLE IF NOT EXISTS invoice_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    related_invoice_id INTEGER NOT NULL,
    relation_type TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
    FOREIGN KEY (related_invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_invoice_relations_invoice_id ON invoice_relations(invoice_id);

CREATE TABLE IF NOT EXISTS event_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER,
    event_time TEXT NOT NULL,
    event_type TEXT NOT NULL,
    invoice_id INTEGER,
    source TEXT,
    status_before TEXT,
    status_after TEXT,
    decision_reason TEXT,
    actor TEXT NOT NULL,
    details TEXT,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id),
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE INDEX IF NOT EXISTS idx_event_logs_invoice_id ON event_logs(invoice_id);
CREATE INDEX IF NOT EXISTS idx_event_logs_event_time ON event_logs(event_time DESC);
CREATE INDEX IF NOT EXISTS idx_event_logs_organization_id ON event_logs(organization_id);

CREATE TABLE IF NOT EXISTS intake_forms (
    intake_form_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    form_name TEXT NOT NULL,
    form_slug TEXT NOT NULL,
    description TEXT,
    field_schema_json TEXT NOT NULL DEFAULT '[]',
    is_public INTEGER NOT NULL DEFAULT 1,
    allow_attachments INTEGER NOT NULL DEFAULT 1,
    default_priority TEXT NOT NULL DEFAULT 'normalny',
    default_assigned_user_id INTEGER,
    public_token TEXT NOT NULL,
    created_by_user_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (default_assigned_user_id) REFERENCES users(user_id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_intake_forms_org_slug
    ON intake_forms(organization_id, form_slug);
CREATE UNIQUE INDEX IF NOT EXISTS idx_intake_forms_public_token
    ON intake_forms(public_token);
CREATE INDEX IF NOT EXISTS idx_intake_forms_org_active
    ON intake_forms(organization_id, is_public);

CREATE TABLE IF NOT EXISTS intake_items (
    intake_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    intake_form_id INTEGER,
    source_kind TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'nowe',
    priority TEXT NOT NULL DEFAULT 'normalny',
    title TEXT NOT NULL,
    description TEXT,
    requester_name TEXT,
    requester_email TEXT,
    source_reference TEXT,
    due_at TEXT,
    metadata_json TEXT,
    assigned_user_id INTEGER,
    linked_task_id INTEGER,
    linked_invoice_id INTEGER,
    created_by_user_id INTEGER,
    last_activity_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (intake_form_id) REFERENCES intake_forms(intake_form_id),
    FOREIGN KEY (assigned_user_id) REFERENCES users(user_id),
    FOREIGN KEY (linked_task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (linked_invoice_id) REFERENCES invoices(id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_intake_items_org_status
    ON intake_items(organization_id, status);
CREATE INDEX IF NOT EXISTS idx_intake_items_org_source
    ON intake_items(organization_id, source_kind);
CREATE INDEX IF NOT EXISTS idx_intake_items_form_id
    ON intake_items(intake_form_id);
CREATE INDEX IF NOT EXISTS idx_intake_items_updated_at
    ON intake_items(updated_at DESC);

CREATE TABLE IF NOT EXISTS intake_item_comments (
    intake_item_comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    intake_item_id INTEGER NOT NULL,
    organization_id INTEGER NOT NULL,
    parent_comment_id INTEGER,
    note_text TEXT NOT NULL,
    mentioned_user_ids TEXT,
    mentioned_user_names TEXT,
    created_by_user_id INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (intake_item_id) REFERENCES intake_items(intake_item_id) ON DELETE CASCADE,
    FOREIGN KEY (parent_comment_id) REFERENCES intake_item_comments(intake_item_comment_id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_intake_item_comments_item_id
    ON intake_item_comments(intake_item_id);
CREATE INDEX IF NOT EXISTS idx_intake_item_comments_parent_id
    ON intake_item_comments(parent_comment_id);

CREATE TABLE IF NOT EXISTS intake_item_history (
    intake_item_history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    intake_item_id INTEGER NOT NULL,
    organization_id INTEGER NOT NULL,
    action_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    message TEXT NOT NULL,
    details TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (intake_item_id) REFERENCES intake_items(intake_item_id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE INDEX IF NOT EXISTS idx_intake_item_history_item_id
    ON intake_item_history(intake_item_id);
CREATE INDEX IF NOT EXISTS idx_intake_item_history_created_at
    ON intake_item_history(created_at DESC);

CREATE TABLE IF NOT EXISTS entity_attachments (
    entity_attachment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    mime_type TEXT,
    file_size INTEGER NOT NULL DEFAULT 0,
    file_link TEXT NOT NULL,
    file_storage_key TEXT NOT NULL,
    storage_backend TEXT NOT NULL DEFAULT 'lokalny',
    uploaded_by_user_id INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (uploaded_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_entity_attachments_entity
    ON entity_attachments(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_attachments_org
    ON entity_attachments(organization_id);

CREATE TABLE IF NOT EXISTS saved_views (
    saved_view_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    module_key TEXT NOT NULL,
    view_slug TEXT NOT NULL,
    view_name TEXT NOT NULL,
    description TEXT,
    view_state_json TEXT NOT NULL DEFAULT '{}',
    is_shared INTEGER NOT NULL DEFAULT 0,
    is_default INTEGER NOT NULL DEFAULT 0,
    created_by_user_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_saved_views_org_module_slug
    ON saved_views(organization_id, module_key, view_slug);
CREATE INDEX IF NOT EXISTS idx_saved_views_org_module
    ON saved_views(organization_id, module_key);

CREATE TABLE IF NOT EXISTS automation_rules (
    automation_rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    rule_slug TEXT NOT NULL,
    rule_name TEXT NOT NULL,
    description TEXT,
    trigger_event_type TEXT NOT NULL,
    conditions_json TEXT NOT NULL DEFAULT '{}',
    actions_json TEXT NOT NULL DEFAULT '[]',
    is_active INTEGER NOT NULL DEFAULT 1,
    last_processed_event_log_id INTEGER NOT NULL DEFAULT 0,
    last_run_at TEXT,
    last_result TEXT,
    execution_count INTEGER NOT NULL DEFAULT 0,
    created_by_user_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_automation_rules_org_slug
    ON automation_rules(organization_id, rule_slug);
CREATE INDEX IF NOT EXISTS idx_automation_rules_org_trigger
    ON automation_rules(organization_id, trigger_event_type, is_active);

CREATE TABLE IF NOT EXISTS automation_executions (
    automation_execution_id INTEGER PRIMARY KEY AUTOINCREMENT,
    automation_rule_id INTEGER NOT NULL,
    organization_id INTEGER NOT NULL,
    event_log_id INTEGER,
    trigger_event_type TEXT NOT NULL,
    execution_status TEXT NOT NULL,
    input_json TEXT,
    result_json TEXT,
    error_message TEXT,
    executed_at TEXT NOT NULL,
    FOREIGN KEY (automation_rule_id) REFERENCES automation_rules(automation_rule_id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE INDEX IF NOT EXISTS idx_automation_executions_rule_id
    ON automation_executions(automation_rule_id);
CREATE INDEX IF NOT EXISTS idx_automation_executions_org
    ON automation_executions(organization_id);
CREATE INDEX IF NOT EXISTS idx_automation_executions_event_log_id
    ON automation_executions(event_log_id);

CREATE TABLE IF NOT EXISTS knowledge_documents (
    knowledge_document_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    file_name TEXT NOT NULL,
    mime_type TEXT,
    file_link TEXT NOT NULL,
    file_storage_key TEXT NOT NULL,
    content_text TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    char_count INTEGER NOT NULL DEFAULT 0,
    source_type TEXT NOT NULL DEFAULT 'manual',
    library_path TEXT NOT NULL DEFAULT '',
    is_downloadable INTEGER NOT NULL DEFAULT 1,
    use_in_assistant INTEGER NOT NULL DEFAULT 1,
    business_status TEXT NOT NULL DEFAULT 'roboczy',
    business_status_before_archive TEXT,
    owner_user_id INTEGER,
    reviewer_user_id INTEGER,
    approver_user_id INTEGER,
    created_by_user_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id),
    FOREIGN KEY (owner_user_id) REFERENCES users(user_id),
    FOREIGN KEY (reviewer_user_id) REFERENCES users(user_id),
    FOREIGN KEY (approver_user_id) REFERENCES users(user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_knowledge_documents_org_storage_key
    ON knowledge_documents(organization_id, file_storage_key);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_organization_id
    ON knowledge_documents(organization_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_updated_at
    ON knowledge_documents(updated_at DESC);
"""

POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS organizations (
    organization_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    module_shortcuts_json TEXT NOT NULL DEFAULT '{}',
    communication_provider TEXT NOT NULL DEFAULT 'telegram',
    communication_config_json TEXT NOT NULL DEFAULT '{}',
    shared_note_text TEXT NOT NULL DEFAULT '',
    shared_note_updated_at TEXT,
    shared_note_updated_by_user_id BIGINT,
    telegram_chat_id TEXT,
    telegram_chat_name TEXT,
    email_inbox_address TEXT,
    email_allowed_sender TEXT,
    email_subject_keyword TEXT,
    email_integration_enabled INTEGER NOT NULL DEFAULT 0,
    email_last_checked_at TEXT,
    email_last_check_status TEXT,
    email_last_connection_tested_at TEXT,
    email_last_connection_status TEXT,
    ksef_company_identifier TEXT,
    ksef_environment TEXT,
    ksef_integration_enabled INTEGER NOT NULL DEFAULT 0,
    ksef_last_checked_at TEXT,
    ksef_last_check_status TEXT,
    ksef_last_connection_tested_at TEXT,
    ksef_last_connection_status TEXT,
    ksef_correction_delegate_user_id BIGINT,
    ksef_correction_delegate_assigned_at TEXT,
    ksef_correction_delegate_expires_at TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS contractors (
    contractor_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT,
    name TEXT NOT NULL,
    nip TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    is_new INTEGER NOT NULL DEFAULT 1,
    last_invoice_date TEXT,
    last_invoice_number TEXT,
    invoice_count INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_contractors_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_contractors_org_nip ON contractors(organization_id, nip);

CREATE TABLE IF NOT EXISTS users (
    user_id BIGSERIAL PRIMARY KEY,
    login TEXT NOT NULL UNIQUE,
    display_name TEXT,
    telegram_user_id TEXT UNIQUE,
    telegram_reminders_enabled INTEGER NOT NULL DEFAULT 1,
    reminder_quiet_hours_start TEXT,
    reminder_quiet_hours_end TEXT,
    reminder_repeat_interval_minutes INTEGER NOT NULL DEFAULT 0,
    organization_id BIGINT,
    password_hash TEXT NOT NULL,
    password_salt TEXT NOT NULL,
    role TEXT NOT NULL,
    can_upload_knowledge INTEGER,
    personal_note_text TEXT NOT NULL DEFAULT '',
    personal_note_updated_at TEXT,
    workspace_state_json TEXT,
    workspace_state_updated_at TEXT,
    workspace_state_device_id TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    last_login_at TEXT,
    created_by_user_id BIGINT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_users_creator
        FOREIGN KEY (created_by_user_id) REFERENCES users(user_id),
    CONSTRAINT fk_users_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE INDEX IF NOT EXISTS idx_users_login ON users(login);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_telegram_user_id ON users(telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_users_organization_id ON users(organization_id);

CREATE TABLE IF NOT EXISTS user_calendars (
    user_calendar_id BIGSERIAL PRIMARY KEY,
    owner_user_id BIGINT NOT NULL,
    provider TEXT NOT NULL DEFAULT 'google_ics',
    display_name TEXT NOT NULL,
    calendar_kind TEXT NOT NULL DEFAULT 'inne',
    linked_organization_id BIGINT,
    default_duration_minutes INTEGER NOT NULL DEFAULT 60,
    description TEXT,
    sync_token TEXT NOT NULL UNIQUE,
    external_calendar_id TEXT,
    external_calendar_name TEXT,
    external_calendar_timezone TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_user_calendars_owner
        FOREIGN KEY (owner_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_user_calendars_linked_organization
        FOREIGN KEY (linked_organization_id) REFERENCES organizations(organization_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_user_calendars_owner_display_name
    ON user_calendars(owner_user_id, display_name);
CREATE INDEX IF NOT EXISTS idx_user_calendars_owner_user_id
    ON user_calendars(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_user_calendars_linked_organization_id
    ON user_calendars(linked_organization_id);
CREATE INDEX IF NOT EXISTS idx_user_calendars_external_calendar_id
    ON user_calendars(external_calendar_id);

CREATE TABLE IF NOT EXISTS user_google_calendar_connections (
    user_google_calendar_connection_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    google_email TEXT,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_expires_at TEXT NOT NULL,
    scope TEXT,
    employee_visibility_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    employee_confirmation_at TEXT,
    approval_status TEXT NOT NULL DEFAULT 'pending_approval',
    approved_by_user_id BIGINT,
    approved_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_user_google_calendar_connections_user
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_user_google_calendar_connections_approved_by
        FOREIGN KEY (approved_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_google_calendar_connections_user_id
    ON user_google_calendar_connections(user_id);
CREATE INDEX IF NOT EXISTS idx_user_google_calendar_connections_approval_status
    ON user_google_calendar_connections(approval_status);

CREATE TABLE IF NOT EXISTS user_calendar_assignments (
    user_calendar_assignment_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    user_calendar_id BIGINT NOT NULL,
    assigned_by_user_id BIGINT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_user_calendar_assignments_user
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_user_calendar_assignments_calendar
        FOREIGN KEY (user_calendar_id) REFERENCES user_calendars(user_calendar_id) ON DELETE CASCADE,
    CONSTRAINT fk_user_calendar_assignments_assigned_by
        FOREIGN KEY (assigned_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_calendar_assignments_user_calendar_id
    ON user_calendar_assignments(user_calendar_id);
CREATE INDEX IF NOT EXISTS idx_user_calendar_assignments_assigned_by_user_id
    ON user_calendar_assignments(assigned_by_user_id);

CREATE TABLE IF NOT EXISTS google_calendar_oauth_states (
    google_calendar_oauth_state_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    state_token TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    CONSTRAINT fk_google_calendar_oauth_states_user
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_google_calendar_oauth_states_state_token
    ON google_calendar_oauth_states(state_token);
CREATE INDEX IF NOT EXISTS idx_google_calendar_oauth_states_expires_at
    ON google_calendar_oauth_states(expires_at);

CREATE TABLE IF NOT EXISTS user_sessions (
    session_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    device_id TEXT,
    device_label TEXT,
    ip_address TEXT,
    user_agent TEXT,
    created_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    CONSTRAINT fk_user_sessions_user
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_device_id ON user_sessions(device_id);

CREATE TABLE IF NOT EXISTS invoices (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT,
    incoming_date TEXT NOT NULL,
    source TEXT NOT NULL,
    file_name TEXT NOT NULL,
    document_type TEXT,
    invoice_number TEXT,
    ksef_number TEXT,
    issuer_nip TEXT,
    issuer_name TEXT,
    issue_date TEXT,
    sale_date TEXT,
    gross_amount DOUBLE PRECISION,
    currency TEXT NOT NULL DEFAULT 'PLN',
    status TEXT NOT NULL,
    duplicate_type TEXT NOT NULL DEFAULT 'brak',
    flag_reason TEXT,
    contractor_id BIGINT,
    file_link TEXT,
    file_storage_key TEXT,
    ocr_link TEXT,
    ocr_storage_key TEXT,
    storage_backend TEXT,
    source_external_id TEXT,
    source_sender_name TEXT,
    source_sender_id TEXT,
    source_metadata TEXT,
    invoice_hash TEXT NOT NULL UNIQUE,
    ocr_raw_text TEXT,
    ocr_confidence DOUBLE PRECISION,
    assigned_user_id BIGINT,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_invoices_contractor
        FOREIGN KEY (contractor_id) REFERENCES contractors(contractor_id),
    CONSTRAINT fk_invoices_assigned_user
        FOREIGN KEY (assigned_user_id) REFERENCES users(user_id),
    CONSTRAINT fk_invoices_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE INDEX IF NOT EXISTS idx_invoices_ksef_number ON invoices(ksef_number);
CREATE INDEX IF NOT EXISTS idx_invoices_number_nip ON invoices(invoice_number, issuer_nip);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_source ON invoices(source);
CREATE INDEX IF NOT EXISTS idx_invoices_organization_id ON invoices(organization_id);
CREATE INDEX IF NOT EXISTS idx_invoices_assigned_user_id ON invoices(assigned_user_id);

CREATE TABLE IF NOT EXISTS tasks (
    task_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    task_type TEXT NOT NULL,
    visibility_scope TEXT NOT NULL DEFAULT 'prywatne',
    owner_user_id BIGINT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,
    priority TEXT NOT NULL,
    due_at TEXT,
    remind_at TEXT,
    recurrence_pattern TEXT NOT NULL DEFAULT 'brak',
    recurrence_interval INTEGER NOT NULL DEFAULT 1,
    recurrence_weekdays TEXT,
    recurrence_end_at TEXT,
    recurrence_series_id TEXT,
    recurrence_parent_task_id BIGINT,
    reminder_sent_at TEXT,
    reminder_last_attempt_at TEXT,
    reminder_last_error TEXT,
    assigned_user_id BIGINT,
    calendar_id BIGINT,
    calendar_duration_minutes INTEGER NOT NULL DEFAULT 60,
    external_calendar_event_id TEXT,
    external_calendar_event_url TEXT,
    external_calendar_synced_at TEXT,
    external_calendar_sync_error TEXT,
    external_calendar_sync_state TEXT,
    external_calendar_sync_message TEXT,
    external_calendar_last_checked_at TEXT,
    external_calendar_last_check_error TEXT,
    external_calendar_remote_updated_at TEXT,
    external_calendar_remote_etag TEXT,
    external_calendar_last_sync_source TEXT,
    created_by_user_id BIGINT NOT NULL,
    completed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_tasks_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_tasks_owner_user
        FOREIGN KEY (owner_user_id) REFERENCES users(user_id),
    CONSTRAINT fk_tasks_assigned_user
        FOREIGN KEY (assigned_user_id) REFERENCES users(user_id),
    CONSTRAINT fk_tasks_calendar
        FOREIGN KEY (calendar_id) REFERENCES user_calendars(user_calendar_id),
    CONSTRAINT fk_tasks_created_by_user
        FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_tasks_organization_id ON tasks(organization_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_due_at ON tasks(due_at);
CREATE INDEX IF NOT EXISTS idx_tasks_remind_at ON tasks(remind_at);
CREATE INDEX IF NOT EXISTS idx_tasks_reminder_sent_at ON tasks(reminder_sent_at);
CREATE INDEX IF NOT EXISTS idx_tasks_reminder_last_attempt_at ON tasks(reminder_last_attempt_at);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_user_id ON tasks(assigned_user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_owner_user_id ON tasks(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_visibility_scope ON tasks(visibility_scope);
CREATE INDEX IF NOT EXISTS idx_tasks_calendar_id ON tasks(calendar_id);
CREATE INDEX IF NOT EXISTS idx_tasks_external_calendar_event_id ON tasks(external_calendar_event_id);
CREATE INDEX IF NOT EXISTS idx_tasks_recurrence_pattern ON tasks(recurrence_pattern);
CREATE INDEX IF NOT EXISTS idx_tasks_recurrence_series_id ON tasks(recurrence_series_id);

CREATE TABLE IF NOT EXISTS task_visibility_users (
    task_visibility_user_id BIGSERIAL PRIMARY KEY,
    task_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    created_at TEXT NOT NULL,
    CONSTRAINT fk_task_visibility_users_task
        FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    CONSTRAINT fk_task_visibility_users_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_task_visibility_users_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_task_visibility_users_unique ON task_visibility_users(task_id, user_id);
CREATE INDEX IF NOT EXISTS idx_task_visibility_users_task_id ON task_visibility_users(task_id);
CREATE INDEX IF NOT EXISTS idx_task_visibility_users_user_id ON task_visibility_users(user_id);

CREATE TABLE IF NOT EXISTS task_links (
    task_link_id BIGSERIAL PRIMARY KEY,
    task_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id BIGINT NOT NULL,
    created_by_user_id BIGINT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_task_links_unique ON task_links(task_id, entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_task_links_entity ON task_links(organization_id, entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_task_links_task_id ON task_links(task_id);

CREATE TABLE IF NOT EXISTS task_notes (
    task_note_id BIGSERIAL PRIMARY KEY,
    task_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,
    parent_note_id BIGINT,
    note_kind TEXT NOT NULL DEFAULT 'comment',
    note_text TEXT NOT NULL,
    mentioned_user_ids TEXT,
    mentioned_user_names TEXT,
    created_by_user_id BIGINT NOT NULL,
    created_at TEXT NOT NULL,
    CONSTRAINT fk_task_notes_task
        FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    CONSTRAINT fk_task_notes_parent_note
        FOREIGN KEY (parent_note_id) REFERENCES task_notes(task_note_id) ON DELETE CASCADE,
    CONSTRAINT fk_task_notes_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_task_notes_created_by_user
        FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_task_notes_task_id ON task_notes(task_id);
CREATE INDEX IF NOT EXISTS idx_task_notes_parent_note_id ON task_notes(parent_note_id);

CREATE TABLE IF NOT EXISTS task_checklist_items (
    task_checklist_item_id BIGSERIAL PRIMARY KEY,
    task_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,
    item_text TEXT NOT NULL,
    item_order INTEGER NOT NULL DEFAULT 0,
    is_completed INTEGER NOT NULL DEFAULT 0,
    completed_at TEXT,
    completed_by_user_id BIGINT,
    created_by_user_id BIGINT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_task_checklist_items_task
        FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    CONSTRAINT fk_task_checklist_items_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_task_checklist_items_completed_by_user
        FOREIGN KEY (completed_by_user_id) REFERENCES users(user_id),
    CONSTRAINT fk_task_checklist_items_created_by_user
        FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_task_checklist_items_task_id ON task_checklist_items(task_id);
CREATE INDEX IF NOT EXISTS idx_task_checklist_items_task_order ON task_checklist_items(task_id, item_order);

CREATE TABLE IF NOT EXISTS task_templates (
    task_template_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    template_name TEXT NOT NULL,
    template_description TEXT,
    task_type TEXT NOT NULL DEFAULT 'zadanie',
    priority TEXT NOT NULL DEFAULT 'normalny',
    visibility_scope TEXT NOT NULL DEFAULT 'prywatne',
    due_offset_minutes INTEGER,
    reminder_offset_minutes INTEGER,
    recurrence_pattern TEXT NOT NULL DEFAULT 'brak',
    recurrence_interval INTEGER NOT NULL DEFAULT 1,
    recurrence_weekdays TEXT,
    recurrence_end_offset_minutes INTEGER,
    calendar_duration_minutes INTEGER NOT NULL DEFAULT 60,
    checklist_json TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_by_user_id BIGINT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_task_templates_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_task_templates_created_by_user
        FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_task_templates_org_active ON task_templates(organization_id, is_active);
CREATE INDEX IF NOT EXISTS idx_task_templates_org_name ON task_templates(organization_id, template_name);

CREATE TABLE IF NOT EXISTS approval_requests (
    approval_request_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id BIGINT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    requested_by_user_id BIGINT NOT NULL,
    requested_user_id BIGINT,
    approve_status TEXT,
    reject_status TEXT,
    metadata_json TEXT,
    requested_at TEXT NOT NULL,
    decided_by_user_id BIGINT,
    decided_at TEXT,
    decision_reason TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_approval_requests_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_approval_requests_requested_by
        FOREIGN KEY (requested_by_user_id) REFERENCES users(user_id),
    CONSTRAINT fk_approval_requests_requested_user
        FOREIGN KEY (requested_user_id) REFERENCES users(user_id),
    CONSTRAINT fk_approval_requests_decided_by
        FOREIGN KEY (decided_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_approval_requests_org_status
    ON approval_requests(organization_id, status);
CREATE INDEX IF NOT EXISTS idx_approval_requests_entity
    ON approval_requests(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_approval_requests_requested_user
    ON approval_requests(requested_user_id);

CREATE TABLE IF NOT EXISTS invoice_ksef_field_overrides (
    invoice_ksef_field_override_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    invoice_id BIGINT NOT NULL,
    approval_request_id BIGINT,
    field_name TEXT NOT NULL,
    source_value TEXT,
    local_value TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    requested_by_user_id BIGINT,
    approved_by_user_id BIGINT,
    rejected_by_user_id BIGINT,
    request_reason TEXT,
    decision_reason TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    approved_at TEXT,
    rejected_at TEXT,
    CONSTRAINT fk_invoice_ksef_override_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_invoice_ksef_override_invoice
        FOREIGN KEY (invoice_id) REFERENCES invoices(id),
    CONSTRAINT fk_invoice_ksef_override_request
        FOREIGN KEY (approval_request_id) REFERENCES approval_requests(approval_request_id),
    CONSTRAINT fk_invoice_ksef_override_requested_by
        FOREIGN KEY (requested_by_user_id) REFERENCES users(user_id),
    CONSTRAINT fk_invoice_ksef_override_approved_by
        FOREIGN KEY (approved_by_user_id) REFERENCES users(user_id),
    CONSTRAINT fk_invoice_ksef_override_rejected_by
        FOREIGN KEY (rejected_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_invoice_ksef_overrides_invoice_status
    ON invoice_ksef_field_overrides(invoice_id, status);
CREATE INDEX IF NOT EXISTS idx_invoice_ksef_overrides_request
    ON invoice_ksef_field_overrides(approval_request_id);

CREATE TABLE IF NOT EXISTS task_attachments (
    task_attachment_id BIGSERIAL PRIMARY KEY,
    task_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,
    file_name TEXT NOT NULL,
    mime_type TEXT,
    file_size BIGINT NOT NULL DEFAULT 0,
    file_link TEXT NOT NULL,
    file_storage_key TEXT NOT NULL,
    storage_backend TEXT NOT NULL DEFAULT 'lokalny',
    uploaded_by_user_id BIGINT NOT NULL,
    created_at TEXT NOT NULL,
    CONSTRAINT fk_task_attachments_task
        FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    CONSTRAINT fk_task_attachments_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_task_attachments_uploaded_by_user
        FOREIGN KEY (uploaded_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_task_attachments_task_id ON task_attachments(task_id);
CREATE INDEX IF NOT EXISTS idx_task_attachments_org_id ON task_attachments(organization_id);

CREATE TABLE IF NOT EXISTS task_history (
    task_history_id BIGSERIAL PRIMARY KEY,
    task_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,
    action_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    message TEXT NOT NULL,
    details TEXT,
    created_at TEXT NOT NULL,
    CONSTRAINT fk_task_history_task
        FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    CONSTRAINT fk_task_history_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE INDEX IF NOT EXISTS idx_task_history_task_id ON task_history(task_id);

CREATE TABLE IF NOT EXISTS work_items (
    work_item_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'manual',
    source_id BIGINT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'nowe',
    priority_level TEXT NOT NULL DEFAULT 'normalny',
    priority_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    assigned_user_id BIGINT,
    created_by_user_id BIGINT NOT NULL,
    updated_by_user_id BIGINT,
    due_at TEXT,
    sla_deadline_at TEXT,
    sla_warning_minutes INTEGER NOT NULL DEFAULT 120,
    sla_warning_at TEXT,
    sla_stage TEXT NOT NULL DEFAULT 'on_track',
    reminder_sent_at TEXT,
    escalation_sent_at TEXT,
    resolved_at TEXT,
    last_sla_transition_at TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_work_items_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_work_items_assigned_user
        FOREIGN KEY (assigned_user_id) REFERENCES users(user_id),
    CONSTRAINT fk_work_items_created_by_user
        FOREIGN KEY (created_by_user_id) REFERENCES users(user_id),
    CONSTRAINT fk_work_items_updated_by_user
        FOREIGN KEY (updated_by_user_id) REFERENCES users(user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_work_items_org_source
    ON work_items(organization_id, source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_work_items_org_status
    ON work_items(organization_id, status);
CREATE INDEX IF NOT EXISTS idx_work_items_org_priority_score
    ON work_items(organization_id, priority_score);
CREATE INDEX IF NOT EXISTS idx_work_items_org_sla_deadline
    ON work_items(organization_id, sla_deadline_at);
CREATE INDEX IF NOT EXISTS idx_work_items_org_sla_stage
    ON work_items(organization_id, sla_stage);
CREATE INDEX IF NOT EXISTS idx_work_items_assigned_user_id
    ON work_items(assigned_user_id);

CREATE TABLE IF NOT EXISTS work_item_history (
    work_item_history_id BIGSERIAL PRIMARY KEY,
    work_item_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,
    action_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    message TEXT NOT NULL,
    details TEXT,
    created_at TEXT NOT NULL,
    CONSTRAINT fk_work_item_history_item
        FOREIGN KEY (work_item_id) REFERENCES work_items(work_item_id) ON DELETE CASCADE,
    CONSTRAINT fk_work_item_history_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE INDEX IF NOT EXISTS idx_work_item_history_item_id
    ON work_item_history(work_item_id);
CREATE INDEX IF NOT EXISTS idx_work_item_history_org_id
    ON work_item_history(organization_id);

CREATE TABLE IF NOT EXISTS task_reminder_outbox (
    task_reminder_outbox_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    task_id BIGINT NOT NULL,
    delivery_channel TEXT NOT NULL,
    delivery_key TEXT NOT NULL,
    delivery_anchor_at TEXT NOT NULL,
    recipient_user_id BIGINT NOT NULL,
    recipient_telegram_user_id TEXT NOT NULL,
    available_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    retryable INTEGER NOT NULL DEFAULT 1,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    claimed_at TEXT,
    claimed_by TEXT,
    last_attempt_at TEXT,
    last_error TEXT,
    sent_at TEXT,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_task_reminder_outbox_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_task_reminder_outbox_task
        FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    CONSTRAINT fk_task_reminder_outbox_recipient
        FOREIGN KEY (recipient_user_id) REFERENCES users(user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_task_reminder_outbox_unique
    ON task_reminder_outbox(task_id, delivery_channel, delivery_key);
CREATE INDEX IF NOT EXISTS idx_task_reminder_outbox_status_available
    ON task_reminder_outbox(status, available_at);
CREATE INDEX IF NOT EXISTS idx_task_reminder_outbox_org_status
    ON task_reminder_outbox(organization_id, status);
CREATE INDEX IF NOT EXISTS idx_task_reminder_outbox_task_id
    ON task_reminder_outbox(task_id);

CREATE TABLE IF NOT EXISTS task_reminder_outbox_attempts (
    task_reminder_outbox_attempt_id BIGSERIAL PRIMARY KEY,
    task_reminder_outbox_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,
    task_id BIGINT NOT NULL,
    delivery_channel TEXT NOT NULL,
    attempt_no INTEGER NOT NULL,
    outcome TEXT NOT NULL,
    attempted_at TEXT NOT NULL,
    worker_name TEXT NOT NULL,
    error_message TEXT,
    details TEXT,
    created_at TEXT NOT NULL,
    CONSTRAINT fk_task_reminder_outbox_attempts_outbox
        FOREIGN KEY (task_reminder_outbox_id) REFERENCES task_reminder_outbox(task_reminder_outbox_id) ON DELETE CASCADE,
    CONSTRAINT fk_task_reminder_outbox_attempts_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_task_reminder_outbox_attempts_task
        FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_task_reminder_outbox_attempts_outbox_id
    ON task_reminder_outbox_attempts(task_reminder_outbox_id);
CREATE INDEX IF NOT EXISTS idx_task_reminder_outbox_attempts_task_id
    ON task_reminder_outbox_attempts(task_id);
CREATE INDEX IF NOT EXISTS idx_task_reminder_outbox_attempts_org_id
    ON task_reminder_outbox_attempts(organization_id);

CREATE TABLE IF NOT EXISTS task_reminder_worker_heartbeats (
    task_reminder_worker_heartbeat_id BIGSERIAL PRIMARY KEY,
    worker_name TEXT NOT NULL UNIQUE,
    worker_role TEXT NOT NULL,
    process_id BIGINT,
    state TEXT NOT NULL DEFAULT 'idle',
    last_heartbeat_at TEXT NOT NULL,
    last_success_at TEXT,
    last_error_at TEXT,
    last_error_message TEXT,
    cycles_completed INTEGER NOT NULL DEFAULT 0,
    processed_total INTEGER NOT NULL DEFAULT 0,
    sent_total INTEGER NOT NULL DEFAULT 0,
    failed_total INTEGER NOT NULL DEFAULT 0,
    deferred_total INTEGER NOT NULL DEFAULT 0,
    retrying_total INTEGER NOT NULL DEFAULT 0,
    skipped_total INTEGER NOT NULL DEFAULT 0,
    queue_total INTEGER NOT NULL DEFAULT 0,
    queue_due INTEGER NOT NULL DEFAULT 0,
    queue_failed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_task_reminder_worker_heartbeats_role
    ON task_reminder_worker_heartbeats(worker_role);
CREATE INDEX IF NOT EXISTS idx_task_reminder_worker_heartbeats_state
    ON task_reminder_worker_heartbeats(state);
CREATE INDEX IF NOT EXISTS idx_task_reminder_worker_heartbeats_heartbeat_at
    ON task_reminder_worker_heartbeats(last_heartbeat_at);

CREATE TABLE IF NOT EXISTS billing_schools (
    billing_school_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    full_name TEXT NOT NULL,
    short_name TEXT NOT NULL,
    city TEXT,
    notes TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_billing_schools_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_schools_org_full_name
    ON billing_schools(organization_id, full_name);
CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_schools_org_short_name
    ON billing_schools(organization_id, short_name);
CREATE INDEX IF NOT EXISTS idx_billing_schools_org
    ON billing_schools(organization_id);

CREATE TABLE IF NOT EXISTS billing_models (
    billing_model_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    name TEXT NOT NULL,
    profile_type TEXT NOT NULL DEFAULT 'education_student',
    school_year TEXT NOT NULL,
    lesson_day TEXT,
    settlement_mode TEXT NOT NULL,
    monthly_rate_amount DOUBLE PRECISION,
    semester_rate_amount DOUBLE PRECISION,
    sibling_discount_amount DOUBLE PRECISION NOT NULL DEFAULT 100,
    large_family_discount_amount DOUBLE PRECISION NOT NULL DEFAULT 50,
    intro_free_lessons_count INTEGER NOT NULL DEFAULT 1,
    contract_required INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_billing_models_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_models_org_name
    ON billing_models(organization_id, name);
CREATE INDEX IF NOT EXISTS idx_billing_models_org
    ON billing_models(organization_id);

CREATE TABLE IF NOT EXISTS billing_payers (
    billing_payer_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    display_name TEXT,
    contact_phone TEXT NOT NULL,
    payment_identifier TEXT NOT NULL,
    has_large_family_card INTEGER NOT NULL DEFAULT 0,
    email TEXT,
    notes TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_billing_payers_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_payers_org_payment_identifier
    ON billing_payers(organization_id, payment_identifier);
CREATE INDEX IF NOT EXISTS idx_billing_payers_org
    ON billing_payers(organization_id);

CREATE TABLE IF NOT EXISTS billing_students (
    billing_student_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    billing_payer_id BIGINT NOT NULL,
    billing_school_id BIGINT,
    billing_model_id BIGINT,
    full_name TEXT NOT NULL,
    lesson_day TEXT,
    family_billing_order INTEGER NOT NULL DEFAULT 1,
    group_name TEXT,
    notes TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_billing_students_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_billing_students_payer
        FOREIGN KEY (billing_payer_id) REFERENCES billing_payers(billing_payer_id),
    CONSTRAINT fk_billing_students_school
        FOREIGN KEY (billing_school_id) REFERENCES billing_schools(billing_school_id),
    CONSTRAINT fk_billing_students_model
        FOREIGN KEY (billing_model_id) REFERENCES billing_models(billing_model_id)
);

CREATE INDEX IF NOT EXISTS idx_billing_students_org
    ON billing_students(organization_id);
CREATE INDEX IF NOT EXISTS idx_billing_students_payer
    ON billing_students(billing_payer_id);
CREATE INDEX IF NOT EXISTS idx_billing_students_school
    ON billing_students(billing_school_id);
CREATE INDEX IF NOT EXISTS idx_billing_students_model
    ON billing_students(billing_model_id);

CREATE TABLE IF NOT EXISTS billing_charge_batches (
    billing_charge_batch_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    billing_model_id BIGINT NOT NULL,
    school_year TEXT NOT NULL,
    period_type TEXT NOT NULL,
    period_label TEXT NOT NULL,
    due_date TEXT NOT NULL,
    lesson_count INTEGER NOT NULL DEFAULT 0,
    generated_by_user_id BIGINT,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_billing_charge_batches_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_billing_charge_batches_model
        FOREIGN KEY (billing_model_id) REFERENCES billing_models(billing_model_id),
    CONSTRAINT fk_billing_charge_batches_generated_by_user
        FOREIGN KEY (generated_by_user_id) REFERENCES users(user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_charge_batches_org_model_period
    ON billing_charge_batches(organization_id, billing_model_id, period_label);
CREATE INDEX IF NOT EXISTS idx_billing_charge_batches_org
    ON billing_charge_batches(organization_id);
CREATE INDEX IF NOT EXISTS idx_billing_charge_batches_model
    ON billing_charge_batches(billing_model_id);

CREATE TABLE IF NOT EXISTS billing_charges (
    billing_charge_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    billing_charge_batch_id BIGINT NOT NULL,
    billing_model_id BIGINT NOT NULL,
    billing_student_id BIGINT NOT NULL,
    billing_payer_id BIGINT NOT NULL,
    school_year TEXT NOT NULL,
    period_label TEXT NOT NULL,
    due_date TEXT NOT NULL,
    lesson_count INTEGER NOT NULL DEFAULT 0,
    unit_rate_amount DOUBLE PRECISION NOT NULL,
    base_amount DOUBLE PRECISION NOT NULL,
    intro_free_discount_amount DOUBLE PRECISION NOT NULL DEFAULT 0,
    sibling_discount_amount DOUBLE PRECISION NOT NULL DEFAULT 0,
    large_family_discount_amount DOUBLE PRECISION NOT NULL DEFAULT 0,
    total_amount DOUBLE PRECISION NOT NULL,
    status TEXT NOT NULL DEFAULT 'otwarta',
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_billing_charges_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_billing_charges_batch
        FOREIGN KEY (billing_charge_batch_id) REFERENCES billing_charge_batches(billing_charge_batch_id),
    CONSTRAINT fk_billing_charges_model
        FOREIGN KEY (billing_model_id) REFERENCES billing_models(billing_model_id),
    CONSTRAINT fk_billing_charges_student
        FOREIGN KEY (billing_student_id) REFERENCES billing_students(billing_student_id),
    CONSTRAINT fk_billing_charges_payer
        FOREIGN KEY (billing_payer_id) REFERENCES billing_payers(billing_payer_id)
);

CREATE INDEX IF NOT EXISTS idx_billing_charges_org
    ON billing_charges(organization_id);
CREATE INDEX IF NOT EXISTS idx_billing_charges_batch
    ON billing_charges(billing_charge_batch_id);
CREATE INDEX IF NOT EXISTS idx_billing_charges_model
    ON billing_charges(billing_model_id);
CREATE INDEX IF NOT EXISTS idx_billing_charges_student
    ON billing_charges(billing_student_id);
CREATE INDEX IF NOT EXISTS idx_billing_charges_payer
    ON billing_charges(billing_payer_id);

CREATE TABLE IF NOT EXISTS billing_student_charge_state (
    billing_student_charge_state_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    billing_student_id BIGINT NOT NULL,
    school_year TEXT NOT NULL,
    intro_free_lessons_remaining INTEGER NOT NULL DEFAULT 0,
    sibling_discount_remaining_amount DOUBLE PRECISION NOT NULL DEFAULT 0,
    sibling_discount_initialized INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_billing_student_charge_state_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_billing_student_charge_state_student
        FOREIGN KEY (billing_student_id) REFERENCES billing_students(billing_student_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_student_charge_state_org_student_year
    ON billing_student_charge_state(organization_id, billing_student_id, school_year);

CREATE TABLE IF NOT EXISTS billing_payer_charge_state (
    billing_payer_charge_state_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    billing_payer_id BIGINT NOT NULL,
    school_year TEXT NOT NULL,
    large_family_discount_remaining_amount DOUBLE PRECISION NOT NULL DEFAULT 0,
    large_family_discount_initialized INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_billing_payer_charge_state_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_billing_payer_charge_state_payer
        FOREIGN KEY (billing_payer_id) REFERENCES billing_payers(billing_payer_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_payer_charge_state_org_payer_year
    ON billing_payer_charge_state(organization_id, billing_payer_id, school_year);

CREATE TABLE IF NOT EXISTS billing_bank_accounts (
    billing_bank_account_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    account_name TEXT NOT NULL,
    bank_name TEXT,
    iban TEXT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'PLN',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_billing_bank_accounts_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_bank_accounts_org_iban
    ON billing_bank_accounts(organization_id, iban);
CREATE INDEX IF NOT EXISTS idx_billing_bank_accounts_org
    ON billing_bank_accounts(organization_id);

CREATE TABLE IF NOT EXISTS billing_statement_imports (
    billing_statement_import_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    billing_bank_account_id BIGINT NOT NULL,
    source_type TEXT NOT NULL,
    source_file_name TEXT,
    imported_by_user_id BIGINT,
    imported_at TEXT NOT NULL,
    row_count INTEGER NOT NULL DEFAULT 0,
    imported_transaction_count INTEGER NOT NULL DEFAULT 0,
    skipped_transaction_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_billing_statement_imports_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_billing_statement_imports_account
        FOREIGN KEY (billing_bank_account_id) REFERENCES billing_bank_accounts(billing_bank_account_id),
    CONSTRAINT fk_billing_statement_imports_user
        FOREIGN KEY (imported_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_billing_statement_imports_org
    ON billing_statement_imports(organization_id);
CREATE INDEX IF NOT EXISTS idx_billing_statement_imports_account
    ON billing_statement_imports(billing_bank_account_id);

CREATE TABLE IF NOT EXISTS billing_transactions (
    billing_transaction_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    billing_bank_account_id BIGINT NOT NULL,
    billing_statement_import_id BIGINT,
    booking_date TEXT NOT NULL,
    value_date TEXT,
    amount DOUBLE PRECISION NOT NULL,
    currency TEXT NOT NULL DEFAULT 'PLN',
    direction TEXT NOT NULL,
    counterparty_name TEXT,
    counterparty_account TEXT,
    title TEXT,
    reference TEXT,
    raw_data TEXT,
    transaction_hash TEXT NOT NULL,
    matched_status TEXT NOT NULL DEFAULT 'nieprzypisana',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_billing_transactions_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_billing_transactions_account
        FOREIGN KEY (billing_bank_account_id) REFERENCES billing_bank_accounts(billing_bank_account_id),
    CONSTRAINT fk_billing_transactions_import
        FOREIGN KEY (billing_statement_import_id) REFERENCES billing_statement_imports(billing_statement_import_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_transactions_unique
    ON billing_transactions(organization_id, billing_bank_account_id, transaction_hash);
CREATE INDEX IF NOT EXISTS idx_billing_transactions_org
    ON billing_transactions(organization_id);
CREATE INDEX IF NOT EXISTS idx_billing_transactions_account
    ON billing_transactions(billing_bank_account_id);
CREATE INDEX IF NOT EXISTS idx_billing_transactions_booking_date
    ON billing_transactions(booking_date DESC);

CREATE TABLE IF NOT EXISTS billing_payment_matches (
    billing_payment_match_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    billing_transaction_id BIGINT NOT NULL,
    billing_payer_id BIGINT NOT NULL,
    billing_charge_id BIGINT,
    matched_amount DOUBLE PRECISION NOT NULL,
    match_status TEXT NOT NULL DEFAULT 'dopasowana',
    match_reason TEXT,
    matched_by_user_id BIGINT,
    matched_at TEXT NOT NULL,
    CONSTRAINT fk_billing_payment_matches_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_billing_payment_matches_transaction
        FOREIGN KEY (billing_transaction_id) REFERENCES billing_transactions(billing_transaction_id) ON DELETE CASCADE,
    CONSTRAINT fk_billing_payment_matches_payer
        FOREIGN KEY (billing_payer_id) REFERENCES billing_payers(billing_payer_id),
    CONSTRAINT fk_billing_payment_matches_charge
        FOREIGN KEY (billing_charge_id) REFERENCES billing_charges(billing_charge_id),
    CONSTRAINT fk_billing_payment_matches_user
        FOREIGN KEY (matched_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_billing_payment_matches_org
    ON billing_payment_matches(organization_id);
CREATE INDEX IF NOT EXISTS idx_billing_payment_matches_transaction
    ON billing_payment_matches(billing_transaction_id);
CREATE INDEX IF NOT EXISTS idx_billing_payment_matches_payer
    ON billing_payment_matches(billing_payer_id);

CREATE TABLE IF NOT EXISTS billing_payer_ledger_entries (
    billing_payer_ledger_entry_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    billing_payer_id BIGINT NOT NULL,
    billing_charge_id BIGINT,
    billing_transaction_id BIGINT,
    entry_kind TEXT NOT NULL,
    amount_delta DOUBLE PRECISION NOT NULL,
    balance_after DOUBLE PRECISION NOT NULL,
    note TEXT,
    created_by_user_id BIGINT,
    created_at TEXT NOT NULL,
    CONSTRAINT fk_billing_payer_ledger_entries_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_billing_payer_ledger_entries_payer
        FOREIGN KEY (billing_payer_id) REFERENCES billing_payers(billing_payer_id),
    CONSTRAINT fk_billing_payer_ledger_entries_charge
        FOREIGN KEY (billing_charge_id) REFERENCES billing_charges(billing_charge_id),
    CONSTRAINT fk_billing_payer_ledger_entries_transaction
        FOREIGN KEY (billing_transaction_id) REFERENCES billing_transactions(billing_transaction_id),
    CONSTRAINT fk_billing_payer_ledger_entries_user
        FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_billing_payer_ledger_entries_org
    ON billing_payer_ledger_entries(organization_id);
CREATE INDEX IF NOT EXISTS idx_billing_payer_ledger_entries_payer
    ON billing_payer_ledger_entries(billing_payer_id);
CREATE INDEX IF NOT EXISTS idx_billing_payer_ledger_entries_created_at
    ON billing_payer_ledger_entries(created_at DESC);

CREATE TABLE IF NOT EXISTS billing_notes (
    billing_note_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    billing_payer_id BIGINT NOT NULL,
    author_user_id BIGINT NOT NULL,
    note_type TEXT NOT NULL DEFAULT 'operator_note',
    note_text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    CONSTRAINT fk_billing_notes_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_billing_notes_payer
        FOREIGN KEY (billing_payer_id) REFERENCES billing_payers(billing_payer_id) ON DELETE CASCADE,
    CONSTRAINT fk_billing_notes_author
        FOREIGN KEY (author_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_billing_notes_payer
    ON billing_notes(billing_payer_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_billing_notes_org
    ON billing_notes(organization_id);

CREATE TABLE IF NOT EXISTS billing_payment_review_events (
    billing_payment_review_event_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    billing_transaction_id BIGINT NOT NULL,
    status TEXT NOT NULL,
    note_text TEXT,
    created_by_user_id BIGINT NOT NULL,
    created_at TEXT NOT NULL,
    CONSTRAINT fk_billing_payment_review_events_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_billing_payment_review_events_transaction
        FOREIGN KEY (billing_transaction_id) REFERENCES billing_transactions(billing_transaction_id) ON DELETE CASCADE,
    CONSTRAINT fk_billing_payment_review_events_user
        FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_billing_payment_review_events_transaction
    ON billing_payment_review_events(billing_transaction_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_billing_payment_review_events_org
    ON billing_payment_review_events(organization_id);

CREATE TABLE IF NOT EXISTS billing_work_queue_events (
    billing_work_queue_event_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    issue_key TEXT NOT NULL,
    issue_type TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id BIGINT,
    action TEXT NOT NULL,
    note_text TEXT,
    created_by_user_id BIGINT NOT NULL,
    created_at TEXT NOT NULL,
    CONSTRAINT fk_billing_work_queue_events_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_billing_work_queue_events_user
        FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_billing_work_queue_events_org
    ON billing_work_queue_events(organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_billing_work_queue_events_issue
    ON billing_work_queue_events(organization_id, issue_key, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_billing_work_queue_events_target
    ON billing_work_queue_events(organization_id, target_type, target_id);

CREATE TABLE IF NOT EXISTS invoice_relations (
    id BIGSERIAL PRIMARY KEY,
    invoice_id BIGINT NOT NULL,
    related_invoice_id BIGINT NOT NULL,
    relation_type TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL,
    CONSTRAINT fk_relations_invoice
        FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
    CONSTRAINT fk_relations_related_invoice
        FOREIGN KEY (related_invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_invoice_relations_invoice_id ON invoice_relations(invoice_id);

CREATE TABLE IF NOT EXISTS event_logs (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT,
    event_time TEXT NOT NULL,
    event_type TEXT NOT NULL,
    invoice_id BIGINT,
    source TEXT,
    status_before TEXT,
    status_after TEXT,
    decision_reason TEXT,
    actor TEXT NOT NULL,
    details TEXT,
    CONSTRAINT fk_event_logs_invoice
        FOREIGN KEY (invoice_id) REFERENCES invoices(id),
    CONSTRAINT fk_event_logs_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE INDEX IF NOT EXISTS idx_event_logs_invoice_id ON event_logs(invoice_id);
CREATE INDEX IF NOT EXISTS idx_event_logs_event_time ON event_logs(event_time DESC);
CREATE INDEX IF NOT EXISTS idx_event_logs_organization_id ON event_logs(organization_id);

CREATE TABLE IF NOT EXISTS intake_forms (
    intake_form_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    form_name TEXT NOT NULL,
    form_slug TEXT NOT NULL,
    description TEXT,
    field_schema_json TEXT NOT NULL DEFAULT '[]',
    is_public INTEGER NOT NULL DEFAULT 1,
    allow_attachments INTEGER NOT NULL DEFAULT 1,
    default_priority TEXT NOT NULL DEFAULT 'normalny',
    default_assigned_user_id BIGINT,
    public_token TEXT NOT NULL,
    created_by_user_id BIGINT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_intake_forms_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_intake_forms_default_assignee
        FOREIGN KEY (default_assigned_user_id) REFERENCES users(user_id),
    CONSTRAINT fk_intake_forms_creator
        FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_intake_forms_org_slug
    ON intake_forms(organization_id, form_slug);
CREATE UNIQUE INDEX IF NOT EXISTS idx_intake_forms_public_token
    ON intake_forms(public_token);
CREATE INDEX IF NOT EXISTS idx_intake_forms_org_active
    ON intake_forms(organization_id, is_public);

CREATE TABLE IF NOT EXISTS intake_items (
    intake_item_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    intake_form_id BIGINT,
    source_kind TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'nowe',
    priority TEXT NOT NULL DEFAULT 'normalny',
    title TEXT NOT NULL,
    description TEXT,
    requester_name TEXT,
    requester_email TEXT,
    source_reference TEXT,
    due_at TEXT,
    metadata_json TEXT,
    assigned_user_id BIGINT,
    linked_task_id BIGINT,
    linked_invoice_id BIGINT,
    created_by_user_id BIGINT,
    last_activity_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_intake_items_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_intake_items_form
        FOREIGN KEY (intake_form_id) REFERENCES intake_forms(intake_form_id),
    CONSTRAINT fk_intake_items_assignee
        FOREIGN KEY (assigned_user_id) REFERENCES users(user_id),
    CONSTRAINT fk_intake_items_task
        FOREIGN KEY (linked_task_id) REFERENCES tasks(task_id),
    CONSTRAINT fk_intake_items_invoice
        FOREIGN KEY (linked_invoice_id) REFERENCES invoices(id),
    CONSTRAINT fk_intake_items_creator
        FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_intake_items_org_status
    ON intake_items(organization_id, status);
CREATE INDEX IF NOT EXISTS idx_intake_items_org_source
    ON intake_items(organization_id, source_kind);
CREATE INDEX IF NOT EXISTS idx_intake_items_form_id
    ON intake_items(intake_form_id);
CREATE INDEX IF NOT EXISTS idx_intake_items_updated_at
    ON intake_items(updated_at DESC);

CREATE TABLE IF NOT EXISTS intake_item_comments (
    intake_item_comment_id BIGSERIAL PRIMARY KEY,
    intake_item_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,
    parent_comment_id BIGINT,
    note_text TEXT NOT NULL,
    mentioned_user_ids TEXT,
    mentioned_user_names TEXT,
    created_by_user_id BIGINT,
    created_at TEXT NOT NULL,
    CONSTRAINT fk_intake_item_comments_item
        FOREIGN KEY (intake_item_id) REFERENCES intake_items(intake_item_id) ON DELETE CASCADE,
    CONSTRAINT fk_intake_item_comments_parent
        FOREIGN KEY (parent_comment_id) REFERENCES intake_item_comments(intake_item_comment_id) ON DELETE CASCADE,
    CONSTRAINT fk_intake_item_comments_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_intake_item_comments_creator
        FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_intake_item_comments_item_id
    ON intake_item_comments(intake_item_id);
CREATE INDEX IF NOT EXISTS idx_intake_item_comments_parent_id
    ON intake_item_comments(parent_comment_id);

CREATE TABLE IF NOT EXISTS intake_item_history (
    intake_item_history_id BIGSERIAL PRIMARY KEY,
    intake_item_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,
    action_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    message TEXT NOT NULL,
    details TEXT,
    created_at TEXT NOT NULL,
    CONSTRAINT fk_intake_item_history_item
        FOREIGN KEY (intake_item_id) REFERENCES intake_items(intake_item_id) ON DELETE CASCADE,
    CONSTRAINT fk_intake_item_history_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE INDEX IF NOT EXISTS idx_intake_item_history_item_id
    ON intake_item_history(intake_item_id);
CREATE INDEX IF NOT EXISTS idx_intake_item_history_created_at
    ON intake_item_history(created_at DESC);

CREATE TABLE IF NOT EXISTS entity_attachments (
    entity_attachment_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id BIGINT NOT NULL,
    file_name TEXT NOT NULL,
    mime_type TEXT,
    file_size INTEGER NOT NULL DEFAULT 0,
    file_link TEXT NOT NULL,
    file_storage_key TEXT NOT NULL,
    storage_backend TEXT NOT NULL DEFAULT 'lokalny',
    uploaded_by_user_id BIGINT,
    created_at TEXT NOT NULL,
    CONSTRAINT fk_entity_attachments_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_entity_attachments_user
        FOREIGN KEY (uploaded_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_entity_attachments_entity
    ON entity_attachments(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_attachments_org
    ON entity_attachments(organization_id);

CREATE TABLE IF NOT EXISTS saved_views (
    saved_view_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    module_key TEXT NOT NULL,
    view_slug TEXT NOT NULL,
    view_name TEXT NOT NULL,
    description TEXT,
    view_state_json TEXT NOT NULL DEFAULT '{}',
    is_shared INTEGER NOT NULL DEFAULT 0,
    is_default INTEGER NOT NULL DEFAULT 0,
    created_by_user_id BIGINT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_saved_views_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_saved_views_creator
        FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_saved_views_org_module_slug
    ON saved_views(organization_id, module_key, view_slug);
CREATE INDEX IF NOT EXISTS idx_saved_views_org_module
    ON saved_views(organization_id, module_key);

CREATE TABLE IF NOT EXISTS automation_rules (
    automation_rule_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    rule_slug TEXT NOT NULL,
    rule_name TEXT NOT NULL,
    description TEXT,
    trigger_event_type TEXT NOT NULL,
    conditions_json TEXT NOT NULL DEFAULT '{}',
    actions_json TEXT NOT NULL DEFAULT '[]',
    is_active INTEGER NOT NULL DEFAULT 1,
    last_processed_event_log_id BIGINT NOT NULL DEFAULT 0,
    last_run_at TEXT,
    last_result TEXT,
    execution_count INTEGER NOT NULL DEFAULT 0,
    created_by_user_id BIGINT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_automation_rules_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_automation_rules_creator
        FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_automation_rules_org_slug
    ON automation_rules(organization_id, rule_slug);
CREATE INDEX IF NOT EXISTS idx_automation_rules_org_trigger
    ON automation_rules(organization_id, trigger_event_type, is_active);

CREATE TABLE IF NOT EXISTS automation_executions (
    automation_execution_id BIGSERIAL PRIMARY KEY,
    automation_rule_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,
    event_log_id BIGINT,
    trigger_event_type TEXT NOT NULL,
    execution_status TEXT NOT NULL,
    input_json TEXT,
    result_json TEXT,
    error_message TEXT,
    executed_at TEXT NOT NULL,
    CONSTRAINT fk_automation_executions_rule
        FOREIGN KEY (automation_rule_id) REFERENCES automation_rules(automation_rule_id) ON DELETE CASCADE,
    CONSTRAINT fk_automation_executions_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

CREATE INDEX IF NOT EXISTS idx_automation_executions_rule_id
    ON automation_executions(automation_rule_id);
CREATE INDEX IF NOT EXISTS idx_automation_executions_org
    ON automation_executions(organization_id);
CREATE INDEX IF NOT EXISTS idx_automation_executions_event_log_id
    ON automation_executions(event_log_id);

CREATE TABLE IF NOT EXISTS knowledge_documents (
    knowledge_document_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    title TEXT NOT NULL,
    file_name TEXT NOT NULL,
    mime_type TEXT,
    file_link TEXT NOT NULL,
    file_storage_key TEXT NOT NULL,
    content_text TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    char_count INTEGER NOT NULL DEFAULT 0,
    source_type TEXT NOT NULL DEFAULT 'manual',
    library_path TEXT NOT NULL DEFAULT '',
    is_downloadable INTEGER NOT NULL DEFAULT 1,
    use_in_assistant INTEGER NOT NULL DEFAULT 1,
    business_status TEXT NOT NULL DEFAULT 'roboczy',
    business_status_before_archive TEXT,
    owner_user_id BIGINT,
    reviewer_user_id BIGINT,
    approver_user_id BIGINT,
    created_by_user_id BIGINT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_knowledge_documents_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    CONSTRAINT fk_knowledge_documents_created_by_user
        FOREIGN KEY (created_by_user_id) REFERENCES users(user_id),
    CONSTRAINT fk_knowledge_documents_owner_user
        FOREIGN KEY (owner_user_id) REFERENCES users(user_id),
    CONSTRAINT fk_knowledge_documents_reviewer_user
        FOREIGN KEY (reviewer_user_id) REFERENCES users(user_id),
    CONSTRAINT fk_knowledge_documents_approver_user
        FOREIGN KEY (approver_user_id) REFERENCES users(user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_knowledge_documents_org_storage_key
    ON knowledge_documents(organization_id, file_storage_key);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_organization_id
    ON knowledge_documents(organization_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_updated_at
    ON knowledge_documents(updated_at DESC);
"""

SQLITE_RESET_SCRIPT = """
PRAGMA foreign_keys = OFF;
  DROP TABLE IF EXISTS system_email_oauth_states;
  DROP TABLE IF EXISTS system_email_google_connections;
  DROP TABLE IF EXISTS user_module_inbox_state;
  DROP TABLE IF EXISTS billing_payer_charge_state;
DROP TABLE IF EXISTS billing_payer_ledger_entries;
DROP TABLE IF EXISTS billing_work_queue_events;
DROP TABLE IF EXISTS billing_payment_review_events;
  DROP TABLE IF EXISTS billing_payment_matches;
DROP TABLE IF EXISTS billing_notes;
DROP TABLE IF EXISTS billing_student_charge_state;
DROP TABLE IF EXISTS billing_charges;
DROP TABLE IF EXISTS billing_charge_batches;
DROP TABLE IF EXISTS billing_students;
DROP TABLE IF EXISTS billing_payers;
DROP TABLE IF EXISTS billing_models;
DROP TABLE IF EXISTS billing_schools;
DROP TABLE IF EXISTS billing_transactions;
  DROP TABLE IF EXISTS billing_statement_imports;
  DROP TABLE IF EXISTS billing_bank_accounts;
  DROP TABLE IF EXISTS contractor_notes;
  DROP TABLE IF EXISTS invoice_comments;
  DROP TABLE IF EXISTS knowledge_document_comments;
  DROP TABLE IF EXISTS invoice_relations;
DROP TABLE IF EXISTS email_import_items;
DROP TABLE IF EXISTS email_import_runs;
DROP TABLE IF EXISTS ksef_import_items;
DROP TABLE IF EXISTS ksef_import_runs;
DROP TABLE IF EXISTS work_item_history;
DROP TABLE IF EXISTS work_items;
DROP TABLE IF EXISTS task_history;
DROP TABLE IF EXISTS task_reminder_outbox_attempts;
DROP TABLE IF EXISTS task_reminder_outbox;
DROP TABLE IF EXISTS task_reminder_worker_heartbeats;
DROP TABLE IF EXISTS approval_requests;
DROP TABLE IF EXISTS task_templates;
DROP TABLE IF EXISTS task_checklist_items;
DROP TABLE IF EXISTS task_attachments;
DROP TABLE IF EXISTS task_notes;
DROP TABLE IF EXISTS task_visibility_users;
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS user_calendars;
DROP TABLE IF EXISTS knowledge_processing_jobs;
DROP TABLE IF EXISTS knowledge_document_versions;
DROP TABLE IF EXISTS knowledge_folder_watchers;
DROP TABLE IF EXISTS organization_memberships;
DROP TABLE IF EXISTS organization_whiteboard_events;
DROP TABLE IF EXISTS organization_modules;
DROP TABLE IF EXISTS user_capabilities;
DROP TABLE IF EXISTS knowledge_documents;
DROP TABLE IF EXISTS event_logs;
DROP TABLE IF EXISTS user_sessions;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS contractors;
DROP TABLE IF EXISTS organizations;
PRAGMA foreign_keys = ON;
"""

POSTGRES_RESET_SCRIPT = """
  DROP TABLE IF EXISTS system_email_oauth_states CASCADE;
  DROP TABLE IF EXISTS system_email_google_connections CASCADE;
  DROP TABLE IF EXISTS user_module_inbox_state CASCADE;
  DROP TABLE IF EXISTS billing_payer_charge_state CASCADE;
DROP TABLE IF EXISTS billing_payer_ledger_entries CASCADE;
DROP TABLE IF EXISTS billing_work_queue_events CASCADE;
DROP TABLE IF EXISTS billing_payment_review_events CASCADE;
  DROP TABLE IF EXISTS billing_payment_matches CASCADE;
DROP TABLE IF EXISTS billing_notes CASCADE;
DROP TABLE IF EXISTS billing_student_charge_state CASCADE;
DROP TABLE IF EXISTS billing_charges CASCADE;
DROP TABLE IF EXISTS billing_charge_batches CASCADE;
DROP TABLE IF EXISTS billing_students CASCADE;
DROP TABLE IF EXISTS billing_payers CASCADE;
DROP TABLE IF EXISTS billing_models CASCADE;
DROP TABLE IF EXISTS billing_schools CASCADE;
DROP TABLE IF EXISTS billing_transactions CASCADE;
  DROP TABLE IF EXISTS billing_statement_imports CASCADE;
  DROP TABLE IF EXISTS billing_bank_accounts CASCADE;
  DROP TABLE IF EXISTS contractor_notes CASCADE;
  DROP TABLE IF EXISTS invoice_comments CASCADE;
  DROP TABLE IF EXISTS knowledge_document_comments CASCADE;
  DROP TABLE IF EXISTS invoice_relations CASCADE;
DROP TABLE IF EXISTS email_import_items CASCADE;
DROP TABLE IF EXISTS email_import_runs CASCADE;
DROP TABLE IF EXISTS ksef_import_items CASCADE;
DROP TABLE IF EXISTS ksef_import_runs CASCADE;
DROP TABLE IF EXISTS work_item_history CASCADE;
DROP TABLE IF EXISTS work_items CASCADE;
DROP TABLE IF EXISTS task_history CASCADE;
DROP TABLE IF EXISTS task_reminder_outbox_attempts CASCADE;
DROP TABLE IF EXISTS task_reminder_outbox CASCADE;
DROP TABLE IF EXISTS task_reminder_worker_heartbeats CASCADE;
DROP TABLE IF EXISTS approval_requests CASCADE;
DROP TABLE IF EXISTS task_templates CASCADE;
DROP TABLE IF EXISTS task_checklist_items CASCADE;
DROP TABLE IF EXISTS task_attachments CASCADE;
DROP TABLE IF EXISTS task_notes CASCADE;
DROP TABLE IF EXISTS task_visibility_users CASCADE;
DROP TABLE IF EXISTS tasks CASCADE;
DROP TABLE IF EXISTS user_calendars CASCADE;
DROP TABLE IF EXISTS knowledge_processing_jobs CASCADE;
DROP TABLE IF EXISTS knowledge_document_versions CASCADE;
DROP TABLE IF EXISTS knowledge_folder_watchers CASCADE;
DROP TABLE IF EXISTS organization_memberships CASCADE;
DROP TABLE IF EXISTS organization_whiteboard_events CASCADE;
DROP TABLE IF EXISTS organization_modules CASCADE;
DROP TABLE IF EXISTS user_capabilities CASCADE;
DROP TABLE IF EXISTS knowledge_documents CASCADE;
DROP TABLE IF EXISTS event_logs CASCADE;
DROP TABLE IF EXISTS user_sessions CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS invoices CASCADE;
DROP TABLE IF EXISTS contractors CASCADE;
DROP TABLE IF EXISTS organizations CASCADE;
"""

ADDITIVE_COLUMNS = {
    "organizations": {
        "module_shortcuts_json": "TEXT NOT NULL DEFAULT '{}'",
        "communication_provider": "TEXT NOT NULL DEFAULT 'telegram'",
        "communication_config_json": "TEXT NOT NULL DEFAULT '{}'",
        "work_item_sla_policy_json": "TEXT NOT NULL DEFAULT '{}'",
        "shared_note_text": "TEXT NOT NULL DEFAULT ''",
        "shared_note_updated_at": "TEXT",
        "shared_note_updated_by_user_id": "INTEGER",
        "telegram_chat_id": "TEXT",
        "telegram_chat_name": "TEXT",
        "email_inbox_address": "TEXT",
        "email_allowed_sender": "TEXT",
        "email_subject_keyword": "TEXT",
        "email_integration_enabled": "INTEGER NOT NULL DEFAULT 0",
        "email_last_checked_at": "TEXT",
        "email_last_check_status": "TEXT",
        "email_last_connection_tested_at": "TEXT",
        "email_last_connection_status": "TEXT",
        "ksef_company_identifier": "TEXT",
        "ksef_environment": "TEXT",
        "ksef_integration_enabled": "INTEGER NOT NULL DEFAULT 0",
        "ksef_last_checked_at": "TEXT",
        "ksef_last_check_status": "TEXT",
        "ksef_last_connection_tested_at": "TEXT",
        "ksef_last_connection_status": "TEXT",
        "ksef_correction_delegate_user_id": "INTEGER",
        "ksef_correction_delegate_assigned_at": "TEXT",
        "ksef_correction_delegate_expires_at": "TEXT",
    },
    "contractors": {
        "organization_id": "INTEGER",
    },
    "users": {
        "organization_id": "INTEGER",
        "telegram_user_id": "TEXT",
        "telegram_reminders_enabled": "INTEGER NOT NULL DEFAULT 1",
        "reminder_quiet_hours_start": "TEXT",
        "reminder_quiet_hours_end": "TEXT",
        "reminder_repeat_interval_minutes": "INTEGER NOT NULL DEFAULT 0",
        "can_upload_knowledge": "INTEGER",
        "browser_notifications_enabled": "INTEGER NOT NULL DEFAULT 0",
        "personal_note_text": "TEXT NOT NULL DEFAULT ''",
        "personal_note_updated_at": "TEXT",
        "workspace_state_json": "TEXT",
        "workspace_state_updated_at": "TEXT",
        "workspace_state_device_id": "TEXT",
    },
    "user_calendars": {
        "calendar_kind": "TEXT NOT NULL DEFAULT 'inne'",
        "linked_organization_id": "INTEGER",
        "default_duration_minutes": "INTEGER NOT NULL DEFAULT 60",
        "external_calendar_id": "TEXT",
        "external_calendar_name": "TEXT",
        "external_calendar_timezone": "TEXT",
    },
    "user_sessions": {
        "device_id": "TEXT",
        "device_label": "TEXT",
    },
    "user_google_calendar_connections": {
        "employee_visibility_confirmed": "INTEGER NOT NULL DEFAULT 0",
        "employee_confirmation_at": "TEXT",
        "approval_status": "TEXT NOT NULL DEFAULT 'pending_approval'",
        "approved_by_user_id": "INTEGER",
        "approved_at": "TEXT",
    },
    "tasks": {
        "external_calendar_event_id": "TEXT",
        "external_calendar_event_url": "TEXT",
        "external_calendar_synced_at": "TEXT",
        "external_calendar_sync_error": "TEXT",
        "external_calendar_sync_state": "TEXT",
        "external_calendar_sync_message": "TEXT",
        "external_calendar_last_checked_at": "TEXT",
        "external_calendar_last_check_error": "TEXT",
        "external_calendar_remote_updated_at": "TEXT",
        "external_calendar_remote_etag": "TEXT",
        "external_calendar_last_sync_source": "TEXT",
        "recurrence_pattern": "TEXT NOT NULL DEFAULT 'brak'",
        "recurrence_interval": "INTEGER NOT NULL DEFAULT 1",
        "recurrence_weekdays": "TEXT",
        "recurrence_end_at": "TEXT",
        "recurrence_series_id": "TEXT",
        "recurrence_parent_task_id": "INTEGER",
        "remind_at": "TEXT",
        "visibility_scope": "TEXT",
        "owner_user_id": "INTEGER",
        "reminder_sent_at": "TEXT",
        "reminder_last_attempt_at": "TEXT",
        "reminder_last_error": "TEXT",
        "calendar_id": "INTEGER",
        "calendar_duration_minutes": "INTEGER NOT NULL DEFAULT 60",
    },
    "task_notes": {
        "parent_note_id": "INTEGER",
        "note_kind": "TEXT NOT NULL DEFAULT 'comment'",
        "mentioned_user_ids": "TEXT",
        "mentioned_user_names": "TEXT",
    },
    "task_checklist_items": {
        "organization_id": "INTEGER",
    },
    "task_templates": {
        "organization_id": "INTEGER",
    },
    "approval_requests": {
        "organization_id": "INTEGER",
    },
    "knowledge_documents": {
        "processing_status": "TEXT NOT NULL DEFAULT 'queued'",
        "processing_error": "TEXT",
        "current_version_number": "INTEGER NOT NULL DEFAULT 0",
        "official_version_number": "INTEGER NOT NULL DEFAULT 0",
        "official_version_marked_at": "TEXT",
        "official_version_marked_by_user_id": "INTEGER",
        "last_processed_at": "TEXT",
        "processing_started_at": "TEXT",
        "library_path": "TEXT NOT NULL DEFAULT ''",
        "is_downloadable": "INTEGER NOT NULL DEFAULT 1",
        "use_in_assistant": "INTEGER NOT NULL DEFAULT 1",
        "business_status": "TEXT NOT NULL DEFAULT 'roboczy'",
        "business_status_before_archive": "TEXT",
        "owner_user_id": "INTEGER",
        "reviewer_user_id": "INTEGER",
        "approver_user_id": "INTEGER",
        "lifecycle_status": "TEXT NOT NULL DEFAULT 'active'",
        "archived_at": "TEXT",
        "archived_by_user_id": "INTEGER",
        "deleted_at": "TEXT",
        "deleted_by_user_id": "INTEGER",
        "duplicate_status": "TEXT NOT NULL DEFAULT 'none'",
        "duplicate_of_document_id": "INTEGER",
        "duplicate_score": "REAL NOT NULL DEFAULT 0",
        "duplicate_reason": "TEXT",
        "last_seen_in_folder_at": "TEXT",
    },
    "billing_payers": {
        "has_large_family_card": "INTEGER NOT NULL DEFAULT 0",
    },
    "billing_students": {
        "family_billing_order": "INTEGER NOT NULL DEFAULT 1",
    },
    "invoices": {
        "organization_id": "INTEGER",
        "document_type": "TEXT",
        "authoritative_source": "TEXT",
        "file_storage_key": "TEXT",
        "ocr_storage_key": "TEXT",
        "storage_backend": "TEXT",
        "source_external_id": "TEXT",
        "source_sender_name": "TEXT",
        "source_sender_id": "TEXT",
        "source_metadata": "TEXT",
        "assigned_user_id": "INTEGER",
        "workflow_state": "TEXT NOT NULL DEFAULT 'w_pracy'",
        "ready_for_handoff_at": "TEXT",
        "ready_for_handoff_by_user_id": "INTEGER",
        "handoff_target": "TEXT",
        "handoff_note": "TEXT",
        "handed_off_at": "TEXT",
        "handed_off_by_user_id": "INTEGER",
        "closed_at": "TEXT",
        "closed_by_user_id": "INTEGER",
        "closed_reason": "TEXT",
        "reopened_at": "TEXT",
        "reopened_by_user_id": "INTEGER",
        "reopen_reason": "TEXT",
    },
    "event_logs": {
        "organization_id": "INTEGER",
    },
    "invoice_handoff_batches": {
        "export_format": "TEXT",
        "export_metadata": "TEXT",
        "updated_at": "TEXT",
    },
    "invoice_handoff_batch_items": {
        "organization_id": "INTEGER",
        "workflow_state_snapshot": "TEXT",
        "status_snapshot": "TEXT",
        "source_snapshot": "TEXT",
        "created_at": "TEXT",
    },
}

ADDITIVE_INDEXES = (
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_organizations_telegram_chat_id ON organizations(telegram_chat_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_telegram_user_id ON users(telegram_user_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_contractors_org_nip ON contractors(organization_id, nip)",
    "CREATE INDEX IF NOT EXISTS idx_users_organization_id ON users(organization_id)",
    "CREATE INDEX IF NOT EXISTS idx_invoices_assigned_user_id ON invoices(assigned_user_id)",
    "CREATE INDEX IF NOT EXISTS idx_invoices_workflow_state ON invoices(workflow_state)",
    "CREATE INDEX IF NOT EXISTS idx_invoices_handed_off_at ON invoices(handed_off_at)",
    "CREATE INDEX IF NOT EXISTS idx_invoices_closed_at ON invoices(closed_at)",
    "CREATE INDEX IF NOT EXISTS idx_intake_items_linked_invoice_source ON intake_items(linked_invoice_id, source_kind)",
    "CREATE INDEX IF NOT EXISTS idx_invoice_handoff_batches_updated_at ON invoice_handoff_batches(updated_at)",
    "CREATE INDEX IF NOT EXISTS idx_invoice_handoff_batch_items_org ON invoice_handoff_batch_items(organization_id)",
    "CREATE INDEX IF NOT EXISTS idx_knowledge_documents_status ON knowledge_documents(processing_status)",
    "CREATE INDEX IF NOT EXISTS idx_knowledge_documents_last_processed_at ON knowledge_documents(last_processed_at)",
    "CREATE INDEX IF NOT EXISTS idx_knowledge_documents_official_version_number ON knowledge_documents(official_version_number)",
    "CREATE INDEX IF NOT EXISTS idx_knowledge_documents_library_path ON knowledge_documents(library_path)",
    "CREATE INDEX IF NOT EXISTS idx_knowledge_documents_is_downloadable ON knowledge_documents(is_downloadable)",
    "CREATE INDEX IF NOT EXISTS idx_knowledge_documents_use_in_assistant ON knowledge_documents(use_in_assistant)",
    "CREATE INDEX IF NOT EXISTS idx_knowledge_documents_business_status ON knowledge_documents(business_status)",
    "CREATE INDEX IF NOT EXISTS idx_knowledge_documents_owner_user_id ON knowledge_documents(owner_user_id)",
    "CREATE INDEX IF NOT EXISTS idx_knowledge_documents_reviewer_user_id ON knowledge_documents(reviewer_user_id)",
    "CREATE INDEX IF NOT EXISTS idx_knowledge_documents_approver_user_id ON knowledge_documents(approver_user_id)",
    "CREATE INDEX IF NOT EXISTS idx_knowledge_documents_lifecycle_status ON knowledge_documents(lifecycle_status)",
    "CREATE INDEX IF NOT EXISTS idx_knowledge_documents_duplicate_status ON knowledge_documents(duplicate_status)",
    "CREATE INDEX IF NOT EXISTS idx_knowledge_documents_duplicate_of ON knowledge_documents(duplicate_of_document_id)",
    "CREATE INDEX IF NOT EXISTS idx_invoices_organization_id ON invoices(organization_id)",
    "CREATE INDEX IF NOT EXISTS idx_event_logs_organization_id ON event_logs(organization_id)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_remind_at ON tasks(remind_at)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_reminder_sent_at ON tasks(reminder_sent_at)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_reminder_last_attempt_at ON tasks(reminder_last_attempt_at)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_owner_user_id ON tasks(owner_user_id)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_visibility_scope ON tasks(visibility_scope)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_user_calendars_owner_display_name ON user_calendars(owner_user_id, display_name)",
    "CREATE INDEX IF NOT EXISTS idx_user_calendars_owner_user_id ON user_calendars(owner_user_id)",
    "CREATE INDEX IF NOT EXISTS idx_user_calendars_linked_organization_id ON user_calendars(linked_organization_id)",
    "CREATE INDEX IF NOT EXISTS idx_user_calendars_external_calendar_id ON user_calendars(external_calendar_id)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_calendar_id ON tasks(calendar_id)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_external_calendar_event_id ON tasks(external_calendar_event_id)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_recurrence_pattern ON tasks(recurrence_pattern)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_recurrence_series_id ON tasks(recurrence_series_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_work_items_org_source ON work_items(organization_id, source_type, source_id)",
    "CREATE INDEX IF NOT EXISTS idx_work_items_org_status ON work_items(organization_id, status)",
    "CREATE INDEX IF NOT EXISTS idx_work_items_org_priority_score ON work_items(organization_id, priority_score)",
    "CREATE INDEX IF NOT EXISTS idx_work_items_org_sla_deadline ON work_items(organization_id, sla_deadline_at)",
    "CREATE INDEX IF NOT EXISTS idx_work_items_org_sla_stage ON work_items(organization_id, sla_stage)",
    "CREATE INDEX IF NOT EXISTS idx_work_items_org_due_at ON work_items(organization_id, due_at)",
    "CREATE INDEX IF NOT EXISTS idx_work_items_assigned_user_id ON work_items(assigned_user_id)",
    "CREATE INDEX IF NOT EXISTS idx_work_items_org_assigned_status ON work_items(organization_id, assigned_user_id, status)",
    "CREATE INDEX IF NOT EXISTS idx_work_item_history_item_id ON work_item_history(work_item_id)",
    "CREATE INDEX IF NOT EXISTS idx_work_item_history_org_id ON work_item_history(organization_id)",
    "CREATE INDEX IF NOT EXISTS idx_task_notes_parent_note_id ON task_notes(parent_note_id)",
    "CREATE INDEX IF NOT EXISTS idx_task_attachments_task_id ON task_attachments(task_id)",
    "CREATE INDEX IF NOT EXISTS idx_task_attachments_org_id ON task_attachments(organization_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_task_reminder_outbox_unique ON task_reminder_outbox(task_id, delivery_channel, delivery_key)",
    "CREATE INDEX IF NOT EXISTS idx_task_reminder_outbox_status_available ON task_reminder_outbox(status, available_at)",
    "CREATE INDEX IF NOT EXISTS idx_task_reminder_outbox_org_status ON task_reminder_outbox(organization_id, status)",
    "CREATE INDEX IF NOT EXISTS idx_task_reminder_outbox_task_id ON task_reminder_outbox(task_id)",
    "CREATE INDEX IF NOT EXISTS idx_task_reminder_outbox_attempts_outbox_id ON task_reminder_outbox_attempts(task_reminder_outbox_id)",
    "CREATE INDEX IF NOT EXISTS idx_task_reminder_outbox_attempts_task_id ON task_reminder_outbox_attempts(task_id)",
    "CREATE INDEX IF NOT EXISTS idx_task_reminder_outbox_attempts_org_id ON task_reminder_outbox_attempts(organization_id)",
    "CREATE INDEX IF NOT EXISTS idx_user_google_calendar_connections_user_id ON user_google_calendar_connections(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_user_google_calendar_connections_approval_status ON user_google_calendar_connections(approval_status)",
    "CREATE INDEX IF NOT EXISTS idx_user_calendar_assignments_user_calendar_id ON user_calendar_assignments(user_calendar_id)",
    "CREATE INDEX IF NOT EXISTS idx_user_calendar_assignments_assigned_by_user_id ON user_calendar_assignments(assigned_by_user_id)",
    "CREATE INDEX IF NOT EXISTS idx_google_calendar_oauth_states_state_token ON google_calendar_oauth_states(state_token)",
    "CREATE INDEX IF NOT EXISTS idx_google_calendar_oauth_states_expires_at ON google_calendar_oauth_states(expires_at)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_task_visibility_users_unique ON task_visibility_users(task_id, user_id)",
    "CREATE INDEX IF NOT EXISTS idx_task_visibility_users_task_id ON task_visibility_users(task_id)",
    "CREATE INDEX IF NOT EXISTS idx_task_visibility_users_user_id ON task_visibility_users(user_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_task_links_unique ON task_links(task_id, entity_type, entity_id)",
    "CREATE INDEX IF NOT EXISTS idx_task_links_entity ON task_links(organization_id, entity_type, entity_id)",
    "CREATE INDEX IF NOT EXISTS idx_task_links_task_id ON task_links(task_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_schools_org_full_name ON billing_schools(organization_id, full_name)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_schools_org_short_name ON billing_schools(organization_id, short_name)",
    "CREATE INDEX IF NOT EXISTS idx_billing_schools_org ON billing_schools(organization_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_models_org_name ON billing_models(organization_id, name)",
    "CREATE INDEX IF NOT EXISTS idx_billing_models_org ON billing_models(organization_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_payers_org_payment_identifier ON billing_payers(organization_id, payment_identifier)",
    "CREATE INDEX IF NOT EXISTS idx_billing_payers_org ON billing_payers(organization_id)",
    "CREATE INDEX IF NOT EXISTS idx_billing_students_org ON billing_students(organization_id)",
    "CREATE INDEX IF NOT EXISTS idx_billing_students_payer ON billing_students(billing_payer_id)",
    "CREATE INDEX IF NOT EXISTS idx_billing_students_school ON billing_students(billing_school_id)",
    "CREATE INDEX IF NOT EXISTS idx_billing_students_model ON billing_students(billing_model_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_charge_batches_org_model_period ON billing_charge_batches(organization_id, billing_model_id, period_label)",
    "CREATE INDEX IF NOT EXISTS idx_billing_charge_batches_org ON billing_charge_batches(organization_id)",
    "CREATE INDEX IF NOT EXISTS idx_billing_charge_batches_model ON billing_charge_batches(billing_model_id)",
    "CREATE INDEX IF NOT EXISTS idx_billing_charges_org ON billing_charges(organization_id)",
    "CREATE INDEX IF NOT EXISTS idx_billing_charges_batch ON billing_charges(billing_charge_batch_id)",
    "CREATE INDEX IF NOT EXISTS idx_billing_charges_model ON billing_charges(billing_model_id)",
    "CREATE INDEX IF NOT EXISTS idx_billing_charges_student ON billing_charges(billing_student_id)",
    "CREATE INDEX IF NOT EXISTS idx_billing_charges_payer ON billing_charges(billing_payer_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_student_charge_state_org_student_year ON billing_student_charge_state(organization_id, billing_student_id, school_year)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_payer_charge_state_org_payer_year ON billing_payer_charge_state(organization_id, billing_payer_id, school_year)",
)


def _ensure_user_capabilities_schema(connection) -> None:
    if connection.backend == "sqlite":
        connection.raw_connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS user_capabilities (
                user_capability_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                capability_code TEXT NOT NULL,
                granted_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_user_capabilities_unique
                ON user_capabilities(user_id, capability_code);
            CREATE INDEX IF NOT EXISTS idx_user_capabilities_user
                ON user_capabilities(user_id);
            """
        )
        return

    for statement in _split_sql_script(
        """
        CREATE TABLE IF NOT EXISTS user_capabilities (
            user_capability_id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            capability_code TEXT NOT NULL,
            granted_at TEXT NOT NULL,
            CONSTRAINT fk_user_capabilities_user
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_user_capabilities_unique
            ON user_capabilities(user_id, capability_code);
        CREATE INDEX IF NOT EXISTS idx_user_capabilities_user
            ON user_capabilities(user_id);
        """
    ):
        connection.execute(statement)


def _ensure_organization_memberships_schema(connection) -> None:
    if connection.backend == "sqlite":
        connection.raw_connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS organization_memberships (
                organization_membership_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                organization_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                membership_status TEXT NOT NULL DEFAULT 'active',
                is_primary INTEGER NOT NULL DEFAULT 1,
                granted_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_organization_memberships_unique
                ON organization_memberships(user_id, organization_id);
            CREATE INDEX IF NOT EXISTS idx_organization_memberships_user
                ON organization_memberships(user_id, is_primary);
            CREATE INDEX IF NOT EXISTS idx_organization_memberships_org
                ON organization_memberships(organization_id, membership_status);
            """
        )
        return

    for statement in _split_sql_script(
        """
        CREATE TABLE IF NOT EXISTS organization_memberships (
            organization_membership_id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            organization_id BIGINT NOT NULL,
            role TEXT NOT NULL,
            membership_status TEXT NOT NULL DEFAULT 'active',
            is_primary INTEGER NOT NULL DEFAULT 1,
            granted_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            CONSTRAINT fk_organization_memberships_user
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            CONSTRAINT fk_organization_memberships_organization
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_organization_memberships_unique
            ON organization_memberships(user_id, organization_id);
        CREATE INDEX IF NOT EXISTS idx_organization_memberships_user
            ON organization_memberships(user_id, is_primary);
        CREATE INDEX IF NOT EXISTS idx_organization_memberships_org
            ON organization_memberships(organization_id, membership_status);
        """
    ):
        connection.execute(statement)


def _ensure_organization_modules_schema(connection) -> None:
    if connection.backend == "sqlite":
        connection.raw_connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS organization_modules (
                organization_module_id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization_id INTEGER NOT NULL,
                module_code TEXT NOT NULL,
                enabled_at TEXT NOT NULL,
                enabled_by_user_id INTEGER,
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE,
                FOREIGN KEY (enabled_by_user_id) REFERENCES users(user_id)
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_organization_modules_unique
                ON organization_modules(organization_id, module_code);
            CREATE INDEX IF NOT EXISTS idx_organization_modules_organization
                ON organization_modules(organization_id);
            """
        )
        return

    for statement in _split_sql_script(
        """
        CREATE TABLE IF NOT EXISTS organization_modules (
            organization_module_id BIGSERIAL PRIMARY KEY,
            organization_id BIGINT NOT NULL,
            module_code TEXT NOT NULL,
            enabled_at TEXT NOT NULL,
            enabled_by_user_id BIGINT,
            CONSTRAINT fk_organization_modules_organization
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE,
            CONSTRAINT fk_organization_modules_enabled_by_user
                FOREIGN KEY (enabled_by_user_id) REFERENCES users(user_id)
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_organization_modules_unique
            ON organization_modules(organization_id, module_code);
        CREATE INDEX IF NOT EXISTS idx_organization_modules_organization
            ON organization_modules(organization_id);
        """
    ):
        connection.execute(statement)


def _ensure_email_import_history_schema(connection) -> None:
    if connection.backend == "sqlite":
        connection.raw_connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS email_import_runs (
                email_import_run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization_id INTEGER NOT NULL,
                mailbox_address TEXT,
                inbox_address TEXT,
                trigger_mode TEXT NOT NULL,
                actor TEXT NOT NULL,
                routing_mode TEXT NOT NULL DEFAULT 'central_mailbox',
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL,
                checked_message_count INTEGER NOT NULL DEFAULT 0,
                matched_message_count INTEGER NOT NULL DEFAULT 0,
                matched_attachment_count INTEGER NOT NULL DEFAULT 0,
                imported_invoice_count INTEGER NOT NULL DEFAULT 0,
                skipped_existing_count INTEGER NOT NULL DEFAULT 0,
                skipped_error_count INTEGER NOT NULL DEFAULT 0,
                summary_message TEXT,
                details TEXT,
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_email_import_runs_org
                ON email_import_runs(organization_id);
            CREATE INDEX IF NOT EXISTS idx_email_import_runs_started_at
                ON email_import_runs(started_at DESC);

            CREATE TABLE IF NOT EXISTS email_import_items (
                email_import_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_import_run_id INTEGER NOT NULL,
                organization_id INTEGER NOT NULL,
                imap_uid TEXT,
                message_id TEXT,
                sender_email TEXT,
                subject TEXT,
                recipients TEXT,
                matched_recipient TEXT,
                attachment_name TEXT,
                attachment_type TEXT,
                attachment_index INTEGER,
                source_external_id TEXT,
                item_status TEXT NOT NULL,
                invoice_id INTEGER,
                reason TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (email_import_run_id) REFERENCES email_import_runs(email_import_run_id) ON DELETE CASCADE,
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id)
            );
            CREATE INDEX IF NOT EXISTS idx_email_import_items_run
                ON email_import_items(email_import_run_id);
            CREATE INDEX IF NOT EXISTS idx_email_import_items_org
                ON email_import_items(organization_id);
            CREATE INDEX IF NOT EXISTS idx_email_import_items_status
                ON email_import_items(item_status);
            """
        )
        return

    for statement in _split_sql_script(
        """
        CREATE TABLE IF NOT EXISTS email_import_runs (
            email_import_run_id BIGSERIAL PRIMARY KEY,
            organization_id BIGINT NOT NULL,
            mailbox_address TEXT,
            inbox_address TEXT,
            trigger_mode TEXT NOT NULL,
            actor TEXT NOT NULL,
            routing_mode TEXT NOT NULL DEFAULT 'central_mailbox',
            started_at TEXT NOT NULL,
            finished_at TEXT,
            status TEXT NOT NULL,
            checked_message_count INTEGER NOT NULL DEFAULT 0,
            matched_message_count INTEGER NOT NULL DEFAULT 0,
            matched_attachment_count INTEGER NOT NULL DEFAULT 0,
            imported_invoice_count INTEGER NOT NULL DEFAULT 0,
            skipped_existing_count INTEGER NOT NULL DEFAULT 0,
            skipped_error_count INTEGER NOT NULL DEFAULT 0,
            summary_message TEXT,
            details TEXT,
            CONSTRAINT fk_email_import_runs_organization
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_email_import_runs_org
            ON email_import_runs(organization_id);
        CREATE INDEX IF NOT EXISTS idx_email_import_runs_started_at
            ON email_import_runs(started_at DESC);

        CREATE TABLE IF NOT EXISTS email_import_items (
            email_import_item_id BIGSERIAL PRIMARY KEY,
            email_import_run_id BIGINT NOT NULL,
            organization_id BIGINT NOT NULL,
            imap_uid TEXT,
            message_id TEXT,
            sender_email TEXT,
            subject TEXT,
            recipients TEXT,
            matched_recipient TEXT,
            attachment_name TEXT,
            attachment_type TEXT,
            attachment_index INTEGER,
            source_external_id TEXT,
            item_status TEXT NOT NULL,
            invoice_id BIGINT,
            reason TEXT,
            created_at TEXT NOT NULL,
            CONSTRAINT fk_email_import_items_run
                FOREIGN KEY (email_import_run_id) REFERENCES email_import_runs(email_import_run_id) ON DELETE CASCADE,
            CONSTRAINT fk_email_import_items_organization
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE,
            CONSTRAINT fk_email_import_items_invoice
                FOREIGN KEY (invoice_id) REFERENCES invoices(id)
        );
        CREATE INDEX IF NOT EXISTS idx_email_import_items_run
            ON email_import_items(email_import_run_id);
        CREATE INDEX IF NOT EXISTS idx_email_import_items_org
            ON email_import_items(organization_id);
        CREATE INDEX IF NOT EXISTS idx_email_import_items_status
            ON email_import_items(item_status);
        """
    ):
        connection.execute(statement)


def _ensure_ksef_import_history_schema(connection) -> None:
    if connection.backend == "sqlite":
        connection.raw_connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS ksef_import_runs (
                ksef_import_run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization_id INTEGER NOT NULL,
                company_identifier TEXT,
                environment TEXT,
                trigger_mode TEXT NOT NULL,
                actor TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL,
                checked_document_count INTEGER NOT NULL DEFAULT 0,
                imported_invoice_count INTEGER NOT NULL DEFAULT 0,
                skipped_existing_count INTEGER NOT NULL DEFAULT 0,
                skipped_error_count INTEGER NOT NULL DEFAULT 0,
                summary_message TEXT,
                details TEXT,
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_ksef_import_runs_org
                ON ksef_import_runs(organization_id);
            CREATE INDEX IF NOT EXISTS idx_ksef_import_runs_started_at
                ON ksef_import_runs(started_at DESC);

            CREATE TABLE IF NOT EXISTS ksef_import_items (
                ksef_import_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ksef_import_run_id INTEGER NOT NULL,
                organization_id INTEGER NOT NULL,
                source_external_id TEXT,
                ksef_number TEXT,
                invoice_number TEXT,
                issuer_nip TEXT,
                issue_date TEXT,
                item_status TEXT NOT NULL,
                invoice_id INTEGER,
                reason TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (ksef_import_run_id) REFERENCES ksef_import_runs(ksef_import_run_id) ON DELETE CASCADE,
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id)
            );
            CREATE INDEX IF NOT EXISTS idx_ksef_import_items_run
                ON ksef_import_items(ksef_import_run_id);
            CREATE INDEX IF NOT EXISTS idx_ksef_import_items_org
                ON ksef_import_items(organization_id);
            CREATE INDEX IF NOT EXISTS idx_ksef_import_items_status
                ON ksef_import_items(item_status);
            """
        )
        return

    for statement in _split_sql_script(
        """
        CREATE TABLE IF NOT EXISTS ksef_import_runs (
            ksef_import_run_id BIGSERIAL PRIMARY KEY,
            organization_id BIGINT NOT NULL,
            company_identifier TEXT,
            environment TEXT,
            trigger_mode TEXT NOT NULL,
            actor TEXT NOT NULL,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            status TEXT NOT NULL,
            checked_document_count INTEGER NOT NULL DEFAULT 0,
            imported_invoice_count INTEGER NOT NULL DEFAULT 0,
            skipped_existing_count INTEGER NOT NULL DEFAULT 0,
            skipped_error_count INTEGER NOT NULL DEFAULT 0,
            summary_message TEXT,
            details TEXT,
            CONSTRAINT fk_ksef_import_runs_organization
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_ksef_import_runs_org
            ON ksef_import_runs(organization_id);
        CREATE INDEX IF NOT EXISTS idx_ksef_import_runs_started_at
            ON ksef_import_runs(started_at DESC);

        CREATE TABLE IF NOT EXISTS ksef_import_items (
            ksef_import_item_id BIGSERIAL PRIMARY KEY,
            ksef_import_run_id BIGINT NOT NULL,
            organization_id BIGINT NOT NULL,
            source_external_id TEXT,
            ksef_number TEXT,
            invoice_number TEXT,
            issuer_nip TEXT,
            issue_date TEXT,
            item_status TEXT NOT NULL,
            invoice_id BIGINT,
            reason TEXT,
            created_at TEXT NOT NULL,
            CONSTRAINT fk_ksef_import_items_run
                FOREIGN KEY (ksef_import_run_id) REFERENCES ksef_import_runs(ksef_import_run_id) ON DELETE CASCADE,
            CONSTRAINT fk_ksef_import_items_organization
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE,
            CONSTRAINT fk_ksef_import_items_invoice
                FOREIGN KEY (invoice_id) REFERENCES invoices(id)
        );
        CREATE INDEX IF NOT EXISTS idx_ksef_import_items_run
            ON ksef_import_items(ksef_import_run_id);
        CREATE INDEX IF NOT EXISTS idx_ksef_import_items_org
            ON ksef_import_items(organization_id);
        CREATE INDEX IF NOT EXISTS idx_ksef_import_items_status
            ON ksef_import_items(item_status);
        """
    ):
        connection.execute(statement)


def _ensure_invoice_ksef_override_schema(connection) -> None:
    if connection.backend == "sqlite":
        connection.raw_connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS invoice_ksef_field_overrides (
                invoice_ksef_field_override_id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization_id INTEGER NOT NULL,
                invoice_id INTEGER NOT NULL,
                approval_request_id INTEGER,
                field_name TEXT NOT NULL,
                source_value TEXT,
                local_value TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                requested_by_user_id INTEGER,
                approved_by_user_id INTEGER,
                rejected_by_user_id INTEGER,
                request_reason TEXT,
                decision_reason TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                approved_at TEXT,
                rejected_at TEXT,
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
                FOREIGN KEY (approval_request_id) REFERENCES approval_requests(approval_request_id) ON DELETE SET NULL,
                FOREIGN KEY (requested_by_user_id) REFERENCES users(user_id),
                FOREIGN KEY (approved_by_user_id) REFERENCES users(user_id),
                FOREIGN KEY (rejected_by_user_id) REFERENCES users(user_id)
            );
            CREATE INDEX IF NOT EXISTS idx_invoice_ksef_overrides_invoice_status
                ON invoice_ksef_field_overrides(invoice_id, status);
            CREATE INDEX IF NOT EXISTS idx_invoice_ksef_overrides_request
                ON invoice_ksef_field_overrides(approval_request_id);
            """
        )
        return

    for statement in _split_sql_script(
        """
        CREATE TABLE IF NOT EXISTS invoice_ksef_field_overrides (
            invoice_ksef_field_override_id BIGSERIAL PRIMARY KEY,
            organization_id BIGINT NOT NULL,
            invoice_id BIGINT NOT NULL,
            approval_request_id BIGINT,
            field_name TEXT NOT NULL,
            source_value TEXT,
            local_value TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            requested_by_user_id BIGINT,
            approved_by_user_id BIGINT,
            rejected_by_user_id BIGINT,
            request_reason TEXT,
            decision_reason TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            approved_at TEXT,
            rejected_at TEXT,
            CONSTRAINT fk_invoice_ksef_overrides_organization
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE,
            CONSTRAINT fk_invoice_ksef_overrides_invoice
                FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
            CONSTRAINT fk_invoice_ksef_overrides_request
                FOREIGN KEY (approval_request_id) REFERENCES approval_requests(approval_request_id) ON DELETE SET NULL,
            CONSTRAINT fk_invoice_ksef_overrides_requested_by
                FOREIGN KEY (requested_by_user_id) REFERENCES users(user_id),
            CONSTRAINT fk_invoice_ksef_overrides_approved_by
                FOREIGN KEY (approved_by_user_id) REFERENCES users(user_id),
            CONSTRAINT fk_invoice_ksef_overrides_rejected_by
                FOREIGN KEY (rejected_by_user_id) REFERENCES users(user_id)
        );
        CREATE INDEX IF NOT EXISTS idx_invoice_ksef_overrides_invoice_status
            ON invoice_ksef_field_overrides(invoice_id, status);
        CREATE INDEX IF NOT EXISTS idx_invoice_ksef_overrides_request
            ON invoice_ksef_field_overrides(approval_request_id);
        """
    ):
        connection.execute(statement)


def _ensure_whiteboard_schema(connection) -> None:
    if connection.backend == "sqlite":
        connection.raw_connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS organization_whiteboard_events (
                whiteboard_event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_by_user_id INTEGER,
                actor_label TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE,
                FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
            );
            CREATE INDEX IF NOT EXISTS idx_organization_whiteboard_events_org
                ON organization_whiteboard_events(organization_id, whiteboard_event_id);
            CREATE INDEX IF NOT EXISTS idx_organization_whiteboard_events_type
                ON organization_whiteboard_events(organization_id, event_type);
            """
        )
        return

    for statement in _split_sql_script(
        """
        CREATE TABLE IF NOT EXISTS organization_whiteboard_events (
            whiteboard_event_id BIGSERIAL PRIMARY KEY,
            organization_id BIGINT NOT NULL,
            event_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_by_user_id BIGINT,
            actor_label TEXT NOT NULL,
            created_at TEXT NOT NULL,
            CONSTRAINT fk_organization_whiteboard_events_organization
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE,
            CONSTRAINT fk_organization_whiteboard_events_user
                FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
        );
        CREATE INDEX IF NOT EXISTS idx_organization_whiteboard_events_org
            ON organization_whiteboard_events(organization_id, whiteboard_event_id);
        CREATE INDEX IF NOT EXISTS idx_organization_whiteboard_events_type
            ON organization_whiteboard_events(organization_id, event_type);
        """
    ):
        connection.execute(statement)


def _ensure_knowledge_pipeline_schema(connection) -> None:
    if connection.backend == "sqlite":
        connection.raw_connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS knowledge_document_versions (
                knowledge_document_version_id INTEGER PRIMARY KEY AUTOINCREMENT,
                knowledge_document_id INTEGER NOT NULL,
                organization_id INTEGER NOT NULL,
                version_number INTEGER NOT NULL,
                title TEXT NOT NULL,
                file_name TEXT NOT NULL,
                mime_type TEXT,
                file_link TEXT NOT NULL,
                file_storage_key TEXT NOT NULL,
                content_text TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                char_count INTEGER NOT NULL DEFAULT 0,
                source_type TEXT NOT NULL DEFAULT 'manual',
                created_by_user_id INTEGER,
                extraction_method TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (knowledge_document_id) REFERENCES knowledge_documents(knowledge_document_id) ON DELETE CASCADE,
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
                FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_knowledge_document_versions_unique
                ON knowledge_document_versions(knowledge_document_id, version_number);
            CREATE INDEX IF NOT EXISTS idx_knowledge_document_versions_document
                ON knowledge_document_versions(knowledge_document_id, created_at DESC);

            CREATE TABLE IF NOT EXISTS knowledge_processing_jobs (
                knowledge_processing_job_id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization_id INTEGER NOT NULL,
                knowledge_document_id INTEGER,
                job_type TEXT NOT NULL DEFAULT 'ingest',
                status TEXT NOT NULL DEFAULT 'pending',
                source_storage_key TEXT NOT NULL,
                source_file_name TEXT NOT NULL,
                source_mime_type TEXT,
                source_type TEXT NOT NULL DEFAULT 'manual',
                source_content_hash TEXT NOT NULL,
                supplemental_text TEXT,
                error_message TEXT,
                attempts INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL DEFAULT 3,
                created_by_user_id INTEGER,
                started_at TEXT,
                finished_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
                FOREIGN KEY (knowledge_document_id) REFERENCES knowledge_documents(knowledge_document_id) ON DELETE SET NULL,
                FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
            );
            CREATE INDEX IF NOT EXISTS idx_knowledge_processing_jobs_status
                ON knowledge_processing_jobs(status, created_at);
            CREATE INDEX IF NOT EXISTS idx_knowledge_processing_jobs_document
                ON knowledge_processing_jobs(knowledge_document_id, created_at DESC);
            """
        )
        return

    for statement in _split_sql_script(
        """
        CREATE TABLE IF NOT EXISTS knowledge_document_versions (
            knowledge_document_version_id BIGSERIAL PRIMARY KEY,
            knowledge_document_id BIGINT NOT NULL,
            organization_id BIGINT NOT NULL,
            version_number INTEGER NOT NULL,
            title TEXT NOT NULL,
            file_name TEXT NOT NULL,
            mime_type TEXT,
            file_link TEXT NOT NULL,
            file_storage_key TEXT NOT NULL,
            content_text TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            char_count INTEGER NOT NULL DEFAULT 0,
            source_type TEXT NOT NULL DEFAULT 'manual',
            created_by_user_id BIGINT,
            extraction_method TEXT,
            created_at TEXT NOT NULL,
            CONSTRAINT fk_knowledge_document_versions_document
                FOREIGN KEY (knowledge_document_id) REFERENCES knowledge_documents(knowledge_document_id) ON DELETE CASCADE,
            CONSTRAINT fk_knowledge_document_versions_organization
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
            CONSTRAINT fk_knowledge_document_versions_created_by_user
                FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_knowledge_document_versions_unique
            ON knowledge_document_versions(knowledge_document_id, version_number);
        CREATE INDEX IF NOT EXISTS idx_knowledge_document_versions_document
            ON knowledge_document_versions(knowledge_document_id, created_at DESC);

        CREATE TABLE IF NOT EXISTS knowledge_processing_jobs (
            knowledge_processing_job_id BIGSERIAL PRIMARY KEY,
            organization_id BIGINT NOT NULL,
            knowledge_document_id BIGINT,
            job_type TEXT NOT NULL DEFAULT 'ingest',
            status TEXT NOT NULL DEFAULT 'pending',
            source_storage_key TEXT NOT NULL,
            source_file_name TEXT NOT NULL,
            source_mime_type TEXT,
            source_type TEXT NOT NULL DEFAULT 'manual',
            source_content_hash TEXT NOT NULL,
            supplemental_text TEXT,
            error_message TEXT,
            attempts INTEGER NOT NULL DEFAULT 0,
            max_attempts INTEGER NOT NULL DEFAULT 3,
            created_by_user_id BIGINT,
            started_at TEXT,
            finished_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            CONSTRAINT fk_knowledge_processing_jobs_organization
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
            CONSTRAINT fk_knowledge_processing_jobs_document
                FOREIGN KEY (knowledge_document_id) REFERENCES knowledge_documents(knowledge_document_id) ON DELETE SET NULL,
            CONSTRAINT fk_knowledge_processing_jobs_created_by_user
                FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
        );
        CREATE INDEX IF NOT EXISTS idx_knowledge_processing_jobs_status
            ON knowledge_processing_jobs(status, created_at);
        CREATE INDEX IF NOT EXISTS idx_knowledge_processing_jobs_document
            ON knowledge_processing_jobs(knowledge_document_id, created_at DESC);
        """
    ):
        connection.execute(statement)


def _ensure_knowledge_watch_schema(connection) -> None:
    if connection.backend == "sqlite":
        connection.raw_connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS knowledge_folder_watchers (
                knowledge_folder_watcher_id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization_id INTEGER NOT NULL,
                watch_mode TEXT NOT NULL DEFAULT 'polling',
                last_scan_started_at TEXT,
                last_scan_completed_at TEXT,
                last_scan_status TEXT NOT NULL DEFAULT 'idle',
                last_actor TEXT,
                last_error TEXT,
                queued_new INTEGER NOT NULL DEFAULT 0,
                queued_updates INTEGER NOT NULL DEFAULT 0,
                unchanged_count INTEGER NOT NULL DEFAULT 0,
                skipped_count INTEGER NOT NULL DEFAULT 0,
                duplicate_count INTEGER NOT NULL DEFAULT 0,
                similar_count INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_knowledge_folder_watchers_org
                ON knowledge_folder_watchers(organization_id);
            """
        )
        return

    for statement in _split_sql_script(
        """
        CREATE TABLE IF NOT EXISTS knowledge_folder_watchers (
            knowledge_folder_watcher_id BIGSERIAL PRIMARY KEY,
            organization_id BIGINT NOT NULL,
            watch_mode TEXT NOT NULL DEFAULT 'polling',
            last_scan_started_at TEXT,
            last_scan_completed_at TEXT,
            last_scan_status TEXT NOT NULL DEFAULT 'idle',
            last_actor TEXT,
            last_error TEXT,
            queued_new INTEGER NOT NULL DEFAULT 0,
            queued_updates INTEGER NOT NULL DEFAULT 0,
            unchanged_count INTEGER NOT NULL DEFAULT 0,
            skipped_count INTEGER NOT NULL DEFAULT 0,
            duplicate_count INTEGER NOT NULL DEFAULT 0,
            similar_count INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL,
            CONSTRAINT fk_knowledge_folder_watchers_org
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_knowledge_folder_watchers_org
            ON knowledge_folder_watchers(organization_id);
        """
    ):
        connection.execute(statement)


def _ensure_knowledge_comment_schema(connection: DatabaseConnection) -> None:
    if connection.backend == "sqlite":
        connection.raw_connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS knowledge_document_comments (
                knowledge_document_comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                knowledge_document_id INTEGER NOT NULL,
                organization_id INTEGER NOT NULL,
                knowledge_document_version_id INTEGER,
                version_number INTEGER,
                parent_comment_id INTEGER,
                annotation_kind TEXT NOT NULL DEFAULT 'comment',
                anchor_label TEXT,
                anchor_excerpt TEXT,
                note_text TEXT NOT NULL,
                created_by_user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (knowledge_document_id) REFERENCES knowledge_documents(knowledge_document_id) ON DELETE CASCADE,
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
                FOREIGN KEY (knowledge_document_version_id) REFERENCES knowledge_document_versions(knowledge_document_version_id) ON DELETE SET NULL,
                FOREIGN KEY (parent_comment_id) REFERENCES knowledge_document_comments(knowledge_document_comment_id) ON DELETE CASCADE,
                FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_knowledge_document_comments_document_id
                ON knowledge_document_comments(knowledge_document_id, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_knowledge_document_comments_organization_id
                ON knowledge_document_comments(organization_id);
            CREATE INDEX IF NOT EXISTS idx_knowledge_document_comments_version_number
                ON knowledge_document_comments(knowledge_document_id, version_number);
            CREATE INDEX IF NOT EXISTS idx_knowledge_document_comments_parent_comment_id
                ON knowledge_document_comments(parent_comment_id);
            """
        )
        return

    for statement in (
        """
        CREATE TABLE IF NOT EXISTS knowledge_document_comments (
            knowledge_document_comment_id BIGSERIAL PRIMARY KEY,
            knowledge_document_id BIGINT NOT NULL,
            organization_id BIGINT NOT NULL,
            knowledge_document_version_id BIGINT,
            version_number INTEGER,
            parent_comment_id BIGINT,
            annotation_kind TEXT NOT NULL DEFAULT 'comment',
            anchor_label TEXT,
            anchor_excerpt TEXT,
            note_text TEXT NOT NULL,
            created_by_user_id BIGINT NOT NULL,
            created_at TEXT NOT NULL,
            CONSTRAINT fk_knowledge_document_comments_document
                FOREIGN KEY (knowledge_document_id) REFERENCES knowledge_documents(knowledge_document_id) ON DELETE CASCADE,
            CONSTRAINT fk_knowledge_document_comments_organization
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
            CONSTRAINT fk_knowledge_document_comments_version
                FOREIGN KEY (knowledge_document_version_id) REFERENCES knowledge_document_versions(knowledge_document_version_id) ON DELETE SET NULL,
            CONSTRAINT fk_knowledge_document_comments_parent
                FOREIGN KEY (parent_comment_id) REFERENCES knowledge_document_comments(knowledge_document_comment_id) ON DELETE CASCADE,
            CONSTRAINT fk_knowledge_document_comments_author
                FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_knowledge_document_comments_document_id ON knowledge_document_comments(knowledge_document_id, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_knowledge_document_comments_organization_id ON knowledge_document_comments(organization_id)",
        "CREATE INDEX IF NOT EXISTS idx_knowledge_document_comments_version_number ON knowledge_document_comments(knowledge_document_id, version_number)",
        "CREATE INDEX IF NOT EXISTS idx_knowledge_document_comments_parent_comment_id ON knowledge_document_comments(parent_comment_id)",
    ):
        connection.execute(statement)


def _split_sql_script(script: str) -> list[str]:
    return [statement.strip() for statement in script.split(";") if statement.strip()]


class DatabaseConnection:
    def __init__(self, raw_connection: Any, backend: str, driver_name: str) -> None:
        self.raw_connection = raw_connection
        self.backend = backend
        self.driver_name = driver_name

    def execute(self, query: str, params: Iterable[Any] | None = None):
        normalized_params = list(params or [])
        translated_query = self._translate_query(query)
        if self.backend == "sqlite":
            return self.raw_connection.execute(translated_query, normalized_params)
        if self.driver_name == "psycopg":
            return self.raw_connection.execute(translated_query, normalized_params)
        cursor = self.raw_connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute(translated_query, normalized_params)
        return cursor

    def commit(self) -> None:
        self.raw_connection.commit()

    def rollback(self) -> None:
        self.raw_connection.rollback()

    def close(self) -> None:
        self.raw_connection.close()

    def _translate_query(self, query: str) -> str:
        if self.backend == "sqlite":
            return query
        return query.replace("?", "%s")


def _open_sqlite_connection() -> DatabaseConnection:
    connection = sqlite3.connect(SQLITE_DB_PATH)
    connection.row_factory = sqlite3.Row
    return DatabaseConnection(connection, backend="sqlite", driver_name="sqlite")


def _open_postgres_connection() -> DatabaseConnection:
    if not DATABASE_URL:
        raise RuntimeError("Brakuje zmiennej INVOICE_DATABASE_URL dla PostgreSQL.")
    connect_timeout_seconds = max(3, int(os.getenv("INVOICE_DB_CONNECT_TIMEOUT_SECONDS", "10")))
    if psycopg is not None:
        connection = psycopg.connect(
            DATABASE_URL,
            row_factory=dict_row,
            connect_timeout=connect_timeout_seconds,
        )
        connection.execute("SET lock_timeout = '10000ms'")
        connection.execute("SET idle_in_transaction_session_timeout = '120000ms'")
        return DatabaseConnection(connection, backend="postgresql", driver_name="psycopg")
    if psycopg2 is not None:
        connection = psycopg2.connect(DATABASE_URL, connect_timeout=connect_timeout_seconds)
        cursor = connection.cursor()
        cursor.execute("SET lock_timeout = '10000ms'")
        cursor.execute("SET idle_in_transaction_session_timeout = '120000ms'")
        cursor.close()
        return DatabaseConnection(connection, backend="postgresql", driver_name="psycopg2")
    raise RuntimeError(
        "Brakuje sterownika PostgreSQL. Zainstaluj 'psycopg[binary]' albo 'psycopg2-binary'."
    )


def _open_connection() -> DatabaseConnection:
    ensure_directories()
    if str(DB_ENGINE or "").strip().lower() in {"sqlite", "sqlite3"}:
        return _open_sqlite_connection()
    return _open_postgres_connection()


def _is_deferred_index_creation_error(statement: str, error: Exception) -> bool:
    normalized_statement = " ".join(statement.strip().upper().split())
    if not (
        normalized_statement.startswith("CREATE INDEX IF NOT EXISTS")
        or normalized_statement.startswith("CREATE UNIQUE INDEX IF NOT EXISTS")
    ):
        return False
    message = str(error).lower()
    return "no such column" in message or "does not exist" in message


def _is_concurrent_create_race_error(statement: str, error: Exception) -> bool:
    normalized_statement = " ".join(statement.strip().upper().split())
    if "IF NOT EXISTS" not in normalized_statement:
        return False
    if not (
        normalized_statement.startswith("CREATE TABLE")
        or normalized_statement.startswith("CREATE INDEX")
        or normalized_statement.startswith("CREATE UNIQUE INDEX")
    ):
        return False
    message = str(error).lower()
    return (
        "pg_type_typname_nsp_index" in message
        or "already exists" in message
        or "duplicate key value violates unique constraint" in message
    )


def _run_schema_script(connection: DatabaseConnection, script: str) -> None:
    if connection.backend == "sqlite":
        connection.raw_connection.executescript(script)
        return
    connection.execute(script)


def _terminate_stale_init_sessions(connection: DatabaseConnection) -> None:
    if connection.backend == "sqlite":
        return
    rows = connection.execute(
        """
        SELECT pid
        FROM pg_stat_activity
        WHERE usename = current_user
          AND pid <> pg_backend_pid()
          AND state = 'idle in transaction'
          AND now() - state_change > interval '45 seconds'
          AND (
              query ILIKE ?
              OR query ILIKE ?
              OR query ILIKE ?
              OR query ILIKE ?
          )
        """,
        (
            "%schema_step%",
            "CREATE TABLE IF NOT EXISTS%",
            "CREATE INDEX IF NOT EXISTS%",
            "ALTER TABLE % ADD COLUMN%",
        ),
    ).fetchall()
    for row in rows:
        connection.execute("SELECT pg_terminate_backend(?)", (int(row["pid"]),))


def _terminate_reset_blocking_sessions(connection: DatabaseConnection) -> None:
    if connection.backend == "sqlite":
        return
    rows = connection.execute(
        """
        SELECT pid
        FROM pg_stat_activity
        WHERE usename = current_user
          AND datname = current_database()
          AND pid <> pg_backend_pid()
        """
    ).fetchall()
    for row in rows:
        connection.execute("SELECT pg_terminate_backend(?)", (int(row["pid"]),))


def _is_retryable_init_error(error: Exception) -> bool:
    message = str(error).lower()
    retry_markers = (
        "deadlock detected",
        "could not obtain lock on relation",
        "canceling statement due to lock timeout",
        "tuple concurrently updated",
        "duplicate key value violates unique constraint \"pg_type_typname_nsp_index\"",
        "terminating connection due to administrator command",
        "the connection is closed",
        "connection already closed",
    )
    return any(marker in message for marker in retry_markers)


def _list_table_columns(connection: DatabaseConnection, table_name: str) -> set[str]:
    if connection.backend == "sqlite":
        rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {row["name"] for row in rows}

    rows = connection.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = ?
        """,
        (table_name,),
    ).fetchall()
    return {row["column_name"] for row in rows}


def _ensure_additive_columns(connection: DatabaseConnection) -> None:
    for table_name, columns in ADDITIVE_COLUMNS.items():
        existing = _list_table_columns(connection, table_name)
        for column_name, column_type in columns.items():
            if column_name in existing:
                continue
            connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")


def _ensure_additive_indexes(connection: DatabaseConnection) -> None:
    for statement in ADDITIVE_INDEXES:
        uses_savepoint = connection.backend != "sqlite"
        if uses_savepoint:
            connection.execute("SAVEPOINT additive_index_step")
        try:
            connection.execute(statement)
            if uses_savepoint:
                connection.execute("RELEASE SAVEPOINT additive_index_step")
        except Exception as error:
            if uses_savepoint:
                connection.execute("ROLLBACK TO SAVEPOINT additive_index_step")
                connection.execute("RELEASE SAVEPOINT additive_index_step")
            if _is_deferred_index_creation_error(statement, error):
                continue
            raise


def _ensure_google_calendar_schema(connection: DatabaseConnection) -> None:
    if connection.backend == "sqlite":
        connection.raw_connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS user_google_calendar_connections (
                user_google_calendar_connection_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                google_email TEXT,
                access_token TEXT NOT NULL,
                refresh_token TEXT,
                token_expires_at TEXT NOT NULL,
                scope TEXT,
                employee_visibility_confirmed INTEGER NOT NULL DEFAULT 0,
                employee_confirmation_at TEXT,
                approval_status TEXT NOT NULL DEFAULT 'pending_approval',
                approved_by_user_id INTEGER,
                approved_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (approved_by_user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS user_calendar_assignments (
                user_calendar_assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                user_calendar_id INTEGER NOT NULL,
                assigned_by_user_id INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (user_calendar_id) REFERENCES user_calendars(user_calendar_id) ON DELETE CASCADE,
                FOREIGN KEY (assigned_by_user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS google_calendar_oauth_states (
                google_calendar_oauth_state_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                state_token TEXT NOT NULL UNIQUE,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
            """
        )
        return

    for statement in _split_sql_script(
        """
        CREATE TABLE IF NOT EXISTS user_google_calendar_connections (
            user_google_calendar_connection_id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL UNIQUE,
            google_email TEXT,
            access_token TEXT NOT NULL,
            refresh_token TEXT,
            token_expires_at TEXT NOT NULL,
            scope TEXT,
            employee_visibility_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
            employee_confirmation_at TEXT,
            approval_status TEXT NOT NULL DEFAULT 'pending_approval',
            approved_by_user_id BIGINT,
            approved_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            CONSTRAINT fk_user_google_calendar_connections_user
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            CONSTRAINT fk_user_google_calendar_connections_approved_by
                FOREIGN KEY (approved_by_user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS user_calendar_assignments (
            user_calendar_assignment_id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL UNIQUE,
            user_calendar_id BIGINT NOT NULL,
            assigned_by_user_id BIGINT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            CONSTRAINT fk_user_calendar_assignments_user
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            CONSTRAINT fk_user_calendar_assignments_calendar
                FOREIGN KEY (user_calendar_id) REFERENCES user_calendars(user_calendar_id) ON DELETE CASCADE,
            CONSTRAINT fk_user_calendar_assignments_assigned_by
                FOREIGN KEY (assigned_by_user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS google_calendar_oauth_states (
            google_calendar_oauth_state_id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            state_token TEXT NOT NULL UNIQUE,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            CONSTRAINT fk_google_calendar_oauth_states_user
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
        """
    ):
        connection.execute(statement)


def _ensure_invoice_comment_schema(connection: DatabaseConnection) -> None:
    if connection.backend == "sqlite":
        connection.raw_connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS invoice_comments (
                invoice_comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                organization_id INTEGER NOT NULL,
                parent_comment_id INTEGER,
                note_text TEXT NOT NULL,
                created_by_user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
                FOREIGN KEY (parent_comment_id) REFERENCES invoice_comments(invoice_comment_id) ON DELETE CASCADE,
                FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_invoice_comments_invoice_id ON invoice_comments(invoice_id);
            CREATE INDEX IF NOT EXISTS idx_invoice_comments_parent_comment_id ON invoice_comments(parent_comment_id);
            CREATE INDEX IF NOT EXISTS idx_invoice_comments_organization_id ON invoice_comments(organization_id);
            """
        )
        return

    for statement in (
        """
        CREATE TABLE IF NOT EXISTS invoice_comments (
            invoice_comment_id BIGSERIAL PRIMARY KEY,
            invoice_id BIGINT NOT NULL,
            organization_id BIGINT NOT NULL,
            parent_comment_id BIGINT,
            note_text TEXT NOT NULL,
            created_by_user_id BIGINT NOT NULL,
            created_at TEXT NOT NULL,
            CONSTRAINT fk_invoice_comments_invoice
                FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
            CONSTRAINT fk_invoice_comments_organization
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
            CONSTRAINT fk_invoice_comments_parent
                FOREIGN KEY (parent_comment_id) REFERENCES invoice_comments(invoice_comment_id) ON DELETE CASCADE,
            CONSTRAINT fk_invoice_comments_author
                FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_invoice_comments_invoice_id ON invoice_comments(invoice_id)",
        "CREATE INDEX IF NOT EXISTS idx_invoice_comments_parent_comment_id ON invoice_comments(parent_comment_id)",
        "CREATE INDEX IF NOT EXISTS idx_invoice_comments_organization_id ON invoice_comments(organization_id)",
    ):
        connection.execute(statement)


def _ensure_contractor_note_schema(connection: DatabaseConnection) -> None:
    if connection.backend == "sqlite":
        connection.raw_connection.executescript(
            """
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
            """
        )
        return

    for statement in (
        """
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
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_contractor_notes_contractor_id ON contractor_notes(contractor_id, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_contractor_notes_organization_id ON contractor_notes(organization_id)",
    ):
        connection.execute(statement)


def _ensure_module_inbox_schema(connection: DatabaseConnection) -> None:
    if connection.backend == "sqlite":
        connection.raw_connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS user_module_inbox_state (
                user_module_inbox_state_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                organization_id INTEGER NOT NULL,
                module_key TEXT NOT NULL,
                last_seen_event_id INTEGER,
                last_seen_at TEXT,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE,
                UNIQUE (user_id, organization_id, module_key)
            );

            CREATE INDEX IF NOT EXISTS idx_user_module_inbox_state_user_org
                ON user_module_inbox_state(user_id, organization_id, module_key);
            """
        )
        return

    for statement in (
        """
        CREATE TABLE IF NOT EXISTS user_module_inbox_state (
            user_module_inbox_state_id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            organization_id BIGINT NOT NULL,
            module_key TEXT NOT NULL,
            last_seen_event_id BIGINT,
            last_seen_at TEXT,
            updated_at TEXT NOT NULL,
            CONSTRAINT fk_user_module_inbox_state_user
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            CONSTRAINT fk_user_module_inbox_state_organization
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id) ON DELETE CASCADE,
            CONSTRAINT uq_user_module_inbox_state_user_org_module
                UNIQUE (user_id, organization_id, module_key)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_user_module_inbox_state_user_org ON user_module_inbox_state(user_id, organization_id, module_key)",
    ):
        connection.execute(statement)


def _ensure_system_email_oauth_schema(connection: DatabaseConnection) -> None:
    if connection.backend == "sqlite":
        connection.raw_connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS system_email_google_connections (
                system_email_google_connection_id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL UNIQUE,
                google_email TEXT,
                access_token TEXT NOT NULL,
                refresh_token TEXT,
                token_expires_at TEXT NOT NULL,
                scope TEXT,
                created_by_user_id INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS system_email_oauth_states (
                system_email_oauth_state_id INTEGER PRIMARY KEY AUTOINCREMENT,
                state_token TEXT NOT NULL UNIQUE,
                created_by_user_id INTEGER,
                login_hint TEXT,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_system_email_oauth_states_state_token
                ON system_email_oauth_states(state_token);
            CREATE INDEX IF NOT EXISTS idx_system_email_oauth_states_expires_at
                ON system_email_oauth_states(expires_at);
            """
        )
        return

    for statement in _split_sql_script(
        """
        CREATE TABLE IF NOT EXISTS system_email_google_connections (
            system_email_google_connection_id BIGSERIAL PRIMARY KEY,
            provider TEXT NOT NULL UNIQUE,
            google_email TEXT,
            access_token TEXT NOT NULL,
            refresh_token TEXT,
            token_expires_at TEXT NOT NULL,
            scope TEXT,
            created_by_user_id BIGINT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            CONSTRAINT fk_system_email_google_connections_user
                FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS system_email_oauth_states (
            system_email_oauth_state_id BIGSERIAL PRIMARY KEY,
            state_token TEXT NOT NULL UNIQUE,
            created_by_user_id BIGINT,
            login_hint TEXT,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            CONSTRAINT fk_system_email_oauth_states_user
                FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
        );

        CREATE INDEX IF NOT EXISTS idx_system_email_oauth_states_state_token
            ON system_email_oauth_states(state_token);
        CREATE INDEX IF NOT EXISTS idx_system_email_oauth_states_expires_at
            ON system_email_oauth_states(expires_at);
        """
    ):
        connection.execute(statement)


def _ensure_system_settings_schema(connection: DatabaseConnection) -> None:
    if connection.backend == "sqlite":
        connection.raw_connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS system_settings (
                system_setting_id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT NOT NULL UNIQUE,
                setting_value_text TEXT,
                updated_by_user_id INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (updated_by_user_id) REFERENCES users(user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_system_settings_key
                ON system_settings(setting_key);
            """
        )
        return

    for statement in _split_sql_script(
        """
        CREATE TABLE IF NOT EXISTS system_settings (
            system_setting_id BIGSERIAL PRIMARY KEY,
            setting_key TEXT NOT NULL UNIQUE,
            setting_value_text TEXT,
            updated_by_user_id BIGINT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            CONSTRAINT fk_system_settings_user
                FOREIGN KEY (updated_by_user_id) REFERENCES users(user_id)
        );

        CREATE INDEX IF NOT EXISTS idx_system_settings_key
            ON system_settings(setting_key);
        """
    ):
        connection.execute(statement)


def _ensure_invoice_handoff_schema(connection: DatabaseConnection) -> None:
    if connection.backend == "sqlite":
        connection.raw_connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS invoice_handoff_batches (
                invoice_handoff_batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization_id INTEGER NOT NULL,
                batch_number TEXT NOT NULL UNIQUE,
                handoff_target TEXT,
                note TEXT,
                status TEXT NOT NULL DEFAULT 'utworzona',
                invoice_count INTEGER NOT NULL DEFAULT 0,
                created_by_user_id INTEGER,
                created_at TEXT NOT NULL,
                exported_at TEXT,
                exported_by_user_id INTEGER,
                export_format TEXT,
                export_metadata TEXT,
                updated_at TEXT,
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
                FOREIGN KEY (created_by_user_id) REFERENCES users(user_id),
                FOREIGN KEY (exported_by_user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS invoice_handoff_batch_items (
                invoice_handoff_batch_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_handoff_batch_id INTEGER NOT NULL,
                invoice_id INTEGER NOT NULL,
                organization_id INTEGER,
                workflow_state_snapshot TEXT,
                status_snapshot TEXT,
                source_snapshot TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (invoice_handoff_batch_id) REFERENCES invoice_handoff_batches(invoice_handoff_batch_id) ON DELETE CASCADE,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id),
                UNIQUE (invoice_handoff_batch_id, invoice_id)
            );

            CREATE INDEX IF NOT EXISTS idx_invoice_handoff_batches_org_created_at
                ON invoice_handoff_batches(organization_id, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_invoice_handoff_batches_status
                ON invoice_handoff_batches(status);
            CREATE INDEX IF NOT EXISTS idx_invoice_handoff_batch_items_batch
                ON invoice_handoff_batch_items(invoice_handoff_batch_id);
            CREATE INDEX IF NOT EXISTS idx_invoice_handoff_batch_items_invoice
                ON invoice_handoff_batch_items(invoice_id);
            """
        )
        return

    for statement in _split_sql_script(
        """
        CREATE TABLE IF NOT EXISTS invoice_handoff_batches (
            invoice_handoff_batch_id BIGSERIAL PRIMARY KEY,
            organization_id BIGINT NOT NULL,
            batch_number TEXT NOT NULL UNIQUE,
            handoff_target TEXT,
            note TEXT,
            status TEXT NOT NULL DEFAULT 'utworzona',
            invoice_count INTEGER NOT NULL DEFAULT 0,
            created_by_user_id BIGINT,
            created_at TEXT NOT NULL,
            exported_at TEXT,
            exported_by_user_id BIGINT,
            export_format TEXT,
            export_metadata TEXT,
            updated_at TEXT,
            CONSTRAINT fk_invoice_handoff_batches_organization
                FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
            CONSTRAINT fk_invoice_handoff_batches_created_by
                FOREIGN KEY (created_by_user_id) REFERENCES users(user_id),
            CONSTRAINT fk_invoice_handoff_batches_exported_by
                FOREIGN KEY (exported_by_user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS invoice_handoff_batch_items (
            invoice_handoff_batch_item_id BIGSERIAL PRIMARY KEY,
            invoice_handoff_batch_id BIGINT NOT NULL,
            invoice_id BIGINT NOT NULL,
            organization_id BIGINT,
            workflow_state_snapshot TEXT,
            status_snapshot TEXT,
            source_snapshot TEXT,
            created_at TEXT NOT NULL,
            CONSTRAINT fk_invoice_handoff_batch_items_batch
                FOREIGN KEY (invoice_handoff_batch_id) REFERENCES invoice_handoff_batches(invoice_handoff_batch_id) ON DELETE CASCADE,
            CONSTRAINT fk_invoice_handoff_batch_items_invoice
                FOREIGN KEY (invoice_id) REFERENCES invoices(id),
            CONSTRAINT uq_invoice_handoff_batch_items_batch_invoice
                UNIQUE (invoice_handoff_batch_id, invoice_id)
        );

        CREATE INDEX IF NOT EXISTS idx_invoice_handoff_batches_org_created_at
            ON invoice_handoff_batches(organization_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_invoice_handoff_batches_status
            ON invoice_handoff_batches(status);
        CREATE INDEX IF NOT EXISTS idx_invoice_handoff_batch_items_batch
            ON invoice_handoff_batch_items(invoice_handoff_batch_id);
        CREATE INDEX IF NOT EXISTS idx_invoice_handoff_batch_items_invoice
            ON invoice_handoff_batch_items(invoice_id);
        """
    ):
        connection.execute(statement)


def _migrate_legacy_user_roles(connection: DatabaseConnection) -> None:
    user_columns = _list_table_columns(connection, "users")
    if "role" not in user_columns:
        return

    connection.execute(
        """
        UPDATE users
        SET role = ?
        WHERE role = 'administrator'
          AND organization_id IS NULL
        """,
        (SYSTEM_OWNER_ROLE,),
    )
    connection.execute(
        """
        UPDATE users
        SET role = ?
        WHERE role = 'administrator'
          AND organization_id IS NOT NULL
        """,
        (ORGANIZATION_ADMIN_ROLE,),
    )
    connection.execute(
        """
        UPDATE users
        SET role = ?
        WHERE role = 'podglad'
        """,
        (GUEST_ROLE,),
    )


def _ensure_task_visibility_defaults(connection: DatabaseConnection) -> None:
    task_columns = _list_table_columns(connection, "tasks")
    if "owner_user_id" not in task_columns or "visibility_scope" not in task_columns:
        return

    connection.execute(
        """
        UPDATE tasks
        SET owner_user_id = created_by_user_id
        WHERE owner_user_id IS NULL
        """
    )
    connection.execute(
        """
        UPDATE tasks
        SET visibility_scope = 'organizacja'
        WHERE visibility_scope IS NULL OR TRIM(COALESCE(visibility_scope, '')) = ''
        """
    )


def _ensure_user_knowledge_defaults(connection: DatabaseConnection) -> None:
    user_columns = _list_table_columns(connection, "users")
    if "can_upload_knowledge" not in user_columns:
        return

    connection.execute(
        """
        UPDATE users
        SET can_upload_knowledge = CASE
            WHEN role IN (?, ?, ?, ?) THEN 1
            ELSE 0
        END
        WHERE can_upload_knowledge IS NULL
        """,
        (SYSTEM_OWNER_ROLE, ORGANIZATION_ADMIN_ROLE, COORDINATOR_ROLE, OPERATOR_ROLE),
    )


def _ensure_user_capability_defaults(connection: DatabaseConnection) -> None:
    rows = connection.execute(
        """
        SELECT user_id, role, can_upload_knowledge
        FROM users
        """
    ).fetchall()
    timestamp = now_iso()
    for row in rows:
        desired = set(default_capabilities_for_role(str(row["role"] or "")))
        if int(row["can_upload_knowledge"] or 0):
            desired.update({KNOWLEDGE_UPLOAD_CAPABILITY, KNOWLEDGE_SYNC_CAPABILITY})
        else:
            desired.discard(KNOWLEDGE_UPLOAD_CAPABILITY)
            desired.discard(KNOWLEDGE_SYNC_CAPABILITY)
        if str(row["role"] or "") == GUEST_ROLE:
            desired = set(desired)
            desired.discard(KNOWLEDGE_UPLOAD_CAPABILITY)
            desired.discard(KNOWLEDGE_SYNC_CAPABILITY)
            desired.discard(KNOWLEDGE_MANAGE_CAPABILITY)
        existing = {
            capability_row["capability_code"]
            for capability_row in connection.execute(
                """
                SELECT capability_code
                FROM user_capabilities
                WHERE user_id = ?
                """,
                (row["user_id"],),
            ).fetchall()
        }
        for capability in sorted(desired - existing):
            connection.execute(
                """
                INSERT INTO user_capabilities (user_id, capability_code, granted_at)
                VALUES (?, ?, ?)
                """,
                (row["user_id"], capability, timestamp),
            )
        removable = set()
        if not int(row["can_upload_knowledge"] or 0):
            removable.update({KNOWLEDGE_UPLOAD_CAPABILITY, KNOWLEDGE_SYNC_CAPABILITY})
        if str(row["role"] or "") == GUEST_ROLE:
            removable.update(existing - desired)
        for capability in sorted(removable & existing):
            connection.execute(
                """
                DELETE FROM user_capabilities
                WHERE user_id = ? AND capability_code = ?
                """,
                (row["user_id"], capability),
            )


def _ensure_organization_membership_defaults(connection: DatabaseConnection) -> None:
    rows = connection.execute(
        """
        SELECT user_id, organization_id, role, is_active
        FROM users
        """
    ).fetchall()
    timestamp = now_iso()
    for row in rows:
        user_id = int(row["user_id"])
        connection.execute(
            "DELETE FROM organization_memberships WHERE user_id = ? AND is_primary = 1",
            (user_id,),
        )
        if row["organization_id"] is None:
            continue
        membership_status = "active" if int(row["is_active"] or 0) else "inactive"
        connection.execute(
            """
            INSERT INTO organization_memberships (
                user_id,
                organization_id,
                role,
                membership_status,
                is_primary,
                granted_at,
                updated_at
            ) VALUES (?, ?, ?, ?, 1, ?, ?)
            """,
            (
                user_id,
                int(row["organization_id"]),
                str(row["role"] or ""),
                membership_status,
                timestamp,
                timestamp,
            ),
        )


def _ensure_user_telegram_reminder_defaults(connection: DatabaseConnection) -> None:
    user_columns = _list_table_columns(connection, "users")
    if "telegram_reminders_enabled" not in user_columns:
        return

    connection.execute(
        """
        UPDATE users
        SET telegram_reminders_enabled = 1
          WHERE telegram_reminders_enabled IS NULL
        """
    )
    if "reminder_repeat_interval_minutes" in user_columns:
        connection.execute(
            """
            UPDATE users
            SET reminder_repeat_interval_minutes = 0
            WHERE reminder_repeat_interval_minutes IS NULL
            """
            )


def _ensure_user_calendar_defaults(connection: DatabaseConnection) -> None:
    calendar_columns = _list_table_columns(connection, "user_calendars")
    if "calendar_kind" in calendar_columns:
        connection.execute(
            """
            UPDATE user_calendars
            SET calendar_kind = 'inne'
            WHERE calendar_kind IS NULL OR TRIM(COALESCE(calendar_kind, '')) = ''
            """
        )
    if "default_duration_minutes" in calendar_columns:
        connection.execute(
            """
            UPDATE user_calendars
            SET default_duration_minutes = 60
            WHERE default_duration_minutes IS NULL OR default_duration_minutes < 1
            """
        )
    if "provider" in calendar_columns:
        connection.execute(
            """
            UPDATE user_calendars
            SET provider = 'google_ics'
            WHERE provider IS NULL OR TRIM(COALESCE(provider, '')) = ''
            """
        )
    if "external_calendar_name" in calendar_columns:
        connection.execute(
            """
            UPDATE user_calendars
            SET external_calendar_name = display_name
            WHERE provider = 'google_api'
              AND COALESCE(TRIM(external_calendar_name), '') = ''
            """
        )
    if "external_calendar_timezone" in calendar_columns:
        connection.execute(
            """
            UPDATE user_calendars
            SET external_calendar_timezone = 'Europe/Warsaw'
            WHERE provider = 'google_api'
              AND COALESCE(TRIM(external_calendar_timezone), '') = ''
            """
        )


def _ensure_google_oauth_state_cleanup(connection: DatabaseConnection) -> None:
    existing = _list_table_columns(connection, "google_calendar_oauth_states")
    if "expires_at" not in existing:
        return
    connection.execute(
        """
        DELETE FROM google_calendar_oauth_states
        WHERE expires_at <= ?
        """,
        (now_iso(),),
    )


def _ensure_google_calendar_connection_defaults(connection: DatabaseConnection) -> None:
    existing = _list_table_columns(connection, "user_google_calendar_connections")
    if not existing:
        return
    if "approval_status" in existing:
        connection.execute(
            """
            UPDATE user_google_calendar_connections
            SET approval_status = 'approved'
            WHERE approval_status IS NULL OR TRIM(COALESCE(approval_status, '')) = ''
            """
        )
    if "employee_visibility_confirmed" in existing:
        connection.execute(
            """
            UPDATE user_google_calendar_connections
            SET employee_visibility_confirmed = TRUE
            WHERE employee_visibility_confirmed IS NULL
            """
        )
    if "employee_confirmation_at" in existing:
        connection.execute(
            """
            UPDATE user_google_calendar_connections
            SET employee_confirmation_at = COALESCE(employee_confirmation_at, updated_at, created_at)
            WHERE COALESCE(employee_visibility_confirmed, FALSE) IS TRUE
              AND employee_confirmation_at IS NULL
            """
        )
    if "approved_at" in existing:
        connection.execute(
            """
            UPDATE user_google_calendar_connections
            SET approved_at = COALESCE(approved_at, updated_at, created_at)
            WHERE approval_status = 'approved'
              AND approved_at IS NULL
            """
        )


def _ensure_system_email_oauth_state_cleanup(connection: DatabaseConnection) -> None:
    existing = _list_table_columns(connection, "system_email_oauth_states")
    if "expires_at" not in existing:
        return
    connection.execute(
        """
        DELETE FROM system_email_oauth_states
        WHERE expires_at <= ?
        """,
        (now_iso(),),
    )


def _ensure_knowledge_document_defaults(connection: DatabaseConnection) -> None:
    knowledge_columns = _list_table_columns(connection, "knowledge_documents")
    if "processing_status" not in knowledge_columns:
        return

    connection.execute(
        """
        UPDATE knowledge_documents
        SET processing_status = CASE
            WHEN TRIM(COALESCE(content_text, '')) = '' THEN 'queued'
            ELSE 'ready'
        END
        WHERE processing_status IS NULL OR TRIM(COALESCE(processing_status, '')) = ''
        """
    )
    if "current_version_number" in knowledge_columns:
        connection.execute(
            """
            UPDATE knowledge_documents
            SET current_version_number = CASE
                WHEN TRIM(COALESCE(content_text, '')) = '' THEN 0
                ELSE 1
            END
            WHERE current_version_number IS NULL
            """
        )
    if "last_processed_at" in knowledge_columns:
        connection.execute(
            """
            UPDATE knowledge_documents
            SET last_processed_at = updated_at
            WHERE last_processed_at IS NULL
              AND processing_status = 'ready'
            """
        )
    if "official_version_number" in knowledge_columns:
        connection.execute(
            """
            UPDATE knowledge_documents
            SET official_version_number = CASE
                WHEN COALESCE(current_version_number, 0) >= 1 THEN COALESCE(current_version_number, 0)
                ELSE 0
            END
            WHERE official_version_number IS NULL
            """
        )
    if "official_version_marked_at" in knowledge_columns and "official_version_number" in knowledge_columns:
        connection.execute(
            """
            UPDATE knowledge_documents
            SET official_version_marked_at = COALESCE(last_processed_at, updated_at)
            WHERE official_version_marked_at IS NULL
              AND COALESCE(official_version_number, 0) >= 1
            """
        )
    if "official_version_marked_by_user_id" in knowledge_columns and "created_by_user_id" in knowledge_columns:
        connection.execute(
            """
            UPDATE knowledge_documents
            SET official_version_marked_by_user_id = created_by_user_id
            WHERE official_version_marked_by_user_id IS NULL
              AND COALESCE(official_version_number, 0) >= 1
            """
        )
    if "library_path" in knowledge_columns:
        connection.execute(
            """
            UPDATE knowledge_documents
            SET library_path = ''
            WHERE library_path IS NULL
            """
        )
    if "is_downloadable" in knowledge_columns:
        connection.execute(
            """
            UPDATE knowledge_documents
            SET is_downloadable = 1
            WHERE is_downloadable IS NULL
            """
        )
    if "use_in_assistant" in knowledge_columns:
        connection.execute(
            """
            UPDATE knowledge_documents
            SET use_in_assistant = 1
            WHERE use_in_assistant IS NULL
            """
        )
    if "business_status" in knowledge_columns:
        connection.execute(
            """
            UPDATE knowledge_documents
            SET business_status = CASE
                WHEN COALESCE(lifecycle_status, 'active') = 'archived' THEN 'archiwalny'
                WHEN COALESCE(current_version_number, 0) <= 0 THEN 'roboczy'
                WHEN COALESCE(official_version_number, 0) <= 0 THEN 'do_akceptacji'
                WHEN COALESCE(official_version_number, 0) < COALESCE(current_version_number, 0) THEN 'do_sprawdzenia'
                ELSE 'obowiazujacy'
            END
            WHERE business_status IS NULL OR TRIM(COALESCE(business_status, '')) = ''
            """
        )
    if "business_status_before_archive" in knowledge_columns:
        connection.execute(
            """
            UPDATE knowledge_documents
            SET business_status_before_archive = NULL
            WHERE TRIM(COALESCE(business_status_before_archive, '')) = ''
            """
        )
    if "lifecycle_status" in knowledge_columns:
        connection.execute(
            """
            UPDATE knowledge_documents
            SET lifecycle_status = 'active'
            WHERE lifecycle_status IS NULL OR TRIM(COALESCE(lifecycle_status, '')) = ''
            """
        )
    if "duplicate_status" in knowledge_columns:
        connection.execute(
            """
            UPDATE knowledge_documents
            SET duplicate_status = 'none'
            WHERE duplicate_status IS NULL OR TRIM(COALESCE(duplicate_status, '')) = ''
            """
        )
    if "duplicate_score" in knowledge_columns:
        connection.execute(
            """
            UPDATE knowledge_documents
            SET duplicate_score = 0
            WHERE duplicate_score IS NULL
            """
        )
    if "business_status" in knowledge_columns and "business_status_before_archive" in knowledge_columns:
        connection.execute(
            """
            UPDATE knowledge_documents
            SET business_status_before_archive = CASE
                    WHEN TRIM(COALESCE(business_status_before_archive, '')) <> '' THEN business_status_before_archive
                    WHEN business_status = 'archiwalny' THEN 'obowiazujacy'
                    ELSE business_status_before_archive
                END,
                business_status = 'archiwalny'
            WHERE COALESCE(lifecycle_status, 'active') = 'archived'
              AND COALESCE(business_status, '') <> 'archiwalny'
            """
        )


def _ensure_knowledge_version_defaults(connection: DatabaseConnection) -> None:
    rows = connection.execute(
        """
        SELECT *
        FROM knowledge_documents
        WHERE processing_status = 'ready'
          AND current_version_number >= 1
          AND knowledge_document_id NOT IN (
              SELECT knowledge_document_id
              FROM knowledge_document_versions
          )
        """
    ).fetchall()
    for row in rows:
        connection.execute(
            """
            INSERT INTO knowledge_document_versions (
                knowledge_document_id,
                organization_id,
                version_number,
                title,
                file_name,
                mime_type,
                file_link,
                file_storage_key,
                content_text,
                content_hash,
                char_count,
                source_type,
                created_by_user_id,
                extraction_method,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["knowledge_document_id"],
                row["organization_id"],
                int(row["current_version_number"] or 1),
                row["title"],
                row["file_name"],
                row["mime_type"],
                row["file_link"],
                row["file_storage_key"],
                row["content_text"],
                row["content_hash"],
                int(row["char_count"] or 0),
                row["source_type"] or "manual",
                row["created_by_user_id"],
                "legacy",
                row["updated_at"] or now_iso(),
            ),
        )


def _sqlite_table_sql(connection: DatabaseConnection, table_name: str) -> str:
    row = connection.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        """,
        (table_name,),
    ).fetchone()
    return str(row["sql"] or "") if row else ""


def _ensure_sqlite_multi_org_contractors(connection: DatabaseConnection) -> None:
    if connection.backend != "sqlite":
        return

    contractors_sql = _sqlite_table_sql(connection, "contractors").upper()
    if "NIP TEXT NOT NULL UNIQUE" not in contractors_sql:
        return

    connection.raw_connection.executescript(
        """
        PRAGMA foreign_keys = OFF;

        CREATE TABLE contractors__migracja (
            contractor_id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_id INTEGER,
            name TEXT NOT NULL,
            nip TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            is_new INTEGER NOT NULL DEFAULT 1,
            last_invoice_date TEXT,
            last_invoice_number TEXT,
            invoice_count INTEGER NOT NULL DEFAULT 0,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
        );

        INSERT INTO contractors__migracja (
            contractor_id, organization_id, name, nip, email, phone, is_new, last_invoice_date,
            last_invoice_number, invoice_count, notes, created_at, updated_at
        )
        SELECT
            contractor_id, organization_id, name, nip, email, phone, is_new, last_invoice_date,
            last_invoice_number, invoice_count, notes, created_at, updated_at
        FROM contractors;

        DROP TABLE contractors;
        ALTER TABLE contractors__migracja RENAME TO contractors;
        CREATE UNIQUE INDEX IF NOT EXISTS idx_contractors_org_nip ON contractors(organization_id, nip);

        PRAGMA foreign_keys = ON;
        """
    )


def _apply_database_schema_bootstrap(connection: DatabaseConnection) -> None:
    _run_schema_script(
        connection,
        SQLITE_SCHEMA if connection.backend == "sqlite" else POSTGRES_SCHEMA,
    )
    _ensure_user_capabilities_schema(connection)
    _ensure_organization_memberships_schema(connection)
    _ensure_organization_modules_schema(connection)
    _ensure_email_import_history_schema(connection)
    _ensure_ksef_import_history_schema(connection)
    _ensure_invoice_ksef_override_schema(connection)
    _ensure_whiteboard_schema(connection)
    _ensure_knowledge_pipeline_schema(connection)
    _ensure_knowledge_watch_schema(connection)
    _ensure_knowledge_comment_schema(connection)
    _ensure_google_calendar_schema(connection)
    _ensure_invoice_comment_schema(connection)
    _ensure_contractor_note_schema(connection)
    _ensure_module_inbox_schema(connection)
    _ensure_system_email_oauth_schema(connection)
    _ensure_system_settings_schema(connection)
    _ensure_invoice_handoff_schema(connection)
    _ensure_additive_columns(connection)
    _ensure_sqlite_multi_org_contractors(connection)
    _ensure_additive_indexes(connection)
    _migrate_legacy_user_roles(connection)
    _ensure_task_visibility_defaults(connection)
    _ensure_user_knowledge_defaults(connection)
    _ensure_user_capability_defaults(connection)
    _ensure_organization_membership_defaults(connection)
    _ensure_user_telegram_reminder_defaults(connection)
    _ensure_user_calendar_defaults(connection)
    _ensure_google_calendar_connection_defaults(connection)
    _ensure_google_oauth_state_cleanup(connection)
    _ensure_system_email_oauth_state_cleanup(connection)
    _ensure_knowledge_document_defaults(connection)
    _ensure_knowledge_version_defaults(connection)


def initialize_database() -> None:
    max_retries = max(1, int(os.getenv("INVOICE_DB_INIT_MAX_RETRIES", "6")))
    retry_sleep_seconds = max(1, int(os.getenv("INVOICE_DB_INIT_RETRY_SLEEP_SECONDS", "2")))
    for attempt in range(1, max_retries + 1):
        connection = _open_connection()
        try:
            _terminate_stale_init_sessions(connection)
            _apply_database_schema_bootstrap(connection)
            connection.commit()
            return
        except Exception as error:
            try:
                connection.rollback()
            except Exception:
                pass
            if attempt >= max_retries or not _is_retryable_init_error(error):
                raise
            time.sleep(retry_sleep_seconds)
        finally:
            connection.close()


def reset_database() -> None:
    max_retries = max(1, int(os.getenv("INVOICE_DB_INIT_MAX_RETRIES", "6")))
    retry_sleep_seconds = max(1, int(os.getenv("INVOICE_DB_INIT_RETRY_SLEEP_SECONDS", "2")))
    for attempt in range(1, max_retries + 1):
        connection = _open_connection()
        try:
            _terminate_stale_init_sessions(connection)
            _terminate_reset_blocking_sessions(connection)
            _run_schema_script(
                connection,
                SQLITE_RESET_SCRIPT if connection.backend == "sqlite" else POSTGRES_RESET_SCRIPT,
            )
            _apply_database_schema_bootstrap(connection)
            connection.commit()
            return
        except Exception as error:
            try:
                connection.rollback()
            except Exception:
                pass
            if attempt >= max_retries or not _is_retryable_init_error(error):
                raise
            time.sleep(retry_sleep_seconds)
        finally:
            connection.close()


@contextmanager
def get_connection():
    connection = _open_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def execute_insert_returning_id(
    connection: DatabaseConnection,
    query: str,
    params: Iterable[Any],
    id_column: str,
) -> int:
    if connection.backend == "sqlite":
        cursor = connection.execute(query, params)
        return int(cursor.lastrowid)
    cursor = connection.execute(f"{query.rstrip().rstrip(';')} RETURNING {id_column}", params)
    row = cursor.fetchone()
    return int(row[id_column])
