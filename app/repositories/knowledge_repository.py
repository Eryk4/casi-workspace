from __future__ import annotations

from typing import Any

from app.db import execute_insert_returning_id, get_connection
from app.utils import now_iso


class KnowledgeRepository:
    def list_documents(
        self,
        organization_id: int,
        search: str = "",
        *,
        assistant_only: bool = False,
        downloadable_only: bool = False,
        include_deleted: bool = False,
        lifecycle_status: str | None = None,
    ) -> list[dict[str, Any]]:
        params: list[Any] = [organization_id]
        query = """
            SELECT
                kd.*,
                o.name AS organization_name,
                o.slug AS organization_slug,
                u.login AS created_by_login,
                u.display_name AS created_by_display_name,
                owner_u.login AS owner_login,
                owner_u.display_name AS owner_display_name,
                reviewer_u.login AS reviewer_login,
                reviewer_u.display_name AS reviewer_display_name,
                approver_u.login AS approver_login,
                approver_u.display_name AS approver_display_name,
                official_u.login AS official_version_marked_by_login,
                official_u.display_name AS official_version_marked_by_display_name
            FROM knowledge_documents kd
            JOIN organizations o ON o.organization_id = kd.organization_id
            LEFT JOIN users u ON u.user_id = kd.created_by_user_id
            LEFT JOIN users owner_u ON owner_u.user_id = kd.owner_user_id
            LEFT JOIN users reviewer_u ON reviewer_u.user_id = kd.reviewer_user_id
            LEFT JOIN users approver_u ON approver_u.user_id = kd.approver_user_id
            LEFT JOIN users official_u ON official_u.user_id = kd.official_version_marked_by_user_id
            WHERE kd.organization_id = ?
        """
        if not include_deleted:
            query += " AND COALESCE(kd.lifecycle_status, 'active') <> 'deleted'"
        if lifecycle_status:
            query += " AND COALESCE(kd.lifecycle_status, 'active') = ?"
            params.append(str(lifecycle_status))
        if assistant_only:
            query += " AND COALESCE(kd.use_in_assistant, 1) = 1"
        if downloadable_only:
            query += " AND COALESCE(kd.is_downloadable, 1) = 1"
        normalized_search = search.strip().lower()
        if normalized_search:
            params.extend(
                [
                    f"%{normalized_search}%",
                    f"%{normalized_search}%",
                    f"%{normalized_search}%",
                    f"%{normalized_search}%",
                ]
            )
            query += """
                AND (
                    LOWER(kd.title) LIKE ?
                    OR LOWER(kd.file_name) LIKE ?
                    OR LOWER(kd.content_text) LIKE ?
                    OR LOWER(COALESCE(kd.library_path, '')) LIKE ?
                )
            """
        query += """
            ORDER BY
                CASE COALESCE(kd.lifecycle_status, 'active')
                    WHEN 'active' THEN 0
                    WHEN 'archived' THEN 1
                    ELSE 2
                END,
                CASE kd.processing_status
                    WHEN 'processing' THEN 0
                    WHEN 'queued' THEN 1
                    WHEN 'error' THEN 2
                    ELSE 3
                END,
                kd.updated_at DESC,
                kd.knowledge_document_id DESC
        """
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_by_id(
        self,
        knowledge_document_id: int,
        organization_id: int | None = None,
    ) -> dict[str, Any] | None:
        params: list[Any] = [knowledge_document_id]
        query = """
            SELECT
                kd.*,
                o.name AS organization_name,
                o.slug AS organization_slug,
                u.login AS created_by_login,
                u.display_name AS created_by_display_name,
                owner_u.login AS owner_login,
                owner_u.display_name AS owner_display_name,
                reviewer_u.login AS reviewer_login,
                reviewer_u.display_name AS reviewer_display_name,
                approver_u.login AS approver_login,
                approver_u.display_name AS approver_display_name,
                official_u.login AS official_version_marked_by_login,
                official_u.display_name AS official_version_marked_by_display_name
            FROM knowledge_documents kd
            JOIN organizations o ON o.organization_id = kd.organization_id
            LEFT JOIN users u ON u.user_id = kd.created_by_user_id
            LEFT JOIN users owner_u ON owner_u.user_id = kd.owner_user_id
            LEFT JOIN users reviewer_u ON reviewer_u.user_id = kd.reviewer_user_id
            LEFT JOIN users approver_u ON approver_u.user_id = kd.approver_user_id
            LEFT JOIN users official_u ON official_u.user_id = kd.official_version_marked_by_user_id
            WHERE kd.knowledge_document_id = ?
        """
        if organization_id is not None:
            query += " AND kd.organization_id = ?"
            params.append(organization_id)
        with get_connection() as connection:
            row = connection.execute(query, params).fetchone()
        return dict(row) if row else None

    def search_documents(
        self,
        query_text: str,
        *,
        organization_id: int | None = None,
        limit: int = 6,
    ) -> list[dict[str, Any]]:
        normalized_query = str(query_text or "").strip().lower()
        if not normalized_query:
            return []

        params: list[Any] = [f"%{normalized_query}%"] * 5
        query = """
            SELECT
                kd.*,
                o.name AS organization_name,
                o.slug AS organization_slug,
                u.login AS created_by_login,
                u.display_name AS created_by_display_name,
                owner_u.login AS owner_login,
                owner_u.display_name AS owner_display_name,
                reviewer_u.login AS reviewer_login,
                reviewer_u.display_name AS reviewer_display_name,
                approver_u.login AS approver_login,
                approver_u.display_name AS approver_display_name,
                official_u.login AS official_version_marked_by_login,
                official_u.display_name AS official_version_marked_by_display_name
            FROM knowledge_documents kd
            JOIN organizations o ON o.organization_id = kd.organization_id
            LEFT JOIN users u ON u.user_id = kd.created_by_user_id
            LEFT JOIN users owner_u ON owner_u.user_id = kd.owner_user_id
            LEFT JOIN users reviewer_u ON reviewer_u.user_id = kd.reviewer_user_id
            LEFT JOIN users approver_u ON approver_u.user_id = kd.approver_user_id
            LEFT JOIN users official_u ON official_u.user_id = kd.official_version_marked_by_user_id
            WHERE COALESCE(o.is_active, 1) = 1
              AND COALESCE(kd.lifecycle_status, 'active') <> 'deleted'
              AND (COALESCE(kd.is_downloadable, 1) = 1 OR COALESCE(kd.use_in_assistant, 1) = 1)
              AND (
                LOWER(COALESCE(kd.title, '')) LIKE ?
                OR LOWER(COALESCE(kd.file_name, '')) LIKE ?
                OR LOWER(COALESCE(kd.content_text, '')) LIKE ?
                OR LOWER(COALESCE(o.name, '')) LIKE ?
                OR LOWER(COALESCE(kd.library_path, '')) LIKE ?
              )
        """
        if organization_id is not None:
            query += " AND kd.organization_id = ?"
            params.append(organization_id)
        query += """
            ORDER BY kd.updated_at DESC, kd.knowledge_document_id DESC
            LIMIT ?
        """
        params.append(limit)

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_by_storage_key(self, organization_id: int, file_storage_key: str) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT
                    kd.*,
                    o.name AS organization_name,
                    o.slug AS organization_slug,
                    u.login AS created_by_login,
                    u.display_name AS created_by_display_name,
                    owner_u.login AS owner_login,
                    owner_u.display_name AS owner_display_name,
                    reviewer_u.login AS reviewer_login,
                    reviewer_u.display_name AS reviewer_display_name,
                    approver_u.login AS approver_login,
                    approver_u.display_name AS approver_display_name,
                    official_u.login AS official_version_marked_by_login,
                    official_u.display_name AS official_version_marked_by_display_name
                FROM knowledge_documents kd
                JOIN organizations o ON o.organization_id = kd.organization_id
                LEFT JOIN users u ON u.user_id = kd.created_by_user_id
                LEFT JOIN users owner_u ON owner_u.user_id = kd.owner_user_id
                LEFT JOIN users reviewer_u ON reviewer_u.user_id = kd.reviewer_user_id
                LEFT JOIN users approver_u ON approver_u.user_id = kd.approver_user_id
                LEFT JOIN users official_u ON official_u.user_id = kd.official_version_marked_by_user_id
                WHERE kd.organization_id = ?
                  AND kd.file_storage_key = ?
                """,
                (organization_id, file_storage_key),
            ).fetchone()
        return dict(row) if row else None

    def create(self, payload: dict[str, Any]) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO knowledge_documents (
                    organization_id,
                    title,
                    file_name,
                    mime_type,
                    file_link,
                    file_storage_key,
                    content_text,
                    content_hash,
                    char_count,
                    source_type,
                    library_path,
                    is_downloadable,
                    use_in_assistant,
                    business_status,
                    business_status_before_archive,
                    owner_user_id,
                    reviewer_user_id,
                    approver_user_id,
                    processing_status,
                    processing_error,
                    current_version_number,
                    official_version_number,
                    official_version_marked_at,
                    official_version_marked_by_user_id,
                    last_processed_at,
                    processing_started_at,
                    created_by_user_id,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["organization_id"],
                    payload["title"],
                    payload["file_name"],
                    payload.get("mime_type"),
                    payload["file_link"],
                    payload["file_storage_key"],
                    payload.get("content_text", ""),
                    payload["content_hash"],
                    int(payload.get("char_count", len(str(payload.get("content_text") or "")))),
                    payload.get("source_type", "manual"),
                    payload.get("library_path", ""),
                    int(bool(payload.get("is_downloadable", True))),
                    int(bool(payload.get("use_in_assistant", True))),
                    payload.get("business_status", "roboczy"),
                    payload.get("business_status_before_archive"),
                    payload.get("owner_user_id"),
                    payload.get("reviewer_user_id"),
                    payload.get("approver_user_id"),
                    payload.get("processing_status", "queued"),
                    payload.get("processing_error"),
                    int(payload.get("current_version_number", 0)),
                    int(payload.get("official_version_number", 0)),
                    payload.get("official_version_marked_at"),
                    payload.get("official_version_marked_by_user_id"),
                    payload.get("last_processed_at"),
                    payload.get("processing_started_at"),
                    payload.get("created_by_user_id"),
                    timestamp,
                    timestamp,
                ),
                "knowledge_document_id",
            )

    def update(self, knowledge_document_id: int, fields: dict[str, Any]) -> None:
        if not fields:
            return
        allowed = {
            "title",
            "file_name",
            "mime_type",
            "file_link",
            "file_storage_key",
            "content_text",
            "content_hash",
            "char_count",
            "source_type",
            "library_path",
            "is_downloadable",
            "use_in_assistant",
            "business_status",
            "business_status_before_archive",
            "owner_user_id",
            "reviewer_user_id",
            "approver_user_id",
            "lifecycle_status",
            "archived_at",
            "archived_by_user_id",
            "deleted_at",
            "deleted_by_user_id",
            "duplicate_status",
            "duplicate_of_document_id",
            "duplicate_score",
            "duplicate_reason",
            "last_seen_in_folder_at",
            "processing_status",
            "processing_error",
            "current_version_number",
            "official_version_number",
            "official_version_marked_at",
            "official_version_marked_by_user_id",
            "last_processed_at",
            "processing_started_at",
            "created_by_user_id",
        }
        update_fields = {key: value for key, value in fields.items() if key in allowed}
        if not update_fields:
            return
        update_fields["updated_at"] = now_iso()
        assignments = ", ".join(f"{key} = ?" for key in update_fields)
        values = list(update_fields.values()) + [knowledge_document_id]
        with get_connection() as connection:
            connection.execute(
                f"UPDATE knowledge_documents SET {assignments} WHERE knowledge_document_id = ?",
                values,
            )

    def create_version(self, payload: dict[str, Any]) -> int:
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO knowledge_document_versions (
                    knowledge_document_id,
                    organization_id,
                    version_number,
                    title,
                    file_name,
                    mime_type,
                    file_link,
                    file_storage_key,
                    content_text,
                    content_hash,
                    char_count,
                    source_type,
                    created_by_user_id,
                    extraction_method,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["knowledge_document_id"],
                    payload["organization_id"],
                    int(payload["version_number"]),
                    payload["title"],
                    payload["file_name"],
                    payload.get("mime_type"),
                    payload["file_link"],
                    payload["file_storage_key"],
                    payload["content_text"],
                    payload["content_hash"],
                    int(payload.get("char_count", len(str(payload.get("content_text") or "")))),
                    payload.get("source_type", "manual"),
                    payload.get("created_by_user_id"),
                    payload.get("extraction_method"),
                    payload.get("created_at") or now_iso(),
                ),
                "knowledge_document_version_id",
            )

    def list_versions(self, knowledge_document_id: int, limit: int | None = 5) -> list[dict[str, Any]]:
        params: list[Any] = [knowledge_document_id]
        query = """
            SELECT *
            FROM knowledge_document_versions
            WHERE knowledge_document_id = ?
            ORDER BY version_number DESC, created_at DESC
        """
        if limit is not None:
            query += " LIMIT ?"
            params.append(max(1, int(limit)))
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_version_by_number(self, knowledge_document_id: int, version_number: int) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM knowledge_document_versions
                WHERE knowledge_document_id = ?
                  AND version_number = ?
                LIMIT 1
                """,
                (knowledge_document_id, version_number),
            ).fetchone()
        return dict(row) if row else None

    def create_comment(self, payload: dict[str, Any]) -> int:
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO knowledge_document_comments (
                    knowledge_document_id,
                    organization_id,
                    knowledge_document_version_id,
                    version_number,
                    parent_comment_id,
                    annotation_kind,
                    anchor_label,
                    anchor_excerpt,
                    note_text,
                    created_by_user_id,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["knowledge_document_id"],
                    payload["organization_id"],
                    payload.get("knowledge_document_version_id"),
                    payload.get("version_number"),
                    payload.get("parent_comment_id"),
                    payload.get("annotation_kind", "comment"),
                    payload.get("anchor_label"),
                    payload.get("anchor_excerpt"),
                    payload["note_text"],
                    payload["created_by_user_id"],
                    payload.get("created_at") or now_iso(),
                ),
                "knowledge_document_comment_id",
            )

    def list_comments(self, knowledge_document_id: int, limit: int | None = 40) -> list[dict[str, Any]]:
        params: list[Any] = [knowledge_document_id]
        query = """
            SELECT
                c.*,
                u.login AS created_by_login,
                u.display_name AS created_by_display_name
            FROM knowledge_document_comments c
            LEFT JOIN users u ON u.user_id = c.created_by_user_id
            WHERE c.knowledge_document_id = ?
            ORDER BY c.created_at DESC, c.knowledge_document_comment_id DESC
        """
        if limit is not None:
            query += " LIMIT ?"
            params.append(max(1, int(limit)))
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def find_by_content_hash(
        self,
        organization_id: int,
        content_hash: str,
        *,
        exclude_document_id: int | None = None,
    ) -> list[dict[str, Any]]:
        params: list[Any] = [organization_id, content_hash]
        query = """
            SELECT
                kd.*,
                o.name AS organization_name,
                o.slug AS organization_slug,
                u.login AS created_by_login,
                u.display_name AS created_by_display_name,
                official_u.login AS official_version_marked_by_login,
                official_u.display_name AS official_version_marked_by_display_name
            FROM knowledge_documents kd
            JOIN organizations o ON o.organization_id = kd.organization_id
            LEFT JOIN users u ON u.user_id = kd.created_by_user_id
            LEFT JOIN users official_u ON official_u.user_id = kd.official_version_marked_by_user_id
            WHERE kd.organization_id = ?
              AND COALESCE(kd.lifecycle_status, 'active') <> 'deleted'
              AND COALESCE(kd.content_hash, '') = ?
        """
        if exclude_document_id is not None:
            query += " AND kd.knowledge_document_id <> ?"
            params.append(exclude_document_id)
        query += " ORDER BY kd.updated_at DESC, kd.knowledge_document_id DESC"
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def list_similarity_candidates(
        self,
        organization_id: int,
        *,
        exclude_document_id: int | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        params: list[Any] = [organization_id]
        query = """
            SELECT
                kd.*,
                o.name AS organization_name,
                o.slug AS organization_slug,
                u.login AS created_by_login,
                u.display_name AS created_by_display_name,
                official_u.login AS official_version_marked_by_login,
                official_u.display_name AS official_version_marked_by_display_name
            FROM knowledge_documents kd
            JOIN organizations o ON o.organization_id = kd.organization_id
            LEFT JOIN users u ON u.user_id = kd.created_by_user_id
            LEFT JOIN users official_u ON official_u.user_id = kd.official_version_marked_by_user_id
            WHERE kd.organization_id = ?
              AND COALESCE(kd.lifecycle_status, 'active') <> 'deleted'
              AND COALESCE(kd.processing_status, 'queued') = 'ready'
        """
        if exclude_document_id is not None:
            query += " AND kd.knowledge_document_id <> ?"
            params.append(exclude_document_id)
        query += """
            ORDER BY kd.updated_at DESC, kd.knowledge_document_id DESC
            LIMIT ?
        """
        params.append(max(1, int(limit)))
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def create_job(self, payload: dict[str, Any]) -> int:
        timestamp = now_iso()
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO knowledge_processing_jobs (
                    organization_id,
                    knowledge_document_id,
                    job_type,
                    status,
                    source_storage_key,
                    source_file_name,
                    source_mime_type,
                    source_type,
                    source_content_hash,
                    supplemental_text,
                    error_message,
                    attempts,
                    max_attempts,
                    created_by_user_id,
                    started_at,
                    finished_at,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["organization_id"],
                    payload.get("knowledge_document_id"),
                    payload.get("job_type", "ingest"),
                    payload.get("status", "pending"),
                    payload["source_storage_key"],
                    payload["source_file_name"],
                    payload.get("source_mime_type"),
                    payload.get("source_type", "manual"),
                    payload["source_content_hash"],
                    payload.get("supplemental_text"),
                    payload.get("error_message"),
                    int(payload.get("attempts", 0)),
                    int(payload.get("max_attempts", 3)),
                    payload.get("created_by_user_id"),
                    payload.get("started_at"),
                    payload.get("finished_at"),
                    timestamp,
                    timestamp,
                ),
                "knowledge_processing_job_id",
            )

    def get_next_pending_job(self) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM knowledge_processing_jobs
                WHERE status = 'pending'
                ORDER BY created_at ASC, knowledge_processing_job_id ASC
                LIMIT 1
                """
            ).fetchone()
        return dict(row) if row else None

    def list_recent_jobs(self, knowledge_document_id: int, limit: int = 5) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM knowledge_processing_jobs
                WHERE knowledge_document_id = ?
                ORDER BY created_at DESC, knowledge_processing_job_id DESC
                LIMIT ?
                """,
                (knowledge_document_id, max(1, int(limit))),
            ).fetchall()
        return [dict(row) for row in rows]

    def mark_job_processing(self, knowledge_processing_job_id: int) -> None:
        timestamp = now_iso()
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE knowledge_processing_jobs
                SET status = 'processing',
                    attempts = attempts + 1,
                    started_at = ?,
                    finished_at = NULL,
                    error_message = NULL,
                    updated_at = ?
                WHERE knowledge_processing_job_id = ?
                """,
                (timestamp, timestamp, knowledge_processing_job_id),
            )

    def mark_job_completed(self, knowledge_processing_job_id: int) -> None:
        timestamp = now_iso()
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE knowledge_processing_jobs
                SET status = 'completed',
                    finished_at = ?,
                    updated_at = ?
                WHERE knowledge_processing_job_id = ?
                """,
                (timestamp, timestamp, knowledge_processing_job_id),
            )

    def mark_job_failed(self, knowledge_processing_job_id: int, error_message: str) -> None:
        timestamp = now_iso()
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE knowledge_processing_jobs
                SET status = 'failed',
                    error_message = ?,
                    finished_at = ?,
                    updated_at = ?
                WHERE knowledge_processing_job_id = ?
                """,
                (error_message, timestamp, timestamp, knowledge_processing_job_id),
            )

    def get_watch_status(self, organization_id: int) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM knowledge_folder_watchers
                WHERE organization_id = ?
                LIMIT 1
                """,
                (organization_id,),
            ).fetchone()
        return dict(row) if row else None

    def upsert_watch_status(self, organization_id: int, fields: dict[str, Any]) -> None:
        timestamp = now_iso()
        existing = self.get_watch_status(organization_id)
        if existing:
            allowed = {
                "watch_mode",
                "last_scan_started_at",
                "last_scan_completed_at",
                "last_scan_status",
                "last_actor",
                "last_error",
                "queued_new",
                "queued_updates",
                "unchanged_count",
                "skipped_count",
                "duplicate_count",
                "similar_count",
            }
            update_fields = {key: value for key, value in fields.items() if key in allowed}
            if not update_fields:
                return
            update_fields["updated_at"] = timestamp
            assignments = ", ".join(f"{key} = ?" for key in update_fields)
            values = list(update_fields.values()) + [organization_id]
            with get_connection() as connection:
                connection.execute(
                    f"UPDATE knowledge_folder_watchers SET {assignments} WHERE organization_id = ?",
                    values,
                )
            return

        with get_connection() as connection:
            execute_insert_returning_id(
                connection,
                """
                INSERT INTO knowledge_folder_watchers (
                    organization_id,
                    watch_mode,
                    last_scan_started_at,
                    last_scan_completed_at,
                    last_scan_status,
                    last_actor,
                    last_error,
                    queued_new,
                    queued_updates,
                    unchanged_count,
                    skipped_count,
                    duplicate_count,
                    similar_count,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    organization_id,
                    fields.get("watch_mode", "polling"),
                    fields.get("last_scan_started_at"),
                    fields.get("last_scan_completed_at"),
                    fields.get("last_scan_status", "idle"),
                    fields.get("last_actor"),
                    fields.get("last_error"),
                    int(fields.get("queued_new", 0)),
                    int(fields.get("queued_updates", 0)),
                    int(fields.get("unchanged_count", 0)),
                    int(fields.get("skipped_count", 0)),
                    int(fields.get("duplicate_count", 0)),
                    int(fields.get("similar_count", 0)),
                    timestamp,
                ),
                "knowledge_folder_watcher_id",
            )
