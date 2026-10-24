from __future__ import annotations

import json
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

from app.data_migration_manifest import MIGRATION_MANIFEST
from app.db import get_connection
from app.domain.constants import USER_ROLES
from app.repositories.automation_repository import AutomationRepository
from app.services.automation_rule_definition import (
    AutomationRuleValidationError,
    get_automation_rule_catalog,
    normalize_active_flag,
    validate_execution_rule_definition,
    validate_management_rule_definition,
    validate_rule_metadata,
    validate_rule_payload_keys,
)
from app.services.automation_service import AutomationService
from tests.http_server_support import HttpServerTestCase


CATALOG_TRIGGER_KEYS = {"invoice_status_changed", "work_item_created", "work_item_updated"}
READ_ALLOWED = {"system_owner", "organization_admin", "coordinator"}
MANAGE_ALLOWED = {"system_owner", "organization_admin"}


def valid_action(title: str = "Sprawdź sprawę") -> dict[str, str]:
    return {"type": "create_inbox_item", "title": title, "description": "Opis literalny"}


class AutomationRuleCatalogTests(unittest.TestCase):
    def test_catalog_is_deterministic_private_and_consistent_with_management_validator(self) -> None:
        first = get_automation_rule_catalog()
        second = get_automation_rule_catalog()
        self.assertEqual(first, second)
        self.assertEqual(first["version"], 1)
        self.assertEqual({item["key"] for item in first["triggers"]}, CATALOG_TRIGGER_KEYS)
        self.assertEqual([item["key"] for item in first["actions"]], ["create_inbox_item"])
        self.assertNotIn("log", {item["key"] for item in first["actions"]})
        self.assertEqual(first["constraints"], {"min_actions": 1, "max_actions": 1, "max_conditions": 3})
        serialized = json.dumps(first).lower()
        for forbidden in (
            "details_contains",
            "decision_reason_contains",
            "requester_email",
            "requester_name",
            "source_reference",
            "nip",
            "token",
            "document_path",
        ):
            self.assertNotIn(forbidden, serialized)

        for trigger in first["triggers"]:
            conditions = {field["key"]: "synthetic" for field in trigger["condition_fields"]}
            definition = validate_management_rule_definition(
                trigger["key"],
                conditions,
                [valid_action()],
            )
            self.assertEqual(definition.trigger_event_type, trigger["key"])

    def test_management_validator_accepts_minimal_definition_and_rejects_invalid_shapes(self) -> None:
        valid = validate_management_rule_definition(
            "work_item_created",
            {},
            [{"type": "create_inbox_item", "title": "Nowa sprawa"}],
        )
        self.assertEqual(valid.conditions, {})
        self.assertEqual(valid.actions[0]["description"], "")

        invalid_cases = (
            ("", {}, [valid_action()]),
            ("unknown_event", {}, [valid_action()]),
            (123, {}, [valid_action()]),
            ("work_item_created", [], [valid_action()]),
            ("work_item_created", "[]", [valid_action()]),
            ("work_item_created", "{", [valid_action()]),
            ("work_item_created", {"unknown": "x"}, [valid_action()]),
            ("work_item_created", {"details_contains": "x"}, [valid_action()]),
            ("work_item_created", {"status_after": 7}, [valid_action()]),
            ("work_item_created", {}, []),
            ("work_item_created", {}, [valid_action(), valid_action("Druga")]),
            ("work_item_created", {}, [{"type": "unknown"}]),
            ("work_item_created", {}, [{"type": "log", "message": "x"}]),
            ("work_item_created", {}, [{}]),
            ("work_item_created", {}, ["create_inbox_item"]),
            ("work_item_created", {}, [{"type": "create_inbox_item"}]),
            ("work_item_created", {}, [{"type": "create_inbox_item", "title": "x", "token": "secret"}]),
            ("work_item_created", {}, [{"type": "create_inbox_item", "title": 7}]),
            ("work_item_created", {}, [{"type": "create_inbox_item", "title": "x" * 201}]),
            ("work_item_created", {}, "["),
        )
        for trigger, conditions, actions in invalid_cases:
            with self.subTest(trigger=trigger, conditions=conditions, actions=actions):
                with self.assertRaises(AutomationRuleValidationError):
                    validate_management_rule_definition(trigger, conditions, actions)

        accepted = validate_management_rule_definition(
            "invoice_status_changed",
            {"source": "email", "status_before": "nowa", "status_after": "weryfikacja"},
            [valid_action()],
        )
        self.assertEqual(len(accepted.conditions), 3)

    def test_execution_validator_preserves_safe_legacy_contract(self) -> None:
        definition = validate_execution_rule_definition(
            "synthetic.legacy",
            {"details_contains": "needle", "decision_reason_contains": "reason"},
            [{"type": "log", "message": "legacy"}, {"type": "log", "message": "second"}],
        )
        self.assertEqual(len(definition.actions), 2)
        self.assertEqual(definition.actions[0]["type"], "log")

        invalid_cases = (
            ([], [{"type": "log"}]),
            ("[]", [{"type": "log"}]),
            ("{", [{"type": "log"}]),
            ({"unknown": "x"}, [{"type": "log"}]),
            ({"source": 1}, [{"type": "log"}]),
            ({}, [{"type": "unknown"}]),
            ({}, [{"type": "log", "message": [], "extra": "x"}]),
            ({}, "["),
        )
        for conditions, actions in invalid_cases:
            with self.subTest(conditions=conditions, actions=actions):
                with self.assertRaises(AutomationRuleValidationError):
                    validate_execution_rule_definition("synthetic.legacy", conditions, actions)

    def test_metadata_payload_fields_and_active_flag_fail_closed(self) -> None:
        self.assertEqual(
            validate_rule_metadata({"rule_name": "Rule", "description": "Description"}, partial=False),
            {"rule_name": "Rule", "description": "Description"},
        )
        for payload in (
            {"rule_name": 7},
            {"rule_name": "x" * 161},
            {"rule_name": "Rule", "description": []},
            {"rule_name": "Rule", "description": "x" * 1001},
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(AutomationRuleValidationError):
                    validate_rule_metadata(payload, partial=False)
        with self.assertRaises(AutomationRuleValidationError):
            validate_rule_payload_keys({"rule_name": "Rule", "unknown": True}, partial=True)
        for value in (None, 1.0, [], "yes"):
            with self.subTest(value=value):
                with self.assertRaises(AutomationRuleValidationError):
                    normalize_active_flag(value)


class AutomationExecutionSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = Mock()
        self.repository.acquire_rule_claim.return_value = True
        self.repository.renew_rule_claim.return_value = True
        self.repository.try_claim_execution.return_value = {
            "claimed": True,
            "reason": "claimed",
            "automation_execution_id": 101,
        }
        self.repository.complete_execution.return_value = True
        self.repository.update_rule_progress.return_value = True
        self.repository.release_rule_claim.return_value = True
        self.events = Mock()
        self.service = AutomationService(self.repository, self.events)
        self.base_rule = {
            "automation_rule_id": 1,
            "organization_id": 7,
            "rule_slug": "legacy",
            "rule_name": "Legacy",
            "trigger_event_type": "synthetic.legacy",
            "conditions_json": "{}",
            "actions_json": '[{"type":"log","message":"safe"}]',
            "last_processed_event_log_id": 0,
            "execution_count": 0,
        }
        self.event = {
            "id": 10,
            "organization_id": 7,
            "event_type": "synthetic.legacy",
            "source": "TEST",
            "status_before": "old",
            "status_after": "new",
            "decision_reason": "reason needle",
            "details": '{"marker":"needle"}',
        }

    def test_unknown_action_and_malformed_conditions_fail_before_event_or_handler(self) -> None:
        cases = (
            {"actions_json": '[{"type":"unknown"}]'},
            {"conditions_json": "[]"},
            {"conditions_json": '"bad"'},
            {"conditions_json": '{"unknown":"x"}'},
            {"conditions_json": '{"source":7}'},
            {"actions_json": '[{"type":"log","message":[],"extra":"x"}]'},
        )
        for changes in cases:
            with self.subTest(changes=changes):
                self.events.reset_mock()
                self.repository.reset_mock()
                rule = dict(self.base_rule, **changes)
                result = self.service._process_rule(rule)
                self.assertEqual(result, {"processed": False, "executions": 0, "errors": 1})
                self.events.list_logs_after.assert_not_called()
                self.repository.try_claim_execution.assert_not_called()
                self.repository.update.assert_not_called()

    def test_manual_invalid_rule_returns_controlled_validation_error(self) -> None:
        rule = dict(self.base_rule, actions_json='[{"type":"unknown"}]')
        with self.assertRaises(AutomationRuleValidationError):
            self.service._process_rule(rule, manual=True)
        self.events.list_logs_after.assert_not_called()

    def test_legacy_log_hidden_condition_and_multi_action_still_execute(self) -> None:
        rule = dict(
            self.base_rule,
            conditions_json='{"details_contains":"needle","decision_reason_contains":"reason"}',
            actions_json='[{"type":"log","message":"one"},{"type":"log","message":"two"}]',
        )
        self.events.list_logs_after.return_value = [self.event]
        result = self.service._process_rule(rule)
        self.assertEqual(result, {"processed": True, "executions": 1, "errors": 0})
        parsed_result = json.loads(self.repository.complete_execution.call_args.kwargs["result_json"])
        self.assertEqual([item["message"] for item in parsed_result["results"]], ["one", "two"])

    def test_valid_create_inbox_action_uses_literal_management_fields(self) -> None:
        intake_service = Mock()
        intake_service.create_item.return_value = {"intake_item_id": 44}
        service = AutomationService(self.repository, self.events, intake_service)
        rule = dict(
            self.base_rule,
            trigger_event_type="work_item_created",
            actions_json=(
                '[{"type":"create_inbox_item","title":"Literal title",'
                '"description":"Literal description"}]'
            ),
        )
        event = dict(self.event, event_type="work_item_created", status_after="nowe")
        self.events.list_logs_after.return_value = [event]
        result = service._process_rule(rule)
        self.assertEqual(result, {"processed": True, "executions": 1, "errors": 0})
        payload = intake_service.create_item.call_args.args[0]
        self.assertEqual(payload["title"], "Literal title")
        self.assertEqual(payload["description"], "Literal description")
        self.assertIsNone(payload["requester_name"])
        self.assertIsNone(payload["requester_email"])

    def test_equals_conditions_are_case_insensitive(self) -> None:
        definition = validate_execution_rule_definition(
            "synthetic.legacy",
            {"source": "test", "status_after": "NEW"},
            [{"type": "log", "message": "safe"}],
        )
        self.assertTrue(self.service._event_matches_conditions(self.event, definition.conditions))


class AutomationRuleDefinitionHttpTests(HttpServerTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.auth_service = self.services["auth_service"]
        self.admin = self.auth_service.list_users()[0]
        suffix = uuid4().hex[:10]
        self.organization = self.services["organization_service"].create_organization(
            {"name": f"Definition A {suffix}", "slug": f"definition-a-{suffix}", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.other_organization = self.services["organization_service"].create_organization(
            {"name": f"Definition B {suffix}", "slug": f"definition-b-{suffix}", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.organization_id = int(self.organization["organization_id"])
        self.other_organization_id = int(self.other_organization["organization_id"])
        self.users = {"system_owner": self.admin}
        for role in USER_ROLES:
            if role == "system_owner":
                continue
            self.users[role] = self.auth_service.create_user(
                {
                    "login": f"definition-{role}-{suffix}",
                    "display_name": role,
                    "password": "Definition123!",
                    "role": role,
                    "organization_id": self.organization_id,
                    "is_active": 1,
                    "capabilities": [],
                },
                actor_login="admin",
                actor_user_id=int(self.admin["user_id"]),
                actor_user=self.admin,
            )
        self.cookies = {
            "system_owner": self._login("admin", "Admin1234"),
            **{
                role: self._login(f"definition-{role}-{suffix}", "Definition123!")
                for role in USER_ROLES
                if role != "system_owner"
            },
        }
        self.repository = AutomationRepository()

    def _scope(self, role: str) -> str:
        return f"?organization_id={self.organization_id}" if role == "system_owner" else ""

    @staticmethod
    def _automation_snapshot() -> dict[str, list[dict[str, object]]]:
        with get_connection() as connection:
            return {
                table: [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()]
                for table in ("automation_rules", "automation_executions", "event_logs")
            }

    @staticmethod
    def _domain_snapshot() -> dict[str, list[dict[str, object]]]:
        with get_connection() as connection:
            return {
                spec.source_table: [
                    dict(row)
                    for row in connection.execute(f'SELECT * FROM "{spec.source_table}" ORDER BY 1').fetchall()
                ]
                for spec in MIGRATION_MANIFEST
                if spec.source_table != "user_sessions"
            }

    def _post_rule(self, payload: dict[str, object], role: str = "organization_admin"):
        return self._request(
            "POST",
            "/api/automation/rules" + self._scope(role),
            body=json.dumps(payload),
            headers={"Cookie": self.cookies[role], "Content-Type": "application/json"},
        )

    def _valid_payload(self, slug: str) -> dict[str, object]:
        return {
            "rule_name": f"Rule {slug}",
            "rule_slug": slug,
            "trigger_event_type": "work_item_created",
            "conditions_json": {"status_after": "nowe"},
            "actions_json": [valid_action()],
        }

    def _create_raw_rule(
        self,
        *,
        slug: str,
        trigger: str = "synthetic.legacy",
        conditions: object = None,
        actions: object = None,
        active: int = 1,
        organization_id: int | None = None,
    ) -> int:
        return self.repository.create(
            {
                "organization_id": organization_id or self.organization_id,
                "rule_slug": slug,
                "rule_name": f"Raw {slug}",
                "description": "legacy",
                "trigger_event_type": trigger,
                "conditions_json": json.dumps({} if conditions is None else conditions),
                "actions_json": json.dumps([{"type": "log", "message": "safe"}] if actions is None else actions),
                "is_active": active,
                "created_by_user_id": int(self.admin["user_id"]),
            }
        )

    def test_catalog_permissions_global_read_only_and_private(self) -> None:
        before = self._domain_snapshot()
        expected = get_automation_rule_catalog()
        self.assertEqual(len(MIGRATION_MANIFEST), 78)
        for role in USER_ROLES:
            with self.subTest(role=role):
                with patch.object(self.services["automation_service"], "list_rules") as list_rules:
                    response, body = self._request(
                        "GET",
                        "/api/automations/catalog",
                        headers={"Cookie": self.cookies[role]},
                    )
                self.assertEqual(response.status, 200 if role in READ_ALLOWED else 403, body.decode())
                list_rules.assert_not_called()
                if response.status == 200:
                    self.assertEqual(json.loads(body), expected)
                    serialized = body.decode().lower()
                    for marker in (
                        "email_fake",
                        "nip_fake",
                        "token_fake",
                        "secret_fake",
                        "document_path_fake",
                        "invoice_data_fake",
                    ):
                        self.assertNotIn(marker, serialized)
        for organization_id in (self.organization_id, self.other_organization_id):
            response, body = self._request(
                "GET",
                f"/api/automations/catalog?organization_id={organization_id}",
                headers={"Cookie": self.cookies["system_owner"]},
            )
            self.assertEqual(response.status, 200, body.decode())
            self.assertEqual(json.loads(body), expected)
        self.assertEqual(before, self._domain_snapshot())

    def test_create_validation_permissions_and_zero_write(self) -> None:
        response, body = self._post_rule(self._valid_payload("valid-create"))
        self.assertEqual(response.status, 201, body.decode())

        invalid_payloads = (
            dict(self._valid_payload("bad-trigger"), trigger_event_type="unknown"),
            dict(self._valid_payload("bad-conditions"), conditions_json=[]),
            dict(self._valid_payload("bad-action"), actions_json=[{"type": "unknown"}]),
            dict(self._valid_payload("two-actions"), actions_json=[valid_action(), valid_action("Two")]),
            dict(self._valid_payload("log-action"), actions_json=[{"type": "log", "message": "x"}]),
            dict(self._valid_payload("unknown-field"), actions_json=[dict(valid_action(), token="TOKEN_FAKE")]),
        )
        for payload in invalid_payloads:
            with self.subTest(slug=payload["rule_slug"]):
                before = self._automation_snapshot()
                response, body = self._post_rule(payload)
                self.assertEqual(response.status, 400, body.decode())
                error = json.loads(body)
                self.assertEqual(set(error), {"error", "code", "field"})
                serialized = body.decode().lower()
                for marker in ("token_fake", "secret_fake", "document_path_fake"):
                    self.assertNotIn(marker, serialized)
                self.assertEqual(before, self._automation_snapshot())

        for role in ("coordinator", "operator", "guest"):
            before = self._automation_snapshot()
            response, body = self._post_rule(self._valid_payload(f"denied-{role}"), role=role)
            self.assertEqual(response.status, 403, body.decode())
            self.assertEqual(before, self._automation_snapshot())

    def test_patch_full_definition_legacy_metadata_disable_enable_and_cross_org(self) -> None:
        response, body = self._post_rule(self._valid_payload("patch-target"))
        self.assertEqual(response.status, 201, body.decode())
        rule_id = int(json.loads(body)["automation_rule_id"])
        headers = {"Cookie": self.cookies["organization_admin"], "Content-Type": "application/json"}

        response, body = self._request(
            "PATCH",
            f"/api/automation/rules/{rule_id}",
            body=json.dumps({"conditions_json": {"status_after": "w_toku"}}),
            headers=headers,
        )
        self.assertEqual(response.status, 200, body.decode())

        for patch_payload in (
            {"trigger_event_type": "synthetic.legacy"},
            {"actions_json": [{"type": "log", "message": "hidden"}]},
            {"conditions_json": {"details_contains": "hidden"}},
        ):
            before = self._automation_snapshot()
            response, body = self._request(
                "PATCH",
                f"/api/automation/rules/{rule_id}",
                body=json.dumps(patch_payload),
                headers=headers,
            )
            self.assertEqual(response.status, 400, body.decode())
            self.assertEqual(before, self._automation_snapshot())

        legacy_id = self._create_raw_rule(slug="legacy-metadata", active=1)
        response, body = self._request(
            "PATCH",
            f"/api/automation/rules/{legacy_id}",
            body=json.dumps({"description": "Metadata only"}),
            headers=headers,
        )
        self.assertEqual(response.status, 200, body.decode())

        malformed_id = self._create_raw_rule(
            slug="malformed-enable",
            conditions=[],
            actions=[{"type": "unknown"}],
            active=1,
        )
        response, body = self._request(
            "PATCH",
            f"/api/automation/rules/{malformed_id}",
            body=json.dumps({"is_active": False}),
            headers=headers,
        )
        self.assertEqual(response.status, 200, body.decode())
        before_enable = self._automation_snapshot()
        response, body = self._request(
            "PATCH",
            f"/api/automation/rules/{malformed_id}",
            body=json.dumps({"is_active": True}),
            headers=headers,
        )
        self.assertEqual(response.status, 400, body.decode())
        self.assertEqual(before_enable, self._automation_snapshot())

        foreign_id = self._create_raw_rule(
            slug="foreign-valid",
            trigger="work_item_created",
            actions=[valid_action()],
            organization_id=self.other_organization_id,
        )
        before_foreign = self._automation_snapshot()
        response, body = self._request(
            "PATCH",
            f"/api/automation/rules/{foreign_id}?organization_id={self.other_organization_id}",
            body=json.dumps({"conditions_json": {"status_after": "nowe"}}),
            headers={**headers, "X-Organization-ID": str(self.other_organization_id)},
        )
        self.assertEqual(response.status, 404, body.decode())
        self.assertEqual(before_foreign, self._automation_snapshot())

    def test_manual_and_automatic_execution_fail_closed_while_legacy_log_runs(self) -> None:
        unknown_id = self._create_raw_rule(slug="unknown-action", actions=[{"type": "unknown"}])
        self.services["event_repository"].log(
            event_type="synthetic.legacy",
            invoice_id=None,
            organization_id=self.organization_id,
            source="TEST",
            status_before=None,
            status_after=None,
            decision_reason="synthetic",
            actor="test",
            details={"marker": "SECRET_FAKE"},
        )
        headers = {"Cookie": self.cookies["organization_admin"]}
        before = self._automation_snapshot()
        response, body = self._request(
            "POST",
            f"/api/automation/rules/{unknown_id}/run",
            headers=headers,
        )
        self.assertEqual(response.status, 400, body.decode())
        self.assertNotIn("secret_fake", body.decode().lower())
        self.assertEqual(before, self._automation_snapshot())

        malformed_id = self._create_raw_rule(slug="malformed-auto", conditions=[])
        result = self.services["automation_service"].process_pending_events(organization_id=self.organization_id)
        self.assertGreaterEqual(result["errors"], 2)
        self.assertEqual(before["automation_executions"], self._automation_snapshot()["automation_executions"])

        with get_connection() as connection:
            connection.execute("UPDATE automation_rules SET is_active = 0 WHERE automation_rule_id IN (?, ?)", (unknown_id, malformed_id))
        log_id = self._create_raw_rule(
            slug="legacy-log-runs",
            conditions={"details_contains": "needle"},
            actions=[{"type": "log", "message": "legacy safe"}],
        )
        self.services["event_repository"].log(
            event_type="synthetic.legacy",
            invoice_id=None,
            organization_id=self.organization_id,
            source="TEST",
            status_before=None,
            status_after=None,
            decision_reason="legacy",
            actor="test",
            details={"needle": True},
        )
        response, body = self._request(
            "POST",
            f"/api/automation/rules/{log_id}/run",
            headers=headers,
        )
        self.assertEqual(response.status, 201, body.decode())
        self.assertEqual(json.loads(body)["executions"], 1)
        executions = self.repository.list_executions(
            organization_id=self.organization_id,
            automation_rule_id=log_id,
        )
        self.assertEqual(executions[0]["execution_status"], "success")

    def test_manual_run_busy_is_a_safe_conflict(self) -> None:
        rule_id = self._create_raw_rule(
            slug="busy-rule",
            trigger="work_item_created",
            conditions={"status_after": "nowe"},
            actions=[valid_action()],
        )
        repository = self.services["automation_service"].automation_repository
        with patch.object(repository, "acquire_rule_claim", return_value=False):
            response, body = self._request(
                "POST",
                f"/api/automation/rules/{rule_id}/run",
                headers={"Cookie": self.cookies["organization_admin"]},
            )
        self.assertEqual(response.status, 409, body.decode())
        self.assertEqual(
            json.loads(body),
            {
                "error": "Reguła automatyzacji jest obecnie przetwarzana.",
                "code": "automation_rule_busy",
            },
        )

    def test_enable_with_active_lease_is_a_safe_conflict_without_partial_update(self) -> None:
        rule_id = self._create_raw_rule(
            slug="busy-enable",
            trigger="work_item_created",
            conditions={"status_after": "nowe"},
            actions=[valid_action()],
            active=0,
        )
        repository = self.services["automation_service"].automation_repository
        self.assertTrue(
            repository.acquire_rule_claim(
                automation_rule_id=rule_id,
                organization_id=self.organization_id,
                claim_token="busy-enable-owner",
                claimed_at="2026-10-25T10:00:00+00:00",
                lease_until="2999-10-25T10:05:00+00:00",
            )
        )
        before = self._automation_snapshot()
        response, body = self._request(
            "PATCH",
            f"/api/automation/rules/{rule_id}",
            body=json.dumps({"rule_name": "Must not persist", "is_active": True}),
            headers={"Cookie": self.cookies["organization_admin"], "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 409, body.decode())
        self.assertEqual(
            json.loads(body),
            {
                "error": "Reguła automatyzacji jest obecnie przetwarzana.",
                "code": "automation_rule_busy",
            },
        )
        self.assertEqual(before, self._automation_snapshot())


if __name__ == "__main__":
    unittest.main()
