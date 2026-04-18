from __future__ import annotations

from typing import Any

from app.db import execute_insert_returning_id, get_connection
from app.utils import json_dumps, now_iso


class KSeFImportRepository:
    def start_run(
        self,
        *,
        organization_id: int,
        company_identifier: str | None,
        environment: str | None,
        trigger_mode: str,
        actor: str,
        details: dict[str, Any] | None = None,
    ) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO ksef_import_runs (
                    organization_id,
                    company_identifier,
                    environment,
                    trigger_mode,
                    actor,
                    started_at,
                    finished_at,
                    status,
                    checked_document_count,
                    imported_invoice_count,
                    skipped_existing_count,
                    skipped_error_count,
                    summary_message,
                    details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    organization_id,
                    company_identifier,
                    environment,
                    trigger_mode,
                    actor,
                    timestamp,
                    None,
                    "running",
                    0,
                    0,
                    0,
                    0,
                    None,
                    json_dumps(details or {}),
                ),
                "ksef_import_run_id",
            )

    def finalize_run(
        self,
        run_id: int,
        *,
        status: str,
        checked_document_count: int,
        imported_invoice_count: int,
        skipped_existing_count: int,
        skipped_error_count: int,
        summary_message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE ksef_import_runs
                SET
                    finished_at = ?,
                    status = ?,
                    checked_document_count = ?,
                    imported_invoice_count = ?,
                    skipped_existing_count = ?,
                    skipped_error_count = ?,
                    summary_message = ?,
                    details = ?
                WHERE ksef_import_run_id = ?
                """,
                (
                    now_iso(),
                    status,
                    checked_document_count,
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
        source_external_id: str | None,
        ksef_number: str | None,
        invoice_number: str | None,
        issuer_nip: str | None,
        issue_date: str | None,
        item_status: str,
        invoice_id: int | None,
        reason: str | None = None,
    ) -> int:
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO ksef_import_items (
                    ksef_import_run_id,
                    organization_id,
                    source_external_id,
                    ksef_number,
                    invoice_number,
                    issuer_nip,
                    issue_date,
                    item_status,
                    invoice_id,
                    reason,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    organization_id,
                    source_external_id,
                    ksef_number,
                    invoice_number,
                    issuer_nip,
                    issue_date,
                    item_status,
                    invoice_id,
                    reason,
                    now_iso(),
                ),
                "ksef_import_item_id",
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
            FROM ksef_import_runs r
            JOIN organizations o ON o.organization_id = r.organization_id
        """
        if organization_id is not None:
            query += " WHERE r.organization_id = ?"
            params.append(organization_id)
        query += """
            ORDER BY COALESCE(r.finished_at, r.started_at) DESC, r.ksef_import_run_id DESC
            LIMIT ?
        """
        params.append(max(int(limit), 1))

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
            runs = [dict(row) for row in rows]
            if not runs:
                return []

            run_ids = [int(row["ksef_import_run_id"]) for row in runs]
            placeholders = ", ".join("?" for _ in run_ids)
            item_rows = connection.execute(
                f"""
                SELECT
                    i.*,
                    inv.file_name AS invoice_file_name
                FROM ksef_import_items i
                LEFT JOIN invoices inv ON inv.id = i.invoice_id
                WHERE i.ksef_import_run_id IN ({placeholders})
                ORDER BY i.created_at DESC, i.ksef_import_item_id DESC
                """,
                run_ids,
            ).fetchall()

        grouped_items: dict[int, list[dict[str, Any]]] = {run_id: [] for run_id in run_ids}
        for row in item_rows:
            grouped_items.setdefault(int(row["ksef_import_run_id"]), []).append(dict(row))

        for run in runs:
            run_id = int(run["ksef_import_run_id"])
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
