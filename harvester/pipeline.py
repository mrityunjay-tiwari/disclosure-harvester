from __future__ import annotations

from dataclasses import dataclass, field

from harvester.classify.classifier import Classifier
from harvester.config import load_sources
from harvester.discovery.browser_discovery import BrowserDiscovery
from harvester.discovery.fixture_discovery import FixtureDiscovery
from harvester.discovery.static_discovery import StaticDiscovery
from harvester.download.downloader import DownloadError, Downloader
from harvester.extract.base import ExtractionError
from harvester.extract.registry import ExtractorRegistry
from harvester.load.database import Database
from harvester.load.repository import Repository
from harvester.publish.publisher import Publisher
from harvester.settings import Settings
from harvester.utils import new_id
from harvester.validate.layout_fingerprint import LayoutFingerprintStore
from harvester.validate.rules import ValidationError, validate_holdings


@dataclass
class PipelineStats:
    sources_checked: int = 0
    documents_found: int = 0
    documents_downloaded: int = 0
    documents_skipped: int = 0
    documents_quarantined: int = 0
    documents_published: int = 0

    def as_dict(self) -> dict[str, int]:
        return self.__dict__.copy()


@dataclass
class Pipeline:
    settings: Settings = field(default_factory=Settings)

    def run_fixtures(self) -> PipelineStats:
        return self._run(mode="fixtures")

    def run_live_static(self) -> PipelineStats:
        return self._run(mode="live-static")

    def run_live(self) -> PipelineStats:
        return self._run(mode="live")

    def _run(self, mode: str, db: Database | None = None) -> PipelineStats:
        self.settings.ensure_directories()
        owns_db = db is None
        db = db or Database(self.settings.warehouse_path)
        db.initialize(self.settings.schema_path)
        repo = Repository(db)
        run_id = new_id("run")
        stats = PipelineStats()
        repo.create_run(run_id)
        try:
            sources = [source for source in load_sources(self.settings.source_config_path) if source.active]
            fixture_discovery = FixtureDiscovery(self.settings.project_root)
            static_discovery = StaticDiscovery(
                timeout_seconds=self.settings.request_timeout_seconds,
                retry_count=self.settings.retry_count,
                retry_initial_delay_seconds=self.settings.retry_initial_delay_seconds,
            )
            browser_discovery = BrowserDiscovery(
                timeout_seconds=self.settings.request_timeout_seconds,
                retry_count=self.settings.retry_count,
                retry_initial_delay_seconds=self.settings.retry_initial_delay_seconds,
            )
            downloader = Downloader(self.settings.raw_dir, self.settings.request_timeout_seconds)
            classifier = Classifier(self.settings)
            extractor_registry = ExtractorRegistry()
            publisher = Publisher(db)
            fingerprints = LayoutFingerprintStore(db)

            for source in sources:
                stats.sources_checked += 1
                for url in source.urls:
                    repo.upsert_source(source.source_id, source.amc_name, url, source.source_type, source.active, source.validated_end_to_end)
                try:
                    if mode == "fixtures":
                        docs = fixture_discovery.discover(source, run_id)
                    elif mode == "live" and source.source_type == "js":
                        docs = browser_discovery.discover(source, run_id)
                    else:
                        docs = static_discovery.discover(source, run_id)
                except Exception as exc:
                    stats.documents_quarantined += 1
                    repo.add_quarantine(None, "source_discovery_failed", {"source_id": source.source_id, "error": str(exc)})
                    repo.audit("source_degraded", "Discovery failed after retries", run_id, source_id=source.source_id, metadata={"error": str(exc)})
                    continue
                stats.documents_found += len(docs)
                if mode != "fixtures" and not docs:
                    repo.audit("source_empty", "No documents discovered for active source", run_id, source_id=source.source_id)
                for doc in docs:
                    try:
                        self._process_document(
                            doc,
                            run_id,
                            source,
                            stats,
                            repo,
                            downloader,
                            classifier,
                            extractor_registry,
                            fingerprints,
                            publisher,
                        )
                    except Exception as exc:
                        stats.documents_quarantined += 1
                        repo.add_quarantine(None, "unexpected_processing_error", {"document_url": doc.document_url, "error": str(exc)})
                        repo.audit("processing_error", "Unexpected error while processing document", run_id, source_id=source.source_id, metadata={"document_url": doc.document_url, "error": str(exc)})
                        continue

            repo.finish_run(run_id, "succeeded", stats.as_dict())
            return stats
        except Exception as exc:
            repo.finish_run(run_id, "failed", stats.as_dict(), str(exc))
            raise
        finally:
            if owns_db:
                db.close()

    def _process_document(
        self,
        doc,
        run_id,
        source,
        stats,
        repo,
        downloader,
        classifier,
        extractor_registry,
        fingerprints,
        publisher,
    ) -> None:
        repo.insert_discovered(doc)
        try:
            raw = downloader.download(doc, run_id, already_seen=False)
        except DownloadError as exc:
            stats.documents_quarantined += 1
            repo.add_quarantine(None, "download_failed", {"document_url": doc.document_url, "error": str(exc)})
            repo.audit("download_failed", "Document download failed", run_id, source_id=source.source_id, metadata={"document_url": doc.document_url, "error": str(exc)})
            return
        if repo.sha_exists(raw.sha256):
            stats.documents_skipped += 1
            repo.audit("duplicate_file_skipped", "File hash already exists", run_id, source_id=source.source_id, metadata={"sha256": raw.sha256})
            return
        repo.insert_raw_file(raw)
        stats.documents_downloaded += 1

        classification = classifier.classify(doc, raw)
        repo.insert_classification(classification)
        if classification.status == "quarantine":
            stats.documents_quarantined += 1
            repo.add_quarantine(raw.file_id, "classification_below_threshold_or_conflict", classification.evidence, classification.confidence_score)
            return

        try:
            rows = extractor_registry.extract(raw.file_id, raw.storage_path)
        except ExtractionError as exc:
            stats.documents_quarantined += 1
            repo.add_quarantine(raw.file_id, "extraction_failed", {"error": str(exc)}, classification.confidence_score)
            repo.audit("extraction_failed", "No parser produced valid rows", run_id, raw.file_id, source.source_id, {"error": str(exc)})
            return
        repo.insert_staging_rows(rows)
        drift = fingerprints.check(source.source_id, classification, rows)
        if drift.drifted:
            stats.documents_quarantined += 1
            repo.add_quarantine(raw.file_id, "layout_drift_detected", {"reasons": drift.reasons}, classification.confidence_score)
            repo.audit("layout_drift_detected", "Current extraction differs from last known good baseline", run_id, raw.file_id, source.source_id, {"reasons": drift.reasons})
            return
        try:
            holdings = validate_holdings(rows, classification, raw)
        except ValidationError as exc:
            stats.documents_quarantined += 1
            repo.add_quarantine(raw.file_id, "validation_failed", {"error": str(exc)}, classification.confidence_score)
            return
        stats.documents_published += publisher.publish(holdings)
        fingerprints.update(source.source_id, classification, raw, rows)
