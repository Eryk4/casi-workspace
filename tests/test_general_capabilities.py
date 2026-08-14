from __future__ import annotations

import json
from unittest.mock import patch

from app.data_migration_manifest import MIGRATION_MANIFEST
from app.db import get_connection
from app.domain.constants import (
    AUTOMATION_READ_CAPABILITY,
    BILLING_READ_CAPABILITY,
    KNOWLEDGE_MANAGE_CAPABILITY,
    KNOWLEDGE_READ_CAPABILITY,
    ROLE_MODULE_CAPABILITIES,
    USER_ROLES,
    WORK_ITEMS_READ_CAPABILITY,
    effective_capabilities_for_role,
)
from app.repositories.user_repository import UserRepository
from tests.http_server_support import HttpServerTestCase


EXPECTED_MODULE_CAPABILITIES = {
    "system_owner": {WORK_ITEMS_READ_CAPABILITY, BILLING_READ_CAPABILITY, AUTOMATION_READ_CAPABILITY},
    "organization_admin": {WORK_ITEMS_READ_CAPABILITY, BILLING_READ_CAPABILITY, AUTOMATION_READ_CAPABILITY},
    "coordinator": {WORK_ITEMS_READ_CAPABILITY, AUTOMATION_READ_CAPABILITY},
    "operator": {WORK_ITEMS_READ_CAPABILITY},
    "guest": set(),
}


class GeneralCapabilitiesTests(HttpServerTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.auth_service = self.services["auth_service"]
        self.admin = self.auth_service.list_users()[0]
        self.organization = self.services["organization_service"].create_organization(
            {
                "name": "General Capabilities",
                "slug": "general-capabilities",
                "is_active": 1,
                "enabled_modules": ["manager_assistant"],
            },
            actor_user=self.admin,
            actor_login="admin",
        )
        self.organization_id = int(self.organization["organization_id"])
        self.other_organization = self.services["organization_service"].create_organization(
            {"name": "General Capabilities Other", "slug": "general-capabilities-other", "is_active": 1},
            actor_user=self.admin,
            actor_login="admin",
        )
        self.users = {"system_owner": self.admin}
        for role in USER_ROLES:
            if role == "system_owner":
                continue
            self.users[role] = self.auth_service.create_user(
                {
                    "login": f"cap-{role}",
                    "display_name": role,
                    "password": "Capability123!",
                    "role": role,
                    "organization_id": self.organization_id,
                    "is_active": 1,
                    "capabilities": [KNOWLEDGE_READ_CAPABILITY, KNOWLEDGE_MANAGE_CAPABILITY],
                },
                actor_login="admin",
                actor_user_id=int(self.admin["user_id"]),
                actor_user=self.admin,
            )

    def _cookie_for_role(self, role: str) -> str:
        if role == "system_owner":
            return self._login("admin", "Admin1234")
        return self._login(f"cap-{role}", "Capability123!")

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

    def test_role_matrix_and_effective_capabilities_are_canonical(self) -> None:
        self.assertEqual(set(USER_ROLES), set(EXPECTED_MODULE_CAPABILITIES))
        for role, expected in EXPECTED_MODULE_CAPABILITIES.items():
            with self.subTest(role=role):
                self.assertEqual(set(ROLE_MODULE_CAPABILITIES[role]), expected)
                effective = effective_capabilities_for_role(
                    role,
                    [KNOWLEDGE_READ_CAPABILITY, KNOWLEDGE_MANAGE_CAPABILITY, "foo.admin", BILLING_READ_CAPABILITY],
                )
                self.assertEqual(
                    set(effective),
                    {KNOWLEDGE_READ_CAPABILITY, KNOWLEDGE_MANAGE_CAPABILITY} | expected,
                )
                self.assertEqual(list(effective), sorted(set(effective)))
        self.assertEqual(
            effective_capabilities_for_role("unknown", [KNOWLEDGE_READ_CAPABILITY, "foo.admin"]),
            (KNOWLEDGE_READ_CAPABILITY,),
        )

    def test_session_exposes_effective_but_storage_remains_knowledge_only(self) -> None:
        repository = UserRepository()
        for role, expected_modules in EXPECTED_MODULE_CAPABILITIES.items():
            cookie = self._cookie_for_role(role)
            response, payload = self._request("GET", "/api/session/current", headers={"Cookie": cookie})
            self.assertEqual(response.status, 200, payload.decode())
            session = json.loads(payload)
            self.assertEqual(set(session["capabilities"]) & set(EXPECTED_MODULE_CAPABILITIES["system_owner"]), expected_modules)
            stored = set(repository.list_capabilities(int(session["user_id"])))
            self.assertFalse(stored & set(EXPECTED_MODULE_CAPABILITIES["system_owner"]))

    def test_capability_update_cannot_persist_or_grant_module_capabilities(self) -> None:
        repository = UserRepository()
        cases = (
            ("operator", BILLING_READ_CAPABILITY),
            ("operator", AUTOMATION_READ_CAPABILITY),
            ("guest", WORK_ITEMS_READ_CAPABILITY),
        )
        for role, attempted in cases:
            with self.subTest(role=role, attempted=attempted):
                user = self.users[role]
                updated = self.auth_service.update_user(
                    int(user["user_id"]),
                    {"capabilities": [KNOWLEDGE_READ_CAPABILITY, attempted]},
                    actor_login="admin",
                    actor_user=self.admin,
                )
                self.assertNotIn(attempted, repository.list_capabilities(int(user["user_id"])))
                self.assertEqual(attempted in updated["capabilities"], attempted in EXPECTED_MODULE_CAPABILITIES[role])

    def test_existing_session_recomputes_capabilities_from_current_role(self) -> None:
        cookie = self._cookie_for_role("operator")
        response, payload = self._request("GET", "/api/session/current", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200, payload.decode())
        self.assertNotIn(BILLING_READ_CAPABILITY, json.loads(payload)["capabilities"])

        self.auth_service.update_user(
            int(self.users["operator"]["user_id"]),
            {"role": "organization_admin"},
            actor_login="admin",
            actor_user=self.admin,
        )
        response, payload = self._request("GET", "/api/session/current", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200, payload.decode())
        self.assertIn(BILLING_READ_CAPABILITY, json.loads(payload)["capabilities"])

    def test_module_read_endpoints_enforce_role_matrix(self) -> None:
        endpoints = {
            WORK_ITEMS_READ_CAPABILITY: f"/api/work-items?organization_id={self.organization_id}&limit=1",
            BILLING_READ_CAPABILITY: f"/api/billing/next-step-attention?organization_id={self.organization_id}",
            AUTOMATION_READ_CAPABILITY: f"/api/automations/operations?organization_id={self.organization_id}",
        }
        cookies = {role: self._cookie_for_role(role) for role in EXPECTED_MODULE_CAPABILITIES}
        before = self._domain_snapshot()
        for role, expected_modules in EXPECTED_MODULE_CAPABILITIES.items():
            cookie = cookies[role]
            for capability, endpoint in endpoints.items():
                with self.subTest(role=role, capability=capability):
                    response, payload = self._request("GET", endpoint, headers={"Cookie": cookie})
                    expected_status = 200 if capability in expected_modules else 403
                    self.assertEqual(response.status, expected_status, payload.decode())
        self.assertEqual(before, self._domain_snapshot())

    def test_capability_guard_reuses_session_resolution_without_extra_lookup(self) -> None:
        cookie = self._cookie_for_role("organization_admin")
        repository = self.auth_service.user_repository
        with patch.object(repository, "list_capabilities", wraps=repository.list_capabilities) as list_capabilities:
            response, payload = self._request(
                "GET",
                f"/api/billing/next-step-attention?organization_id={self.organization_id}",
                headers={"Cookie": cookie},
            )
        self.assertEqual(response.status, 200, payload.decode())
        self.assertEqual(list_capabilities.call_count, 1)

    def test_module_gates_preserve_cross_organization_scope(self) -> None:
        cookie = self._cookie_for_role("organization_admin")
        other_id = int(self.other_organization["organization_id"])
        response, payload = self._request(
            "GET",
            f"/api/billing/next-step-attention?organization_id={other_id}",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 200, payload.decode())
        self.assertEqual(json.loads(payload)["organization_id"], self.organization_id)
        response, payload = self._request(
            "GET",
            f"/api/automations/operations?organization_id={other_id}",
            headers={"Cookie": cookie},
        )
        self.assertEqual(response.status, 404, payload.decode())

    def test_automation_overview_detail_and_activity_share_the_gate(self) -> None:
        endpoints = (
            f"/api/automations/operations?organization_id={self.organization_id}",
            f"/api/automations/operations/internal_notification_scheduler?organization_id={self.organization_id}",
            f"/api/automations/operations/activity?organization_id={self.organization_id}&limit=1",
        )
        for role in ("coordinator", "operator"):
            cookie = self._cookie_for_role(role)
            for endpoint in endpoints:
                with self.subTest(role=role, endpoint=endpoint):
                    response, payload = self._request("GET", endpoint, headers={"Cookie": cookie})
                    self.assertEqual(response.status, 200 if role == "coordinator" else 403, payload.decode())

    def test_work_items_capability_does_not_bypass_task_acl(self) -> None:
        operator = self.users["operator"]
        coordinator = self.users["coordinator"]
        task = self.services["task_service"].create_task(
            {
                "title": "Prywatne zadanie operatora",
                "task_type": "zadanie",
                "status": "nowe",
                "priority": "normalny",
                "assigned_user_id": int(operator["user_id"]),
            },
            actor_user=operator,
            actor="operator",
            organization_id=self.organization_id,
        )
        task_path = f"/api/tasks/{task['task_id']}?organization_id={self.organization_id}"
        response, payload = self._request("GET", task_path, headers={"Cookie": self._cookie_for_role("operator")})
        self.assertEqual(response.status, 200, payload.decode())
        response, payload = self._request("GET", task_path, headers={"Cookie": self._cookie_for_role("coordinator")})
        self.assertEqual(response.status, 404, payload.decode())
        response, payload = self._request("GET", task_path, headers={"Cookie": self._cookie_for_role("guest")})
        self.assertEqual(response.status, 403, payload.decode())


if __name__ == "__main__":
    import unittest

    unittest.main()
