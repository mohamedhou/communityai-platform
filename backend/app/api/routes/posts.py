from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.workspace_context import (
    WorkspaceContext,
    get_workspace_context,
    require_workspace_editor,
)
from app.models.post import PostApprovalStatus, PostStatus
from app.models.workspace import WorkspaceRole
from app.schemas.post import (
    PostCreate,
    PostRejectRequest,
    PostResponse,
    PostScheduleRequest,
    PostUpdate,
)
from app.services.post_service import PostService

router = APIRouter(prefix="/api/v1/posts", tags=["posts"])


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    payload: PostCreate,
    context: WorkspaceContext = Depends(require_workspace_editor),
    db: Session = Depends(get_db),
) -> PostResponse:
    service = PostService(db)
    try:
        post = service.create_post(
            workspace_id=context.workspace_id,
            user_id=context.user.id,
            social_account_id=payload.social_account_id,
            content=payload.content,
            media_url=payload.media_url,
            media_asset_id=payload.media_asset_id,
        )
        return PostResponse.model_validate(post)
    except ValueError as exc:
        if str(exc) == "social_account_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Social account not found",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Media asset does not belong to your workspace" if str(exc) == "media_not_authorized" else "Social account does not belong to your workspace",
        ) from exc


@router.get("", response_model=list[PostResponse])
def list_posts(
    status_filter: PostStatus | None = None,
    approval_status: PostApprovalStatus | None = None,
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
) -> list[PostResponse]:
    service = PostService(db)
    posts = service.list_posts(
        context.workspace_id,
        status=status_filter,
        approval_status=approval_status,
    )
    return [PostResponse.model_validate(p) for p in posts]


@router.get("/review/queue", response_model=list[PostResponse])
def get_review_queue(
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
) -> list[PostResponse]:
    service = PostService(db)
    posts = service.list_review_queue(context.workspace_id)
    return [PostResponse.model_validate(p) for p in posts]


@router.get("/review/history", response_model=list[PostResponse])
def get_review_history(
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
) -> list[PostResponse]:
    service = PostService(db)
    posts = service.list_review_history(context.workspace_id)
    return [PostResponse.model_validate(p) for p in posts]


@router.get("/{post_id}", response_model=PostResponse)
def get_post(
    post_id: int,
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
) -> PostResponse:
    service = PostService(db)
    try:
        post = service.get_post_by_id(context.workspace_id, post_id)
        return PostResponse.model_validate(post)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this post",
        ) from exc


@router.put("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    payload: PostUpdate,
    context: WorkspaceContext = Depends(require_workspace_editor),
    db: Session = Depends(get_db),
) -> PostResponse:
    service = PostService(db)
    try:
        updated_post = service.update_post(
            workspace_id=context.workspace_id,
            post_id=post_id,
            content=payload.content,
            media_url=payload.media_url,
            social_account_id=payload.social_account_id,
            media_asset_id=payload.media_asset_id,
            media_asset_id_provided="media_asset_id" in payload.model_fields_set,
        )
        return PostResponse.model_validate(updated_post)
    except ValueError as exc:
        if str(exc) == "post_not_found" or str(exc) == "social_account_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc).replace("_", " ").capitalize(),
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Media asset does not belong to your workspace" if str(exc) == "media_not_authorized" else "Not authorized to access resource",
        ) from exc


@router.delete("/{post_id}", status_code=status.HTTP_200_OK)
def delete_post(
    post_id: int,
    context: WorkspaceContext = Depends(require_workspace_editor),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    service = PostService(db)
    try:
        service.delete_post(context.workspace_id, post_id)
        return {"message": "Post deleted successfully"}
    except ValueError as exc:
        if str(exc) == "post_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this post",
        ) from exc


@router.post("/{post_id}/publish", response_model=PostResponse)
def publish_post(
    post_id: int,
    context: WorkspaceContext = Depends(require_workspace_editor),
    db: Session = Depends(get_db),
) -> PostResponse:
    service = PostService(db)
    try:
        post = service.publish_post(context.workspace_id, post_id, context.role)
        if post.status == PostStatus.FAILED:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=post.error_message,
            )
        return PostResponse.model_validate(post)
    except ValueError as exc:
        if str(exc) == "post_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access resource",
        ) from exc


@router.post("/{post_id}/schedule", response_model=PostResponse)
def schedule_post(
    post_id: int,
    payload: PostScheduleRequest,
    context: WorkspaceContext = Depends(require_workspace_editor),
    db: Session = Depends(get_db),
) -> PostResponse:
    service = PostService(db)
    try:
        post = service.schedule_post(
            context.workspace_id,
            post_id,
            payload.scheduled_at,
            actor_user_id=context.user.id,
            actor_role=context.role,
        )
        return PostResponse.model_validate(post)
    except ValueError as exc:
        if str(exc) == "post_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this post",
        ) from exc


@router.post("/{post_id}/cancel", response_model=PostResponse)
def cancel_post(
    post_id: int,
    context: WorkspaceContext = Depends(require_workspace_editor),
    db: Session = Depends(get_db),
) -> PostResponse:
    service = PostService(db)
    try:
        post = service.cancel_post(context.workspace_id, post_id)
        return PostResponse.model_validate(post)
    except ValueError as exc:
        if str(exc) == "post_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this post",
        ) from exc


@router.post("/{post_id}/submit-review", response_model=PostResponse)
def submit_for_review(
    post_id: int,
    context: WorkspaceContext = Depends(require_workspace_editor),
    db: Session = Depends(get_db),
) -> PostResponse:
    service = PostService(db)
    try:
        post = service.submit_for_review(context.workspace_id, post_id, context.user.id)
        return PostResponse.model_validate(post)
    except ValueError as exc:
        if str(exc) == "post_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this post",
        ) from exc


@router.post("/{post_id}/approve", response_model=PostResponse)
def approve_post(
    post_id: int,
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
) -> PostResponse:
    if context.role not in (WorkspaceRole.OWNER, WorkspaceRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owners and admins can approve posts",
        )
    service = PostService(db)
    try:
        post = service.approve_post(context.workspace_id, post_id, context.user.id, context.role)
        return PostResponse.model_validate(post)
    except ValueError as exc:
        if str(exc) == "post_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.post("/{post_id}/reject", response_model=PostResponse)
def reject_post(
    post_id: int,
    payload: PostRejectRequest,
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
) -> PostResponse:
    if context.role not in (WorkspaceRole.OWNER, WorkspaceRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owners and admins can reject posts",
        )
    service = PostService(db)
    try:
        post = service.reject_post(
            context.workspace_id,
            post_id,
            context.user.id,
            context.role,
            payload.reason,
        )
        return PostResponse.model_validate(post)
    except ValueError as exc:
        if str(exc) == "post_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
