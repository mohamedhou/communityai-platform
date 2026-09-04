from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
import urllib.parse

import httpx

from app.core.config import get_settings
from app.social.base import SocialProvider, SocialProfileInfo, SocialPublishingProvider, SocialInboxProvider
from app.social.exceptions import SocialProviderError


class LinkedInProvider(SocialProvider, SocialPublishingProvider, SocialInboxProvider):
    def get_authorization_url(self, state: str) -> str:
        settings = get_settings()
        if settings.social_mock_mode:
            # Under mock mode, redirect directly to the backend callback endpoint
            return f"http://localhost:8000/api/v1/social-accounts/linkedin/callback?code=mock-linkedin-code&state={state}"

        if not settings.linkedin_client_id or not settings.linkedin_redirect_uri:
            raise SocialProviderError("LinkedIn OAuth client_id or redirect_uri not configured")

        params = {
            "response_type": "code",
            "client_id": settings.linkedin_client_id,
            "redirect_uri": settings.linkedin_redirect_uri,
            "state": state,
            "scope": "r_liteprofile w_member_social",  # standard lite profile and post permission scopes
        }
        return "https://www.linkedin.com/oauth/v2/authorization?" + urllib.parse.urlencode(params)

    def exchange_code(self, code: str) -> dict[str, Any]:
        settings = get_settings()
        if settings.social_mock_mode:
            return {
                "access_token": "mock-linkedin-access-token",
                "refresh_token": "mock-linkedin-refresh-token",
                "expires_in": 5184000,  # 60 days
            }

        if not settings.linkedin_client_id or not settings.linkedin_client_secret or not settings.linkedin_redirect_uri:
            raise SocialProviderError("LinkedIn credentials not configured")

        url = "https://www.linkedin.com/oauth/v2/accessToken"
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.linkedin_redirect_uri,
            "client_id": settings.linkedin_client_id,
            "client_secret": settings.linkedin_client_secret,
        }

        try:
            with httpx.Client() as client:
                res = client.post(url, data=data)
                if res.status_code != 200:
                    raise SocialProviderError(f"LinkedIn token exchange failed: {res.text}")
                return res.json()
        except Exception as exc:
            if isinstance(exc, SocialProviderError):
                raise
            raise SocialProviderError(f"HTTP error during LinkedIn token exchange: {exc}") from exc

    def get_accounts_info(self, tokens: dict[str, Any]) -> list[SocialProfileInfo]:
        settings = get_settings()
        if settings.social_mock_mode:
            expires_at = None
            if "expires_in" in tokens:
                expires_at = datetime.now() + timedelta(seconds=tokens["expires_in"])

            return [
                SocialProfileInfo(
                    platform="linkedin",
                    external_account_id="mock-linkedin-member-789",
                    account_name="Mock LinkedIn Profile",
                    account_username="mock_linkedin_user",
                    profile_image_url="https://placehold.co/150",
                    access_token=tokens["access_token"],
                    refresh_token=tokens.get("refresh_token"),
                    expires_at=expires_at,
                    scopes="r_liteprofile w_member_social",
                )
            ]

        access_token = tokens.get("access_token")
        if not access_token:
            raise SocialProviderError("No access token provided to fetch LinkedIn profile")

        # In real mode, call LinkedIn Lite Profile API to get user info
        profile_url = "https://api.linkedin.com/v2/me"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            with httpx.Client() as client:
                res = client.get(profile_url, headers=headers)
                if res.status_code != 200:
                    raise SocialProviderError(f"Failed to fetch LinkedIn profile: {res.text}")
                
                profile_data = res.json()
                first_name = profile_data.get("localizedFirstName", "")
                last_name = profile_data.get("localizedLastName", "")
                full_name = f"{first_name} {last_name}".strip() or "LinkedIn Member"
                member_id = profile_data.get("id")

                # Fetch profile picture
                pic_url = "https://api.linkedin.com/v2/me?projection=(id,profilePicture(displayImage~:playableStreams))"
                pic_res = client.get(pic_url, headers=headers)
                profile_image_url = None
                if pic_res.status_code == 200:
                    try:
                        pic_data = pic_res.json()
                        elements = pic_data.get("profilePicture", {}).get("displayImage~", {}).get("elements", [])
                        if elements:
                            # Use the last size stream
                            profile_image_url = elements[-1].get("identifiers", [{}])[0].get("identifier")
                    except Exception:
                        pass

                expires_at = None
                if "expires_in" in tokens:
                    expires_at = datetime.now() + timedelta(seconds=tokens["expires_in"])

                return [
                    SocialProfileInfo(
                        platform="linkedin",
                        external_account_id=member_id,
                        account_name=full_name,
                        account_username=None,  # LinkedIn V2 doesn't return vanity name here
                        profile_image_url=profile_image_url,
                        access_token=access_token,
                        refresh_token=tokens.get("refresh_token"),
                        expires_at=expires_at,
                        scopes=tokens.get("scope", "r_liteprofile w_member_social"),
                    )
                ]
        except Exception as exc:
            if isinstance(exc, SocialProviderError):
                raise
            raise SocialProviderError(f"LinkedIn Profile API error: {exc}") from exc

    def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        settings = get_settings()
        if settings.social_mock_mode:
            return {
                "access_token": "mock-linkedin-refreshed-access-token",
                "refresh_token": "mock-linkedin-refreshed-refresh-token",
                "expires_in": 5184000,
            }

        if not settings.linkedin_client_id or not settings.linkedin_client_secret:
            raise SocialProviderError("LinkedIn credentials not configured")

        url = "https://www.linkedin.com/oauth/v2/accessToken"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": settings.linkedin_client_id,
            "client_secret": settings.linkedin_client_secret,
        }

        try:
            with httpx.Client() as client:
                res = client.post(url, data=data)
                if res.status_code != 200:
                    raise SocialProviderError(f"LinkedIn token refresh failed: {res.text}")
                return res.json()
        except Exception as exc:
            if isinstance(exc, SocialProviderError):
                raise
            raise SocialProviderError(f"HTTP error during LinkedIn token refresh: {exc}") from exc

    def revoke_access(self, access_token: str) -> None:
        settings = get_settings()
        if settings.social_mock_mode:
            return

        # LinkedIn revocation: POST https://www.linkedin.com/oauth/v2/revoke
        url = "https://www.linkedin.com/oauth/v2/revoke"
        data = {
            "client_id": settings.linkedin_client_id,
            "client_secret": settings.linkedin_client_secret,
            "token": access_token,
        }

        try:
            with httpx.Client() as client:
                client.post(url, data=data)
        except Exception as exc:
            raise SocialProviderError(f"Failed to revoke LinkedIn access: {exc}") from exc

    def publish_post(
        self,
        content: str,
        access_token: str,
        external_account_id: str,
        media_url: str | None = None
    ) -> str:
        settings = get_settings()
        if settings.social_mock_mode:
            return "mock-linkedin-post-id"

        url = "https://api.linkedin.com/v2/ugcPosts"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }

        # Build author URN
        author_urn = f"urn:li:person:{external_account_id}"

        # Build share content
        share_content = {
            "shareCommentary": {
                "text": content
            },
            "shareMediaCategory": "NONE"
        }

        if media_url:
            share_content["shareMediaCategory"] = "ARTICLE"
            share_content["media"] = [
                {
                    "status": "READY",
                    "originalUrl": media_url
                }
            ]

        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": share_content
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        try:
            with httpx.Client() as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code not in (200, 201):
                    raise SocialProviderError(f"LinkedIn publishing failed: {res.text}")
                data = res.json()
                return data.get("id") or "linkedin-post-id"
        except Exception as exc:
            if isinstance(exc, SocialProviderError):
                raise
            raise SocialProviderError(f"HTTP error during LinkedIn publishing: {exc}") from exc

    def send_reply(
        self,
        content: str,
        access_token: str,
        external_account_id: str,
        external_interaction_id: str,
        interaction_type: str = "COMMENT",
    ) -> str:
        settings = get_settings()
        if settings.social_mock_mode:
            return f"mock-linkedin-reply-{external_interaction_id}"

        # Real LinkedIn API call for replying
        url = f"https://api.linkedin.com/v2/socialActions/{external_interaction_id}/comments"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }

        if external_account_id.startswith("urn:li:"):
            author_urn = external_account_id
        elif external_account_id.isdigit():
            author_urn = f"urn:li:organization:{external_account_id}"
        else:
            author_urn = f"urn:li:person:{external_account_id}"

        payload = {
            "actor": author_urn,
            "message": {
                "text": content,
            },
        }

        try:
            with httpx.Client() as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code not in (200, 201):
                    raise SocialProviderError(f"LinkedIn reply failed: {res.text}")
                data = res.json()
                return data.get("id") or f"linkedin-reply-{external_interaction_id}"
        except Exception as exc:
            if isinstance(exc, SocialProviderError):
                raise
            raise SocialProviderError(f"HTTP error during LinkedIn reply: {exc}") from exc
