from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class AICMMode(StrEnum):
    MANUAL = "MANUAL"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    AUTOMATIC = "AUTOMATIC"


class AIReplyDraftStatus(StrEnum):
    SUGGESTED = "SUGGESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SENT = "SENT"
    FAILED = "FAILED"


class AICMSettings(Base):
    """
    Configuration and automation rules for AI Community Manager per workspace.
    """
    __tablename__ = "ai_cm_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    mode: Mapped[AICMMode] = mapped_column(
        Enum(AICMMode, name="aicm_mode"),
        default=AICMMode.APPROVAL_REQUIRED,
        nullable=False,
    )

    enabled_platforms: Mapped[list[str]] = mapped_column(
        JSON,
        default=lambda: ["facebook", "instagram", "linkedin"],
        nullable=False,
    )

    allowed_languages: Mapped[list[str]] = mapped_column(
        JSON,
        default=lambda: ["fr", "en"],
        nullable=False,
    )

    min_confidence_score: Mapped[float] = mapped_column(Float, default=0.85, nullable=False)

    # Intents authorized for automatic replies (only effective when mode == AUTOMATIC)
    auto_reply_intents: Mapped[list[str]] = mapped_column(
        JSON,
        default=lambda: ["compliment", "question", "support_request"],
        nullable=False,
    )

    # Strictly forbidden intents for automatic dispatch (safety blocklist)
    blocked_intents: Mapped[list[str]] = mapped_column(
        JSON,
        default=lambda: ["complaint", "refund", "threat", "legal", "payment_issue", "spam"],
        nullable=False,
    )

    # Schedule restrictions
    working_hours_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    working_hours_schedule: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Escalation default lead
    default_escalation_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Optional model customization
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    temperature: Mapped[float] = mapped_column(Float, default=0.3, nullable=False)

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

    workspace = relationship("Workspace")
    default_escalation_user = relationship("User")


class AIReplyDraft(Base):
    """
    Proposed AI replies, approval workflow, and send delivery state.
    """
    __tablename__ = "ai_reply_drafts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    inbox_message_id: Mapped[int] = mapped_column(
        ForeignKey("inbox_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    reply_text: Mapped[str] = mapped_column(Text, nullable=False)
    original_reply_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.9, nullable=False)
    sources_used: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    status: Mapped[AIReplyDraftStatus] = mapped_column(
        Enum(AIReplyDraftStatus, name="ai_reply_draft_status"),
        default=AIReplyDraftStatus.SUGGESTED,
        nullable=False,
    )

    requires_human: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    escalation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_ai: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    reviewed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    external_reply_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)

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

    workspace = relationship("Workspace")
    inbox_message = relationship("InboxMessage")
    reviewed_by_user = relationship("User")


class AICMAuditLog(Base):
    """
    Audit log of AI analysis, reviews, sends, escalations, and automated decisions.
    """
    __tablename__ = "ai_cm_audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    inbox_message_id: Mapped[int | None] = mapped_column(
        ForeignKey("inbox_messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    action: Mapped[str] = mapped_column(String(100), nullable=False)  # ANALYZE, DRAFT, APPROVE, REJECT, SEND, AUTO_SEND, BLOCKED_AUTO_SEND, ESCALATE, ASSIGN
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    workspace = relationship("Workspace")
    inbox_message = relationship("InboxMessage")
    user = relationship("User")
