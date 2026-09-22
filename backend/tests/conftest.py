from __future__ import annotations

import os
import sys
from pathlib import Path
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault(
    "SOCIAL_TOKEN_ENCRYPTION_KEY",
    "G3cZ84fJd9X2-vK8pQLt8G3cZ84fJd9X2-vK8pQLt8E=",
)

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.api.dependencies import get_db
from app.core.config import get_settings
from app.database.base import Base
from app.main import app
from app.models import RefreshToken, User
from app.models.analytics_snapshot import AnalyticsSnapshot
from app.models.inbox_message import InboxMessage
from app.models.post import Post
from app.models.workspace import MembershipStatus, Workspace, WorkspaceMember, WorkspaceRole
from app.social.models import SocialAccount
from sqlalchemy import event


def _ensure_workspace_for_user(session: Session, user_id: int) -> int:
    membership = (
        session.query(WorkspaceMember)
        .filter(
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.status == MembershipStatus.ACTIVE,
        )
        .order_by(WorkspaceMember.id.asc())
        .first()
    )
    if membership:
        return membership.workspace_id

    workspace = session.query(Workspace).filter(Workspace.owner_id == user_id).first()
    if not workspace:
        user = session.get(User, user_id)
        email_prefix = user.email.split("@", 1)[0].lower() if user and user.email else f"user-{user_id}"
        workspace = Workspace(
            name=f"{user.first_name if user else 'Test'}'s Workspace",
            slug=f"{email_prefix}-{user_id}",
            owner_id=user_id,
        )
        session.add(workspace)
        session.flush()

    membership = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=user_id,
        role=WorkspaceRole.OWNER,
        status=MembershipStatus.ACTIVE,
    )
    session.add(membership)
    session.flush()
    return workspace.id


@event.listens_for(Session, "before_flush")
def _auto_populate_workspace_in_tests(session: Session, flush_context, instances):
    for obj in list(session.new):
        if isinstance(obj, (SocialAccount, Post, InboxMessage, AnalyticsSnapshot)):
            if getattr(obj, "workspace_id", None) is None:
                user_id = getattr(obj, "user_id", None)
                if not user_id and hasattr(obj, "social_account_id") and obj.social_account_id:
                    sa = session.get(SocialAccount, obj.social_account_id)
                    if sa:
                        user_id = sa.user_id
                        if sa.workspace_id:
                            obj.workspace_id = sa.workspace_id
                            continue
                if user_id:
                    obj.workspace_id = _ensure_workspace_for_user(session, user_id)


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    get_settings.cache_clear()
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)



@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
