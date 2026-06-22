from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Source:
    source_id: str
    amc_name: str
    urls: list[str]
    source_type: str
    active: bool
    validated_end_to_end: bool
    document_keywords: list[str]
    fixture_documents: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DiscoveredDocument:
    document_id: str
    run_id: str
    source_id: str
    amc_name: str
    page_url: str
    document_url: str
    normalized_url: str
    link_text: str
    surrounding_text: str
    file_type: str


@dataclass(frozen=True)
class RawFile:
    file_id: str
    document_id: str
    source_id: str
    storage_path: Path
    sha256: str
    file_size: int
    mime_type: str
    is_duplicate: bool


@dataclass(frozen=True)
class Classification:
    file_id: str
    amc_name: str | None
    period: str | None
    document_type: str | None
    confidence_score: int
    status: str
    hard_conflict: bool
    evidence: dict[str, Any]


@dataclass(frozen=True)
class StagingRow:
    file_id: str
    sheet_or_page: str
    section_name: str | None
    scheme_name_raw: str | None
    row_number: int
    raw_data: dict[str, Any]
    parser_used: str


@dataclass(frozen=True)
class ValidatedHolding:
    amc_name: str
    scheme_name: str
    period: str
    document_type: str
    holding_business_key: str
    isin: str | None
    security_name: str
    asset_type: str
    quantity: float | None
    market_value: float | None
    percentage_to_nav: float | None
    source_file_id: str
    source_sha256: str
