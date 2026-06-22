from __future__ import annotations

import re
from typing import Any

from harvester.models import Classification, RawFile, StagingRow, ValidatedHolding
from harvester.publish.business_key import holding_business_key


ISIN_PATTERN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")


class ValidationError(Exception):
    pass


def validate_holdings(rows: list[StagingRow], classification: Classification, raw_file: RawFile) -> list[ValidatedHolding]:
    if not classification.period:
        raise ValidationError("missing canonical period")
    if not classification.document_type:
        raise ValidationError("missing document type")
    if not rows:
        raise ValidationError("no staging rows extracted")

    validated: list[ValidatedHolding] = []
    for row in rows:
        data = {str(k).strip().lower(): v for k, v in row.raw_data.items()}
        scheme_name = clean(data.get("scheme_name"))
        security_name = clean(data.get("security_name"))
        asset_type = clean(data.get("asset_type")) or "unknown"
        isin = clean(data.get("isin"))
        if not scheme_name:
            raise ValidationError(f"missing scheme on row {row.row_number}")
        if not security_name:
            raise ValidationError(f"missing security on row {row.row_number}")
        if isin and not ISIN_PATTERN.match(isin.upper()):
            raise ValidationError(f"invalid isin on row {row.row_number}")
        validated.append(
            ValidatedHolding(
                amc_name=classification.amc_name or "",
                scheme_name=scheme_name,
                period=classification.period,
                document_type=classification.document_type,
                holding_business_key=holding_business_key(isin, security_name, asset_type),
                isin=isin.upper() if isin else None,
                security_name=security_name,
                asset_type=asset_type,
                quantity=parse_float(data.get("quantity")),
                market_value=parse_float(data.get("market_value")),
                percentage_to_nav=parse_float(data.get("percentage_to_nav")),
                source_file_id=raw_file.file_id,
                source_sha256=raw_file.sha256,
            )
        )
    return validated


def clean(value: Any) -> str:
    return str(value or "").strip()


def parse_float(value: Any) -> float | None:
    text = str(value or "").replace(",", "").replace("%", "").strip()
    if not text:
        return None
    return float(text)
