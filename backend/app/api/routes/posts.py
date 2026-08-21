from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.post import PostStatus
from app.schemas.post import PostCreate, PostUpdate, PostResponse, PostScheduleRequest
from app.services.post_service import PostService
from app.social.exceptions import SocialProviderError

router = APIRouter(prefix="/api/v1/posts", tags=["posts"])


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    payload: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PostResponse:
    service = PostService(db)
    try:
        post = service.create_post(
            user_id=current_user.id,
            social_account_id=payload.social_account_id,
            content=payload.content,
            media_url=payload.media_url,
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
            detail="You do not own this social account",
        ) from exc


@router.get("", response_model=list[PostResponse])
def list_posts(
    status_filter: PostStatus | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PostResponse]:
    service = PostService(db)
    posts = service.list_posts(current_user.id, status=status_filter)
    return [PostResponse.model_validate(p) for p in posts]


@router.get("/{post_id}", response_model=PostResponse)
def get_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PostResponse:
    service = PostService(db)
    try:
        post = service.get_post_by_id(current_user.id, post_id)
        return PostResponse.model_validate(post)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this post",
        ) from exc


@router.put("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    payload: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PostResponse:
    service = PostService(db)
    try:
        updated_post = service.update_post(
            user_id=current_user.id,
            post_id=post_id,
            content=payload.content,
            media_url=payload.media_url,
            social_account_id=payload.social_account_id,
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
            detail="Not authorized to access resource",
        ) from exc


@router.delete("/{post_id}", status_code=status.HTTP_200_OK)
def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    service = PostService(db)
    try:
        service.delete_post(current_user.id, post_id)
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
            detail="You do not own this post",
        ) from exc


@router.post("/{post_id}/publish", response_model=PostResponse)
def publish_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PostResponse:
    service = PostService(db)
    try:
        post = service.publish_post(current_user.id, post_id)
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PostResponse:
    service = PostService(db)
    try:
        post = service.schedule_post(current_user.id, post_id, payload.scheduled_at)
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
            detail="You do not own this post",
        ) from exc


@router.post("/{post_id}/cancel", response_model=PostResponse)
def cancel_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PostResponse:
    service = PostService(db)
    try:
        post = service.cancel_post(current_user.id, post_id)
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
            detail="You do not own this post",
        ) from exc
