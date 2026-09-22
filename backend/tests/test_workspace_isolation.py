from __future__ import annotations

import os
from datetime import UTC, date, datetime, timedelta
import pytest
from sqlalchemy.orm import Session
from sqlalchemy import select

os.environ["SOCIAL_TOKEN_ENCRYPTION_KEY"] = "G3cZ84fJd9X2-vK8pQLt8G3cZ84fJd9X2-vK8pQLt8E="
os.environ["SOCIAL_MOCK_MODE"] = "true"

from app.core.encryption import encrypt_token
from app.models.analytics_snapshot import AnalyticsSnapshot
from app.models.inbox_message import InboxMessage, InboxMessageType
from app.models.post import Post, PostStatus
from app.models.user import User
from app.models.workspace import WorkspaceMember
from app.social.models import OAuthState, SocialAccount



def _register_and_login(client, email: str, first_name: str = "Test", last_name: str = "User") -> tuple[str, dict]:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "first_name": first_name,
            "last_name": last_name,
        },
    )
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPassword123!"},
    )
    token = res.json()["access_token"]
    return token, {"Authorization": f"Bearer {token}"}


def test_cross_workspace_social_account_isolation(client, db_session: Session):
    token_1, headers_1 = _register_and_login(client, "ws1_user@example.com", "User", "One")
    token_2, headers_2 = _register_and_login(client, "ws2_user@example.com", "User", "Two")

    user_1 = db_session.scalar(select(User).where(User.email == "ws1_user@example.com"))
    user_2 = db_session.scalar(select(User).where(User.email == "ws2_user@example.com"))

    member_1 = db_session.scalar(select(WorkspaceMember).where(WorkspaceMember.user_id == user_1.id))
    member_2 = db_session.scalar(select(WorkspaceMember).where(WorkspaceMember.user_id == user_2.id))

    # Create account in Workspace 1
    sa_1 = SocialAccount(
        workspace_id=member_1.workspace_id,
        user_id=user_1.id,
        platform="facebook",
        provider="meta",
        external_account_id=f"fb-acc-{user_1.id}",
        account_name="WS1 Facebook Page",
        access_token_encrypted=encrypt_token("mock-token-1"),
        status="CONNECTED",
    )
    db_session.add(sa_1)
    db_session.commit()
    db_session.refresh(sa_1)

    # Workspace 1 sees it
    res_1 = client.get("/api/v1/social-accounts", headers=headers_1)
    assert res_1.status_code == 200
    assert len(res_1.json()) == 1
    assert res_1.json()[0]["account_name"] == "WS1 Facebook Page"

    # Workspace 2 does NOT see it
    res_2 = client.get("/api/v1/social-accounts", headers=headers_2)
    assert res_2.status_code == 200
    assert len(res_2.json()) == 0

    # User 2 probing disconnect on User 1's account -> 403 Forbidden
    del_res = client.delete(f"/api/v1/social-accounts/{sa_1.id}", headers=headers_2)
    assert del_res.status_code == 403

    # User 2 probing refresh on User 1's account -> 403 Forbidden
    ref_res = client.post(f"/api/v1/social-accounts/{sa_1.id}/refresh", headers=headers_2)
    assert ref_res.status_code == 403


def test_cross_workspace_post_isolation_and_same_workspace_collaboration(client, db_session: Session):
    token_owner, headers_owner = _register_and_login(client, "owner_post@example.com", "Owner", "Post")
    owner_user = db_session.scalar(select(User).where(User.email == "owner_post@example.com"))
    owner_member = db_session.scalar(select(WorkspaceMember).where(WorkspaceMember.user_id == owner_user.id))

    # Invite collaborator to same workspace
    inv_res = client.post(
        "/api/v1/workspace/invitations",
        headers=headers_owner,
        json={"email": "collab_post@example.com", "role": "COMMUNITY_MANAGER"},
    )
    token_str = inv_res.json()["invitation_url"].split("/")[-1]
    token_collab, headers_collab = _register_and_login(client, "collab_post@example.com", "Collab", "Post")
    client.post(f"/api/v1/workspace/invitations/{token_str}/accept", headers=headers_collab)

    # Unrelated user in Workspace 2
    token_other, headers_other = _register_and_login(client, "other_post@example.com", "Other", "Post")

    # Add social account to Workspace 1
    sa = SocialAccount(
        workspace_id=owner_member.workspace_id,
        user_id=owner_user.id,
        platform="facebook",
        provider="meta",
        external_account_id=f"fb-acc-{owner_user.id}",
        account_name="Team Facebook",
        access_token_encrypted=encrypt_token("mock-token"),
        status="CONNECTED",
    )
    db_session.add(sa)
    db_session.commit()
    db_session.refresh(sa)

    # Owner creates post in Workspace 1
    create_res = client.post(
        "/api/v1/posts",
        headers=headers_owner,
        json={
            "social_account_id": sa.id,
            "content": "Collaborative post from Workspace 1",
        },
    )
    assert create_res.status_code == 201
    post_id = create_res.json()["id"]

    # Collaborator in same workspace CAN see and edit the post
    collab_ws_headers = {**headers_collab, "X-Workspace-ID": str(owner_member.workspace_id)}
    collab_list = client.get("/api/v1/posts", headers=collab_ws_headers)
    assert collab_list.status_code == 200
    assert len(collab_list.json()) == 1

    edit_res = client.put(
        f"/api/v1/posts/{post_id}",
        headers=collab_ws_headers,
        json={
            "content": "Updated by collaborator in same workspace",
            "social_account_id": sa.id,
        },
    )
    assert edit_res.status_code == 200
    assert edit_res.json()["content"] == "Updated by collaborator in same workspace"


    # User in Workspace 2 CANNOT see the post
    other_list = client.get("/api/v1/posts", headers=headers_other)
    assert other_list.status_code == 200
    assert len(other_list.json()) == 0

    # User in Workspace 2 probing edit -> 403 Forbidden
    other_edit = client.put(
        f"/api/v1/posts/{post_id}",
        headers=headers_other,
        json={"content": "Malicious edit attempt"},
    )
    assert other_edit.status_code == 403

    # User in Workspace 2 probing publish -> 403 Forbidden
    other_pub = client.post(f"/api/v1/posts/{post_id}/publish", headers=headers_other)
    assert other_pub.status_code == 403

    # User in Workspace 2 probing delete -> 403 Forbidden
    other_del = client.delete(f"/api/v1/posts/{post_id}", headers=headers_other)
    assert other_del.status_code == 403


def test_cross_workspace_inbox_isolation(client, db_session: Session):
    token_1, headers_1 = _register_and_login(client, "inbox_ws1@example.com", "Inbox", "One")
    token_2, headers_2 = _register_and_login(client, "inbox_ws2@example.com", "Inbox", "Two")

    user_1 = db_session.scalar(select(User).where(User.email == "inbox_ws1@example.com"))
    member_1 = db_session.scalar(select(WorkspaceMember).where(WorkspaceMember.user_id == user_1.id))

    sa_1 = SocialAccount(
        workspace_id=member_1.workspace_id,
        user_id=user_1.id,
        platform="facebook",
        provider="meta",
        external_account_id=f"fb-inbox-{user_1.id}",
        account_name="WS1 Inbox Page",
        access_token_encrypted=encrypt_token("mock-token-1"),
        status="CONNECTED",
    )
    db_session.add(sa_1)
    db_session.commit()
    db_session.refresh(sa_1)

    # Add inbox message in Workspace 1
    msg = InboxMessage(
        workspace_id=member_1.workspace_id,
        user_id=user_1.id,
        social_account_id=sa_1.id,
        external_id="msg-ext-101",
        type=InboxMessageType.MESSAGE,
        sender_name="Customer A",
        sender_external_id="customera",
        content="Hello from customer A",
        is_read=False,
        is_resolved=False,
    )
    db_session.add(msg)
    db_session.commit()
    db_session.refresh(msg)


    # Workspace 1 sees it
    res_1 = client.get("/api/v1/inbox", headers=headers_1)
    assert res_1.status_code == 200
    assert len(res_1.json()["items"]) == 1

    # Workspace 2 does NOT see it
    res_2 = client.get("/api/v1/inbox", headers=headers_2)
    assert res_2.status_code == 200
    assert len(res_2.json()["items"]) == 0

    # User 2 probing mark-read -> 404 Not Found (or 403)
    probe_patch = client.patch(
        f"/api/v1/inbox/{msg.id}/read",
        headers=headers_2,
        json={"is_read": True},
    )
    assert probe_patch.status_code in (403, 404)

    # User 2 probing reply -> 404 Not Found (or 403)
    probe_reply = client.post(
        f"/api/v1/inbox/{msg.id}/reply",
        headers=headers_2,
        json={"content": "Unauthorized reply"},
    )
    assert probe_reply.status_code in (403, 404)


def test_cross_workspace_analytics_and_reporting_isolation(client, db_session: Session):
    token_1, headers_1 = _register_and_login(client, "ana_ws1@example.com", "Ana", "One")
    token_2, headers_2 = _register_and_login(client, "ana_ws2@example.com", "Ana", "Two")

    user_1 = db_session.scalar(select(User).where(User.email == "ana_ws1@example.com"))
    user_2 = db_session.scalar(select(User).where(User.email == "ana_ws2@example.com"))
    member_1 = db_session.scalar(select(WorkspaceMember).where(WorkspaceMember.user_id == user_1.id))
    member_2 = db_session.scalar(select(WorkspaceMember).where(WorkspaceMember.user_id == user_2.id))

    sa_1 = SocialAccount(
        workspace_id=member_1.workspace_id,
        user_id=user_1.id,
        platform="facebook",
        provider="meta",
        external_account_id=f"fb-ana-{user_1.id}",
        account_name="WS1 Ana Page",
        access_token_encrypted=encrypt_token("mock-token-1"),
        status="CONNECTED",
    )
    db_session.add(sa_1)

    sa_2 = SocialAccount(
        workspace_id=member_2.workspace_id,
        user_id=user_2.id,
        platform="facebook",
        provider="meta",
        external_account_id=f"fb-ana-{user_2.id}",
        account_name="WS2 Ana Page",
        access_token_encrypted=encrypt_token("mock-token-2"),
        status="CONNECTED",
    )
    db_session.add(sa_2)
    db_session.commit()
    db_session.refresh(sa_1)
    db_session.refresh(sa_2)

    today = date.today()
    snapshot_1 = AnalyticsSnapshot(
        workspace_id=member_1.workspace_id,
        user_id=user_1.id,
        social_account_id=sa_1.id,
        date=today,
        followers=5000,
        follower_growth=50,
        impressions=10000,
        reach=8000,
        engagement=900,
        likes=500,
        comments=200,
        shares=100,
        clicks=100,
    )
    snapshot_2 = AnalyticsSnapshot(
        workspace_id=member_2.workspace_id,
        user_id=user_2.id,
        social_account_id=sa_2.id,
        date=today,
        followers=100,
        follower_growth=5,
        impressions=200,
        reach=150,
        engagement=20,
        likes=10,
        comments=5,
        shares=3,
        clicks=2,
    )
    db_session.add(snapshot_1)
    db_session.add(snapshot_2)
    db_session.commit()

    # Workspace 1 summary has 5000 followers
    ana_1 = client.get(
        f"/api/v1/analytics/summary?start_date={today - timedelta(days=7)}&end_date={today}",
        headers=headers_1,
    )
    assert ana_1.status_code == 200
    assert ana_1.json()["kpis"]["total_followers"] == 5000

    # Workspace 2 summary has 100 followers
    ana_2 = client.get(
        f"/api/v1/analytics/summary?start_date={today - timedelta(days=7)}&end_date={today}",
        headers=headers_2,
    )
    assert ana_2.status_code == 200
    assert ana_2.json()["kpis"]["total_followers"] == 100

    # Reporting preview in Workspace 2 only sees Workspace 2 data
    rep_2 = client.get(
        f"/api/v1/reports/preview?start_date={today - timedelta(days=7)}&end_date={today}",
        headers=headers_2,
    )
    assert rep_2.status_code == 200
    assert rep_2.json()["kpis"]["total_followers"] == 100
    assert "WS1 Ana Page" not in rep_2.json()["accounts"]
    assert "WS2 Ana Page" in rep_2.json()["accounts"]


def test_header_workspace_id_validation(client, db_session: Session):
    token_1, headers_1 = _register_and_login(client, "hdr_ws1@example.com", "Hdr", "One")
    token_2, headers_2 = _register_and_login(client, "hdr_ws2@example.com", "Hdr", "Two")

    user_1 = db_session.scalar(select(User).where(User.email == "hdr_ws1@example.com"))
    member_1 = db_session.scalar(select(WorkspaceMember).where(WorkspaceMember.user_id == user_1.id))

    # User 1 passes their own valid X-Workspace-ID header
    valid_headers = {**headers_1, "X-Workspace-ID": str(member_1.workspace_id)}
    res_valid = client.get("/api/v1/workspace/members", headers=valid_headers)
    assert res_valid.status_code == 200

    # User 2 attempts to send X-Workspace-ID of Workspace 1 -> blocked with 403
    spoofed_headers = {**headers_2, "X-Workspace-ID": str(member_1.workspace_id)}
    res_spoofed = client.get("/api/v1/workspace/members", headers=spoofed_headers)
    assert res_spoofed.status_code == 403
    assert "Access to specified workspace is forbidden" in res_spoofed.json()["detail"]


def test_oauth_state_workspace_binding(client, db_session: Session):
    token, headers = _register_and_login(client, "oauth_owner@example.com", "OAuth", "Owner")
    user = db_session.scalar(select(User).where(User.email == "oauth_owner@example.com"))
    member = db_session.scalar(select(WorkspaceMember).where(WorkspaceMember.user_id == user.id))

    # Initiating OAuth persists workspace_id
    auth_res = client.get("/api/v1/social-accounts/meta/connect", headers=headers)
    assert auth_res.status_code == 200
    auth_url = auth_res.json()["url"]
    state = auth_url.split("state=")[-1]

    oauth_state = db_session.scalar(select(OAuthState).where(OAuthState.state == state))
    assert oauth_state is not None
    assert oauth_state.workspace_id == member.workspace_id
    assert oauth_state.user_id == user.id

