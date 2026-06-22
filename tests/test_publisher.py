import unittest
import uuid
from pathlib import Path

from harvester.load.database import Database
from harvester.models import ValidatedHolding
from harvester.publish.publisher import Publisher


class PublisherTests(unittest.TestCase):
    def test_revised_file_supersedes_current_holding(self):
        tmp_root = Path(__file__).resolve().parents[1] / ".tmp_tests"
        tmp_root.mkdir(exist_ok=True)
        db = Database(tmp_root / f"publisher_{uuid.uuid4().hex}.duckdb")
        db.initialize(Path(__file__).resolve().parents[1] / "sql" / "001_create_tables.sql")
        publisher = Publisher(db)
        first = ValidatedHolding(
            amc_name="SBI Mutual Fund",
            scheme_name="SBI Equity Fund",
            period="2026-06",
            document_type="monthly_portfolio",
            holding_business_key="isin:INE040A01034",
            isin="INE040A01034",
            security_name="HDFC Bank Ltd",
            asset_type="equity",
            quantity=1000,
            market_value=1500000,
            percentage_to_nav=5.2,
            source_file_id="file_old",
            source_sha256="old",
        )
        revised = ValidatedHolding(
            **{**first.__dict__, "market_value": 1600000, "source_file_id": "file_new", "source_sha256": "new"}
        )
        self.assertEqual(publisher.publish([first]), 1)
        self.assertEqual(publisher.publish([revised]), 1)
        current = db.fetchall("select source_file_id from published_holdings where is_current = true")
        old = db.fetchall("select source_file_id from published_holdings where is_current = false")
        self.assertEqual(len(current), 1)
        self.assertEqual(current[0][0], "file_new")
        self.assertEqual(len(old), 1)
        db.close()


if __name__ == "__main__":
    unittest.main()
