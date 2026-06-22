from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from harvester.load.database import Database
from harvester.models import Classification, DiscoveredDocument, RawFile, StagingRow
from harvester.utils import new_id


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Repository:
    def __init__(self, db: Database):
        self.db = db

    def create_run(self, run_id: str) -> None:
        self.db.execute("insert into pipeline_runs (run_id, status) values (?, ?)", [run_id, "running"])

    def finish_run(self, run_id: str, status: str, stats: dict[str, Any], error: str | None = None) -> None:
        self.db.execute(
            """
            update pipeline_runs
            set finished_at = current_timestamp,
                status = ?,
                sources_checked = ?,
                documents_found = ?,
                documents_downloaded = ?,
                documents_skipped = ?,
                documents_quarantined = ?,
                documents_published = ?,
                error_message = ?
            where run_id = ?
            """,
            [
                status,
                stats.get("sources_checked", 0),
                stats.get("documents_found", 0),
                stats.get("documents_downloaded", 0),
                stats.get("documents_skipped", 0),
                stats.get("documents_quarantined", 0),
                stats.get("documents_published", 0),
                error,
                run_id,
            ],
        )

    def insert_discovered(self, doc: DiscoveredDocument) -> None:
        existing = self.db.fetchone("select document_id from discovered_documents where normalized_url = ?", [doc.normalized_url])
        if existing:
            return
        self.db.execute(
            """
            insert into discovered_documents
            (document_id, run_id, source_id, page_url, document_url, normalized_url, link_text, surrounding_text, file_type)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                doc.document_id,
                doc.run_id,
                doc.source_id,
                doc.page_url,
                doc.document_url,
                doc.normalized_url,
                doc.link_text,
                doc.surrounding_text,
                doc.file_type,
            ],
        )

    def sha_exists(self, sha256: str) -> bool:
        return self.db.fetchone("select file_id from raw_files where sha256 = ?", [sha256]) is not None

    def insert_raw_file(self, raw_file: RawFile) -> None:
        self.db.execute(
            """
            insert into raw_files
            (file_id, document_id, storage_path, sha256, file_size, mime_type, is_duplicate)
            values (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                raw_file.file_id,
                raw_file.document_id,
                str(raw_file.storage_path),
                raw_file.sha256,
                raw_file.file_size,
                raw_file.mime_type,
                raw_file.is_duplicate,
            ],
        )

    def insert_classification(self, classification: Classification) -> None:
        self.db.execute(
            """
            insert into document_classifications
            (classification_id, file_id, amc_name, period, document_type, confidence_score, status, hard_conflict, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                new_id("classification"),
                classification.file_id,
                classification.amc_name,
                classification.period,
                classification.document_type,
                classification.confidence_score,
                classification.status,
                classification.hard_conflict,
                json.dumps(classification.evidence, sort_keys=True),
            ],
        )

    def insert_staging_rows(self, rows: list[StagingRow]) -> None:
        for row in rows:
            self.db.execute(
                """
                insert into staging_rows
                (staging_id, file_id, sheet_or_page, section_name, scheme_name_raw, row_number, raw_data_json, parser_used)
                values (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    new_id("stage"),
                    row.file_id,
                    row.sheet_or_page,
                    row.section_name,
                    row.scheme_name_raw,
                    row.row_number,
                    json.dumps(row.raw_data, sort_keys=True),
                    row.parser_used,
                ],
            )

    def add_quarantine(self, file_id: str | None, reason: str, details: dict[str, Any], confidence_score: int | None = None) -> None:
        self.db.execute(
            """
            insert into quarantine (quarantine_id, file_id, reason, details_json, confidence_score, status)
            values (?, ?, ?, ?, ?, ?)
            """,
            [new_id("quarantine"), file_id, reason, json.dumps(details, sort_keys=True), confidence_score, "pending_review"],
        )

    def audit(self, event_type: str, message: str, run_id: str | None = None, file_id: str | None = None, source_id: str | None = None, metadata: dict[str, Any] | None = None) -> None:
        self.db.execute(
            """
            insert into audit_events (event_id, run_id, file_id, source_id, event_type, message, metadata_json)
            values (?, ?, ?, ?, ?, ?, ?)
            """,
            [new_id("event"), run_id, file_id, source_id, event_type, message, json.dumps(metadata or {}, sort_keys=True)],
        )
