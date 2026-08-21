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


def _register_payload(email: str = "alice@example.com") -> dict[str, str]:
    return {
        "email": email,
        "password": "StrongPass123",
        "first_name": "Alice",
        "last_name": "Martin",
    }


def _login(client, email: str = "alice@example.com", password: str = "StrongPass123"):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )


def _setup_user_and_social(client, db_session: Session, email: str = "alice@example.com"):
    client.post("/api/v1/auth/register", json=_register_payload(email))
    token = _login(client, email=email).json()["access_token"]
    user = db_session.query(User).filter(User.email == email).one()

    # Create social account for user
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


def test_posts_unauthenticated(client):
    res = client.get("/api/v1/posts")
    assert res.status_code == 401


def test_create_and_get_post(client, db_session: Session):
    token, user, account = _setup_user_and_social(client, db_session)

    # Create post
    payload = {
        "content": "Hello world from test!",
        "media_url": "https://example.com/image.jpg",
        "social_account_id": account.id,
    }
    res = client.post(
        "/api/v1/posts",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    body = res.json()
    assert body["content"] == "Hello world from test!"
    assert body["status"] == "DRAFT"
    assert body["user_id"] == user.id

    # Get post by ID
    post_id = body["id"]
    get_res = client.get(
        f"/api/v1/posts/{post_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_res.status_code == 200
    assert get_res.json()["content"] == "Hello world from test!"


def test_social_account_ownership_check(client, db_session: Session):
    token_a, user_a, account_a = _setup_user_and_social(client, db_session, "user_a@example.com")
    token_b, user_b, account_b = _setup_user_and_social(client, db_session, "user_b@example.com")

    # User A tries to create a post using User B's social account -> expects 403
    payload = {
        "content": "Trying to steal account!",
        "social_account_id": account_b.id,
    }
    res = client.post(
        "/api/v1/posts",
        json=payload,
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res.status_code == 403


def test_post_ownership_check(client, db_session: Session):
    token_a, user_a, account_a = _setup_user_and_social(client, db_session, "user_a@example.com")
    token_b, user_b, account_b = _setup_user_and_social(client, db_session, "user_b@example.com")

    # Create post for User A
    post_a = Post(
        user_id=user_a.id,
        social_account_id=account_a.id,
        content="Post A",
        status=PostStatus.DRAFT,
    )
    db_session.add(post_a)
    db_session.commit()

    # User B tries to read/edit/delete User A's post -> expects 403
    get_res = client.get(
        f"/api/v1/posts/{post_a.id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert get_res.status_code == 403

    put_res = client.put(
        f"/api/v1/posts/{post_a.id}",
        json={"content": "Hacked content"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert put_res.status_code == 403

    del_res = client.delete(
        f"/api/v1/posts/{post_a.id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert del_res.status_code == 403


def test_update_and_delete_draft(client, db_session: Session):
    token, user, account = _setup_user_and_social(client, db_session)

    # Create post
    post = Post(
        user_id=user.id,
        social_account_id=account.id,
        content="Draft post",
        status=PostStatus.DRAFT,
    )
    db_session.add(post)
    db_session.commit()

    # Update draft
    put_res = client.put(
        f"/api/v1/posts/{post.id}",
        json={"content": "Updated content!"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert put_res.status_code == 200
    assert put_res.json()["content"] == "Updated content!"

    # Delete draft
    del_res = client.delete(
        f"/api/v1/posts/{post.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_res.status_code == 200
    assert db_session.get(Post, post.id) is None


def test_publish_immediately_success_mock(client, db_session: Session):
    token, user, account = _setup_user_and_social(client, db_session)

    # Create post
    post = Post(
        user_id=user.id,
        social_account_id=account.id,
        content="Testing publish!",
        status=PostStatus.DRAFT,
    )
    db_session.add(post)
    db_session.commit()

    # Publish immediate
    pub_res = client.post(
        f"/api/v1/posts/{post.id}/publish",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert pub_res.status_code == 200
    body = pub_res.json()
    assert body["status"] == "PUBLISHED"
    assert body["external_post_id"] == "mock-meta-post-id"


def test_publish_immediately_failure_mock(client, db_session: Session):
    token, user, account = _setup_user_and_social(client, db_session)

    # Modify encryption token to trigger decryption failure
    account.access_token_encrypted = "invalid-encrypted-token"
    db_session.add(account)
    db_session.commit()

    # Create post
    post = Post(
        user_id=user.id,
        social_account_id=account.id,
        content="Testing failed publish!",
        status=PostStatus.DRAFT,
    )
    db_session.add(post)
    db_session.commit()

    # Publish immediate
    pub_res = client.post(
        f"/api/v1/posts/{post.id}/publish",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert pub_res.status_code == 502
    
    # Reload and verify FAILED state
    db_session.refresh(post)
    assert post.status == PostStatus.FAILED
    assert post.error_message is not None


def test_double_publish_protection(client, db_session: Session):
    token, user, account = _setup_user_and_social(client, db_session)

    # Create a post in PUBLISHING status
    post = Post(
        user_id=user.id,
        social_account_id=account.id,
        content="Already publishing post",
        status=PostStatus.PUBLISHING,
    )
    db_session.add(post)
    db_session.commit()

    # Call publish -> expects 400 Bad Request
    pub_res = client.post(
        f"/api/v1/posts/{post.id}/publish",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert pub_res.status_code == 400
    assert "already publishing or published" in pub_res.json()["detail"]


def test_schedule_and_cancel_post(client, db_session: Session):
    token, user, account = _setup_user_and_social(client, db_session)

    post = Post(
        user_id=user.id,
        social_account_id=account.id,
        content="Draft to schedule",
        status=PostStatus.DRAFT,
    )
    db_session.add(post)
    db_session.commit()

    # Schedule post
    future_time = (datetime.now(UTC) + timedelta(hours=2)).isoformat()
    sch_res = client.post(
        f"/api/v1/posts/{post.id}/schedule",
        json={"scheduled_at": future_time},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert sch_res.status_code == 200
    assert sch_res.json()["status"] == "SCHEDULED"

    # Cancel post
    cnc_res = client.post(
        f"/api/v1/posts/{post.id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert cnc_res.status_code == 200
    assert cnc_res.json()["status"] == "CANCELLED"
