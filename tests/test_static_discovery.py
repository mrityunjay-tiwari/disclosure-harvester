import unittest
from pathlib import Path

from harvester.discovery.static_discovery import StaticDiscovery
from harvester.models import Source


class StaticDiscoveryTests(unittest.TestCase):
    def test_extracts_document_links_from_html_page(self):
        page = (Path(__file__).resolve().parent / "fixtures" / "pages" / "static_disclosure.html").resolve()
        source = Source(
            source_id="sbi_portfolio",
            amc_name="SBI Mutual Fund",
            urls=[page.as_uri()],
            source_type="static",
            active=True,
            validated_end_to_end=True,
            document_keywords=["monthly portfolio"],
        )
        discovery = StaticDiscovery(timeout_seconds=5, retry_count=1, retry_initial_delay_seconds=0)
        docs = discovery.discover(source, "run_test")
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].file_type, "txt")
        self.assertIn("sbi_monthly_portfolio_june_2026", docs[0].document_url)


if __name__ == "__main__":
    unittest.main()
