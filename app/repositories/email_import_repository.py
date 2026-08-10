from __future__ import annotations

from typing import Any

from app.db import execute_insert_returning_id, get_connection
from app.utils import json_dumps, now_iso


class EmailImportRepository:
    def get_operations_snapshot(self, organization_id: int) -> dict[str, Any]:
        """Return an organization-scoped, read-only operational snapshot.

        The projection deliberately excludes mailbox addresses, message metadata,
        item payloads and importer details because Automation Operations monitors
        the process rather than e-mail content.
        """
        with get_connection() as connection:
            organization = connection.execute(
                """
                SELECT
                    organization_id,
                    is_active,
                    email_integration_enabled,
                    CASE WHEN COALESCE(TRIM(email_inbox_address), '') <> '' THEN 1 ELSE 0 END AS has_inbox
                FROM organizations
                WHERE organization_id = ?
                """,
                (organization_id,),
            ).fetchone()
            latest_run = connection.execute(
                """
                SELECT
                    email_import_run_id,
                    trigger_mode,
                    started_at,
                    finished_at,
                    status,
                    checked_message_count,
                    matched_message_count,
                    matched_attachment_count,
                    imported_invoice_count,
                    skipped_existing_count,
                    skipped_error_count
                FROM email_import_runs
                WHERE organization_id = ?
                ORDER BY COALESCE(finished_at, started_at) DESC, email_import_run_id DESC
                LIMIT 1
                """,
                (organization_id,),
            ).fetchone()
            latest_terminal_run = connection.execute(
                """
                SELECT
                    email_import_run_id,
                    started_at,
                    finished_at,
                    status
                FROM email_import_runs
                WHERE organization_id = ?
                  AND status <> 'running'
                ORDER BY COALESCE(finished_at, started_at) DESC, email_import_run_id DESC
                LIMIT 1
                """,
                (organization_id,),
            ).fetchone()
            aggregates = connection.execute(
                """
                SELECT
                    COUNT(*) AS runs_count,
                    (
                        SELECT COUNT(*)
                        FROM (
                            SELECT status
                            FROM email_import_runs
                            WHERE organization_id = ?
                            ORDER BY COALESCE(finished_at, started_at) DESC, email_import_run_id DESC
                            LIMIT 50
                        ) recent_runs
                        WHERE status IN ('failed', 'completed_with_issues')
                    ) AS recent_failure_count,
                    MAX(CASE WHEN status IN ('completed', 'no_new_documents') THEN finished_at END) AS last_success_at,
                    MAX(CASE WHEN status IN ('failed', 'completed_with_issues') THEN finished_at END) AS last_failure_at
                FROM email_import_runs
                WHERE organization_id = ?
                """,
                (organization_id, organization_id),
            ).fetchone()
            item_counts = connection.execute(
                """
                SELECT
                    SUM(CASE WHEN item_status = 'imported' THEN 1 ELSE 0 END) AS imported_count,
                    SUM(CASE WHEN item_status = 'skipped_existing' THEN 1 ELSE 0 END) AS duplicate_count,
                    SUM(CASE WHEN item_status = 'skipped_error' THEN 1 ELSE 0 END) AS failed_count
                FROM email_import_items
                WHERE organization_id = ?
                """,
                (organization_id,),
            ).fetchone()
        return {
            "organization": dict(organization) if organization else None,
            "latest_run": dict(latest_run) if latest_run else None,
            "latest_terminal_run": dict(latest_terminal_run) if latest_terminal_run else None,
            "aggregates": dict(aggregates) if aggregates else {},
            "item_counts": dict(item_counts) if item_counts else {},
        }

    def list_runs_read_only(self, *, organization_id: int, limit: int = 20) -> list[dict[str, Any]]:
        """List sanitized run-level history without loading e-mail items."""
        normalized_limit = max(1, min(int(limit), 50))
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    email_import_run_id,
                    trigger_mode,
                    started_at,
                    finished_at,
                    status,
                    checked_message_count,
                    matched_message_count,
                    matched_attachment_count,
                    imported_invoice_count,
                    skipped_existing_count,
                    skipped_error_count
                FROM email_import_runs
                WHERE organization_id = ?
                ORDER BY COALESCE(finished_at, started_at) DESC, email_import_run_id DESC
                LIMIT ?
                """,
                (organization_id, normalized_limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def start_run(
        self,
        *,
        organization_id: int,
        mailbox_address: str | None,
        inbox_address: str | None,
        trigger_mode: str,
        actor: str,
        routing_mode: str,
        details: dict[str, Any] | None = None,
    ) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO email_import_runs (
                    organization_id,
                    mailbox_address,
                    inbox_address,
                    trigger_mode,
                    actor,
                    routing_mode,
                    started_at,
                    finished_at,
                    status,
                    checked_message_count,
                    matched_message_count,
                    matched_attachment_count,
                    imported_invoice_count,
                    skipped_existing_count,
                    skipped_error_count,
                    summary_message,
                    details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    organization_id,
                    mailbox_address,
                    inbox_address,
                    trigger_mode,
                    actor,
                    routing_mode,
                    timestamp,
                    None,
                    "running",
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    None,
                    json_dumps(details or {}),
                ),
                "email_import_run_id",
            )

    def finalize_run(
        self,
        run_id: int,
        *,
        status: str,
        checked_message_count: int,
        matched_message_count: int,
        matched_attachment_count: int,
        imported_invoice_count: int,
        skipped_existing_count: int,
        skipped_error_count: int,
        summary_message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE email_import_runs
                SET
                    finished_at = ?,
                    status = ?,
                    checked_message_count = ?,
                    matched_message_count = ?,
                    matched_attachment_count = ?,
                    imported_invoice_count = ?,
                    skipped_existing_count = ?,
                    skipped_error_count = ?,
                    summary_message = ?,
                    details = ?
                WHERE email_import_run_id = ?
                """,
                (
                    now_iso(),
                    status,
                    checked_message_count,
                    matched_message_count,
                    matched_attachment_count,
                    imported_invoice_count,
                    skipped_existing_count,
                    skipped_error_count,
                    summary_message,
                    json_dumps(details or {}),
                    run_id,
                ),
            )

    def add_item(
        self,
        *,
        run_id: int,
        organization_id: int,
        imap_uid: str | None,
        message_id: str | None,
        sender_email: str | None,
        subject: str | None,
        recipients: list[str] | None,
        matched_recipient: str | None,
        attachment_name: str | None,
        attachment_type: str | None,
        attachment_index: int | None,
        source_external_id: str | None,
        item_status: str,
        invoice_id: int | None,
        reason: str | None = None,
    ) -> int:
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO email_import_items (
                    email_import_run_id,
                    organization_id,
                    imap_uid,
                    message_id,
                    sender_email,
                    subject,
                    recipients,
                    matched_recipient,
                    attachment_name,
                    attachment_type,
                    attachment_index,
                    source_external_id,
                    item_status,
                    invoice_id,
                    reason,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    organization_id,
                    imap_uid,
                    message_id,
                    sender_email,
                    subject,
                    json_dumps(recipients or []),
                    matched_recipient,
                    attachment_name,
                    attachment_type,
                    attachment_index,
                    source_external_id,
                    item_status,
                    invoice_id,
                    reason,
                    now_iso(),
                ),
                "email_import_item_id",
            )

    def list_runs(
        self,
        *,
        organization_id: int | None = None,
        limit: int = 10,
        preview_items_limit: int = 5,
    ) -> list[dict[str, Any]]:
        params: list[Any] = []
        query = """
            SELECT
                r.*,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM email_import_runs r
            JOIN organizations o ON o.organization_id = r.organization_id
        """
        if organization_id is not None:
            query += " WHERE r.organization_id = ?"
            params.append(organization_id)
        query += """
            ORDER BY COALESCE(r.finished_at, r.started_at) DESC, r.email_import_run_id DESC
            LIMIT ?
        """
        params.append(max(int(limit), 1))

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
            runs = [dict(row) for row in rows]
            if not runs:
                return []

            run_ids = [int(row["email_import_run_id"]) for row in runs]
            placeholders = ", ".join("?" for _ in run_ids)
            item_rows = connection.execute(
                f"""
                SELECT
                    i.*,
                    inv.invoice_number,
                    inv.ksef_number,
                    inv.file_name AS invoice_file_name
                FROM email_import_items i
                LEFT JOIN invoices inv ON inv.id = i.invoice_id
                WHERE i.email_import_run_id IN ({placeholders})
                ORDER BY i.created_at DESC, i.email_import_item_id DESC
                """,
                run_ids,
            ).fetchall()

        grouped_items: dict[int, list[dict[str, Any]]] = {run_id: [] for run_id in run_ids}
        for row in item_rows:
            item = dict(row)
            item["recipients"] = self._deserialize_recipients(item.get("recipients"))
            grouped_items.setdefault(int(item["email_import_run_id"]), []).append(item)

        for run in runs:
            run_id = int(run["email_import_run_id"])
            run["details"] = self._deserialize_details(run.get("details"))
            run["items_preview"] = grouped_items.get(run_id, [])[:preview_items_limit]

        return runs

    def list_runs_for_organization(
        self,
        organization_id: int,
        *,
        limit: int = 10,
        preview_items_limit: int = 5,
    ) -> list[dict[str, Any]]:
        return self.list_runs(
            organization_id=organization_id,
            limit=limit,
            preview_items_limit=preview_items_limit,
        )

    def _deserialize_details(self, raw_value: Any) -> dict[str, Any]:
        if not raw_value:
            return {}
        if isinstance(raw_value, dict):
            return raw_value
        try:
            import json

            parsed = json.loads(str(raw_value))
        except (TypeError, ValueError):
            return {"raw_value": raw_value}
        return parsed if isinstance(parsed, dict) else {"raw_value": parsed}

    def _deserialize_recipients(self, raw_value: Any) -> list[str]:
        if not raw_value:
            return []
        try:
            import json

            parsed = json.loads(str(raw_value))
        except (TypeError, ValueError):
            return []
        if not isinstance(parsed, list):
            return []
        return [str(item).strip() for item in parsed if str(item).strip()]
