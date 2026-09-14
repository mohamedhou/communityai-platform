from __future__ import annotations

from datetime import date
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsSeedResponse,
    AnalyticsSummaryResponse,
    AnalyticsTimeSeriesResponse,
    TopPostsResponse,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])
analytics_service = AnalyticsService()


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def get_analytics_summary(
    social_account_id: int | None = Query(default=None),
    platform: str | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    days: int | None = Query(default=None, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalyticsSummaryResponse:
    return analytics_service.get_summary(
        db=db,
        user_id=current_user.id,
        social_account_id=social_account_id,
        platform=platform,
        start_date=start_date,
        end_date=end_date,
        days=days,
    )


@router.get("/timeseries", response_model=AnalyticsTimeSeriesResponse)
def get_analytics_timeseries(
    social_account_id: int | None = Query(default=None),
    platform: str | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    days: int | None = Query(default=None, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalyticsTimeSeriesResponse:
    return analytics_service.get_time_series(
        db=db,
        user_id=current_user.id,
        social_account_id=social_account_id,
        platform=platform,
        start_date=start_date,
        end_date=end_date,
        days=days,
    )


@router.get("/top-posts", response_model=TopPostsResponse)
def get_top_posts(
    social_account_id: int | None = Query(default=None),
    platform: str | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TopPostsResponse:
    return analytics_service.get_top_posts(
        db=db,
        user_id=current_user.id,
        social_account_id=social_account_id,
        platform=platform,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )


@router.post("/seed-mock", response_model=AnalyticsSeedResponse, status_code=status.HTTP_201_CREATED)
def seed_mock_analytics(
    days: int = Query(default=30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalyticsSeedResponse:
    return analytics_service.seed_mock(
        db=db,
        user_id=current_user.id,
        days=days,
    )
