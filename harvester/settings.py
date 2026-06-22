from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    project_root: Path = Path(__file__).resolve().parents[1]
    source_config_path: Path = project_root / "configs" / "sources.yaml"
    schema_path: Path = project_root / "sql" / "001_create_tables.sql"
    data_dir: Path = project_root / "data"
    raw_dir: Path = data_dir / "raw"
    warehouse_dir: Path = data_dir / "warehouse"
    warehouse_path: Path = warehouse_dir / "disclosure_harvester.duckdb"
    quarantine_dir: Path = data_dir / "quarantine"
    request_timeout_seconds: int = 30
    retry_count: int = 3
    confidence_auto_process_threshold: int = 80
    confidence_manual_review_threshold: int = 50

    def ensure_directories(self) -> None:
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.warehouse_dir.mkdir(parents=True, exist_ok=True)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
