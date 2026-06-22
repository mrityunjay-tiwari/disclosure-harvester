from __future__ import annotations

from pathlib import Path

from harvester.models import DiscoveredDocument, Source
from harvester.utils import file_type_from_path_or_url, new_id, normalize_url


class FixtureDiscovery:
    def __init__(self, project_root: Path):
        self.project_root = project_root

    def discover(self, source: Source, run_id: str) -> list[DiscoveredDocument]:
        documents: list[DiscoveredDocument] = []
        for fixture in source.fixture_documents:
            fixture_path = (self.project_root / fixture).resolve()
            document_url = fixture_path.as_uri()
            documents.append(
                DiscoveredDocument(
                    document_id=new_id("doc"),
                    run_id=run_id,
                    source_id=source.source_id,
                    amc_name=source.amc_name,
                    page_url=f"fixture://{source.source_id}",
                    document_url=document_url,
                    normalized_url=normalize_url(document_url),
                    link_text=fixture_path.name.replace("_", " "),
                    surrounding_text=f"{source.amc_name} Monthly Portfolio Disclosure",
                    file_type=file_type_from_path_or_url(str(fixture_path)),
                )
            )
        return documents
