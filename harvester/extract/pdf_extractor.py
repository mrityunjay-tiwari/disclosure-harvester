from __future__ import annotations

from pathlib import Path

from harvester.extract.base import ExtractionError, Extractor
from harvester.models import StagingRow


class PdfPlumberExtractor(Extractor):
    parser_name = "pdfplumber"

    def can_extract(self, path: Path) -> bool:
        return path.suffix.lower() == ".pdf"

    def extract(self, file_id: str, path: Path) -> list[StagingRow]:
        try:
            import pdfplumber  # type: ignore
        except ModuleNotFoundError as exc:
            raise ExtractionError("pdfplumber is not installed") from exc

        rows: list[StagingRow] = []
        try:
            with pdfplumber.open(path) as pdf:
                for page_index, page in enumerate(pdf.pages, start=1):
                    for table_index, table in enumerate(page.extract_tables() or [], start=1):
                        if not table or len(table) < 2:
                            continue
                        headers = [str(cell or "").strip() for cell in table[0]]
                        for row_number, values in enumerate(table[1:], start=1):
                            raw = {headers[i] or f"column_{i + 1}": values[i] if i < len(values) else None for i in range(len(headers))}
                            rows.append(
                                StagingRow(
                                    file_id=file_id,
                                    sheet_or_page=f"page_{page_index}",
                                    section_name=f"table_{table_index}",
                                    scheme_name_raw=raw.get("scheme_name") or raw.get("Scheme Name"),
                                    row_number=row_number,
                                    raw_data=raw,
                                    parser_used=self.parser_name,
                                )
                            )
        except Exception as exc:
            raise ExtractionError(f"failed to extract PDF tables: {exc}") from exc
        if not rows:
            raise ExtractionError("no extractable tables found")
        return rows
