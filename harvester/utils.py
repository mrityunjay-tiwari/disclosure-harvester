from __future__ import annotations

import hashlib
import re
import uuid
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "fbclid", "gclid"}


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    query = urlencode([(k, v) for k, v in parse_qsl(parsed.query) if k.lower() not in TRACKING_PARAMS])
    normalized = parsed._replace(netloc=parsed.netloc.lower(), fragment="", query=query)
    return urlunparse(normalized)


def normalize_text(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def file_type_from_path_or_url(value: str) -> str:
    lower = value.lower().split("?")[0]
    for ext in (".pdf", ".xlsx", ".xls", ".xlsb", ".csv", ".txt"):
        if lower.endswith(ext):
            return ext.lstrip(".")
    return "unknown"
