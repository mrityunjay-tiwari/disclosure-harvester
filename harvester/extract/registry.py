from __future__ import annotations

from pathlib import Path

from harvester.extract.base import ExtractionError, Extractor
from harvester.extract.excel_extractor import CsvExtractor, PandasExcelExtractor
from harvester.extract.pdf_extractor import PdfPlumberExtractor
from harvester.extract.text_fixture_extractor import TextFixtureExtractor
from harvester.models import StagingRow


class ExtractorRegistry:
    def __init__(self, extractors: list[Extractor] | None = None):
        self.extractors = extractors or [
            TextFixtureExtractor(),
            CsvExtractor(),
            PandasExcelExtractor(),
            PdfPlumberExtractor(),
        ]

    def extract(self, file_id: str, path: Path) -> list[StagingRow]:
        failures: list[str] = []
        for extractor in self.extractors:
            if not extractor.can_extract(path):
                continue
            try:
                rows = extractor.extract(file_id, path)
            except ExtractionError as exc:
                failures.append(f"{extractor.parser_name}: {exc}")
                continue
            if rows:
                return rows
            failures.append(f"{extractor.parser_name}: no rows")
        if failures:
            raise ExtractionError("; ".join(failures))
        raise ExtractionError(f"no extractor available for {path.suffix.lower() or 'unknown file type'}")
