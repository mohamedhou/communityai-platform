from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.notification import NotificationSeverity, NotificationType
from app.models.user import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationMarkReadRequest,
    NotificationResponse,
    NotificationUnreadCountResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])
notification_service = NotificationService()


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    type: NotificationType | None = Query(default=None),
    severity: NotificationSeverity | None = Query(default=None),
    is_read: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationListResponse:
    return notification_service.list_notifications(
        db=db,
        user_id=current_user.id,
        type=type,
        severity=severity,
        is_read=is_read,
        page=page,
        limit=limit,
    )


@router.get("/unread-count", response_model=NotificationUnreadCountResponse)
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationUnreadCountResponse:
    return notification_service.get_unread_count(db=db, user_id=current_user.id)


@router.get("/{id}", response_model=NotificationResponse)
def get_notification(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationResponse:
    notif = notification_service.get_notification_by_id(db=db, notification_id=id, user_id=current_user.id)
    return NotificationResponse.model_validate(notif)


@router.patch("/read-all", response_model=dict[str, Any])
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    count = notification_service.mark_all_read(db=db, user_id=current_user.id)
    return {"success": True, "marked_count": count}


@router.patch("/{id}/read", response_model=NotificationResponse)
def mark_notification_read(
    id: int,
    body: NotificationMarkReadRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationResponse:
    is_read = body.is_read if body is not None else True
    notif = notification_service.mark_read(db=db, notification_id=id, user_id=current_user.id, is_read=is_read)
    return NotificationResponse.model_validate(notif)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    notification_service.delete_notification(db=db, notification_id=id, user_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
