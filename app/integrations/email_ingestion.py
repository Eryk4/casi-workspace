from __future__ import annotations

import hashlib
import imaplib
from datetime import datetime, timezone
from email.parser import BytesParser
from email.policy import default
from email.utils import getaddresses, parsedate_to_datetime
from pathlib import Path
from typing import Any, TYPE_CHECKING

from app.config import (
    EMAIL_FETCH_LIMIT,
    EMAIL_IMAP_FOLDER,
    EMAIL_IMAP_HOST,
    EMAIL_IMAP_PASSWORD,
    EMAIL_IMAP_PORT,
    EMAIL_IMAP_USE_SSL,
    EMAIL_IMAP_USERNAME,
)
from app.integrations.ocr_engine import OCREngine

if TYPE_CHECKING:
    from app.integrations.email_google_oauth import EmailGoogleOAuthAdapter
    from app.repositories.email_oauth_repository import EmailOAuthRepository


class EmailIngestionError(RuntimeError):
    pass


class EmailIngestionAdapter:
    SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp", ".xml"}
    SUPPORTED_CONTENT_TYPES = {
        "application/pdf",
        "application/xml",
        "text/xml",
        "image/jpeg",
        "image/png",
        "image/bmp",
        "image/tiff",
        "image/webp",
    }

    def __init__(
        self,
        ocr_engine: OCREngine | None = None,
        *,
        host: str = "",
        port: int | None = None,
        username: str = "",
        password: str = "",
        folder: str = "",
        use_ssl: bool | None = None,
        fetch_limit: int | None = None,
        oauth_repository: EmailOAuthRepository | None = None,
        google_oauth_adapter: EmailGoogleOAuthAdapter | None = None,
    ) -> None:
        self.ocr_engine = ocr_engine or OCREngine()
        self.host = (host or EMAIL_IMAP_HOST or "").strip()
        self.port = int(port or EMAIL_IMAP_PORT or 993)
        self.username = (username or EMAIL_IMAP_USERNAME or "").strip()
        self.password = password or EMAIL_IMAP_PASSWORD or ""
        self.folder = (folder or EMAIL_IMAP_FOLDER or "INBOX").strip() or "INBOX"
        self.use_ssl = EMAIL_IMAP_USE_SSL if use_ssl is None else bool(use_ssl)
        self.fetch_limit = max(int(fetch_limit or EMAIL_FETCH_LIMIT or 30), 1)
        self.oauth_repository = oauth_repository
        self.google_oauth_adapter = google_oauth_adapter

    def integration_status(self) -> dict[str, Any]:
        configured = self.is_configured()
        google_connection = self._resolve_google_connection(refresh_if_needed=False)
        mailbox_address = self.mailbox_address()
        mode = "not_configured"
        if google_connection:
            mode = "google_oauth"
        elif self.host and self.username and self.password:
            mode = "imap"
        return {
            "enabled": configured,
            "configured": configured,
            "mode": mode,
            "routing_mode": "central_mailbox",
            "folder": self.folder,
            "fetch_limit": self.fetch_limit,
            "host": self.host,
            "mailbox_address": mailbox_address,
            "uses_google_oauth": bool(google_connection),
            "google_email": google_connection.get("google_email") if google_connection else "",
        }

    def test_connection(self, *, limit: int | None = None) -> dict[str, Any]:
        if not self.is_configured():
            raise EmailIngestionError(
                "Integracja e-mail nie jest jeszcze skonfigurowana na poziomie systemu. Uzupelnij ustawienia IMAP."
            )

        client = None
        preview_limit = max(int(limit or 5), 1)
        try:
            client = self._connect()
            status, _ = client.select(self.folder, readonly=True)
            if status != "OK":
                raise EmailIngestionError("Nie udalo sie otworzyc folderu e-mail do testu polaczenia.")

            status, data = client.uid("search", None, "ALL")
            if status != "OK":
                raise EmailIngestionError("Nie udalo sie pobrac listy wiadomosci e-mail do testu.")

            raw_ids = data[0] if data else b""
            message_ids = [item.decode("utf-8", errors="ignore") for item in raw_ids.split() if item]
            latest_ids = list(reversed(message_ids[-preview_limit:]))
            return {
                "connected": True,
                "host": self.host,
                "port": self.port,
                "folder": self.folder,
                "use_ssl": self.use_ssl,
                "username_masked": self._mask_login(self.mailbox_address() or self.username),
                "message_count": len(message_ids),
                "preview_uids": latest_ids,
            }
        except EmailIngestionError:
            raise
        except (imaplib.IMAP4.error, OSError) as error:
            raise EmailIngestionError(self._friendly_connection_error_message(error)) from error
        finally:
            if client is not None:
                try:
                    client.logout()
                except Exception:
                    pass

    def is_configured(self) -> bool:
        return bool(self.host and ((self.username and self.password) or self._resolve_google_connection(refresh_if_needed=False)))

    def mailbox_address(self) -> str:
        google_connection = self._resolve_google_connection(refresh_if_needed=False)
        if google_connection and google_connection.get("google_email"):
            return str(google_connection.get("google_email") or "").strip()
        return self.username

    def fetch_invoice_candidates(
        self,
        organization: dict[str, Any] | None = None,
        *,
        limit: int | None = None,
        trigger_mode: str = "manual",
    ) -> dict[str, Any]:
        if not self.is_configured():
            raise EmailIngestionError(
                "Integracja e-mail nie jest jeszcze skonfigurowana na poziomie systemu. Uzupelnij ustawienia IMAP."
            )

        organization = organization or {}
        mailbox_snapshot = self.fetch_mailbox_documents(limit=limit)
        candidates: list[dict[str, Any]] = []
        matched_message_ids: set[str] = set()

        for document in mailbox_snapshot["documents"]:
            if not self._document_matches_organization(document, organization):
                continue
            matched_message_ids.add(str(document.get("imap_uid") or ""))
            candidates.append(
                self._build_organization_candidate(
                    document,
                    organization,
                    trigger_mode=trigger_mode,
                )
            )

        return {
            "candidates": candidates,
            "checked_message_count": int(mailbox_snapshot["message_count"]),
            "matched_message_count": len([item for item in matched_message_ids if item]),
            "matched_attachment_count": len(candidates),
            "routing_mode": "central_mailbox",
        }

    def fetch_mailbox_documents(self, *, limit: int | None = None) -> dict[str, Any]:
        if not self.is_configured():
            raise EmailIngestionError(
                "Integracja e-mail nie jest jeszcze skonfigurowana na poziomie systemu. Uzupelnij ustawienia IMAP."
            )

        message_records = self._list_recent_messages(limit or self.fetch_limit)
        documents: list[dict[str, Any]] = []
        for message_uid, message in message_records:
            documents.extend(
                self._build_documents_from_message(
                    message_uid=message_uid,
                    message=message,
                )
            )
        return {
            "message_count": len(message_records),
            "documents": documents,
            "routing_mode": "central_mailbox",
        }

    def fetch_mock_invoice(self, organization: dict[str, Any] | None = None) -> dict[str, Any]:
        organization = organization or {}
        organization_slug = str(organization.get("slug") or "organizacja").strip() or "organizacja"
        inbox_address = str(organization.get("email_inbox_address") or "faktury@twojafirma.pl").strip()
        allowed_sender = str(organization.get("email_allowed_sender") or "faktury@marketing-operacyjny.pl").strip()
        subject_keyword = str(organization.get("email_subject_keyword") or "Faktura").strip() or "Faktura"

        return {
            "incoming_date": "2026-04-07",
            "source": "EMAIL",
            "file_name": "mail_fv_marketing_2026_04_07.pdf",
            "document_type": "pdf",
            "invoice_number": "FV/MAIL/100/04/2026",
            "ksef_number": "",
            "issuer_nip": "8943001122",
            "issuer_name": "Agencja Marketing Operacyjny",
            "issue_date": "2026-04-06",
            "sale_date": "2026-04-06",
            "gross_amount": 1890.00,
            "currency": "PLN",
            "source_external_id": f"email-{organization_slug}-wiadomosc-2026-04-07-001",
            "source_sender_name": allowed_sender,
            "source_metadata": {
                "temat": f"{subject_keyword} FV/MAIL/100/04/2026",
                "skrzynka": inbox_address,
                "tryb": "manual-check-mock",
            },
            "notes": "Import testowy z recznego sprawdzenia e-maila.",
        }

    def _list_recent_messages(self, limit: int) -> list[tuple[str, Any]]:
        client = None
        try:
            client = self._connect()
            status, _ = client.select(self.folder, readonly=True)
            if status != "OK":
                raise EmailIngestionError("Nie udalo sie otworzyc folderu e-mail do importu.")

            status, data = client.uid("search", None, "ALL")
            if status != "OK":
                raise EmailIngestionError("Nie udalo sie pobrac listy wiadomosci e-mail.")

            raw_ids = data[0] if data else b""
            message_ids = [item for item in raw_ids.split() if item]
            message_ids = list(reversed(message_ids[-limit:]))

            parsed_messages: list[tuple[str, Any]] = []
            for message_id in message_ids:
                status, fetch_data = client.uid("fetch", message_id, "(RFC822)")
                if status != "OK":
                    continue
                raw_message = self._extract_raw_message(fetch_data)
                if not raw_message:
                    continue
                message = BytesParser(policy=default).parsebytes(raw_message)
                parsed_messages.append((message_id.decode("utf-8", errors="ignore"), message))
            return parsed_messages
        except EmailIngestionError:
            raise
        except (imaplib.IMAP4.error, OSError) as error:
            raise EmailIngestionError(self._friendly_connection_error_message(error)) from error
        finally:
            if client is not None:
                try:
                    client.logout()
                except Exception:
                    pass

    def _connect(self):
        client_factory = imaplib.IMAP4_SSL if self.use_ssl else imaplib.IMAP4
        client = client_factory(self.host, self.port)
        google_connection = self._resolve_google_connection(refresh_if_needed=True)
        if google_connection:
            google_email = str(google_connection.get("google_email") or "").strip()
            access_token = str(google_connection.get("access_token") or "").strip()
            if not google_email or not access_token:
                raise EmailIngestionError("Polaczenie Google Workspace dla e-mail jest niepelne. Polacz skrzynke ponownie.")
            if not self.google_oauth_adapter:
                raise EmailIngestionError("Brakuje adaptera OAuth Google dla skrzynki e-mail.")
            xoauth2_payload = self.google_oauth_adapter.build_xoauth2_string(google_email, access_token)
            client.authenticate("XOAUTH2", lambda _: xoauth2_payload)
            return client
        client.login(self.username, self.password)
        return client

    def _friendly_connection_error_message(self, error: Exception) -> str:
        raw_message = str(error or "").strip()
        normalized = raw_message.lower()
        using_google_oauth = bool(self._resolve_google_connection(refresh_if_needed=False))

        auth_markers = [
            "application-specific password",
            "app password",
            "username and password not accepted",
            "invalid credentials",
            "authenticationfailed",
            "authentication failed",
            "login failed",
            "web login required",
            "not authenticated",
        ]
        network_markers = [
            "timed out",
            "timeout",
            "name or service not known",
            "getaddrinfo failed",
            "connection refused",
            "network is unreachable",
            "temporary failure",
        ]

        if any(marker in normalized for marker in auth_markers):
            if using_google_oauth:
                return (
                    "Google Workspace odrzucil polaczenie XOAUTH2. "
                    "Rozlacz i polacz centralna skrzynke ponownie, aby odswiezyc zgode dostepu."
                )
            return (
                "Logowanie do IMAP zostalo odrzucone. Dla Google Workspace / Gmail uzyj pelnego adresu skrzynki, "
                "hasla aplikacji Google i upewnij sie, ze IMAP jest wlaczony."
            )
        if any(marker in normalized for marker in network_markers) or isinstance(error, OSError):
            return "Nie udalo sie polaczyc z serwerem IMAP. Sprawdz host, port, SSL i polaczenie z internetem."
        return "Nie udalo sie polaczyc ze skrzynka e-mail. Sprawdz ustawienia IMAP."

    def _resolve_google_connection(self, *, refresh_if_needed: bool) -> dict[str, Any] | None:
        if not self.oauth_repository:
            return None
        connection = self.oauth_repository.get_google_connection()
        if not connection:
            return None
        if not refresh_if_needed or not self._token_expired(connection.get("token_expires_at")):
            return connection
        refresh_token = str(connection.get("refresh_token") or "").strip()
        if not refresh_token:
            return connection
        if not self.google_oauth_adapter:
            return connection
        try:
            refreshed = self.google_oauth_adapter.refresh_tokens(refresh_token)
        except Exception as error:
            raise EmailIngestionError(
                "Nie udalo sie odswiezyc polaczenia Google Workspace dla skrzynki e-mail. Polacz skrzynke ponownie."
            ) from error
        refreshed_payload = {
            "google_email": connection.get("google_email"),
            "access_token": refreshed["access_token"],
            "refresh_token": refreshed.get("refresh_token") or refresh_token,
            "token_expires_at": refreshed["token_expires_at"],
            "scope": refreshed.get("scope") or connection.get("scope"),
        }
        self.oauth_repository.upsert_google_connection(refreshed_payload, created_by_user_id=connection.get("created_by_user_id"))
        return self.oauth_repository.get_google_connection()

    def _token_expired(self, raw_value: Any) -> bool:
        normalized = str(raw_value or "").strip()
        if not normalized:
            return True
        try:
            token_expires_at = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        except ValueError:
            return True
        if token_expires_at.tzinfo is None:
            token_expires_at = token_expires_at.replace(tzinfo=timezone.utc)
        return token_expires_at <= datetime.now(timezone.utc)

    def _extract_raw_message(self, fetch_data: Any) -> bytes:
        if isinstance(fetch_data, (bytes, bytearray)):
            return bytes(fetch_data)

        if not isinstance(fetch_data, (list, tuple)):
            return b""

        for item in fetch_data:
            if isinstance(item, tuple) and len(item) >= 2 and isinstance(item[1], (bytes, bytearray)):
                return bytes(item[1])
        return b""

    def _document_matches_organization(self, document: dict[str, Any], organization: dict[str, Any]) -> bool:
        inbox_address = str(organization.get("email_inbox_address") or "").strip().lower()
        if not inbox_address:
            return False

        recipients = {str(address).strip().lower() for address in document.get("recipients") or [] if str(address).strip()}
        if inbox_address not in recipients:
            return False

        allowed_sender = str(organization.get("email_allowed_sender") or "").strip().lower()
        sender_email = str(document.get("sender_email") or "").strip().lower()
        if allowed_sender and allowed_sender != sender_email:
            return False

        subject_keyword = str(organization.get("email_subject_keyword") or "").strip().lower()
        subject = str(document.get("subject") or "").strip().lower()
        if subject_keyword and subject_keyword not in subject:
            return False

        return True

    def _build_documents_from_message(
        self,
        *,
        message_uid: str,
        message: Any,
    ) -> list[dict[str, Any]]:
        sender_name, sender_email = self._extract_sender(message)
        subject = self._message_subject(message)
        recipients = sorted(self._extract_recipient_addresses(message))
        message_id = str(message.get("Message-ID") or "").strip()
        message_date = self._message_date_iso(message)
        incoming_date = message_date[:10] if message_date else ""

        candidates: list[dict[str, Any]] = []
        for attachment_index, attachment in enumerate(message.iter_attachments(), start=1):
            attachment_info = self._extract_attachment_info(attachment, attachment_index)
            if not attachment_info:
                continue

            ocr_result = self.ocr_engine.extract_data(
                attachment_info["file_name"],
                attachment_info["content"],
            )

            candidates.append(
                {
                    "incoming_date": incoming_date,
                    "file_name": attachment_info["file_name"],
                    "document_type": self._document_type_from_attachment(attachment_info["file_name"], attachment_info["content_type"]),
                    "attachment_type": attachment_info["content_type"],
                    "attachment_index": attachment_index,
                    "message_id": message_id,
                    "imap_uid": message_uid,
                    "sender_name": sender_name,
                    "sender_email": sender_email,
                    "subject": subject,
                    "recipients": recipients,
                    "message_date": message_date,
                    "source_external_id": self._build_source_external_id(
                        message_id=message_id,
                        message_uid=message_uid,
                        attachment_index=attachment_index,
                        file_name=attachment_info["file_name"],
                    ),
                    "document_bytes": attachment_info["content"],
                    **ocr_result,
                }
            )

        return candidates

    def _build_organization_candidate(
        self,
        document: dict[str, Any],
        organization: dict[str, Any],
        *,
        trigger_mode: str = "manual",
    ) -> dict[str, Any]:
        matched_recipient = self._resolve_matched_recipient(document, organization)
        mode_label = "automatic-check-imap" if str(trigger_mode or "").strip().lower() == "automatic" else "manual-check-imap"
        candidate = dict(document)
        candidate.update(
            {
                "source": "EMAIL",
                "source_sender_name": document.get("sender_email") or document.get("sender_name"),
                "source_metadata": {
                    "temat": document.get("subject"),
                    "skrzynka": organization.get("email_inbox_address"),
                    "tryb": mode_label,
                    "routing_mode": "central_mailbox",
                    "message_id": document.get("message_id"),
                    "imap_uid": document.get("imap_uid"),
                    "nadawca_email": document.get("sender_email"),
                    "nadawca_nazwa": document.get("sender_name"),
                    "data_wiadomosci": document.get("message_date"),
                    "odbiorcy": document.get("recipients") or [],
                    "dopasowany_odbiorca": matched_recipient,
                    "zalacznik_nazwa": document.get("file_name"),
                    "zalacznik_typ": document.get("attachment_type"),
                    "zalacznik_index": document.get("attachment_index"),
                },
                "notes": "Import z recznego sprawdzenia e-maila.",
            }
        )
        return candidate

    def _extract_attachment_info(self, attachment: Any, attachment_index: int) -> dict[str, Any] | None:
        content = attachment.get_payload(decode=True)
        if not content:
            return None

        content_type = str(attachment.get_content_type() or "application/octet-stream").lower()
        file_name = attachment.get_filename() or self._fallback_file_name(attachment_index, content_type)
        extension = Path(str(file_name)).suffix.lower()

        if extension not in self.SUPPORTED_EXTENSIONS and content_type not in self.SUPPORTED_CONTENT_TYPES:
            return None

        return {
            "file_name": str(file_name),
            "content_type": content_type,
            "content": bytes(content),
        }

    def _fallback_file_name(self, attachment_index: int, content_type: str) -> str:
        fallback_extensions = {
            "application/pdf": ".pdf",
            "application/xml": ".xml",
            "text/xml": ".xml",
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/bmp": ".bmp",
            "image/tiff": ".tif",
            "image/webp": ".webp",
        }
        return f"email_zalacznik_{attachment_index}{fallback_extensions.get(content_type, '.bin')}"

    def _extract_recipient_addresses(self, message: Any) -> set[str]:
        recipient_headers = []
        for header_name in ("To", "Cc", "Delivered-To", "X-Original-To", "Resent-To"):
            recipient_headers.extend(message.get_all(header_name, []))
        return {
            address.strip().lower()
            for _, address in getaddresses(recipient_headers)
            if address and address.strip()
        }

    def _extract_sender(self, message: Any) -> tuple[str, str]:
        senders = getaddresses(message.get_all("From", []))
        if not senders:
            return "", ""
        display_name, email_address = senders[0]
        return str(display_name or "").strip(), str(email_address or "").strip().lower()

    def _extract_sender_email(self, message: Any) -> str:
        _, sender_email = self._extract_sender(message)
        return sender_email

    def _resolve_matched_recipient(self, document: dict[str, Any], organization: dict[str, Any]) -> str:
        inbox_address = str(organization.get("email_inbox_address") or "").strip().lower()
        if not inbox_address:
            return ""
        for recipient in document.get("recipients") or []:
            normalized = str(recipient).strip().lower()
            if normalized == inbox_address:
                return normalized
        return inbox_address

    def _mask_login(self, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            return ""
        if "@" not in normalized:
            if len(normalized) <= 2:
                return "*" * len(normalized)
            return normalized[:2] + "***"
        local_part, domain = normalized.split("@", 1)
        if len(local_part) <= 2:
            masked_local = "*" * len(local_part)
        else:
            masked_local = local_part[:2] + "***"
        return f"{masked_local}@{domain}"

    def _message_subject(self, message: Any) -> str:
        return str(message.get("Subject") or "").strip()

    def _message_date_iso(self, message: Any) -> str:
        raw_date = str(message.get("Date") or "").strip()
        if not raw_date:
            return ""

        try:
            parsed = parsedate_to_datetime(raw_date)
        except (TypeError, ValueError, IndexError, OverflowError):
            return ""

        return parsed.isoformat()

    def _document_type_from_attachment(self, file_name: str, content_type: str) -> str:
        extension = Path(file_name).suffix.lower()
        if extension == ".pdf" or content_type == "application/pdf":
            return "pdf"
        if extension in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
            return "zdjecie"
        if extension in {".tif", ".tiff"}:
            return "skan"
        if extension == ".xml" or content_type in {"application/xml", "text/xml"}:
            return "xml"
        return "plik"

    def _build_source_external_id(
        self,
        *,
        message_id: str,
        message_uid: str,
        attachment_index: int,
        file_name: str,
    ) -> str:
        raw_value = "|".join(
            [
                message_id.strip() or f"uid:{message_uid}",
                str(attachment_index),
                file_name.strip().lower(),
            ]
        )
        digest = hashlib.sha256(raw_value.encode("utf-8")).hexdigest()[:24]
        return f"email-{digest}"
