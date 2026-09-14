from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.analytics import AnalyticsKpiSummary, AnalyticsTimeSeriesPoint, TopPostMetric


class ReportRequest(BaseModel):
    social_account_id: int | None = Field(default=None, ge=1)
    platform: str | None = Field(default=None, max_length=50)
    start_date: date
    end_date: date

    @field_validator("platform")
    @classmethod
    def normalize_platform(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        return cleaned or None

    @model_validator(mode="after")
    def validate_period(self) -> "ReportRequest":
        if self.start_date > self.end_date:
            raise ValueError("start_date must be before or equal to end_date")
        if (self.end_date - self.start_date).days > 365:
            raise ValueError("report period cannot exceed 366 days")
        return self


class ReportPreviewResponse(BaseModel):
    report_title: str
    workspace_name: str
    period_start: date
    period_end: date
    platform: str | None
    accounts: list[str]
    kpis: AnalyticsKpiSummary
    time_series: list[AnalyticsTimeSeriesPoint]
    engagement_breakdown: dict[str, int]
    top_posts: list[TopPostMetric]
    generated_at: datetime