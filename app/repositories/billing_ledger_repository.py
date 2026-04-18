from __future__ import annotations

from typing import Any

from app.db import execute_insert_returning_id, get_connection
from app.utils import now_iso


class BillingLedgerRepository:
    def create_payment_match(self, payload: dict[str, Any]) -> int:
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO billing_payment_matches (
                    organization_id, billing_transaction_id, billing_payer_id, billing_charge_id, matched_amount,
                    match_status, match_reason, matched_by_user_id, matched_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["organization_id"],
                    payload["billing_transaction_id"],
                    payload["billing_payer_id"],
                    payload.get("billing_charge_id"),
                    float(payload["matched_amount"]),
                    payload.get("match_status") or "rozliczona",
                    payload.get("match_reason"),
                    payload.get("matched_by_user_id"),
                    payload.get("matched_at") or now_iso(),
                ),
                "billing_payment_match_id",
            )

    def list_payment_matches(
        self,
        *,
        organization_id: int | None = None,
        billing_payer_id: int | None = None,
        billing_transaction_id: int | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        params: list[Any] = []
        conditions = []
        if organization_id is not None:
            conditions.append("m.organization_id = ?")
            params.append(organization_id)
        if billing_payer_id is not None:
            conditions.append("m.billing_payer_id = ?")
            params.append(billing_payer_id)
        if billing_transaction_id is not None:
            conditions.append("m.billing_transaction_id = ?")
            params.append(billing_transaction_id)
        query = """
            SELECT
                m.*,
                p.display_name AS payer_display_name,
                p.contact_phone AS payer_contact_phone,
                t.booking_date AS transaction_booking_date,
                t.amount AS transaction_amount,
                t.title AS transaction_title,
                t.reference AS transaction_reference,
                c.total_amount AS charge_total_amount
            FROM billing_payment_matches m
            JOIN billing_payers p ON p.billing_payer_id = m.billing_payer_id
            JOIN billing_transactions t ON t.billing_transaction_id = m.billing_transaction_id
            LEFT JOIN billing_charges c ON c.billing_charge_id = m.billing_charge_id
        """
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY m.matched_at DESC, m.billing_payment_match_id DESC LIMIT ?"
        params.append(max(1, int(limit)))
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def create_ledger_entry(self, payload: dict[str, Any]) -> int:
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO billing_payer_ledger_entries (
                    organization_id, billing_payer_id, billing_charge_id, billing_transaction_id, entry_kind,
                    amount_delta, balance_after, note, created_by_user_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["organization_id"],
                    payload["billing_payer_id"],
                    payload.get("billing_charge_id"),
                    payload.get("billing_transaction_id"),
                    payload["entry_kind"],
                    float(payload["amount_delta"]),
                    float(payload["balance_after"]),
                    payload.get("note"),
                    payload.get("created_by_user_id"),
                    payload.get("created_at") or now_iso(),
                ),
                "billing_payer_ledger_entry_id",
            )

    def list_ledger_entries(
        self,
        *,
        organization_id: int | None = None,
        billing_payer_id: int | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        params: list[Any] = []
        conditions = []
        if organization_id is not None:
            conditions.append("l.organization_id = ?")
            params.append(organization_id)
        if billing_payer_id is not None:
            conditions.append("l.billing_payer_id = ?")
            params.append(billing_payer_id)
        query = """
            SELECT
                l.*,
                p.display_name AS payer_display_name,
                p.contact_phone AS payer_contact_phone,
                c.total_amount AS charge_total_amount,
                t.amount AS transaction_amount,
                t.booking_date AS transaction_booking_date,
                t.title AS transaction_title
            FROM billing_payer_ledger_entries l
            JOIN billing_payers p ON p.billing_payer_id = l.billing_payer_id
            LEFT JOIN billing_charges c ON c.billing_charge_id = l.billing_charge_id
            LEFT JOIN billing_transactions t ON t.billing_transaction_id = l.billing_transaction_id
        """
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY l.created_at DESC, l.billing_payer_ledger_entry_id DESC LIMIT ?"
        params.append(max(1, int(limit)))
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def list_balance_rows(self, organization_id: int | None = None) -> list[dict[str, Any]]:
        params: list[Any] = []
        conditions = []
        if organization_id is not None:
            conditions.append("p.organization_id = ?")
            params.append(organization_id)
        query = """
            SELECT
                p.*,
                COALESCE(charges.total_charges, 0) AS total_charges,
                COALESCE(matches.total_matches, 0) AS total_matches,
                COALESCE(charges.total_charges, 0) - COALESCE(matches.total_matches, 0) AS balance_due,
                last_match.last_match_at AS last_payment_at,
                last_match.last_match_amount AS last_payment_amount,
                last_match.last_match_currency AS last_payment_currency,
                last_match.last_match_title AS last_payment_title,
                last_match.last_match_reference AS last_payment_reference,
                matches.match_count AS matched_payment_count
            FROM billing_payers p
            LEFT JOIN (
                SELECT
                    organization_id,
                    billing_payer_id,
                    SUM(total_amount) AS total_charges
                FROM billing_charges
                GROUP BY organization_id, billing_payer_id
            ) charges
                ON charges.organization_id = p.organization_id
               AND charges.billing_payer_id = p.billing_payer_id
            LEFT JOIN (
                SELECT
                    organization_id,
                    billing_payer_id,
                    SUM(matched_amount) AS total_matches,
                    COUNT(*) AS match_count
                FROM billing_payment_matches
                GROUP BY organization_id, billing_payer_id
            ) matches
                ON matches.organization_id = p.organization_id
               AND matches.billing_payer_id = p.billing_payer_id
            LEFT JOIN (
                SELECT
                    ranked.organization_id,
                    ranked.billing_payer_id,
                    ranked.booking_date AS last_match_at,
                    ranked.matched_amount AS last_match_amount,
                    t.currency AS last_match_currency,
                    t.title AS last_match_title,
                    t.reference AS last_match_reference
                FROM (
                    SELECT
                        pm.*,
                        t.booking_date,
                        ROW_NUMBER() OVER (
                            PARTITION BY pm.organization_id, pm.billing_payer_id
                            ORDER BY t.booking_date DESC, pm.billing_payment_match_id DESC
                        ) AS row_number
                    FROM billing_payment_matches pm
                    JOIN billing_transactions t ON t.billing_transaction_id = pm.billing_transaction_id
                ) ranked
                JOIN billing_transactions t ON t.billing_transaction_id = ranked.billing_transaction_id
                WHERE ranked.row_number = 1
            ) last_match
                ON last_match.organization_id = p.organization_id
               AND last_match.billing_payer_id = p.billing_payer_id
        """
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY balance_due DESC, p.display_name ASC, p.billing_payer_id ASC"
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_balance_row(self, organization_id: int, billing_payer_id: int) -> dict[str, Any] | None:
        rows = self.list_balance_rows(organization_id=organization_id)
        for row in rows:
            if int(row["billing_payer_id"]) == int(billing_payer_id):
                return row
        return None
