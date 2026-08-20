from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.social.models import SocialAccountStatus


class SocialAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    platform: str
    provider: str
    account_name: str
    account_username: str | None = None
    profile_image_url: str | None = None
    status: SocialAccountStatus
    token_expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
