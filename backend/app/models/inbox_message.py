from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class InboxMessageType(StrEnum):
    COMMENT = "COMMENT"
    MESSAGE = "MESSAGE"
    MENTION = "MENTION"


class InboxSentiment(StrEnum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"
    UNKNOWN = "UNKNOWN"


class InboxMessage(Base):
    __tablename__ = "inbox_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    social_account_id: Mapped[int] = mapped_column(
        ForeignKey("social_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[InboxMessageType] = mapped_column(
        Enum(InboxMessageType, name="inbox_message_type", create_type=False),
        nullable=False,
    )
    sender_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sender_external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment: Mapped[InboxSentiment] = mapped_column(
        Enum(InboxSentiment, name="inbox_sentiment", create_type=False),
        default=InboxSentiment.UNKNOWN,
        nullable=False,
    )
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # AI Community Manager fields
    intent: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    urgency: Mapped[str | None] = mapped_column(String(50), nullable=True, default="normal", index=True)
    topic: Mapped[str | None] = mapped_column(String(150), nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    ai_analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Team assignment and escalation
    assigned_to_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_escalated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    escalated_to_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    escalation_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    workspace = relationship("Workspace")
    user = relationship("User", foreign_keys=[user_id])
    social_account = relationship("SocialAccount")
    assigned_to_user = relationship("User", foreign_keys=[assigned_to_user_id])
    escalated_to_user = relationship("User", foreign_keys=[escalated_to_user_id])
