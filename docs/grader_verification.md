# Grader Verification

This project is a CLI pipeline, not a web API. It is verified with terminal commands and DuckDB table output rather than Postman.

## 1. Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
```

## 2. Check Environment

```bash
python -m harvester.main doctor
```

Expected:

```text
ready_for_fixture_demo: true
ready_for_live_demo: true
```

If `ready_for_live_demo` is false, fixture verification and unit tests still prove the core pipeline. Live discovery depends on browser binaries, network access, and AMC website availability.

## 3. Run One-Command Verification

```bash
python -m harvester.main verify
```

This uses the fixture disclosure file at:

```text
tests/fixtures/documents/sbi_monthly_portfolio_june_2026.txt
```

It proves source config loading, discovery, download and SHA256 hashing, duplicate detection, classification, extraction, validation, publishing, and layout fingerprint creation.

Expected important checks:

```json
{
  "first_run_published_rows": true,
  "second_run_skipped_duplicate": true,
  "published_holdings_present": true,
  "classification_present": true,
  "layout_fingerprint_present": true
}
```

## 4. Run Tests

```bash
python -m unittest discover tests
```

Expected:

```text
OK
```

## 5. Run Live AMC Discovery

```bash
python -m harvester.main run-live
```

Live mode uses the active sources in `configs/sources.yaml`. Dynamic sources use Playwright and network-response capture.

Real AMC sites can block automation, change layouts, or return temporary errors. In those cases the correct behavior is quarantine/audit, not silent publishing.

## 6. Inspect Warehouse

After `run-fixtures`, inspect DuckDB:

```bash
python -c "import duckdb; con=duckdb.connect('data/warehouse/disclosure_harvester.duckdb'); print(con.sql('select * from pipeline_runs').df())"
python -c "import duckdb; con=duckdb.connect('data/warehouse/disclosure_harvester.duckdb'); print(con.sql('select source_id, document_url from discovered_documents').df())"
python -c "import duckdb; con=duckdb.connect('data/warehouse/disclosure_harvester.duckdb'); print(con.sql('select amc_name, period, document_type, confidence_score, status from document_classifications').df())"
python -c "import duckdb; con=duckdb.connect('data/warehouse/disclosure_harvester.duckdb'); print(con.sql('select amc_name, scheme_name, period, security_name, isin, is_current from published_holdings').df())"
python -c "import duckdb; con=duckdb.connect('data/warehouse/disclosure_harvester.duckdb'); print(con.sql('select reason, details_json from quarantine').df())"
```

The deterministic proof is `verify`; live mode is included to demonstrate the intended real-world path.

## Note On Local DuckDB Files

DuckDB is an embedded database. Run verification commands one at a time, not in parallel, because concurrent local writers can lock the `.duckdb.wal` file on Windows.

To use a fresh database path for any manual one-pass run:

```bash
python -m harvester.main --warehouse-path data/warehouse/manual_check.duckdb run-fixtures
python -m harvester.main --warehouse-path data/warehouse/live_check.duckdb run-live
```

Use `python -m harvester.main verify` for the two-pass duplicate-skip proof. It keeps one managed DuckDB connection open for both passes, which avoids Windows WAL timing issues.
