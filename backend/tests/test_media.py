from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.encryption import encrypt_token
from app.core.config import get_settings
from app.models.post import Post, PostApprovalStatus, PostStatus
from app.models.user import User
from app.models.workspace import WorkspaceMember
from app.social.models import SocialAccount


def _register_and_login(client, email: str) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "first_name": "Media",
            "last_name": "Tester",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPassword123!"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _account(db: Session, workspace_id: int, user_id: int, suffix: str = "") -> SocialAccount:
    account = SocialAccount(
        workspace_id=workspace_id,
        user_id=user_id,
        platform="facebook",
        provider="meta",
        external_account_id=f"media-account-{workspace_id}-{user_id}-{suffix}",
        account_name="Media Test Account",
        access_token_encrypted=encrypt_token("mock-token"),
        status="CONNECTED",
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def _workspace_id(db: Session, email: str) -> int:
    user = db.scalar(select(User).where(User.email == email))
    member = db.scalar(select(WorkspaceMember).where(WorkspaceMember.user_id == user.id))
    return member.workspace_id


def test_valid_image_and_video_upload(client, db_session: Session):
    headers = _register_and_login(client, "media-valid@example.com")
    image = client.post(
        "/api/v1/media",
        headers=headers,
        files={"file": ("photo.png", b"\x89PNG\r\n\x1a\nimage", "image/png")},
    )
    assert image.status_code == 201
    assert image.json()["media_kind"] == "IMAGE"

    video = client.post(
        "/api/v1/media",
        headers=headers,
        files={"file": ("clip.mp4", b"\x00\x00\x00\x18ftypmp42video", "video/mp4")},
    )
    assert video.status_code == 201
    assert video.json()["media_kind"] == "VIDEO"
    assert client.get(video.json()["content_url"], headers=headers).status_code == 200


def test_media_validation_rejects_unsupported_mime_and_oversized(client, monkeypatch):
    headers = _register_and_login(client, "media-validation@example.com")
    unsupported = client.post(
        "/api/v1/media",
        headers=headers,
        files={"file": ("file.exe", b"MZbad", "application/octet-stream")},
    )
    assert unsupported.status_code == 400

    invalid_mime = client.post(
        "/api/v1/media",
        headers=headers,
        files={"file": ("photo.png", b"\x89PNG\r\n\x1a\nimage", "image/jpeg")},
    )
    assert invalid_mime.status_code == 400

    monkeypatch.setenv("MEDIA_MAX_UPLOAD_BYTES", "10")
    get_settings.cache_clear()
    oversized = client.post(
        "/api/v1/media",
        headers=headers,
        files={"file": ("photo.png", b"\x89PNG\r\n\x1a\n123456789", "image/png")},
    )
    assert oversized.status_code == 400
    get_settings.cache_clear()


def test_media_filename_is_sanitized_and_workspace_isolation_enforced(client, db_session: Session):
    headers_a = _register_and_login(client, "media-owner-a@example.com")
    uploaded = client.post(
        "/api/v1/media",
        headers=headers_a,
        files={"file": ("../../outside.png", b"\x89PNG\r\n\x1a\nimage", "image/png")},
    )
    assert uploaded.status_code == 201
    body = uploaded.json()
    assert body["original_filename"] == "outside.png"
    assert ".." not in body["content_url"]
    assert client.get("/api/v1/media", headers=headers_a).json()[0]["id"] == body["id"]

    headers_b = _register_and_login(client, "media-owner-b@example.com")
    assert client.get(f"/api/v1/media/{body['id']}", headers=headers_b).status_code == 404
    assert client.get(f"/api/v1/media/{body['id']}/content", headers=headers_b).status_code == 404
    assert client.delete(f"/api/v1/media/{body['id']}", headers=headers_b).status_code == 404


def test_media_can_be_attached_replaced_removed_and_invalidates_approval(client, db_session: Session):
    headers = _register_and_login(client, "media-post@example.com")
    user = db_session.scalar(select(User).where(User.email == "media-post@example.com"))
    member = db_session.scalar(select(WorkspaceMember).where(WorkspaceMember.user_id == user.id))
    account = _account(db_session, member.workspace_id, user.id)
    first = client.post(
        "/api/v1/media",
        headers=headers,
        files={"file": ("first.png", b"\x89PNG\r\n\x1a\nfirst", "image/png")},
    ).json()
    second = client.post(
        "/api/v1/media",
        headers=headers,
        files={"file": ("second.png", b"\x89PNG\r\n\x1a\nsecond", "image/png")},
    ).json()

    post = client.post(
        "/api/v1/posts",
        headers=headers,
        json={"content": "Media post", "social_account_id": account.id, "media_asset_id": first["id"]},
    )
    assert post.status_code == 201
    assert post.json()["media_asset_id"] == first["id"]

    updated = client.put(
        f"/api/v1/posts/{post.json()['id']}",
        headers=headers,
        json={"media_asset_id": second["id"]},
    )
    assert updated.status_code == 200
    assert updated.json()["media_asset_id"] == second["id"]

    removed = client.put(
        f"/api/v1/posts/{post.json()['id']}",
        headers=headers,
        json={"media_asset_id": None},
    )
    assert removed.status_code == 200
    assert removed.json()["media_asset_id"] is None

    # Reattach and exercise scheduled approved invalidation.
    client.put(f"/api/v1/posts/{post.json()['id']}", headers=headers, json={"media_asset_id": first["id"]})
    client.post(f"/api/v1/posts/{post.json()['id']}/submit-review", headers=headers)
    client.post(f"/api/v1/posts/{post.json()['id']}/approve", headers=headers)
    future = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    client.post(f"/api/v1/posts/{post.json()['id']}/schedule", headers=headers, json={"scheduled_at": future})

    changed = client.put(
        f"/api/v1/posts/{post.json()['id']}",
        headers=headers,
        json={"media_asset_id": second["id"]},
    )
    assert changed.status_code == 200
    assert changed.json()["approval_status"] == "REJECTED"
    assert changed.json()["status"] == "DRAFT"
    assert changed.json()["scheduled_at"] is None


def test_cross_workspace_media_attachment_is_rejected(client, db_session: Session):
    headers_a = _register_and_login(client, "media-attach-a@example.com")
    asset = client.post(
        "/api/v1/media",
        headers=headers_a,
        files={"file": ("private.png", b"\x89PNG\r\n\x1a\nprivate", "image/png")},
    ).json()

    headers_b = _register_and_login(client, "media-attach-b@example.com")
    user_b = db_session.scalar(select(User).where(User.email == "media-attach-b@example.com"))
    member_b = db_session.scalar(select(WorkspaceMember).where(WorkspaceMember.user_id == user_b.id))
    account_b = _account(db_session, member_b.workspace_id, user_b.id)
    post = client.post(
        "/api/v1/posts",
        headers=headers_b,
        json={"content": "Cross workspace", "social_account_id": account_b.id},
    ).json()
    response = client.put(
        f"/api/v1/posts/{post['id']}",
        headers=headers_b,
        json={"media_asset_id": asset["id"]},
    )
    assert response.status_code == 403
