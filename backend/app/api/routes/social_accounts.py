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


def _safe_configuration_status() -> dict[str, object]:
    """Expose only safe connection-mode metadata for the frontend."""
    from app.core.config import get_settings

    settings = get_settings()
    return {
        "mock_mode": settings.social_mock_mode,
        "meta_configured": bool(settings.meta_client_id and settings.meta_client_secret and settings.meta_redirect_uri),
        "linkedin_configured": bool(
            settings.linkedin_client_id and settings.linkedin_client_secret and settings.linkedin_redirect_uri
        ),
    }


@router.get("/mode")
def get_social_mode(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    return _safe_configuration_status()


@router.get("/config-status")
def get_social_config_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return _safe_configuration_status()


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
    error: str | None = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    service = SocialAccountService(db)
    from app.core.config import get_settings

    frontend_base_url = f"{get_settings().frontend_app_url.rstrip('/')}/social-accounts"
    try:
        if error:
            return RedirectResponse(url=f"{frontend_base_url}?error=provider_denied")
        service.process_callback(platform, code, state)
        return RedirectResponse(url=frontend_base_url)
    except OAuthStateExpiredOrInvalid as exc:
        err_param = urllib.parse.quote("state_invalid_or_expired")
        return RedirectResponse(url=f"{frontend_base_url}?error={err_param}")
    except SocialProviderError as exc:
        safe_error = "oauth_provider_error"
        message = str(exc)
        if "not configured" in message.lower():
            safe_error = "oauth_not_configured"
        err_param = urllib.parse.quote(safe_error)
        return RedirectResponse(url=f"{frontend_base_url}?error={err_param}")
    except Exception:
        err_param = urllib.parse.quote("oauth_unexpected_error")
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
