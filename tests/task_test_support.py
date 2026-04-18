from __future__ import annotations

import unittest

from app.bootstrap import build_services
from app.db import reset_database
from app.domain.constants import MANAGER_ASSISTANT_MODULE


class TaskMvpTestCase(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        self.services["auth_service"].ensure_default_admin()
        self.admin = self.services["auth_service"].list_users()[0]
        self.organization = self.services["organization_service"].create_organization(
            {
                "name": "Klient Zadaniowy",
                "slug": "klient-zadaniowy",
                "is_active": 1,
                "enabled_modules": ["manager_assistant"],
            },
            actor_user=self.admin,
            actor_login="admin",
        )
        self.services["organization_repository"].replace_enabled_modules(
            int(self.organization["organization_id"]),
            [MANAGER_ASSISTANT_MODULE],
            enabled_by_user_id=int(self.admin["user_id"]),
        )
        self.operator = self.services["auth_service"].create_user(
            {
                "login": "olga",
                "display_name": "Olga",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": self.organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )
        self.coordinator = self.services["auth_service"].create_user(
            {
                "login": "karol",
                "display_name": "Karol",
                "password": "1234",
                "role": "coordinator",
                "is_active": 1,
                "organization_id": self.organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )
        self.second_operator = self.services["auth_service"].create_user(
            {
                "login": "ania",
                "display_name": "Ania",
                "password": "1234",
                "role": "operator",
                "is_active": 1,
                "organization_id": self.organization["organization_id"],
            },
            actor_login="admin",
            actor_user_id=self.admin["user_id"],
            actor_user=self.admin,
        )
