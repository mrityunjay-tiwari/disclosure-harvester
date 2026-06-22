from __future__ import annotations

import re


MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


def parse_period(text: str) -> str | None:
    normalized = text.lower()
    numeric = re.search(r"(?<!\d)(20\d{2})[-_/\.](0?[1-9]|1[0-2])(?!\d)", normalized)
    if numeric:
        return f"{int(numeric.group(1)):04d}-{int(numeric.group(2)):02d}"
    reverse_numeric = re.search(r"(?<!\d)(0?[1-9]|1[0-2])[-_/\.](20\d{2})(?!\d)", normalized)
    if reverse_numeric:
        return f"{int(reverse_numeric.group(2)):04d}-{int(reverse_numeric.group(1)):02d}"
    for month_text, month_number in MONTHS.items():
        match = re.search(rf"\b{month_text}\b\D{{0,20}}\b(20\d{{2}})\b", normalized)
        if match:
            return f"{int(match.group(1)):04d}-{month_number:02d}"
        match = re.search(rf"\b(20\d{{2}})\b\D{{0,20}}\b{month_text}\b", normalized)
        if match:
            return f"{int(match.group(1)):04d}-{month_number:02d}"
    return None
