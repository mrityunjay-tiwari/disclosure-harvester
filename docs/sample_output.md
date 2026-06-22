# Sample Output

## Environment Check

```bash
python -m harvester.main doctor
```

Example shape:

```json
{
  "python": "3.12.x",
  "ready_for_fixture_demo": true,
  "ready_for_live_demo": true,
  "dependencies": [
    {
      "name": "duckdb",
      "import_name": "duckdb",
      "required_for": "local warehouse",
      "installed": true
    }
  ]
}
```

## Fixture Pipeline

```bash
python -m harvester.main run-fixtures
```

Expected shape:

```json
{
  "documents_downloaded": 1,
  "documents_found": 1,
  "documents_published": 3,
  "documents_quarantined": 0,
  "documents_skipped": 0,
  "sources_checked": 3
}
```

The fixture file contains two schemes and one non-ISIN holding, so it exercises multi-scheme extraction and null-ISIN business-key handling.

## Test Suite

```bash
python -m unittest discover tests
```

Expected result:

```text
OK
```
