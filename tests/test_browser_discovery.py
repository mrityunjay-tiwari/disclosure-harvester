import unittest

from harvester.discovery.browser_discovery import capture_response_url, dedupe_documents
from harvester.models import DiscoveredDocument


class BrowserDiscoveryTests(unittest.TestCase):
    def test_capture_response_url_keeps_document_candidates(self):
        captured: set[str] = set()
        capture_response_url(captured, "https://example.com/monthly-portfolio-june-2026.pdf", ["monthly portfolio"])
        capture_response_url(captured, "https://example.com/app.js", ["monthly portfolio"])
        self.assertEqual(captured, {"https://example.com/monthly-portfolio-june-2026.pdf"})

    def test_dedupe_documents_by_normalized_url(self):
        first = DiscoveredDocument(
            document_id="doc_1",
            run_id="run_1",
            source_id="source",
            amc_name="AMC",
            page_url="https://example.com",
            document_url="https://example.com/a.pdf",
            normalized_url="https://example.com/a.pdf",
            link_text="A",
            surrounding_text="A",
            file_type="pdf",
        )
        second = DiscoveredDocument(
            **{**first.__dict__, "document_id": "doc_2", "link_text": "Duplicate"}
        )
        self.assertEqual(dedupe_documents([first, second]), [first])


if __name__ == "__main__":
    unittest.main()
