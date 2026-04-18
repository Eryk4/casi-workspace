SOURCES = ("KSeF", "EMAIL", "TELEGRAM", "SLACK")

INVOICE_STATUSES = (
    "nowa",
    "weryfikacja",
    "poprawna",
    "podejrzenie_duplikatu",
    "pewny_duplikat",
    "odrzucona",
    "zaksiegowana",
)

DUPLICATE_TYPES = ("brak", "podejrzenie", "pewny")

INVOICE_VERIFICATION_BUCKET_ORDER = (
    "verification",
    "duplicates",
    "ksef_corrections",
    "ocr_attention",
)

INVOICE_WORKFLOW_STATES = (
    "w_pracy",
    "gotowa_do_przekazania",
    "przekazana",
    "zamknieta",
)

INVOICE_SLA_THRESHOLDS_DAYS = {
    "verification": 2,
    "duplicates": 1,
    "ksef_corrections": 1,
    "ocr_attention": 1,
}

INVOICE_WORKFLOW_SLA_THRESHOLDS_DAYS = {
    "ready_for_handoff": 1,
}

EVENT_TYPES = (
    "invoice_created",
    "invoice_updated",
    "invoice_status_changed",
    "invoice_assigned",
    "invoice_reassigned",
    "invoice_unassigned",
    "invoice_comment_added",
    "invoice_ready_for_handoff",
    "invoice_handed_off",
    "invoice_closed",
    "invoice_reopened",
    "invoice_handoff_batch_created",
    "invoice_handoff_batch_exported",
    "duplicate_detected",
    "duplicate_rejected",
    "duplicate_confirmed",
    "email_connection_tested",
    "email_connection_test_failed",
    "email_check_executed",
    "email_check_failed",
    "contractor_created",
    "telegram_notification_prepared",
    "mock_import_executed",
    "user_created",
    "user_updated",
    "user_login",
    "user_logout",
    "organization_created",
    "organization_updated",
    "whiteboard_updated",
    "whiteboard_cleared",
    "whiteboard_image_added",
    "whiteboard_image_transformed",
    "task_created",
    "task_updated",
    "task_note_added",
    "task_comment_added",
    "task_comment_mentioned",
    "task_checklist_item_added",
    "task_checklist_item_toggled",
    "task_template_created",
    "task_template_updated",
    "task_template_applied",
    "task_reminder_sent",
    "task_reminder_failed",
    "intake_form_created",
    "intake_form_updated",
    "intake_form_archived",
    "intake_item_created",
    "intake_item_updated",
    "intake_comment_added",
    "intake_attachment_added",
    "saved_view_created",
    "saved_view_updated",
    "saved_view_deleted",
    "automation_rule_created",
    "automation_rule_updated",
    "automation_rule_executed",
    "automation_rule_failed",
    "automation_rule_disabled",
    "approval_requested",
    "approval_approved",
    "approval_rejected",
    "approval_cancelled",
    "approval_attachment_added",
    "google_calendar_connection_pending",
    "google_calendar_connection_approved",
    "google_calendar_connection_rejected",
    "google_calendar_disconnected",
    "user_calendar_created",
    "user_calendar_updated",
    "user_calendar_deleted",
    "organization_calendar_assigned",
    "organization_calendar_assignment_removed",
    "user_reminder_preferences_updated",
    "knowledge_document_created",
    "knowledge_document_updated",
    "knowledge_document_downloaded",
    "knowledge_document_archived",
    "knowledge_document_deleted",
    "knowledge_document_restored",
    "knowledge_document_version_restored",
    "knowledge_document_replaced",
    "knowledge_sync_executed",
    "knowledge_watch_scan",
    "billing_model_created",
    "billing_payer_created",
    "billing_student_created",
    "billing_school_created",
    "billing_bank_account_created",
    "billing_charge_batch_generated",
    "billing_statement_imported",
    "billing_ledger_charge_recorded",
    "billing_payment_matched",
)

SYSTEM_OWNER_ROLE = "system_owner"
ORGANIZATION_ADMIN_ROLE = "organization_admin"
COORDINATOR_ROLE = "coordinator"
OPERATOR_ROLE = "operator"
GUEST_ROLE = "guest"

USER_ROLES = (
    SYSTEM_OWNER_ROLE,
    ORGANIZATION_ADMIN_ROLE,
    COORDINATOR_ROLE,
    OPERATOR_ROLE,
    GUEST_ROLE,
)

READ_ROLES = USER_ROLES
WRITE_ROLES = (
    SYSTEM_OWNER_ROLE,
    ORGANIZATION_ADMIN_ROLE,
    COORDINATOR_ROLE,
    OPERATOR_ROLE,
)
USER_MANAGEMENT_ROLES = (
    SYSTEM_OWNER_ROLE,
    ORGANIZATION_ADMIN_ROLE,
)
ORGANIZATION_SETTINGS_ROLES = (
    SYSTEM_OWNER_ROLE,
    ORGANIZATION_ADMIN_ROLE,
)
ORGANIZATION_MANAGEMENT_ROLES = (SYSTEM_OWNER_ROLE,)
INVOICE_DECISION_ROLES = (
    SYSTEM_OWNER_ROLE,
    ORGANIZATION_ADMIN_ROLE,
    COORDINATOR_ROLE,
)
MANAGER_ASSISTANT_MODULE = "manager_assistant"
ORGANIZATION_MODULE_CODES = (MANAGER_ASSISTANT_MODULE,)
MANAGER_ASSISTANT_MANAGER_ROLES = (
    SYSTEM_OWNER_ROLE,
    ORGANIZATION_ADMIN_ROLE,
    COORDINATOR_ROLE,
)
MANAGER_ASSISTANT_WORKSPACE_ROLES = (
    SYSTEM_OWNER_ROLE,
    ORGANIZATION_ADMIN_ROLE,
    COORDINATOR_ROLE,
    OPERATOR_ROLE,
)
TASK_ASSIGNMENT_ROLES = (
    SYSTEM_OWNER_ROLE,
    ORGANIZATION_ADMIN_ROLE,
    COORDINATOR_ROLE,
    OPERATOR_ROLE,
)
KNOWLEDGE_UPLOAD_DEFAULT_ROLES = WRITE_ROLES

KNOWLEDGE_READ_CAPABILITY = "knowledge.read"
KNOWLEDGE_DOWNLOAD_CAPABILITY = "knowledge.download"
KNOWLEDGE_UPLOAD_CAPABILITY = "knowledge.upload"
KNOWLEDGE_SYNC_CAPABILITY = "knowledge.sync"
KNOWLEDGE_MANAGE_CAPABILITY = "knowledge.manage"
KNOWLEDGE_ASSISTANT_USE_CAPABILITY = "knowledge.assistant_use"

KNOWLEDGE_CAPABILITIES = (
    KNOWLEDGE_READ_CAPABILITY,
    KNOWLEDGE_DOWNLOAD_CAPABILITY,
    KNOWLEDGE_UPLOAD_CAPABILITY,
    KNOWLEDGE_SYNC_CAPABILITY,
    KNOWLEDGE_MANAGE_CAPABILITY,
    KNOWLEDGE_ASSISTANT_USE_CAPABILITY,
)

ROLE_DEFAULT_CAPABILITIES = {
    SYSTEM_OWNER_ROLE: KNOWLEDGE_CAPABILITIES,
    ORGANIZATION_ADMIN_ROLE: KNOWLEDGE_CAPABILITIES,
    COORDINATOR_ROLE: (
        KNOWLEDGE_READ_CAPABILITY,
        KNOWLEDGE_DOWNLOAD_CAPABILITY,
        KNOWLEDGE_UPLOAD_CAPABILITY,
        KNOWLEDGE_SYNC_CAPABILITY,
        KNOWLEDGE_MANAGE_CAPABILITY,
        KNOWLEDGE_ASSISTANT_USE_CAPABILITY,
    ),
    OPERATOR_ROLE: (
        KNOWLEDGE_READ_CAPABILITY,
        KNOWLEDGE_DOWNLOAD_CAPABILITY,
        KNOWLEDGE_UPLOAD_CAPABILITY,
        KNOWLEDGE_SYNC_CAPABILITY,
        KNOWLEDGE_ASSISTANT_USE_CAPABILITY,
    ),
    GUEST_ROLE: (
        KNOWLEDGE_READ_CAPABILITY,
        KNOWLEDGE_DOWNLOAD_CAPABILITY,
    ),
}

KNOWLEDGE_DOCUMENT_STATUSES = ("queued", "processing", "ready", "error")
KNOWLEDGE_JOB_STATUSES = ("pending", "processing", "completed", "failed")
KNOWLEDGE_JOB_TYPES = ("ingest", "reprocess", "replace", "restore_version")
KNOWLEDGE_LIFECYCLE_STATUSES = ("active", "archived", "deleted")
KNOWLEDGE_DUPLICATE_STATUSES = ("none", "exact_duplicate", "similar_version")


def default_capabilities_for_role(role: str) -> tuple[str, ...]:
    return tuple(ROLE_DEFAULT_CAPABILITIES.get(role, (KNOWLEDGE_READ_CAPABILITY,)))

TASK_TYPES = ("zadanie", "wydarzenie", "przypomnienie", "notatka")

TASK_STATUSES = ("nowe", "w_toku", "oczekuje", "zakonczone", "anulowane")

TASK_PRIORITIES = ("niski", "normalny", "wysoki", "krytyczny")

TASK_VISIBILITY_SCOPES = ("prywatne", "wybrane_osoby", "organizacja")

TASK_RECURRENCE_PATTERNS = ("brak", "codziennie", "co_tydzien", "dni_robocze", "co_miesiac")

TASK_RECURRENCE_EDIT_SCOPES = (
    "tylko_ten",
    "ten_i_nastepne",
    "cala_seria",
)

TASK_NOTE_KINDS = (
    "comment",
    "reply",
    "decision",
)

APPROVAL_STATUSES = (
    "pending",
    "approved",
    "rejected",
    "cancelled",
)

APPROVAL_ENTITY_TYPES = (
    "task",
    "invoice",
    "billing_charge",
    "knowledge_document",
    "decision",
)

TASK_FOCUS_VIEWS = (
    "moj_dzien",
    "do_decyzji",
    "przypisane_do_mnie",
    "po_terminie",
    "czeka_na_kogos",
    "prywatne",
    "organizacyjne",
)

TASK_FOCUS_VIEW_LABELS = {
    "moj_dzien": "Moj dzien",
    "do_decyzji": "Do decyzji",
    "przypisane_do_mnie": "Przypisane do mnie",
    "po_terminie": "Po terminie",
    "czeka_na_kogos": "Czeka na kogos",
    "prywatne": "Prywatne",
    "organizacyjne": "Organizacyjne",
}

MANAGER_TASK_FOCUS_VIEWS = (
    "moj_dzien",
    "do_decyzji",
    "po_terminie",
    "czeka_na_kogos",
    "organizacyjne",
    "prywatne",
)

WORKER_TASK_FOCUS_VIEWS = (
    "moj_dzien",
    "przypisane_do_mnie",
    "po_terminie",
    "czeka_na_kogos",
    "organizacyjne",
    "prywatne",
)

CALENDAR_KINDS = ("organizacja", "rodzinny", "prywatny", "inne")

OWNER_CALENDAR_KINDS = CALENDAR_KINDS
WORKER_CALENDAR_KINDS = ("inne",)

CALENDAR_KIND_LABELS = {
    "organizacja": "Organizacja",
    "rodzinny": "Rodzinny",
    "prywatny": "Prywatny",
    "inne": "Sluzbowy osobisty",
}

BILLING_STATEMENT_IMPORT_STATUSES = ("przetwarzany", "zaimportowany", "blad")

BILLING_TRANSACTION_MATCH_STATUSES = ("nieprzypisana", "czesciowo_rozliczona", "rozliczona")
