from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.inbox_message import InboxMessageType, InboxSentiment
from app.models.user import User
from app.schemas.ai import AIResponse
from app.schemas.inbox import (
    InboxListResponse,
    InboxMarkReadRequest,
    InboxMarkResolvedRequest,
    InboxMessageResponse,
    InboxReplyRequest,
    InboxSuggestReplyRequest,
    InboxUnreadCountResponse,
)
from app.services.inbox_service import InboxService

router = APIRouter(prefix="/api/v1/inbox", tags=["inbox"])
inbox_service = InboxService()


@router.get("", response_model=InboxListResponse)
def list_inbox_messages(
    type: InboxMessageType | None = Query(default=None),
    platform: str | None = Query(default=None),
    sentiment: InboxSentiment | None = Query(default=None),
    is_read: bool | None = Query(default=None),
    is_resolved: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InboxListResponse:
    return inbox_service.list_messages(
        db=db,
        user_id=current_user.id,
        type=type,
        platform=platform,
        sentiment=sentiment,
        is_read=is_read,
        is_resolved=is_resolved,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.get("/unread-count", response_model=InboxUnreadCountResponse)
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InboxUnreadCountResponse:
    return inbox_service.get_unread_count(db=db, user_id=current_user.id)


@router.post("/seed-mock", response_model=list[InboxMessageResponse], status_code=status.HTTP_201_CREATED)
def seed_mock_messages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[InboxMessageResponse]:
    created = inbox_service.seed_mock(db=db, user_id=current_user.id)
    return [InboxMessageResponse.model_validate(msg) for msg in created]


@router.get("/{message_id}", response_model=InboxMessageResponse)
def get_inbox_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InboxMessageResponse:
    msg = inbox_service.get_message_by_id(db=db, message_id=message_id, user_id=current_user.id)
    return InboxMessageResponse.model_validate(msg)


@router.patch("/{message_id}/read", response_model=InboxMessageResponse)
def mark_inbox_message_read(
    message_id: int,
    body: InboxMarkReadRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InboxMessageResponse:
    is_read = body.is_read if body is not None else True
    msg = inbox_service.mark_read(db=db, message_id=message_id, user_id=current_user.id, is_read=is_read)
    return InboxMessageResponse.model_validate(msg)


@router.patch("/{message_id}/resolve", response_model=InboxMessageResponse)
def mark_inbox_message_resolved(
    message_id: int,
    body: InboxMarkResolvedRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InboxMessageResponse:
    is_resolved = body.is_resolved if body is not None else True
    msg = inbox_service.mark_resolved(db=db, message_id=message_id, user_id=current_user.id, is_resolved=is_resolved)
    return InboxMessageResponse.model_validate(msg)


@router.post("/{message_id}/suggest-reply", response_model=AIResponse)
def suggest_inbox_reply(
    message_id: int,
    body: InboxSuggestReplyRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AIResponse:
    req = body or InboxSuggestReplyRequest()
    return inbox_service.suggest_reply(db=db, message_id=message_id, user_id=current_user.id, req=req)


@router.post("/{message_id}/reply", response_model=InboxMessageResponse)
def reply_to_inbox_message(
    message_id: int,
    body: InboxReplyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InboxMessageResponse:
    msg = inbox_service.send_reply(
        db=db,
        message_id=message_id,
        user_id=current_user.id,
        content=body.content,
    )
    return InboxMessageResponse.model_validate(msg)
