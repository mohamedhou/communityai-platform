from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.settings import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    UserSettingsResponse,
    UserSettingsUpdate,
)
from app.services.settings_service import SettingsService


router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


@router.get("", response_model=UserSettingsResponse)
def get_settings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> UserSettingsResponse:
    return SettingsService(db).get_settings(current_user)


@router.patch("", response_model=UserSettingsResponse)
def update_settings(
    payload: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserSettingsResponse:
    return SettingsService(db).update_settings(current_user, payload)


@router.post("/change-password", response_model=ChangePasswordResponse)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChangePasswordResponse:
    try:
        SettingsService(db).change_password(current_user, payload)
    except ValueError as exc:
        if str(exc) == "invalid_current_password":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid current password") from exc
        raise
    return ChangePasswordResponse(message="Password changed successfully")