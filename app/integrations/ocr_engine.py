from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.config import OCR_LANGUAGE, OCR_TESSERACT_CMD


class OCREngine:
    def __init__(self, tesseract_cmd: str = "", language: str = "") -> None:
        self.language = (language or OCR_LANGUAGE or "pol+eng").strip() or "pol+eng"
        self.tesseract_cmd = self._resolve_tesseract_cmd(tesseract_cmd or OCR_TESSERACT_CMD)

    def integration_status(self) -> dict:
        return {
            "enabled": bool(self.tesseract_cmd),
            "mode": "tesseract" if self.tesseract_cmd else "fallback",
            "language": self.language,
        }

    def extract_data(self, file_name: str, file_bytes: bytes | None = None) -> dict:
        if file_bytes in (None, b""):
            return self.extract_mock_data(file_name)

        suffix = Path(file_name).suffix.lower()
        raw_text, confidence = self._extract_raw_text(file_name, file_bytes, suffix)
        parsed_fields = self._parse_invoice_fields(raw_text)

        return {
            "ocr_raw_text": raw_text,
            "ocr_confidence": confidence,
            **parsed_fields,
        }

    def extract_text(self, file_name: str, file_bytes: bytes | None = None) -> str:
        if file_bytes in (None, b""):
            return ""
        suffix = Path(file_name).suffix.lower()
        raw_text, confidence = self._extract_raw_text(file_name, file_bytes, suffix)
        if confidence == 0.0 and raw_text.startswith("Nie uda"):
            return ""
        return raw_text

    def extract_mock_data(self, file_name: str) -> dict:
        raw_text = (
            f"MOCK OCR\n"
            f"Plik: {file_name}\n"
            "Numer faktury: TG/2026/04/07\n"
            "NIP wystawcy: 9988877766\n"
            "Kwota brutto: 442.80 PLN\n"
        )
        return {
            "ocr_raw_text": raw_text,
            "ocr_confidence": 0.84,
            "invoice_number": "TG/2026/04/07",
            "ksef_number": "",
            "issuer_nip": "9988877766",
            "issuer_name": "",
            "issue_date": "",
            "sale_date": "",
            "gross_amount": 442.80,
            "currency": "PLN",
        }

    def _extract_raw_text(self, file_name: str, file_bytes: bytes, suffix: str) -> tuple[str, float | None]:
        if suffix in {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}:
            text = self._extract_image_text(file_bytes, suffix)
            if text:
                return text, None

        if suffix == ".pdf":
            pdf_text = self._extract_pdf_text(file_bytes)
            if pdf_text:
                return pdf_text, 0.99

        decoded_text = self._extract_decodable_text(file_bytes)
        if decoded_text:
            return decoded_text, 0.99

        fallback = (
            "Nie udało się odczytać treści dokumentu lokalnym OCR.\n"
            f"Plik: {file_name}\n"
            "Sprawdź, czy na serwerze jest zainstalowany Tesseract albo czy dokument zawiera warstwę tekstową."
        )
        return fallback, 0.0

    def _extract_image_text(self, file_bytes: bytes, suffix: str) -> str:
        if not self.tesseract_cmd:
            return ""

        with tempfile.TemporaryDirectory(prefix="ocr_telegram_") as temp_dir:
            input_path = Path(temp_dir) / f"telegram_ocr{suffix or '.bin'}"
            input_path.write_bytes(file_bytes)
            candidates: list[str] = []
            for psm in ("6", "11", "4"):
                result = subprocess.run(
                    [
                        self.tesseract_cmd,
                        str(input_path),
                        "stdout",
                        "-l",
                        self.language,
                        "--oem",
                        "1",
                        "--psm",
                        psm,
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    check=False,
                )
                if result.returncode != 0:
                    continue
                cleaned = self._cleanup_text(result.stdout)
                if cleaned:
                    candidates.append(cleaned)

        if not candidates:
            return ""

        ranked = sorted(
            candidates,
            key=lambda item: (
                self._looks_like_document_text(item),
                len(re.findall(r"[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9]", item)),
                len(item),
            ),
            reverse=True,
        )
        return ranked[0]

    def _extract_pdf_text(self, file_bytes: bytes) -> str:
        decoded = file_bytes.decode("latin-1", errors="ignore")
        literal_strings = re.findall(r"\(([^()]{3,})\)", decoded)
        cleaned_strings = [self._cleanup_text(item) for item in literal_strings]
        useful_strings = [item for item in cleaned_strings if self._looks_like_document_text(item)]
        if useful_strings:
            return "\n".join(useful_strings)

        return self._extract_decodable_text(file_bytes)

    def _extract_decodable_text(self, file_bytes: bytes) -> str:
        for encoding in ("utf-8", "cp1250", "latin-1"):
            try:
                decoded = file_bytes.decode(encoding)
            except UnicodeDecodeError:
                continue

            cleaned = self._cleanup_text(decoded)
            if self._looks_like_document_text(cleaned):
                return cleaned
        return ""

    def _parse_invoice_fields(self, text: str) -> dict:
        normalized = self._normalize_for_search(text)
        amount, amount_currency = self._extract_gross_amount_and_currency(normalized)
        return {
            "invoice_number": self._extract_invoice_number(normalized) or "",
            "ksef_number": self._extract_ksef_number(normalized) or "",
            "issuer_nip": self._extract_issuer_nip(normalized) or "",
            "issuer_name": self._extract_issuer_name(normalized) or "",
            "issue_date": self._extract_issue_date(normalized) or "",
            "sale_date": self._extract_sale_date(normalized) or "",
            "gross_amount": amount,
            "currency": amount_currency or self._extract_currency(normalized) or "",
        }

    def _extract_invoice_number(self, text: str) -> str:
        patterns = (
            r"(?:numer|nr)\s+faktury[:\s]+([A-Z0-9][A-Z0-9\/\-.]{2,})",
            r"faktura(?:\s+vat)?\s+(?:nr|numer)?[:\s]+([A-Z0-9][A-Z0-9\/\-.]{2,})",
        )
        return self._extract_first_group(patterns, text)

    def _extract_ksef_number(self, text: str) -> str:
        return self._extract_first_group(
            (
                r"(?:numer\s+)?ksef[:\s]+([A-Z0-9\/\-.]{6,})",
                r"ksef\s+nr[:\s]+([A-Z0-9\/\-.]{6,})",
            ),
            text,
        )

    def _extract_issuer_nip(self, text: str) -> str:
        candidate = self._extract_first_group(
            (
                r"nip(?:\s+wystawcy|\s+sprzedawcy|\s+dostawcy)?[:\s]+([0-9 \-]{10,})",
                r"sprzedawca.*?nip[:\s]+([0-9 \-]{10,})",
            ),
            text,
        )
        digits = re.sub(r"\D", "", candidate)
        if len(digits) == 10:
            return digits

        fallback = re.search(r"\b(\d{10})\b", text)
        return fallback.group(1) if fallback else ""

    def _extract_issuer_name(self, text: str) -> str:
        candidate = self._extract_first_group(
            (
                r"(?:nazwa\s+wystawcy|wystawca|sprzedawca)[:\s]+([A-ZĄĆĘŁŃÓŚŹŻ0-9][A-ZĄĆĘŁŃÓŚŹŻ0-9 .,&()\-]{3,})",
            ),
            text,
        )
        return candidate[:180].strip()

    def _extract_issue_date(self, text: str) -> str:
        return self._extract_date_by_labels(
            text,
            ("data wystawienia", "wystawiono", "data dokumentu"),
        )

    def _extract_sale_date(self, text: str) -> str:
        return self._extract_date_by_labels(
            text,
            ("data sprzedaży", "data sprzedazy", "data wykonania", "sprzedaz"),
        )

    def _extract_gross_amount_and_currency(self, text: str) -> tuple[float | None, str]:
        label_patterns = (
            r"(?:kwota|wartość|wartosc)\s+brutto[:\s]+([0-9 .,\u00a0]{3,})\s*(PLN|EUR|USD|GBP)?",
            r"(?:razem|suma)\s+brutto[:\s]+([0-9 .,\u00a0]{3,})\s*(PLN|EUR|USD|GBP)?",
            r"do\s+zap[łl]aty[:\s]+([0-9 .,\u00a0]{3,})\s*(PLN|EUR|USD|GBP)?",
        )

        for pattern in label_patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if not match:
                continue
            amount = self._parse_decimal(match.group(1))
            if amount is not None:
                return amount, (match.group(2) or "").strip().upper()
        return None, ""

    def _extract_currency(self, text: str) -> str:
        match = re.search(r"\b(PLN|EUR|USD|GBP)\b", text, flags=re.IGNORECASE)
        return (match.group(1) or "").upper() if match else ""

    def _extract_date_by_labels(self, text: str, labels: tuple[str, ...]) -> str:
        for label in labels:
            pattern = rf"{re.escape(label)}[:\s]+([0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}|[0-9]{{2}}[.\-/][0-9]{{2}}[.\-/][0-9]{{4}})"
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                normalized = self._normalize_date(match.group(1))
                if normalized:
                    return normalized
        return ""

    def _extract_first_group(self, patterns: tuple[str, ...], text: str) -> str:
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return self._cleanup_candidate(match.group(1))
        return ""

    def _normalize_date(self, raw_value: str) -> str:
        value = raw_value.strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return value

        match = re.fullmatch(r"(\d{2})[.\-/](\d{2})[.\-/](\d{4})", value)
        if match:
            day, month, year = match.groups()
            return f"{year}-{month}-{day}"
        return ""

    def _parse_decimal(self, raw_value: str) -> float | None:
        cleaned = raw_value.replace("\u00a0", " ").strip()
        cleaned = cleaned.replace(" ", "").replace(".", "").replace(",", ".")
        match = re.search(r"\d+(?:\.\d{1,2})?", cleaned)
        if not match:
            return None
        try:
            return float(match.group(0))
        except ValueError:
            return None

    def _normalize_for_search(self, text: str) -> str:
        return self._cleanup_text(text).replace("ł", "l").replace("Ł", "L")

    def _cleanup_text(self, text: str) -> str:
        lines = []
        for line in text.splitlines():
            compact = re.sub(r"[ \t]+", " ", line).strip()
            if compact:
                lines.append(compact)
        return "\n".join(lines).strip()

    def _cleanup_candidate(self, value: str) -> str:
        return value.strip().rstrip(".,;:")

    def _looks_like_document_text(self, text: str) -> bool:
        if not text:
            return False
        if len(text) < 12:
            return False
        if re.search(r"(faktur|nip|kwota|brutto|sprzeda|wystaw)", text, flags=re.IGNORECASE):
            return True
        printable = sum(1 for char in text if char.isprintable() and char not in "\x00\x01\x02\x03\x04\x05")
        return printable / max(len(text), 1) > 0.85 and len(re.findall(r"[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż]", text)) > 20

    def _resolve_tesseract_cmd(self, configured: str) -> str:
        candidate = configured.strip()
        if candidate:
            return candidate

        for path_candidate in (
            shutil.which("tesseract"),
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ):
            if path_candidate and Path(path_candidate).exists():
                return str(path_candidate)
        return ""
