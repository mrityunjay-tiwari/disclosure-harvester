import unittest
from pathlib import Path

from harvester.download.downloader import DownloadError, Downloader
from harvester.models import DiscoveredDocument


class DownloaderTests(unittest.TestCase):
    def test_missing_file_url_raises_download_error(self):
        missing_path = (Path(__file__).resolve().parent / "fixtures" / "documents" / "missing.pdf").resolve()
        doc = DiscoveredDocument(
            document_id="doc_1",
            run_id="run_1",
            source_id="source_1",
            amc_name="AMC",
            page_url="fixture://source_1",
            document_url=missing_path.as_uri(),
            normalized_url=missing_path.as_uri(),
            link_text="Missing PDF",
            surrounding_text="Missing PDF",
            file_type="pdf",
        )
        with self.assertRaises(DownloadError):
            Downloader(Path("data/raw"), timeout_seconds=1).download(doc, "run_1", already_seen=False)


if __name__ == "__main__":
    unittest.main()
