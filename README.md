# Disclosure Harvester

A resilient pipeline for discovering, downloading, classifying, extracting, validating, and publishing AMC monthly disclosure data.

The system is designed to fail safely: uncertain files are quarantined instead of being silently published.

## What It Does

- Discovers PDF/Excel disclosure files from configured AMC sources.
- Supports static pages, dynamic Playwright pages, and fixture mode for repeatable demos.
- Downloads only novel files using SHA256 content hashes.
- Classifies files using URL, filename, page context, and document header evidence.
- Uses canonical periods such as `2026-06`.
- Extracts rows into staging before validation.
- Resolves schemes at section/row level because one disclosure file can contain many schemes.
- Detects layout drift using last-known-good fingerprints.
- Publishes with business keys, not file IDs, so revised files supersede old rows safely.
- Stores audit and quarantine records for traceability.

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
```

## Run Fixture Demo

Fixture mode does not depend on live AMC websites and is useful for grading or offline checks.

```bash
python -m harvester.main run-fixtures
```

The local warehouse is created automatically at:

```text
data/warehouse/disclosure_harvester.duckdb
```

Generated databases and downloaded files are ignored by git.

## Run Tests

```bash
python -m unittest discover tests
```

If `pytest` is installed, this also works:

```bash
pytest
```

## Production Note

DuckDB is used for local demo mode because it requires no server. PostgreSQL can be added later by replacing the database adapter while keeping the same schema concepts.
