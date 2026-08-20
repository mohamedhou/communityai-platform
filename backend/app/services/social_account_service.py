from __future__ import annotations

from datetime import UTC, datetime, timedelta
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.encryption import encrypt_token, decrypt_token
from app.social.base import SocialProvider
from app.social.exceptions import OAuthStateExpiredOrInvalid, SocialProviderError
from app.social.models import SocialAccount, SocialAccountStatus, OAuthState
from app.social.providers.linkedin import LinkedInProvider
from app.social.providers.meta import MetaProvider


class SocialAccountService:
    def __init__(self, db: Session):
        self.db = db

    def get_provider(self, platform_or_provider: str) -> SocialProvider:
        norm = platform_or_provider.lower().strip()
        if norm in ("meta", "facebook", "instagram"):
            return MetaProvider()
        elif norm == "linkedin":
            return LinkedInProvider()
        else:
            raise ValueError(f"Unknown social platform: {platform_or_provider}")

    def create_authorization_url(self, user_id: int, platform: str) -> str:
        # 1. Generate secure, cryptographically random state parameter
        state_str = str(uuid.uuid4())

        # 2. Save it in database with user_id and expiration (10 minutes)
        oauth_state = OAuthState(
            state=state_str,
            user_id=user_id,
            expires_at=datetime.now(UTC) + timedelta(minutes=10),
        )
        self.db.add(oauth_state)
        self.db.commit()

        # 3. Ask provider for the OAuth url containing this state
        provider = self.get_provider(platform)
        return provider.get_authorization_url(state_str)

    def process_callback(self, platform: str, code: str, state: str) -> list[SocialAccount]:
        # 1. Validate and consume the state parameter (protect against CSRF)
        user_id = self.validate_and_consume_state(state)

        # 2. Get provider
        provider = self.get_provider(platform)

        # 3. Exchange OAuth code for tokens
        tokens = provider.exchange_code(code)

        # 4. Get connected accounts info from the provider
        accounts_info = provider.get_accounts_info(tokens)
        if not accounts_info:
            raise SocialProviderError("No accounts returned from provider")

        connected_accounts = []
        for info in accounts_info:
            # 5. Encrypt tokens at rest
            encrypted_access = encrypt_token(info.access_token)
            encrypted_refresh = encrypt_token(info.refresh_token)

            # 6. Check if account already connected for this user and platform
            stmt = select(SocialAccount).where(
                SocialAccount.user_id == user_id,
                SocialAccount.platform == info.platform,
                SocialAccount.external_account_id == info.external_account_id,
            )
            existing_account = self.db.execute(stmt).scalar_one_or_none()

            # We use provider name derived from the platform choice
            provider_name = "meta" if info.platform in ("facebook", "instagram") else "linkedin"

            if existing_account:
                existing_account.account_name = info.account_name
                existing_account.account_username = info.account_username
                existing_account.profile_image_url = info.profile_image_url
                existing_account.access_token_encrypted = encrypted_access
                existing_account.refresh_token_encrypted = encrypted_refresh
                existing_account.token_expires_at = info.expires_at
                existing_account.scopes = info.scopes
                existing_account.status = SocialAccountStatus.CONNECTED
                self.db.add(existing_account)
                connected_accounts.append(existing_account)
            else:
                new_account = SocialAccount(
                    user_id=user_id,
                    platform=info.platform,
                    provider=provider_name,
                    external_account_id=info.external_account_id,
                    account_name=info.account_name,
                    account_username=info.account_username,
                    profile_image_url=info.profile_image_url,
                    access_token_encrypted=encrypted_access,
                    refresh_token_encrypted=encrypted_refresh,
                    token_expires_at=info.expires_at,
                    scopes=info.scopes,
                    status=SocialAccountStatus.CONNECTED,
                )
                self.db.add(new_account)
                connected_accounts.append(new_account)

        self.db.commit()
        for acc in connected_accounts:
            self.db.refresh(acc)
        return connected_accounts

    def list_accounts(self, user_id: int) -> list[SocialAccount]:
        stmt = select(SocialAccount).where(SocialAccount.user_id == user_id).order_by(SocialAccount.id)
        return list(self.db.execute(stmt).scalars().all())

    def get_account_by_id(self, account_id: int) -> SocialAccount:
        stmt = select(SocialAccount).where(SocialAccount.id == account_id)
        account = self.db.execute(stmt).scalar_one_or_none()
        if not account:
            raise ValueError("account_not_found")
        return account

    def disconnect_account(self, user_id: int, account_id: int) -> None:
        account = self.get_account_by_id(account_id)
        if account.user_id != user_id:
            raise PermissionError("not_authorized")

        # Try to revoke credentials on the provider side
        try:
            provider = self.get_provider(account.provider)
            decrypted_access_token = decrypt_token(account.access_token_encrypted)
            if decrypted_access_token:
                provider.revoke_access(decrypted_access_token)
        except Exception:
            # Proceed with DB deletion even if provider revocation fails
            pass

        self.db.delete(account)
        self.db.commit()

    def refresh_account_token(self, user_id: int, account_id: int) -> SocialAccount:
        account = self.get_account_by_id(account_id)
        if account.user_id != user_id:
            raise PermissionError("not_authorized")

        decrypted_refresh = decrypt_token(account.refresh_token_encrypted)
        if not decrypted_refresh:
            raise SocialProviderError("No refresh token available for this account")

        provider = self.get_provider(account.provider)
        # Exchange refresh token for new access and optional refresh tokens
        new_tokens = provider.refresh_token(decrypted_refresh)

        # Update in database
        account.access_token_encrypted = encrypt_token(new_tokens.get("access_token"))
        if "refresh_token" in new_tokens:
            account.refresh_token_encrypted = encrypt_token(new_tokens["refresh_token"])

        if "expires_in" in new_tokens:
            account.token_expires_at = datetime.now(UTC) + timedelta(seconds=new_tokens["expires_in"])
        else:
            # default 60 days if expires_in is not returned on refresh but expires
            account.token_expires_at = datetime.now(UTC) + timedelta(days=60)

        account.status = SocialAccountStatus.CONNECTED
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def validate_and_consume_state(self, state_str: str) -> int:
        stmt = select(OAuthState).where(OAuthState.state == state_str)
        oauth_state = self.db.execute(stmt).scalar_one_or_none()
        if not oauth_state:
            raise OAuthStateExpiredOrInvalid("OAuth state not found or invalid")

        expires_at = oauth_state.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)

        if expires_at < datetime.now(UTC):
            self.db.delete(oauth_state)
            self.db.commit()
            raise OAuthStateExpiredOrInvalid("OAuth state expired")

        user_id = oauth_state.user_id
        # Single-use: consume (delete) immediately
        self.db.delete(oauth_state)
        self.db.commit()
        return user_id
