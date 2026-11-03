from __future__ import annotations

import logging
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.inbox_message import InboxMessage
from app.models.ai_community_manager import AIReplyDraft

logger = logging.getLogger(__name__)


class ConversationService:
    """
    Manages customer interaction threads and message history.
    """

    def get_conversation_history(
        self,
        db: Session,
        workspace_id: int,
        message_id: int,
        limit: int = 20,
    ) -> list[dict]:
        """
        Retrieves all past messages from the same sender or interaction thread
        in chronological order, with drafts and sent replies.
        """
        target_message = (
            db.query(InboxMessage)
            .filter(
                InboxMessage.id == message_id,
                InboxMessage.workspace_id == workspace_id,
            )
            .first()
        )
        if not target_message:
            return []

        # Find messages from same sender
        query = db.query(InboxMessage).filter(InboxMessage.workspace_id == workspace_id)
        if target_message.sender_external_id:
            query = query.filter(
                or_(
                    InboxMessage.sender_external_id == target_message.sender_external_id,
                    InboxMessage.sender_name == target_message.sender_name,
                )
            )
        else:
            query = query.filter(InboxMessage.sender_name == target_message.sender_name)

        messages = query.order_by(InboxMessage.created_at.asc()).limit(limit).all()

        history = []
        for msg in messages:
            # Customer message item
            history.append({
                "id": msg.id,
                "role": "customer",
                "sender_name": msg.sender_name,
                "content": msg.content,
                "type": msg.type.value,
                "created_at": msg.created_at.isoformat(),
                "sentiment": msg.sentiment.value if msg.sentiment else "UNKNOWN",
                "intent": msg.intent,
                "urgency": msg.urgency,
            })

            # Check if there are associated sent or approved AI replies
            drafts = (
                db.query(AIReplyDraft)
                .filter(AIReplyDraft.inbox_message_id == msg.id)
                .order_by(AIReplyDraft.created_at.asc())
                .all()
            )
            for d in drafts:
                if d.status in ("SENT", "APPROVED"):
                    history.append({
                        "id": f"draft-{d.id}",
                        "role": "assistant",
                        "sender_name": "Community Manager",
                        "content": d.reply_text,
                        "type": "REPLY",
                        "created_at": (d.sent_at or d.reviewed_at or d.created_at).isoformat(),
                        "status": d.status,
                    })

        return history
