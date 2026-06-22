from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname
from urllib.request import Request, urlopen

from harvester.models import DiscoveredDocument, RawFile
from harvester.utils import new_id, sha256_bytes


class DownloadError(Exception):
    pass


class Downloader:
    def __init__(self, raw_dir: Path, timeout_seconds: int = 30):
        self.raw_dir = raw_dir
        self.timeout_seconds = timeout_seconds

    def download(self, doc: DiscoveredDocument, run_id: str, already_seen: bool) -> RawFile:
        try:
            content = self._read(doc.document_url)
        except Exception as exc:
            raise DownloadError(f"failed to download {doc.document_url}: {exc}") from exc
        sha256 = sha256_bytes(content)
        extension = doc.file_type if doc.file_type != "unknown" else "bin"
        target_dir = self.raw_dir / doc.source_id / run_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{sha256}.{extension}"
        if not target_path.exists():
            target_path.write_bytes(content)
        return RawFile(
            file_id=new_id("file"),
            document_id=doc.document_id,
            source_id=doc.source_id,
            storage_path=target_path,
            sha256=sha256,
            file_size=len(content),
            mime_type=self._mime_type(extension),
            is_duplicate=already_seen,
        )

    def _read(self, url: str) -> bytes:
        parsed = urlparse(url)
        if parsed.scheme == "file":
            path_text = url2pathname(parsed.path)
            path = Path(path_text)
            if len(path_text) > 2 and path_text[0] == "/" and path_text[2] == ":":
                path = Path(path_text.lstrip("/"))
            return path.read_bytes()
        request = Request(url, headers={"User-Agent": "DisclosureHarvester/1.0"})
        with urlopen(request, timeout=self.timeout_seconds) as response:
            return response.read()

    @staticmethod
    def _mime_type(extension: str) -> str:
        return {
            "pdf": "application/pdf",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "xls": "application/vnd.ms-excel",
            "csv": "text/csv",
            "txt": "text/plain",
        }.get(extension, "application/octet-stream")
