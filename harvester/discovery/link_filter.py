from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from harvester.utils import file_type_from_path_or_url, normalize_text, normalize_url


DOCUMENT_EXTENSIONS = {"pdf", "xls", "xlsx", "xlsb", "csv"}


def extract_document_links(html: str, page_url: str, keywords: list[str]) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    keyword_text = [normalize_text(keyword) for keyword in keywords]
    results: list[dict[str, str]] = []
    for anchor in soup.find_all("a"):
        href = anchor.get("href")
        if not href:
            continue
        absolute = urljoin(page_url, href)
        file_type = file_type_from_path_or_url(absolute)
        text = anchor.get_text(" ", strip=True)
        surrounding = anchor.parent.get_text(" ", strip=True) if anchor.parent else text
        if is_document_candidate(absolute, text, surrounding, keywords):
            results.append(
                {
                    "document_url": absolute,
                    "normalized_url": normalize_url(absolute),
                    "link_text": text,
                    "surrounding_text": surrounding,
                    "file_type": file_type,
                }
            )
    return results


def is_document_candidate(url: str, link_text: str, surrounding_text: str, keywords: list[str]) -> bool:
    file_type = file_type_from_path_or_url(url)
    if file_type in DOCUMENT_EXTENSIONS:
        return True
    keyword_text = [normalize_text(keyword) for keyword in keywords]
    haystack = normalize_text(" ".join([url, link_text, surrounding_text]))
    return any(keyword in haystack for keyword in keyword_text)
