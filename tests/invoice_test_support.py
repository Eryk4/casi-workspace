from __future__ import annotations

import unittest

from app.bootstrap import build_services
from app.db import get_connection, reset_database
from app.demo_seed import seed_demo_data
from app.services.auth_service import PermissionError


class InvoiceMvpTestCase(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.services = build_services()
        self.auth_service = self.services["auth_service"]
        self.organization_repository = self.services["organization_repository"]
        self.organization_service = self.services["organization_service"]
        self.approval_service = self.services["approval_service"]
        self.auth_service.ensure_default_admin()
        self.admin = self.auth_service.list_users()[0]
        self.default_organization = self.organization_repository.ensure_default_organization()
        seed_demo_data(self.services["invoice_service"], self.services["invoice_repository"])
