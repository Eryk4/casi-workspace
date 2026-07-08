from __future__ import annotations

from typing import Any

from app.db import execute_insert_returning_id, get_connection
from app.utils import json_dumps, now_iso


class BillingRepository:
    def list_models(
        self,
        organization_id: int | None = None,
        only_active: bool = False,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT
                m.*,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM billing_models m
            LEFT JOIN organizations o ON o.organization_id = m.organization_id
        """
        conditions: list[str] = []
        params: list[Any] = []

        if organization_id is not None:
            conditions.append("m.organization_id = ?")
            params.append(organization_id)
        if only_active:
            conditions.append("m.is_active = 1")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY m.is_active DESC, m.school_year DESC, m.lesson_day ASC, m.name ASC, m.billing_model_id ASC"

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_model_by_id(
        self,
        billing_model_id: int,
        organization_id: int | None = None,
    ) -> dict[str, Any] | None:
        query = """
            SELECT
                m.*,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM billing_models m
            LEFT JOIN organizations o ON o.organization_id = m.organization_id
            WHERE m.billing_model_id = ?
        """
        params: list[Any] = [billing_model_id]
        if organization_id is not None:
            query += " AND m.organization_id = ?"
            params.append(organization_id)

        with get_connection() as connection:
            row = connection.execute(query, params).fetchone()
        return dict(row) if row else None

    def get_model_by_name(
        self,
        name: str,
        organization_id: int,
    ) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM billing_models
                WHERE organization_id = ?
                  AND name = ?
                """,
                (organization_id, name),
            ).fetchone()
        return dict(row) if row else None

    def create_model(self, payload: dict[str, Any]) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO billing_models (
                    organization_id, name, profile_type, school_year, lesson_day, settlement_mode,
                    monthly_rate_amount, semester_rate_amount, sibling_discount_amount,
                    large_family_discount_amount, intro_free_lessons_count, contract_required,
                    notes, is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["organization_id"],
                    payload["name"],
                    payload.get("profile_type", "education_student"),
                    payload["school_year"],
                    payload.get("lesson_day"),
                    payload["settlement_mode"],
                    payload.get("monthly_rate_amount"),
                    payload.get("semester_rate_amount"),
                    payload.get("sibling_discount_amount", 100),
                    payload.get("large_family_discount_amount", 50),
                    payload.get("intro_free_lessons_count", 1),
                    int(payload.get("contract_required", 0)),
                    payload.get("notes"),
                    int(payload.get("is_active", 1)),
                    timestamp,
                    timestamp,
                ),
                "billing_model_id",
            )

    def list_payers(
        self,
        organization_id: int | None = None,
        only_active: bool = False,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT
                p.*,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM billing_payers p
            LEFT JOIN organizations o ON o.organization_id = p.organization_id
        """
        conditions: list[str] = []
        params: list[Any] = []

        if organization_id is not None:
            conditions.append("p.organization_id = ?")
            params.append(organization_id)
        if only_active:
            conditions.append("p.is_active = 1")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY p.is_active DESC, p.display_name ASC, p.contact_phone ASC, p.billing_payer_id ASC"

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_payer_by_id(
        self,
        billing_payer_id: int,
        organization_id: int | None = None,
    ) -> dict[str, Any] | None:
        query = """
            SELECT
                p.*,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM billing_payers p
            LEFT JOIN organizations o ON o.organization_id = p.organization_id
            WHERE p.billing_payer_id = ?
        """
        params: list[Any] = [billing_payer_id]
        if organization_id is not None:
            query += " AND p.organization_id = ?"
            params.append(organization_id)

        with get_connection() as connection:
            row = connection.execute(query, params).fetchone()
        return dict(row) if row else None

    def get_payer_by_payment_identifier(
        self,
        payment_identifier: str,
        organization_id: int,
    ) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM billing_payers
                WHERE organization_id = ?
                  AND payment_identifier = ?
                """,
                (organization_id, payment_identifier),
            ).fetchone()
        return dict(row) if row else None

    def add_payer_note(self, payload: dict[str, Any]) -> int:
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO billing_notes (
                    organization_id, billing_payer_id, author_user_id, note_type, note_text, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["organization_id"],
                    payload["billing_payer_id"],
                    payload["author_user_id"],
                    payload.get("note_type") or "operator_note",
                    payload["note_text"],
                    now_iso(),
                ),
                "billing_note_id",
            )

    def list_payer_notes(
        self,
        billing_payer_id: int,
        *,
        organization_id: int | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        params: list[Any] = [billing_payer_id]
        query = """
            SELECT
                n.*,
                COALESCE(u.display_name, u.login) AS author_user_name,
                u.role AS author_user_role
            FROM billing_notes n
            LEFT JOIN users u ON u.user_id = n.author_user_id
            WHERE n.billing_payer_id = ?
        """
        if organization_id is not None:
            query += " AND n.organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY n.created_at DESC, n.billing_note_id DESC LIMIT ?"
        params.append(max(1, int(limit)))
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def add_payment_review_event(self, payload: dict[str, Any]) -> int:
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO billing_payment_review_events (
                    organization_id, billing_transaction_id, status, note_text, created_by_user_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["organization_id"],
                    payload["billing_transaction_id"],
                    payload["status"],
                    payload.get("note_text"),
                    payload["created_by_user_id"],
                    now_iso(),
                ),
                "billing_payment_review_event_id",
            )

    def list_payment_review_events(
        self,
        billing_transaction_id: int,
        *,
        organization_id: int | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        params: list[Any] = [billing_transaction_id]
        query = """
            SELECT
                e.*,
                COALESCE(u.display_name, u.login) AS created_by_user_name,
                u.role AS created_by_user_role
            FROM billing_payment_review_events e
            LEFT JOIN users u ON u.user_id = e.created_by_user_id
            WHERE e.billing_transaction_id = ?
        """
        if organization_id is not None:
            query += " AND e.organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY e.created_at DESC, e.billing_payment_review_event_id DESC LIMIT ?"
        params.append(max(1, int(limit)))
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def create_payer(self, payload: dict[str, Any]) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO billing_payers (
                    organization_id, display_name, contact_phone, payment_identifier,
                    has_large_family_card, email, notes, is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["organization_id"],
                    payload.get("display_name"),
                    payload["contact_phone"],
                    payload["payment_identifier"],
                    int(payload.get("has_large_family_card", 0)),
                    payload.get("email"),
                    payload.get("notes"),
                    int(payload.get("is_active", 1)),
                    timestamp,
                    timestamp,
                ),
                "billing_payer_id",
            )

    def list_students(
        self,
        organization_id: int | None = None,
        only_active: bool = False,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT
                s.*,
                o.name AS organization_name,
                o.slug AS organization_slug,
                p.display_name AS payer_display_name,
                p.contact_phone AS payer_contact_phone,
                p.payment_identifier AS payer_payment_identifier,
                p.is_active AS payer_is_active,
                sc.full_name AS school_full_name,
                sc.short_name AS school_short_name,
                sc.city AS school_city,
                m.name AS model_name,
                m.school_year AS model_school_year,
                m.lesson_day AS model_lesson_day,
                m.settlement_mode AS model_settlement_mode
            FROM billing_students s
            LEFT JOIN organizations o ON o.organization_id = s.organization_id
            JOIN billing_payers p ON p.billing_payer_id = s.billing_payer_id
            LEFT JOIN billing_schools sc ON sc.billing_school_id = s.billing_school_id
            LEFT JOIN billing_models m ON m.billing_model_id = s.billing_model_id
        """
        conditions: list[str] = []
        params: list[Any] = []

        if organization_id is not None:
            conditions.append("s.organization_id = ?")
            params.append(organization_id)
        if only_active:
            conditions.append("s.is_active = 1")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY s.is_active DESC, s.full_name ASC, s.billing_student_id ASC"

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_student_by_id(
        self,
        billing_student_id: int,
        organization_id: int | None = None,
    ) -> dict[str, Any] | None:
        query = """
            SELECT
                s.*,
                o.name AS organization_name,
                o.slug AS organization_slug,
                p.display_name AS payer_display_name,
                p.contact_phone AS payer_contact_phone,
                p.payment_identifier AS payer_payment_identifier,
                sc.full_name AS school_full_name,
                sc.short_name AS school_short_name,
                m.name AS model_name,
                m.school_year AS model_school_year,
                m.lesson_day AS model_lesson_day,
                m.settlement_mode AS model_settlement_mode
            FROM billing_students s
            LEFT JOIN organizations o ON o.organization_id = s.organization_id
            JOIN billing_payers p ON p.billing_payer_id = s.billing_payer_id
            LEFT JOIN billing_schools sc ON sc.billing_school_id = s.billing_school_id
            LEFT JOIN billing_models m ON m.billing_model_id = s.billing_model_id
            WHERE s.billing_student_id = ?
        """
        params: list[Any] = [billing_student_id]
        if organization_id is not None:
            query += " AND s.organization_id = ?"
            params.append(organization_id)

        with get_connection() as connection:
            row = connection.execute(query, params).fetchone()
        return dict(row) if row else None

    def create_student(self, payload: dict[str, Any]) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO billing_students (
                    organization_id, billing_payer_id, billing_school_id, billing_model_id, full_name,
                    lesson_day, family_billing_order, group_name, notes, is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["organization_id"],
                    payload["billing_payer_id"],
                    payload.get("billing_school_id"),
                    payload.get("billing_model_id"),
                    payload["full_name"],
                    payload.get("lesson_day"),
                    int(payload.get("family_billing_order", 1)),
                    payload.get("group_name"),
                    payload.get("notes"),
                    int(payload.get("is_active", 1)),
                    timestamp,
                    timestamp,
                ),
                "billing_student_id",
            )

    def get_charge_batch_by_id(
        self,
        billing_charge_batch_id: int,
        organization_id: int | None = None,
    ) -> dict[str, Any] | None:
        query = """
            SELECT
                b.*,
                m.name AS model_name,
                m.lesson_day AS model_lesson_day,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM billing_charge_batches b
            JOIN billing_models m ON m.billing_model_id = b.billing_model_id
            LEFT JOIN organizations o ON o.organization_id = b.organization_id
            WHERE b.billing_charge_batch_id = ?
        """
        params: list[Any] = [billing_charge_batch_id]
        if organization_id is not None:
            query += " AND b.organization_id = ?"
            params.append(organization_id)

        with get_connection() as connection:
            row = connection.execute(query, params).fetchone()
        return dict(row) if row else None

    def get_charge_batch_by_model_and_period(
        self,
        *,
        organization_id: int,
        billing_model_id: int,
        period_label: str,
    ) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM billing_charge_batches
                WHERE organization_id = ?
                  AND billing_model_id = ?
                  AND period_label = ?
                """,
                (organization_id, billing_model_id, period_label),
            ).fetchone()
        return dict(row) if row else None

    def create_charge_batch(self, payload: dict[str, Any]) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO billing_charge_batches (
                    organization_id, billing_model_id, school_year, period_type, period_label, due_date,
                    lesson_count, generated_by_user_id, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["organization_id"],
                    payload["billing_model_id"],
                    payload["school_year"],
                    payload["period_type"],
                    payload["period_label"],
                    payload["due_date"],
                    int(payload.get("lesson_count", 0)),
                    payload.get("generated_by_user_id"),
                    payload.get("notes"),
                    timestamp,
                    timestamp,
                ),
                "billing_charge_batch_id",
            )

    def create_charge(self, payload: dict[str, Any]) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO billing_charges (
                    organization_id, billing_charge_batch_id, billing_model_id, billing_student_id, billing_payer_id,
                    school_year, period_label, due_date, lesson_count, unit_rate_amount, base_amount,
                    intro_free_discount_amount, sibling_discount_amount, large_family_discount_amount,
                    total_amount, status, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["organization_id"],
                    payload["billing_charge_batch_id"],
                    payload["billing_model_id"],
                    payload["billing_student_id"],
                    payload["billing_payer_id"],
                    payload["school_year"],
                    payload["period_label"],
                    payload["due_date"],
                    int(payload.get("lesson_count", 0)),
                    float(payload["unit_rate_amount"]),
                    float(payload["base_amount"]),
                    float(payload.get("intro_free_discount_amount", 0)),
                    float(payload.get("sibling_discount_amount", 0)),
                    float(payload.get("large_family_discount_amount", 0)),
                    float(payload["total_amount"]),
                    payload.get("status", "otwarta"),
                    payload.get("notes"),
                    timestamp,
                    timestamp,
                ),
                "billing_charge_id",
            )

    def list_charges(
        self,
        *,
        organization_id: int | None = None,
        billing_charge_batch_id: int | None = None,
        billing_model_id: int | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT
                c.*,
                b.period_type,
                m.name AS model_name,
                m.lesson_day AS model_lesson_day,
                s.full_name AS student_full_name,
                s.lesson_day AS student_lesson_day,
                s.group_name AS student_group_name,
                p.display_name AS payer_display_name,
                p.contact_phone AS payer_contact_phone,
                p.payment_identifier AS payer_payment_identifier,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM billing_charges c
            JOIN billing_charge_batches b ON b.billing_charge_batch_id = c.billing_charge_batch_id
            JOIN billing_models m ON m.billing_model_id = c.billing_model_id
            JOIN billing_students s ON s.billing_student_id = c.billing_student_id
            JOIN billing_payers p ON p.billing_payer_id = c.billing_payer_id
            LEFT JOIN organizations o ON o.organization_id = c.organization_id
        """
        conditions: list[str] = []
        params: list[Any] = []

        if organization_id is not None:
            conditions.append("c.organization_id = ?")
            params.append(organization_id)
        if billing_charge_batch_id is not None:
            conditions.append("c.billing_charge_batch_id = ?")
            params.append(billing_charge_batch_id)
        if billing_model_id is not None:
            conditions.append("c.billing_model_id = ?")
            params.append(billing_model_id)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += """
            ORDER BY c.due_date DESC, c.created_at DESC, c.billing_charge_id DESC
            LIMIT ?
        """
        params.append(limit)

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_student_charge_state(
        self,
        *,
        organization_id: int,
        billing_student_id: int,
        school_year: str,
    ) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM billing_student_charge_state
                WHERE organization_id = ?
                  AND billing_student_id = ?
                  AND school_year = ?
                """,
                (organization_id, billing_student_id, school_year),
            ).fetchone()
        return dict(row) if row else None

    def create_student_charge_state(self, payload: dict[str, Any]) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO billing_student_charge_state (
                    organization_id, billing_student_id, school_year, intro_free_lessons_remaining,
                    sibling_discount_remaining_amount, sibling_discount_initialized, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["organization_id"],
                    payload["billing_student_id"],
                    payload["school_year"],
                    int(payload.get("intro_free_lessons_remaining", 0)),
                    float(payload.get("sibling_discount_remaining_amount", 0)),
                    int(payload.get("sibling_discount_initialized", 0)),
                    timestamp,
                    timestamp,
                ),
                "billing_student_charge_state_id",
            )

    def update_student_charge_state(self, billing_student_charge_state_id: int, fields: dict[str, Any]) -> None:
        if not fields:
            return
        allowed = {
            "intro_free_lessons_remaining",
            "sibling_discount_remaining_amount",
            "sibling_discount_initialized",
        }
        update_fields = {key: value for key, value in fields.items() if key in allowed}
        if not update_fields:
            return

        update_fields["updated_at"] = now_iso()
        assignments = ", ".join(f"{key} = ?" for key in update_fields)
        values = list(update_fields.values()) + [billing_student_charge_state_id]

        with get_connection() as connection:
            connection.execute(
                f"UPDATE billing_student_charge_state SET {assignments} WHERE billing_student_charge_state_id = ?",
                values,
            )

    def get_payer_charge_state(
        self,
        *,
        organization_id: int,
        billing_payer_id: int,
        school_year: str,
    ) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM billing_payer_charge_state
                WHERE organization_id = ?
                  AND billing_payer_id = ?
                  AND school_year = ?
                """,
                (organization_id, billing_payer_id, school_year),
            ).fetchone()
        return dict(row) if row else None

    def create_payer_charge_state(self, payload: dict[str, Any]) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO billing_payer_charge_state (
                    organization_id, billing_payer_id, school_year, large_family_discount_remaining_amount,
                    large_family_discount_initialized, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["organization_id"],
                    payload["billing_payer_id"],
                    payload["school_year"],
                    float(payload.get("large_family_discount_remaining_amount", 0)),
                    int(payload.get("large_family_discount_initialized", 0)),
                    timestamp,
                    timestamp,
                ),
                "billing_payer_charge_state_id",
            )

    def update_payer_charge_state(self, billing_payer_charge_state_id: int, fields: dict[str, Any]) -> None:
        if not fields:
            return
        allowed = {
            "large_family_discount_remaining_amount",
            "large_family_discount_initialized",
        }
        update_fields = {key: value for key, value in fields.items() if key in allowed}
        if not update_fields:
            return

        update_fields["updated_at"] = now_iso()
        assignments = ", ".join(f"{key} = ?" for key in update_fields)
        values = list(update_fields.values()) + [billing_payer_charge_state_id]

        with get_connection() as connection:
            connection.execute(
                f"UPDATE billing_payer_charge_state SET {assignments} WHERE billing_payer_charge_state_id = ?",
                values,
            )

    def list_recent_incoming_transactions(
        self,
        organization_id: int | None = None,
        limit: int = 5000,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT
                t.billing_transaction_id,
                t.organization_id,
                t.booking_date,
                t.amount,
                t.currency,
                t.title,
                t.reference,
                t.counterparty_name,
                t.counterparty_account
            FROM billing_transactions t
            WHERE t.direction = 'uznanie'
        """
        params: list[Any] = []
        if organization_id is not None:
            query += " AND t.organization_id = ?"
            params.append(organization_id)

        query += """
            ORDER BY t.booking_date DESC, t.billing_transaction_id DESC
            LIMIT ?
        """
        params.append(limit)

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def list_schools(
        self,
        organization_id: int | None = None,
        only_active: bool = False,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT
                s.*,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM billing_schools s
            LEFT JOIN organizations o ON o.organization_id = s.organization_id
        """
        conditions: list[str] = []
        params: list[Any] = []

        if organization_id is not None:
            conditions.append("s.organization_id = ?")
            params.append(organization_id)
        if only_active:
            conditions.append("s.is_active = 1")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY s.is_active DESC, s.short_name ASC, s.full_name ASC, s.billing_school_id ASC"

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_school_by_id(
        self,
        billing_school_id: int,
        organization_id: int | None = None,
    ) -> dict[str, Any] | None:
        query = """
            SELECT
                s.*,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM billing_schools s
            LEFT JOIN organizations o ON o.organization_id = s.organization_id
            WHERE s.billing_school_id = ?
        """
        params: list[Any] = [billing_school_id]
        if organization_id is not None:
            query += " AND s.organization_id = ?"
            params.append(organization_id)

        with get_connection() as connection:
            row = connection.execute(query, params).fetchone()
        return dict(row) if row else None

    def get_school_by_full_name(
        self,
        full_name: str,
        organization_id: int,
    ) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM billing_schools
                WHERE organization_id = ?
                  AND full_name = ?
                """,
                (organization_id, full_name),
            ).fetchone()
        return dict(row) if row else None

    def get_school_by_short_name(
        self,
        short_name: str,
        organization_id: int,
    ) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM billing_schools
                WHERE organization_id = ?
                  AND short_name = ?
                """,
                (organization_id, short_name),
            ).fetchone()
        return dict(row) if row else None

    def create_school(self, payload: dict[str, Any]) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO billing_schools (
                    organization_id, full_name, short_name, city, notes, is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["organization_id"],
                    payload["full_name"],
                    payload["short_name"],
                    payload.get("city"),
                    payload.get("notes"),
                    int(payload.get("is_active", 1)),
                    timestamp,
                    timestamp,
                ),
                "billing_school_id",
            )

    def list_bank_accounts(
        self,
        organization_id: int | None = None,
        only_active: bool = False,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT
                a.*,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM billing_bank_accounts a
            LEFT JOIN organizations o ON o.organization_id = a.organization_id
        """
        conditions: list[str] = []
        params: list[Any] = []

        if organization_id is not None:
            conditions.append("a.organization_id = ?")
            params.append(organization_id)
        if only_active:
            conditions.append("a.is_active = 1")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY a.is_active DESC, a.account_name ASC, a.billing_bank_account_id ASC"

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_bank_account_by_id(
        self,
        billing_bank_account_id: int,
        organization_id: int | None = None,
    ) -> dict[str, Any] | None:
        query = """
            SELECT
                a.*,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM billing_bank_accounts a
            LEFT JOIN organizations o ON o.organization_id = a.organization_id
            WHERE a.billing_bank_account_id = ?
        """
        params: list[Any] = [billing_bank_account_id]
        if organization_id is not None:
            query += " AND a.organization_id = ?"
            params.append(organization_id)

        with get_connection() as connection:
            row = connection.execute(query, params).fetchone()
        return dict(row) if row else None

    def get_bank_account_by_iban(
        self,
        iban: str,
        organization_id: int | None = None,
    ) -> dict[str, Any] | None:
        query = """
            SELECT
                a.*,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM billing_bank_accounts a
            LEFT JOIN organizations o ON o.organization_id = a.organization_id
            WHERE a.iban = ?
        """
        params: list[Any] = [iban]
        if organization_id is not None:
            query += " AND a.organization_id = ?"
            params.append(organization_id)

        with get_connection() as connection:
            row = connection.execute(query, params).fetchone()
        return dict(row) if row else None

    def create_bank_account(self, payload: dict[str, Any]) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO billing_bank_accounts (
                    organization_id, account_name, bank_name, iban, currency, is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["organization_id"],
                    payload["account_name"],
                    payload.get("bank_name"),
                    payload["iban"],
                    payload.get("currency", "PLN"),
                    int(payload.get("is_active", 1)),
                    timestamp,
                    timestamp,
                ),
                "billing_bank_account_id",
            )

    def create_statement_import(self, payload: dict[str, Any]) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO billing_statement_imports (
                    organization_id, billing_bank_account_id, source_type, source_file_name,
                    imported_by_user_id, imported_at, row_count, imported_transaction_count,
                    skipped_transaction_count, status, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["organization_id"],
                    payload["billing_bank_account_id"],
                    payload["source_type"],
                    payload.get("source_file_name"),
                    payload.get("imported_by_user_id"),
                    payload.get("imported_at", timestamp),
                    int(payload.get("row_count", 0)),
                    int(payload.get("imported_transaction_count", 0)),
                    int(payload.get("skipped_transaction_count", 0)),
                    payload["status"],
                    payload.get("notes"),
                    timestamp,
                    timestamp,
                ),
                "billing_statement_import_id",
            )

    def update_statement_import(self, billing_statement_import_id: int, fields: dict[str, Any]) -> None:
        if not fields:
            return
        allowed = {
            "row_count",
            "imported_transaction_count",
            "skipped_transaction_count",
            "status",
            "notes",
        }
        update_fields = {key: value for key, value in fields.items() if key in allowed}
        if not update_fields:
            return

        update_fields["updated_at"] = now_iso()
        assignments = ", ".join(f"{key} = ?" for key in update_fields)
        values = list(update_fields.values()) + [billing_statement_import_id]

        with get_connection() as connection:
            connection.execute(
                f"UPDATE billing_statement_imports SET {assignments} WHERE billing_statement_import_id = ?",
                values,
            )

    def get_statement_import_by_id(
        self,
        billing_statement_import_id: int,
        organization_id: int | None = None,
    ) -> dict[str, Any] | None:
        query = """
            SELECT
                si.*,
                a.account_name,
                a.iban,
                o.name AS organization_name,
                o.slug AS organization_slug,
                u.login AS imported_by_login,
                u.display_name AS imported_by_name
            FROM billing_statement_imports si
            JOIN billing_bank_accounts a ON a.billing_bank_account_id = si.billing_bank_account_id
            LEFT JOIN organizations o ON o.organization_id = si.organization_id
            LEFT JOIN users u ON u.user_id = si.imported_by_user_id
            WHERE si.billing_statement_import_id = ?
        """
        params: list[Any] = [billing_statement_import_id]
        if organization_id is not None:
            query += " AND si.organization_id = ?"
            params.append(organization_id)

        with get_connection() as connection:
            row = connection.execute(query, params).fetchone()
        return dict(row) if row else None

    def get_transaction_by_hash(
        self,
        *,
        organization_id: int,
        billing_bank_account_id: int,
        transaction_hash: str,
    ) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM billing_transactions
                WHERE organization_id = ?
                  AND billing_bank_account_id = ?
                  AND transaction_hash = ?
                """,
                (organization_id, billing_bank_account_id, transaction_hash),
            ).fetchone()
        return dict(row) if row else None

    def get_transaction_by_id(
        self,
        billing_transaction_id: int,
        organization_id: int | None = None,
    ) -> dict[str, Any] | None:
        params: list[Any] = [billing_transaction_id]
        query = """
            SELECT
                t.*,
                a.account_name,
                a.iban,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM billing_transactions t
            JOIN billing_bank_accounts a ON a.billing_bank_account_id = t.billing_bank_account_id
            LEFT JOIN organizations o ON o.organization_id = t.organization_id
            WHERE t.billing_transaction_id = ?
        """
        if organization_id is not None:
            query += " AND t.organization_id = ?"
            params.append(organization_id)
        with get_connection() as connection:
            row = connection.execute(query, params).fetchone()
        return dict(row) if row else None

    def create_transaction(self, payload: dict[str, Any]) -> int:
        timestamp = now_iso()
        raw_data = payload.get("raw_data")
        serialized_raw_data = raw_data if isinstance(raw_data, str) else json_dumps(raw_data or {})
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO billing_transactions (
                    organization_id, billing_bank_account_id, billing_statement_import_id, booking_date,
                    value_date, amount, currency, direction, counterparty_name, counterparty_account,
                    title, reference, raw_data, transaction_hash, matched_status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["organization_id"],
                    payload["billing_bank_account_id"],
                    payload.get("billing_statement_import_id"),
                    payload["booking_date"],
                    payload.get("value_date"),
                    float(payload["amount"]),
                    payload.get("currency", "PLN"),
                    payload["direction"],
                    payload.get("counterparty_name"),
                    payload.get("counterparty_account"),
                    payload.get("title"),
                    payload.get("reference"),
                    serialized_raw_data,
                    payload["transaction_hash"],
                    payload.get("matched_status", "nieprzypisana"),
                    timestamp,
                    timestamp,
                ),
                "billing_transaction_id",
            )

    def update_transaction(self, billing_transaction_id: int, fields: dict[str, Any]) -> None:
        if not fields:
            return
        allowed = {
            "booking_date",
            "value_date",
            "amount",
            "currency",
            "direction",
            "counterparty_name",
            "counterparty_account",
            "title",
            "reference",
            "raw_data",
            "transaction_hash",
            "matched_status",
        }
        update_fields = {key: value for key, value in fields.items() if key in allowed}
        if not update_fields:
            return
        if "raw_data" in update_fields and not isinstance(update_fields["raw_data"], str):
            update_fields["raw_data"] = json_dumps(update_fields["raw_data"])
        update_fields["updated_at"] = now_iso()
        assignments = ", ".join(f"{key} = ?" for key in update_fields)
        values = list(update_fields.values()) + [billing_transaction_id]
        with get_connection() as connection:
            connection.execute(
                f"UPDATE billing_transactions SET {assignments} WHERE billing_transaction_id = ?",
                values,
            )

    def list_transactions(
        self,
        *,
        organization_id: int | None = None,
        billing_bank_account_id: int | None = None,
        matched_status: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT
                t.*,
                a.account_name,
                a.iban,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM billing_transactions t
            JOIN billing_bank_accounts a ON a.billing_bank_account_id = t.billing_bank_account_id
            LEFT JOIN organizations o ON o.organization_id = t.organization_id
        """
        conditions: list[str] = []
        params: list[Any] = []

        if organization_id is not None:
            conditions.append("t.organization_id = ?")
            params.append(organization_id)
        if billing_bank_account_id is not None:
            conditions.append("t.billing_bank_account_id = ?")
            params.append(billing_bank_account_id)
        if matched_status:
            conditions.append("t.matched_status = ?")
            params.append(matched_status)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += """
            ORDER BY t.booking_date DESC, t.billing_transaction_id DESC
            LIMIT ?
        """
        params.append(limit)

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def search_bank_accounts(
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
        params: list[Any] = [value, value, value, value, value]
        query = """
            SELECT
                a.*,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM billing_bank_accounts a
            LEFT JOIN organizations o ON o.organization_id = a.organization_id
            WHERE (
                LOWER(COALESCE(a.account_name, '')) LIKE ?
                OR LOWER(COALESCE(a.bank_name, '')) LIKE ?
                OR LOWER(COALESCE(a.iban, '')) LIKE ?
                OR LOWER(COALESCE(a.currency, '')) LIKE ?
                OR LOWER(COALESCE(o.name, '')) LIKE ?
            )
              AND COALESCE(o.is_active, 1) = 1
        """
        if organization_id is not None:
            query += " AND a.organization_id = ?"
            params.append(organization_id)
        query += """
            ORDER BY a.is_active DESC, a.updated_at DESC, a.billing_bank_account_id DESC
            LIMIT ?
        """
        params.append(limit)

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def search_transactions(
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
        params: list[Any] = [value, value, value, value, value, value, value, value, value, value, value, value]
        query = """
            SELECT
                t.*,
                a.account_name,
                a.iban,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM billing_transactions t
            JOIN billing_bank_accounts a ON a.billing_bank_account_id = t.billing_bank_account_id
            LEFT JOIN organizations o ON o.organization_id = t.organization_id
            WHERE (
                CAST(t.billing_transaction_id AS TEXT) LIKE ?
                OR LOWER(COALESCE(t.reference, '')) LIKE ?
                OR LOWER(COALESCE(t.title, '')) LIKE ?
                OR LOWER(COALESCE(t.counterparty_name, '')) LIKE ?
                OR LOWER(COALESCE(t.counterparty_account, '')) LIKE ?
                OR LOWER(COALESCE(t.matched_status, '')) LIKE ?
                OR COALESCE(t.booking_date, '') LIKE ?
                OR COALESCE(t.value_date, '') LIKE ?
                OR CAST(COALESCE(t.amount, '') AS TEXT) LIKE ?
                OR LOWER(COALESCE(a.account_name, '')) LIKE ?
                OR LOWER(COALESCE(a.iban, '')) LIKE ?
                OR LOWER(COALESCE(o.name, '')) LIKE ?
            )
              AND COALESCE(o.is_active, 1) = 1
        """
        if organization_id is not None:
            query += " AND t.organization_id = ?"
            params.append(organization_id)
        query += """
            ORDER BY t.booking_date DESC, t.billing_transaction_id DESC
            LIMIT ?
        """
        params.append(limit)

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]
