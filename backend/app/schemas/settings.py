from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models.user import UserRole


SUPPORTED_LANGUAGES = {"en", "fr"}
SUPPORTED_PLATFORMS = {"facebook", "instagram", "linkedin", "meta"}


def validate_timezone(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("timezone must not be empty")
    try:
        ZoneInfo(cleaned)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("timezone is not supported") from exc
    return cleaned


class UserSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole
    workspace_name: str
    workspace_description: str | None
    timezone: str
    language: str
    default_platform: str | None
    notifications_enabled: bool
    post_notifications_enabled: bool
    inbox_notifications_enabled: bool
    social_notifications_enabled: bool
    analytics_notifications_enabled: bool
    connected_account_count: int
    created_at: datetime
    updated_at: datetime


class UserSettingsUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    workspace_name: str | None = Field(default=None, min_length=1, max_length=150)
    workspace_description: str | None = Field(default=None, max_length=500)
    timezone: str | None = None
    language: str | None = None
    default_platform: str | None = None
    notifications_enabled: bool | None = None
    post_notifications_enabled: bool | None = None
    inbox_notifications_enabled: bool | None = None
    social_notifications_enabled: bool | None = None
    analytics_notifications_enabled: bool | None = None

    @field_validator("timezone")
    @classmethod
    def check_timezone(cls, value: str | None) -> str | None:
        return validate_timezone(value) if value is not None else None

    @field_validator("language")
    @classmethod
    def check_language(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        if cleaned not in SUPPORTED_LANGUAGES:
            raise ValueError("language must be one of: en, fr")
        return cleaned

    @field_validator("default_platform")
    @classmethod
    def check_platform(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        if cleaned not in SUPPORTED_PLATFORMS:
            raise ValueError("default_platform is not supported")
        return cleaned


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def passwords_match(self) -> "ChangePasswordRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("new passwords do not match")
        return self


class ChangePasswordResponse(BaseModel):
    message: str