from __future__ import annotations

from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field


class AnalyticsKpiSummary(BaseModel):
    total_followers: int = Field(default=0, description="Sum of latest followers across selected accounts")
    follower_growth: int = Field(default=0, description="Growth across period (latest - earliest)")
    total_impressions: int = Field(default=0)
    total_reach: int = Field(default=0)
    total_engagement: int = Field(default=0)
    engagement_rate: float = Field(default=0.0, description="total_engagement / total_reach * 100")
    total_likes: int = Field(default=0)
    total_comments: int = Field(default=0)
    total_shares: int = Field(default=0)
    total_clicks: int = Field(default=0)
    posts_published: int = Field(default=0)


class AnalyticsSummaryResponse(BaseModel):
    period_start: date
    period_end: date
    kpis: AnalyticsKpiSummary
    social_account_id: int | None = None
    platform: str | None = None
    accounts_count: int = 1


class AnalyticsTimeSeriesPoint(BaseModel):
    date: date
    followers: int = 0
    follower_growth: int = 0
    impressions: int = 0
    reach: int = 0
    engagement: int = 0
    engagement_rate: float = 0.0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    clicks: int = 0
    posts_published: int = 0


class AnalyticsTimeSeriesResponse(BaseModel):
    period_start: date
    period_end: date
    points: list[AnalyticsTimeSeriesPoint]


class TopPostMetric(BaseModel):
    post_id: int
    content: str
    media_url: str | None = None
    platform: str
    account_name: str
    published_at: datetime | None = None
    likes: int = 0
    comments: int = 0
    shares: int = 0
    clicks: int = 0
    impressions: int = 0
    reach: int = 0
    engagement: int = 0
    engagement_rate: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class TopPostsResponse(BaseModel):
    items: list[TopPostMetric]
    total: int


class AnalyticsSeedResponse(BaseModel):
    message: str
    snapshots_created: int
