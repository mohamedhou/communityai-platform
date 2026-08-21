from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.models.post import PostStatus


class PostBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    media_url: str | None = Field(default=None, max_length=2048)
    social_account_id: int


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    content: str | None = Field(default=None, min_length=1, max_length=5000)
    media_url: str | None = Field(default=None, max_length=2048)
    social_account_id: int | None = None


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    social_account_id: int
    content: str
    media_url: str | None = None
    scheduled_at: datetime | None = None
    published_at: datetime | None = None
    status: PostStatus
    external_post_id: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class PostScheduleRequest(BaseModel):
    scheduled_at: datetime
