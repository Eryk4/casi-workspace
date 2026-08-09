from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.db import get_connection, initialize_database, reset_database
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.invoice_ksef_override_repository import InvoiceKSeFOverrideRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository


class InvoiceKSeFOverrideIntegrityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.database = Path(self.temporary.name) / "override-integrity.sqlite3"
        self.path_patch = patch("app.db.SQLITE_DB_PATH", self.database)
        self.engine_patch = patch("app.db.DB_ENGINE", "sqlite")
        self.path_patch.start()
        self.engine_patch.start()
        initialize_database()

        self.organizations = OrganizationRepository()
        self.users = UserRepository()
        self.invoices = InvoiceRepository()
        self.approvals = ApprovalRepository()
        self.overrides = InvoiceKSeFOverrideRepository()
        self.organization_a = self.organizations.create({"name": "A", "slug": "a"})
        self.organization_b = self.organizations.create({"name": "B", "slug": "b"})
        self.user_a = self.users.create(
            {
                "login": "user-a",
                "organization_id": self.organization_a,
                "password_hash": "hash",
                "password_salt": "salt",
                "role": "administrator",
            }
        )
        self.invoice_a = self._create_invoice(self.organization_a, "a")
        self.invoice_b = self._create_invoice(self.organization_b, "b")
        self.approval_a = self.approvals.create(
            {
                "organization_id": self.organization_a,
                "entity_type": "invoice",
                "entity_id": self.invoice_a,
                "title": "Korekta KSeF",
                "requested_by_user_id": self.user_a,
            }
        )

    def tearDown(self) -> None:
        self.engine_patch.stop()
        self.path_patch.stop()
        self.temporary.cleanup()

    def _create_invoice(self, organization_id: int, suffix: str) -> int:
        return self.invoices.create(
            {
                "organization_id": organization_id,
                "incoming_date": "2026-08-09",
                "source": "KSeF",
                "file_name": f"invoice-{suffix}.xml",
                "invoice_number": f"FV/{suffix}",
                "gross_amount": "100.00",
                "currency": "PLN",
                "status": "nowa",
                "invoice_hash": f"hash-{suffix}",
            }
        )

    def _payload(self, **overrides) -> dict:
        payload = {
            "organization_id": self.organization_a,
            "invoice_id": self.invoice_a,
            "approval_request_id": self.approval_a,
            "field_name": "gross_amount",
            "source_value": "100.00",
            "local_value": "110.00",
            "status": "pending",
            "requested_by_user_id": self.user_a,
        }
        payload.update(overrides)
        return payload

    def test_valid_link_and_direct_approved_override_are_allowed(self) -> None:
        linked_id = self.overrides.create(self._payload())
        direct_id = self.overrides.create(
            self._payload(
                approval_request_id=None,
                status="approved",
                approved_by_user_id=self.user_a,
            )
        )
        self.assertGreater(linked_id, 0)
        self.assertGreater(direct_id, linked_id)

    def test_missing_parent_and_pending_without_parent_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Nie znaleziono wniosku"):
            self.overrides.create(self._payload(approval_request_id=999999))
        with self.assertRaisesRegex(ValueError, "wymaga wniosku"):
            self.overrides.create(self._payload(approval_request_id=None))
        with get_connection() as connection:
            count = connection.execute(
                "SELECT COUNT(*) AS total FROM invoice_ksef_field_overrides"
            ).fetchone()["total"]
        self.assertEqual(int(count), 0)

    def test_cross_organization_and_wrong_invoice_links_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Faktura nie nalezy"):
            self.overrides.create(
                self._payload(organization_id=self.organization_b)
            )
        with self.assertRaisesRegex(ValueError, "nie odpowiada"):
            self.overrides.create(
                self._payload(
                    organization_id=self.organization_b,
                    invoice_id=self.invoice_b,
                )
            )

    def test_parent_cannot_be_relinked_and_delete_is_blocked(self) -> None:
        override_id = self.overrides.create(self._payload())
        with self.assertRaisesRegex(ValueError, "Nie mozna przepinac"):
            self.overrides.update(override_id, {"approval_request_id": None})
        with self.assertRaises(sqlite3.IntegrityError):
            with get_connection() as connection:
                connection.execute(
                    "DELETE FROM approval_requests WHERE approval_request_id = ?",
                    (self.approval_a,),
                )

    def test_integrity_query_detects_no_orphans_or_context_mismatches(self) -> None:
        self.overrides.create(self._payload())
        self.overrides.create(
            self._payload(
                approval_request_id=None,
                status="approved",
                approved_by_user_id=self.user_a,
            )
        )
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT override.invoice_ksef_field_override_id
                FROM invoice_ksef_field_overrides override
                LEFT JOIN invoices invoice ON invoice.id = override.invoice_id
                LEFT JOIN approval_requests approval
                  ON approval.approval_request_id = override.approval_request_id
                WHERE invoice.id IS NULL
                   OR invoice.organization_id <> override.organization_id
                   OR (override.approval_request_id IS NULL AND override.status <> 'approved')
                   OR (
                        override.approval_request_id IS NOT NULL
                        AND (
                            approval.approval_request_id IS NULL
                            OR approval.organization_id <> override.organization_id
                            OR approval.entity_type <> 'invoice'
                            OR approval.entity_id <> override.invoice_id
                        )
                   )
                """
            ).fetchall()
        self.assertEqual(rows, [])

    def test_reset_removes_overrides_before_approval_requests(self) -> None:
        self.overrides.create(self._payload())
        reset_database()
        with get_connection() as connection:
            override_count = connection.execute(
                "SELECT COUNT(*) AS total FROM invoice_ksef_field_overrides"
            ).fetchone()["total"]
            approval_count = connection.execute(
                "SELECT COUNT(*) AS total FROM approval_requests"
            ).fetchone()["total"]
            foreign_key_issues = connection.execute("PRAGMA foreign_key_check").fetchall()
        self.assertEqual(int(override_count), 0)
        self.assertEqual(int(approval_count), 0)
        self.assertEqual(foreign_key_issues, [])


if __name__ == "__main__":
    unittest.main()
