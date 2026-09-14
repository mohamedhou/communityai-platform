from __future__ import annotations

from datetime import UTC, datetime
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationSeverity, NotificationType
from app.schemas.notification import NotificationCreate


class NotificationRepository:
    def get_by_id(self, db: Session, notification_id: int, user_id: int) -> Notification | None:
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        return db.scalars(stmt).first()

    def list_notifications(
        self,
        db: Session,
        user_id: int,
        type: NotificationType | None = None,
        severity: NotificationSeverity | None = None,
        is_read: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Notification], int]:
        base_query = select(Notification).where(Notification.user_id == user_id)

        if type is not None:
            base_query = base_query.where(Notification.type == type)

        if severity is not None:
            base_query = base_query.where(Notification.severity == severity)

        if is_read is not None:
            base_query = base_query.where(Notification.is_read == is_read)

        count_stmt = select(func.count()).select_from(base_query.subquery())
        total = db.scalar(count_stmt) or 0

        stmt = base_query.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
        items = list(db.scalars(stmt).all())

        return items, total

    def count_unread(self, db: Session, user_id: int) -> int:
        stmt = select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        return db.scalar(stmt) or 0

    def mark_read(
        self, db: Session, notification_id: int, user_id: int, is_read: bool = True
    ) -> Notification | None:
        notification = self.get_by_id(db, notification_id=notification_id, user_id=user_id)
        if not notification:
            return None

        notification.is_read = is_read
        notification.read_at = datetime.now(UTC) if is_read else None
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    def mark_all_read(self, db: Session, user_id: int) -> int:
        now = datetime.now(UTC)
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(is_read=True, read_at=now)
        )
        result = db.execute(stmt)
        db.commit()
        return result.rowcount or 0

    def delete(self, db: Session, notification_id: int, user_id: int) -> bool:
        notification = self.get_by_id(db, notification_id=notification_id, user_id=user_id)
        if not notification:
            return False

        db.delete(notification)
        db.commit()
        return True

    def create(self, db: Session, notification_in: NotificationCreate) -> Notification:
        db_obj = Notification(
            user_id=notification_in.user_id,
            type=notification_in.type,
            title=notification_in.title,
            message=notification_in.message,
            severity=notification_in.severity,
            action_url=notification_in.action_url,
            entity_type=notification_in.entity_type,
            entity_id=notification_in.entity_id,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
