from __future__ import annotations

from pathlib import Path
import time
from typing import Any, Iterable


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = "duckdb"
        try:
            import duckdb  # type: ignore

            self.connection = self._connect_duckdb_with_retry(duckdb, path)
        except ModuleNotFoundError:
            import sqlite3

            self.engine = "sqlite"
            self.connection = sqlite3.connect(":memory:")
            self.connection.row_factory = sqlite3.Row

    def execute(self, sql: str, params: Iterable[Any] | None = None) -> None:
        self.connection.execute(sql, list(params or []))
        self._commit_if_needed()

    def executemany(self, sql: str, rows: Iterable[Iterable[Any]]) -> None:
        self.connection.executemany(sql, [list(row) for row in rows])
        self._commit_if_needed()

    def fetchone(self, sql: str, params: Iterable[Any] | None = None) -> Any | None:
        cursor = self.connection.execute(sql, list(params or []))
        return cursor.fetchone()

    def fetchall(self, sql: str, params: Iterable[Any] | None = None) -> list[Any]:
        cursor = self.connection.execute(sql, list(params or []))
        return list(cursor.fetchall())

    def initialize(self, schema_path: Path) -> None:
        schema = schema_path.read_text(encoding="utf-8")
        for statement in schema.split(";"):
            if statement.strip():
                self.execute(statement)

    def close(self) -> None:
        self.connection.close()

    def _commit_if_needed(self) -> None:
        if self.engine == "sqlite":
            self.connection.commit()

    @staticmethod
    def _connect_duckdb_with_retry(duckdb: Any, path: Path) -> Any:
        last_error: Exception | None = None
        for _ in range(10):
            try:
                return duckdb.connect(str(path))
            except Exception as exc:
                last_error = exc
                time.sleep(0.2)
        raise last_error or RuntimeError("failed to connect to DuckDB")
