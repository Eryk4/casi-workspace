from __future__ import annotations

from typing import Any

from app.config import SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_SECRET
from app.domain.constants import SYSTEM_OWNER_ROLE
from app.repositories.event_repository import EventRepository
from app.repositories.system_settings_repository import SystemSettingsRepository


class SystemSettingsError(ValueError):
    pass


class SystemSettingsService:
    TELEGRAM_BOT_TOKEN_KEY = "communication.telegram.bot_token"
    TELEGRAM_WEBHOOK_SECRET_KEY = "communication.telegram.webhook_secret"
    SLACK_BOT_TOKEN_KEY = "communication.slack.bot_token"
    SLACK_SIGNING_SECRET_KEY = "communication.slack.signing_secret"

    def __init__(
        self,
        system_settings_repository: SystemSettingsRepository,
        event_repository: EventRepository,
    ) -> None:
        self.system_settings_repository = system_settings_repository
        self.event_repository = event_repository

    def build_communication_settings_snapshot(
        self,
        *,
        actor_user: dict[str, Any] | None,
        public_base_url: str = "",
    ) -> dict[str, Any]:
        self._ensure_system_owner(actor_user)
        telegram_credentials = self.resolve_telegram_credentials()
        slack_credentials = self.resolve_slack_credentials()
        normalized_base_url = str(public_base_url or "").strip().rstrip("/")
        telegram_webhook_path = (
            f"/api/telegram/webhook/{telegram_credentials['webhook_secret']}"
            if telegram_credentials["webhook_secret"]
            else None
        )
        slack_webhook_path = "/api/slack/events" if slack_credentials["signing_secret"] else None
        return {
            "telegram": {
                "provider": "telegram",
                "display_name": "Telegram",
                "enabled": bool(telegram_credentials["bot_token"] and telegram_credentials["webhook_secret"]),
                "outbound_enabled": bool(telegram_credentials["bot_token"]),
                "mode": (
                    "aktywny"
                    if telegram_credentials["bot_token"] and telegram_credentials["webhook_secret"]
                    else "czesciowy"
                    if (telegram_credentials["bot_token"] or telegram_credentials["webhook_secret"])
                    else "wylaczony"
                ),
                "bot_token": self._describe_secret(
                    telegram_credentials["bot_token"],
                    telegram_credentials["bot_token_source"],
                ),
                "webhook_secret": self._describe_secret(
                    telegram_credentials["webhook_secret"],
                    telegram_credentials["webhook_secret_source"],
                ),
                "webhook_path": telegram_webhook_path,
                "webhook_url": (
                    f"{normalized_base_url}{telegram_webhook_path}"
                    if normalized_base_url and telegram_webhook_path
                    else None
                ),
            },
            "slack": {
                "provider": "slack",
                "display_name": "Slack",
                "enabled": bool(slack_credentials["bot_token"] and slack_credentials["signing_secret"]),
                "outbound_enabled": bool(slack_credentials["bot_token"]),
                "mode": (
                    "aktywny"
                    if slack_credentials["bot_token"] and slack_credentials["signing_secret"]
                    else "czesciowy"
                    if (slack_credentials["bot_token"] or slack_credentials["signing_secret"])
                    else "wylaczony"
                ),
                "bot_token": self._describe_secret(
                    slack_credentials["bot_token"],
                    slack_credentials["bot_token_source"],
                ),
                "signing_secret": self._describe_secret(
                    slack_credentials["signing_secret"],
                    slack_credentials["signing_secret_source"],
                ),
                "webhook_path": slack_webhook_path,
                "webhook_url": (
                    f"{normalized_base_url}{slack_webhook_path}"
                    if normalized_base_url and slack_webhook_path
                    else None
                ),
            },
            "whatsapp": {
                "provider": "whatsapp",
                "display_name": "WhatsApp",
                "enabled": False,
                "mode": "planowany",
                "note": "Organizacje moga juz wybrac WhatsApp jako docelowy kanal, ale integracja systemowa pozostaje do wdrozenia.",
            },
        }

    def update_communication_settings(
        self,
        payload: dict[str, Any],
        *,
        actor_user: dict[str, Any] | None,
        actor_login: str,
    ) -> dict[str, Any]:
        self._ensure_system_owner(actor_user)
        normalized_payload = payload if isinstance(payload, dict) else {}
        changes: list[str] = []

        telegram_payload = normalized_payload.get("telegram")
        if isinstance(telegram_payload, dict):
            changes.extend(
                self._apply_provider_update(
                    provider_key="telegram",
                    provider_payload=telegram_payload,
                    value_mapping={
                        "bot_token": self.TELEGRAM_BOT_TOKEN_KEY,
                        "webhook_secret": self.TELEGRAM_WEBHOOK_SECRET_KEY,
                    },
                    updated_by_user_id=int(actor_user["user_id"]),
                )
            )

        slack_payload = normalized_payload.get("slack")
        if isinstance(slack_payload, dict):
            changes.extend(
                self._apply_provider_update(
                    provider_key="slack",
                    provider_payload=slack_payload,
                    value_mapping={
                        "bot_token": self.SLACK_BOT_TOKEN_KEY,
                        "signing_secret": self.SLACK_SIGNING_SECRET_KEY,
                    },
                    updated_by_user_id=int(actor_user["user_id"]),
                )
            )

        if not changes:
            raise SystemSettingsError("Nie wykryto zmian w ustawieniach komunikatorow.")

        self.event_repository.log(
            event_type="system_communication_settings_updated",
            invoice_id=None,
            organization_id=None,
            source="SYSTEM",
            status_before=None,
            status_after=None,
            decision_reason="Zmieniono globalne ustawienia komunikatorow systemowych.",
            actor=actor_login,
            details={"changes": changes},
        )

        return self.build_communication_settings_snapshot(actor_user=actor_user)

    def resolve_telegram_credentials(self) -> dict[str, str | None]:
        bot_token_value, bot_token_source = self._resolve_value(self.TELEGRAM_BOT_TOKEN_KEY, TELEGRAM_BOT_TOKEN)
        webhook_secret_value, webhook_secret_source = self._resolve_value(
            self.TELEGRAM_WEBHOOK_SECRET_KEY,
            TELEGRAM_WEBHOOK_SECRET,
        )
        return {
            "bot_token": bot_token_value,
            "bot_token_source": bot_token_source,
            "webhook_secret": webhook_secret_value,
            "webhook_secret_source": webhook_secret_source,
        }

    def resolve_slack_credentials(self) -> dict[str, str | None]:
        bot_token_value, bot_token_source = self._resolve_value(self.SLACK_BOT_TOKEN_KEY, SLACK_BOT_TOKEN)
        signing_secret_value, signing_secret_source = self._resolve_value(
            self.SLACK_SIGNING_SECRET_KEY,
            SLACK_SIGNING_SECRET,
        )
        return {
            "bot_token": bot_token_value,
            "bot_token_source": bot_token_source,
            "signing_secret": signing_secret_value,
            "signing_secret_source": signing_secret_source,
        }

    def _apply_provider_update(
        self,
        *,
        provider_key: str,
        provider_payload: dict[str, Any],
        value_mapping: dict[str, str],
        updated_by_user_id: int,
    ) -> list[str]:
        changes: list[str] = []
        clear_all = provider_payload.get("clear") in {True, 1, "1", "true", "tak", "yes"}
        if clear_all:
            for storage_key in value_mapping.values():
                self.system_settings_repository.delete(storage_key)
            return [f"{provider_key}:clear"]

        for field_key, storage_key in value_mapping.items():
            if provider_payload.get(f"clear_{field_key}") in {True, 1, "1", "true", "tak", "yes"}:
                self.system_settings_repository.delete(storage_key)
                changes.append(f"{provider_key}:{field_key}:clear")
                continue
            raw_value = str(provider_payload.get(field_key) or "").strip()
            if not raw_value:
                continue
            self.system_settings_repository.upsert(
                storage_key,
                raw_value,
                updated_by_user_id=updated_by_user_id,
            )
            changes.append(f"{provider_key}:{field_key}:save")
        return changes

    def _resolve_value(self, storage_key: str, env_fallback: str) -> tuple[str, str | None]:
        stored = self.system_settings_repository.get(storage_key)
        if stored is not None:
            return str(stored.get("setting_value_text") or "").strip(), "panel"
        normalized_env = str(env_fallback or "").strip()
        if normalized_env:
            return normalized_env, "env"
        return "", None

    def _describe_secret(self, value: str, source: str | None) -> dict[str, Any]:
        return {
            "configured": bool(value),
            "source": source,
            "masked_value": self._mask_secret(value),
        }

    def _mask_secret(self, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            return ""
        suffix = normalized[-4:] if len(normalized) > 4 else normalized
        return f"{'*' * max(4, min(len(normalized), 12))}{suffix}"

    def _ensure_system_owner(self, actor_user: dict[str, Any] | None) -> None:
        if not actor_user or str(actor_user.get("role") or "").strip() != SYSTEM_OWNER_ROLE:
            raise SystemSettingsError("Tylko Wlasciciel systemu moze zarzadzac globalnymi ustawieniami komunikatorow.")
