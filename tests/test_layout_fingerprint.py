import unittest
import uuid
from pathlib import Path

from harvester.classify.classifier import Classification
from harvester.load.database import Database
from harvester.models import RawFile, StagingRow
from harvester.validate.layout_fingerprint import LayoutFingerprintStore


class LayoutFingerprintTests(unittest.TestCase):
    def test_successful_rows_update_baseline_and_missing_header_drifts(self):
        tmp_root = Path(__file__).resolve().parents[1] / ".tmp_tests"
        tmp_root.mkdir(exist_ok=True)
        db = Database(tmp_root / f"fingerprint_{uuid.uuid4().hex}.duckdb")
        db.initialize(Path(__file__).resolve().parents[1] / "sql" / "001_create_tables.sql")
        store = LayoutFingerprintStore(db)
        classification = Classification(
            file_id="file_1",
            amc_name="SBI Mutual Fund",
            period="2026-06",
            document_type="monthly_portfolio",
            confidence_score=90,
            status="classified",
            hard_conflict=False,
            evidence={},
        )
        raw = RawFile(
            file_id="file_1",
            document_id="doc_1",
            source_id="sbi_portfolio",
            storage_path=Path("sample.txt"),
            sha256="abc",
            file_size=10,
            mime_type="text/plain",
            is_duplicate=False,
        )
        rows = [
            StagingRow(
                file_id="file_1",
                sheet_or_page="fixture",
                section_name=None,
                scheme_name_raw="SBI Equity Fund",
                row_number=1,
                raw_data={"scheme_name": "SBI Equity Fund", "security_name": "HDFC Bank", "market_value": "10"},
                parser_used="text_fixture",
            )
        ]
        store.update("sbi_portfolio", classification, raw, rows)
        drift = store.check(
            "sbi_portfolio",
            Classification(**{**classification.__dict__, "file_id": "file_2"}),
            [
                StagingRow(
                    file_id="file_2",
                    sheet_or_page="fixture",
                    section_name=None,
                    scheme_name_raw="SBI Equity Fund",
                    row_number=1,
                    raw_data={"scheme_name": "SBI Equity Fund", "security_name": "HDFC Bank"},
                    parser_used="text_fixture",
                )
            ],
        )
        self.assertTrue(drift.drifted)
        self.assertIn("missing_headers:market_value", drift.reasons)
        db.close()


if __name__ == "__main__":
    unittest.main()
