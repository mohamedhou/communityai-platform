from __future__ import annotations

from datetime import datetime, UTC

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "communityai-api",
        "timestamp": datetime.now(UTC).isoformat(),
    }
