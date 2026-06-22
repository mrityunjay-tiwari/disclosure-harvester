from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from harvester.extract.base import ExtractionError, Extractor
from harvester.models import StagingRow
from harvester.utils import normalize_text


HEADER_KEYWORDS = {"scheme", "scheme name", "isin", "security", "quantity", "market value", "nav", "asset type"}


class CsvExtractor(Extractor):
    parser_name = "csv"

    def can_extract(self, path: Path) -> bool:
        return path.suffix.lower() == ".csv"

    def extract(self, file_id: str, path: Path) -> list[StagingRow]:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        header_index = detect_header_row(lines)
        if header_index is None:
            raise ExtractionError("could not detect CSV header row")
        reader = csv.DictReader(lines[header_index:])
        rows: list[StagingRow] = []
        for row_number, row in enumerate(reader, start=1):
            rows.append(
                StagingRow(
                    file_id=file_id,
                    sheet_or_page="csv",
                    section_name=row.get("scheme_name") or row.get("Scheme Name"),
                    scheme_name_raw=row.get("scheme_name") or row.get("Scheme Name"),
                    row_number=row_number,
                    raw_data=dict(row),
                    parser_used=self.parser_name,
                )
            )
        return rows


class PandasExcelExtractor(Extractor):
    parser_name = "pandas_excel"

    def can_extract(self, path: Path) -> bool:
        return path.suffix.lower() in {".xlsx", ".xls"}

    def extract(self, file_id: str, path: Path) -> list[StagingRow]:
        try:
            import pandas as pd  # type: ignore
        except ModuleNotFoundError as exc:
            raise ExtractionError("pandas is not installed") from exc

        rows: list[StagingRow] = []
        try:
            workbook = pd.read_excel(path, sheet_name=None, header=None, nrows=40)
        except Exception as exc:
            raise ExtractionError(f"failed to read workbook preview: {exc}") from exc

        for sheet_name, preview in workbook.items():
            header_index = detect_header_row_from_values(preview.fillna("").values.tolist())
            if header_index is None:
                continue
            frame = pd.read_excel(path, sheet_name=sheet_name, header=header_index)
            for row_number, item in enumerate(frame.fillna("").to_dict(orient="records"), start=1):
                raw = {str(key).strip(): value for key, value in item.items()}
                rows.append(
                    StagingRow(
                        file_id=file_id,
                        sheet_or_page=str(sheet_name),
                        section_name=str(raw.get("scheme_name") or raw.get("Scheme Name") or "") or None,
                        scheme_name_raw=str(raw.get("scheme_name") or raw.get("Scheme Name") or "") or None,
                        row_number=row_number,
                        raw_data=raw,
                        parser_used=self.parser_name,
                    )
                )
        if not rows:
            raise ExtractionError("no sheet with recognizable holdings headers")
        return rows


def detect_header_row(lines: list[str]) -> int | None:
    values = [line.split(",") for line in lines[:40]]
    return detect_header_row_from_values(values)


def detect_header_row_from_values(values: list[list[Any]]) -> int | None:
    best_index: int | None = None
    best_score = 0
    for index, row in enumerate(values):
        normalized_cells = [normalize_text(str(cell)) for cell in row]
        row_text = " ".join(normalized_cells)
        score = 0
        for keyword in HEADER_KEYWORDS:
            normalized_keyword = normalize_text(keyword)
            if normalized_keyword in normalized_cells or normalized_keyword in row_text:
                score += 1
        if score > best_score:
            best_index = index
            best_score = score
    return best_index if best_score >= 2 else None
