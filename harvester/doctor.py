from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class DependencyCheck:
    name: str
    import_name: str
    required_for: str
    installed: bool


def run_doctor() -> dict[str, object]:
    checks = [
        check("PyYAML", "yaml", "configuration loading"),
        check("beautifulsoup4", "bs4", "static link extraction"),
        check("duckdb", "duckdb", "local warehouse"),
        check("playwright", "playwright", "dynamic JS discovery"),
        check("pandas", "pandas", "Excel extraction"),
        check("openpyxl", "openpyxl", "xlsx parsing"),
        check("pdfplumber", "pdfplumber", "PDF extraction"),
    ]
    return {
        "python": sys.version.split()[0],
        "dependencies": [item.__dict__ for item in checks],
        "ready_for_fixture_demo": all(item.installed for item in checks if item.import_name in {"yaml", "bs4"}),
        "ready_for_live_demo": all(item.installed for item in checks),
    }


def check(name: str, import_name: str, required_for: str) -> DependencyCheck:
    return DependencyCheck(
        name=name,
        import_name=import_name,
        required_for=required_for,
        installed=importlib.util.find_spec(import_name) is not None,
    )
