from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.analytics_snapshot import AnalyticsSnapshot
from app.models.post import Post, PostStatus
from app.schemas.analytics import TopPostMetric
from app.social.models import SocialAccount


class AnalyticsRepository:
    def get_user_social_accounts(
        self,
        db: Session,
        user_id: int,
        social_account_id: int | None = None,
        platform: str | None = None,
    ) -> list[SocialAccount]:
        query = select(SocialAccount).where(SocialAccount.user_id == user_id)
        if social_account_id is not None:
            query = query.where(SocialAccount.id == social_account_id)
        if platform:
            plat_clean = platform.strip().lower()
            query = query.where(
                or_(
                    func.lower(SocialAccount.platform) == plat_clean,
                    func.lower(SocialAccount.provider) == plat_clean,
                )
            )
        return list(db.scalars(query).all())

    def get_snapshots(
        self,
        db: Session,
        user_id: int,
        social_account_id: int | None = None,
        platform: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[AnalyticsSnapshot]:
        query = (
            select(AnalyticsSnapshot)
            .options(joinedload(AnalyticsSnapshot.social_account))
            .where(AnalyticsSnapshot.user_id == user_id)
        )

        if social_account_id is not None:
            query = query.where(AnalyticsSnapshot.social_account_id == social_account_id)

        if platform:
            plat_clean = platform.strip().lower()
            query = query.join(SocialAccount, AnalyticsSnapshot.social_account_id == SocialAccount.id).where(
                or_(
                    func.lower(SocialAccount.platform) == plat_clean,
                    func.lower(SocialAccount.provider) == plat_clean,
                )
            )

        if start_date is not None:
            query = query.where(AnalyticsSnapshot.date >= start_date)
        if end_date is not None:
            query = query.where(AnalyticsSnapshot.date <= end_date)

        query = query.order_by(AnalyticsSnapshot.date.asc(), AnalyticsSnapshot.social_account_id.asc())
        return list(db.scalars(query).unique().all())

    def create_snapshot(self, db: Session, snapshot: AnalyticsSnapshot) -> AnalyticsSnapshot:
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return snapshot

    def get_top_posts(
        self,
        db: Session,
        user_id: int,
        social_account_id: int | None = None,
        platform: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 10,
    ) -> list[TopPostMetric]:
        query = (
            select(Post)
            .options(joinedload(Post.social_account))
            .where(Post.user_id == user_id)
        )

        if social_account_id is not None:
            query = query.where(Post.social_account_id == social_account_id)

        if platform:
            plat_clean = platform.strip().lower()
            query = query.join(SocialAccount, Post.social_account_id == SocialAccount.id).where(
                or_(
                    func.lower(SocialAccount.platform) == plat_clean,
                    func.lower(SocialAccount.provider) == plat_clean,
                )
            )

        if start_date is not None:
            query = query.where(func.date(Post.created_at) >= start_date)
        if end_date is not None:
            query = query.where(func.date(Post.created_at) <= end_date)

        query = query.order_by(Post.created_at.desc()).limit(limit * 2)
        posts = list(db.scalars(query).unique().all())

        # Generate coherent metrics for posts
        top_metrics: list[TopPostMetric] = []
        for p in posts:
            # Deterministic calculation based on post attributes
            seed_val = (p.id * 17 + len(p.content) * 3) % 100
            reach = 850 + seed_val * 45
            impressions = int(reach * 1.4)
            likes = int(reach * 0.05) + (seed_val % 20)
            comments = int(likes * 0.25) + (seed_val % 8)
            shares = int(likes * 0.12) + (seed_val % 5)
            clicks = int(reach * 0.03) + (seed_val % 10)
            engagement = likes + comments + shares + clicks
            rate = round((engagement / reach * 100), 2) if reach > 0 else 0.0

            plat_name = p.social_account.platform if p.social_account else "Social"
            acc_name = p.social_account.account_name if p.social_account else "Account"

            top_metrics.append(
                TopPostMetric(
                    post_id=p.id,
                    content=p.content,
                    media_url=p.media_url,
                    platform=plat_name,
                    account_name=acc_name,
                    published_at=p.published_at or p.created_at,
                    likes=likes,
                    comments=comments,
                    shares=shares,
                    clicks=clicks,
                    impressions=impressions,
                    reach=reach,
                    engagement=engagement,
                    engagement_rate=rate,
                )
            )

        # Sort by total engagement descending
        top_metrics.sort(key=lambda x: x.engagement, reverse=True)
        return top_metrics[:limit]

    def seed_mock_analytics(
        self,
        db: Session,
        user_id: int,
        social_account: SocialAccount,
        days: int = 30,
    ) -> list[AnalyticsSnapshot]:
        end = date.today()
        start = end - timedelta(days=days - 1)

        # Base numbers by platform
        is_meta = "meta" in (social_account.provider or "").lower() or "facebook" in (social_account.platform or "").lower()
        base_followers = 12000 if is_meta else 5600
        growth_step = 12 if is_meta else 7

        created = []
        current_followers = base_followers

        # Check existing snapshots to avoid duplicates
        existing_dates = set(
            db.scalars(
                select(AnalyticsSnapshot.date).where(
                    AnalyticsSnapshot.social_account_id == social_account.id,
                    AnalyticsSnapshot.date >= start,
                    AnalyticsSnapshot.date <= end,
                )
            ).all()
        )

        for i in range(days):
            cur_date = start + timedelta(days=i)
            if cur_date in existing_dates:
                continue

            day_of_week = cur_date.weekday()  # 0 is Mon, 6 is Sun
            # Plausible weekday vs weekend curve
            is_weekend = day_of_week >= 5
            growth = growth_step + (i % 5) - (2 if is_weekend else 0)
            if growth < 1:
                growth = 1

            current_followers += growth

            # Reach & Impressions
            reach_base = 1400 if is_meta else 800
            reach = reach_base + (i % 6) * 120 + (i * 10) - (250 if is_weekend else 0)
            impressions = int(reach * (1.35 if is_meta else 1.28))

            # Engagement breakdown (correlated with reach)
            likes = int(reach * 0.045) + (i % 4) * 3
            comments = int(likes * 0.22) + (i % 3) * 2
            shares = int(likes * 0.10) + (i % 2) * 2
            clicks = int(reach * 0.02) + (i % 3)
            engagement = likes + comments + shares + clicks
            posts_pub = 1 if (i % 3 == 0 and not is_weekend) else 0

            snapshot = AnalyticsSnapshot(
                user_id=user_id,
                social_account_id=social_account.id,
                date=cur_date,
                followers=current_followers,
                follower_growth=growth,
                impressions=impressions,
                reach=reach,
                engagement=engagement,
                likes=likes,
                comments=comments,
                shares=shares,
                clicks=clicks,
                posts_published=posts_pub,
            )
            db.add(snapshot)
            created.append(snapshot)

        db.commit()
        return created
