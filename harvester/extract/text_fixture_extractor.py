from __future__ import annotations

import csv
from pathlib import Path

from harvester.extract.base import Extractor
from harvester.models import StagingRow


class TextFixtureExtractor(Extractor):
    parser_name = "text_fixture"

    def can_extract(self, path: Path) -> bool:
        return path.suffix.lower() in {".txt", ".csv"}

    def extract(self, file_id: str, path: Path) -> list[StagingRow]:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        table_start = None
        for index, line in enumerate(lines):
            if line.strip().lower().startswith("scheme_name,"):
                table_start = index
                break
        if table_start is None:
            return []

        rows: list[StagingRow] = []
        reader = csv.DictReader(lines[table_start:])
        for row_number, row in enumerate(reader, start=1):
            rows.append(
                StagingRow(
                    file_id=file_id,
                    sheet_or_page="fixture",
                    section_name=row.get("scheme_name") or None,
                    scheme_name_raw=row.get("scheme_name") or None,
                    row_number=row_number,
                    raw_data=dict(row),
                    parser_used=self.parser_name,
                )
            )
        return rows
