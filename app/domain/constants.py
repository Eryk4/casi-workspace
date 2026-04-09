SOURCES = ("KSeF", "EMAIL", "TELEGRAM")

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

EVENT_TYPES = (
    "invoice_created",
    "invoice_updated",
    "invoice_status_changed",
    "duplicate_detected",
    "duplicate_rejected",
    "duplicate_confirmed",
    "contractor_created",
    "telegram_notification_prepared",
    "mock_import_executed",
    "user_created",
    "user_updated",
    "user_login",
    "user_logout",
    "organization_created",
    "organization_updated",
)

USER_ROLES = ("administrator", "operator", "podglad")
