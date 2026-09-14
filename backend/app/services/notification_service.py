from __future__ import annotations

from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationSeverity, NotificationType
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import (
    NotificationCreate,
    NotificationListResponse,
    NotificationResponse,
    NotificationUnreadCountResponse,
    validate_internal_action_url,
)


class NotificationService:
    def __init__(self, repository: NotificationRepository | None = None):
        self.repository = repository or NotificationRepository()

    def list_notifications(
        self,
        db: Session,
        user_id: int,
        type: NotificationType | None = None,
        severity: NotificationSeverity | None = None,
        is_read: bool | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> NotificationListResponse:
        page = max(1, page)
        limit = max(1, min(limit, 100))
        offset = (page - 1) * limit

        items, total = self.repository.list_notifications(
            db=db,
            user_id=user_id,
            type=type,
            severity=severity,
            is_read=is_read,
            limit=limit,
            offset=offset,
        )
        unread_count = self.repository.count_unread(db=db, user_id=user_id)

        return NotificationListResponse(
            items=[NotificationResponse.model_validate(item) for item in items],
            total=total,
            unread_count=unread_count,
            page=page,
            limit=limit,
        )

    def get_unread_count(self, db: Session, user_id: int) -> NotificationUnreadCountResponse:
        count = self.repository.count_unread(db=db, user_id=user_id)
        return NotificationUnreadCountResponse(unread_count=count)

    def get_notification_by_id(self, db: Session, notification_id: int, user_id: int) -> Notification:
        notification = self.repository.get_by_id(db=db, notification_id=notification_id, user_id=user_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )
        return notification

    def mark_read(self, db: Session, notification_id: int, user_id: int, is_read: bool = True) -> Notification:
        notification = self.repository.mark_read(
            db=db,
            notification_id=notification_id,
            user_id=user_id,
            is_read=is_read,
        )
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )
        return notification

    def mark_all_read(self, db: Session, user_id: int) -> int:
        return self.repository.mark_all_read(db=db, user_id=user_id)

    def delete_notification(self, db: Session, notification_id: int, user_id: int) -> None:
        deleted = self.repository.delete(db=db, notification_id=notification_id, user_id=user_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )

    def create_notification(self, db: Session, notification_in: NotificationCreate) -> Notification:
        # Strictly validate action_url if present
        if notification_in.action_url:
            notification_in.action_url = validate_internal_action_url(notification_in.action_url)
        return self.repository.create(db=db, notification_in=notification_in)

    # -------------------------------------------------------------------------
    # Notification Dispatch Helpers
    # -------------------------------------------------------------------------

    def notify_post_published(
        self,
        db: Session,
        user_id: int,
        post_id: int,
        title: str = "Publication réussie",
        message: str | None = None,
        action_url: str = "/posts",
    ) -> Notification:
        msg = message or f"Votre publication #{post_id} a été publiée avec succès sur vos réseaux."
        return self.create_notification(
            db=db,
            notification_in=NotificationCreate(
                user_id=user_id,
                type=NotificationType.POST_PUBLISHED,
                title=title,
                message=msg,
                severity=NotificationSeverity.SUCCESS,
                action_url=action_url,
                entity_type="post",
                entity_id=str(post_id),
            ),
        )

    def notify_post_failed(
        self,
        db: Session,
        user_id: int,
        post_id: int,
        error_message: str | None = None,
        title: str = "Publication échouée",
        action_url: str = "/posts",
    ) -> Notification:
        detail = f" : {error_message}" if error_message else "."
        msg = f"La publication du post #{post_id} a échoué{detail}"
        return self.create_notification(
            db=db,
            notification_in=NotificationCreate(
                user_id=user_id,
                type=NotificationType.POST_FAILED,
                title=title,
                message=msg,
                severity=NotificationSeverity.ERROR,
                action_url=action_url,
                entity_type="post",
                entity_id=str(post_id),
            ),
        )

    def notify_post_scheduled(
        self,
        db: Session,
        user_id: int,
        post_id: int,
        scheduled_at: datetime | str | None = None,
        title: str = "Publication programmée",
        action_url: str = "/calendar",
    ) -> Notification:
        date_str = f" pour le {scheduled_at}" if scheduled_at else ""
        msg = f"Votre post #{post_id} a été programmé avec succès{date_str}."
        return self.create_notification(
            db=db,
            notification_in=NotificationCreate(
                user_id=user_id,
                type=NotificationType.POST_SCHEDULED,
                title=title,
                message=msg,
                severity=NotificationSeverity.INFO,
                action_url=action_url,
                entity_type="post",
                entity_id=str(post_id),
            ),
        )

    def notify_inbox_message(
        self,
        db: Session,
        user_id: int,
        message_id: int,
        sender_name: str,
        preview: str | None = None,
        title: str = "Nouvelle interaction Inbox",
        action_url: str = "/inbox",
    ) -> Notification:
        snippet = f' : "{preview[:60]}..."' if preview and len(preview) > 60 else (f' : "{preview}"' if preview else "")
        msg = f"Nouveau message reçu de {sender_name}{snippet}"
        return self.create_notification(
            db=db,
            notification_in=NotificationCreate(
                user_id=user_id,
                type=NotificationType.INBOX_MESSAGE,
                title=title,
                message=msg,
                severity=NotificationSeverity.INFO,
                action_url=action_url,
                entity_type="inbox_message",
                entity_id=str(message_id),
            ),
        )

    def notify_ai_suggestion(
        self,
        db: Session,
        user_id: int,
        title: str = "Suggestion IA disponible",
        message: str = "Une nouvelle suggestion de contenu ou réponse est disponible.",
        action_url: str = "/ai",
    ) -> Notification:
        return self.create_notification(
            db=db,
            notification_in=NotificationCreate(
                user_id=user_id,
                type=NotificationType.AI_SUGGESTION,
                title=title,
                message=message,
                severity=NotificationSeverity.INFO,
                action_url=action_url,
                entity_type="ai",
                entity_id=None,
            ),
        )

    def notify_social_account(
        self,
        db: Session,
        user_id: int,
        title: str,
        message: str,
        severity: NotificationSeverity = NotificationSeverity.WARNING,
        action_url: str = "/social-accounts",
    ) -> Notification:
        return self.create_notification(
            db=db,
            notification_in=NotificationCreate(
                user_id=user_id,
                type=NotificationType.SOCIAL_ACCOUNT,
                title=title,
                message=message,
                severity=severity,
                action_url=action_url,
                entity_type="social_account",
                entity_id=None,
            ),
        )

    def notify_analytics(
        self,
        db: Session,
        user_id: int,
        title: str,
        message: str,
        severity: NotificationSeverity = NotificationSeverity.INFO,
        action_url: str = "/analytics",
    ) -> Notification:
        return self.create_notification(
            db=db,
            notification_in=NotificationCreate(
                user_id=user_id,
                type=NotificationType.ANALYTICS,
                title=title,
                message=message,
                severity=severity,
                action_url=action_url,
                entity_type="analytics",
                entity_id=None,
            ),
        )

    def notify_system(
        self,
        db: Session,
        user_id: int,
        title: str,
        message: str,
        severity: NotificationSeverity = NotificationSeverity.INFO,
        action_url: str | None = None,
    ) -> Notification:
        return self.create_notification(
            db=db,
            notification_in=NotificationCreate(
                user_id=user_id,
                type=NotificationType.SYSTEM,
                title=title,
                message=message,
                severity=severity,
                action_url=action_url,
                entity_type="system",
                entity_id=None,
            ),
        )
