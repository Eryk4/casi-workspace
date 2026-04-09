from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from app.config import (
    SECURE_COOKIES,
    SESSION_COOKIE_NAME,
    SESSION_DURATION_HOURS,
    STATIC_DIR,
    database_label,
    default_login_hint_enabled,
    test_imports_enabled,
)
from app.domain.constants import (
    DUPLICATE_TYPES,
    INVOICE_STATUSES,
    SOURCES,
    TASK_PRIORITIES,
    TASK_STATUSES,
    TASK_TYPES,
    USER_ROLES,
)
from app.services.auth_service import AuthError, PermissionError
from app.services.organization_service import OrganizationError, OrganizationPermissionError
from app.services.storage_service import StorageError


READ_ROLES = ("administrator", "operator", "podglad")
WRITE_ROLES = ("administrator", "operator")
ADMIN_ROLES = ("administrator",)


def create_server(host: str, port: int, services: dict[str, object]) -> ThreadingHTTPServer:
    class InvoiceOpsHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            return

        @property
        def invoice_service(self):
            return services["invoice_service"]

        @property
        def dashboard_service(self):
            return services["dashboard_service"]

        @property
        def task_service(self):
            return services["task_service"]

        @property
        def auth_service(self):
            return services["auth_service"]

        @property
        def organization_service(self):
            return services["organization_service"]

        @property
        def storage_service(self):
            return services["storage_service"]

        @property
        def telegram_adapter(self):
            return self.invoice_service.telegram_adapter

        @property
        def current_user(self) -> dict[str, Any] | None:
            if not hasattr(self, "_cached_user"):
                self._cached_user = self.auth_service.get_current_user(self._session_token())
            return self._cached_user

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)

            if self._is_public_static_path(path):
                return self._serve_static(path)

            if path == "/health":
                return self._send_json({"ok": True})

            if path == "/api/meta":
                return self._send_json(
                    {
                        "sources": list(SOURCES),
                        "statuses": list(INVOICE_STATUSES),
                        "duplicate_types": list(DUPLICATE_TYPES),
                        "task_types": list(TASK_TYPES),
                        "task_statuses": list(TASK_STATUSES),
                        "task_priorities": list(TASK_PRIORITIES),
                        "roles": list(USER_ROLES),
                        "database_label": database_label(),
                        "telegram_enabled": self.invoice_service.telegram_integration_info()["enabled"],
                        "storage_backend": self.invoice_service.storage_integration_info()["backend"],
                        "test_imports_enabled": test_imports_enabled(),
                        "default_login_hint_enabled": default_login_hint_enabled(),
                    }
                )

            if path == "/api/session/current":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                return self._send_json(user)

            if path == "/api/organizations":
                user = self._require_user(ADMIN_ROLES)
                if not user:
                    return
                try:
                    organizations = self.organization_service.list_organizations(user)
                except (OrganizationError, OrganizationPermissionError) as error:
                    return self._handle_scope_error(error)
                return self._send_json(organizations)

            if path == "/api/users":
                user = self._require_user(ADMIN_ROLES)
                if not user:
                    return
                try:
                    requested_organization_id = self._requested_organization_id(query)
                    users = self.auth_service.list_users(user, requested_organization_id=requested_organization_id)
                except PermissionError as error:
                    return self._send_json({"error": str(error)}, status=403)
                except AuthError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(users)
            if path == "/api/tasks/users":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                return self._send_json(self.task_service.list_assignable_users(organization_id=organization_id))

            user = self._require_user(READ_ROLES)
            if not user:
                return

            if path == "/api/dashboard":
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                return self._send_json(self.dashboard_service.get_snapshot(organization_id=organization_id))
            if path == "/api/invoices":
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                filters = {
                    "search": self._query_one(query, "search"),
                    "source": self._query_one(query, "source"),
                    "status": self._query_one(query, "status"),
                    "duplicate_type": self._query_one(query, "duplicate_type"),
                    "date_from": self._query_one(query, "date_from"),
                    "date_to": self._query_one(query, "date_to"),
                    "contractor_id": self._query_one(query, "contractor_id"),
                    "nip": self._query_one(query, "nip"),
                    "invoice_number": self._query_one(query, "invoice_number"),
                    "ksef_number": self._query_one(query, "ksef_number"),
                    "sort_by": self._query_one(query, "sort_by"),
                    "sort_order": self._query_one(query, "sort_order"),
                }
                return self._send_json(self.invoice_service.list_invoices(filters, organization_id=organization_id))
            if path.startswith("/api/invoices/"):
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                invoice_id = self._extract_id(path, "/api/invoices/")
                if invoice_id is None:
                    return self._not_found()
                detail = self.invoice_service.get_invoice_detail(invoice_id, organization_id=organization_id)
                if not detail:
                    return self._send_json({"error": "Nie znaleziono faktury."}, status=404)
                return self._send_json(detail)
            if path == "/api/contractors":
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                search = self._query_one(query, "search")
                only_new = self._query_one(query, "only_new") in {"1", "true", "tak"}
                return self._send_json(
                    self.invoice_service.list_contractors(
                        search,
                        only_new=only_new,
                        organization_id=organization_id,
                    )
                )
            if path.startswith("/api/contractors/"):
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                contractor_id = self._extract_id(path, "/api/contractors/")
                if contractor_id is None:
                    return self._not_found()
                detail = self.invoice_service.get_contractor_detail(contractor_id, organization_id=organization_id)
                if not detail:
                    return self._send_json({"error": "Nie znaleziono kontrahenta."}, status=404)
                return self._send_json(detail)
            if path == "/api/logs":
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                return self._send_json(self.invoice_service.list_logs(organization_id=organization_id))
            if path == "/api/tasks":
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                filters = {
                    "search": self._query_one(query, "search"),
                    "task_type": self._query_one(query, "task_type"),
                    "status": self._query_one(query, "status"),
                    "priority": self._query_one(query, "priority"),
                    "assigned_user_id": self._query_one(query, "assigned_user_id"),
                    "due_from": self._query_one(query, "due_from"),
                    "due_to": self._query_one(query, "due_to"),
                    "remind_from": self._query_one(query, "remind_from"),
                    "remind_to": self._query_one(query, "remind_to"),
                    "due_reminders_only": self._query_one(query, "due_reminders_only"),
                }
                return self._send_json(self.task_service.list_tasks(filters, organization_id=organization_id))
            if path.startswith("/api/tasks/"):
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                task_id = self._extract_id(path, "/api/tasks/")
                if task_id is None:
                    return self._not_found()
                detail = self.task_service.get_task_detail(task_id, organization_id=organization_id)
                if not detail:
                    return self._send_json({"error": "Nie znaleziono zadania."}, status=404)
                return self._send_json(detail)
            if path == "/api/search":
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                return self._send_json(
                    self.invoice_service.global_search(self._query_one(query, "q"), organization_id=organization_id)
                )
            matched_storage = self._match_storage_path(path)
            if matched_storage:
                artifact_type, storage_key = matched_storage
                return self._send_storage_file(artifact_type, storage_key, user)
            return self._serve_static(path)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)

            if self.telegram_adapter.webhook_path and path == self.telegram_adapter.webhook_path:
                payload = self._read_json()
                try:
                    invoice = self.invoice_service.import_telegram_update(payload)
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json({"ok": True, "invoice_id": invoice["id"]})

            if path == "/api/session/login":
                payload = self._read_json()
                try:
                    user, session_token = self.auth_service.login(
                        payload.get("login", ""),
                        payload.get("password", ""),
                        self._client_ip(),
                        self.headers.get("User-Agent"),
                    )
                except AuthError as error:
                    return self._send_json({"error": str(error)}, status=401)
                self._cached_user = user
                return self._send_json(
                    user,
                    extra_headers=[("Set-Cookie", self._build_session_cookie(session_token))],
                )

            if path == "/api/session/logout":
                user = self._require_user(READ_ROLES)
                if not user:
                    return
                token = self._session_token()
                if token:
                    self.auth_service.logout(token, actor_login=self._actor_label(user))
                self._cached_user = None
                return self._send_json(
                    {"ok": True},
                    extra_headers=[("Set-Cookie", self._build_clear_cookie())],
                )

            if path == "/api/organizations":
                user = self._require_user(ADMIN_ROLES)
                if not user:
                    return
                payload = self._read_json()
                if not user.get("is_global_admin"):
                    return self._send_json({"error": "Tylko administrator globalny może zarządzać organizacjami."}, status=403)
                try:
                    created = self.organization_service.create_organization(
                        payload,
                        actor_user=user,
                        actor_login=self._actor_label(user),
                    )
                except (OrganizationError, OrganizationPermissionError) as error:
                    return self._handle_scope_error(error)
                return self._send_json(created, status=201)

            if path == "/api/users":
                user = self._require_user(ADMIN_ROLES)
                if not user:
                    return
                payload = self._read_json()
                try:
                    created = self.auth_service.create_user(
                        payload,
                        actor_login=self._actor_label(user),
                        actor_user_id=int(user["user_id"]),
                        actor_user=user,
                    )
                except PermissionError as error:
                    return self._send_json({"error": str(error)}, status=403)
                except AuthError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(created, status=201)

            user = self._require_user(WRITE_ROLES)
            if not user:
                return

            if path == "/api/tasks":
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                payload = self._read_json()
                try:
                    created = self.task_service.create_task(
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(created, status=201)

            if path.startswith("/api/tasks/") and path.endswith("/notes"):
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                task_id = self._extract_id(path, "/api/tasks/", suffix="/notes")
                if task_id is None:
                    return self._not_found()
                payload = self._read_json()
                try:
                    detail = self.task_service.add_task_note(
                        task_id,
                        payload.get("note_text", ""),
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not detail:
                    return self._send_json({"error": "Nie znaleziono zadania."}, status=404)
                return self._send_json(detail, status=201)

            if path.startswith("/api/invoices/") and path.endswith("/actions/confirm-duplicate"):
                invoice_id = self._extract_id(path, "/api/invoices/", suffix="/actions/confirm-duplicate")
                if invoice_id is None:
                    return self._not_found()
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                invoice = self.invoice_service.confirm_duplicate(
                    invoice_id,
                    actor=self._actor_label(user),
                    organization_id=organization_id,
                )
                if not invoice:
                    return self._send_json({"error": "Nie znaleziono faktury."}, status=404)
                return self._send_json(invoice)

            if path.startswith("/api/invoices/") and path.endswith("/actions/reject-duplicate"):
                invoice_id = self._extract_id(path, "/api/invoices/", suffix="/actions/reject-duplicate")
                if invoice_id is None:
                    return self._not_found()
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                invoice = self.invoice_service.reject_duplicate(
                    invoice_id,
                    actor=self._actor_label(user),
                    organization_id=organization_id,
                )
                if not invoice:
                    return self._send_json({"error": "Nie znaleziono faktury."}, status=404)
                return self._send_json(invoice)

            if path.startswith("/api/import/"):
                if not test_imports_enabled():
                    return self._send_json({"error": "Import testowy jest wyłączony w tym środowisku."}, status=403)
                source = path.removeprefix("/api/import/")
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                try:
                    invoice = self.invoice_service.import_mock(
                        source,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                except Exception as error:  # pragma: no cover
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(invoice, status=201)

            return self._not_found()

        def do_PATCH(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)

            if path.startswith("/api/organizations/"):
                user = self._require_user(ADMIN_ROLES)
                if not user:
                    return
                if not user.get("is_global_admin"):
                    return self._send_json({"error": "Tylko administrator globalny może zarządzać organizacjami."}, status=403)
                organization_id = self._extract_id(path, "/api/organizations/")
                if organization_id is None:
                    return self._not_found()
                payload = self._read_json()
                try:
                    updated = self.organization_service.update_organization(
                        organization_id,
                        payload,
                        actor_user=user,
                        actor_login=self._actor_label(user),
                    )
                except (OrganizationError, OrganizationPermissionError) as error:
                    return self._handle_scope_error(error)
                return self._send_json(updated)

            if path.startswith("/api/users/"):
                user = self._require_user(ADMIN_ROLES)
                if not user:
                    return
                user_id = self._extract_id(path, "/api/users/")
                if user_id is None:
                    return self._not_found()
                payload = self._read_json()
                try:
                    updated = self.auth_service.update_user(
                        user_id,
                        payload,
                        actor_login=self._actor_label(user),
                        actor_user=user,
                    )
                except PermissionError as error:
                    return self._send_json({"error": str(error)}, status=403)
                except AuthError as error:
                    return self._send_json({"error": str(error)}, status=400)
                return self._send_json(updated)

            if path.startswith("/api/invoices/"):
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_data_scope(user, query)
                if organization_id is ...:
                    return
                invoice_id = self._extract_id(path, "/api/invoices/")
                if invoice_id is None:
                    return self._not_found()
                payload = self._read_json()
                try:
                    invoice = self.invoice_service.update_invoice(
                        invoice_id,
                        payload,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not invoice:
                    return self._send_json({"error": "Nie znaleziono faktury."}, status=404)
                return self._send_json(invoice)

            if path.startswith("/api/tasks/"):
                user = self._require_user(WRITE_ROLES)
                if not user:
                    return
                organization_id = self._resolve_write_scope(user, query)
                if organization_id is ...:
                    return
                task_id = self._extract_id(path, "/api/tasks/")
                if task_id is None:
                    return self._not_found()
                payload = self._read_json()
                try:
                    task = self.task_service.update_task(
                        task_id,
                        payload,
                        actor_user=user,
                        actor=self._actor_label(user),
                        organization_id=organization_id,
                    )
                except ValueError as error:
                    return self._send_json({"error": str(error)}, status=400)
                if not task:
                    return self._send_json({"error": "Nie znaleziono zadania."}, status=404)
                return self._send_json(task)

            return self._not_found()

        def _serve_static(self, path: str) -> None:
            if path in {"/", ""}:
                target = STATIC_DIR / "index.html"
            else:
                target = STATIC_DIR / path.lstrip("/")
            if not target.exists() or not target.is_file():
                return self._not_found()

            content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
            data = target.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _is_public_static_path(self, path: str) -> bool:
            if path.startswith("/api/"):
                return False
            if self._match_storage_path(path):
                return False
            if path in {"/", ""}:
                return True
            target = STATIC_DIR / path.lstrip("/")
            return target.exists() and target.is_file()

        def _match_storage_path(self, path: str) -> tuple[str, str] | None:
            for artifact_type in ("document", "ocr"):
                route_prefix = self.storage_service.route_prefix(artifact_type)
                if path.startswith(route_prefix):
                    return artifact_type, path.removeprefix(route_prefix)
            return None

        def _send_storage_file(self, artifact_type: str, storage_key: str, user: dict[str, Any]) -> None:
            normalized_key = storage_key.lstrip("/")
            if not self._can_access_storage_path(normalized_key, user):
                return self._send_json({"error": "Brak dostępu do plików innej organizacji."}, status=403)

            try:
                safe_path = self.storage_service.resolve_local_path(artifact_type, normalized_key)
            except StorageError:
                return self._send_json({"error": "Nieprawidłowa ścieżka pliku."}, status=400)

            if not safe_path.exists() or not safe_path.is_file():
                return self._not_found()
            data = safe_path.read_bytes()
            content_type = mimetypes.guess_type(str(safe_path))[0] or "text/plain; charset=utf-8"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _can_access_storage_path(self, relative_path: str, user: dict[str, Any]) -> bool:
            if user.get("is_global_admin"):
                return True
            organization_slug = str(user.get("organization_slug") or "").strip()
            if not organization_slug:
                return False
            normalized_parts = Path(relative_path).parts
            return len(normalized_parts) >= 2 and normalized_parts[0] == "organizacje" and normalized_parts[1] == organization_slug

        def _send_json(self, payload: Any, status: int = 200, extra_headers: list[tuple[str, str]] | None = None) -> None:
            data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            if extra_headers:
                for key, value in extra_headers:
                    self.send_header(key, value)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            if length == 0:
                return {}
            raw = self.rfile.read(length).decode("utf-8")
            return json.loads(raw)

        def _query_one(self, query: dict[str, list[str]], key: str) -> str:
            values = query.get(key)
            return values[0] if values else ""

        def _requested_organization_id(self, query: dict[str, list[str]]) -> int | None:
            raw = self._query_one(query, "organization_id").strip()
            if not raw:
                return None
            return int(raw) if raw.isdigit() else None

        def _resolve_data_scope(self, user: dict[str, Any], query: dict[str, list[str]]) -> int | None | Ellipsis:
            try:
                return self.organization_service.resolve_data_scope(user, self._requested_organization_id(query))
            except (OrganizationError, OrganizationPermissionError) as error:
                self._handle_scope_error(error)
                return ...

        def _resolve_write_scope(self, user: dict[str, Any], query: dict[str, list[str]]) -> int | None | Ellipsis:
            try:
                return self.organization_service.resolve_write_scope(user, self._requested_organization_id(query))
            except (OrganizationError, OrganizationPermissionError) as error:
                self._handle_scope_error(error)
                return ...

        def _handle_scope_error(self, error: Exception) -> None:
            status = 403 if isinstance(error, OrganizationPermissionError) else 400
            self._send_json({"error": str(error)}, status=status)

        def _extract_id(self, path: str, prefix: str, suffix: str = "") -> int | None:
            value = path.removeprefix(prefix)
            if suffix and value.endswith(suffix):
                value = value[: -len(suffix)]
            value = value.strip("/")
            return int(value) if value.isdigit() else None

        def _require_user(self, allowed_roles: tuple[str, ...]) -> dict[str, Any] | None:
            try:
                self.auth_service.require_role(self.current_user, allowed_roles)
            except PermissionError as error:
                status = 401 if not self.current_user else 403
                self._send_json({"error": str(error)}, status=status)
                return None
            return self.current_user

        def _session_token(self) -> str | None:
            raw_cookie = self.headers.get("Cookie")
            if not raw_cookie:
                return None
            cookie = SimpleCookie()
            cookie.load(raw_cookie)
            morsel = cookie.get(SESSION_COOKIE_NAME)
            return morsel.value if morsel else None

        def _build_session_cookie(self, session_token: str) -> str:
            cookie = SimpleCookie()
            cookie[SESSION_COOKIE_NAME] = session_token
            cookie[SESSION_COOKIE_NAME]["path"] = "/"
            cookie[SESSION_COOKIE_NAME]["httponly"] = True
            cookie[SESSION_COOKIE_NAME]["samesite"] = "Lax"
            if SECURE_COOKIES:
                cookie[SESSION_COOKIE_NAME]["secure"] = True
            cookie[SESSION_COOKIE_NAME]["max-age"] = str(SESSION_DURATION_HOURS * 3600)
            return cookie.output(header="").strip()

        def _build_clear_cookie(self) -> str:
            cookie = SimpleCookie()
            cookie[SESSION_COOKIE_NAME] = ""
            cookie[SESSION_COOKIE_NAME]["path"] = "/"
            cookie[SESSION_COOKIE_NAME]["httponly"] = True
            cookie[SESSION_COOKIE_NAME]["samesite"] = "Lax"
            if SECURE_COOKIES:
                cookie[SESSION_COOKIE_NAME]["secure"] = True
            cookie[SESSION_COOKIE_NAME]["expires"] = "Thu, 01 Jan 1970 00:00:00 GMT"
            cookie[SESSION_COOKIE_NAME]["max-age"] = "0"
            return cookie.output(header="").strip()

        def _client_ip(self) -> str | None:
            return self.client_address[0] if self.client_address else None

        def _actor_label(self, user: dict[str, Any]) -> str:
            return user.get("display_name") or user["login"]

        def _not_found(self) -> None:
            self._send_json({"error": "Nie znaleziono zasobu."}, status=404)

    return ThreadingHTTPServer((host, port), InvoiceOpsHandler)
