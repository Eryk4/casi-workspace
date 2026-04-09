from __future__ import annotations

class OCREngine:
    def extract_data(self, file_name: str, file_bytes: bytes | None = None) -> dict:
        # TODO: tutaj podłącz prawdziwy silnik OCR dla PDF, zdjęć i skanów.
        # Na tym etapie używamy jeszcze OCR testowego, ale już z interfejsem
        # gotowym na przekazanie prawdziwej zawartości pliku.
        return self.extract_mock_data(file_name)

    def extract_mock_data(self, file_name: str) -> dict:
        # TODO: tutaj podłącz prawdziwy silnik OCR dla PDF, zdjęć i skanów.
        # OCR zwraca surowy tekst i confidence. Zapis pliku OCR odbywa się później
        # w serwisie aplikacyjnym, żeby cały magazyn plików był organizowany jednolicie.
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
        }
