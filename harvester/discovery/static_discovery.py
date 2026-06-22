from __future__ import annotations

from urllib.request import Request, urlopen

from harvester.discovery.link_filter import extract_document_links
from harvester.models import DiscoveredDocument, Source
from harvester.resilience import with_retries
from harvester.utils import new_id


class StaticDiscovery:
    def __init__(self, *, timeout_seconds: int, retry_count: int, retry_initial_delay_seconds: float):
        self.timeout_seconds = timeout_seconds
        self.retry_count = retry_count
        self.retry_initial_delay_seconds = retry_initial_delay_seconds

    def discover(self, source: Source, run_id: str) -> list[DiscoveredDocument]:
        documents: list[DiscoveredDocument] = []
        for page_url in source.urls:
            html = with_retries(
                lambda: self._fetch_html(page_url),
                attempts=self.retry_count,
                initial_delay_seconds=self.retry_initial_delay_seconds,
            )
            for link in extract_document_links(html, page_url, source.document_keywords):
                documents.append(
                    DiscoveredDocument(
                        document_id=new_id("doc"),
                        run_id=run_id,
                        source_id=source.source_id,
                        amc_name=source.amc_name,
                        page_url=page_url,
                        document_url=link["document_url"],
                        normalized_url=link["normalized_url"],
                        link_text=link["link_text"],
                        surrounding_text=link["surrounding_text"],
                        file_type=link["file_type"],
                    )
                )
        return documents

    def _fetch_html(self, url: str) -> str:
        request = Request(url, headers={"User-Agent": "DisclosureHarvester/1.0"})
        with urlopen(request, timeout=self.timeout_seconds) as response:
            return response.read().decode("utf-8", errors="ignore")
