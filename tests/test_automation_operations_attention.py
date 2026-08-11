from __future__ import annotations

import unittest

from app.services.automation_operations_service import (
    AUTOMATION_ENGINE_KEY,
    EMAIL_IMPORT_KEY,
    INTERNAL_NOTIFICATION_SCHEDULER_KEY,
    KNOWLEDGE_PROCESSING_KEY,
    KSEF_IMPORT_KEY,
    TASK_REMINDERS_KEY,
    AutomationOperationsRegistry,
    AutomationOperationsService,
    build_attention_items,
)


def operation(
    automation_key: str,
    reason_code: str,
    *,
    title: str | None = None,
    health: str = "attention",
    status: str = "enabled",
    occurred_at: str | None = "2026-06-01T10:00:00+00:00",
    settings_url: str | None = None,
) -> dict[str, object]:
    return {
        "automation_key": automation_key,
        "automation_type": automation_key,
        "title": title or f"Tytuł {automation_key}",
        "description": "Opis",
        "status": status,
        "enabled": status == "enabled",
        "health": health,
        "health_reason_code": reason_code,
        "organization_provider_supported": True,
        "next_run_at": None,
        "last_run_at": occurred_at,
        "last_run_status": "failed" if health == "attention" else None,
        "last_failure_at": occurred_at,
        "last_attempt_at": occurred_at,
        "last_scan_at": occurred_at,
        "recent_failure_count": 1 if health == "attention" else 0,
        "settings_url": settings_url,
        "details_url": f"/automatyzacje/{automation_key}",
        "updated_at": occurred_at,
        # Deliberately sensitive-looking fields prove that attention ignores source text.
        "last_error_summary": "subject private@example.invalid NIP 123 payload token stack trace",
        "task_title": "Poufne zadanie klienta",
        "input_json": '{"secret":"value"}',
    }


class AutomationAttentionModelTests(unittest.TestCase):
    def test_healthy_disabled_never_run_runtime_unknown_and_no_work_are_not_attention(self) -> None:
        cases = (
            operation(INTERNAL_NOTIFICATION_SCHEDULER_KEY, "last_run_succeeded", health="healthy"),
            operation(INTERNAL_NOTIFICATION_SCHEDULER_KEY, "schedule_disabled", health="disabled", status="disabled"),
            operation(KNOWLEDGE_PROCESSING_KEY, "no_terminal_job", health="never_run"),
            operation(EMAIL_IMPORT_KEY, "last_email_import_run_succeeded", health="healthy"),
            operation(KSEF_IMPORT_KEY, "ksef_import_disabled", health="disabled", status="disabled"),
            operation(AUTOMATION_ENGINE_KEY, "no_enabled_rules", health="disabled", status="disabled"),
        )
        for case in cases:
            case["runtime_status"] = "unknown"
            with self.subTest(reason=case["health_reason_code"]):
                self.assertEqual(build_attention_items([case]), [])

    def test_execution_rules_for_all_relevant_adapters_are_controlled_and_sanitized(self) -> None:
        cases = (
            (INTERNAL_NOTIFICATION_SCHEDULER_KEY, "last_run_failed"),
            (TASK_REMINDERS_KEY, "last_attempt_failed"),
            (KNOWLEDGE_PROCESSING_KEY, "last_job_failed"),
            (KNOWLEDGE_PROCESSING_KEY, "last_folder_scan_failed"),
            (EMAIL_IMPORT_KEY, "last_email_import_run_requires_attention"),
            (KSEF_IMPORT_KEY, "last_ksef_import_run_requires_attention"),
            (AUTOMATION_ENGINE_KEY, "last_execution_failed"),
        )
        for automation_key, reason_code in cases:
            with self.subTest(automation_key=automation_key, reason_code=reason_code):
                item = build_attention_items([operation(automation_key, reason_code)])[0]
                self.assertEqual(item["attention_category"], "execution")
                self.assertEqual(item["reason_code"], reason_code)
                self.assertEqual(item["details_url"], f"/automatyzacje/{automation_key}")
                serialized = str(item).lower()
                for forbidden in ("subject", "private@", "nip 123", "poufne zadanie", "payload", "token", "stack trace", "secret"):
                    self.assertNotIn(forbidden, serialized)

    def test_configuration_attention_requires_an_explicit_supported_contract(self) -> None:
        explicit = (
            operation(TASK_REMINDERS_KEY, "telegram_not_configured", health="disabled", status="disabled"),
            operation(EMAIL_IMPORT_KEY, "system_mailbox_not_configured", health="disabled", status="not_configured", settings_url="/ustawienia"),
            operation(KSEF_IMPORT_KEY, "organization_ksef_not_configured", health="disabled", status="not_configured", settings_url="/ustawienia"),
        )
        self.assertTrue(all(build_attention_items([item])[0]["attention_category"] == "configuration" for item in explicit))
        ambiguous = (
            operation(TASK_REMINDERS_KEY, "runtime_disabled", health="disabled", status="disabled"),
            operation(TASK_REMINDERS_KEY, "organization_provider_not_supported", health="disabled", status="disabled"),
            operation(EMAIL_IMPORT_KEY, "organization_email_not_configured", health="disabled", status="not_configured"),
            operation(KSEF_IMPORT_KEY, "ksef_import_disabled", health="disabled", status="disabled"),
            operation(INTERNAL_NOTIFICATION_SCHEDULER_KEY, "schedule_not_configured", health="disabled", status="not_configured"),
        )
        self.assertTrue(all(build_attention_items([item]) == [] for item in ambiguous))
        unsupported = operation(TASK_REMINDERS_KEY, "telegram_not_configured", health="disabled", status="disabled")
        unsupported["organization_provider_supported"] = False
        self.assertEqual(build_attention_items([unsupported]), [])

    def test_failed_outbox_is_the_only_backlog_contract(self) -> None:
        item = build_attention_items([operation(TASK_REMINDERS_KEY, "failed_outbox_present")])[0]
        self.assertEqual(item["attention_category"], "backlog")
        self.assertIn("przypomnienie", item["summary"].lower())
        self.assertEqual(build_attention_items([operation(TASK_REMINDERS_KEY, "no_delivery_attempt", health="never_run")]), [])

    def test_sorting_uses_timestamp_then_registry_and_nulls_are_last(self) -> None:
        first = operation(INTERNAL_NOTIFICATION_SCHEDULER_KEY, "last_run_failed", occurred_at="2026-06-01T10:00:00+00:00")
        tied = operation(KNOWLEDGE_PROCESSING_KEY, "last_job_failed", occurred_at="2026-06-01T10:00:00+00:00")
        newest = operation(AUTOMATION_ENGINE_KEY, "last_execution_failed", occurred_at="2026-06-02T10:00:00+00:00")
        missing = operation(KSEF_IMPORT_KEY, "organization_ksef_not_configured", health="disabled", status="not_configured", occurred_at=None)
        invalid = operation(EMAIL_IMPORT_KEY, "last_email_import_run_requires_attention", occurred_at="not-a-time")
        items = build_attention_items([first, tied, missing, newest, invalid])
        self.assertEqual([item["automation_key"] for item in items], [AUTOMATION_ENGINE_KEY, INTERNAL_NOTIFICATION_SCHEDULER_KEY, KNOWLEDGE_PROCESSING_KEY, KSEF_IMPORT_KEY, EMAIL_IMPORT_KEY])
        self.assertIsNone(items[-1]["occurred_at"])
        self.assertIsNone(items[-2]["occurred_at"])

    def test_title_links_and_settings_come_only_from_the_canonical_operation(self) -> None:
        item = build_attention_items([
            operation(EMAIL_IMPORT_KEY, "system_mailbox_not_configured", title="Import e-maili", health="disabled", status="not_configured", occurred_at=None, settings_url="/ustawienia")
        ])[0]
        self.assertEqual(item["title"], "Import e-maili")
        self.assertEqual(item["settings_url"], "/ustawienia")
        self.assertEqual(item["details_url"], "/automatyzacje/email_import")
        self.assertIsNone(item["occurred_at"])

    def test_maximum_one_item_per_adapter(self) -> None:
        items = build_attention_items([
            operation(TASK_REMINDERS_KEY, "failed_outbox_present"),
            operation(TASK_REMINDERS_KEY, "last_attempt_failed", occurred_at="2026-06-02T10:00:00+00:00"),
        ])
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["reason_code"], "failed_outbox_present")

    def test_dashboard_calls_each_adapter_once_and_attention_is_an_in_memory_projection(self) -> None:
        keys_and_reasons = (
            (INTERNAL_NOTIFICATION_SCHEDULER_KEY, "last_run_failed"),
            (TASK_REMINDERS_KEY, "failed_outbox_present"),
            (KNOWLEDGE_PROCESSING_KEY, "last_job_failed"),
            (EMAIL_IMPORT_KEY, "last_email_import_run_requires_attention"),
            (KSEF_IMPORT_KEY, "last_ksef_import_run_requires_attention"),
            (AUTOMATION_ENGINE_KEY, "last_execution_failed"),
        )

        class Adapter:
            scope = "organization"
            capabilities = frozenset({"summary", "history"})

            def __init__(self, key: str, reason: str) -> None:
                self.automation_key = key
                self.reason = reason
                self.calls = 0

            def get_operation(self, *, organization_id: int, recipient_user_id: int) -> dict[str, object]:
                self.calls += 1
                return operation(self.automation_key, self.reason)

            def get_history(self, *, organization_id: int, recipient_user_id: int, limit: int) -> list[dict[str, object]]:
                return []

        class Scope:
            def validate_recipient_scope(self, **kwargs: object) -> None:
                return None

        adapters = tuple(Adapter(key, reason) for key, reason in keys_and_reasons)
        service = AutomationOperationsService(
            registry=AutomationOperationsRegistry(adapters),
            notification_service=Scope(),  # type: ignore[arg-type]
        )
        dashboard = service.dashboard(organization_id=1, recipient_user_id=2, actor_user={})
        self.assertEqual(len(dashboard["items"]), 6)
        self.assertEqual(len(dashboard["attention_items"]), 6)
        self.assertTrue(all(adapter.calls == 1 for adapter in adapters))


if __name__ == "__main__":
    unittest.main()
