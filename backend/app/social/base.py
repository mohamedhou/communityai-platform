from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class SocialProfileInfo:
    def __init__(
        self,
        platform: str,
        external_account_id: str,
        account_name: str,
        account_username: str | None = None,
        profile_image_url: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        expires_at: datetime | None = None,
        scopes: str | None = None,
    ):
        self.platform = platform
        self.external_account_id = external_account_id
        self.account_name = account_name
        self.account_username = account_username
        self.profile_image_url = profile_image_url
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_at = expires_at
        self.scopes = scopes


class SocialProvider(ABC):
    @abstractmethod
    def get_authorization_url(self, state: str) -> str:
        """Generate the OAuth authorization URL for the provider."""
        pass

    @abstractmethod
    def exchange_code(self, code: str) -> dict[str, Any]:
        """Exchange the authorization code for access and refresh tokens."""
        pass

    @abstractmethod
    def get_accounts_info(self, tokens: dict[str, Any]) -> list[SocialProfileInfo]:
        """Retrieve account profile info using the exchanged tokens."""
        pass

    @abstractmethod
    def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """Refresh the access token using a refresh token."""
        pass

    @abstractmethod
    def revoke_access(self, access_token: str) -> None:
        """Revoke the access token on the provider side."""
        pass


class SocialPublishingProvider(ABC):
    @abstractmethod
    def publish_post(
        self,
        content: str,
        access_token: str,
        external_account_id: str,
        media_url: str | None = None
    ) -> str:
        """Publish a post to the platform and return the external post ID."""
        pass


class SocialInboxProvider(ABC):
    @abstractmethod
    def send_reply(
        self,
        content: str,
        access_token: str,
        external_account_id: str,
        external_interaction_id: str,
        interaction_type: str = "COMMENT",
    ) -> str:
        """Send a reply to an interaction on the social platform and return the external reply ID."""
        pass
