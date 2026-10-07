from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import BinaryIO


class LocalMediaStorage:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, storage_key: str) -> Path:
        path = (self.root / storage_key).resolve()
        if path != self.root and self.root not in path.parents:
            raise ValueError("invalid_storage_key")
        return path

    def create_storage_key(self, workspace_id: int, extension: str) -> str:
        return f"{workspace_id}/{uuid.uuid4().hex}{extension}"

    def save(self, source: BinaryIO, storage_key: str) -> tuple[int, str]:
        path = self._safe_path(storage_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        size = 0
        digest = hashlib.sha256()
        with path.open("wb") as destination:
            while chunk := source.read(1024 * 1024):
                size += len(chunk)
                digest.update(chunk)
                destination.write(chunk)
        return size, digest.hexdigest()

    def delete(self, storage_key: str) -> None:
        path = self._safe_path(storage_key)
        if path.exists():
            path.unlink()

    def open(self, storage_key: str) -> Path:
        path = self._safe_path(storage_key)
        if not path.is_file():
            raise FileNotFoundError(storage_key)
        return path
