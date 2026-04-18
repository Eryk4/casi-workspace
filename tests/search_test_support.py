from __future__ import annotations

import shutil
import unittest

from app.bootstrap import build_services
from app.config import KNOWLEDGE_DIR
from app.db import reset_database
from app.demo_seed import seed_demo_data


class SearchServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        shutil.rmtree(KNOWLEDGE_DIR, ignore_errors=True)
        KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
        self.services = build_services()
        self.auth_service = self.services["auth_service"]
        self.auth_service.ensure_default_admin()
        seed_demo_data(
            self.services["invoice_service"],
            self.services["invoice_repository"],
            task_service=self.services["task_service"],
            auth_service=self.auth_service,
            billing_service=self.services["billing_service"],
            knowledge_service=self.services["knowledge_service"],
            calendar_service=self.services["calendar_service"],
        )
        self.search_service = self.services["search_service"]
        self.organization_repository = self.services["organization_repository"]
        self.users_by_login = {item["login"]: item for item in self.auth_service.list_users()}
