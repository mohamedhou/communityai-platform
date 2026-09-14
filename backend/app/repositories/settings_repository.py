from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user_settings import UserSettings


class SettingsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: int) -> UserSettings | None:
        stmt = select(UserSettings).where(UserSettings.user_id == user_id)
        return self.db.scalars(stmt).first()

    def create(self, user_id: int) -> UserSettings:
        settings = UserSettings(user_id=user_id)
        self.db.add(settings)
        self.db.flush()
        return settings

    def update(self, settings: UserSettings, values: dict[str, object]) -> UserSettings:
        for key, value in values.items():
            setattr(settings, key, value)
        self.db.add(settings)
        self.db.flush()
        return settings

    def get_or_create(self, user_id: int) -> UserSettings:
        settings = self.get_by_user_id(user_id)
        return settings if settings is not None else self.create(user_id)