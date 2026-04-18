from __future__ import annotations

from typing import Any

from app.db import execute_insert_returning_id, get_connection
from app.utils import now_iso


class SystemSettingsRepository:
    def get(self, setting_key: str) -> dict[str, Any] | None:
        normalized_key = str(setting_key or "").strip()
        if not normalized_key:
            return None
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM system_settings
                WHERE setting_key = ?
                """,
                (normalized_key,),
            ).fetchone()
        return dict(row) if row else None

    def get_many(self, setting_keys: list[str] | tuple[str, ...] | None = None) -> dict[str, dict[str, Any]]:
        with get_connection() as connection:
            if setting_keys:
                normalized_keys = [str(item or "").strip() for item in setting_keys if str(item or "").strip()]
                if not normalized_keys:
                    return {}
                placeholders = ", ".join("?" for _ in normalized_keys)
                rows = connection.execute(
                    f"""
                    SELECT *
                    FROM system_settings
                    WHERE setting_key IN ({placeholders})
                    """,
                    normalized_keys,
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT *
                    FROM system_settings
                    """
                ).fetchall()
        return {str(row["setting_key"]): dict(row) for row in rows}

    def upsert(self, setting_key: str, setting_value_text: str, *, updated_by_user_id: int | None = None) -> dict[str, Any]:
        normalized_key = str(setting_key or "").strip()
        if not normalized_key:
            raise ValueError("Klucz ustawienia systemowego jest wymagany.")

        timestamp = now_iso()
        existing = self.get(normalized_key)
        if existing:
            with get_connection() as connection:
                connection.execute(
                    """
                    UPDATE system_settings
                    SET setting_value_text = ?, updated_by_user_id = ?, updated_at = ?
                    WHERE setting_key = ?
                    """,
                    (
                        setting_value_text,
                        updated_by_user_id,
                        timestamp,
                        normalized_key,
                    ),
                )
            return self.get(normalized_key) or existing

        with get_connection() as connection:
            execute_insert_returning_id(
                connection,
                """
                INSERT INTO system_settings (
                    setting_key,
                    setting_value_text,
                    updated_by_user_id,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    normalized_key,
                    setting_value_text,
                    updated_by_user_id,
                    timestamp,
                    timestamp,
                ),
                "system_setting_id",
            )
        created = self.get(normalized_key)
        assert created is not None
        return created

    def delete(self, setting_key: str) -> None:
        normalized_key = str(setting_key or "").strip()
        if not normalized_key:
            return
        with get_connection() as connection:
            connection.execute(
                """
                DELETE FROM system_settings
                WHERE setting_key = ?
                """,
                (normalized_key,),
            )
