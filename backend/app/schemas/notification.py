from __future__ import annotations

from datetime import datetime
import re
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.notification import NotificationSeverity, NotificationType


def validate_internal_action_url(v: str | None) -> str | None:
    if v is None:
        return None
    cleaned = v.strip()
    if not cleaned:
        return None
    # Must start with a single '/' and not '//' (protocol-relative URL)
    # and must not contain any schema/protocol like http:, https:, javascript:, data:
    if not cleaned.startswith("/") or cleaned.startswith("//") or "://" in cleaned or re.match(r"^[a-zA-Z0-9+-.]+:", cleaned):
        raise ValueError("action_url must be a relative internal URL starting with '/' (e.g. /posts, /inbox)")
    return cleaned


class NotificationBase(BaseModel):
    type: NotificationType
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    severity: NotificationSeverity = NotificationSeverity.INFO
    action_url: str | None = Field(default=None, max_length=255)
    entity_type: str | None = Field(default=None, max_length=100)
    entity_id: str | None = Field(default=None, max_length=100)

    @field_validator("action_url")
    @classmethod
    def check_action_url(cls, v: str | None) -> str | None:
        return validate_internal_action_url(v)


class NotificationCreate(NotificationBase):
    user_id: int


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: NotificationType
    title: str
    message: str
    severity: NotificationSeverity
    is_read: bool
    action_url: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    created_at: datetime
    read_at: datetime | None = None


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    unread_count: int
    page: int
    limit: int


class NotificationUnreadCountResponse(BaseModel):
    unread_count: int


class NotificationMarkReadRequest(BaseModel):
    is_read: bool = True
