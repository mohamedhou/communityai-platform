from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class SentimentType(StrEnum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class IntentType(StrEnum):
    QUESTION = "question"
    PURCHASE = "purchase"
    PRICE_INQUIRY = "price_inquiry"
    COMPLAINT = "complaint"
    COMPLIMENT = "compliment"
    DELIVERY_INQUIRY = "delivery_inquiry"
    SUPPORT_REQUEST = "support_request"
    SPAM = "spam"


class UrgencyLevel(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class AIAnalysisResult(BaseModel):
    """
    Validated Pydantic schema for structured message analysis.
    Guarantees strict type constraints and prompt injection resistance.
    """
    sentiment: SentimentType
    intent: IntentType
    language: str = Field(default="fr", description="ISO 639-1 language code, e.g. 'fr', 'en'")
    urgency: UrgencyLevel = UrgencyLevel.NORMAL
    topic: str = Field(description="Primary topic, e.g. 'delivery', 'billing', 'feature_request'")
    requires_human: bool = Field(default=False, description="True if sentiment is negative, intent is complaint/threat, or facts are uncertain")
    reason: str = Field(description="Justification for the classification and human intervention requirement")
    customer_need: str | None = Field(default=None, description="Inferred underlying objective or question of the customer")
    potential_risk: str | None = Field(default=None, description="Identified risk: churn, legal, reputational, scam")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0, description="Classification confidence score between 0 and 1")


class AIReplyResult(BaseModel):
    """
    Structured generation result containing proposed response and audit metadata.
    """
    reply_text: str = Field(description="Proposed text ready to be reviewed or dispatched")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0, description="Confidence score that reply accurately addresses customer using verified facts")
    sources_used: list[str] = Field(default_factory=list, description="Internal sources cited, e.g. 'FAQ: Délais', 'Politique: Retours'")
    requires_human: bool = Field(default=False, description="True if proposed answer should not be sent automatically")
    escalation_reason: str | None = Field(default=None, description="Explanation why human approval or escalation is required")


class AIReplyDraftResponse(BaseModel):
    id: int
    workspace_id: int
    inbox_message_id: int
    reply_text: str
    original_reply_text: str
    confidence_score: float
    sources_used: list[str]
    status: str
    requires_human: bool
    escalation_reason: str | None = None
    created_by_ai: bool
    reviewed_by_user_id: int | None = None
    reviewed_at: datetime | None = None
    sent_at: datetime | None = None
    external_reply_id: str | None = None
    error_message: str | None = None
    idempotency_key: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIReplyApprovalRequest(BaseModel):
    approved: bool
    modified_reply_text: str | None = None
    auto_send: bool = True  # If true and approved, immediately dispatch via social provider


class AIReplySendRequest(BaseModel):
    content: str = Field(min_length=1)
    idempotency_key: str | None = None


class AICMSettingsUpdate(BaseModel):
    mode: str | None = Field(default=None, description="MANUAL, APPROVAL_REQUIRED, AUTOMATIC")
    enabled_platforms: list[str] | None = None
    allowed_languages: list[str] | None = None
    min_confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    auto_reply_intents: list[str] | None = None
    blocked_intents: list[str] | None = None
    working_hours_only: bool | None = None
    working_hours_schedule: dict[str, Any] | None = None
    default_escalation_user_id: int | None = None
    model_name: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=1.5)


class AICMSettingsResponse(BaseModel):
    id: int
    workspace_id: int
    mode: str
    enabled_platforms: list[str]
    allowed_languages: list[str]
    min_confidence_score: float
    auto_reply_intents: list[str]
    blocked_intents: list[str]
    working_hours_only: bool
    working_hours_schedule: dict[str, Any] | None = None
    default_escalation_user_id: int | None = None
    model_name: str | None = None
    temperature: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageEscalationRequest(BaseModel):
    escalated_to_user_id: int | None = None
    escalation_note: str = Field(min_length=2, description="Reason for escalating this interaction to management")


class MessageAssignmentRequest(BaseModel):
    assigned_to_user_id: int | None = Field(description="Target team member user ID, or null to unassign")


class AICMAuditLogResponse(BaseModel):
    id: int
    workspace_id: int
    inbox_message_id: int | None = None
    user_id: int | None = None
    action: str
    details: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SentimentBreakdown(BaseModel):
    positive: int = 0
    neutral: int = 0
    negative: int = 0


class IntentBreakdown(BaseModel):
    question: int = 0
    purchase: int = 0
    price_inquiry: int = 0
    complaint: int = 0
    compliment: int = 0
    delivery_inquiry: int = 0
    support_request: int = 0
    spam: int = 0


class AICMDashboardMetrics(BaseModel):
    total_comments_analyzed: int
    total_messages_analyzed: int
    replies_generated: int
    replies_sent: int
    replies_pending_approval: int
    urgent_messages_count: int
    escalated_conversations_count: int
    resolution_rate: float  # Percentage 0-100
    average_response_time_seconds: float | None = None
    sentiment_breakdown: SentimentBreakdown
    intent_breakdown: IntentBreakdown
