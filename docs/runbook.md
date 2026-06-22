# Disclosure Harvester Runbook

## Add A New Source

1. Add the AMC to `configs/sources.yaml`.
2. Include the source URL, source type, and document keywords.
3. Run fixture or discovery mode.
4. Check discovered links.
5. Add parser/header tuning only if validation or drift detection requires it.

## Review Quarantine

1. Open the `quarantine` table.
2. Inspect `reason`, `details_json`, and `confidence_score`.
3. If metadata is wrong, correct AMC/period/document type.
4. If parser output is wrong, update extractor rules and add a regression test.
5. Reprocess the file only after the issue is understood.

## Handle Layout Drift

1. Compare current headers and row counts with `layout_fingerprints`.
2. Inspect the source file and extraction output.
3. Update parser mappings if the AMC changed layout.
4. Add a test fixture for the new layout.
5. Reprocess the quarantined document.

## Handle Revised Files

If the AMC posts a corrected file for the same period, the new SHA256 allows it to be processed. Publishing uses business keys, so changed holdings supersede old current rows. Old rows remain in history with `is_current = false`.
