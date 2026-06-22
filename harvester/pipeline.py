from __future__ import annotations

from dataclasses import dataclass, field

from harvester.classify.classifier import Classifier
from harvester.config import load_sources
from harvester.discovery.fixture_discovery import FixtureDiscovery
from harvester.download.downloader import Downloader
from harvester.extract.text_fixture_extractor import TextFixtureExtractor
from harvester.load.database import Database
from harvester.load.repository import Repository
from harvester.publish.publisher import Publisher
from harvester.settings import Settings
from harvester.utils import new_id
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
        self.settings.ensure_directories()
        db = Database(self.settings.warehouse_path)
        db.initialize(self.settings.schema_path)
        repo = Repository(db)
        run_id = new_id("run")
        stats = PipelineStats()
        repo.create_run(run_id)
        try:
            sources = [source for source in load_sources(self.settings.source_config_path) if source.active]
            discovery = FixtureDiscovery(self.settings.project_root)
            downloader = Downloader(self.settings.raw_dir, self.settings.request_timeout_seconds)
            classifier = Classifier(self.settings)
            extractor = TextFixtureExtractor()
            publisher = Publisher(db)

            for source in sources:
                stats.sources_checked += 1
                docs = discovery.discover(source, run_id)
                stats.documents_found += len(docs)
                for doc in docs:
                    repo.insert_discovered(doc)
                    content_sha_seen_before = False
                    raw = downloader.download(doc, run_id, already_seen=False)
                    content_sha_seen_before = repo.sha_exists(raw.sha256)
                    if content_sha_seen_before:
                        stats.documents_skipped += 1
                        repo.audit("duplicate_file_skipped", "File hash already exists", run_id, source_id=source.source_id, metadata={"sha256": raw.sha256})
                        continue
                    repo.insert_raw_file(raw)
                    stats.documents_downloaded += 1

                    classification = classifier.classify(doc, raw)
                    repo.insert_classification(classification)
                    if classification.status == "quarantine":
                        stats.documents_quarantined += 1
                        repo.add_quarantine(raw.file_id, "classification_below_threshold_or_conflict", classification.evidence, classification.confidence_score)
                        continue

                    rows = extractor.extract(raw.file_id, raw.storage_path) if extractor.can_extract(raw.storage_path) else []
                    repo.insert_staging_rows(rows)
                    try:
                        holdings = validate_holdings(rows, classification, raw)
                    except ValidationError as exc:
                        stats.documents_quarantined += 1
                        repo.add_quarantine(raw.file_id, "validation_failed", {"error": str(exc)}, classification.confidence_score)
                        continue
                    stats.documents_published += publisher.publish(holdings)

            repo.finish_run(run_id, "succeeded", stats.as_dict())
            return stats
        except Exception as exc:
            repo.finish_run(run_id, "failed", stats.as_dict(), str(exc))
            raise
        finally:
            db.close()
