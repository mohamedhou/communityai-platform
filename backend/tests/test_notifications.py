from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
import pytest
from sqlalchemy.orm import Session

# Set test environment defaults before imports
os.environ["SOCIAL_TOKEN_ENCRYPTION_KEY"] = "G3cZ84fJd9X2-vK8pQLt8G3cZ84fJd9X2-vK8pQLt8E="
os.environ["SOCIAL_MOCK_MODE"] = "true"

from app.core.encryption import encrypt_token
from app.models.notification import Notification, NotificationSeverity, NotificationType
from app.models.user import User
from app.schemas.notification import NotificationCreate, validate_internal_action_url
from app.services.notification_service import NotificationService
from app.services.post_service import PostService
from app.services.inbox_service import InboxService
from app.social.models import SocialAccount


def _register_payload(email: str = "alice_notif@example.com") -> dict[str, str]:
    return {
        "email": email,
        "password": "StrongPass123",
        "first_name": "Alice",
        "last_name": "Martin",
    }


def _login(client, email: str = "alice_notif@example.com", password: str = "StrongPass123"):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )


def _setup_user(client, db_session: Session, email: str = "alice_notif@example.com"):
    client.post("/api/v1/auth/register", json=_register_payload(email))
    token = _login(client, email=email).json()["access_token"]
    user = db_session.query(User).filter(User.email == email).one()
    return token, user


def test_notifications_unauthenticated(client):
    endpoints = [
        ("GET", "/api/v1/notifications"),
        ("GET", "/api/v1/notifications/unread-count"),
        ("GET", "/api/v1/notifications/1"),
        ("PATCH", "/api/v1/notifications/1/read"),
        ("PATCH", "/api/v1/notifications/read-all"),
        ("DELETE", "/api/v1/notifications/1"),
    ]
    for method, path in endpoints:
        if method == "GET":
            res = client.get(path)
        elif method == "PATCH":
            res = client.patch(path, json={})
        elif method == "DELETE":
            res = client.delete(path)
        assert res.status_code == 401, f"Expected 401 for {method} {path}, got {res.status_code}"


def test_list_notifications_and_unread_count(client, db_session: Session):
    token, user = _setup_user(client, db_session, email="list_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    service = NotificationService()
    # Create 3 notifications: 2 unread, 1 read
    n1 = service.create_notification(
        db_session,
        NotificationCreate(
            user_id=user.id,
            type=NotificationType.POST_PUBLISHED,
            title="Post Published",
            message="Post #1 published successfully",
            severity=NotificationSeverity.SUCCESS,
            action_url="/posts",
        ),
    )
    n2 = service.create_notification(
        db_session,
        NotificationCreate(
            user_id=user.id,
            type=NotificationType.INBOX_MESSAGE,
            title="New Inbox Message",
            message="Message from Sophie",
            severity=NotificationSeverity.INFO,
            action_url="/inbox",
        ),
    )
    n3 = service.create_notification(
        db_session,
        NotificationCreate(
            user_id=user.id,
            type=NotificationType.POST_FAILED,
            title="Post Failed",
            message="Post #2 failed",
            severity=NotificationSeverity.ERROR,
            action_url="/posts",
        ),
    )
    service.mark_read(db_session, notification_id=n3.id, user_id=user.id, is_read=True)

    # Check unread count endpoint
    res_unread = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert res_unread.status_code == 200
    assert res_unread.json()["unread_count"] == 2

    # Check list endpoint
    res_list = client.get("/api/v1/notifications", headers=headers)
    assert res_list.status_code == 200
    data = res_list.json()
    assert data["total"] == 3
    assert data["unread_count"] == 2
    assert len(data["items"]) == 3
    assert data["page"] == 1
    assert data["limit"] == 50


def test_no_user_id_in_response_and_no_secrets(client, db_session: Session):
    token, user = _setup_user(client, db_session, email="security_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    service = NotificationService()
    n = service.create_notification(
        db_session,
        NotificationCreate(
            user_id=user.id,
            type=NotificationType.SYSTEM,
            title="System Alert",
            message="Maintenance planned",
            severity=NotificationSeverity.INFO,
            action_url="/notifications",
        ),
    )

    res = client.get(f"/api/v1/notifications/{n.id}", headers=headers)
    assert res.status_code == 200
    item = res.json()

    # Verify user_id is NOT in response
    assert "user_id" not in item
    assert "password" not in item
    assert "token" not in item
    assert "access_token" not in item
    assert "refresh_token" not in item

    # Verify fields present
    assert item["id"] == n.id
    assert item["type"] == "SYSTEM"
    assert item["title"] == "System Alert"
    assert item["message"] == "Maintenance planned"
    assert item["severity"] == "INFO"
    assert item["is_read"] is False
    assert item["action_url"] == "/notifications"


def test_ownership_isolation(client, db_session: Session):
    token1, user1 = _setup_user(client, db_session, email="owner1@example.com")
    token2, user2 = _setup_user(client, db_session, email="owner2@example.com")

    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    service = NotificationService()
    n1 = service.create_notification(
        db_session,
        NotificationCreate(
            user_id=user1.id,
            type=NotificationType.POST_PUBLISHED,
            title="User 1 Post",
            message="User 1 private post",
        ),
    )

    # User 2 tries to GET User 1's notification -> 404
    res_get = client.get(f"/api/v1/notifications/{n1.id}", headers=headers2)
    assert res_get.status_code == 404
    assert res_get.json()["detail"] == "Notification not found"

    # User 2 tries to PATCH read User 1's notification -> 404
    res_patch = client.patch(f"/api/v1/notifications/{n1.id}/read", json={"is_read": True}, headers=headers2)
    assert res_patch.status_code == 404

    # User 2 tries to DELETE User 1's notification -> 404
    res_del = client.delete(f"/api/v1/notifications/{n1.id}", headers=headers2)
    assert res_del.status_code == 404

    # User 2's list must not contain User 1's notification
    res_list2 = client.get("/api/v1/notifications", headers=headers2)
    assert res_list2.status_code == 200
    assert res_list2.json()["total"] == 0
    assert len(res_list2.json()["items"]) == 0


def test_mark_read_and_unread(client, db_session: Session):
    token, user = _setup_user(client, db_session, email="mark_read_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    service = NotificationService()
    n = service.create_notification(
        db_session,
        NotificationCreate(
            user_id=user.id,
            type=NotificationType.POST_PUBLISHED,
            title="Test Post",
            message="Test message",
        ),
    )
    assert n.is_read is False

    # Mark as read
    res_read = client.patch(f"/api/v1/notifications/{n.id}/read", json={"is_read": True}, headers=headers)
    assert res_read.status_code == 200
    assert res_read.json()["is_read"] is True
    assert res_read.json()["read_at"] is not None

    # Mark as unread
    res_unread = client.patch(f"/api/v1/notifications/{n.id}/read", json={"is_read": False}, headers=headers)
    assert res_unread.status_code == 200
    assert res_unread.json()["is_read"] is False
    assert res_unread.json()["read_at"] is None


def test_mark_all_read(client, db_session: Session):
    token, user = _setup_user(client, db_session, email="mark_all_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    service = NotificationService()
    for i in range(4):
        service.create_notification(
            db_session,
            NotificationCreate(
                user_id=user.id,
                type=NotificationType.SYSTEM,
                title=f"System #{i}",
                message=f"Notice #{i}",
            ),
        )

    res_unread_before = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert res_unread_before.json()["unread_count"] == 4

    # Mark all read
    res_all = client.patch("/api/v1/notifications/read-all", headers=headers)
    assert res_all.status_code == 200
    assert res_all.json()["success"] is True
    assert res_all.json()["marked_count"] == 4

    # Unread count is now 0
    res_unread_after = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert res_unread_after.json()["unread_count"] == 0


def test_delete_notification(client, db_session: Session):
    token, user = _setup_user(client, db_session, email="delete_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    service = NotificationService()
    n = service.create_notification(
        db_session,
        NotificationCreate(
            user_id=user.id,
            type=NotificationType.AI_SUGGESTION,
            title="AI Idea",
            message="Try this new hook",
        ),
    )

    # Delete
    res_del = client.delete(f"/api/v1/notifications/{n.id}", headers=headers)
    assert res_del.status_code == 204

    # Subsequent GET returns 404
    res_get = client.get(f"/api/v1/notifications/{n.id}", headers=headers)
    assert res_get.status_code == 404


def test_filtering_by_type_severity_and_read(client, db_session: Session):
    token, user = _setup_user(client, db_session, email="filter_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    service = NotificationService()
    service.create_notification(
        db_session,
        NotificationCreate(
            user_id=user.id,
            type=NotificationType.POST_PUBLISHED,
            title="Published",
            message="Success",
            severity=NotificationSeverity.SUCCESS,
        ),
    )
    service.create_notification(
        db_session,
        NotificationCreate(
            user_id=user.id,
            type=NotificationType.POST_FAILED,
            title="Failed",
            message="Error occurred",
            severity=NotificationSeverity.ERROR,
        ),
    )
    n_inbox = service.create_notification(
        db_session,
        NotificationCreate(
            user_id=user.id,
            type=NotificationType.INBOX_MESSAGE,
            title="Inbox",
            message="New reply",
            severity=NotificationSeverity.INFO,
        ),
    )
    service.mark_read(db_session, notification_id=n_inbox.id, user_id=user.id, is_read=True)

    # Filter by type=POST_PUBLISHED
    res_type = client.get("/api/v1/notifications?type=POST_PUBLISHED", headers=headers)
    assert res_type.status_code == 200
    assert res_type.json()["total"] == 1
    assert res_type.json()["items"][0]["type"] == "POST_PUBLISHED"

    # Filter by severity=ERROR
    res_sev = client.get("/api/v1/notifications?severity=ERROR", headers=headers)
    assert res_sev.status_code == 200
    assert res_sev.json()["total"] == 1
    assert res_sev.json()["items"][0]["severity"] == "ERROR"

    # Filter by is_read=true
    res_read = client.get("/api/v1/notifications?is_read=true", headers=headers)
    assert res_read.status_code == 200
    assert res_read.json()["total"] == 1
    assert res_read.json()["items"][0]["type"] == "INBOX_MESSAGE"

    # Filter by is_read=false
    res_unread = client.get("/api/v1/notifications?is_read=false", headers=headers)
    assert res_unread.status_code == 200
    assert res_unread.json()["total"] == 2


def test_internal_action_url_validation():
    # Valid internal URLs
    assert validate_internal_action_url("/posts") == "/posts"
    assert validate_internal_action_url("/calendar") == "/calendar"
    assert validate_internal_action_url("/inbox") == "/inbox"
    assert validate_internal_action_url("/analytics") == "/analytics"
    assert validate_internal_action_url("/social-accounts") == "/social-accounts"
    assert validate_internal_action_url("/ai") == "/ai"
    assert validate_internal_action_url("/notifications") == "/notifications"
    assert validate_internal_action_url(None) is None

    # Invalid external or malicious URLs
    invalid_urls = [
        "https://evil.com",
        "http://malicious.org/login",
        "//phishing.com",
        "javascript:alert(1)",
        "data:text/html,hack",
        "ftp://external.server",
        "relative-without-slash",
    ]
    for url in invalid_urls:
        with pytest.raises(ValueError):
            validate_internal_action_url(url)


def test_notification_helper_dispatchers(db_session: Session, client):
    token, user = _setup_user(client, db_session, email="helpers_user@example.com")
    service = NotificationService()

    n_pub = service.notify_post_published(db_session, user_id=user.id, post_id=101)
    assert n_pub.type == NotificationType.POST_PUBLISHED
    assert n_pub.severity == NotificationSeverity.SUCCESS
    assert n_pub.action_url == "/posts"
    assert n_pub.entity_type == "post"
    assert n_pub.entity_id == "101"

    n_fail = service.notify_post_failed(db_session, user_id=user.id, post_id=102, error_message="Network timeout")
    assert n_fail.type == NotificationType.POST_FAILED
    assert n_fail.severity == NotificationSeverity.ERROR
    assert "Network timeout" in n_fail.message

    n_sched = service.notify_post_scheduled(db_session, user_id=user.id, post_id=103, scheduled_at="2026-10-01 12:00")
    assert n_sched.type == NotificationType.POST_SCHEDULED
    assert n_sched.action_url == "/calendar"

    n_inbox = service.notify_inbox_message(db_session, user_id=user.id, message_id=201, sender_name="Marie Curie", preview="Bonjour !")
    assert n_inbox.type == NotificationType.INBOX_MESSAGE
    assert "Marie Curie" in n_inbox.message

    n_ai = service.notify_ai_suggestion(db_session, user_id=user.id)
    assert n_ai.type == NotificationType.AI_SUGGESTION
    assert n_ai.action_url == "/ai"

    n_soc = service.notify_social_account(db_session, user_id=user.id, title="Token Warning", message="LinkedIn token expires soon")
    assert n_soc.type == NotificationType.SOCIAL_ACCOUNT
    assert n_soc.severity == NotificationSeverity.WARNING

    n_ana = service.notify_analytics(db_session, user_id=user.id, title="Milestone", message="Reached 10k followers")
    assert n_ana.type == NotificationType.ANALYTICS

    n_sys = service.notify_system(db_session, user_id=user.id, title="System Notice", message="Platform update v2.0")
    assert n_sys.type == NotificationType.SYSTEM


def test_post_scheduling_and_publishing_integrations(client, db_session: Session):
    token, user = _setup_user(client, db_session, email="post_integration_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    account = SocialAccount(
        user_id=user.id,
        platform="facebook",
        provider="meta",
        external_account_id=f"fb-acc-{user.id}",
        account_name="Alice Page",
        access_token_encrypted=encrypt_token("mock-token"),
        status="CONNECTED",
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    post_service = PostService(db_session)
    post = post_service.create_post(
        user_id=user.id,
        social_account_id=account.id,
        content="Exciting news launching today!",
    )

    # Schedule post -> should generate POST_SCHEDULED notification
    future_time = datetime.now(UTC) + timedelta(days=2)
    post_service.schedule_post(user_id=user.id, post_id=post.id, scheduled_at=future_time)

    res_notif = client.get("/api/v1/notifications?type=POST_SCHEDULED", headers=headers)
    assert res_notif.status_code == 200
    assert res_notif.json()["total"] == 1
    assert res_notif.json()["items"][0]["entity_id"] == str(post.id)
