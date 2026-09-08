from __future__ import annotations

import json
from unittest.mock import patch
from uuid import uuid4

from app.data_migration_manifest import MIGRATION_MANIFEST
from app.db import get_connection
from app.domain.constants import AUTOMATION_MANAGE_CAPABILITY, AUTOMATION_READ_CAPABILITY, USER_ROLES
from app.repositories.automation_repository import AutomationRepository
from tests.http_server_support import HttpServerTestCase


READ_ALLOWED = {"system_owner", "organization_admin", "coordinator"}
MANAGE_ALLOWED = {"system_owner", "organization_admin"}
RULE_PUBLIC_FIELDS = {
    "automation_rule_id",
    "rule_name",
    "rule_slug",
    "description",
    "trigger_event_type",
    "is_active",
    "last_run_at",
    "execution_count",
    "created_at",
    "updated_at",
}
EXECUTION_PUBLIC_FIELDS = {
    "automation_execution_id",
    "automation_rule_id",
    "execution_status",
    "trigger_event_type",
    "executed_at",
    "error_code",
    "error_summary",
}


class AutomationManagementSecurityTests(HttpServerTestCase):
    def setUp(self) -> None:
        super().setUp()
        with get_connection() as connection:
            self.initial_rule_id = int(
                connection.execute("SELECT COALESCE(MAX(automation_rule_id), 0) FROM automation_rules").fetchone()[0]
            )
            self.initial_execution_id = int(
                connection.execute(
                    "SELECT COALESCE(MAX(automation_execution_id), 0) FROM automation_executions"
                ).fetchone()[0]
            )
        self.auth_service = self.services["auth_service"]
        self.fixture_suffix = uuid4().hex[:12]
        self.admin = self.auth_service.list_users()[0]
        organization_service = self.services["organization_service"]
        self.organization = organization_service.create_organization(
            {"name": "Automation Security A", "slug": "automation-security-a", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.other_organization = organization_service.create_organization(
            {"name": "Automation Security B", "slug": "automation-security-b", "is_active": 1},
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
                    "login": f"automation-security-{role}",
                    "display_name": role,
                    "password": "Capability123!",
                    "role": role,
                    "organization_id": self.organization_id,
                    "is_active": 1,
                    "capabilities": [],
                },
                actor_login="admin",
                actor_user_id=int(self.admin["user_id"]),
                actor_user=self.admin,
            )
        self.repository = AutomationRepository()
        self.rule_id = self._create_raw_rule(self.organization_id, f"private-a-{self.fixture_suffix}")
        self.execution_id = self.repository.create_execution(
            {
                "automation_rule_id": self.rule_id,
                "organization_id": self.organization_id,
                "trigger_event_type": "synthetic.private",
                "execution_status": "failed",
                "input_json": '{"email":"raw-input@example.invalid"}',
                "result_json": '{"token":"raw-result-secret"}',
                "error_message": "Traceback C:\\Users\\private\\secret.py token=raw-error-secret",
            }
        )

    def tearDown(self) -> None:
        super().tearDown()
        with get_connection() as connection:
            connection.execute(
                "DELETE FROM automation_executions WHERE automation_execution_id > ?",
                (self.initial_execution_id,),
            )
            connection.execute(
                "DELETE FROM automation_rules WHERE automation_rule_id > ?",
                (self.initial_rule_id,),
            )

    def _create_raw_rule(self, organization_id: int, slug: str) -> int:
        return self.repository.create(
            {
                "organization_id": organization_id,
                "rule_slug": slug,
                "rule_name": f"Rule {slug}",
                "description": "Bezpieczny opis",
                "trigger_event_type": "synthetic.private",
                "conditions_json": '{"customer":"raw-condition-secret","nip":"9999999999"}',
                "actions_json": (
                    '[{"type":"raw-action-secret","token":"secret",'
                    '"document_path":"C:\\\\synthetic\\\\invoice.pdf","invoice_total":"123.45"}]'
                ),
                "is_active": 1,
                "last_result": "raw-last-result-secret",
                "created_by_user_id": int(self.admin["user_id"]),
            }
        )

    def _cookie_for_role(self, role: str) -> str:
        if role == "system_owner":
            return self._login("admin", "Admin1234")
        return self._login(f"automation-security-{role}", "Capability123!")

    def _scope(self, role: str, organization_id: int | None = None) -> str:
        if role == "system_owner":
            return f"?organization_id={organization_id or self.organization_id}"
        return ""

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

    def test_legacy_read_role_matrix_and_safe_dtos(self) -> None:
        cookies = {role: self._cookie_for_role(role) for role in USER_ROLES}
        before = self._domain_snapshot()
        for role in USER_ROLES:
            for route in ("/api/automation/rules", "/api/automation/executions"):
                with self.subTest(role=role, route=route):
                    response, body = self._request(
                        "GET",
                        route + self._scope(role),
                        headers={"Cookie": cookies[role]},
                    )
                    self.assertEqual(response.status, 200 if role in READ_ALLOWED else 403, body.decode())
                    if response.status != 200:
                        continue
                    payload = json.loads(body)
                    self.assertTrue(payload)
                    expected_fields = RULE_PUBLIC_FIELDS if route.endswith("rules") else EXECUTION_PUBLIC_FIELDS
                    self.assertEqual(set(payload[0]), expected_fields)
                    serialized = json.dumps(payload).lower()
                    for secret in (
                        "raw-condition-secret",
                        "raw-action-secret",
                        "raw-input@example.invalid",
                        "raw-result-secret",
                        "raw-error-secret",
                        "9999999999",
                        "synthetic\\\\invoice.pdf",
                        "123.45",
                        "conditions_json",
                        "actions_json",
                        "input_json",
                        "result_json",
                        "error_message",
                    ):
                        self.assertNotIn(secret, serialized)
        self.assertEqual(before, self._domain_snapshot())

    def test_session_contract_and_persistence_reject_manage_injection(self) -> None:
        user_repository = self.auth_service.user_repository
        for role in USER_ROLES:
            with self.subTest(role=role):
                cookie = self._cookie_for_role(role)
                response, body = self._request("GET", "/api/session/current", headers={"Cookie": cookie})
                self.assertEqual(response.status, 200, body.decode())
                capabilities = set(json.loads(body)["capabilities"])
                self.assertEqual(AUTOMATION_READ_CAPABILITY in capabilities, role in READ_ALLOWED)
                self.assertEqual(AUTOMATION_MANAGE_CAPABILITY in capabilities, role in MANAGE_ALLOWED)
                user_id = int(self.users[role]["user_id"])
                self.assertNotIn(AUTOMATION_MANAGE_CAPABILITY, user_repository.list_capabilities(user_id))

        coordinator = self.users["coordinator"]
        updated = self.auth_service.update_user(
            int(coordinator["user_id"]),
            {"capabilities": [AUTOMATION_MANAGE_CAPABILITY]},
            actor_login="admin",
            actor_user=self.admin,
        )
        self.assertNotIn(AUTOMATION_MANAGE_CAPABILITY, updated["capabilities"])
        self.assertNotIn(
            AUTOMATION_MANAGE_CAPABILITY,
            user_repository.list_capabilities(int(coordinator["user_id"])),
        )

    def test_legacy_write_role_matrix_and_denials_have_no_domain_side_effects(self) -> None:
        operations = (
            ("POST", "/api/automation/rules", lambda role: json.dumps({
                "rule_name": f"Created {role}",
                "rule_slug": f"created-{role}",
                "trigger_event_type": f"synthetic.created.{role}",
                "conditions_json": {},
                "actions_json": [],
            })),
            ("PATCH", f"/api/automation/rules/{self.rule_id}", lambda role: json.dumps({"description": f"Updated {role}"})),
            ("DELETE", f"/api/automation/rules/{self.rule_id}", lambda role: None),
            ("POST", f"/api/automation/rules/{self.rule_id}/run", lambda role: None),
        )
        for role in USER_ROLES:
            cookie = self._cookie_for_role(role)
            for method, route, body_builder in operations:
                with self.subTest(role=role, method=method, route=route):
                    before = self._domain_snapshot()
                    body = body_builder(role)
                    headers = {"Cookie": cookie}
                    if body is not None:
                        headers["Content-Type"] = "application/json"
                    response, payload = self._request(
                        method,
                        route + self._scope(role),
                        body=body,
                        headers=headers,
                    )
                    if role in MANAGE_ALLOWED:
                        self.assertIn(response.status, {200, 201}, payload.decode())
                        parsed = json.loads(payload)
                        if "automation_rule_id" in parsed:
                            self.assertEqual(set(parsed), RULE_PUBLIC_FIELDS)
                            self.assertNotIn("conditions_json", parsed)
                            self.assertNotIn("actions_json", parsed)
                            self.assertNotIn("last_result", parsed)
                    else:
                        self.assertEqual(response.status, 403, payload.decode())
                        self.assertEqual(before, self._domain_snapshot())

    def test_cross_org_spoofing_does_not_read_or_write_foreign_rules(self) -> None:
        foreign_rule_id = self._create_raw_rule(
            self.other_organization_id,
            f"private-b-{self.fixture_suffix}",
        )
        foreign_execution_id = self.repository.create_execution(
            {
                "automation_rule_id": foreign_rule_id,
                "organization_id": self.other_organization_id,
                "trigger_event_type": "synthetic.foreign",
                "execution_status": "failed",
                "input_json": '{"private":"foreign-execution-secret"}',
                "error_message": "foreign-error-secret",
            }
        )
        mismatched_execution_id = self.repository.create_execution(
            {
                "automation_rule_id": foreign_rule_id,
                "organization_id": self.organization_id,
                "trigger_event_type": "synthetic.mismatched",
                "execution_status": "failed",
                "input_json": '{"private":"mismatched-tenant-secret"}',
                "error_message": "mismatched-error-secret",
            }
        )
        cookie = self._cookie_for_role("organization_admin")
        response, body = self._request(
            "GET",
            f"/api/automation/rules?organization_id={self.other_organization_id}",
            headers={"Cookie": cookie, "X-Organization-ID": str(self.other_organization_id)},
        )
        self.assertEqual(response.status, 200, body.decode())
        ids = {int(item["automation_rule_id"]) for item in json.loads(body)}
        self.assertIn(self.rule_id, ids)
        self.assertNotIn(foreign_rule_id, ids)

        response, body = self._request(
            "GET",
            (
                f"/api/automation/executions?organization_id={self.other_organization_id}"
                f"&automation_rule_id={foreign_rule_id}"
            ),
            headers={"Cookie": cookie, "X-Organization-ID": str(self.other_organization_id)},
        )
        self.assertEqual(response.status, 200, body.decode())
        execution_ids = {int(item["automation_execution_id"]) for item in json.loads(body)}
        self.assertNotIn(foreign_execution_id, execution_ids)
        self.assertNotIn(mismatched_execution_id, execution_ids)
        self.assertNotIn("foreign-execution-secret", body.decode())
        self.assertNotIn("mismatched-tenant-secret", body.decode())

        attempts = (
            (
                "PATCH",
                f"/api/automation/rules/{foreign_rule_id}",
                json.dumps({
                    "description": "spoofed",
                    "organization_id": self.other_organization_id,
                    "capabilities": [AUTOMATION_MANAGE_CAPABILITY],
                    "role": "system_owner",
                }),
            ),
            ("DELETE", f"/api/automation/rules/{foreign_rule_id}", None),
            ("POST", f"/api/automation/rules/{foreign_rule_id}/run", None),
        )
        for method, route, request_body in attempts:
            with self.subTest(method=method):
                before = self._domain_snapshot()
                headers = {
                    "Cookie": cookie,
                    "X-Organization-ID": str(self.other_organization_id),
                    "X-Role": "system_owner",
                    "X-Capabilities": AUTOMATION_MANAGE_CAPABILITY,
                }
                if request_body is not None:
                    headers["Content-Type"] = "application/json"
                response, body = self._request(
                    method,
                    f"{route}?organization_id={self.other_organization_id}",
                    body=request_body,
                    headers=headers,
                )
                self.assertEqual(response.status, 404, body.decode())
                self.assertEqual(before, self._domain_snapshot())

    def test_guest_header_and_body_injection_cannot_grant_manage(self) -> None:
        cookie = self._cookie_for_role("guest")
        before = self._domain_snapshot()
        response, body = self._request(
            "POST",
            "/api/automation/rules",
            body=json.dumps({
                "rule_name": "Injected",
                "trigger_event_type": "synthetic.injected",
                "role": "system_owner",
                "capabilities": [AUTOMATION_MANAGE_CAPABILITY],
            }),
            headers={
                "Cookie": cookie,
                "Content-Type": "application/json",
                "X-Role": "system_owner",
                "X-Capabilities": AUTOMATION_MANAGE_CAPABILITY,
            },
        )
        self.assertEqual(response.status, 403, body.decode())
        self.assertEqual(before, self._domain_snapshot())

    def test_capability_guard_reuses_session_resolution_without_extra_lookup(self) -> None:
        cookie = self._cookie_for_role("organization_admin")
        user_repository = self.auth_service.user_repository
        with patch.object(
            user_repository,
            "list_capabilities",
            wraps=user_repository.list_capabilities,
        ) as list_capabilities:
            response, body = self._request(
                "GET",
                "/api/automation/rules",
                headers={"Cookie": cookie},
            )
        self.assertEqual(response.status, 200, body.decode())
        self.assertEqual(list_capabilities.call_count, 1)

    def test_authorized_manual_run_uses_only_synthetic_no_network_log_action(self) -> None:
        trigger = f"synthetic.manual.{self.fixture_suffix}"
        rule_id = self.repository.create(
            {
                "organization_id": self.organization_id,
                "rule_slug": f"manual-{self.fixture_suffix}",
                "rule_name": "Synthetic manual rule",
                "trigger_event_type": trigger,
                "conditions_json": "{}",
                "actions_json": '[{"type":"log","message":"synthetic no-network"}]',
                "is_active": 1,
                "created_by_user_id": int(self.admin["user_id"]),
            }
        )
        self.services["event_repository"].log(
            event_type=trigger,
            invoice_id=None,
            organization_id=self.organization_id,
            source="TEST",
            status_before=None,
            status_after=None,
            decision_reason="synthetic",
            actor="test",
            details={"fixture": self.fixture_suffix},
        )
        cookie = self._cookie_for_role("organization_admin")
        response, body = self._request(
            "POST",
            f"/api/automation/rules/{rule_id}/run",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 201, body.decode())
        self.assertEqual(json.loads(body), {"processed": True, "executions": 1, "errors": 0})
        executions = self.repository.list_executions(
            organization_id=self.organization_id,
            automation_rule_id=rule_id,
        )
        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0]["execution_status"], "success")
