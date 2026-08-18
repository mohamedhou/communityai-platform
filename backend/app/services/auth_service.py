from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.user import User, UserRole
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)

    def register_user(self, payload: UserCreate) -> User:
        normalized_email = payload.email.strip().lower()
        existing_user = self.users.get_by_email(normalized_email)
        if existing_user is not None:
            raise ValueError("email_already_used")

        return self.users.create_user(
            email=normalized_email,
            password_hash=hash_password(payload.password),
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            role=UserRole.COMMUNITY_MANAGER,
        )

    def authenticate_user(self, *, email: str, password: str) -> User | None:
        normalized_email = email.strip().lower()
        user = self.users.get_by_email(normalized_email)
        if user is None:
            return None
        if not verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        return user

    def issue_tokens(self, user: User) -> tuple[str, str]:
        access_token = create_access_token(user.id, user.role)
        refresh_token, expires_at = create_refresh_token(user.id)
        self.refresh_tokens.create(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=expires_at,
        )
        return access_token, refresh_token

    def refresh_access_token(self, refresh_token: str) -> tuple[str, User]:
        payload = decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise ValueError("invalid_token_type")

        subject = payload.get("sub")
        if subject is None or not str(subject).isdigit():
            raise ValueError("invalid_subject")

        user_id = int(subject)
        user = self.users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise ValueError("invalid_user")

        token_record = self.refresh_tokens.get_valid_by_hash(hash_token(refresh_token))
        if token_record is None:
            raise ValueError("invalid_refresh_token")

        access_token = create_access_token(user.id, user.role)
        return access_token, user

    def revoke_refresh_token(self, refresh_token: str) -> None:
        try:
            payload = decode_token(refresh_token)
        except ValueError:
            return

        if payload.get("type") != "refresh":
            return

        token_record = self.refresh_tokens.get_valid_by_hash(hash_token(refresh_token))
        if token_record is None:
            return
        self.refresh_tokens.revoke(token_record)

    def validate_access_token(self, token: str) -> User:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise ValueError("invalid_token_type")

        subject = payload.get("sub")
        if subject is None or not str(subject).isdigit():
            raise ValueError("invalid_subject")

        user = self.users.get_by_id(int(subject))
        if user is None:
            raise ValueError("user_not_found")
        if not user.is_active:
            raise ValueError("inactive_user")

        return user

    @staticmethod
    def is_refresh_payload_expired(payload: dict[str, object]) -> bool:
        exp = payload.get("exp")
        if not isinstance(exp, (int, float)):
            return True
        return datetime.fromtimestamp(exp, tz=UTC) <= datetime.now(UTC)
