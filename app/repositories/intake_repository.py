from __future__ import annotations

from typing import Any

from app.db import execute_insert_returning_id, get_connection
from app.utils import now_iso


class IntakeRepository:
    def list_forms(self, organization_id: int | None = None, *, include_inactive: bool = False) -> list[dict[str, Any]]:
        params: list[Any] = []
        conditions = []
        if organization_id is not None:
            conditions.append("f.organization_id = ?")
            params.append(organization_id)
        if not include_inactive:
            conditions.append("COALESCE(f.is_public, 1) = 1")

        query = """
            SELECT
                f.*,
                COALESCE(creator.display_name, creator.login) AS created_by_user_name,
                COALESCE(assignee.display_name, assignee.login) AS default_assigned_user_name,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM intake_forms f
            LEFT JOIN users creator ON creator.user_id = f.created_by_user_id
            LEFT JOIN users assignee ON assignee.user_id = f.default_assigned_user_id
            LEFT JOIN organizations o ON o.organization_id = f.organization_id
        """
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY f.is_public DESC, f.form_name ASC, f.intake_form_id ASC"
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_form_by_id(self, intake_form_id: int, organization_id: int | None = None) -> dict[str, Any] | None:
        params: list[Any] = [intake_form_id]
        query = """
            SELECT
                f.*,
                COALESCE(creator.display_name, creator.login) AS created_by_user_name,
                COALESCE(assignee.display_name, assignee.login) AS default_assigned_user_name,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM intake_forms f
            LEFT JOIN users creator ON creator.user_id = f.created_by_user_id
            LEFT JOIN users assignee ON assignee.user_id = f.default_assigned_user_id
            LEFT JOIN organizations o ON o.organization_id = f.organization_id
            WHERE f.intake_form_id = ?
        """
        if organization_id is not None:
            query += " AND f.organization_id = ?"
            params.append(organization_id)
        with get_connection() as connection:
            row = connection.execute(query, params).fetchone()
        return dict(row) if row else None

    def get_form_by_slug(self, organization_id: int, form_slug: str) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM intake_forms
                WHERE organization_id = ?
                  AND form_slug = ?
                """,
                (organization_id, form_slug),
            ).fetchone()
        return dict(row) if row else None

    def get_form_by_token(self, public_token: str) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM intake_forms
                WHERE public_token = ?
                """,
                (public_token,),
            ).fetchone()
        return dict(row) if row else None

    def create_form(self, payload: dict[str, Any]) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO intake_forms (
                    organization_id, form_name, form_slug, description, field_schema_json, is_public,
                    allow_attachments, default_priority, default_assigned_user_id, public_token,
                    created_by_user_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["organization_id"],
                    payload["form_name"],
                    payload["form_slug"],
                    payload.get("description"),
                    payload.get("field_schema_json") or "[]",
                    int(payload.get("is_public", 1)),
                    int(payload.get("allow_attachments", 1)),
                    payload.get("default_priority") or "normalny",
                    payload.get("default_assigned_user_id"),
                    payload["public_token"],
                    payload.get("created_by_user_id"),
                    timestamp,
                    timestamp,
                ),
                "intake_form_id",
            )

    def update_form(self, intake_form_id: int, fields: dict[str, Any]) -> None:
        if not fields:
            return
        allowed = {
            "form_name",
            "form_slug",
            "description",
            "field_schema_json",
            "is_public",
            "allow_attachments",
            "default_priority",
            "default_assigned_user_id",
            "public_token",
        }
        update_fields = {key: value for key, value in fields.items() if key in allowed}
        if not update_fields:
            return
        update_fields["updated_at"] = now_iso()
        assignments = ", ".join(f"{key} = ?" for key in update_fields)
        values = list(update_fields.values()) + [intake_form_id]
        with get_connection() as connection:
            connection.execute(
                f"UPDATE intake_forms SET {assignments} WHERE intake_form_id = ?",
                values,
            )

    def list_items(
        self,
        *,
        organization_id: int | None = None,
        status: str | None = None,
        source_kind: str | None = None,
        search: str | None = None,
        assigned_user_id: int | None = None,
        created_by_user_id: int | None = None,
        linked_invoice_id: int | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        params: list[Any] = []
        conditions = []
        if organization_id is not None:
            conditions.append("i.organization_id = ?")
            params.append(organization_id)
        if status:
            conditions.append("i.status = ?")
            params.append(status)
        if source_kind:
            conditions.append("i.source_kind = ?")
            params.append(source_kind)
        if assigned_user_id is not None:
            conditions.append("i.assigned_user_id = ?")
            params.append(assigned_user_id)
        if created_by_user_id is not None:
            conditions.append("i.created_by_user_id = ?")
            params.append(created_by_user_id)
        if linked_invoice_id is not None:
            conditions.append("i.linked_invoice_id = ?")
            params.append(linked_invoice_id)
        normalized_search = str(search or "").strip().lower()
        if normalized_search:
            like = f"%{normalized_search}%"
            conditions.append(
                """
                (
                    CAST(i.intake_item_id AS TEXT) LIKE ?
                    OR LOWER(COALESCE(i.title, '')) LIKE ?
                    OR LOWER(COALESCE(i.description, '')) LIKE ?
                    OR LOWER(COALESCE(i.requester_name, '')) LIKE ?
                    OR LOWER(COALESCE(i.requester_email, '')) LIKE ?
                    OR LOWER(COALESCE(i.source_reference, '')) LIKE ?
                    OR LOWER(COALESCE(f.form_name, '')) LIKE ?
                )
                """
            )
            params.extend([like] * 7)

        query = """
            SELECT
                i.*,
                f.form_name,
                f.form_slug,
                f.public_token,
                f.allow_attachments,
                COALESCE(assignee.display_name, assignee.login) AS assigned_user_name,
                COALESCE(creator.display_name, creator.login) AS created_by_user_name,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM intake_items i
            LEFT JOIN intake_forms f ON f.intake_form_id = i.intake_form_id
            LEFT JOIN users assignee ON assignee.user_id = i.assigned_user_id
            LEFT JOIN users creator ON creator.user_id = i.created_by_user_id
            LEFT JOIN organizations o ON o.organization_id = i.organization_id
        """
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY i.last_activity_at DESC, i.updated_at DESC, i.intake_item_id DESC LIMIT ?"
        params.append(max(1, int(limit)))
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_item_by_id(
        self,
        intake_item_id: int,
        organization_id: int | None = None,
        *,
        created_by_user_id: int | None = None,
    ) -> dict[str, Any] | None:
        params: list[Any] = [intake_item_id]
        query = """
            SELECT
                i.*,
                f.form_name,
                f.form_slug,
                f.public_token,
                f.allow_attachments,
                COALESCE(assignee.display_name, assignee.login) AS assigned_user_name,
                COALESCE(creator.display_name, creator.login) AS created_by_user_name,
                o.name AS organization_name,
                o.slug AS organization_slug
            FROM intake_items i
            LEFT JOIN intake_forms f ON f.intake_form_id = i.intake_form_id
            LEFT JOIN users assignee ON assignee.user_id = i.assigned_user_id
            LEFT JOIN users creator ON creator.user_id = i.created_by_user_id
            LEFT JOIN organizations o ON o.organization_id = i.organization_id
            WHERE i.intake_item_id = ?
        """
        if organization_id is not None:
            query += " AND i.organization_id = ?"
            params.append(organization_id)
        if created_by_user_id is not None:
            query += " AND i.created_by_user_id = ?"
            params.append(created_by_user_id)
        with get_connection() as connection:
            row = connection.execute(query, params).fetchone()
        return dict(row) if row else None

    def create_item(self, payload: dict[str, Any]) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO intake_items (
                    organization_id, intake_form_id, source_kind, status, priority, title, description,
                    requester_name, requester_email, source_reference, due_at, metadata_json, assigned_user_id,
                    linked_task_id, linked_invoice_id, created_by_user_id, last_activity_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["organization_id"],
                    payload.get("intake_form_id"),
                    payload["source_kind"],
                    payload.get("status") or "nowe",
                    payload.get("priority") or "normalny",
                    payload["title"],
                    payload.get("description"),
                    payload.get("requester_name"),
                    payload.get("requester_email"),
                    payload.get("source_reference"),
                    payload.get("due_at"),
                    payload.get("metadata_json") or "{}",
                    payload.get("assigned_user_id"),
                    payload.get("linked_task_id"),
                    payload.get("linked_invoice_id"),
                    payload.get("created_by_user_id"),
                    payload.get("last_activity_at") or timestamp,
                    timestamp,
                    timestamp,
                ),
                "intake_item_id",
            )

    def update_item(self, intake_item_id: int, fields: dict[str, Any]) -> None:
        if not fields:
            return
        allowed = {
            "intake_form_id",
            "source_kind",
            "status",
            "priority",
            "title",
            "description",
            "requester_name",
            "requester_email",
            "source_reference",
            "due_at",
            "metadata_json",
            "assigned_user_id",
            "linked_task_id",
            "linked_invoice_id",
            "last_activity_at",
        }
        update_fields = {key: value for key, value in fields.items() if key in allowed}
        if not update_fields:
            return
        update_fields["updated_at"] = now_iso()
        assignments = ", ".join(f"{key} = ?" for key in update_fields)
        values = list(update_fields.values()) + [intake_item_id]
        with get_connection() as connection:
            connection.execute(
                f"UPDATE intake_items SET {assignments} WHERE intake_item_id = ?",
                values,
            )

    def create_comment(self, payload: dict[str, Any]) -> int:
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO intake_item_comments (
                    intake_item_id, organization_id, parent_comment_id, note_text, mentioned_user_ids,
                    mentioned_user_names, created_by_user_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["intake_item_id"],
                    payload["organization_id"],
                    payload.get("parent_comment_id"),
                    payload["note_text"],
                    payload.get("mentioned_user_ids"),
                    payload.get("mentioned_user_names"),
                    payload["created_by_user_id"],
                    now_iso(),
                ),
                "intake_item_comment_id",
            )

    def list_comments(self, intake_item_id: int) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    c.*,
                    COALESCE(u.display_name, u.login) AS created_by_user_name
                FROM intake_item_comments c
                LEFT JOIN users u ON u.user_id = c.created_by_user_id
                WHERE c.intake_item_id = ?
                ORDER BY c.created_at ASC, c.intake_item_comment_id ASC
                """,
                (intake_item_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def create_history(self, payload: dict[str, Any]) -> int:
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO intake_item_history (
                    intake_item_id, organization_id, action_type, actor, message, details, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["intake_item_id"],
                    payload["organization_id"],
                    payload["action_type"],
                    payload["actor"],
                    payload["message"],
                    payload.get("details"),
                    now_iso(),
                ),
                "intake_item_history_id",
            )

    def list_history(self, intake_item_id: int) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM intake_item_history
                WHERE intake_item_id = ?
                ORDER BY created_at DESC, intake_item_history_id DESC
                """,
                (intake_item_id,),
            ).fetchall()
        return [dict(row) for row in rows]
