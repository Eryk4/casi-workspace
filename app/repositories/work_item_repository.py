from __future__ import annotations

from typing import Any

from app.db import execute_insert_returning_id, get_connection
from app.utils import now_iso, now_local_datetime_value


class WorkItemRepository:
    def list_work_items(
        self,
        filters: dict[str, Any] | None = None,
        *,
        organization_id: int | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        filters = filters or {}
        params: list[Any] = []
        conditions = ["COALESCE(o.is_active, 1) = 1"]
        now_value = str(filters.get("now_value") or "").strip() or now_local_datetime_value()

        if organization_id is not None:
            conditions.append("w.organization_id = ?")
            params.append(int(organization_id))

        search = str(filters.get("search") or "").strip()
        if search:
            like = f"%{search}%"
            conditions.append(
                """
                (
                    CAST(w.work_item_id AS TEXT) LIKE ?
                    OR COALESCE(w.title, '') LIKE ?
                    OR COALESCE(w.description, '') LIKE ?
                    OR COALESCE(assignee.display_name, assignee.login, '') LIKE ?
                    OR COALESCE(creator.display_name, creator.login, '') LIKE ?
                )
                """
            )
            params.extend([like, like, like, like, like])

        for key, column in {
            "status": "w.status",
            "priority_level": "w.priority_level",
            "sla_stage": "w.sla_stage",
            "source_type": "w.source_type",
        }.items():
            value = str(filters.get(key) or "").strip()
            if value:
                conditions.append(f"{column} = ?")
                params.append(value)

        assigned_user_id = filters.get("assigned_user_id")
        if assigned_user_id not in (None, ""):
            try:
                normalized_assigned_user_id = int(assigned_user_id)
            except (TypeError, ValueError):
                normalized_assigned_user_id = 0
            if normalized_assigned_user_id > 0:
                conditions.append("w.assigned_user_id = ?")
                params.append(normalized_assigned_user_id)

        only_open = str(filters.get("only_open") or "").strip().lower()
        if only_open in {"1", "true", "tak", "yes"}:
            conditions.append("w.status NOT IN ('zamkniete', 'anulowane')")

        unassigned_only = str(filters.get("unassigned_only") or "").strip().lower()
        if unassigned_only in {"1", "true", "tak", "yes"}:
            conditions.append("w.assigned_user_id IS NULL")

        due_before = str(filters.get("due_before") or "").strip()
        if due_before:
            conditions.append("COALESCE(w.due_at, '') <> ''")
            conditions.append("w.due_at <= ?")
            params.append(due_before)

        due_overdue_only = str(filters.get("due_overdue_only") or "").strip().lower()
        if due_overdue_only in {"1", "true", "tak", "yes"}:
            conditions.append("w.status NOT IN ('zamkniete', 'anulowane')")
            conditions.append("COALESCE(w.due_at, '') <> ''")
            conditions.append("w.due_at <= ?")
            params.append(now_value)

        sla_overdue_only = str(filters.get("sla_overdue_only") or "").strip().lower()
        if sla_overdue_only in {"1", "true", "tak", "yes"}:
            conditions.append("w.status NOT IN ('zamkniete', 'anulowane')")
            conditions.append("COALESCE(w.sla_deadline_at, '') <> ''")
            conditions.append("w.sla_deadline_at <= ?")
            params.append(now_value)

        sort_by_raw = str(filters.get("sort_by") or "").strip().lower()
        sort_dir_raw = str(filters.get("sort_dir") or "").strip().lower()
        sort_direction = "ASC" if sort_dir_raw == "asc" else "DESC"
        allowed_sort_columns = {
            "priority_score": "w.priority_score",
            "sla_deadline_at": "w.sla_deadline_at",
            "due_at": "w.due_at",
            "updated_at": "w.updated_at",
            "created_at": "w.created_at",
        }
        sort_column = allowed_sort_columns.get(sort_by_raw)

        query = """
            SELECT
                w.*,
                o.name AS organization_name,
                o.slug AS organization_slug,
                COALESCE(assignee.display_name, assignee.login) AS assigned_user_name,
                assignee.telegram_user_id AS assigned_telegram_user_id,
                COALESCE(creator.display_name, creator.login) AS created_by_user_name,
                COALESCE(updater.display_name, updater.login) AS updated_by_user_name
            FROM work_items w
            JOIN organizations o ON o.organization_id = w.organization_id
            LEFT JOIN users assignee ON assignee.user_id = w.assigned_user_id
            LEFT JOIN users creator ON creator.user_id = w.created_by_user_id
            LEFT JOIN users updater ON updater.user_id = w.updated_by_user_id
        """
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += """
            ORDER BY
                CASE
                    WHEN w.status IN ('zamkniete', 'anulowane') THEN 1
                    ELSE 0
                END,
        """
        if sort_column:
            if sort_column in {"w.sla_deadline_at", "w.due_at"}:
                query += f"""
                CASE
                    WHEN COALESCE({sort_column}, '') = '' THEN 1
                    ELSE 0
                END ASC,
                {sort_column} {sort_direction},
                """
            else:
                query += f"{sort_column} {sort_direction},"
        else:
            query += """
                w.priority_score DESC,
                CASE
                    WHEN COALESCE(w.sla_deadline_at, '') = '' THEN 1
                    ELSE 0
                END,
                w.sla_deadline_at ASC,
            """
        query += """
                w.updated_at DESC,
                w.work_item_id DESC
            LIMIT ?
        """
        params.append(max(1, int(limit)))

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_by_id(
        self,
        work_item_id: int,
        *,
        organization_id: int | None = None,
    ) -> dict[str, Any] | None:
        params: list[Any] = [int(work_item_id)]
        query = """
            SELECT
                w.*,
                o.name AS organization_name,
                o.slug AS organization_slug,
                COALESCE(assignee.display_name, assignee.login) AS assigned_user_name,
                assignee.telegram_user_id AS assigned_telegram_user_id,
                COALESCE(creator.display_name, creator.login) AS created_by_user_name,
                COALESCE(updater.display_name, updater.login) AS updated_by_user_name
            FROM work_items w
            JOIN organizations o ON o.organization_id = w.organization_id
            LEFT JOIN users assignee ON assignee.user_id = w.assigned_user_id
            LEFT JOIN users creator ON creator.user_id = w.created_by_user_id
            LEFT JOIN users updater ON updater.user_id = w.updated_by_user_id
            WHERE w.work_item_id = ?
              AND COALESCE(o.is_active, 1) = 1
        """
        if organization_id is not None:
            query += " AND w.organization_id = ?"
            params.append(int(organization_id))

        with get_connection() as connection:
            row = connection.execute(query, params).fetchone()
        return dict(row) if row else None

    def create(self, payload: dict[str, Any]) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO work_items (
                    organization_id,
                    source_type,
                    source_id,
                    title,
                    description,
                    status,
                    priority_level,
                    priority_score,
                    assigned_user_id,
                    created_by_user_id,
                    updated_by_user_id,
                    due_at,
                    sla_deadline_at,
                    sla_warning_minutes,
                    sla_warning_at,
                    sla_stage,
                    reminder_sent_at,
                    escalation_sent_at,
                    resolved_at,
                    last_sla_transition_at,
                    metadata_json,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(payload["organization_id"]),
                    payload.get("source_type") or "manual",
                    payload.get("source_id"),
                    payload["title"],
                    payload.get("description"),
                    payload.get("status") or "nowe",
                    payload.get("priority_level") or "normalny",
                    float(payload.get("priority_score") or 0),
                    payload.get("assigned_user_id"),
                    int(payload["created_by_user_id"]),
                    payload.get("updated_by_user_id"),
                    payload.get("due_at"),
                    payload.get("sla_deadline_at"),
                    int(payload.get("sla_warning_minutes") or 120),
                    payload.get("sla_warning_at"),
                    payload.get("sla_stage") or "on_track",
                    payload.get("reminder_sent_at"),
                    payload.get("escalation_sent_at"),
                    payload.get("resolved_at"),
                    payload.get("last_sla_transition_at"),
                    payload.get("metadata_json") or "{}",
                    timestamp,
                    timestamp,
                ),
                "work_item_id",
            )

    def update(self, work_item_id: int, fields: dict[str, Any]) -> None:
        if not fields:
            return
        allowed = {
            "source_type",
            "source_id",
            "title",
            "description",
            "status",
            "priority_level",
            "priority_score",
            "assigned_user_id",
            "updated_by_user_id",
            "due_at",
            "sla_deadline_at",
            "sla_warning_minutes",
            "sla_warning_at",
            "sla_stage",
            "reminder_sent_at",
            "escalation_sent_at",
            "resolved_at",
            "last_sla_transition_at",
            "metadata_json",
        }
        update_fields = {key: value for key, value in fields.items() if key in allowed}
        if not update_fields:
            return
        update_fields["updated_at"] = now_iso()
        assignments = ", ".join(f"{key} = ?" for key in update_fields)
        values = list(update_fields.values()) + [int(work_item_id)]
        with get_connection() as connection:
            connection.execute(f"UPDATE work_items SET {assignments} WHERE work_item_id = ?", values)

    def create_history(self, payload: dict[str, Any]) -> int:
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO work_item_history (
                    work_item_id,
                    organization_id,
                    action_type,
                    actor,
                    message,
                    details,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(payload["work_item_id"]),
                    int(payload["organization_id"]),
                    payload["action_type"],
                    payload["actor"],
                    payload["message"],
                    payload.get("details"),
                    now_iso(),
                ),
                "work_item_history_id",
            )

    def list_history(self, work_item_id: int) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM work_item_history
                WHERE work_item_id = ?
                ORDER BY created_at DESC, work_item_history_id DESC
                """,
                (int(work_item_id),),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_due_sla_candidates(
        self,
        *,
        now_value: str,
        organization_id: int | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        params: list[Any] = [now_value, now_value]
        conditions = [
            "COALESCE(o.is_active, 1) = 1",
            "w.status NOT IN ('zamkniete', 'anulowane')",
            """
            (
                (
                    w.sla_stage IN ('on_track')
                    AND COALESCE(w.sla_warning_at, '') <> ''
                    AND COALESCE(w.sla_warning_at, '') <= ?
                )
                OR
                (
                    w.sla_stage IN ('on_track', 'warning', 'breached')
                    AND COALESCE(w.sla_deadline_at, '') <> ''
                    AND COALESCE(w.sla_deadline_at, '') <= ?
                )
            )
            """,
        ]
        if organization_id is not None:
            conditions.append("w.organization_id = ?")
            params.append(int(organization_id))

        query = f"""
            SELECT
                w.*,
                o.name AS organization_name,
                o.slug AS organization_slug,
                COALESCE(assignee.display_name, assignee.login) AS assigned_user_name,
                COALESCE(creator.display_name, creator.login) AS created_by_user_name
            FROM work_items w
            JOIN organizations o ON o.organization_id = w.organization_id
            LEFT JOIN users assignee ON assignee.user_id = w.assigned_user_id
            LEFT JOIN users creator ON creator.user_id = w.created_by_user_id
            WHERE {' AND '.join(conditions)}
            ORDER BY
                COALESCE(w.sla_deadline_at, '') ASC,
                w.priority_score DESC,
                w.work_item_id ASC
            LIMIT ?
        """
        params.append(max(1, int(limit)))
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def assignee_workload(
        self,
        *,
        organization_id: int | None = None,
        now_value: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        params: list[Any] = [now_value, now_value]
        conditions = [
            "COALESCE(o.is_active, 1) = 1",
            "w.status NOT IN ('zamkniete', 'anulowane')",
        ]
        if organization_id is not None:
            conditions.append("w.organization_id = ?")
            params.append(int(organization_id))

        query = f"""
            SELECT
                COALESCE(w.assigned_user_id, 0) AS assigned_user_id,
                CASE
                    WHEN w.assigned_user_id IS NULL THEN 'Nieprzypisane'
                    ELSE COALESCE(u.display_name, u.login, 'Uzytkownik')
                END AS assigned_user_name,
                COUNT(*) AS open_items,
                SUM(CASE WHEN w.sla_stage = 'escalated' THEN 1 ELSE 0 END) AS escalated_items,
                SUM(CASE WHEN w.sla_stage = 'warning' THEN 1 ELSE 0 END) AS warning_items,
                SUM(CASE WHEN COALESCE(w.sla_deadline_at, '') <> '' AND w.sla_deadline_at <= ? THEN 1 ELSE 0 END) AS overdue_sla_items,
                SUM(CASE WHEN COALESCE(w.due_at, '') <> '' AND w.due_at <= ? THEN 1 ELSE 0 END) AS overdue_due_items,
                ROUND(AVG(COALESCE(w.priority_score, 0)), 2) AS avg_priority_score,
                MAX(COALESCE(w.priority_score, 0)) AS max_priority_score
            FROM work_items w
            JOIN organizations o ON o.organization_id = w.organization_id
            LEFT JOIN users u ON u.user_id = w.assigned_user_id
            WHERE {' AND '.join(conditions)}
            GROUP BY
                COALESCE(w.assigned_user_id, 0),
                CASE
                    WHEN w.assigned_user_id IS NULL THEN 'Nieprzypisane'
                    ELSE COALESCE(u.display_name, u.login, 'Uzytkownik')
                END
            ORDER BY
                escalated_items DESC,
                overdue_sla_items DESC,
                open_items DESC,
                avg_priority_score DESC,
                assigned_user_name ASC
            LIMIT ?
        """
        params.append(max(1, int(limit)))
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def list_by_ids(
        self,
        work_item_ids: list[int],
        *,
        organization_id: int | None = None,
    ) -> list[dict[str, Any]]:
        normalized_ids = sorted({int(item_id) for item_id in work_item_ids if int(item_id) > 0})
        if not normalized_ids:
            return []
        placeholders = ", ".join("?" for _ in normalized_ids)
        params: list[Any] = list(normalized_ids)
        query = f"""
            SELECT
                w.*,
                o.name AS organization_name,
                o.slug AS organization_slug,
                COALESCE(assignee.display_name, assignee.login) AS assigned_user_name,
                assignee.telegram_user_id AS assigned_telegram_user_id,
                COALESCE(creator.display_name, creator.login) AS created_by_user_name,
                COALESCE(updater.display_name, updater.login) AS updated_by_user_name
            FROM work_items w
            JOIN organizations o ON o.organization_id = w.organization_id
            LEFT JOIN users assignee ON assignee.user_id = w.assigned_user_id
            LEFT JOIN users creator ON creator.user_id = w.created_by_user_id
            LEFT JOIN users updater ON updater.user_id = w.updated_by_user_id
            WHERE w.work_item_id IN ({placeholders})
              AND COALESCE(o.is_active, 1) = 1
        """
        if organization_id is not None:
            query += " AND w.organization_id = ?"
            params.append(int(organization_id))
        query += " ORDER BY w.work_item_id ASC"
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def search_work_items(
        self,
        query_text: str,
        *,
        organization_id: int | None = None,
        limit: int = 6,
    ) -> list[dict[str, Any]]:
        return self.list_work_items(
            {
                "search": query_text,
                "only_open": "1",
            },
            organization_id=organization_id,
            limit=limit,
        )

    def summary(
        self,
        *,
        organization_id: int | None = None,
        now_value: str,
    ) -> dict[str, Any]:
        where_params: list[Any] = []
        conditions = ["COALESCE(o.is_active, 1) = 1"]
        if organization_id is not None:
            conditions.append("w.organization_id = ?")
            where_params.append(int(organization_id))
        summary_params: list[Any] = [now_value, now_value, *where_params]

        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN w.status = 'nowe' THEN 1 ELSE 0 END) AS status_nowe,
                    SUM(CASE WHEN w.status = 'w_toku' THEN 1 ELSE 0 END) AS status_w_toku,
                    SUM(CASE WHEN w.status = 'oczekuje' THEN 1 ELSE 0 END) AS status_oczekuje,
                    SUM(CASE WHEN w.status = 'zamkniete' THEN 1 ELSE 0 END) AS status_zamkniete,
                    SUM(CASE WHEN w.status = 'anulowane' THEN 1 ELSE 0 END) AS status_anulowane,
                    SUM(CASE WHEN w.sla_stage = 'on_track' THEN 1 ELSE 0 END) AS sla_on_track,
                    SUM(CASE WHEN w.sla_stage = 'warning' THEN 1 ELSE 0 END) AS sla_warning,
                    SUM(CASE WHEN w.sla_stage = 'breached' THEN 1 ELSE 0 END) AS sla_breached,
                    SUM(CASE WHEN w.sla_stage = 'escalated' THEN 1 ELSE 0 END) AS sla_escalated,
                    SUM(CASE WHEN w.sla_stage = 'resolved' THEN 1 ELSE 0 END) AS sla_resolved,
                    SUM(CASE WHEN w.status NOT IN ('zamkniete', 'anulowane') AND COALESCE(w.sla_deadline_at, '') <> '' AND w.sla_deadline_at <= ? THEN 1 ELSE 0 END) AS overdue_sla,
                    SUM(CASE WHEN w.status NOT IN ('zamkniete', 'anulowane') AND COALESCE(w.due_at, '') <> '' AND w.due_at <= ? THEN 1 ELSE 0 END) AS overdue_due
                FROM work_items w
                JOIN organizations o ON o.organization_id = w.organization_id
                WHERE {' AND '.join(conditions)}
                """,
                summary_params,
            ).fetchone()
            top_risk_rows = connection.execute(
                f"""
                SELECT
                    w.work_item_id,
                    w.organization_id,
                    w.title,
                    w.status,
                    w.priority_level,
                    w.priority_score,
                    w.sla_stage,
                    w.sla_deadline_at,
                    w.due_at,
                    COALESCE(assignee.display_name, assignee.login) AS assigned_user_name
                FROM work_items w
                JOIN organizations o ON o.organization_id = w.organization_id
                LEFT JOIN users assignee ON assignee.user_id = w.assigned_user_id
                WHERE {' AND '.join(conditions)}
                  AND w.status NOT IN ('zamkniete', 'anulowane')
                ORDER BY
                    w.priority_score DESC,
                    CASE WHEN COALESCE(w.sla_deadline_at, '') = '' THEN 1 ELSE 0 END,
                    w.sla_deadline_at ASC,
                    w.work_item_id ASC
                LIMIT 8
                """,
                where_params,
            ).fetchall()
        summary_row = dict(row) if row else {}
        return {
            "counts": {
                "total": int(summary_row.get("total") or 0),
                "status": {
                    "nowe": int(summary_row.get("status_nowe") or 0),
                    "w_toku": int(summary_row.get("status_w_toku") or 0),
                    "oczekuje": int(summary_row.get("status_oczekuje") or 0),
                    "zamkniete": int(summary_row.get("status_zamkniete") or 0),
                    "anulowane": int(summary_row.get("status_anulowane") or 0),
                },
                "sla": {
                    "on_track": int(summary_row.get("sla_on_track") or 0),
                    "warning": int(summary_row.get("sla_warning") or 0),
                    "breached": int(summary_row.get("sla_breached") or 0),
                    "escalated": int(summary_row.get("sla_escalated") or 0),
                    "resolved": int(summary_row.get("sla_resolved") or 0),
                },
                "overdue_sla": int(summary_row.get("overdue_sla") or 0),
                "overdue_due": int(summary_row.get("overdue_due") or 0),
            },
            "top_risk": [dict(item) for item in top_risk_rows],
        }
