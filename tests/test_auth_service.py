from __future__ import annotations

import unittest

from app.bootstrap import build_services
from app.db import reset_database
from app.services.auth_service import AuthError


class AuthServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        self.auth_service = self.services["auth_service"]

    def test_default_admin_is_created_once_for_empty_database(self) -> None:
        created = self.auth_service.ensure_default_admin()
        self.assertIsNotNone(created)
        self.assertEqual(created["login"], "admin")
        self.assertEqual(created["role"], "administrator")

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
        self.assertEqual(current_user["role"], "administrator")

        self.auth_service.logout(session_token, actor_login="admin")
        self.assertIsNone(self.auth_service.get_current_user(session_token))

    def test_admin_can_create_and_update_operator_account(self) -> None:
        admin = self.auth_service.ensure_default_admin()
        assert admin is not None

        created = self.auth_service.create_user(
            {
                "login": "Eryk",
                "display_name": "Eryk Operator",
                "telegram_user_id": "582114092",
                "password": "9834",
                "role": "operator",
                "is_active": 1,
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
        )
        self.assertEqual(created["login"], "Eryk")
        self.assertEqual(created["role"], "operator")
        self.assertEqual(created["telegram_user_id"], "582114092")

        updated = self.auth_service.update_user(
            created["user_id"],
            {
                "display_name": "Eryk Główny",
                "role": "podglad",
                "password": "nowe-haslo",
            },
            actor_login="admin",
        )
        self.assertEqual(updated["display_name"], "Eryk Główny")
        self.assertEqual(updated["role"], "podglad")

        with self.assertRaises(AuthError):
            self.auth_service.login("Eryk", "9834", "127.0.0.1", "unittest")

        refreshed, _ = self.auth_service.login("Eryk", "nowe-haslo", "127.0.0.1", "unittest")
        self.assertEqual(refreshed["role"], "podglad")

    def test_telegram_user_id_must_be_unique(self) -> None:
        admin = self.auth_service.ensure_default_admin()
        assert admin is not None

        self.auth_service.create_user(
            {
                "login": "Eryk",
                "display_name": "Eryk",
                "telegram_user_id": "582114092",
                "password": "9834",
                "role": "operator",
                "is_active": 1,
            },
            actor_login="admin",
            actor_user_id=admin["user_id"],
        )

        with self.assertRaises(AuthError):
            self.auth_service.create_user(
                {
                    "login": "Anna",
                    "display_name": "Anna",
                    "telegram_user_id": "582114092",
                    "password": "1234",
                    "role": "operator",
                    "is_active": 1,
                },
                actor_login="admin",
                actor_user_id=admin["user_id"],
            )


if __name__ == "__main__":
    unittest.main()
