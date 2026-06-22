from __future__ import annotations

import uuid
from dataclasses import replace
from pathlib import Path
from typing import Any

from harvester.load.database import Database
from harvester.pipeline import Pipeline
from harvester.settings import Settings


TABLES_TO_COUNT = [
    "pipeline_runs",
    "discovered_documents",
    "raw_files",
    "document_classifications",
    "staging_rows",
    "published_holdings",
    "layout_fingerprints",
    "quarantine",
    "audit_events",
]


def run_verification() -> dict[str, Any]:
    settings = Settings()
    verification_id = uuid.uuid4().hex
    verify_settings = replace(
        settings,
        raw_dir=settings.raw_dir / "verification",
        quarantine_dir=settings.quarantine_dir / "verification",
        warehouse_path=settings.warehouse_dir / f"verification_{verification_id}.duckdb",
    )
    db = Database(verify_settings.warehouse_path)
    try:
        pipeline = Pipeline(verify_settings)
        first_run = pipeline._run("fixtures", db=db)
        second_run = pipeline._run("fixtures", db=db)
        table_counts = count_tables(db)
    finally:
        db.close()
    checks = {
        "first_run_published_rows": first_run.documents_published == 3,
        "second_run_skipped_duplicate": second_run.documents_skipped == 1,
        "published_holdings_present": table_counts["published_holdings"] == 3,
        "classification_present": table_counts["document_classifications"] >= 1,
        "layout_fingerprint_present": table_counts["layout_fingerprints"] >= 1,
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "database": str(verify_settings.warehouse_path),
        "first_run": first_run.as_dict(),
        "second_run": second_run.as_dict(),
        "table_counts": table_counts,
        "checks": checks,
    }


def count_tables(db: Database) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table in TABLES_TO_COUNT:
        row = db.fetchone(f"select count(*) from {table}")
        counts[table] = int(row[0])
    return counts
