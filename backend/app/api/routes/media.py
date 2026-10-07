from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.workspace_context import WorkspaceContext, get_workspace_context, require_workspace_editor
from app.schemas.media import MediaAssetResponse
from app.services.media_service import MediaService

router = APIRouter(prefix="/api/v1/media", tags=["media"])


def _response(asset) -> MediaAssetResponse:
    return MediaAssetResponse.model_validate(
        {
            **asset.__dict__,
            "content_url": f"/api/v1/media/{asset.id}/content",
        }
    )


@router.post("", response_model=MediaAssetResponse, status_code=status.HTTP_201_CREATED)
def upload_media(
    file: UploadFile = File(...),
    context: WorkspaceContext = Depends(require_workspace_editor),
    db: Session = Depends(get_db),
) -> MediaAssetResponse:
    try:
        asset = MediaService(db).upload(
            workspace_id=context.workspace_id,
            uploaded_by=context.user.id,
            filename=file.filename,
            content_type=file.content_type,
            source=file.file,
        )
        return _response(asset)
    except ValueError as exc:
        details = {
            "filename_required": "Filename is required",
            "unsupported_extension": "Unsupported file extension",
            "invalid_mime_type": "Invalid MIME type",
            "invalid_file_signature": "File content does not match its declared type",
            "file_too_large": "File exceeds the configured upload limit",
        }
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=details.get(str(exc), str(exc))) from exc


@router.get("", response_model=list[MediaAssetResponse])
def list_media(
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
) -> list[MediaAssetResponse]:
    return [_response(asset) for asset in MediaService(db).list(context.workspace_id)]


@router.get("/{media_id}", response_model=MediaAssetResponse)
def get_media(
    media_id: int,
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
) -> MediaAssetResponse:
    try:
        return _response(MediaService(db).get(context.workspace_id, media_id))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found") from exc


@router.get("/{media_id}/content")
def get_media_content(
    media_id: int,
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
) -> FileResponse:
    service = MediaService(db)
    try:
        asset = service.get(context.workspace_id, media_id)
        path = service.storage.open(asset.storage_key)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found") from exc
    return FileResponse(path, media_type=asset.mime_type, filename=asset.original_filename)


@router.delete("/{media_id}", status_code=status.HTTP_200_OK)
def delete_media(
    media_id: int,
    context: WorkspaceContext = Depends(require_workspace_editor),
    db: Session = Depends(get_db),
) -> None:
    try:
        MediaService(db).delete(context.workspace_id, media_id)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found") from exc
