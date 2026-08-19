from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def get_user_by_id(self, user_id: int) -> User:
        user = self.user_repo.get_by_id(user_id)
        if user is None:
            raise ValueError("user_not_found")
        return user

    def update_profile(self, user: User, first_name: str, last_name: str) -> User:
        user.first_name = first_name
        user.last_name = last_name
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def change_password(self, user: User, current_password: str, new_password: str) -> None:
        if not verify_password(current_password, user.password_hash):
            raise ValueError("invalid_current_password")

        user.password_hash = hash_password(new_password)
        self.db.add(user)
        self._revoke_all_refresh_tokens(user.id)
        self.db.commit()

    def list_users(self) -> list[User]:
        stmt = select(User).order_by(User.id)
        return list(self.db.execute(stmt).scalars().all())

    def update_user_profile_admin(self, user_id: int, first_name: str, last_name: str) -> User:
        user = self.get_user_by_id(user_id)
        user.first_name = first_name
        user.last_name = last_name
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user_status(self, user_id: int, is_active: bool, current_user_id: int) -> User:
        if user_id == current_user_id:
            raise ValueError("cannot_deactivate_self")

        user = self.get_user_by_id(user_id)
        user.is_active = is_active
        self.db.add(user)

        if not is_active:
            self._revoke_all_refresh_tokens(user_id)

        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user_role(self, user_id: int, role: UserRole, current_user_id: int) -> User:
        if user_id == current_user_id:
            raise ValueError("cannot_modify_own_role")

        user = self.get_user_by_id(user_id)
        user.role = role
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def _revoke_all_refresh_tokens(self, user_id: int) -> None:
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked.is_(False),
        )
        tokens = self.db.execute(stmt).scalars().all()
        for token in tokens:
            token.revoked = True
            token.revoked_at = datetime.now(UTC)
            self.db.add(token)
