from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse


class DocumentStore:
    def __init__(self, root: Path | str = ".jobctl/documents") -> None:
        self.root = Path(root)

    def write(self, name: str, content: bytes) -> str:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / name
        path.write_bytes(content)
        return str(path)

    def read(self, content_ref: str) -> bytes:
        return Path(content_ref).read_bytes()


def filename_from_uri(uri: str, fallback: str = "document") -> str:
    path = urlparse(uri).path
    name = Path(path).name
    return name or fallback
