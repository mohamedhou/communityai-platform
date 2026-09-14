from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.analytics_snapshot import AnalyticsSnapshot
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import (
    AnalyticsKpiSummary,
    AnalyticsSeedResponse,
    AnalyticsSummaryResponse,
    AnalyticsTimeSeriesPoint,
    AnalyticsTimeSeriesResponse,
    TopPostMetric,
    TopPostsResponse,
)
from app.social.models import SocialAccount, SocialAccountStatus


class AnalyticsService:
    def __init__(self, repository: AnalyticsRepository | None = None):
        self.repository = repository or AnalyticsRepository()

    def _normalize_dates(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        days: int | None = None,
    ) -> tuple[date, date]:
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            day_count = days if days and days > 0 else 30
            start_date = end_date - timedelta(days=day_count - 1)
        if start_date > end_date:
            start_date, end_date = end_date, start_date
        return start_date, end_date

    def _verify_social_account_ownership(
        self,
        db: Session,
        user_id: int,
        social_account_id: int | None,
    ) -> None:
        if social_account_id is None:
            return
        account = db.get(SocialAccount, social_account_id)
        if not account or account.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Social account not found",
            )

    def _ensure_mock_data_if_needed(self, db: Session, user_id: int) -> None:
        settings = get_settings()
        if not settings.social_mock_mode:
            return

        accounts = self.repository.get_user_social_accounts(db, user_id=user_id)
        if not accounts:
            from app.core.encryption import encrypt_token

            # Create mock social account for development
            acc = SocialAccount(
                user_id=user_id,
                platform="facebook",
                provider="meta",
                external_account_id=f"fb_mock_acc_{user_id}",
                account_name="CommunityAI Page",
                account_username="communityai_page",
                profile_image_url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe",
                access_token_encrypted=encrypt_token("mock-token"),
                status=SocialAccountStatus.CONNECTED,
            )
            db.add(acc)
            db.commit()
            db.refresh(acc)
            accounts = [acc]

        # Check if snapshots exist
        existing = self.repository.get_snapshots(db, user_id=user_id)
        if not existing:
            for acc in accounts:
                self.repository.seed_mock_analytics(db, user_id=user_id, social_account=acc, days=30)

    def get_summary(
        self,
        db: Session,
        user_id: int,
        social_account_id: int | None = None,
        platform: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        days: int | None = None,
    ) -> AnalyticsSummaryResponse:
        self._verify_social_account_ownership(db, user_id, social_account_id)
        self._ensure_mock_data_if_needed(db, user_id)

        start, end = self._normalize_dates(start_date, end_date, days)
        snapshots = self.repository.get_snapshots(
            db=db,
            user_id=user_id,
            social_account_id=social_account_id,
            platform=platform,
            start_date=start,
            end_date=end,
        )

        accounts = self.repository.get_user_social_accounts(
            db=db,
            user_id=user_id,
            social_account_id=social_account_id,
            platform=platform,
        )
        accounts_count = len(accounts) or 1

        if not snapshots:
            return AnalyticsSummaryResponse(
                period_start=start,
                period_end=end,
                kpis=AnalyticsKpiSummary(),
                social_account_id=social_account_id,
                platform=platform,
                accounts_count=accounts_count,
            )

        # Compute followers & follower growth strictly according to specification:
        # Group snapshots by social_account_id
        by_account: dict[int, list[AnalyticsSnapshot]] = defaultdict(list)
        for s in snapshots:
            by_account[s.social_account_id].append(s)

        earliest_total_followers = 0
        latest_total_followers = 0

        for acc_id, snaps in by_account.items():
            earliest_snap = min(snaps, key=lambda x: x.date)
            latest_snap = max(snaps, key=lambda x: x.date)
            earliest_total_followers += earliest_snap.followers
            latest_total_followers += latest_snap.followers

        total_followers = latest_total_followers
        follower_growth = latest_total_followers - earliest_total_followers

        # Sum cumulative metrics across period
        total_impressions = sum(s.impressions for s in snapshots)
        total_reach = sum(s.reach for s in snapshots)
        total_engagement = sum(s.engagement for s in snapshots)
        engagement_rate = (
            round((total_engagement / total_reach * 100), 2) if total_reach > 0 else 0.0
        )
        total_likes = sum(s.likes for s in snapshots)
        total_comments = sum(s.comments for s in snapshots)
        total_shares = sum(s.shares for s in snapshots)
        total_clicks = sum(s.clicks for s in snapshots)
        posts_published = sum(s.posts_published for s in snapshots)

        kpis = AnalyticsKpiSummary(
            total_followers=total_followers,
            follower_growth=follower_growth,
            total_impressions=total_impressions,
            total_reach=total_reach,
            total_engagement=total_engagement,
            engagement_rate=engagement_rate,
            total_likes=total_likes,
            total_comments=total_comments,
            total_shares=total_shares,
            total_clicks=total_clicks,
            posts_published=posts_published,
        )

        return AnalyticsSummaryResponse(
            period_start=start,
            period_end=end,
            kpis=kpis,
            social_account_id=social_account_id,
            platform=platform,
            accounts_count=accounts_count,
        )

    def get_time_series(
        self,
        db: Session,
        user_id: int,
        social_account_id: int | None = None,
        platform: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        days: int | None = None,
    ) -> AnalyticsTimeSeriesResponse:
        self._verify_social_account_ownership(db, user_id, social_account_id)
        self._ensure_mock_data_if_needed(db, user_id)

        start, end = self._normalize_dates(start_date, end_date, days)
        snapshots = self.repository.get_snapshots(
            db=db,
            user_id=user_id,
            social_account_id=social_account_id,
            platform=platform,
            start_date=start,
            end_date=end,
        )

        # Group by date for metric-appropriate aggregation
        by_date: dict[date, list[AnalyticsSnapshot]] = defaultdict(list)
        for s in snapshots:
            by_date[s.date].append(s)

        points: list[AnalyticsTimeSeriesPoint] = []
        for d in sorted(by_date.keys()):
            day_snaps = by_date[d]
            followers = sum(s.followers for s in day_snaps)
            growth = sum(s.follower_growth for s in day_snaps)
            impressions = sum(s.impressions for s in day_snaps)
            reach = sum(s.reach for s in day_snaps)
            engagement = sum(s.engagement for s in day_snaps)
            rate = round((engagement / reach * 100), 2) if reach > 0 else 0.0
            likes = sum(s.likes for s in day_snaps)
            comments = sum(s.comments for s in day_snaps)
            shares = sum(s.shares for s in day_snaps)
            clicks = sum(s.clicks for s in day_snaps)
            posts_pub = sum(s.posts_published for s in day_snaps)

            points.append(
                AnalyticsTimeSeriesPoint(
                    date=d,
                    followers=followers,
                    follower_growth=growth,
                    impressions=impressions,
                    reach=reach,
                    engagement=engagement,
                    engagement_rate=rate,
                    likes=likes,
                    comments=comments,
                    shares=shares,
                    clicks=clicks,
                    posts_published=posts_pub,
                )
            )

        return AnalyticsTimeSeriesResponse(
            period_start=start,
            period_end=end,
            points=points,
        )

    def get_top_posts(
        self,
        db: Session,
        user_id: int,
        social_account_id: int | None = None,
        platform: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 10,
    ) -> TopPostsResponse:
        self._verify_social_account_ownership(db, user_id, social_account_id)
        self._ensure_mock_data_if_needed(db, user_id)

        items = self.repository.get_top_posts(
            db=db,
            user_id=user_id,
            social_account_id=social_account_id,
            platform=platform,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

        return TopPostsResponse(
            items=items,
            total=len(items),
        )

    def seed_mock(
        self,
        db: Session,
        user_id: int,
        days: int = 30,
    ) -> AnalyticsSeedResponse:
        settings = get_settings()
        if not settings.social_mock_mode:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Mock mode is disabled",
            )

        accounts = self.repository.get_user_social_accounts(db, user_id=user_id)
        if not accounts:
            from app.core.encryption import encrypt_token

            acc = SocialAccount(
                user_id=user_id,
                platform="facebook",
                provider="meta",
                external_account_id=f"fb_seed_{user_id}",
                account_name="CommunityAI Page",
                account_username="communityai_page",
                profile_image_url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe",
                access_token_encrypted=encrypt_token("mock-token"),
                status=SocialAccountStatus.CONNECTED,
            )
            db.add(acc)
            db.commit()
            db.refresh(acc)
            accounts = [acc]

        total_created = 0
        for acc in accounts:
            created = self.repository.seed_mock_analytics(
                db=db,
                user_id=user_id,
                social_account=acc,
                days=days,
            )
            total_created += len(created)

        return AnalyticsSeedResponse(
            message=f"Successfully seeded mock analytics data ({total_created} snapshots created).",
            snapshots_created=total_created,
        )
