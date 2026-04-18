from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from app.integrations.ocr_engine import OCREngine


class SlackBotError(ValueError):
    pass


class SlackBotAdapter:
    def __init__(self, ocr_engine: OCREngine, bot_token: str = "", signing_secret: str = "") -> None:
        self.ocr_engine = ocr_engine
        self.bot_token = bot_token.strip()
        self.signing_secret = signing_secret.strip()

    def configure(self, *, bot_token: str = "", signing_secret: str = "") -> None:
        self.bot_token = str(bot_token or "").strip()
        self.signing_secret = str(signing_secret or "").strip()

    @property
    def webhook_path(self) -> str | None:
        if not self.signing_secret:
            return None
        return "/api/slack/events"

    def is_configured(self) -> bool:
        return bool(self.bot_token and self.signing_secret)

    def can_send_messages(self) -> bool:
        return bool(self.bot_token)

    def integration_status(self) -> dict[str, Any]:
        mode = "aktywny" if self.is_configured() else "czesciowy" if (self.bot_token or self.signing_secret) else "wylaczony"
        return {
            "enabled": self.is_configured(),
            "outbound_enabled": self.can_send_messages(),
            "mode": mode,
        }

    def verify_request(self, headers: Any, raw_body: bytes) -> bool:
        if not self.signing_secret:
            raise SlackBotError("Brak Slack signing secret do weryfikacji webhooka.")

        signature = str(headers.get("X-Slack-Signature") or headers.get("x-slack-signature") or "").strip()
        timestamp = str(headers.get("X-Slack-Request-Timestamp") or headers.get("x-slack-request-timestamp") or "").strip()
        if not signature or not timestamp:
            return False

        try:
            request_timestamp = int(timestamp)
        except (TypeError, ValueError):
            return False

        now_timestamp = int(time.time())
        if abs(now_timestamp - request_timestamp) > 60 * 5:
            return False

        base_string = f"v0:{request_timestamp}:{raw_body.decode('utf-8')}".encode("utf-8")
        expected_signature = "v0=" + hmac.new(
            self.signing_secret.encode("utf-8"),
            base_string,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected_signature, signature)

    def send_text_message(self, channel_id: str, text: str) -> dict[str, Any]:
        normalized_channel_id = str(channel_id or "").strip()
        normalized_text = str(text or "").strip()
        if not self.can_send_messages():
            raise SlackBotError("Brak tokenu bota Slack do wysylki wiadomosci.")
        if not normalized_channel_id:
            raise SlackBotError("Brak identyfikatora kanalu Slack do wysylki wiadomosci.")
        if not normalized_text:
            raise SlackBotError("Brak tresci wiadomosci Slack.")

        request = self._authorized_request(
            "https://slack.com/api/chat.postMessage",
            data=json.dumps({"channel": normalized_channel_id, "text": normalized_text}).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        return self._slack_api_json(request)

    def fetch_mock_invoice(self) -> dict[str, Any]:
        file_name = "slack_faktura_testowa_2026_04_18.pdf"
        ocr_data = self.ocr_engine.extract_mock_data(file_name)
        return {
            "incoming_date": "2026-04-18",
            "source": "SLACK",
            "file_name": file_name,
            "document_type": "pdf",
            "invoice_number": "SL/2026/04/18",
            "ksef_number": "",
            "issuer_nip": "5544332211",
            "issuer_name": "Slack Dostawca Sp. z o.o.",
            "issue_date": "2026-04-18",
            "sale_date": "2026-04-18",
            "gross_amount": 318.60,
            "currency": "PLN",
            "source_external_id": "slack-event-test-2026-04-18",
            "source_sender_name": "Slack user U123456",
            "source_sender_id": "U123456",
            "source_metadata": {
                "kanal": "Webhook Slack",
                "typ_wiadomosci": "upload_pdf",
                "slack_channel_id": "C0123456789",
                "slack_channel_name": "#faktury-test",
                "slack_file_id": "F0123456789",
            },
            "notes": "Import testowy ze Slacka z OCR i zapisem kanalu.",
            **ocr_data,
        }

    def create_invoice_payload_from_event(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        if not self.is_configured():
            raise SlackBotError(
                "Integracja Slack nie jest skonfigurowana. Ustaw token bota i signing secret."
            )

        if str(payload.get("type") or "").strip() != "event_callback":
            return None

        event = payload.get("event")
        if not isinstance(event, dict):
            return None

        file_info = self._resolve_file_info(event)
        if not file_info:
            return None

        document_descriptor = self._resolve_document_descriptor(file_info)
        channel_context = self._resolve_channel_context(event, file_info)
        downloaded = self._download_private_file(
            str(file_info.get("url_private_download") or file_info.get("url_private") or "").strip(),
            document_descriptor["suggested_file_name"],
        )
        file_name = downloaded["file_name"]
        ocr_data = self.ocr_engine.extract_data(file_name, downloaded["content"])
        incoming_date = self._resolve_incoming_date(event, file_info)
        sender_id = self._resolve_sender_id(event, file_info)
        sender_name = self._resolve_sender_name(event, file_info, sender_id)

        invoice_payload = {
            "incoming_date": incoming_date,
            "source": "SLACK",
            "file_name": file_name,
            "document_type": document_descriptor["document_type"],
            "invoice_number": self._fallback_invoice_number(incoming_date, file_info),
            "ksef_number": "",
            "issuer_nip": "",
            "issuer_name": "Dokument ze Slacka",
            "issue_date": incoming_date,
            "sale_date": incoming_date,
            "gross_amount": 0.0,
            "currency": "PLN",
            "source_external_id": self._build_source_external_id(payload, event, file_info),
            "source_sender_name": sender_name,
            "source_sender_id": sender_id,
            "source_metadata": {
                "kanal": "Webhook Slack",
                "typ_wiadomosci": document_descriptor["message_type"],
                "slack_event_type": event.get("type"),
                "slack_event_id": payload.get("event_id"),
                "slack_event_ts": event.get("event_ts") or event.get("ts"),
                "slack_team_id": payload.get("team_id"),
                "slack_api_app_id": payload.get("api_app_id"),
                "slack_channel_id": channel_context["channel_id"],
                "slack_channel_name": channel_context["channel_name"],
                "slack_file_id": file_info.get("id"),
                "slack_permalink": file_info.get("permalink") or file_info.get("permalink_public"),
            },
            "notes": "Dodano dokument z webhooka Slack.",
            "document_bytes": downloaded["content"],
            **ocr_data,
        }

        for key in (
            "invoice_number",
            "ksef_number",
            "issuer_nip",
            "issuer_name",
            "issue_date",
            "sale_date",
            "gross_amount",
            "currency",
        ):
            if ocr_data.get(key) not in (None, ""):
                invoice_payload[key] = ocr_data[key]

        return invoice_payload

    def _resolve_file_info(self, event: dict[str, Any]) -> dict[str, Any] | None:
        event_type = str(event.get("type") or "").strip()
        if event_type == "file_shared":
            file_id = str(event.get("file_id") or "").strip()
            if not file_id:
                return None
            return self._fetch_file_info(file_id)

        if event_type != "message":
            return None

        files = event.get("files")
        if isinstance(files, list):
            for file_entry in files:
                resolved = self._hydrate_file_info(file_entry)
                if resolved:
                    return resolved

        file_id = str(event.get("file_id") or "").strip()
        if file_id:
            return self._fetch_file_info(file_id)
        return None

    def _hydrate_file_info(self, value: Any) -> dict[str, Any] | None:
        if not isinstance(value, dict):
            return None
        if value.get("url_private_download") or value.get("url_private"):
            return dict(value)
        file_id = str(value.get("id") or "").strip()
        if not file_id:
            return None
        return self._fetch_file_info(file_id)

    def _fetch_file_info(self, file_id: str) -> dict[str, Any]:
        normalized_file_id = str(file_id or "").strip()
        if not normalized_file_id:
            raise SlackBotError("Brak identyfikatora pliku Slack.")

        request = self._authorized_request(
            f"https://slack.com/api/files.info?{urlencode({'file': normalized_file_id})}",
            method="GET",
        )
        payload = self._slack_api_json(request)
        file_info = payload.get("file")
        if not isinstance(file_info, dict):
            raise SlackBotError("Slack nie zwrocil szczegolow pliku.")
        return file_info

    def _download_private_file(self, download_url: str, suggested_file_name: str) -> dict[str, Any]:
        normalized_url = str(download_url or "").strip()
        if not normalized_url:
            raise SlackBotError("Slack nie zwrocil adresu pobierania pliku.")

        request = self._authorized_request(normalized_url, method="GET")
        try:
            with urlopen(request, timeout=20) as response:
                content = response.read()
        except (HTTPError, URLError) as error:
            raise SlackBotError(f"Nie udalo sie pobrac pliku ze Slacka: {error}") from error

        file_name = str(suggested_file_name or "").strip() or "slack_plik.bin"
        return {
            "file_name": file_name,
            "content": content,
        }

    def _slack_api_json(self, request_or_url: str | Request) -> dict[str, Any]:
        try:
            with urlopen(request_or_url, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, json.JSONDecodeError) as error:
            raise SlackBotError(f"Nie udalo sie pobrac danych ze Slacka: {error}") from error
        if not isinstance(payload, dict):
            raise SlackBotError("Slack zwrocil nieprawidlowy format odpowiedzi.")
        if payload.get("ok") is False:
            raise SlackBotError(str(payload.get("error") or "Slack zwrocil blad API."))
        return payload

    def _authorized_request(
        self,
        url: str,
        *,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        method: str = "GET",
    ) -> Request:
        if not self.bot_token:
            raise SlackBotError("Brak tokenu bota Slack.")
        normalized_headers = {"Authorization": f"Bearer {self.bot_token}"}
        if headers:
            normalized_headers.update(headers)
        return Request(url, data=data, headers=normalized_headers, method=method)

    def _resolve_document_descriptor(self, file_info: dict[str, Any]) -> dict[str, str]:
        file_name = str(file_info.get("name") or "").strip()
        file_id = str(file_info.get("id") or "").strip()
        if not file_name:
            file_name = f"slack_plik_{file_id or 'document'}.bin"

        extension = Path(file_name).suffix.lower()
        mime_type = str(file_info.get("mimetype") or "").strip().lower()
        if mime_type == "application/pdf" or extension == ".pdf":
            return {
                "suggested_file_name": file_name,
                "message_type": "upload_pdf",
                "document_type": "pdf",
            }
        if mime_type.startswith("image/") or extension in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            return {
                "suggested_file_name": file_name,
                "message_type": "upload_zdjecia",
                "document_type": "zdjecie",
            }
        return {
            "suggested_file_name": file_name,
            "message_type": "upload_pliku",
            "document_type": "plik",
        }

    def _resolve_channel_context(self, event: dict[str, Any], file_info: dict[str, Any]) -> dict[str, str | None]:
        channel_id = str(event.get("channel") or "").strip() or None
        channel_name = str(event.get("channel_name") or "").strip() or None
        if channel_id or channel_name:
            return {"channel_id": channel_id, "channel_name": channel_name}

        shares = file_info.get("shares") or {}
        if isinstance(shares, dict):
            for visibility_key in ("private", "public"):
                visibility = shares.get(visibility_key) or {}
                if not isinstance(visibility, dict):
                    continue
                for share_items in visibility.values():
                    if not isinstance(share_items, list):
                        continue
                    for share in share_items:
                        if not isinstance(share, dict):
                            continue
                        channel_id = str(share.get("channel_id") or "").strip() or None
                        channel_name = str(share.get("channel_name") or "").strip() or None
                        if channel_id or channel_name:
                            return {"channel_id": channel_id, "channel_name": channel_name}

        channels = file_info.get("channels")
        if isinstance(channels, list) and channels:
            first_channel = str(channels[0] or "").strip() or None
            if first_channel:
                return {"channel_id": first_channel, "channel_name": None}
        return {"channel_id": None, "channel_name": None}

    def _resolve_incoming_date(self, event: dict[str, Any], file_info: dict[str, Any]) -> str:
        candidates = (
            file_info.get("created"),
            event.get("event_ts"),
            event.get("ts"),
        )
        for candidate in candidates:
            normalized = str(candidate or "").strip()
            if not normalized:
                continue
            seconds_text = normalized.split(".", 1)[0]
            try:
                return datetime.fromtimestamp(int(seconds_text), tz=timezone.utc).date().isoformat()
            except (TypeError, ValueError, OSError):
                continue
        return datetime.now(timezone.utc).date().isoformat()

    def _resolve_sender_id(self, event: dict[str, Any], file_info: dict[str, Any]) -> str | None:
        for candidate in (event.get("user"), file_info.get("user")):
            normalized = str(candidate or "").strip()
            if normalized:
                return normalized
        return None

    def _resolve_sender_name(self, event: dict[str, Any], file_info: dict[str, Any], sender_id: str | None) -> str | None:
        for candidate in (
            event.get("username"),
            file_info.get("username"),
            file_info.get("user_profile", {}).get("display_name") if isinstance(file_info.get("user_profile"), dict) else None,
            file_info.get("title"),
        ):
            normalized = str(candidate or "").strip()
            if normalized:
                return normalized
        if sender_id:
            return f"Slack user {sender_id}"
        return "Slack"

    def _build_source_external_id(self, payload: dict[str, Any], event: dict[str, Any], file_info: dict[str, Any]) -> str:
        for prefix, candidate in (
            ("event", payload.get("event_id")),
            ("file", file_info.get("id")),
            ("ts", event.get("event_ts") or event.get("ts")),
        ):
            normalized = str(candidate or "").strip()
            if normalized:
                return f"slack:{prefix}:{normalized}"
        raise SlackBotError("Slack webhook nie zawiera identyfikatora zdarzenia ani pliku.")

    def _fallback_invoice_number(self, incoming_date: str, file_info: dict[str, Any]) -> str:
        file_id = str(file_info.get("id") or "").strip()
        suffix = file_id or "dokument"
        return f"SLACK/{incoming_date.replace('-', '/')}/{quote(suffix, safe='')}"
