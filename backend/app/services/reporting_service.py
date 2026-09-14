from __future__ import annotations

import csv
import io
import re
from datetime import UTC, date, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.settings_repository import SettingsRepository
from app.schemas.analytics import AnalyticsKpiSummary, AnalyticsTimeSeriesPoint, TopPostMetric
from app.schemas.reporting import ReportPreviewResponse, ReportRequest
from app.services.analytics_service import AnalyticsService


class ReportingService:
    def __init__(self, analytics_service: AnalyticsService | None = None):
        self.analytics = analytics_service or AnalyticsService()

    def build_preview(self, db: Session, user: User, request: ReportRequest) -> ReportPreviewResponse:
        self._validate_request(request)
        summary = self.analytics.get_summary(
            db=db, user_id=user.id, social_account_id=request.social_account_id,
            platform=request.platform, start_date=request.start_date, end_date=request.end_date,
        )
        time_series = self.analytics.get_time_series(
            db=db, user_id=user.id, social_account_id=request.social_account_id,
            platform=request.platform, start_date=request.start_date, end_date=request.end_date,
        )
        top_posts = self.analytics.get_top_posts(
            db=db, user_id=user.id, social_account_id=request.social_account_id,
            platform=request.platform, start_date=request.start_date, end_date=request.end_date, limit=10,
        )
        settings = SettingsRepository(db).get_by_user_id(user.id)
        account_names = self.analytics.repository.get_user_social_accounts(
            db=db, user_id=user.id, social_account_id=request.social_account_id, platform=request.platform,
        )
        return ReportPreviewResponse(
            report_title="CommunityAI Performance Report",
            workspace_name=settings.workspace_name if settings else f"{user.first_name} {user.last_name}",
            period_start=summary.period_start,
            period_end=summary.period_end,
            platform=request.platform,
            accounts=[account.account_name for account in account_names],
            kpis=summary.kpis,
            time_series=time_series.points,
            engagement_breakdown={
                "likes": summary.kpis.total_likes,
                "comments": summary.kpis.total_comments,
                "shares": summary.kpis.total_shares,
                "clicks": summary.kpis.total_clicks,
            },
            top_posts=top_posts.items,
            generated_at=datetime.now(UTC),
        )

    def generate_csv(self, preview: ReportPreviewResponse) -> bytes:
        output = io.StringIO(newline="")
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(["REPORT"])
        writer.writerow(["workspace", preview.workspace_name])
        writer.writerow(["period", f"{preview.period_start} - {preview.period_end}"])
        writer.writerow(["platform", preview.platform or "all"])
        writer.writerow([])
        writer.writerow(["KPI"])
        writer.writerow(["metric", "value"])
        for key, value in preview.kpis.model_dump().items():
            writer.writerow([key, value])
        writer.writerow([])
        writer.writerow(["TIME SERIES"])
        writer.writerow([
            "date", "followers", "follower_growth", "impressions", "reach", "engagement",
            "likes", "comments", "shares", "clicks", "posts_published",
        ])
        for point in preview.time_series:
            writer.writerow([
                point.date, point.followers, point.follower_growth, point.impressions, point.reach,
                point.engagement, point.likes, point.comments, point.shares, point.clicks, point.posts_published,
            ])
        writer.writerow([])
        writer.writerow(["TOP POSTS"])
        writer.writerow(["rank", "post_id", "content", "platform", "published_at", "engagement", "likes", "comments", "shares", "clicks", "engagement_rate"])
        for rank, post in enumerate(preview.top_posts, start=1):
            writer.writerow([
                rank, post.post_id, post.content, post.platform, post.published_at,
                post.engagement, post.likes, post.comments, post.shares, post.clicks, post.engagement_rate,
            ])
        return output.getvalue().encode("utf-8-sig")

    def generate_pdf(self, preview: ReportPreviewResponse) -> bytes:
        lines = [
            "CommunityAI Performance Report",
            f"Workspace: {preview.workspace_name}",
            f"Period: {preview.period_start} - {preview.period_end}",
            f"Platform: {preview.platform or 'All platforms'}",
            f"Accounts: {', '.join(preview.accounts) or 'All accounts'}",
            "",
            "KPI SUMMARY",
            f"Followers: {preview.kpis.total_followers} | Growth: {preview.kpis.follower_growth}",
            f"Reach: {preview.kpis.total_reach} | Impressions: {preview.kpis.total_impressions}",
            f"Engagement: {preview.kpis.total_engagement} | Rate: {preview.kpis.engagement_rate}%",
            f"Published posts: {preview.kpis.posts_published}",
            "",
            "ENGAGEMENT BREAKDOWN",
            f"Likes: {preview.engagement_breakdown['likes']} | Comments: {preview.engagement_breakdown['comments']}",
            f"Shares: {preview.engagement_breakdown['shares']} | Clicks: {preview.engagement_breakdown['clicks']}",
            "",
            "PERFORMANCE EVOLUTION",
        ]
        for point in preview.time_series[:31]:
            lines.append(f"{point.date}: followers {point.followers}, reach {point.reach}, engagement {point.engagement}")
        lines.extend(["", "TOP PERFORMING POSTS"])
        for rank, post in enumerate(preview.top_posts, start=1):
            content = self._pdf_text(post.content[:90])
            lines.append(f"{rank}. {content} | engagement {post.engagement} | {post.platform}")
        return self._make_pdf(lines)

    @staticmethod
    def _validate_request(request: ReportRequest) -> None:
        if request.start_date > request.end_date or (request.end_date - request.start_date).days > 365:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid report period")

    @staticmethod
    def _pdf_text(value: str) -> str:
        return value.encode("latin-1", errors="replace").decode("latin-1").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    def _make_pdf(self, lines: list[str]) -> bytes:
        pages = [lines[index:index + 42] for index in range(0, len(lines), 42)] or [[]]
        objects: list[bytes] = []
        objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
        page_ids = [3 + index * 2 for index in range(len(pages))]
        objects.append(f"<< /Type /Pages /Kids [{' '.join(f'{page_id} 0 R' for page_id in page_ids)}] /Count {len(page_ids)} >>".encode())
        for index, page_lines in enumerate(pages):
            page_id = page_ids[index]
            content_id = page_id + 1
            stream_lines = ["BT", "/F1 11 Tf", "50 760 Td"]
            for line in page_lines:
                stream_lines.append(f"({self._pdf_text(line)}) Tj")
                stream_lines.append("0 -17 Td")
            stream_lines.append("ET")
            stream = "\n".join(stream_lines).encode("latin-1", errors="replace")
            objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 {3 + len(pages) * 2} 0 R >> >> /Contents {content_id} 0 R >>".encode())
            objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")
        font_id = 3 + len(pages) * 2
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        result = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for object_id, obj in enumerate(objects, start=1):
            offsets.append(len(result))
            result.extend(f"{object_id} 0 obj\n".encode() + obj + b"\nendobj\n")
        xref = len(result)
        result.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
        result.extend("".join(f"{offset:010d} 00000 n \n" for offset in offsets[1:]).encode())
        result.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode())
        return bytes(result)