from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from harvester.models import StagingRow


class ExtractionError(Exception):
    pass


class Extractor(ABC):
    parser_name: str

    @abstractmethod
    def can_extract(self, path: Path) -> bool:
        raise NotImplementedError

    @abstractmethod
    def extract(self, file_id: str, path: Path) -> list[StagingRow]:
        raise NotImplementedError
