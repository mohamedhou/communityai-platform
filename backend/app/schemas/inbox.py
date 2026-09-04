from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.inbox_message import InboxMessageType, InboxSentiment
from app.schemas.ai import AITone


class SocialAccountSummary(BaseModel):
    id: int
    platform: str
    provider: str
    account_name: str
    account_username: str | None = None
    profile_image_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class InboxMessageResponse(BaseModel):
    id: int
    user_id: int
    social_account_id: int
    external_id: str
    type: InboxMessageType
    sender_name: str
    sender_external_id: str | None = None
    content: str
    sentiment: InboxSentiment
    sentiment_score: float | None = None
    is_read: bool
    is_resolved: bool
    replied_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    social_account: SocialAccountSummary | None = None

    model_config = ConfigDict(from_attributes=True)


class InboxListResponse(BaseModel):
    items: list[InboxMessageResponse]
    total: int
    unread_count: int


class InboxUnreadCountResponse(BaseModel):
    unread_count: int


class InboxMarkReadRequest(BaseModel):
    is_read: bool = True


class InboxMarkResolvedRequest(BaseModel):
    is_resolved: bool = True


class InboxReplyRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000, description="Reply text content")


class InboxSuggestReplyRequest(BaseModel):
    tone: AITone | None = None
    instructions: str | None = Field(default=None, max_length=1000)


class InboxMessageCreate(BaseModel):
    user_id: int
    social_account_id: int
    external_id: str
    type: InboxMessageType
    sender_name: str
    sender_external_id: str | None = None
    content: str
    sentiment: InboxSentiment = InboxSentiment.UNKNOWN
    sentiment_score: float | None = None
    is_read: bool = False
    is_resolved: bool = False
