from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConfidenceResult:
    score: int
    hard_conflict: bool
    reasons: list[str]


def score_document(
    *,
    amc_from_source: bool,
    amc_in_document: bool,
    period_from_name_or_link: bool,
    period_in_document: bool,
    document_type_from_link: bool,
    document_type_in_document: bool,
    missing_period: bool,
    missing_document_type: bool,
    conflicting_amc: bool,
    conflicting_period: bool,
) -> ConfidenceResult:
    score = 0
    reasons: list[str] = []
    if amc_from_source:
        score += 25
        reasons.append("amc_from_source")
    if amc_in_document:
        score += 25
        reasons.append("amc_in_document")
    if period_from_name_or_link:
        score += 15
        reasons.append("period_from_name_or_link")
    if period_in_document:
        score += 20
        reasons.append("period_in_document")
    if document_type_from_link:
        score += 10
        reasons.append("document_type_from_link")
    if document_type_in_document:
        score += 15
        reasons.append("document_type_in_document")
    if missing_period:
        score -= 25
        reasons.append("missing_period")
    if missing_document_type:
        score -= 15
        reasons.append("missing_document_type")

    hard_conflict = conflicting_amc or conflicting_period
    if conflicting_amc:
        reasons.append("conflicting_amc")
    if conflicting_period:
        reasons.append("conflicting_period")
    return ConfidenceResult(score=max(0, min(100, score)), hard_conflict=hard_conflict, reasons=reasons)
