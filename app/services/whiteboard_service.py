from __future__ import annotations

import hashlib
import json
import mimetypes
from pathlib import Path
import re
from typing import Any

from app.repositories.event_repository import EventRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.whiteboard_repository import WhiteboardRepository
from app.services.storage_service import StorageService
from app.utils import json_dumps, now_iso


class WhiteboardService:
    MAX_STROKES_PER_REQUEST = 24
    MAX_POINTS_PER_STROKE = 600
    MAX_IMAGE_UPLOAD_BYTES = 8 * 1024 * 1024
    MIN_STROKE_WIDTH = 1
    MAX_STROKE_WIDTH = 32
    MIN_IMAGE_RATIO = 0.03
    MAX_IMAGE_RATIO = 1.0
    MAX_IMAGE_ROTATION_DEGREES = 360.0
    _HEX_COLOR_RE = re.compile(r"#[0-9a-fA-F]{6}")
    _NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
    _ALLOWED_IMAGE_MIME_TYPES = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }
    _ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

    def __init__(
        self,
        whiteboard_repository: WhiteboardRepository,
        organization_repository: OrganizationRepository,
        event_repository: EventRepository,
        storage_service: StorageService,
    ) -> None:
        self.whiteboard_repository = whiteboard_repository
        self.organization_repository = organization_repository
        self.event_repository = event_repository
        self.storage_service = storage_service

    def get_board_state(
        self,
        organization_id: int,
        *,
        after_event_id: int | None = None,
    ) -> dict[str, Any]:
        self._ensure_active_organization(organization_id)
        latest_event = self.whiteboard_repository.get_latest_event(organization_id)
        latest_event_id = int(latest_event["whiteboard_event_id"]) if latest_event else 0
        latest_clear_event = self.whiteboard_repository.get_latest_clear_event(organization_id)
        last_cleared_event_id = int(latest_clear_event["whiteboard_event_id"]) if latest_clear_event else 0

        if latest_event_id == 0:
            return {
                "organization_id": organization_id,
                "mode": "full",
                "latest_event_id": 0,
                "last_cleared_event_id": 0,
                "updated_at": None,
                "updated_by": None,
                "events": [],
            }

        if after_event_id is not None and int(after_event_id) >= last_cleared_event_id:
            rows = self.whiteboard_repository.list_events(
                organization_id,
                after_event_id=int(after_event_id),
            )
            return {
                "organization_id": organization_id,
                "mode": "patch",
                "latest_event_id": latest_event_id,
                "last_cleared_event_id": last_cleared_event_id,
                "updated_at": latest_event["created_at"],
                "updated_by": latest_event["actor_label"],
                "events": [self._serialize_event(row) for row in rows],
            }

        full_after_event_id = last_cleared_event_id - 1 if last_cleared_event_id > 0 else None
        rows = self.whiteboard_repository.list_events(
            organization_id,
            after_event_id=full_after_event_id,
        )
        return {
            "organization_id": organization_id,
            "mode": "full",
            "latest_event_id": latest_event_id,
            "last_cleared_event_id": last_cleared_event_id,
            "updated_at": latest_event["created_at"],
            "updated_by": latest_event["actor_label"],
            "events": [self._serialize_event(row) for row in rows],
        }

    def add_strokes(
        self,
        organization_id: int,
        *,
        strokes: list[dict[str, Any]] | Any,
        actor_user: dict[str, Any],
        actor: str,
    ) -> dict[str, Any]:
        self._ensure_active_organization(organization_id)
        normalized_strokes = self._normalize_strokes(strokes)
        if not normalized_strokes:
            raise ValueError("Brak poprawnych ruchow do zapisania na tablicy.")

        created_events: list[dict[str, Any]] = []
        for stroke in normalized_strokes:
            created_events.append(
                self._create_event(
                    organization_id=organization_id,
                    event_type="stroke",
                    payload=stroke,
                    actor_user=actor_user,
                    actor=actor,
                )
            )

        self.event_repository.log(
            event_type="whiteboard_updated",
            invoice_id=None,
            organization_id=organization_id,
            source="WHITEBOARD",
            status_before=None,
            status_after=f"{len(normalized_strokes)} ruchow",
            decision_reason=f"Dodano {len(normalized_strokes)} ruchow na wspolnej tablicy organizacji.",
            actor=actor,
            details={
                "stroke_count": len(normalized_strokes),
                "whiteboard_event_ids": [item["whiteboard_event_id"] for item in created_events],
                "created_by_user_id": actor_user.get("user_id"),
            },
        )
        return self._build_patch_response(organization_id, created_events)

    def add_image(
        self,
        organization_id: int,
        *,
        file_name: str,
        file_bytes: bytes | bytearray | Any,
        mime_type: str | None,
        placement: dict[str, Any] | Any,
        actor_user: dict[str, Any],
        actor: str,
    ) -> dict[str, Any]:
        organization = self._resolve_organization(organization_id)
        normalized_file_name = str(file_name or "").strip()
        normalized_file_bytes = self._normalize_image_bytes(file_bytes)
        normalized_mime_type = self._normalize_image_mime_type(normalized_file_name, mime_type)
        normalized_placement = self._normalize_image_placement(placement)

        stored_name = self._build_stored_image_name(
            normalized_file_name,
            normalized_file_bytes,
            normalized_mime_type,
        )
        relative_path = self._build_image_relative_path(str(organization.get("slug") or ""), stored_name)
        artifact = self.storage_service.save_binary("whiteboard", relative_path, normalized_file_bytes)

        created_event = self._create_event(
            organization_id=organization_id,
            event_type="image",
            payload={
                "file_name": normalized_file_name,
                "mime_type": normalized_mime_type,
                "image_link": artifact.public_link,
                "image_storage_key": artifact.storage_key,
                **normalized_placement,
            },
            actor_user=actor_user,
            actor=actor,
        )

        self.event_repository.log(
            event_type="whiteboard_image_added",
            invoice_id=None,
            organization_id=organization_id,
            source="WHITEBOARD",
            status_before=None,
            status_after="obrazek dodany",
            decision_reason=f"Dodano obrazek {normalized_file_name} na wspolna tablice organizacji.",
            actor=actor,
            details={
                "whiteboard_event_id": created_event["whiteboard_event_id"],
                "file_name": normalized_file_name,
                "mime_type": normalized_mime_type,
                "image_storage_key": artifact.storage_key,
                "created_by_user_id": actor_user.get("user_id"),
            },
        )
        return self._build_patch_response(organization_id, [created_event])

    def clear_board(
        self,
        organization_id: int,
        *,
        actor_user: dict[str, Any],
        actor: str,
    ) -> dict[str, Any]:
        self._ensure_active_organization(organization_id)
        clear_event = self._create_event(
            organization_id=organization_id,
            event_type="clear",
            payload={"reason": "manual_clear"},
            actor_user=actor_user,
            actor=actor,
        )
        self.event_repository.log(
            event_type="whiteboard_cleared",
            invoice_id=None,
            organization_id=organization_id,
            source="WHITEBOARD",
            status_before="aktywny",
            status_after="wyczyszczony",
            decision_reason="Wyczyszczono wspolna tablice organizacji.",
            actor=actor,
            details={
                "whiteboard_event_id": clear_event["whiteboard_event_id"],
                "created_by_user_id": actor_user.get("user_id"),
            },
        )
        return self._build_patch_response(organization_id, [clear_event])

    def update_image_transform(
        self,
        organization_id: int,
        *,
        image_event_id: int,
        placement: dict[str, Any] | Any,
        actor_user: dict[str, Any],
        actor: str,
    ) -> dict[str, Any]:
        self._ensure_active_organization(organization_id)
        image_event = self.whiteboard_repository.get_event_by_id(organization_id, int(image_event_id))
        if not image_event or str(image_event.get("event_type") or "") != "image":
            raise ValueError("Nie znaleziono obrazka na tablicy.")

        latest_clear_event = self.whiteboard_repository.get_latest_clear_event(organization_id)
        if latest_clear_event and int(latest_clear_event["whiteboard_event_id"]) >= int(image_event_id):
            raise ValueError("Nie mozna edytowac obrazka, ktory zostal juz wyczyszczony z tablicy.")

        normalized_placement = self._normalize_image_placement(placement)
        created_event = self._create_event(
            organization_id=organization_id,
            event_type="image_transform",
            payload={
                "image_event_id": int(image_event_id),
                **normalized_placement,
            },
            actor_user=actor_user,
            actor=actor,
        )

        self.event_repository.log(
            event_type="whiteboard_image_transformed",
            invoice_id=None,
            organization_id=organization_id,
            source="WHITEBOARD",
            status_before="obrazek aktywny",
            status_after="obrazek przeksztalcony",
            decision_reason="Zmieniono polozenie, rozmiar albo obrot obrazka na wspolnej tablicy organizacji.",
            actor=actor,
            details={
                "whiteboard_event_id": created_event["whiteboard_event_id"],
                "image_event_id": int(image_event_id),
                "created_by_user_id": actor_user.get("user_id"),
                **normalized_placement,
            },
        )
        return self._build_patch_response(organization_id, [created_event])

    def _build_patch_response(
        self,
        organization_id: int,
        events: list[dict[str, Any]],
    ) -> dict[str, Any]:
        latest_event = events[-1] if events else None
        last_cleared_event_id = 0
        for event in reversed(events):
            if event["event_type"] == "clear":
                last_cleared_event_id = int(event["whiteboard_event_id"])
                break
        if last_cleared_event_id == 0:
            latest_clear = self.whiteboard_repository.get_latest_clear_event(organization_id)
            last_cleared_event_id = int(latest_clear["whiteboard_event_id"]) if latest_clear else 0

        return {
            "organization_id": organization_id,
            "mode": "patch",
            "latest_event_id": int(latest_event["whiteboard_event_id"]) if latest_event else 0,
            "last_cleared_event_id": last_cleared_event_id,
            "updated_at": latest_event["created_at"] if latest_event else None,
            "updated_by": latest_event["actor_label"] if latest_event else None,
            "events": events,
        }

    def _create_event(
        self,
        *,
        organization_id: int,
        event_type: str,
        payload: dict[str, Any],
        actor_user: dict[str, Any],
        actor: str,
    ) -> dict[str, Any]:
        created_at = now_iso()
        created_by_user_id = self._extract_actor_user_id(actor_user)
        whiteboard_event_id = self.whiteboard_repository.create_event(
            organization_id=organization_id,
            event_type=event_type,
            payload_json=json_dumps(payload),
            actor_label=actor,
            created_at=created_at,
            created_by_user_id=created_by_user_id,
        )
        return {
            "whiteboard_event_id": whiteboard_event_id,
            "organization_id": organization_id,
            "event_type": event_type,
            "payload": payload,
            "created_by_user_id": created_by_user_id,
            "actor_label": actor,
            "created_at": created_at,
        }

    def _serialize_event(self, row: dict[str, Any]) -> dict[str, Any]:
        payload: dict[str, Any]
        try:
            payload = json.loads(str(row.get("payload_json") or "{}"))
        except json.JSONDecodeError:
            payload = {}
        return {
            "whiteboard_event_id": int(row["whiteboard_event_id"]),
            "organization_id": int(row["organization_id"]),
            "event_type": str(row["event_type"]),
            "payload": payload,
            "created_by_user_id": (
                int(row["created_by_user_id"]) if row.get("created_by_user_id") is not None else None
            ),
            "actor_label": str(row.get("actor_label") or ""),
            "created_at": row.get("created_at"),
        }

    def _ensure_active_organization(self, organization_id: int) -> None:
        self._resolve_organization(organization_id)

    def _resolve_organization(self, organization_id: int) -> dict[str, Any]:
        organization = self.organization_repository.get_by_id(organization_id)
        if not organization:
            raise ValueError("Wybrana organizacja nie istnieje.")
        if not organization.get("is_active"):
            raise ValueError("Nie mozna pracowac na tablicy organizacji oznaczonej jako nieaktywna.")
        return organization

    def _normalize_strokes(self, value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            raise ValueError("Lista ruchow tablicy ma nieprawidlowy format.")
        if not value:
            return []
        if len(value) > self.MAX_STROKES_PER_REQUEST:
            raise ValueError("Jednorazowo mozna zapisac ograniczona liczbe ruchow tablicy.")
        return [self._normalize_stroke(item) for item in value]

    def _normalize_stroke(self, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("Ruch tablicy ma nieprawidlowy format.")

        tool = str(value.get("tool") or "pen").strip().lower()
        if tool not in {"pen", "eraser"}:
            raise ValueError("Obslugiwane narzedzia tablicy to pen albo eraser.")

        raw_width = value.get("width", 4)
        try:
            width = float(raw_width)
        except (TypeError, ValueError) as error:
            raise ValueError("Szerokosc ruchu tablicy musi byc liczba.") from error
        width = max(self.MIN_STROKE_WIDTH, min(self.MAX_STROKE_WIDTH, round(width, 2)))

        color = str(value.get("color") or "#0f5c90").strip()
        if tool == "pen" and not self._HEX_COLOR_RE.fullmatch(color):
            raise ValueError("Kolor ruchu tablicy musi miec format #RRGGBB.")
        if tool == "eraser":
            color = "#ffffff"

        points = value.get("points")
        if not isinstance(points, list) or not points:
            raise ValueError("Ruch tablicy musi zawierac co najmniej jeden punkt.")
        if len(points) > self.MAX_POINTS_PER_STROKE:
            raise ValueError("Ruch tablicy ma zbyt duzo punktow.")

        normalized_points = [self._normalize_point(point) for point in points]
        return {
            "tool": tool,
            "color": color.lower(),
            "width": width,
            "points": normalized_points,
        }

    def _normalize_point(self, value: Any) -> dict[str, float]:
        if not isinstance(value, dict):
            raise ValueError("Punkt ruchu tablicy ma nieprawidlowy format.")
        try:
            x = float(value.get("x"))
            y = float(value.get("y"))
        except (TypeError, ValueError) as error:
            raise ValueError("Wspolrzedne ruchu tablicy musza byc liczbami.") from error

        x = round(max(0.0, min(1.0, x)), 6)
        y = round(max(0.0, min(1.0, y)), 6)
        return {"x": x, "y": y}

    def _normalize_image_bytes(self, value: bytes | bytearray | Any) -> bytes:
        if not isinstance(value, (bytes, bytearray)) or not value:
            raise ValueError("Wybierz obrazek do dodania na tablice.")
        normalized = bytes(value)
        if len(normalized) > self.MAX_IMAGE_UPLOAD_BYTES:
            raise ValueError("Obrazek na tablice jest za duzy.")
        return normalized

    def _normalize_image_mime_type(self, file_name: str, mime_type: str | None) -> str:
        normalized_file_name = str(file_name or "").strip()
        if not normalized_file_name:
            raise ValueError("Brakuje nazwy obrazka.")

        extension = Path(normalized_file_name).suffix.lower()
        if extension and extension not in self._ALLOWED_IMAGE_EXTENSIONS:
            raise ValueError("Tablica obsluguje obrazki PNG, JPG, WEBP albo GIF.")

        resolved_mime_type = str(
            mime_type
            or mimetypes.guess_type(normalized_file_name)[0]
            or ""
        ).strip().lower()
        if resolved_mime_type not in self._ALLOWED_IMAGE_MIME_TYPES:
            raise ValueError("Tablica obsluguje obrazki PNG, JPG, WEBP albo GIF.")
        return resolved_mime_type

    def _normalize_image_placement(self, value: dict[str, Any] | Any) -> dict[str, float]:
        if not isinstance(value, dict):
            raise ValueError("Pozycja obrazka na tablicy ma nieprawidlowy format.")

        x = self._parse_ratio(value.get("x"), allow_zero=True)
        y = self._parse_ratio(value.get("y"), allow_zero=True)
        width = self._parse_ratio(value.get("width"), minimum=self.MIN_IMAGE_RATIO)
        height = self._parse_ratio(value.get("height"), minimum=self.MIN_IMAGE_RATIO)
        rotation_deg = self._parse_rotation_degrees(value.get("rotation_deg", 0))

        width = min(self.MAX_IMAGE_RATIO, width)
        height = min(self.MAX_IMAGE_RATIO, height)
        x = max(0.0, min(1.0 - width, x))
        y = max(0.0, min(1.0 - height, y))

        return {
            "x": round(x, 6),
            "y": round(y, 6),
            "width": round(width, 6),
            "height": round(height, 6),
            "rotation_deg": round(rotation_deg, 3),
        }

    def _parse_ratio(
        self,
        value: Any,
        *,
        minimum: float = 0.0,
        allow_zero: bool = False,
    ) -> float:
        try:
            parsed = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError("Pozycja albo rozmiar obrazka musi byc liczba.") from error

        effective_minimum = 0.0 if allow_zero else minimum
        return max(effective_minimum, min(self.MAX_IMAGE_RATIO, parsed))

    def _parse_rotation_degrees(self, value: Any) -> float:
        try:
            parsed = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError("Obrot obrazka musi byc liczba.") from error
        normalized = parsed % self.MAX_IMAGE_ROTATION_DEGREES
        if normalized > 180:
            normalized -= 360
        return normalized

    def _build_stored_image_name(self, file_name: str, file_bytes: bytes, mime_type: str) -> str:
        stem = self._slug(Path(file_name).stem) or "tablica"
        digest = hashlib.sha256(file_bytes).hexdigest()[:12]
        extension = Path(file_name).suffix.lower()
        if extension not in self._ALLOWED_IMAGE_EXTENSIONS:
            extension = self._ALLOWED_IMAGE_MIME_TYPES[mime_type]
        return f"{stem}_{digest}{extension}"

    def _build_image_relative_path(self, organization_slug: str, stored_name: str) -> Path:
        month_stamp = now_iso()[:7].split("-")
        return Path("organizacje") / self._slug(organization_slug or "organizacja") / "tablica" / Path(*month_stamp) / stored_name

    def _slug(self, value: str) -> str:
        normalized = self._NON_ALNUM_RE.sub("-", str(value or "").strip().lower()).strip("-")
        return normalized or "organizacja"

    def _extract_actor_user_id(self, actor_user: dict[str, Any] | None) -> int | None:
        raw_user_id = actor_user.get("user_id") if actor_user else None
        try:
            return int(raw_user_id) if raw_user_id is not None else None
        except (TypeError, ValueError):
            return None
