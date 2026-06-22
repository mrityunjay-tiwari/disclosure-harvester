from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DriftResult:
    drifted: bool
    reasons: list[str]


def detect_drift(
    *,
    current_headers: set[str],
    current_row_count: int,
    current_confidence: int,
    expected_headers: set[str] | None,
    last_good_row_count: int | None,
    last_good_confidence_avg: float | None,
) -> DriftResult:
    reasons: list[str] = []
    if expected_headers:
        missing = expected_headers - current_headers
        if missing:
            reasons.append(f"missing_headers:{','.join(sorted(missing))}")
    if last_good_row_count and last_good_row_count > 0:
        if current_row_count < last_good_row_count * 0.30:
            reasons.append("row_count_dropped_below_30_percent")
        if current_row_count > last_good_row_count * 3.00:
            reasons.append("row_count_above_300_percent")
    if last_good_confidence_avg is not None and current_confidence < last_good_confidence_avg - 25:
        reasons.append("confidence_drop_above_25_points")
    if current_row_count == 0:
        reasons.append("zero_rows_extracted")
    return DriftResult(drifted=bool(reasons), reasons=reasons)
