from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.media_asset import MediaKind


class MediaAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int
    uploaded_by: int
    original_filename: str
    mime_type: str
    extension: str
    size_bytes: int
    checksum: str
    media_kind: MediaKind
    created_at: datetime
    updated_at: datetime
    content_url: str
