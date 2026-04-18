from __future__ import annotations

import json
import re
from typing import Any

from app.domain.constants import GUEST_ROLE, ORGANIZATION_MODULE_CODES
from app.repositories.event_repository import EventRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository
from app.utils import now_iso


class OrganizationError(ValueError):
    pass


class OrganizationPermissionError(PermissionError):
    pass


class OrganizationService:
    SUPPORTED_COMMUNICATION_PROVIDERS = ("telegram", "slack", "whatsapp")
    SUPPORTED_MODULE_SHORTCUT_VIEWS = (
        "dashboard",
        "invoices",
        "knowledge",
        "contractors",
        "tasks",
        "billing",
        "support",
        "inbox",
        "views",
        "automation",
        "health",
        "logs",
        "organizations",
        "email-center",
        "users",
    )

    def __init__(
        self,
        organization_repository: OrganizationRepository,
        event_repository: EventRepository,
        user_repository: UserRepository,
    ) -> None:
        self.organization_repository = organization_repository
        self.event_repository = event_repository
        self.user_repository = user_repository

    def ensure_default_setup(self, default_admin_login: str) -> dict[str, Any]:
        organization = self.organization_repository.ensure_default_organization()
        self.organization_repository.assign_legacy_records_to_default(
            int(organization["organization_id"]),
            default_admin_login,
        )
        return self._decorate_organization(organization)

    def list_organizations(self, actor_user: dict[str, Any]) -> list[dict[str, Any]]:
        if actor_user.get("is_global_admin"):
            return self._decorate_organizations(self.organization_repository.list_organizations())

        organization_id = actor_user.get("organization_id")
        if not organization_id:
            return []
        organization = self.organization_repository.get_by_id(int(organization_id))
        return self._decorate_organizations([organization] if organization else [])

    def create_organization(self, payload: dict[str, Any], actor_user: dict[str, Any], actor_login: str) -> dict[str, Any]:
        self._require_global_admin(actor_user)
        normalized = self._normalize_payload(payload)
        enabled_modules = normalized.pop("enabled_modules", [])

        if self.organization_repository.get_by_name(normalized["name"]):
            raise OrganizationError("Organizacja o takiej nazwie juz istnieje.")
        if self.organization_repository.get_by_slug(normalized["slug"]):
            raise OrganizationError("Organizacja o takim identyfikatorze katalogu juz istnieje.")

        telegram_chat_id = self._extract_active_telegram_chat_id(normalized)
        if telegram_chat_id:
            existing_by_chat = self.organization_repository.get_by_telegram_chat_id(telegram_chat_id)
            if existing_by_chat:
                raise OrganizationError("Ten kanal Telegram jest juz przypisany do innej organizacji.")
        slack_channel_id = self._extract_active_slack_channel_id(normalized)
        if slack_channel_id:
            existing_by_channel = self.organization_repository.get_by_active_slack_channel_id(slack_channel_id)
            if existing_by_channel:
                raise OrganizationError("Ten kanal Slack jest juz przypisany do innej organizacji.")

        organization_id = self.organization_repository.create(normalized)
        self.organization_repository.replace_enabled_modules(
            organization_id,
            enabled_modules,
            enabled_by_user_id=self._extract_actor_user_id(actor_user),
        )
        created = self.organization_repository.get_by_id(organization_id)
        assert created is not None

        self.event_repository.log(
            event_type="organization_created",
            invoice_id=None,
            source=None,
            status_before=None,
            status_after=None,
            decision_reason=f"Utworzono organizacje {created['name']}.",
            actor=actor_login,
            organization_id=created["organization_id"],
            details={
                "organization_id": created["organization_id"],
                "slug": created["slug"],
                "enabled_modules": enabled_modules,
                "module_shortcuts": created.get("module_shortcuts") or {},
            },
        )
        return self._decorate_organization(created)

    def get_organization_for_settings(self, organization_id: int, actor_user: dict[str, Any]) -> dict[str, Any]:
        current = self.organization_repository.get_by_id(organization_id)
        if not current:
            raise OrganizationError("Nie znaleziono organizacji.")
        current = self._decorate_organization(current)

        if actor_user.get("is_global_admin"):
            return current

        if actor_user.get("role") != "organization_admin":
            raise OrganizationPermissionError("Tylko Wlasciciel systemu albo Administrator organizacji moze edytowac organizacje.")

        actor_organization_id = actor_user.get("organization_id")
        if not actor_organization_id or int(actor_organization_id) != int(current["organization_id"]):
            raise OrganizationPermissionError("Administrator organizacji moze edytowac tylko swoja organizacje.")

        return current

    def update_organization(
        self,
        organization_id: int,
        payload: dict[str, Any],
        actor_user: dict[str, Any],
        actor_login: str,
    ) -> dict[str, Any]:
        current = self.get_organization_for_settings(organization_id, actor_user)
        if not actor_user.get("is_global_admin") and "is_active" in payload:
            requested_active = 1 if payload.get("is_active") not in {False, 0, "0", "false"} else 0
            if int(current.get("is_active") or 0) != requested_active:
                raise OrganizationPermissionError("Tylko Wlasciciel systemu moze aktywowac albo dezaktywowac organizacje.")
        normalized = self._normalize_payload(payload, current=current)
        enabled_modules = normalized.pop("enabled_modules", None)
        if enabled_modules is not None and not actor_user.get("is_global_admin"):
            if sorted(enabled_modules) != sorted(current.get("enabled_modules") or []):
                raise OrganizationPermissionError("Tylko Wlasciciel systemu moze zmieniac aktywne pakiety organizacji.")
        if normalized.get("name") and normalized["name"] != current["name"]:
            existing_by_name = self.organization_repository.get_by_name(normalized["name"])
            if existing_by_name and int(existing_by_name["organization_id"]) != organization_id:
                raise OrganizationError("Organizacja o takiej nazwie juz istnieje.")
        if normalized.get("slug") and normalized["slug"] != current["slug"]:
            existing_by_slug = self.organization_repository.get_by_slug(normalized["slug"])
            if existing_by_slug and int(existing_by_slug["organization_id"]) != organization_id:
                raise OrganizationError("Organizacja o takim identyfikatorze katalogu juz istnieje.")

        next_telegram_chat_id = self._extract_active_telegram_chat_id(normalized, fallback=current)
        current_telegram_chat_id = self._extract_active_telegram_chat_id(current)
        if next_telegram_chat_id != current_telegram_chat_id:
            if next_telegram_chat_id:
                existing_by_chat = self.organization_repository.get_by_telegram_chat_id(next_telegram_chat_id)
                if existing_by_chat and int(existing_by_chat["organization_id"]) != organization_id:
                    raise OrganizationError("Ten kanal Telegram jest juz przypisany do innej organizacji.")
        next_slack_channel_id = self._extract_active_slack_channel_id(normalized, fallback=current)
        current_slack_channel_id = self._extract_active_slack_channel_id(current)
        if next_slack_channel_id != current_slack_channel_id:
            if next_slack_channel_id:
                existing_by_channel = self.organization_repository.get_by_active_slack_channel_id(next_slack_channel_id)
                if existing_by_channel and int(existing_by_channel["organization_id"]) != organization_id:
                    raise OrganizationError("Ten kanal Slack jest juz przypisany do innej organizacji.")

        self.organization_repository.update(organization_id, normalized)
        if enabled_modules is not None and actor_user.get("is_global_admin"):
            self.organization_repository.replace_enabled_modules(
                organization_id,
                enabled_modules,
                enabled_by_user_id=self._extract_actor_user_id(actor_user),
            )
        refreshed = self.organization_repository.get_by_id(organization_id)
        assert refreshed is not None
        refreshed = self._decorate_organization(refreshed)

        self.event_repository.log(
            event_type="organization_updated",
            invoice_id=None,
            source=None,
            status_before=None,
            status_after=None,
            decision_reason=f"Zmieniono organizacje {refreshed['name']}.",
            actor=actor_login,
            organization_id=refreshed["organization_id"],
            details={
                "organization_id": organization_id,
                "updates": list(normalized.keys()),
                "enabled_modules": refreshed.get("enabled_modules") or [],
                "module_shortcuts": refreshed.get("module_shortcuts") or {},
            },
        )
        return refreshed

    def get_shared_note(
        self,
        *,
        actor_user: dict[str, Any],
        requested_organization_id: int | None,
    ) -> dict[str, Any]:
        organization_id = self.resolve_data_scope(actor_user, requested_organization_id)
        if organization_id is None:
            raise OrganizationError("Wybierz organizacje, aby otworzyc wspolna notatke.")
        organization = self.organization_repository.get_by_id(int(organization_id))
        if not organization:
            raise OrganizationError("Wybrana organizacja nie istnieje.")
        return self._build_shared_note_payload(organization)

    def update_shared_note(
        self,
        *,
        actor_user: dict[str, Any],
        actor_login: str,
        requested_organization_id: int | None,
        shared_note_text: Any,
    ) -> dict[str, Any]:
        organization_id = self.resolve_write_scope(actor_user, requested_organization_id)
        if organization_id is None:
            raise OrganizationError("Wybierz organizacje, aby zapisac wspolna notatke.")
        normalized_text = self._normalize_shared_note_text(shared_note_text)
        self.organization_repository.update(
            int(organization_id),
            {
                "shared_note_text": normalized_text,
                "shared_note_updated_at": now_iso(),
                "shared_note_updated_by_user_id": self._extract_actor_user_id(actor_user),
            },
        )
        refreshed = self.organization_repository.get_by_id(int(organization_id))
        assert refreshed is not None
        payload = self._build_shared_note_payload(refreshed)
        self.event_repository.log(
            event_type="organization_shared_note_updated",
            invoice_id=None,
            source=None,
            status_before=None,
            status_after=None,
            decision_reason=f"Zmieniono wspolna notatke organizacji {refreshed['name']}.",
            actor=actor_login,
            organization_id=int(organization_id),
            details={
                "organization_id": int(organization_id),
                "shared_note_length": len(payload["shared_note_text"]),
            },
        )
        return payload

    def organization_has_module(self, organization_id: int, module_code: str) -> bool:
        return self.organization_repository.organization_has_module(organization_id, module_code)

    def resolve_data_scope(self, actor_user: dict[str, Any], requested_organization_id: int | None) -> int | None:
        if actor_user.get("is_global_admin"):
            if requested_organization_id is None:
                return None
            organization = self.organization_repository.get_by_id(requested_organization_id)
            if not organization:
                raise OrganizationError("Wybrana organizacja nie istnieje.")
            return int(organization["organization_id"])

        organization_id = actor_user.get("organization_id")
        if not organization_id:
            raise OrganizationPermissionError("To konto nie ma przypisanej organizacji.")
        return int(organization_id)

    def resolve_write_scope(self, actor_user: dict[str, Any], requested_organization_id: int | None) -> int | None:
        scope = self.resolve_data_scope(actor_user, requested_organization_id)
        if actor_user.get("is_global_admin") and scope is None:
            raise OrganizationError("Wybierz organizacje przed wykonaniem tej operacji.")
        if scope is not None:
            organization = self.organization_repository.get_by_id(scope)
            if not organization:
                raise OrganizationError("Wybrana organizacja nie istnieje.")
            if not organization.get("is_active"):
                raise OrganizationError("Nie mozna pracowac na organizacji oznaczonej jako nieaktywna.")
        return scope

    def normalize_user_organization_id(self, actor_user: dict[str, Any] | None, payload: dict[str, Any]) -> int | None:
        raw_value = payload.get("organization_id")
        requested_organization_id = self._parse_optional_id(raw_value)

        if actor_user is None:
            return requested_organization_id

        if actor_user.get("is_global_admin"):
            if requested_organization_id is None:
                return None
            organization = self.organization_repository.get_by_id(requested_organization_id)
            if not organization:
                raise OrganizationError("Wybrana organizacja nie istnieje.")
            return int(organization["organization_id"])

        actor_organization_id = actor_user.get("organization_id")
        if not actor_organization_id:
            raise OrganizationPermissionError("To konto nie ma przypisanej organizacji.")
        if requested_organization_id not in {None, int(actor_organization_id)}:
            raise OrganizationPermissionError("Nie mozna przypisac uzytkownika do innej organizacji.")
        return int(actor_organization_id)

    def _normalize_payload(self, payload: dict[str, Any], current: dict[str, Any] | None = None) -> dict[str, Any]:
        if current is None:
            name = (payload.get("name") or "").strip()
            slug_source = payload.get("slug")
            is_active = 1 if payload.get("is_active", True) not in {False, 0, "0", "false"} else 0
            email_inbox_address = self._normalize_optional_email(payload.get("email_inbox_address"))
            email_allowed_sender = self._normalize_optional_email(payload.get("email_allowed_sender"))
            email_subject_keyword = self._normalize_optional_text(payload.get("email_subject_keyword"))
            email_integration_enabled = (
                1 if payload.get("email_integration_enabled", False) not in {False, 0, "0", "false", ""} else 0
            )
            ksef_company_identifier = self._normalize_optional_text(payload.get("ksef_company_identifier"))
            ksef_environment = self._normalize_ksef_environment(payload.get("ksef_environment"))
            ksef_integration_enabled = (
                1 if payload.get("ksef_integration_enabled", False) not in {False, 0, "0", "false", ""} else 0
            )
            if not name:
                raise OrganizationError("Nazwa organizacji jest wymagana.")
            slug = self._slugify(slug_source or name)
            if not slug:
                raise OrganizationError("Identyfikator katalogu organizacji jest wymagany.")
            self._validate_email_settings(
                email_inbox_address=email_inbox_address,
                email_allowed_sender=email_allowed_sender,
                email_integration_enabled=email_integration_enabled,
            )
            self._validate_ksef_settings(
                ksef_company_identifier=ksef_company_identifier,
                ksef_integration_enabled=ksef_integration_enabled,
            )
            delegate_data = self._normalize_ksef_delegate_fields(
                payload,
                organization_id=None,
            )
            return {
                "name": name,
                "slug": slug,
                "module_shortcuts_json": self._serialize_module_shortcuts(
                    self._normalize_module_shortcuts(payload.get("module_shortcuts"))
                ),
                **self._normalize_communication_payload(payload),
                "email_inbox_address": email_inbox_address,
                "email_allowed_sender": email_allowed_sender,
                "email_subject_keyword": email_subject_keyword,
                "email_integration_enabled": email_integration_enabled,
                "ksef_company_identifier": ksef_company_identifier,
                "ksef_environment": ksef_environment,
                "ksef_integration_enabled": ksef_integration_enabled,
                "ksef_correction_delegate_user_id": delegate_data["delegate_user_id"],
                "ksef_correction_delegate_assigned_at": delegate_data["assigned_at"],
                "ksef_correction_delegate_expires_at": delegate_data["expires_at"],
                "is_active": is_active,
                "enabled_modules": self._normalize_enabled_modules(payload.get("enabled_modules")),
            }

        updates: dict[str, Any] = {}
        if "name" in payload:
            name = (payload.get("name") or "").strip()
            if not name:
                raise OrganizationError("Nazwa organizacji jest wymagana.")
            updates["name"] = name
        if "slug" in payload:
            slug = self._slugify(payload.get("slug") or payload.get("name") or current["slug"])
            if not slug:
                raise OrganizationError("Identyfikator katalogu organizacji jest wymagany.")
            updates["slug"] = slug
        if "module_shortcuts" in payload:
            updates["module_shortcuts_json"] = self._serialize_module_shortcuts(
                self._normalize_module_shortcuts(payload.get("module_shortcuts"))
            )
        if "is_active" in payload:
            updates["is_active"] = 1 if payload.get("is_active") not in {False, 0, "0", "false"} else 0
        if self._payload_has_communication_updates(payload):
            updates.update(self._normalize_communication_payload(payload, current=current))
        if "email_inbox_address" in payload:
            updates["email_inbox_address"] = self._normalize_optional_email(payload.get("email_inbox_address"))
        if "email_allowed_sender" in payload:
            updates["email_allowed_sender"] = self._normalize_optional_email(payload.get("email_allowed_sender"))
        if "email_subject_keyword" in payload:
            updates["email_subject_keyword"] = self._normalize_optional_text(payload.get("email_subject_keyword"))
        if "email_integration_enabled" in payload:
            updates["email_integration_enabled"] = (
                1 if payload.get("email_integration_enabled") not in {False, 0, "0", "false", ""} else 0
            )
        if "ksef_company_identifier" in payload:
            updates["ksef_company_identifier"] = self._normalize_optional_text(payload.get("ksef_company_identifier"))
        if "ksef_environment" in payload:
            updates["ksef_environment"] = self._normalize_ksef_environment(payload.get("ksef_environment"))
        if "ksef_integration_enabled" in payload:
            updates["ksef_integration_enabled"] = (
                1 if payload.get("ksef_integration_enabled") not in {False, 0, "0", "false", ""} else 0
            )
        if {
            "ksef_correction_delegate_user_id",
            "ksef_correction_delegate_expires_at",
        } & set(payload):
            delegate_data = self._normalize_ksef_delegate_fields(
                payload,
                organization_id=int(current["organization_id"]),
                current=current,
            )
            updates["ksef_correction_delegate_user_id"] = delegate_data["delegate_user_id"]
            updates["ksef_correction_delegate_assigned_at"] = delegate_data["assigned_at"]
            updates["ksef_correction_delegate_expires_at"] = delegate_data["expires_at"]
        if "enabled_modules" in payload:
            updates["enabled_modules"] = self._normalize_enabled_modules(payload.get("enabled_modules"))
        self._validate_email_settings(
            email_inbox_address=updates.get("email_inbox_address", current.get("email_inbox_address")),
            email_allowed_sender=updates.get("email_allowed_sender", current.get("email_allowed_sender")),
            email_integration_enabled=updates.get("email_integration_enabled", current.get("email_integration_enabled")),
        )
        self._validate_ksef_settings(
            ksef_company_identifier=updates.get("ksef_company_identifier", current.get("ksef_company_identifier")),
            ksef_integration_enabled=updates.get("ksef_integration_enabled", current.get("ksef_integration_enabled")),
        )
        return updates

    def _decorate_organizations(self, organizations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not organizations:
            return []
        modules_map = self.organization_repository.list_enabled_modules_map(
            [int(item["organization_id"]) for item in organizations if item and item.get("organization_id")]
        )
        return [self._decorate_organization(item, modules_map=modules_map) for item in organizations]

    def _decorate_organization(
        self,
        organization: dict[str, Any],
        *,
        modules_map: dict[int, list[str]] | None = None,
    ) -> dict[str, Any]:
        decorated = dict(organization)
        module_shortcuts = self._parse_module_shortcuts_json(decorated.pop("module_shortcuts_json", None))
        communication_provider = self._normalize_communication_provider(decorated.get("communication_provider"))
        communication_config = self._parse_communication_config_json(decorated.pop("communication_config_json", None))
        if not (communication_config.get("telegram") or {}).get("chat_id"):
            communication_config["telegram"] = self._normalize_telegram_communication_config(
                {
                    "chat_id": decorated.get("telegram_chat_id"),
                    "chat_name": decorated.get("telegram_chat_name"),
                }
            )
        decorated["module_shortcuts"] = module_shortcuts
        decorated["communication_provider"] = communication_provider
        decorated["communication_config"] = communication_config
        decorated["active_communication_settings"] = dict(communication_config.get(communication_provider) or {})
        decorated["communication_provider_label"] = self._communication_provider_label(communication_provider)
        decorated["communication_target_summary"] = self._build_communication_target_summary(
            communication_provider,
            decorated["active_communication_settings"],
        )
        organization_id = int(decorated["organization_id"])
        enabled_modules = (
            modules_map.get(organization_id)
            if modules_map is not None
            else self.organization_repository.list_enabled_modules(organization_id)
        )
        decorated["enabled_modules"] = list(enabled_modules or [])
        delegate_user_id = self._parse_optional_id(decorated.get("ksef_correction_delegate_user_id"))
        decorated["ksef_correction_delegate_user_id"] = delegate_user_id
        decorated["shared_note_text"] = str(decorated.get("shared_note_text") or "")
        shared_note_updated_by_user_id = self._parse_optional_id(decorated.get("shared_note_updated_by_user_id"))
        decorated["shared_note_updated_by_user_id"] = shared_note_updated_by_user_id
        if shared_note_updated_by_user_id:
            updated_by_user = self.user_repository.get_by_id(shared_note_updated_by_user_id)
            decorated["shared_note_updated_by_name"] = (
                updated_by_user.get("display_name") or updated_by_user.get("login")
                if updated_by_user
                else None
            )
        else:
            decorated["shared_note_updated_by_name"] = None
        if delegate_user_id:
            decorated["ksef_correction_delegate_user"] = self._sanitize_delegate_user(
                self.user_repository.get_by_id(delegate_user_id),
                organization_id=organization_id,
            )
        else:
            decorated["ksef_correction_delegate_user"] = None
        return decorated

    def _normalize_enabled_modules(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            raw_values = [item.strip() for item in value.split(",")]
        else:
            raw_values = [str(item).strip() for item in list(value)]
        normalized = [item for item in raw_values if item in ORGANIZATION_MODULE_CODES]
        return sorted(set(normalized))

    def _normalize_module_shortcuts(self, value: Any) -> dict[str, str]:
        if value is None or value == "":
            return {}
        if not isinstance(value, dict):
            raise OrganizationError("Skroty modulow musza byc zapisane jako mapa modul -> skrot.")

        normalized: dict[str, str] = {}
        used_shortcuts: dict[str, str] = {}
        for raw_view, raw_shortcut in value.items():
            view = str(raw_view or "").strip()
            if not view:
                continue
            if view not in self.SUPPORTED_MODULE_SHORTCUT_VIEWS:
                raise OrganizationError(f"Nie mozna ustawic skrotu dla nieznanego modulu: {view}.")
            shortcut = self._normalize_single_module_shortcut(raw_shortcut)
            if not shortcut:
                continue
            if shortcut in used_shortcuts:
                other_view = used_shortcuts[shortcut]
                raise OrganizationError(
                    f"Skrot {shortcut} jest juz przypisany do modulu {other_view}. Kazdy skrot musi byc unikalny."
                )
            used_shortcuts[shortcut] = view
            normalized[view] = shortcut
        return dict(sorted(normalized.items()))

    def _normalize_single_module_shortcut(self, value: Any) -> str | None:
        normalized = str(value or "").strip()
        if not normalized:
            return None

        parts = [part.strip() for part in normalized.split("+") if part.strip()]
        if len(parts) < 2:
            raise OrganizationError("Skrot modulu musi miec format podobny do Ctrl+1 albo Ctrl+Shift+K.")

        raw_key = parts[-1].upper()
        seen_modifiers: set[str] = set()
        aliases = {
            "ctrl": "Ctrl",
            "control": "Ctrl",
            "alt": "Alt",
            "shift": "Shift",
        }
        for token in parts[:-1]:
            alias = aliases.get(token.lower())
            if not alias:
                raise OrganizationError("Skrot modulu moze uzywac tylko klawiszy Ctrl, Alt, Shift oraz litery lub cyfry.")
            if alias in seen_modifiers:
                raise OrganizationError("Kazdy modyfikator w skrocie modulu moze wystapic tylko raz.")
            seen_modifiers.add(alias)

        if "Ctrl" not in seen_modifiers and "Alt" not in seen_modifiers:
            raise OrganizationError("Skrot modulu musi zawierac Ctrl albo Alt, na przyklad Ctrl+1 albo Alt+2.")
        if len(raw_key) != 1 or not raw_key.isalnum():
            raise OrganizationError("Ostatni klawisz skrotu modulu musi byc pojedyncza litera albo cyfra.")

        ordered_modifiers = [name for name in ("Ctrl", "Alt", "Shift") if name in seen_modifiers]
        return "+".join([*ordered_modifiers, raw_key])

    def _serialize_module_shortcuts(self, value: dict[str, str]) -> str:
        return json.dumps(value or {}, ensure_ascii=True, sort_keys=True)

    def _parse_module_shortcuts_json(self, value: Any) -> dict[str, str]:
        if not value:
            return {}
        try:
            parsed = json.loads(str(value))
        except json.JSONDecodeError:
            return {}
        if not isinstance(parsed, dict):
            return {}
        try:
            return self._normalize_module_shortcuts(parsed)
        except OrganizationError:
            return {}

    def _extract_actor_user_id(self, actor_user: dict[str, Any] | None) -> int | None:
        raw_user_id = actor_user.get("user_id") if actor_user else None
        try:
            return int(raw_user_id) if raw_user_id is not None else None
        except (TypeError, ValueError):
            return None

    def _slugify(self, value: Any) -> str:
        normalized = re.sub(r"[^A-Za-z0-9]+", "-", str(value or "").strip().lower())
        return normalized.strip("-")

    def _payload_has_communication_updates(self, payload: dict[str, Any]) -> bool:
        return bool(
            {
                "communication_provider",
                "communication_config",
                "telegram_chat_id",
                "telegram_chat_name",
                "slack_workspace_name",
                "slack_channel_id",
                "slack_channel_name",
                "whatsapp_phone_number",
                "whatsapp_display_name",
            }
            & set(payload)
        )

    def _normalize_communication_payload(
        self,
        payload: dict[str, Any],
        *,
        current: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        provider_source = payload.get("communication_provider")
        if provider_source in {None, ""} and current is not None:
            provider_source = current.get("communication_provider")
        provider = self._normalize_communication_provider(provider_source)
        config = self._normalize_communication_config(payload, current=current)
        telegram_settings = dict(config.get("telegram") or {})
        telegram_chat_id = telegram_settings.get("chat_id") if provider == "telegram" else None
        telegram_chat_name = telegram_settings.get("chat_name") if provider == "telegram" else None
        return {
            "communication_provider": provider,
            "communication_config_json": self._serialize_communication_config(config),
            "telegram_chat_id": telegram_chat_id,
            "telegram_chat_name": telegram_chat_name,
        }

    def _normalize_communication_provider(self, value: Any) -> str:
        normalized = str(value or "").strip().lower() or "telegram"
        if normalized not in self.SUPPORTED_COMMUNICATION_PROVIDERS:
            raise OrganizationError("Komunikator organizacji musi byc ustawiony jako Telegram, Slack albo WhatsApp.")
        return normalized

    def _normalize_communication_config(
        self,
        payload: dict[str, Any],
        *,
        current: dict[str, Any] | None = None,
    ) -> dict[str, dict[str, str]]:
        base = self._parse_communication_config_json(current.get("communication_config")) if current else {}
        if current and not (base.get("telegram") or {}).get("chat_id"):
            base["telegram"] = {
                **dict(base.get("telegram") or {}),
                "chat_id": current.get("telegram_chat_id"),
                "chat_name": current.get("telegram_chat_name"),
            }
        raw_config = payload.get("communication_config")
        if isinstance(raw_config, dict):
            for provider in self.SUPPORTED_COMMUNICATION_PROVIDERS:
                if provider in raw_config and isinstance(raw_config[provider], dict):
                    base[provider] = dict(raw_config[provider])

        if {"telegram_chat_id", "telegram_chat_name"} & set(payload):
            base["telegram"] = {
                **dict(base.get("telegram") or {}),
                "chat_id": payload.get("telegram_chat_id"),
                "chat_name": payload.get("telegram_chat_name"),
            }
        if {"slack_workspace_name", "slack_channel_id", "slack_channel_name"} & set(payload):
            base["slack"] = {
                **dict(base.get("slack") or {}),
                "workspace_name": payload.get("slack_workspace_name"),
                "channel_id": payload.get("slack_channel_id"),
                "channel_name": payload.get("slack_channel_name"),
            }
        if {"whatsapp_phone_number", "whatsapp_display_name"} & set(payload):
            base["whatsapp"] = {
                **dict(base.get("whatsapp") or {}),
                "phone_number": payload.get("whatsapp_phone_number"),
                "display_name": payload.get("whatsapp_display_name"),
            }

        normalized = {
            "telegram": self._normalize_telegram_communication_config(base.get("telegram")),
            "slack": self._normalize_slack_communication_config(base.get("slack")),
            "whatsapp": self._normalize_whatsapp_communication_config(base.get("whatsapp")),
        }
        return normalized

    def _normalize_telegram_communication_config(self, value: Any) -> dict[str, str]:
        source = value if isinstance(value, dict) else {}
        return {
            "chat_id": self._normalize_telegram_chat_id(source.get("chat_id")),
            "chat_name": self._normalize_optional_text(source.get("chat_name")),
        }

    def _normalize_slack_communication_config(self, value: Any) -> dict[str, str]:
        source = value if isinstance(value, dict) else {}
        return {
            "workspace_name": self._normalize_optional_text(source.get("workspace_name")),
            "channel_id": self._normalize_optional_text(source.get("channel_id")),
            "channel_name": self._normalize_optional_text(source.get("channel_name")),
        }

    def _normalize_whatsapp_communication_config(self, value: Any) -> dict[str, str]:
        source = value if isinstance(value, dict) else {}
        return {
            "phone_number": self._normalize_whatsapp_phone_number(source.get("phone_number")),
            "display_name": self._normalize_optional_text(source.get("display_name")),
        }

    def _normalize_whatsapp_phone_number(self, value: Any) -> str | None:
        normalized = str(value or "").strip()
        if not normalized:
            return None
        compact = re.sub(r"[\s()-]+", "", normalized)
        if not re.fullmatch(r"\+?\d{6,20}", compact):
            raise OrganizationError("Numer WhatsApp musi miec format typu +48123123123.")
        return compact

    def _serialize_communication_config(self, value: dict[str, dict[str, str]]) -> str:
        return json.dumps(value or {}, ensure_ascii=True, sort_keys=True)

    def _parse_communication_config_json(self, value: Any) -> dict[str, dict[str, str]]:
        if isinstance(value, dict):
            parsed = value
        elif not value:
            parsed = {}
        else:
            try:
                parsed = json.loads(str(value))
            except json.JSONDecodeError:
                parsed = {}
        if not isinstance(parsed, dict):
            parsed = {}
        try:
            return {
                "telegram": self._normalize_telegram_communication_config(parsed.get("telegram")),
                "slack": self._normalize_slack_communication_config(parsed.get("slack")),
                "whatsapp": self._normalize_whatsapp_communication_config(parsed.get("whatsapp")),
            }
        except OrganizationError:
            return {
                "telegram": {"chat_id": None, "chat_name": None},
                "slack": {"workspace_name": None, "channel_id": None, "channel_name": None},
                "whatsapp": {"phone_number": None, "display_name": None},
            }

    def _extract_active_telegram_chat_id(
        self,
        payload: dict[str, Any],
        *,
        fallback: dict[str, Any] | None = None,
    ) -> str | None:
        provider_source = payload.get("communication_provider")
        if provider_source in {None, ""} and fallback is not None:
            provider_source = fallback.get("communication_provider")
        provider = self._normalize_communication_provider(provider_source)
        if provider != "telegram":
            return None
        if "telegram_chat_id" in payload:
            return self._normalize_telegram_chat_id(payload.get("telegram_chat_id"))
        if "communication_config_json" in payload:
            parsed = self._parse_communication_config_json(payload.get("communication_config_json"))
            return parsed.get("telegram", {}).get("chat_id")
        if "communication_config" in payload:
            parsed = self._parse_communication_config_json(payload.get("communication_config"))
            return parsed.get("telegram", {}).get("chat_id")
        if fallback is None:
            return self._normalize_telegram_chat_id(payload.get("telegram_chat_id"))
        communication_config = fallback.get("communication_config") or self._parse_communication_config_json(
            fallback.get("communication_config_json")
        )
        if isinstance(communication_config, dict):
            return self._normalize_telegram_chat_id((communication_config.get("telegram") or {}).get("chat_id"))
        return self._normalize_telegram_chat_id(fallback.get("telegram_chat_id"))

    def _extract_active_slack_channel_id(
        self,
        payload: dict[str, Any],
        *,
        fallback: dict[str, Any] | None = None,
    ) -> str | None:
        provider_source = payload.get("communication_provider")
        if provider_source in {None, ""} and fallback is not None:
            provider_source = fallback.get("communication_provider")
        provider = self._normalize_communication_provider(provider_source)
        if provider != "slack":
            return None
        if "communication_config_json" in payload:
            parsed = self._parse_communication_config_json(payload.get("communication_config_json"))
            return self._normalize_optional_text((parsed.get("slack") or {}).get("channel_id"))
        if "communication_config" in payload:
            parsed = self._parse_communication_config_json(payload.get("communication_config"))
            return self._normalize_optional_text((parsed.get("slack") or {}).get("channel_id"))
        if {"slack_workspace_name", "slack_channel_id", "slack_channel_name"} & set(payload):
            return self._normalize_optional_text(payload.get("slack_channel_id"))
        if fallback is None:
            return self._normalize_optional_text(payload.get("slack_channel_id"))
        communication_config = fallback.get("communication_config") or self._parse_communication_config_json(
            fallback.get("communication_config_json")
        )
        if isinstance(communication_config, dict):
            return self._normalize_optional_text((communication_config.get("slack") or {}).get("channel_id"))
        return self._normalize_optional_text(payload.get("slack_channel_id"))

    def _communication_provider_label(self, provider: str) -> str:
        labels = {
            "telegram": "Telegram",
            "slack": "Slack",
            "whatsapp": "WhatsApp",
        }
        return labels.get(provider, provider.title())

    def _build_communication_target_summary(self, provider: str, settings: dict[str, Any]) -> str | None:
        settings = settings or {}
        if provider == "telegram":
            return str(settings.get("chat_name") or settings.get("chat_id") or "").strip() or None
        if provider == "slack":
            return str(settings.get("channel_name") or settings.get("channel_id") or settings.get("workspace_name") or "").strip() or None
        if provider == "whatsapp":
            return str(settings.get("display_name") or settings.get("phone_number") or "").strip() or None
        return None

    def _normalize_telegram_chat_id(self, value: Any) -> str | None:
        normalized = str(value or "").strip()
        if not normalized:
            return None
        if not re.fullmatch(r"-?\d+", normalized):
            raise OrganizationError("ID kanalu Telegram musi byc liczba, na przyklad -1001234567890.")
        return normalized

    def _normalize_optional_text(self, value: Any) -> str | None:
        normalized = str(value or "").strip()
        return normalized or None

    def _normalize_shared_note_text(self, value: Any) -> str:
        normalized = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
        if len(normalized) > 20000:
            raise OrganizationError("Wspolna notatka organizacji moze miec maksymalnie 20000 znakow.")
        return normalized

    def _normalize_ksef_environment(self, value: Any) -> str:
        normalized = str(value or "").strip().lower()
        if normalized in {"", "demo", "test"}:
            return "demo"
        if normalized in {"production", "prod", "produkcyjne"}:
            return "production"
        raise OrganizationError("Srodowisko KSeF musi byc ustawione jako demo albo production.")

    def _normalize_optional_email(self, value: Any) -> str | None:
        normalized = str(value or "").strip().lower()
        if not normalized:
            return None
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
            raise OrganizationError("Adres e-mail musi miec poprawny format, na przyklad faktury@firma.pl.")
        return normalized

    def _validate_email_settings(
        self,
        *,
        email_inbox_address: str | None,
        email_allowed_sender: str | None,
        email_integration_enabled: int | bool | None,
    ) -> None:
        if email_integration_enabled and not email_inbox_address:
            raise OrganizationError("Adres skrzynki e-mail jest wymagany, gdy integracja e-mail jest aktywna.")
        if email_allowed_sender and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email_allowed_sender):
            raise OrganizationError("Dozwolony nadawca e-mail musi miec poprawny adres.")

    def _validate_ksef_settings(
        self,
        *,
        ksef_company_identifier: str | None,
        ksef_integration_enabled: int | bool | None,
    ) -> None:
        if ksef_integration_enabled and not ksef_company_identifier:
            raise OrganizationError("Identyfikator firmy w KSeF jest wymagany, gdy integracja KSeF jest aktywna.")

    def _parse_optional_id(self, value: Any) -> int | None:
        normalized = str(value or "").strip()
        if not normalized:
            return None
        if not normalized.isdigit():
            raise OrganizationError("Nieprawidlowy identyfikator organizacji.")
        return int(normalized)

    def _normalize_ksef_delegate_fields(
        self,
        payload: dict[str, Any],
        *,
        organization_id: int | None,
        current: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raw_delegate_user_id = payload.get(
            "ksef_correction_delegate_user_id",
            current.get("ksef_correction_delegate_user_id") if current else None,
        )
        raw_expires_at = payload.get(
            "ksef_correction_delegate_expires_at",
            current.get("ksef_correction_delegate_expires_at") if current else None,
        )
        delegate_user_id = self._parse_optional_id(raw_delegate_user_id)
        expires_at = self._normalize_optional_text(raw_expires_at)

        if delegate_user_id is None:
            return {
                "delegate_user_id": None,
                "assigned_at": None,
                "expires_at": None,
            }

        if not expires_at:
            raise OrganizationError("Przy wyborze tymczasowego kierownika KSeF trzeba ustawic termin wygasniecia.")

        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", expires_at):
            raise OrganizationError("Termin wygasniecia tymczasowego kierownika musi miec format daty i godziny.")

        delegate_user = self.user_repository.get_by_id(delegate_user_id)
        if not delegate_user:
            raise OrganizationError("Nie znaleziono wskazanego tymczasowego kierownika KSeF.")
        if not int(delegate_user.get("is_active") or 0):
            raise OrganizationError("Tymczasowy kierownik KSeF musi miec aktywne konto.")
        if str(delegate_user.get("role") or "") == GUEST_ROLE:
            raise OrganizationError("Gosc nie moze byc tymczasowym kierownikiem KSeF.")
        if organization_id is not None and int(delegate_user.get("organization_id") or 0) != int(organization_id):
            raise OrganizationError("Tymczasowy kierownik KSeF musi nalezec do tej samej organizacji.")

        assigned_at = current.get("ksef_correction_delegate_assigned_at") if current else None
        current_delegate_user_id = self._parse_optional_id(current.get("ksef_correction_delegate_user_id")) if current else None
        current_expires_at = self._normalize_optional_text(current.get("ksef_correction_delegate_expires_at")) if current else None
        if delegate_user_id != current_delegate_user_id or expires_at != current_expires_at:
            assigned_at = now_iso()

        return {
            "delegate_user_id": delegate_user_id,
            "assigned_at": assigned_at,
            "expires_at": expires_at,
        }

    def _sanitize_delegate_user(
        self,
        user: dict[str, Any] | None,
        *,
        organization_id: int,
    ) -> dict[str, Any] | None:
        if not user:
            return None
        if int(user.get("organization_id") or 0) != int(organization_id):
            return None
        return {
            "user_id": user["user_id"],
            "login": user.get("login"),
            "display_name": user.get("display_name") or user.get("login"),
            "role": user.get("role"),
            "is_active": bool(user.get("is_active")),
        }

    def _build_shared_note_payload(self, organization: dict[str, Any]) -> dict[str, Any]:
        updated_by_user_id = self._parse_optional_id(organization.get("shared_note_updated_by_user_id"))
        updated_by_user = self.user_repository.get_by_id(updated_by_user_id) if updated_by_user_id else None
        return {
            "organization_id": int(organization["organization_id"]),
            "organization_name": organization.get("name") or "",
            "shared_note_text": str(organization.get("shared_note_text") or ""),
            "shared_note_updated_at": organization.get("shared_note_updated_at"),
            "shared_note_updated_by_user_id": updated_by_user_id,
            "shared_note_updated_by_name": (
                updated_by_user.get("display_name") or updated_by_user.get("login")
                if updated_by_user
                else None
            ),
        }

    def _require_global_admin(self, actor_user: dict[str, Any]) -> None:
        if not actor_user.get("is_global_admin"):
            raise OrganizationPermissionError("Tylko Wlasciciel systemu moze zarzadzac organizacjami.")
