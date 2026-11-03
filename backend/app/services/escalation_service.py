from __future__ import annotations

import logging
from datetime import UTC, datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.inbox_message import InboxMessage
from app.models.ai_community_manager import AICMSettings, AICMAuditLog
from app.models.notification import NotificationSeverity, NotificationType
from app.models.user import User
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class EscalationService:
    """
    Handles assigning messages to team members, escalating sensitive conversations,
    and recording audit logs.
    """

    def __init__(self, notification_service: NotificationService | None = None):
        self.notification_service = notification_service or NotificationService()

    def assign_message(
        self,
        db: Session,
        workspace_id: int,
        message_id: int,
        assigned_to_user_id: int | None,
        actor_user_id: int | None = None,
    ) -> InboxMessage:
        message = (
            db.query(InboxMessage)
            .filter(
                InboxMessage.id == message_id,
                InboxMessage.workspace_id == workspace_id,
            )
            .first()
        )
        if not message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message introuvable.")

        target_user = None
        if assigned_to_user_id is not None:
            target_user = db.get(User, assigned_to_user_id)
            if not target_user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur cible introuvable.")

        message.assigned_to_user_id = assigned_to_user_id
        db.commit()
        db.refresh(message)

        # Audit log
        audit = AICMAuditLog(
            workspace_id=workspace_id,
            inbox_message_id=message.id,
            user_id=actor_user_id,
            action="ASSIGN",
            details={
                "assigned_to_user_id": assigned_to_user_id,
                "assigned_to_name": f"{target_user.first_name} {target_user.last_name}" if target_user else None,
            },
        )
        db.add(audit)
        db.commit()

        # Notify assigned user
        if assigned_to_user_id and actor_user_id != assigned_to_user_id:
            try:
                self.notification_service.create_notification(
                    db=db,
                    user_id=assigned_to_user_id,
                    type=NotificationType.INBOX_MESSAGE,
                    title="Nouveau message assigné",
                    message=f"Le message de {message.sender_name} vous a été assigné.",
                    severity=NotificationSeverity.INFO,
                    link="/inbox",
                )
            except Exception as exc:
                logger.warning("Could not dispatch notification: %s", exc)

        return message

    def escalate_message(
        self,
        db: Session,
        workspace_id: int,
        message_id: int,
        note: str,
        escalated_to_user_id: int | None = None,
        actor_user_id: int | None = None,
    ) -> InboxMessage:
        message = (
            db.query(InboxMessage)
            .filter(
                InboxMessage.id == message_id,
                InboxMessage.workspace_id == workspace_id,
            )
            .first()
        )
        if not message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message introuvable.")

        # Determine target user
        target_user_id = escalated_to_user_id
        if not target_user_id:
            settings = (
                db.query(AICMSettings)
                .filter(AICMSettings.workspace_id == workspace_id)
                .first()
            )
            if settings and settings.default_escalation_user_id:
                target_user_id = settings.default_escalation_user_id

        message.is_escalated = True
        message.escalated_to_user_id = target_user_id
        message.escalation_note = note
        message.escalated_at = datetime.now(UTC)

        db.commit()
        db.refresh(message)

        # Audit log
        audit = AICMAuditLog(
            workspace_id=workspace_id,
            inbox_message_id=message.id,
            user_id=actor_user_id,
            action="ESCALATE",
            details={
                "note": note,
                "escalated_to_user_id": target_user_id,
            },
        )
        db.add(audit)
        db.commit()

        # Notify escalated user if set
        if target_user_id:
            try:
                self.notification_service.create_notification(
                    db=db,
                    user_id=target_user_id,
                    type=NotificationType.INBOX_MESSAGE,
                    title="⚠️ Message escaladé requérant votre attention",
                    message=f"Interaction de {message.sender_name} escaladée : {note[:100]}",
                    severity=NotificationSeverity.WARNING,
                    link="/inbox",
                )
            except Exception as exc:
                logger.warning("Could not dispatch escalation notification: %s", exc)

        return message
