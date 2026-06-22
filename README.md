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
- Uses an extractor registry for CSV, Excel, PDF, and fixture files.
- Emits structured JSON logs for pipeline start/finish and stores detailed audit events in the warehouse.

## Assignment Rubric Coverage

| Requirement | Implementation |
| --- | --- |
| Source config as data | `configs/sources.yaml` |
| Static and JS discovery | `StaticDiscovery`, `BrowserDiscovery` |
| Novelty heuristics | URL normalization and SHA256 hashing |
| Confidence scoring | `harvester/classify/` |
| Quarantine | `quarantine` table and pipeline failure paths |
| Staging -> validated -> published | `staging_rows`, validation rules, `Publisher` |
| Idempotency | content hashes plus published business keys |
| Drift detection | `layout_fingerprints` baseline checks |
| Observability | JSON logs plus `audit_events` |

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

Use `python -m harvester.main verify` to demonstrate idempotency. It runs the fixture pipeline twice through one managed database connection and proves that the second pass skips the already-seen file hash.

## Run Static Live Discovery

This mode is useful for simple HTML pages. Dynamic AMC pages will be handled by Playwright in a later pipeline layer.

```bash
python -m harvester.main run-live-static
```

## Run Full Live Discovery

This mode uses each source's configured type. Sources marked `js` use Playwright.

```bash
python -m harvester.main run-live
```

Pass `--verbose` before the command to print structured logs:

```bash
python -m harvester.main --verbose run-fixtures
```

## Check Environment

```bash
python -m harvester.main doctor
```

This reports installed optional dependencies. Fixture tests work with fewer packages; full live discovery needs Playwright and browser binaries.

## One-Command Verification

This is the easiest command for an evaluator to run after installing requirements:

```bash
python -m harvester.main verify
```

It creates an isolated verification warehouse, runs the fixture pipeline twice, and reports:

- first run published rows,
- second run skipped the duplicate file,
- warehouse table counts,
- classification, staging, publishing, and layout fingerprint evidence.

Run DuckDB-backed commands one at a time. Parallel local runs can lock the DuckDB WAL file on Windows.

To test against a fresh database without deleting old local generated files:

```bash
python -m harvester.main --warehouse-path data/warehouse/manual_check.duckdb run-fixtures
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

## Source Coverage

The first three sources are active for the demo path. Additional AMCs from the assignment prompt are included in `configs/sources.yaml` as inactive discovery-ready entries. They can be enabled one at a time after parser validation.

## Included Documents

- [Design document](docs/design.md)
- [Runbook](docs/runbook.md)
- [Grader verification](docs/grader_verification.md)
- [Sample output](docs/sample_output.md)

## Production Note

DuckDB is used for local demo mode because it requires no server. PostgreSQL can be added later by replacing the database adapter while keeping the same schema concepts.
