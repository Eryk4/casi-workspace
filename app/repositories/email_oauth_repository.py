from __future__ import annotations

from typing import Any

from app.db import execute_insert_returning_id, get_connection
from app.utils import now_iso


class EmailOAuthRepository:
    PROVIDER_GOOGLE = "google_workspace"

    def get_google_connection(self) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM system_email_google_connections
                WHERE provider = ?
                """,
                (self.PROVIDER_GOOGLE,),
            ).fetchone()
        return dict(row) if row else None

    def upsert_google_connection(self, payload: dict[str, Any], *, created_by_user_id: int | None) -> int:
        existing = self.get_google_connection()
        timestamp = now_iso()
        with get_connection() as connection:
            if existing:
                connection.execute(
                    """
                    UPDATE system_email_google_connections
                    SET
                        google_email = ?,
                        access_token = ?,
                        refresh_token = ?,
                        token_expires_at = ?,
                        scope = ?,
                        created_by_user_id = ?,
                        updated_at = ?
                    WHERE provider = ?
                    """,
                    (
                        payload.get("google_email"),
                        payload["access_token"],
                        payload.get("refresh_token"),
                        payload["token_expires_at"],
                        payload.get("scope"),
                        created_by_user_id,
                        timestamp,
                        self.PROVIDER_GOOGLE,
                    ),
                )
                return int(existing["system_email_google_connection_id"])
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO system_email_google_connections (
                    provider,
                    google_email,
                    access_token,
                    refresh_token,
                    token_expires_at,
                    scope,
                    created_by_user_id,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.PROVIDER_GOOGLE,
                    payload.get("google_email"),
                    payload["access_token"],
                    payload.get("refresh_token"),
                    payload["token_expires_at"],
                    payload.get("scope"),
                    created_by_user_id,
                    timestamp,
                    timestamp,
                ),
                "system_email_google_connection_id",
            )

    def delete_google_connection(self) -> None:
        with get_connection() as connection:
            connection.execute(
                "DELETE FROM system_email_google_connections WHERE provider = ?",
                (self.PROVIDER_GOOGLE,),
            )

    def create_google_oauth_state(
        self,
        *,
        state_token: str,
        created_by_user_id: int | None,
        login_hint: str | None,
        expires_at: str,
    ) -> int:
        with get_connection() as connection:
            return execute_insert_returning_id(
                connection,
                """
                INSERT INTO system_email_oauth_states (
                    state_token,
                    created_by_user_id,
                    login_hint,
                    expires_at,
                    created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    state_token,
                    created_by_user_id,
                    login_hint,
                    expires_at,
                    now_iso(),
                ),
                "system_email_oauth_state_id",
            )

    def consume_google_oauth_state(self, state_token: str) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM system_email_oauth_states
                WHERE state_token = ?
                """,
                (state_token,),
            ).fetchone()
            if not row:
                return None
            connection.execute(
                "DELETE FROM system_email_oauth_states WHERE system_email_oauth_state_id = ?",
                (row["system_email_oauth_state_id"],),
            )
        return dict(row) if row else None

    def clear_expired_google_oauth_states(self, expires_before: str) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                DELETE FROM system_email_oauth_states
                WHERE expires_at <= ?
                """,
                (expires_before,),
            )
