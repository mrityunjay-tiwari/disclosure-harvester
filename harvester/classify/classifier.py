from __future__ import annotations

from pathlib import Path

from harvester.classify.confidence import score_document
from harvester.classify.period_parser import parse_period
from harvester.models import Classification, DiscoveredDocument, RawFile
from harvester.settings import Settings
from harvester.utils import normalize_text


DOCUMENT_TYPE_PATTERNS = {
    "monthly_portfolio": ("monthly portfolio", "portfolio disclosure", "portfolio"),
    "factsheet": ("factsheet", "fact sheet"),
}


class Classifier:
    def __init__(self, settings: Settings):
        self.settings = settings

    def classify(self, doc: DiscoveredDocument, raw_file: RawFile) -> Classification:
        file_text = self._read_light_text(raw_file.storage_path)
        name_and_link = " ".join([Path(doc.document_url).name, doc.link_text, doc.surrounding_text])
        combined = " ".join([name_and_link, file_text])
        normalized_combined = normalize_text(combined)
        normalized_doc = normalize_text(file_text)
        normalized_amc = normalize_text(doc.amc_name)

        name_period = parse_period(name_and_link)
        document_period = parse_period(file_text)
        period = document_period or name_period
        conflicting_period = bool(name_period and document_period and name_period != document_period)

        document_type = self._document_type(combined)
        document_type_from_link = self._document_type(name_and_link) is not None
        document_type_in_document = self._document_type(file_text) is not None

        amc_in_document = normalized_amc in normalized_doc
        conflicting_amc = False
        result = score_document(
            amc_from_source=True,
            amc_in_document=amc_in_document,
            period_from_name_or_link=name_period is not None,
            period_in_document=document_period is not None,
            document_type_from_link=document_type_from_link,
            document_type_in_document=document_type_in_document,
            missing_period=period is None,
            missing_document_type=document_type is None,
            conflicting_amc=conflicting_amc,
            conflicting_period=conflicting_period,
        )
        status = "classified"
        if result.hard_conflict or result.score < self.settings.confidence_auto_process_threshold:
            status = "quarantine"
        return Classification(
            file_id=raw_file.file_id,
            amc_name=doc.amc_name,
            period=period,
            document_type=document_type,
            confidence_score=result.score,
            status=status,
            hard_conflict=result.hard_conflict,
            evidence={
                "name_period": name_period,
                "document_period": document_period,
                "document_type": document_type,
                "amc_in_document": amc_in_document,
                "confidence_reasons": result.reasons,
                "text_sample": normalized_combined[:500],
            },
        )

    @staticmethod
    def _document_type(text: str) -> str | None:
        normalized = normalize_text(text)
        for doc_type, patterns in DOCUMENT_TYPE_PATTERNS.items():
            if any(pattern in normalized for pattern in patterns):
                return doc_type
        return None

    @staticmethod
    def _read_light_text(path: Path) -> str:
        if path.suffix.lower() in {".txt", ".csv"}:
            return path.read_text(encoding="utf-8", errors="ignore")[:10000]
        return path.name
