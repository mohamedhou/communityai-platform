from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def read_root() -> dict[str, str]:
    return {
        "message": "CommunityAI API is running",
        "status": "ok",
    }
