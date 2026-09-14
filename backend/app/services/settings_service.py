from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.models.user_settings import UserSettings
from app.repositories.settings_repository import SettingsRepository
from app.schemas.settings import ChangePasswordRequest, UserSettingsResponse, UserSettingsUpdate
from app.social.models import SocialAccount


class SettingsService:
    def __init__(self, db: Session, repository: SettingsRepository | None = None):
        self.db = db
        self.repository = repository or SettingsRepository(db)

    def get_settings(self, user: User) -> UserSettingsResponse:
        settings = self.repository.get_or_create(user.id)
        self.db.commit()
        self.db.refresh(settings)
        return self._response(user, settings)

    def update_settings(self, user: User, payload: UserSettingsUpdate) -> UserSettingsResponse:
        settings = self.repository.get_or_create(user.id)
        values = payload.model_dump(exclude_unset=True)
        profile_values = {key: values.pop(key) for key in ("first_name", "last_name") if key in values}
        for key, value in profile_values.items():
            setattr(user, key, value)
        self.db.add(user)
        self.repository.update(settings, values)
        self.db.commit()
        self.db.refresh(user)
        self.db.refresh(settings)
        return self._response(user, settings)

    def change_password(self, user: User, payload: ChangePasswordRequest) -> None:
        if not verify_password(payload.current_password, user.password_hash):
            raise ValueError("invalid_current_password")
        user.password_hash = hash_password(payload.new_password)
        self.db.add(user)
        tokens = self.db.scalars(
            select(RefreshToken).where(RefreshToken.user_id == user.id, RefreshToken.revoked.is_(False))
        ).all()
        now = datetime.now(UTC)
        for token in tokens:
            token.revoked = True
            token.revoked_at = now
            self.db.add(token)
        self.db.commit()

    def _response(self, user: User, settings: UserSettings) -> UserSettingsResponse:
        connected_count = self.db.scalar(
            select(func.count()).select_from(SocialAccount).where(SocialAccount.user_id == user.id)
        ) or 0
        return UserSettingsResponse(
            id=settings.id,
            user_id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            workspace_name=settings.workspace_name,
            workspace_description=settings.workspace_description,
            timezone=settings.timezone,
            language=settings.language,
            default_platform=settings.default_platform,
            notifications_enabled=settings.notifications_enabled,
            post_notifications_enabled=settings.post_notifications_enabled,
            inbox_notifications_enabled=settings.inbox_notifications_enabled,
            social_notifications_enabled=settings.social_notifications_enabled,
            analytics_notifications_enabled=settings.analytics_notifications_enabled,
            connected_account_count=connected_count,
            created_at=settings.created_at,
            updated_at=settings.updated_at,
        )