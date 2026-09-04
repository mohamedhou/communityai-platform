from __future__ import annotations

import os
import pytest
from sqlalchemy.orm import Session

# Set test environment defaults before imports
os.environ["SOCIAL_TOKEN_ENCRYPTION_KEY"] = "G3cZ84fJd9X2-vK8pQLt8G3cZ84fJd9X2-vK8pQLt8E="
os.environ["SOCIAL_MOCK_MODE"] = "true"

from app.core.config import get_settings
from app.core.encryption import encrypt_token
from app.models.inbox_message import InboxMessage, InboxMessageType, InboxSentiment
from app.models.user import User
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


def test_inbox_unauthenticated(client):
    endpoints = [
        ("GET", "/api/v1/inbox"),
        ("GET", "/api/v1/inbox/unread-count"),
        ("GET", "/api/v1/inbox/1"),
        ("PATCH", "/api/v1/inbox/1/read"),
        ("PATCH", "/api/v1/inbox/1/resolve"),
        ("POST", "/api/v1/inbox/1/suggest-reply"),
        ("POST", "/api/v1/inbox/1/reply"),
        ("POST", "/api/v1/inbox/seed-mock"),
    ]
    for method, path in endpoints:
        if method == "GET":
            res = client.get(path)
        elif method == "PATCH":
            res = client.patch(path, json={})
        elif method == "POST":
            res = client.post(path, json={})
        assert res.status_code == 401, f"Expected 401 for {method} {path}, got {res.status_code}"


def test_inbox_seed_mock_and_unread_count(client, db_session: Session):
    token, user, account = _setup_user_and_social(client, db_session, email="inbox_user1@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Seed mock interactions
    seed_res = client.post("/api/v1/inbox/seed-mock", headers=headers)
    assert seed_res.status_code == 201
    seeded = seed_res.json()
    assert len(seeded) == 5

    # Check unread count
    unread_res = client.get("/api/v1/inbox/unread-count", headers=headers)
    assert unread_res.status_code == 200
    # 4 of the 5 seeded are unread
    assert unread_res.json()["unread_count"] == 4


def test_inbox_seed_mock_disabled(client, db_session: Session, monkeypatch):
    token, user, account = _setup_user_and_social(client, db_session, email="inbox_nomock@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    settings = get_settings()
    monkeypatch.setattr(settings, "social_mock_mode", False)

    res = client.post("/api/v1/inbox/seed-mock", headers=headers)
    assert res.status_code == 403
    assert "disabled" in res.json()["detail"].lower()


def test_inbox_list_and_ownership(client, db_session: Session):
    token_a, user_a, acc_a = _setup_user_and_social(client, db_session, email="user_a@example.com")
    token_b, user_b, acc_b = _setup_user_and_social(client, db_session, email="user_b@example.com")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Seed User A
    client.post("/api/v1/inbox/seed-mock", headers=headers_a)

    # User A lists messages -> sees 5
    res_a = client.get("/api/v1/inbox", headers=headers_a)
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert data_a["total"] == 5
    assert len(data_a["items"]) == 5

    # User B lists messages -> sees 0
    res_b = client.get("/api/v1/inbox", headers=headers_b)
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["total"] == 0
    assert len(data_b["items"]) == 0


def test_inbox_item_ownership_protection(client, db_session: Session):
    token_a, user_a, acc_a = _setup_user_and_social(client, db_session, email="owner_a@example.com")
    token_b, user_b, acc_b = _setup_user_and_social(client, db_session, email="intruder_b@example.com")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Seed User A
    seed_res = client.post("/api/v1/inbox/seed-mock", headers=headers_a)
    msg_id = seed_res.json()[0]["id"]

    # Intruder User B attempts to access or modify User A's message -> 404
    assert client.get(f"/api/v1/inbox/{msg_id}", headers=headers_b).status_code == 404
    assert client.patch(f"/api/v1/inbox/{msg_id}/read", headers=headers_b, json={"is_read": True}).status_code == 404
    assert client.patch(f"/api/v1/inbox/{msg_id}/resolve", headers=headers_b, json={"is_resolved": True}).status_code == 404
    assert client.post(f"/api/v1/inbox/{msg_id}/suggest-reply", headers=headers_b, json={}).status_code == 404
    assert client.post(f"/api/v1/inbox/{msg_id}/reply", headers=headers_b, json={"content": "Unauthorized reply"}).status_code == 404


def test_inbox_filters(client, db_session: Session):
    token, user, account = _setup_user_and_social(client, db_session, email="filter_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    client.post("/api/v1/inbox/seed-mock", headers=headers)

    # Filter by type=COMMENT
    res_type = client.get("/api/v1/inbox?type=COMMENT", headers=headers)
    assert res_type.status_code == 200
    assert all(item["type"] == "COMMENT" for item in res_type.json()["items"])
    assert res_type.json()["total"] == 3

    # Filter by sentiment=NEGATIVE
    res_neg = client.get("/api/v1/inbox?sentiment=NEGATIVE", headers=headers)
    assert res_neg.status_code == 200
    assert all(item["sentiment"] == "NEGATIVE" for item in res_neg.json()["items"])
    assert res_neg.json()["total"] == 1

    # Filter by sentiment=POSITIVE
    res_pos = client.get("/api/v1/inbox?sentiment=POSITIVE", headers=headers)
    assert res_pos.status_code == 200
    assert all(item["sentiment"] == "POSITIVE" for item in res_pos.json()["items"])
    assert res_pos.json()["total"] == 2

    # Filter by is_read=true
    res_read = client.get("/api/v1/inbox?is_read=true", headers=headers)
    assert res_read.status_code == 200
    assert res_read.json()["total"] == 1

    # Filter by is_resolved=false
    res_unres = client.get("/api/v1/inbox?is_resolved=false", headers=headers)
    assert res_unres.status_code == 200
    assert res_unres.json()["total"] == 5

    # Filter by platform
    res_plat = client.get("/api/v1/inbox?platform=facebook", headers=headers)
    assert res_plat.status_code == 200
    assert res_plat.json()["total"] == 5


def test_inbox_search(client, db_session: Session):
    token, user, account = _setup_user_and_social(client, db_session, email="search_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    client.post("/api/v1/inbox/seed-mock", headers=headers)

    # Search for "export"
    res_search = client.get("/api/v1/inbox?search=export", headers=headers)
    assert res_search.status_code == 200
    data = res_search.json()
    assert data["total"] == 1
    assert "export" in data["items"][0]["content"].lower()

    # Search by sender name "Sophie"
    res_sender = client.get("/api/v1/inbox?search=Sophie", headers=headers)
    assert res_sender.status_code == 200
    data = res_sender.json()
    assert data["total"] == 1
    assert "Sophie" in data["items"][0]["sender_name"]


def test_inbox_mark_read_and_resolved(client, db_session: Session):
    token, user, account = _setup_user_and_social(client, db_session, email="mark_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    seed_res = client.post("/api/v1/inbox/seed-mock", headers=headers)
    msg = seed_res.json()[0]
    msg_id = msg["id"]

    # Mark as Read
    res_read = client.patch(f"/api/v1/inbox/{msg_id}/read", headers=headers, json={"is_read": True})
    assert res_read.status_code == 200
    assert res_read.json()["is_read"] is True

    # Mark as Unread
    res_unread = client.patch(f"/api/v1/inbox/{msg_id}/read", headers=headers, json={"is_read": False})
    assert res_unread.status_code == 200
    assert res_unread.json()["is_read"] is False

    # Mark as Resolved
    res_resolved = client.patch(f"/api/v1/inbox/{msg_id}/resolve", headers=headers, json={"is_resolved": True})
    assert res_resolved.status_code == 200
    assert res_resolved.json()["is_resolved"] is True

    # Mark as Unresolved
    res_unresolved = client.patch(f"/api/v1/inbox/{msg_id}/resolve", headers=headers, json={"is_resolved": False})
    assert res_unresolved.status_code == 200
    assert res_unresolved.json()["is_resolved"] is False


def test_inbox_suggest_reply(client, db_session: Session):
    token, user, account = _setup_user_and_social(client, db_session, email="suggest_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    seed_res = client.post("/api/v1/inbox/seed-mock", headers=headers)
    # The first item is negative comment
    neg_msg = seed_res.json()[0]
    msg_id = neg_msg["id"]

    suggest_res = client.post(
        f"/api/v1/inbox/{msg_id}/suggest-reply",
        headers=headers,
        json={"tone": "PROFESSIONAL", "instructions": "Be very polite and offer direct assistance"},
    )
    assert suggest_res.status_code == 200
    ai_data = suggest_res.json()
    assert "content" in ai_data
    assert len(ai_data["content"]) > 0
    assert ai_data["action"] == "SUGGEST_REPLY"

    # Verify that message was NOT marked as replied or resolved by suggestion
    get_res = client.get(f"/api/v1/inbox/{msg_id}", headers=headers)
    assert get_res.status_code == 200
    msg_data = get_res.json()
    assert msg_data["replied_at"] is None
    assert msg_data["is_resolved"] is False


def test_inbox_send_reply_and_security(client, db_session: Session):
    token, user, account = _setup_user_and_social(client, db_session, email="reply_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    seed_res = client.post("/api/v1/inbox/seed-mock", headers=headers)
    msg_id = seed_res.json()[0]["id"]

    reply_payload = {"content": "Merci pour votre retour, notre équipe a résolu le problème d'export !"}
    reply_res = client.post(f"/api/v1/inbox/{msg_id}/reply", headers=headers, json=reply_payload)
    assert reply_res.status_code == 200
    res_data = reply_res.json()

    assert res_data["is_resolved"] is True
    assert res_data["is_read"] is True
    assert res_data["replied_at"] is not None

    # CRITICAL SECURITY CHECK: No encrypted or raw tokens present in response
    assert "access_token" not in res_data
    assert "access_token_encrypted" not in res_data
    assert "refresh_token" not in res_data
    assert "refresh_token_encrypted" not in res_data
    if res_data.get("social_account"):
        assert "access_token" not in res_data["social_account"]
        assert "access_token_encrypted" not in res_data["social_account"]
