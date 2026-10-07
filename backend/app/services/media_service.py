from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import BinaryIO
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.media_asset import MediaAsset, MediaKind
from app.services.storage_service import LocalMediaStorage


IMAGE_FORMATS = {
    ".jpg": ("image/jpeg", MediaKind.IMAGE),
    ".jpeg": ("image/jpeg", MediaKind.IMAGE),
    ".png": ("image/png", MediaKind.IMAGE),
    ".webp": ("image/webp", MediaKind.IMAGE),
    ".gif": ("image/gif", MediaKind.IMAGE),
}
VIDEO_FORMATS = {
    ".mp4": ("video/mp4", MediaKind.VIDEO),
    ".webm": ("video/webm", MediaKind.VIDEO),
}
SUPPORTED_FORMATS = {**IMAGE_FORMATS, **VIDEO_FORMATS}


class MediaService:
    def __init__(self, db: Session):
        self.db = db
        settings = get_settings()
        self.storage = LocalMediaStorage(settings.media_root)
        self.max_upload_bytes = settings.media_max_upload_bytes

    def _validate_file(self, filename: str | None, content_type: str | None) -> tuple[str, str, MediaKind]:
        if not filename:
            raise ValueError("filename_required")
        extension = Path(filename).suffix.lower()
        if extension not in SUPPORTED_FORMATS:
            raise ValueError("unsupported_extension")
        expected_mime, media_kind = SUPPORTED_FORMATS[extension]
        if content_type != expected_mime:
            raise ValueError("invalid_mime_type")
        return extension, expected_mime, media_kind

    @staticmethod
    def _validate_signature(data: bytes, extension: str) -> None:
        valid = {
            ".jpg": data.startswith(b"\xff\xd8\xff"),
            ".jpeg": data.startswith(b"\xff\xd8\xff"),
            ".png": data.startswith(b"\x89PNG\r\n\x1a\n"),
            ".webp": len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP",
            ".gif": data.startswith((b"GIF87a", b"GIF89a")),
            ".mp4": len(data) >= 12 and data[4:8] == b"ftyp",
            ".webm": data.startswith(b"\x1a\x45\xdf\xa3"),
        }
        if not valid.get(extension, False):
            raise ValueError("invalid_file_signature")

    def upload(
        self,
        *,
        workspace_id: int,
        uploaded_by: int,
        filename: str | None,
        content_type: str | None,
        source: BinaryIO,
    ) -> MediaAsset:
        extension, mime_type, media_kind = self._validate_file(filename, content_type)
        data = source.read(self.max_upload_bytes + 1)
        if len(data) > self.max_upload_bytes:
            raise ValueError("file_too_large")
        self._validate_signature(data, extension)

        storage_key = self.storage.create_storage_key(workspace_id, extension)
        size, checksum = self.storage.save(BytesIO(data), storage_key)
        asset = MediaAsset(
            workspace_id=workspace_id,
            uploaded_by=uploaded_by,
            original_filename=Path(filename).name[:255],
            storage_key=storage_key,
            mime_type=mime_type,
            extension=extension,
            size_bytes=size,
            checksum=checksum,
            media_kind=media_kind,
        )
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def get(self, workspace_id: int, media_id: int) -> MediaAsset:
        asset = self.db.scalar(select(MediaAsset).where(MediaAsset.id == media_id, MediaAsset.workspace_id == workspace_id))
        if asset is None:
            raise ValueError("media_not_found")
        return asset

    def list(self, workspace_id: int) -> list[MediaAsset]:
        return list(
            self.db.scalars(
                select(MediaAsset).where(MediaAsset.workspace_id == workspace_id).order_by(MediaAsset.created_at.desc())
            ).all()
        )

    def delete(self, workspace_id: int, media_id: int) -> None:
        asset = self.get(workspace_id, media_id)
        self.storage.delete(asset.storage_key)
        self.db.delete(asset)
        self.db.commit()

    def validate_workspace_asset(self, workspace_id: int, media_id: int | None) -> None:
        if media_id is None:
            return
        self.get(workspace_id, media_id)
