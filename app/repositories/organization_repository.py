from __future__ import annotations

import json
from typing import Any

from app.db import execute_insert_returning_id, get_connection
from app.utils import now_iso


class OrganizationRepository:
    DEFAULT_ORGANIZATION_NAME = "CASI"
    DEFAULT_ORGANIZATION_SLUG = "casi"

    def list_organizations(self, only_active: bool = False) -> list[dict[str, Any]]:
        query = """
            SELECT
                o.*,
                (
                    SELECT COUNT(*)
                    FROM users u
                    WHERE u.organization_id = o.organization_id
                ) AS user_count,
                (
                    SELECT COUNT(*)
                    FROM invoices i
                    WHERE i.organization_id = o.organization_id
                ) AS invoice_count,
                (
                    SELECT COUNT(*)
                    FROM contractors c
                    WHERE c.organization_id = o.organization_id
                ) AS contractor_count
            FROM organizations o
        """
        params: list[Any] = []
        if only_active:
            query += " WHERE o.is_active = ?"
            params.append(1)
        query += " ORDER BY o.is_active DESC, o.name ASC"

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_by_id(self, organization_id: int) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM organizations
                WHERE organization_id = ?
                """,
                (organization_id,),
            ).fetchone()
        return dict(row) if row else None

    def get_by_name(self, name: str) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM organizations
                WHERE name = ?
                """,
                (name,),
            ).fetchone()
        return dict(row) if row else None

    def get_by_slug(self, slug: str) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM organizations
                WHERE slug = ?
                """,
                (slug,),
            ).fetchone()
        return dict(row) if row else None

    def search_organizations(
        self,
        query_text: str,
        *,
        organization_id: int | None = None,
        limit: int = 6,
    ) -> list[dict[str, Any]]:
        normalized_query = str(query_text or "").strip().lower()
        if not normalized_query:
            return []

        value = f"%{normalized_query}%"
        params: list[Any] = [value, value, value, value, value, value, value]
        query = """
            SELECT
                o.*,
                (
                    SELECT COUNT(*)
                    FROM users u
                    WHERE u.organization_id = o.organization_id
                ) AS user_count,
                (
                    SELECT COUNT(*)
                    FROM invoices i
                    WHERE i.organization_id = o.organization_id
                ) AS invoice_count,
                (
                    SELECT COUNT(*)
                    FROM contractors c
                    WHERE c.organization_id = o.organization_id
                ) AS contractor_count
            FROM organizations o
            WHERE (
                CAST(o.organization_id AS TEXT) LIKE ?
                OR LOWER(COALESCE(o.name, '')) LIKE ?
                OR LOWER(COALESCE(o.slug, '')) LIKE ?
                OR LOWER(COALESCE(o.email_inbox_address, '')) LIKE ?
                OR LOWER(COALESCE(o.communication_provider, '')) LIKE ?
                OR LOWER(COALESCE(o.telegram_chat_id, '')) LIKE ?
                OR LOWER(COALESCE(o.telegram_chat_name, '')) LIKE ?
            )
        """
        if organization_id is not None:
            query += " AND o.organization_id = ?"
            params.append(organization_id)
        query += """
            ORDER BY o.is_active DESC, o.name ASC, o.organization_id ASC
            LIMIT ?
        """
        params.append(limit)

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_by_telegram_chat_id(self, telegram_chat_id: str) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM organizations
                WHERE telegram_chat_id = ?
                """,
                (telegram_chat_id,),
            ).fetchone()
        return dict(row) if row else None

    def get_by_active_slack_channel_id(self, slack_channel_id: str) -> dict[str, Any] | None:
        normalized_channel_id = str(slack_channel_id or "").strip()
        if not normalized_channel_id:
            return None

        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM organizations
                WHERE communication_provider = ?
                """,
                ("slack",),
            ).fetchall()

        for row in rows:
            organization = dict(row)
            try:
                communication_config = json.loads(str(organization.get("communication_config_json") or "{}"))
            except json.JSONDecodeError:
                continue
            if not isinstance(communication_config, dict):
                continue
            slack_settings = communication_config.get("slack") or {}
            if not isinstance(slack_settings, dict):
                continue
            configured_channel_id = str(slack_settings.get("channel_id") or "").strip()
            if configured_channel_id == normalized_channel_id:
                return organization
        return None

    def list_email_ready_organizations(self, *, only_active: bool = True) -> list[dict[str, Any]]:
        params: list[Any] = [1]
        query = """
            SELECT *
            FROM organizations
            WHERE email_integration_enabled = ?
              AND COALESCE(TRIM(email_inbox_address), '') <> ''
        """
        if only_active:
            query += " AND is_active = ?"
            params.append(1)
        query += " ORDER BY name ASC, organization_id ASC"

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def list_ksef_ready_organizations(self, *, only_active: bool = True) -> list[dict[str, Any]]:
        params: list[Any] = [1]
        query = """
            SELECT *
            FROM organizations
            WHERE ksef_integration_enabled = ?
              AND COALESCE(TRIM(ksef_company_identifier), '') <> ''
        """
        if only_active:
            query += " AND is_active = ?"
            params.append(1)
        query += " ORDER BY name ASC, organization_id ASC"

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def list_enabled_modules(self, organization_id: int) -> list[str]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT module_code
                FROM organization_modules
                WHERE organization_id = ?
                ORDER BY module_code ASC
                """,
                (organization_id,),
            ).fetchall()
        return [str(row["module_code"]) for row in rows]

    def list_enabled_modules_map(self, organization_ids: list[int]) -> dict[int, list[str]]:
        normalized_ids = sorted({int(item) for item in organization_ids if item})
        if not normalized_ids:
            return {}
        placeholders = ", ".join("?" for _ in normalized_ids)
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT organization_id, module_code
                FROM organization_modules
                WHERE organization_id IN ({placeholders})
                ORDER BY organization_id ASC, module_code ASC
                """,
                normalized_ids,
            ).fetchall()
        result = {organization_id: [] for organization_id in normalized_ids}
        for row in rows:
            result.setdefault(int(row["organization_id"]), []).append(str(row["module_code"]))
        return result

    def replace_enabled_modules(
        self,
        organization_id: int,
        module_codes: list[str],
        enabled_by_user_id: int | None = None,
    ) -> None:
        normalized_codes = sorted({str(code).strip() for code in module_codes if str(code).strip()})
        timestamp = now_iso()
        with get_connection() as connection:
            connection.execute(
                """
                DELETE FROM organization_modules
                WHERE organization_id = ?
                """,
                (organization_id,),
            )
            for module_code in normalized_codes:
                connection.execute(
                    """
                    INSERT INTO organization_modules (
                        organization_id,
                        module_code,
                        enabled_at,
                        enabled_by_user_id
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (organization_id, module_code, timestamp, enabled_by_user_id),
                )

    def organization_has_module(self, organization_id: int, module_code: str) -> bool:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT 1
                FROM organization_modules
                WHERE organization_id = ?
                  AND module_code = ?
                """,
                (organization_id, module_code),
            ).fetchone()
        return bool(row)

    def update_email_check_state(
        self,
        organization_id: int,
        *,
        checked_at: str,
        status: str,
    ) -> None:
        self.update(
            organization_id,
            {
                "email_last_checked_at": checked_at,
                "email_last_check_status": status,
            },
        )

    def update_email_connection_state(
        self,
        organization_id: int,
        *,
        checked_at: str,
        status: str,
    ) -> None:
        self.update(
            organization_id,
            {
                "email_last_connection_tested_at": checked_at,
                "email_last_connection_status": status,
            },
        )

    def update_ksef_check_state(
        self,
        organization_id: int,
        *,
        checked_at: str,
        status: str,
    ) -> None:
        self.update(
            organization_id,
            {
                "ksef_last_checked_at": checked_at,
                "ksef_last_check_status": status,
            },
        )

    def update_ksef_connection_state(
        self,
        organization_id: int,
        *,
        checked_at: str,
        status: str,
    ) -> None:
        self.update(
            organization_id,
            {
                "ksef_last_connection_tested_at": checked_at,
                "ksef_last_connection_status": status,
            },
        )

    def create(self, payload: dict[str, Any]) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO organizations (
                    name, slug, module_shortcuts_json, communication_provider, communication_config_json,
                    shared_note_text, shared_note_updated_at, shared_note_updated_by_user_id,
                    telegram_chat_id, telegram_chat_name,
                    email_inbox_address, email_allowed_sender, email_subject_keyword,
                    email_integration_enabled, email_last_checked_at, email_last_check_status,
                    email_last_connection_tested_at, email_last_connection_status,
                    ksef_company_identifier, ksef_environment, ksef_integration_enabled,
                    ksef_last_checked_at, ksef_last_check_status,
                    ksef_last_connection_tested_at, ksef_last_connection_status,
                    ksef_correction_delegate_user_id, ksef_correction_delegate_assigned_at, ksef_correction_delegate_expires_at,
                    is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["name"],
                    payload["slug"],
                    payload.get("module_shortcuts_json") or json.dumps({}, ensure_ascii=True, sort_keys=True),
                    payload.get("communication_provider") or "telegram",
                    payload.get("communication_config_json") or json.dumps({}, ensure_ascii=True, sort_keys=True),
                    payload.get("shared_note_text") or "",
                    payload.get("shared_note_updated_at"),
                    payload.get("shared_note_updated_by_user_id"),
                    payload.get("telegram_chat_id"),
                    payload.get("telegram_chat_name"),
                    payload.get("email_inbox_address"),
                    payload.get("email_allowed_sender"),
                    payload.get("email_subject_keyword"),
                    int(payload.get("email_integration_enabled", 0)),
                    payload.get("email_last_checked_at"),
                    payload.get("email_last_check_status"),
                    payload.get("email_last_connection_tested_at"),
                    payload.get("email_last_connection_status"),
                    payload.get("ksef_company_identifier"),
                    payload.get("ksef_environment"),
                    int(payload.get("ksef_integration_enabled", 0)),
                    payload.get("ksef_last_checked_at"),
                    payload.get("ksef_last_check_status"),
                    payload.get("ksef_last_connection_tested_at"),
                    payload.get("ksef_last_connection_status"),
                    payload.get("ksef_correction_delegate_user_id"),
                    payload.get("ksef_correction_delegate_assigned_at"),
                    payload.get("ksef_correction_delegate_expires_at"),
                    int(payload.get("is_active", 1)),
                    timestamp,
                    timestamp,
                ),
                "organization_id",
            )

    def update(self, organization_id: int, fields: dict[str, Any]) -> None:
        if not fields:
            return
        allowed = {
            "name",
            "slug",
            "module_shortcuts_json",
            "communication_provider",
            "communication_config_json",
            "shared_note_text",
            "shared_note_updated_at",
            "shared_note_updated_by_user_id",
            "telegram_chat_id",
            "telegram_chat_name",
            "email_inbox_address",
            "email_allowed_sender",
            "email_subject_keyword",
            "email_integration_enabled",
            "email_last_checked_at",
            "email_last_check_status",
            "email_last_connection_tested_at",
            "email_last_connection_status",
            "ksef_company_identifier",
            "ksef_environment",
            "ksef_integration_enabled",
            "ksef_last_checked_at",
            "ksef_last_check_status",
            "ksef_last_connection_tested_at",
            "ksef_last_connection_status",
            "ksef_correction_delegate_user_id",
            "ksef_correction_delegate_assigned_at",
            "ksef_correction_delegate_expires_at",
            "is_active",
        }
        update_fields = {key: value for key, value in fields.items() if key in allowed}
        if not update_fields:
            return
        update_fields["updated_at"] = now_iso()
        assignments = ", ".join(f"{key} = ?" for key in update_fields)
        values = list(update_fields.values()) + [organization_id]
        with get_connection() as connection:
            connection.execute(
                f"UPDATE organizations SET {assignments} WHERE organization_id = ?",
                values,
            )

    def ensure_default_organization(self) -> dict[str, Any]:
        existing = self.get_by_slug(self.DEFAULT_ORGANIZATION_SLUG)
        if existing:
            return existing

        organization_id = self.create(
            {
                "name": self.DEFAULT_ORGANIZATION_NAME,
                "slug": self.DEFAULT_ORGANIZATION_SLUG,
                "is_active": 1,
            }
        )
        created = self.get_by_id(organization_id)
        assert created is not None
        return created

    def assign_legacy_records_to_default(
        self,
        default_organization_id: int,
        default_admin_login: str,
    ) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE contractors
                SET organization_id = ?
                WHERE organization_id IS NULL
                """,
                (default_organization_id,),
            )
            connection.execute(
                """
                UPDATE invoices
                SET organization_id = ?
                WHERE organization_id IS NULL
                """,
                (default_organization_id,),
            )
            connection.execute(
                """
                UPDATE event_logs
                SET organization_id = (
                    SELECT i.organization_id
                    FROM invoices i
                    WHERE i.id = event_logs.invoice_id
                )
                WHERE organization_id IS NULL
                  AND invoice_id IS NOT NULL
                """
            )
            connection.execute(
                """
                UPDATE event_logs
                SET organization_id = ?
                WHERE organization_id IS NULL
                """,
                (default_organization_id,),
            )
            connection.execute(
                """
                UPDATE users
                SET organization_id = ?
                WHERE organization_id IS NULL
                  AND login <> ?
                """,
                (default_organization_id, default_admin_login),
            )
