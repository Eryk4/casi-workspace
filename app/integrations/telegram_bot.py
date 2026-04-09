from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen

from app.integrations.ocr_engine import OCREngine


class TelegramBotError(ValueError):
    pass


class TelegramBotAdapter:
    def __init__(self, ocr_engine: OCREngine, bot_token: str = "", webhook_secret: str = "") -> None:
        self.ocr_engine = ocr_engine
        self.bot_token = bot_token.strip()
        self.webhook_secret = webhook_secret.strip()

    @property
    def webhook_path(self) -> str | None:
        if not self.webhook_secret:
            return None
        return f"/api/telegram/webhook/{self.webhook_secret}"

    def is_configured(self) -> bool:
        return bool(self.bot_token and self.webhook_secret)

    def integration_status(self) -> dict[str, Any]:
        return {
            "enabled": self.is_configured(),
            "mode": "aktywny" if self.is_configured() else "wylaczony",
        }

    def fetch_mock_invoice(self) -> dict[str, Any]:
        # TODO: tutaj podłącz prawdziwy Telegram bot / webhook, odbiór pliku,
        # identyfikator wiadomości, nazwę użytkownika i wywołanie OCR.
        file_name = "telegram_scan_nowy_kontrahent_2026_04_07.jpg"
        ocr_data = self.ocr_engine.extract_mock_data(file_name)
        return {
            "incoming_date": "2026-04-07",
            "source": "TELEGRAM",
            "file_name": file_name,
            "document_type": "zdjecie",
            "invoice_number": "TG/2026/04/07",
            "ksef_number": "",
            "issuer_nip": "9988877766",
            "issuer_name": "Nowy Dostawca Instalacje",
            "issue_date": "2026-04-07",
            "sale_date": "2026-04-07",
            "gross_amount": 442.80,
            "currency": "PLN",
            "source_external_id": "telegram-wiadomosc-2026-04-07-1457",
            "source_sender_name": "eryklach95",
            "source_sender_id": "582114092",
            "source_metadata": {
                "kanal": "Bot Telegram / czat operacyjny",
                "typ_wiadomosci": "upload_zdjecia",
                "nazwa_pliku_wejsciowego": file_name,
            },
            "notes": "Import testowy z Telegrama z OCR i zapisem nadawcy.",
            **ocr_data,
        }

    def create_invoice_payload_from_update(self, update: dict[str, Any]) -> dict[str, Any]:
        if not self.is_configured():
            raise TelegramBotError(
                "Integracja Telegram nie jest skonfigurowana. Ustaw token bota i sekret webhooka."
            )

        message = self._extract_message(update)
        attachment = self._extract_attachment(message)
        downloaded = self._download_file(attachment["file_id"], attachment["suggested_file_name"])
        file_name = downloaded["file_name"]
        ocr_data = self.ocr_engine.extract_data(file_name, downloaded["content"])
        incoming_date = self._resolve_incoming_date(message)
        sender_name = self._resolve_sender_name(message)
        sender_id = self._resolve_sender_id(message)
        message_id = message.get("message_id")
        source_external_id = self._build_source_external_id(message)

        payload = {
            "incoming_date": incoming_date,
            "source": "TELEGRAM",
            "file_name": file_name,
            "document_type": attachment["document_type"],
            "invoice_number": self._fallback_invoice_number(incoming_date, message_id),
            "ksef_number": "",
            "issuer_nip": "",
            "issuer_name": "Dokument z Telegrama",
            "issue_date": incoming_date,
            "sale_date": incoming_date,
            "gross_amount": 0.0,
            "currency": "PLN",
            "source_external_id": source_external_id,
            "source_sender_name": sender_name,
            "source_sender_id": sender_id,
            "source_metadata": {
                "kanal": "Webhook Telegram",
                "typ_wiadomosci": attachment["message_type"],
                "chat_id": (message.get("chat") or {}).get("id"),
                "chat_typ": (message.get("chat") or {}).get("type"),
                "caption": message.get("caption") or "",
                "telegram_message_id": message_id,
                "telegram_file_id": attachment["file_id"],
                "telegram_file_unique_id": attachment.get("file_unique_id"),
                "telegram_file_path": downloaded.get("telegram_file_path"),
            },
            "notes": "Dodano dokument z webhooka Telegram.",
            "document_bytes": downloaded["content"],
            **ocr_data,
        }

        for key in ("invoice_number", "ksef_number", "issuer_nip", "issuer_name", "issue_date", "sale_date", "gross_amount", "currency"):
            if ocr_data.get(key) not in (None, ""):
                payload[key] = ocr_data[key]

        return payload

    def _extract_message(self, update: dict[str, Any]) -> dict[str, Any]:
        for key in ("message", "edited_message", "channel_post", "edited_channel_post"):
            message = update.get(key)
            if isinstance(message, dict):
                return message
        raise TelegramBotError("Webhook Telegram nie zawiera obsługiwanej wiadomości.")

    def _extract_attachment(self, message: dict[str, Any]) -> dict[str, Any]:
        if isinstance(message.get("document"), dict):
            document = message["document"]
            file_name = str(document.get("file_name") or "").strip()
            if not file_name:
                mime_type = str(document.get("mime_type") or "").strip().lower()
                suffix = {
                    "application/pdf": ".pdf",
                    "image/jpeg": ".jpg",
                    "image/png": ".png",
                }.get(mime_type, ".bin")
                file_name = f"telegram_dokument_{document.get('file_unique_id') or message.get('message_id')}{suffix or '.bin'}"
            extension = Path(file_name).suffix.lower()
            if extension == ".pdf":
                message_type = "upload_pdf"
                document_type = "pdf"
            else:
                message_type = "upload_pliku"
                document_type = "plik"
            return {
                "file_id": str(document.get("file_id") or ""),
                "file_unique_id": document.get("file_unique_id"),
                "suggested_file_name": file_name,
                "message_type": message_type,
                "document_type": document_type,
            }

        photos = message.get("photo") or []
        if isinstance(photos, list) and photos:
            best_photo = max(photos, key=lambda item: int(item.get("file_size") or 0))
            return {
                "file_id": str(best_photo.get("file_id") or ""),
                "file_unique_id": best_photo.get("file_unique_id"),
                "suggested_file_name": f"telegram_zdjecie_{best_photo.get('file_unique_id') or message.get('message_id')}.jpg",
                "message_type": "upload_zdjecia",
                "document_type": "zdjecie",
            }

        raise TelegramBotError("Wiadomość Telegram nie zawiera obsługiwanego PDF-a ani zdjęcia.")

    def _download_file(self, file_id: str, suggested_file_name: str) -> dict[str, Any]:
        if not file_id:
            raise TelegramBotError("Brak identyfikatora pliku Telegram.")
        if not self.bot_token:
            raise TelegramBotError("Brak tokenu bota Telegram.")

        file_info = self._telegram_api_json(f"https://api.telegram.org/bot{self.bot_token}/getFile?file_id={quote(file_id)}")
        file_path = (((file_info or {}).get("result") or {}).get("file_path") or "").strip()
        if not file_path:
            raise TelegramBotError("Telegram nie zwrócił ścieżki pliku do pobrania.")

        download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
        try:
            with urlopen(download_url, timeout=20) as response:
                content = response.read()
        except (HTTPError, URLError) as error:
            raise TelegramBotError(f"Nie udało się pobrać pliku z Telegrama: {error}") from error

        downloaded_name = Path(file_path).name or suggested_file_name
        final_name = suggested_file_name or downloaded_name or "telegram_plik.bin"

        return {
            "file_name": final_name,
            "content": content,
            "telegram_file_path": file_path,
        }

    def _telegram_api_json(self, url: str) -> dict[str, Any]:
        try:
            with urlopen(url, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, json.JSONDecodeError) as error:
            raise TelegramBotError(f"Nie udało się pobrać danych z Telegrama: {error}") from error

    def _resolve_incoming_date(self, message: dict[str, Any]) -> str:
        raw_timestamp = message.get("date")
        if raw_timestamp in (None, ""):
            return datetime.now(timezone.utc).date().isoformat()
        try:
            return datetime.fromtimestamp(int(raw_timestamp), tz=timezone.utc).date().isoformat()
        except (TypeError, ValueError, OSError):
            return datetime.now(timezone.utc).date().isoformat()

    def _resolve_sender_name(self, message: dict[str, Any]) -> str:
        sender = message.get("from") or {}
        username = str(sender.get("username") or "").strip()
        if username:
            return username

        parts = [str(sender.get("first_name") or "").strip(), str(sender.get("last_name") or "").strip()]
        combined = " ".join(part for part in parts if part).strip()
        if combined:
            return combined

        sender_chat = message.get("sender_chat") or {}
        title = str(sender_chat.get("title") or "").strip()
        if title:
            return title
        return "Nieznany użytkownik Telegram"

    def _resolve_sender_id(self, message: dict[str, Any]) -> str:
        sender = message.get("from") or {}
        if sender.get("id") is not None:
            return str(sender["id"])
        sender_chat = message.get("sender_chat") or {}
        if sender_chat.get("id") is not None:
            return str(sender_chat["id"])
        return ""

    def _build_source_external_id(self, message: dict[str, Any]) -> str:
        chat_id = (message.get("chat") or {}).get("id")
        message_id = message.get("message_id")
        if chat_id is None or message_id is None:
            return "telegram-wiadomosc-bez-id"
        return f"telegram-{chat_id}-{message_id}"

    def _fallback_invoice_number(self, incoming_date: str, message_id: Any) -> str:
        compact_date = incoming_date.replace("-", "")
        return f"TG/{compact_date}/{message_id or 'brak-id'}"
