from __future__ import annotations

from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.root import router as root_router
from app.api.routes.users import router as users_router
from app.api.routes.social_accounts import router as social_accounts_router
from app.api.routes.posts import router as posts_router
from app.api.routes.ai import router as ai_router
from app.api.routes.inbox import router as inbox_router

api_router = APIRouter()
api_router.include_router(root_router)
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(social_accounts_router)
api_router.include_router(posts_router)
api_router.include_router(ai_router)
api_router.include_router(inbox_router)
