from __future__ import annotations

from urllib.parse import urljoin

from harvester.discovery.link_filter import extract_document_links, is_document_candidate
from harvester.models import DiscoveredDocument, Source
from harvester.resilience import with_retries
from harvester.utils import file_type_from_path_or_url, new_id, normalize_url


class BrowserDiscovery:
    def __init__(self, *, timeout_seconds: int, retry_count: int, retry_initial_delay_seconds: float):
        self.timeout_seconds = timeout_seconds
        self.retry_count = retry_count
        self.retry_initial_delay_seconds = retry_initial_delay_seconds

    def discover(self, source: Source, run_id: str) -> list[DiscoveredDocument]:
        documents: list[DiscoveredDocument] = []
        for page_url in source.urls:
            page_documents = with_retries(
                lambda: self._discover_page(source, run_id, page_url),
                attempts=self.retry_count,
                initial_delay_seconds=self.retry_initial_delay_seconds,
            )
            documents.extend(page_documents)
        return dedupe_documents(documents)

    def _discover_page(self, source: Source, run_id: str, page_url: str) -> list[DiscoveredDocument]:
        try:
            from playwright.sync_api import sync_playwright  # type: ignore
        except ModuleNotFoundError as exc:
            raise RuntimeError("Playwright is not installed. Run: pip install -r requirements.txt") from exc

        captured_urls: set[str] = set()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.on("response", lambda response: capture_response_url(captured_urls, response.url, source.document_keywords))
                page.goto(page_url, wait_until="networkidle", timeout=self.timeout_seconds * 1000)
                html = page.content()
            finally:
                browser.close()

        documents = [
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
            for link in extract_document_links(html, page_url, source.document_keywords)
        ]
        for captured_url in captured_urls:
            absolute = urljoin(page_url, captured_url)
            documents.append(
                DiscoveredDocument(
                    document_id=new_id("doc"),
                    run_id=run_id,
                    source_id=source.source_id,
                    amc_name=source.amc_name,
                    page_url=page_url,
                    document_url=absolute,
                    normalized_url=normalize_url(absolute),
                    link_text="network-captured document",
                    surrounding_text="network response",
                    file_type=file_type_from_path_or_url(absolute),
                )
            )
        return documents


def capture_response_url(captured_urls: set[str], url: str, keywords: list[str]) -> None:
    if is_document_candidate(url, "", "", keywords):
        captured_urls.add(url)


def dedupe_documents(documents: list[DiscoveredDocument]) -> list[DiscoveredDocument]:
    seen: set[str] = set()
    result: list[DiscoveredDocument] = []
    for document in documents:
        if document.normalized_url in seen:
            continue
        seen.add(document.normalized_url)
        result.append(document)
    return result
