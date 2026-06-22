from __future__ import annotations

from harvester.utils import normalize_text


def holding_business_key(isin: str | None, security_name: str, asset_type: str) -> str:
    normalized_isin = (isin or "").strip().upper()
    if normalized_isin:
        return f"isin:{normalized_isin}"
    normalized_security = normalize_text(security_name)
    normalized_asset_type = normalize_text(asset_type or "unknown")
    return f"name:{normalized_security}|asset:{normalized_asset_type}"
