import unittest
from pathlib import Path

from harvester.extract.base import ExtractionError
from harvester.extract.excel_extractor import CsvExtractor, detect_header_row
from harvester.extract.pdf_extractor import PdfPlumberExtractor
from harvester.extract.registry import ExtractorRegistry


class ExtractorTests(unittest.TestCase):
    def test_csv_header_detection_skips_preamble(self):
        lines = [
            "SBI Mutual Fund",
            "For June 2026",
            "",
            "scheme_name,security_name,market_value",
        ]
        self.assertEqual(detect_header_row(lines), 3)

    def test_csv_extractor_reads_rows_after_detected_header(self):
        path = Path(__file__).resolve().parent / "fixtures" / "documents" / "holdings_with_preamble.csv"
        rows = CsvExtractor().extract("file_1", path)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].raw_data["scheme_name"], "SBI Equity Fund")

    def test_pdf_extractor_reports_missing_dependency_or_empty_pdf_cleanly(self):
        extractor = PdfPlumberExtractor()
        try:
            extractor.extract("file_1", Path("missing.pdf"))
        except ExtractionError as exc:
            self.assertTrue(str(exc))
        else:
            self.fail("expected PDF extraction to fail for a missing file")

    def test_registry_raises_clear_error_for_unknown_type(self):
        registry = ExtractorRegistry(extractors=[])
        with self.assertRaises(ExtractionError):
            registry.extract("file_1", Path("holdings.unknown"))


if __name__ == "__main__":
    unittest.main()
