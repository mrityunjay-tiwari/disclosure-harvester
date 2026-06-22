from __future__ import annotations

import json

from harvester.load.database import Database
from harvester.models import Classification, RawFile, StagingRow
from harvester.utils import new_id
from harvester.validate.drift import DriftResult, detect_drift


class LayoutFingerprintStore:
    def __init__(self, db: Database):
        self.db = db

    def check(self, source_id: str, classification: Classification, rows: list[StagingRow]) -> DriftResult:
        if not classification.amc_name or not classification.document_type:
            return DriftResult(drifted=False, reasons=[])
        current_headers = headers_from_rows(rows)
        current_row_count = len(rows)
        baseline = self.db.fetchone(
            """
            select expected_headers_json, last_good_row_count, last_good_confidence_avg
            from layout_fingerprints
            where source_id = ? and amc_name = ? and document_type = ? and scheme_name is null
            order by updated_at desc
            limit 1
            """,
            [source_id, classification.amc_name, classification.document_type],
        )
        if not baseline:
            return detect_drift(
                current_headers=current_headers,
                current_row_count=current_row_count,
                current_confidence=classification.confidence_score,
                expected_headers=None,
                last_good_row_count=None,
                last_good_confidence_avg=None,
            )
        expected_headers = set(json.loads(baseline[0]))
        return detect_drift(
            current_headers=current_headers,
            current_row_count=current_row_count,
            current_confidence=classification.confidence_score,
            expected_headers=expected_headers,
            last_good_row_count=int(baseline[1]),
            last_good_confidence_avg=float(baseline[2]),
        )

    def update(self, source_id: str, classification: Classification, raw_file: RawFile, rows: list[StagingRow]) -> None:
        if not classification.amc_name or not classification.document_type or not rows:
            return
        headers = sorted(headers_from_rows(rows))
        parser_used = rows[0].parser_used
        existing = self.db.fetchone(
            """
            select fingerprint_id
            from layout_fingerprints
            where source_id = ? and amc_name = ? and document_type = ? and scheme_name is null
            """,
            [source_id, classification.amc_name, classification.document_type],
        )
        if existing:
            self.db.execute(
                """
                update layout_fingerprints
                set expected_headers_json = ?,
                    last_good_row_count = ?,
                    last_good_confidence_avg = ?,
                    last_good_file_hash = ?,
                    parser_used = ?,
                    updated_at = current_timestamp
                where fingerprint_id = ?
                """,
                [json.dumps(headers), len(rows), classification.confidence_score, raw_file.sha256, parser_used, existing[0]],
            )
            return
        self.db.execute(
            """
            insert into layout_fingerprints
            (fingerprint_id, source_id, amc_name, document_type, scheme_name, expected_headers_json,
             last_good_row_count, last_good_confidence_avg, last_good_page_count, last_good_file_hash, parser_used)
            values (?, ?, ?, ?, null, ?, ?, ?, null, ?, ?)
            """,
            [
                new_id("fingerprint"),
                source_id,
                classification.amc_name,
                classification.document_type,
                json.dumps(headers),
                len(rows),
                classification.confidence_score,
                raw_file.sha256,
                parser_used,
            ],
        )


def headers_from_rows(rows: list[StagingRow]) -> set[str]:
    headers: set[str] = set()
    for row in rows:
        headers.update(str(key).strip().lower() for key in row.raw_data)
    return headers
