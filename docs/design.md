# Disclosure Harvester Design

## Goal

Disclosure Harvester collects AMC monthly disclosure files, classifies them, extracts holdings, validates the output, and publishes only trusted data.

The system is not designed to pretend external websites never fail. It is designed to avoid silent data corruption. When confidence is low, metadata conflicts, extraction fails, or layout drift appears, the document is quarantined.

## Pipeline

```text
Source Config -> Discovery -> Download + Hashing -> Classification -> Extraction -> Validation -> Published Data
                                                        |                    |
                                                        v                    v
                                                   Quarantine          Drift Detection
```

## Key Design Choices

- Sources are defined in YAML, not hardcoded.
- DuckDB is used for local demo mode and is created automatically at runtime.
- Raw files are stored by `source_id/run_id/sha256` because period is not known at download time.
- SHA256 identifies file novelty.
- Published rows use business keys, not file IDs.
- Revised disclosure files supersede old current rows while preserving audit history.
- Periods are canonical `YYYY-MM`.
- Scheme identity is resolved during extraction because one monthly document can contain many schemes.
- PDF extraction starts with lightweight parsers. Docling is an optional fallback for difficult layouts.
- Excel extraction uses spreadsheet-native parsers because Excel already contains structured cells.
- Extraction is selected through a registry. If one parser cannot handle a file, the next eligible parser can try. If no parser succeeds, the file is quarantined with the parser failure reason.
- Dynamic sources use browser discovery with Playwright. The browser layer inspects rendered links and network responses, then deduplicates discovered document URLs by normalized URL.

## Confidence Scoring

Evidence sources vote: source config, URL, filename, link text, page context, and document header. Agreement increases confidence. Missing signals are soft penalties. Hard conflicts force quarantine.

Examples of hard conflicts:

- Filename says June 2026 but document header says May 2026.
- Source config says SBI but document text strongly indicates ICICI.

Thresholds:

```text
80-100: automatic processing
50-79: manual review
0-49: quarantine/reject
hard conflict: quarantine
```

## Drift Detection

Drift compares current extraction to the last known good baseline stored in `layout_fingerprints`.

Signals include missing headers, row-count anomalies, page-count changes, confidence drops, and zero extracted tables. Successful published documents update the baseline.

Source discovery failures are treated as source health problems. The system retries with exponential backoff, records an audit event, and continues with the remaining sources instead of stopping the full run.

## Warehouse Tables

The warehouse contains:

- `sources` for configured AMC URLs.
- `pipeline_runs` for run-level statistics.
- `discovered_documents` for discovered document links.
- `raw_files` for downloaded files and SHA256 hashes.
- `document_classifications` for AMC, period, type, confidence, and evidence.
- `staging_rows` for raw parser output.
- `published_holdings` for current and historical business records.
- `layout_fingerprints` for drift baselines.
- `quarantine` for documents that require review.
- `audit_events` for operational lineage.

## Revised File Policy

If an AMC republishes a corrected file for the same period, the new SHA256 is treated as a new file, but publishing uses the holding business key. Changed current holdings are superseded and replaced by the latest valid version. Old rows remain in history with `is_current = false`.

## Idempotency

The system uses two identities:

- File identity: SHA256, URL, file ID.
- Business identity: AMC, scheme, period, document type, holding key.

The final published table never uses `file_id` as the uniqueness boundary. `file_id` is lineage only.

## Quarantine

Documents are quarantined for low confidence, parser failure, hard conflicts, validation failure, unknown scheme, duplicate business conflicts, or drift.
