from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
import pytest
from sqlalchemy.orm import Session

# Set test environment defaults before imports
os.environ["SOCIAL_TOKEN_ENCRYPTION_KEY"] = "G3cZ84fJd9X2-vK8pQLt8G3cZ84fJd9X2-vK8pQLt8E="
os.environ["SOCIAL_MOCK_MODE"] = "true"

from app.core.encryption import encrypt_token
from app.models.user import User
from app.models.post import Post, PostStatus
from app.social.models import SocialAccount


def _register_payload(email: str = "calendar_user@example.com") -> dict[str, str]:
    return {
        "email": email,
        "password": "StrongPass123",
        "first_name": "Cal",
        "last_name": "User",
    }


def _login(client, email: str = "calendar_user@example.com", password: str = "StrongPass123"):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )


def _setup_user_and_social(client, db_session: Session, email: str = "calendar_user@example.com"):
    client.post("/api/v1/auth/register", json=_register_payload(email))
    token = _login(client, email=email).json()["access_token"]
    user = db_session.query(User).filter(User.email == email).one()

    account = SocialAccount(
        user_id=user.id,
        platform="facebook",
        provider="meta",
        external_account_id=f"fb-page-{user.id}",
        account_name=f"{user.first_name} FB Page",
        access_token_encrypted=encrypt_token("mock-token"),
        status="CONNECTED",
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return token, user, account


def test_calendar_list_scheduled_posts(client, db_session: Session):
    token, user, account = _setup_user_and_social(client, db_session, "cal_list@example.com")

    # Create mixed posts: 2 SCHEDULED, 1 DRAFT, 1 PUBLISHED
    time1 = datetime.now(UTC) + timedelta(days=2)
    time2 = datetime.now(UTC) + timedelta(days=5)

    post_sched1 = Post(
        user_id=user.id,
        social_account_id=account.id,
        content="Scheduled post 1",
        status=PostStatus.SCHEDULED,
        scheduled_at=time1,
    )
    post_sched2 = Post(
        user_id=user.id,
        social_account_id=account.id,
        content="Scheduled post 2",
        status=PostStatus.SCHEDULED,
        scheduled_at=time2,
    )
    post_draft = Post(
        user_id=user.id,
        social_account_id=account.id,
        content="Draft post",
        status=PostStatus.DRAFT,
    )
    post_published = Post(
        user_id=user.id,
        social_account_id=account.id,
        content="Published post",
        status=PostStatus.PUBLISHED,
        published_at=datetime.now(UTC),
    )
    db_session.add_all([post_sched1, post_sched2, post_draft, post_published])
    db_session.commit()

    # List all posts
    res_all = client.get(
        "/api/v1/posts",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_all.status_code == 200
    all_posts = res_all.json()
    assert len(all_posts) == 4

    # List only SCHEDULED posts
    res_sched = client.get(
        "/api/v1/posts?status_filter=SCHEDULED",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_sched.status_code == 200
    sched_posts = res_sched.json()
    assert len(sched_posts) == 2
    for p in sched_posts:
        assert p["status"] == "SCHEDULED"
        assert p["scheduled_at"] is not None


def test_calendar_ownership(client, db_session: Session):
    token_a, user_a, account_a = _setup_user_and_social(client, db_session, "cal_a@example.com")
    token_b, user_b, account_b = _setup_user_and_social(client, db_session, "cal_b@example.com")

    future_time = datetime.now(UTC) + timedelta(days=3)
    post_a = Post(
        user_id=user_a.id,
        social_account_id=account_a.id,
        content="User A's calendar post",
        status=PostStatus.SCHEDULED,
        scheduled_at=future_time,
    )
    db_session.add(post_a)
    db_session.commit()

    # User B list posts -> should not see User A's post
    res_b_list = client.get(
        "/api/v1/posts",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_b_list.status_code == 200
    assert len(res_b_list.json()) == 0

    # User B tries to reschedule User A's post -> expects 403 Forbidden
    new_time = (datetime.now(UTC) + timedelta(days=6)).isoformat()
    res_hack = client.post(
        f"/api/v1/posts/{post_a.id}/schedule",
        json={"scheduled_at": new_time},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_hack.status_code == 403


def test_calendar_modify_scheduled_at(client, db_session: Session):
    token, user, account = _setup_user_and_social(client, db_session, "cal_modify@example.com")

    initial_time = datetime.now(UTC) + timedelta(days=2)
    post = Post(
        user_id=user.id,
        social_account_id=account.id,
        content="Initial schedule",
        status=PostStatus.SCHEDULED,
        scheduled_at=initial_time,
    )
    db_session.add(post)
    db_session.commit()

    # Move to 7 days later (drag & drop simulation)
    new_time = datetime.now(UTC) + timedelta(days=7)
    res = client.post(
        f"/api/v1/posts/{post.id}/schedule",
        json={"scheduled_at": new_time.isoformat()},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "SCHEDULED"
    db_session.refresh(post)
    assert post.scheduled_at is not None
    assert post.scheduled_at.date() == new_time.date()


def test_calendar_schedule_from_draft(client, db_session: Session):
    token, user, account = _setup_user_and_social(client, db_session, "cal_draft@example.com")

    post = Post(
        user_id=user.id,
        social_account_id=account.id,
        content="Draft to be scheduled on calendar",
        status=PostStatus.DRAFT,
    )
    db_session.add(post)
    db_session.commit()

    target_time = datetime.now(UTC) + timedelta(days=4)
    res = client.post(
        f"/api/v1/posts/{post.id}/schedule",
        json={"scheduled_at": target_time.isoformat()},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "SCHEDULED"
    db_session.refresh(post)
    assert post.status == PostStatus.SCHEDULED
    assert post.scheduled_at is not None


def test_calendar_refuse_modify_published(client, db_session: Session):
    token, user, account = _setup_user_and_social(client, db_session, "cal_published@example.com")

    post = Post(
        user_id=user.id,
        social_account_id=account.id,
        content="Already published post",
        status=PostStatus.PUBLISHED,
        published_at=datetime.now(UTC),
    )
    db_session.add(post)
    db_session.commit()

    # Attempt to reschedule a PUBLISHED post -> must fail with 400 Bad Request
    target_time = (datetime.now(UTC) + timedelta(days=3)).isoformat()
    res = client.post(
        f"/api/v1/posts/{post.id}/schedule",
        json={"scheduled_at": target_time},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400
    assert "Invalid status transition" in res.json()["detail"]


def test_calendar_refuse_modify_publishing(client, db_session: Session):
    token, user, account = _setup_user_and_social(client, db_session, "cal_publishing@example.com")

    post = Post(
        user_id=user.id,
        social_account_id=account.id,
        content="Currently publishing post",
        status=PostStatus.PUBLISHING,
    )
    db_session.add(post)
    db_session.commit()

    # Attempt to reschedule a PUBLISHING post -> must fail with 400 Bad Request
    target_time = (datetime.now(UTC) + timedelta(days=3)).isoformat()
    res = client.post(
        f"/api/v1/posts/{post.id}/schedule",
        json={"scheduled_at": target_time},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400
    assert "Invalid status transition" in res.json()["detail"]


def test_calendar_refuse_invalid_past_dates(client, db_session: Session):
    token, user, account = _setup_user_and_social(client, db_session, "cal_past@example.com")

    post = Post(
        user_id=user.id,
        social_account_id=account.id,
        content="Post for past schedule test",
        status=PostStatus.DRAFT,
    )
    db_session.add(post)
    db_session.commit()

    # Past date
    past_time = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
    res = client.post(
        f"/api/v1/posts/{post.id}/schedule",
        json={"scheduled_at": past_time},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400
    assert "Scheduled time must be in the future" in res.json()["detail"]


def test_calendar_cancel_scheduled_post(client, db_session: Session):
    token, user, account = _setup_user_and_social(client, db_session, "cal_cancel@example.com")

    future_time = datetime.now(UTC) + timedelta(days=1)
    post = Post(
        user_id=user.id,
        social_account_id=account.id,
        content="Scheduled post to cancel",
        status=PostStatus.SCHEDULED,
        scheduled_at=future_time,
    )
    db_session.add(post)
    db_session.commit()

    res = client.post(
        f"/api/v1/posts/{post.id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "CANCELLED"
    db_session.refresh(post)
    assert post.status == PostStatus.CANCELLED
