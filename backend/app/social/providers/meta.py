from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
import urllib.parse

import httpx

from app.core.config import get_settings
from app.social.base import SocialProvider, SocialProfileInfo, SocialPublishingProvider, SocialInboxProvider, SocialAnalyticsProvider
from app.social.exceptions import SocialProviderError


class MetaProvider(SocialProvider, SocialPublishingProvider, SocialInboxProvider, SocialAnalyticsProvider):
    def get_authorization_url(self, state: str) -> str:
        settings = get_settings()
        if settings.social_mock_mode:
            # Under mock mode, redirect directly to the backend callback endpoint
            return f"http://localhost:8000/api/v1/social-accounts/meta/callback?code=mock-meta-code&state={state}"

        if not settings.meta_client_id or not settings.meta_client_secret or not settings.meta_redirect_uri:
            raise SocialProviderError("Meta OAuth is not configured")

        params = {
            "client_id": settings.meta_client_id,
            "redirect_uri": settings.meta_redirect_uri,
            "state": state,
            "scope": "pages_show_list,pages_read_engagement,instagram_basic,instagram_manage_insights",
            "response_type": "code",
        }
        return f"https://www.facebook.com/{settings.meta_graph_api_version}/dialog/oauth?" + urllib.parse.urlencode(params)

    def exchange_code(self, code: str) -> dict[str, Any]:
        settings = get_settings()
        if settings.social_mock_mode:
            return {
                "access_token": "mock-meta-access-token",
                "expires_in": 5184000,  # 60 days
            }

        if not settings.meta_client_id or not settings.meta_client_secret or not settings.meta_redirect_uri:
            raise SocialProviderError("Meta OAuth is not configured")

        url = f"https://graph.facebook.com/{settings.meta_graph_api_version}/oauth/access_token"
        params = {
            "client_id": settings.meta_client_id,
            "client_secret": settings.meta_client_secret,
            "redirect_uri": settings.meta_redirect_uri,
            "code": code,
        }

        try:
            with httpx.Client() as client:
                res = client.get(url, params=params)
                if res.status_code != 200:
                    raise SocialProviderError("Meta token exchange failed")
                return res.json()
        except Exception as exc:
            if isinstance(exc, SocialProviderError):
                raise
            raise SocialProviderError(f"HTTP error during Meta token exchange: {exc}") from exc

    def get_accounts_info(self, tokens: dict[str, Any]) -> list[SocialProfileInfo]:
        settings = get_settings()
        if settings.social_mock_mode:
            # Mock mode returns a mock FB page and a linked IG professional account
            expires_at = None
            if "expires_in" in tokens:
                expires_at = datetime.now() + timedelta(seconds=tokens["expires_in"])

            return [
                SocialProfileInfo(
                    platform="facebook",
                    external_account_id="mock-fb-page-123",
                    account_name="Mock Facebook Page",
                    account_username="mock_fb_page",
                    profile_image_url="https://placehold.co/150",
                    access_token=tokens["access_token"],
                    expires_at=expires_at,
                    scopes="pages_show_list,pages_read_engagement",
                ),
                SocialProfileInfo(
                    platform="instagram",
                    external_account_id="mock-ig-professional-456",
                    account_name="Mock Instagram Professional",
                    account_username="mock_ig_professional",
                    profile_image_url="https://placehold.co/150",
                    access_token=tokens["access_token"],
                    expires_at=expires_at,
                    scopes="instagram_basic,instagram_manage_insights",
                ),
            ]

        access_token = tokens.get("access_token")
        if not access_token:
            raise SocialProviderError("No access token provided to fetch accounts")

        # In real mode, query the Facebook Graph API to list Pages and find Instagram accounts linked
        # Step 1: GET /me/accounts to list Facebook pages
        graph_base = f"https://graph.facebook.com/{settings.meta_graph_api_version}"
        pages_url = f"{graph_base}/me/accounts"
        headers = {"Authorization": f"Bearer {access_token}"}
        profiles = []

        try:
            with httpx.Client() as client:
                # 1. Fetch FB pages
                res = client.get(pages_url, headers=headers)
                if res.status_code != 200:
                    raise SocialProviderError("Failed to fetch Facebook pages")
                
                pages_data = res.json().get("data", [])
                for page in pages_data:
                    page_id = page.get("id")
                    page_name = page.get("name")
                    page_token = page.get("access_token")
                    
                    # Fetch Facebook Page profile image
                    pic_url = f"{graph_base}/{page_id}/picture"
                    pic_params = {"redirect": "false", "type": "large"}
                    pic_res = client.get(pic_url, headers=headers, params=pic_params)
                    profile_image_url = None
                    if pic_res.status_code == 200:
                        profile_image_url = pic_res.json().get("data", {}).get("url")

                    # Create Facebook page profile
                    profiles.append(
                        SocialProfileInfo(
                            platform="facebook",
                            external_account_id=page_id,
                            account_name=page_name,
                            account_username=page.get("username"),
                            profile_image_url=profile_image_url,
                            access_token=page_token or access_token,
                            scopes="pages_show_list,pages_read_engagement",
                        )
                    )

                    # Step 2: Query linked Instagram Business account
                    ig_url = f"{graph_base}/{page_id}"
                    ig_params = {"fields": "instagram_business_account"}
                    ig_res = client.get(ig_url, headers=headers, params=ig_params)
                    if ig_res.status_code == 200:
                        ig_account = ig_res.json().get("instagram_business_account")
                        if ig_account:
                            ig_id = ig_account.get("id")
                            # Fetch Instagram Account details
                            ig_info_url = f"{graph_base}/{ig_id}"
                            ig_info_params = {"fields": "name,username,profile_picture_url"}
                            ig_info_res = client.get(ig_info_url, headers=headers, params=ig_info_params)
                            if ig_info_res.status_code == 200:
                                ig_info = ig_info_res.json()
                                profiles.append(
                                    SocialProfileInfo(
                                        platform="instagram",
                                        external_account_id=ig_id,
                                        account_name=ig_info.get("name", "Instagram Business"),
                                        account_username=ig_info.get("username"),
                                        profile_image_url=ig_info.get("profile_picture_url"),
                                        access_token=page_token or access_token,
                                        scopes="instagram_basic,instagram_manage_insights",
                                    )
                                )
            return profiles
        except Exception as exc:
            if isinstance(exc, SocialProviderError):
                raise
            raise SocialProviderError(f"Meta Graph API error: {exc}") from exc

    def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        # Meta Page access tokens are typically long-lived and don't use standard refresh tokens.
        # We can simulate/raise NotImplementedError or return the token as is.
        return {"access_token": refresh_token}

    def revoke_access(self, access_token: str) -> None:
        settings = get_settings()
        if settings.social_mock_mode:
            return

        # Meta revocation: DELETE /me/permissions
        url = f"https://graph.facebook.com/{settings.meta_graph_api_version}/me/permissions"
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            with httpx.Client() as client:
                client.delete(url, headers=headers)
        except Exception as exc:
            raise SocialProviderError(f"Failed to revoke Meta access: {exc}") from exc

    def publish_post(
        self,
        content: str,
        access_token: str,
        external_account_id: str,
        media_url: str | None = None
    ) -> str:
        settings = get_settings()
        if settings.social_mock_mode:
            return "mock-meta-post-id"

        url = f"https://graph.facebook.com/{settings.meta_graph_api_version}/{external_account_id}/feed"
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {"message": content}
        if media_url:
            payload["link"] = media_url

        try:
            with httpx.Client() as client:
                res = client.post(url, headers=headers, data=payload)
                if res.status_code not in (200, 201):
                    raise SocialProviderError("Meta publishing failed")
                data = res.json()
                return data.get("id") or "meta-post-id"
        except Exception as exc:
            if isinstance(exc, SocialProviderError):
                raise
            raise SocialProviderError(f"HTTP error during Meta publishing: {exc}") from exc

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
            return f"mock-meta-reply-{external_interaction_id}"

        # Real Meta Graph API call
        url = f"https://graph.facebook.com/{settings.meta_graph_api_version}/{external_interaction_id}/comments"
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {"message": content}

        try:
            with httpx.Client() as client:
                res = client.post(url, headers=headers, data=payload)
                if res.status_code not in (200, 201):
                    raise SocialProviderError("Meta reply failed")
                data = res.json()
                return data.get("id") or f"meta-reply-{external_interaction_id}"
        except Exception as exc:
            if isinstance(exc, SocialProviderError):
                raise
            raise SocialProviderError(f"HTTP error during Meta reply: {exc}") from exc

    def get_account_metrics(
        self,
        access_token: str,
        external_account_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        settings = get_settings()
        if settings.social_mock_mode:
            return {
                "followers": 12450,
                "follower_growth": 340,
                "impressions": 48200,
                "reach": 35600,
                "engagement": 2980,
                "likes": 2100,
                "comments": 530,
                "shares": 220,
                "clicks": 130,
                "posts_published": 14,
            }
        # Future live Meta Graph API insights
        return {"followers": 0, "impressions": 0, "reach": 0, "engagement": 0}

    def get_post_metrics(
        self,
        access_token: str,
        external_account_id: str,
        external_post_id: str,
    ) -> dict[str, Any]:
        settings = get_settings()
        if settings.social_mock_mode:
            return {
                "likes": 145,
                "comments": 32,
                "shares": 18,
                "clicks": 45,
                "impressions": 3200,
                "reach": 2800,
                "engagement": 240,
            }
        return {"likes": 0, "comments": 0, "shares": 0, "clicks": 0, "impressions": 0, "reach": 0, "engagement": 0}

    def get_time_series(
        self,
        access_token: str,
        external_account_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict[str, Any]]:
        settings = get_settings()
        if settings.social_mock_mode:
            points = []
            cur = start_date
            base_followers = 12000
            day_idx = 0
            while cur <= end_date:
                daily_growth = 10 + (day_idx % 7) * 4
                base_followers += daily_growth
                reach = 1200 + (day_idx % 5) * 200 + (day_idx * 15)
                impressions = int(reach * 1.35)
                likes = 60 + (day_idx % 6) * 15
                comments = 15 + (day_idx % 4) * 5
                shares = 6 + (day_idx % 3) * 3
                clicks = 12 + (day_idx % 5) * 4
                engagement = likes + comments + shares + clicks
                points.append({
                    "date": cur.date() if isinstance(cur, datetime) else cur,
                    "followers": base_followers,
                    "follower_growth": daily_growth,
                    "impressions": impressions,
                    "reach": reach,
                    "engagement": engagement,
                    "likes": likes,
                    "comments": comments,
                    "shares": shares,
                    "clicks": clicks,
                    "posts_published": 1 if day_idx % 2 == 0 else 0,
                })
                cur += timedelta(days=1)
                day_idx += 1
            return points
        return []
