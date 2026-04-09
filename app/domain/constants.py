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
    "task_created",
    "task_updated",
    "task_note_added",
)

USER_ROLES = ("administrator", "operator", "podglad")

TASK_TYPES = ("zadanie", "wydarzenie", "przypomnienie")

TASK_STATUSES = ("nowe", "w_toku", "oczekuje", "zakonczone", "anulowane")

TASK_PRIORITIES = ("niski", "normalny", "wysoki", "krytyczny")
