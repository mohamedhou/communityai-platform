from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.models.post import PostApprovalStatus, PostStatus


class PostBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    media_url: str | None = Field(default=None, max_length=2048)
    media_asset_id: int | None = None
    social_account_id: int


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    content: str | None = Field(default=None, min_length=1, max_length=5000)
    media_url: str | None = Field(default=None, max_length=2048)
    media_asset_id: int | None = None
    social_account_id: int | None = None


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    social_account_id: int
    content: str
    media_url: str | None = None
    media_asset_id: int | None = None
    scheduled_at: datetime | None = None
    published_at: datetime | None = None
    status: PostStatus
    approval_status: PostApprovalStatus = PostApprovalStatus.NOT_REQUIRED
    reviewed_by: int | None = None
    reviewed_at: datetime | None = None
    rejection_reason: str | None = None
    submitted_for_review_at: datetime | None = None
    external_post_id: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class PostScheduleRequest(BaseModel):
    scheduled_at: datetime


class PostRejectRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=1000)
