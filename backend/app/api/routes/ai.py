from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.ai.exceptions import AIProviderError
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.ai import (
    AIAdaptPlatformRequest,
    AIChangeToneRequest,
    AIExpandRequest,
    AIGenerateRequest,
    AIIdeasRequest,
    AIImproveRequest,
    AIResponse,
    AIRewriteRequest,
    AIShortenRequest,
)
from app.services.ai_service import AIService

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


@router.post("/generate", response_model=AIResponse)
def generate_post(
    payload: AIGenerateRequest,
    current_user: User = Depends(get_current_user),
) -> AIResponse:
    service = AIService()
    try:
        return service.generate_post(payload)
    except AIProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/rewrite", response_model=AIResponse)
def rewrite_content(
    payload: AIRewriteRequest,
    current_user: User = Depends(get_current_user),
) -> AIResponse:
    service = AIService()
    try:
        return service.rewrite_content(payload)
    except AIProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/improve", response_model=AIResponse)
def improve_content(
    payload: AIImproveRequest,
    current_user: User = Depends(get_current_user),
) -> AIResponse:
    service = AIService()
    try:
        return service.improve_content(payload)
    except AIProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/shorten", response_model=AIResponse)
def shorten_content(
    payload: AIShortenRequest,
    current_user: User = Depends(get_current_user),
) -> AIResponse:
    service = AIService()
    try:
        return service.shorten_content(payload)
    except AIProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/expand", response_model=AIResponse)
def expand_content(
    payload: AIExpandRequest,
    current_user: User = Depends(get_current_user),
) -> AIResponse:
    service = AIService()
    try:
        return service.expand_content(payload)
    except AIProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/change-tone", response_model=AIResponse)
def change_tone(
    payload: AIChangeToneRequest,
    current_user: User = Depends(get_current_user),
) -> AIResponse:
    service = AIService()
    try:
        return service.change_tone(payload)
    except AIProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/adapt-platform", response_model=AIResponse)
def adapt_platform(
    payload: AIAdaptPlatformRequest,
    current_user: User = Depends(get_current_user),
) -> AIResponse:
    service = AIService()
    try:
        return service.adapt_platform(payload)
    except AIProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/ideas", response_model=AIResponse)
def generate_ideas(
    payload: AIIdeasRequest,
    current_user: User = Depends(get_current_user),
) -> AIResponse:
    service = AIService()
    try:
        return service.generate_ideas(payload)
    except AIProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
