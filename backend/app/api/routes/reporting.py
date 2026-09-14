from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.reporting import ReportPreviewResponse, ReportRequest
from app.services.reporting_service import ReportingService


router = APIRouter(prefix="/api/v1/reports", tags=["reporting"])


def _request(
    social_account_id: int | None,
    platform: str | None,
    start_date: date,
    end_date: date,
) -> ReportRequest:
    try:
        return ReportRequest(
            social_account_id=social_account_id,
            platform=platform,
            start_date=start_date,
            end_date=end_date,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid report request") from exc


@router.get("/preview", response_model=ReportPreviewResponse)
def preview(
    social_account_id: int | None = Query(default=None, ge=1),
    platform: str | None = Query(default=None),
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReportPreviewResponse:
    return ReportingService().build_preview(db, current_user, _request(social_account_id, platform, start_date, end_date))


def _export_request(
    social_account_id: int | None,
    platform: str | None,
    start_date: date,
    end_date: date,
    current_user: User,
    db: Session,
    kind: str,
) -> Response:
    service = ReportingService()
    preview_response = service.build_preview(db, current_user, _request(social_account_id, platform, start_date, end_date))
    today = date.today().isoformat()
    if kind == "csv":
        return Response(
            content=service.generate_csv(preview_response),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="communityai-report-{today}.csv"'},
        )
    return Response(
        content=service.generate_pdf(preview_response),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="communityai-report-{today}.pdf"'},
    )


@router.get("/export/csv")
def export_csv(
    social_account_id: int | None = Query(default=None, ge=1), platform: str | None = Query(default=None),
    start_date: date = Query(...), end_date: date = Query(...),
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
) -> Response:
    return _export_request(social_account_id, platform, start_date, end_date, current_user, db, "csv")


@router.get("/export/pdf")
def export_pdf(
    social_account_id: int | None = Query(default=None, ge=1), platform: str | None = Query(default=None),
    start_date: date = Query(...), end_date: date = Query(...),
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
) -> Response:
    return _export_request(social_account_id, platform, start_date, end_date, current_user, db, "pdf")