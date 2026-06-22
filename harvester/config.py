from __future__ import annotations

from pathlib import Path

import yaml

from harvester.models import Source


def load_sources(path: Path) -> list[Source]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    sources: list[Source] = []
    for item in payload.get("sources", []):
        sources.append(
            Source(
                source_id=item["source_id"],
                amc_name=item["amc_name"],
                urls=list(item.get("urls", [])),
                source_type=item.get("source_type", "static"),
                active=bool(item.get("active", True)),
                validated_end_to_end=bool(item.get("validated_end_to_end", False)),
                document_keywords=list(item.get("document_keywords", [])),
                fixture_documents=list(item.get("fixture_documents", [])),
            )
        )
    return sources
