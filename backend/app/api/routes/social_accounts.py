from __future__ import annotations

import urllib.parse

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.social_account import SocialAccountResponse
from app.services.social_account_service import SocialAccountService
from app.social.exceptions import OAuthStateExpiredOrInvalid, SocialProviderError

router = APIRouter(prefix="/api/v1/social-accounts", tags=["social-accounts"])


@router.get("", response_model=list[SocialAccountResponse])
def list_social_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SocialAccountResponse]:
    service = SocialAccountService(db)
    accounts = service.list_accounts(current_user.id)
    return [SocialAccountResponse.model_validate(acc) for acc in accounts]


@router.get("/{platform}/connect")
def get_connect_url(
    platform: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    service = SocialAccountService(db)
    try:
        url = service.create_authorization_url(current_user.id, platform)
        return {"url": url}
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except SocialProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.get("/{platform}/callback")
def oauth_callback(
    platform: str,
    code: str,
    state: str,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    service = SocialAccountService(db)
    frontend_base_url = "http://localhost:5173/social-accounts"
    try:
        service.process_callback(platform, code, state)
        return RedirectResponse(url=frontend_base_url)
    except OAuthStateExpiredOrInvalid as exc:
        err_param = urllib.parse.quote("state_invalid_or_expired")
        return RedirectResponse(url=f"{frontend_base_url}?error={err_param}")
    except SocialProviderError as exc:
        err_param = urllib.parse.quote(str(exc))
        return RedirectResponse(url=f"{frontend_base_url}?error={err_param}")
    except Exception as exc:
        err_param = urllib.parse.quote(f"Unexpected error: {exc}")
        return RedirectResponse(url=f"{frontend_base_url}?error={err_param}")


@router.delete("/{account_id}", status_code=status.HTTP_200_OK)
def disconnect_social_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    service = SocialAccountService(db)
    try:
        service.disconnect_account(current_user.id, account_id)
        return {"message": "Account disconnected successfully"}
    except ValueError as exc:
        if str(exc) == "account_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Social account not found",
            ) from exc
        raise
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this social account",
        ) from exc


@router.post("/{account_id}/refresh", response_model=SocialAccountResponse)
def refresh_social_account_token(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SocialAccountResponse:
    service = SocialAccountService(db)
    try:
        updated_account = service.refresh_account_token(current_user.id, account_id)
        return SocialAccountResponse.model_validate(updated_account)
    except ValueError as exc:
        if str(exc) == "account_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Social account not found",
            ) from exc
        raise
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this social account",
        ) from exc
    except SocialProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
