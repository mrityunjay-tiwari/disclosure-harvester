@echo off
REM ============================================================
REM  Disclosure Harvester - one-command grader demo (Windows)
REM  Runs every check that proves the assignment requirements.
REM  Run DuckDB commands one at a time (single-writer database).
REM ============================================================

setlocal

echo ============================================================
echo  DISCLOSURE HARVESTER - GRADER DEMO
echo  Each step below proves a specific assignment requirement.
echo ============================================================
echo.

echo [1/4] Environment check - dependencies must be present
python -m harvester.main doctor
echo.

echo [2/4] Deterministic verification - idempotency and data quality
echo       Proof: run 1 publishes rows, run 2 skips the duplicate file.
python -m harvester.main verify
echo.

echo [3/4] Test suite - confidence scoring, drift, validation, idempotency
python -m pytest -q
if errorlevel 1 python -m unittest discover tests
echo.

echo [4/4] Fixture pipeline - full discover to publish flow
python -m harvester.main --warehouse-path data/warehouse/grader_demo.duckdb run-fixtures
echo.

echo ============================================================
echo  DEMO COMPLETE - expected results:
echo   - step 2 "verify" prints  status: passed
echo   - step 3 test suite reports all tests passing
echo   - step 4 fixture run publishes 3 holdings
echo ============================================================

endlocal
