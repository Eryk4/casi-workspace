from __future__ import annotations

import json
import unittest

from app.bootstrap import build_services
from app.db import reset_database
from app.domain.constants import (
    KNOWLEDGE_MANAGE_CAPABILITY,
    KNOWLEDGE_READ_CAPABILITY,
    KNOWLEDGE_SYNC_CAPABILITY,
    KNOWLEDGE_UPLOAD_CAPABILITY,
    MANAGER_ASSISTANT_MODULE,
)
from app.services.auth_service import AuthError


class AuthServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        self.auth_service = self.services["auth_service"]
        self.organization_service = self.services["organization_service"]

    def test_default_admin_is_created_once_for_empty_database(self) -> None:
        created = self.auth_service.ensure_default_admin()
        self.assertIsNotNone(created)
        assert created is not None
        self.assertEqual(created["login"], "admin")
        self.assertEqual(created["role"], "system_owner")
        self.assertEqual(created["can_upload_knowledge"], 1)
        self.assertIsNone(created["organization_id"])
        self.assertTrue(created["is_global_admin"])

        again = self.auth_service.ensure_default_admin()
        self.assertIsNone(again)
        self.assertEqual(len(self.auth_service.list_users()), 1)

    def test_login_logout_and_current_session_flow(self) -> None:
        self.auth_service.ensure_default_admin()

        user, session_token = self.auth_service.login("admin", "Admin1234", "127.0.0.1", "unittest")
        self.assertEqual(user["login"], "admin")
        self.assertTrue(session_token)

        current_user = self.auth_service.get_current_user(session_token)
        self.assertIsNotNone(current_user)
        assert current_user is not None
        self.assertEqual(current_user["role"], "system_owner")
        self.assertEqual(current_user["can_upload_knowledge"], 1)
        self.assertTrue(current_user["is_global_admin"])

        self.auth_service.logout(session_token, actor_login="admin")
        self.assertIsNone(self.auth_service.get_current_user(session_token))

    def test_workspace_state_is_exposed_and_can_be_updated(self) -> None:
        admin = self.auth_service.ensure_default_admin()
        assert admin is not None

        current_user, _ = self.auth_service.login(
            "admin",
            "Admin1234",
            "127.0.0.1",
            "unittest",
            "device-a",
            "Laptop",
        )
        self.assertIsNone(current_user["workspace_state"])

        updated = self.auth_service.update_workspace_state(
            current_user,
            {
                "active_slot_id": "slot-2",
                "slots": [{"slot_id": "slot-2", "module_key": "knowledge", "subtab_key": "assistant"}],
            },
            device_id="device-a",
        )
        self.assertEqual(updated["workspace_state"]["active_slot_id"], "slot-2")
        self.assertEqual(updated["workspace_state_device_id"], "device-a")
        self.assertIsNotNone(updated["workspace_state_updated_at"])

        refreshed = self.auth_service.get_current_user(_)
        assert refreshed is not None
        self.assertEqual(refreshed["workspace_state"]["slots"][0]["module_key"], "knowledge")

    def test_same_account_allows_at_most_three_devices(self) -> None:
        self.auth_service.ensure_default_admin()

        for device_id in ("device-a", "device-b", "device-c"):
            user, token = self.auth_service.login(
                "admin",
                "Admin1234",
                "127.0.0.1",
                "unittest",
                device_id,
                f"Device {device_id}",
            )
            self.assertEqual(user["current_device_id"], device_id)
            self.assertTrue(token)

        with self.assertRaises(AuthError):
            self.auth_service.login(
                "admin",
                "Admin1234",
                "127.0.0.1",
                "unittest",
                "device-d",
                "Phone",
            )

    def test_relogin_on_same_device_reuses_device_slot(self) -> None:
        self.auth_service.ensure_default_admin()

        self.auth_service.login("admin", "Admin1234", "127.0.0.1", "unittest", "device-a", "Laptop")
        self.auth_service.login("admin", "Admin1234", "127.0.0.1", "unittest", "device-b", "Tablet")
        self.auth_service.login("admin", "Admin1234", "127.0.0.1", "unittest", "device-c", "Phone")

        user, token = self.auth_service.login(
            "admin",
            "Admin1234",
            "127.0.0.1",
            "unittest",
            "device-c",
            "Phone",
        )
        self.assertEqual(user["current_device_id"], "device-c")
        self.assertTrue(token)

    def test_personal_note_is_saved_per_user(self) -> None:
        admin = self.auth_service.ensure_default_admin()
        assert admin is not None
        organization = self.organization_service.create_organization(
            {"name": "Klient Notatka", "slug": "klient-notatka", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        created = self.auth_service.create_user(
            {
                "login": "osobista",
                "display_name": "Osobista",
                "password": "1234",
                "role": "operator",
                "organization_id": organization["organization_id"],
                "is_active": 1,
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )

        current_user, _ = self.auth_service.login("osobista", "1234", "127.0.0.1", "unittest")
        self.assertEqual(self.auth_service.get_personal_note(current_user)["personal_note_text"], "")

        updated = self.auth_service.update_personal_note(
            current_user,
            personal_note_text="Moje prywatne TODO na rano.",
            actor_login="osobista",
        )
        self.assertEqual(updated["personal_note_text"], "Moje prywatne TODO na rano.")
        self.assertIsNotNone(updated["personal_note_updated_at"])

        refreshed = self.auth_service.get_personal_note({"user_id": created["user_id"]})
        self.assertEqual(refreshed["personal_note_text"], "Moje prywatne TODO na rano.")

    def test_session_and_list_users_expose_organization_modules(self) -> None:
        admin = self.auth_service.ensure_default_admin()
        assert admin is not None
        organization = self.organization_service.create_organization(
            {
                "name": "Klient Moduly",
                "slug": "klient-moduly",
                "is_active": 1,
                "enabled_modules": [MANAGER_ASSISTANT_MODULE],
                "module_shortcuts": {"knowledge": "Ctrl+2", "tasks": "Alt+3"},
            },
            actor_user=admin,
            actor_login="admin",
        )

        created = self.auth_service.create_user(
            {
                "login": "moduly-admin",
                "display_name": "Moduly Admin",
                "password": "1234",
                "role": "organization_admin",
                "organization_id": organization["organization_id"],
                "is_active": 1,
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        self.assertEqual(created["organization_modules"], [MANAGER_ASSISTANT_MODULE])

        current_user, session_token = self.auth_service.login("moduly-admin", "1234", "127.0.0.1", "unittest")
        self.assertTrue(session_token)
        self.assertEqual(current_user["organization_modules"], [MANAGER_ASSISTANT_MODULE])
        self.assertEqual(
            current_user["organization_module_shortcuts"],
            {"knowledge": "Ctrl+2", "tasks": "Alt+3"},
        )

        listed = self.auth_service.list_users(admin, requested_organization_id=int(organization["organization_id"]))
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["organization_modules"], [MANAGER_ASSISTANT_MODULE])

    def test_session_and_list_users_expose_memberships(self) -> None:
        admin = self.auth_service.ensure_default_admin()
        assert admin is not None
        organization = self.organization_service.create_organization(
            {"name": "Klient Membership", "slug": "klient-membership", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )

        created = self.auth_service.create_user(
            {
                "login": "membership-admin",
                "display_name": "Membership Admin",
                "password": "1234",
                "role": "organization_admin",
                "organization_id": organization["organization_id"],
                "is_active": 1,
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )

        self.assertTrue(created["memberships"])
        self.assertEqual(created["memberships"][0]["organization_id"], organization["organization_id"])
        self.assertTrue(created["memberships"][0]["is_primary"])
        self.assertEqual(created["primary_membership"]["organization_id"], organization["organization_id"])

        current_user, session_token = self.auth_service.login("membership-admin", "1234", "127.0.0.1", "unittest")
        self.assertTrue(session_token)
        self.assertTrue(current_user["memberships"])
        self.assertEqual(current_user["primary_membership"]["organization_slug"], "klient-membership")

        listed = self.auth_service.list_users(admin, requested_organization_id=int(organization["organization_id"]))
        self.assertEqual(len(listed), 1)
        self.assertTrue(listed[0]["memberships"])
        self.assertEqual(listed[0]["memberships"][0]["organization_slug"], "klient-membership")

    def test_admin_can_create_and_update_operator_account(self) -> None:
        admin = self.auth_service.ensure_default_admin()
        assert admin is not None
        organization = self.organization_service.create_organization(
            {"name": "Klient Testowy", "slug": "klient-testowy", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )

        created = self.auth_service.create_user(
            {
                "login": "Eryk",
                "display_name": "Eryk Operator",
                "telegram_user_id": "582114092",
                "password": "9834",
                "role": "operator",
                "organization_id": organization["organization_id"],
                "is_active": 1,
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )
        self.assertEqual(created["login"], "Eryk")
        self.assertEqual(created["role"], "operator")
        self.assertEqual(created["telegram_user_id"], "582114092")
        self.assertEqual(created["telegram_reminders_enabled"], 1)
        self.assertEqual(created["can_upload_knowledge"], 1)
        self.assertEqual(created["organization_id"], organization["organization_id"])

        updated = self.auth_service.update_user(
            created["user_id"],
            {
                "display_name": "Eryk Glowny",
                "role": "guest",
                "telegram_reminders_enabled": 0,
                "can_upload_knowledge": 1,
                "password": "nowe-haslo",
                "organization_id": organization["organization_id"],
            },
            actor_login="admin",
            actor_user=admin,
        )
        self.assertEqual(updated["display_name"], "Eryk Glowny")
        self.assertEqual(updated["role"], "guest")
        self.assertEqual(updated["telegram_reminders_enabled"], 0)
        self.assertEqual(updated["can_upload_knowledge"], 0)

        with self.assertRaises(AuthError):
            self.auth_service.login("Eryk", "9834", "127.0.0.1", "unittest")

        refreshed, _ = self.auth_service.login("Eryk", "nowe-haslo", "127.0.0.1", "unittest")
        self.assertEqual(refreshed["role"], "guest")
        self.assertEqual(refreshed["telegram_reminders_enabled"], 0)
        self.assertEqual(refreshed["can_upload_knowledge"], 0)

    def test_guest_user_defaults_to_blocked_knowledge_upload(self) -> None:
        admin = self.auth_service.ensure_default_admin()
        assert admin is not None
        organization = self.organization_service.create_organization(
            {"name": "Klient Gosc", "slug": "klient-gosc", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )

        created = self.auth_service.create_user(
            {
                "login": "anna",
                "display_name": "Anna",
                "password": "1234",
                "role": "guest",
                "organization_id": organization["organization_id"],
                "is_active": 1,
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )

        self.assertEqual(created["role"], "guest")
        self.assertEqual(created["can_upload_knowledge"], 0)

    def test_explicit_capabilities_allow_fine_grained_knowledge_access(self) -> None:
        admin = self.auth_service.ensure_default_admin()
        assert admin is not None
        organization = self.organization_service.create_organization(
            {"name": "Klient Capability", "slug": "klient-capability", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )

        created = self.auth_service.create_user(
            {
                "login": "ania-cap",
                "display_name": "Ania Capability",
                "password": "1234",
                "role": "operator",
                "organization_id": organization["organization_id"],
                "is_active": 1,
                "can_upload_knowledge": 0,
                "capabilities": [KNOWLEDGE_READ_CAPABILITY, KNOWLEDGE_MANAGE_CAPABILITY],
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )

        self.assertEqual(
            set(created["capabilities"]),
            {KNOWLEDGE_READ_CAPABILITY, KNOWLEDGE_MANAGE_CAPABILITY},
        )
        self.assertEqual(created["can_upload_knowledge"], 0)
        self.assertTrue(self.auth_service.has_capability(created, KNOWLEDGE_MANAGE_CAPABILITY))
        self.assertFalse(self.auth_service.has_capability(created, KNOWLEDGE_UPLOAD_CAPABILITY))

        updated = self.auth_service.update_user(
            created["user_id"],
            {
                "can_upload_knowledge": 1,
                "capabilities": [
                    KNOWLEDGE_READ_CAPABILITY,
                    KNOWLEDGE_MANAGE_CAPABILITY,
                    KNOWLEDGE_UPLOAD_CAPABILITY,
                    KNOWLEDGE_SYNC_CAPABILITY,
                ],
            },
            actor_login="admin",
            actor_user=admin,
        )

        self.assertEqual(
            set(updated["capabilities"]),
            {
                KNOWLEDGE_READ_CAPABILITY,
                KNOWLEDGE_MANAGE_CAPABILITY,
                KNOWLEDGE_UPLOAD_CAPABILITY,
                KNOWLEDGE_SYNC_CAPABILITY,
            },
        )
        self.assertEqual(updated["can_upload_knowledge"], 1)

        current_user, _ = self.auth_service.login("ania-cap", "1234", "127.0.0.1", "unittest")
        self.assertEqual(set(current_user["capabilities"]), set(updated["capabilities"]))
        self.assertEqual(current_user["can_upload_knowledge"], 1)

    def test_organization_admin_cannot_grant_system_owner_role(self) -> None:
        admin = self.auth_service.ensure_default_admin()
        assert admin is not None
        organization = self.organization_service.create_organization(
            {"name": "Klient Uprawnien", "slug": "klient-uprawnien", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )
        org_admin = self.auth_service.create_user(
            {
                "login": "org-admin",
                "display_name": "Admin Organizacji",
                "password": "1234",
                "role": "organization_admin",
                "organization_id": organization["organization_id"],
                "is_active": 1,
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )

        with self.assertRaises(AuthError):
            self.auth_service.create_user(
                {
                    "login": "wlasciciel-proba",
                    "display_name": "Nieuprawniony",
                    "password": "1234",
                    "role": "system_owner",
                    "organization_id": None,
                    "is_active": 1,
                },
                actor_login="org-admin",
                actor_user_id=org_admin["user_id"],
                actor_user=org_admin,
            )

    def test_telegram_user_id_must_be_unique(self) -> None:
        admin = self.auth_service.ensure_default_admin()
        assert admin is not None
        organization = self.organization_service.create_organization(
            {"name": "Klient Telegram", "slug": "klient-telegram", "is_active": 1},
            actor_user=admin,
            actor_login="admin",
        )

        self.auth_service.create_user(
            {
                "login": "Eryk",
                "display_name": "Eryk",
                "telegram_user_id": "582114092",
                "password": "9834",
                "role": "operator",
                "organization_id": organization["organization_id"],
                "is_active": 1,
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
            actor_user=admin,
        )

        with self.assertRaises(AuthError):
            self.auth_service.create_user(
                {
                    "login": "Anna",
                    "display_name": "Anna",
                    "telegram_user_id": "582114092",
                    "password": "1234",
                    "role": "operator",
                    "organization_id": organization["organization_id"],
                    "is_active": 1,
                },
                actor_login="admin",
                actor_user_id=admin["user_id"],
                actor_user=admin,
            )


if __name__ == "__main__":
    unittest.main()
