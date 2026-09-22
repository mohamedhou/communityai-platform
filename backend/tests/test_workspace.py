from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
import pytest
from sqlalchemy.orm import Session
from sqlalchemy import select

os.environ["SOCIAL_TOKEN_ENCRYPTION_KEY"] = "G3cZ84fJd9X2-vK8pQLt8G3cZ84fJd9X2-vK8pQLt8E="
os.environ["SOCIAL_MOCK_MODE"] = "true"

from app.models.user import User
from app.models.workspace import (
    MembershipStatus,
    Workspace,
    WorkspaceActivity,
    WorkspaceInvitation,
    WorkspaceMember,
    WorkspaceRole,
)
from app.models.notification import Notification


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


def test_list_workspace_members_and_default_workspace(client, db_session: Session):
    token, headers = _register_and_login(client, "owner@example.com", "Alice", "Owner")
    res = client.get("/api/v1/workspace/members", headers=headers)
    assert res.status_code == 200
    members = res.json()
    assert len(members) == 1
    assert members[0]["email"] == "owner@example.com"
    assert members[0]["role"] == "OWNER"
    assert members[0]["status"] == "ACTIVE"


def test_create_and_list_invitations(client, db_session: Session):
    token, headers = _register_and_login(client, "manager@example.com", "Bob", "Manager")

    # Invite a community manager
    invite_res = client.post(
        "/api/v1/workspace/invitations",
        headers=headers,
        json={"email": "cm@example.com", "role": "COMMUNITY_MANAGER"},
    )
    assert invite_res.status_code == 201
    invite_data = invite_res.json()
    assert invite_data["email"] == "cm@example.com"
    assert invite_data["role"] == "COMMUNITY_MANAGER"
    assert invite_data["status"] == "PENDING"
    assert invite_data["invitation_url"] is not None
    invitation_url = invite_data["invitation_url"]
    token_str = invitation_url.split("/")[-1]

    # Cannot invite as OWNER
    bad_invite = client.post(
        "/api/v1/workspace/invitations",
        headers=headers,
        json={"email": "hacker@example.com", "role": "OWNER"},
    )
    assert bad_invite.status_code == 400

    # Duplicate active invitation
    dup_res = client.post(
        "/api/v1/workspace/invitations",
        headers=headers,
        json={"email": "cm@example.com", "role": "CLIENT"},
    )
    assert dup_res.status_code == 409

    # List invitations
    list_res = client.get("/api/v1/workspace/invitations", headers=headers)
    assert list_res.status_code == 200
    invitations = list_res.json()
    assert len(invitations) == 1
    assert invitations[0]["email"] == "cm@example.com"

    # Preview invitation publicly (no auth required)
    preview_res = client.get(f"/api/v1/workspace/invitations/{token_str}")
    assert preview_res.status_code == 200
    preview = preview_res.json()
    assert preview["email"] == "cm@example.com"
    assert preview["role"] == "COMMUNITY_MANAGER"
    assert preview["status"] == "PENDING"


def test_revoke_invitation(client, db_session: Session):
    token, headers = _register_and_login(client, "owner_revoker@example.com", "Revoke", "Admin")

    invite_res = client.post(
        "/api/v1/workspace/invitations",
        headers=headers,
        json={"email": "temp@example.com", "role": "CLIENT"},
    )
    assert invite_res.status_code == 201
    invitation_id = invite_res.json()["id"]

    # Revoke
    revoke_res = client.post(
        f"/api/v1/workspace/invitations/{invitation_id}/revoke",
        headers=headers,
    )
    assert revoke_res.status_code == 204

    # Listing reflects revoked status
    list_res = client.get("/api/v1/workspace/invitations", headers=headers)
    assert list_res.json()[0]["status"] == "REVOKED"


def test_accept_invitation_flow(client, db_session: Session):
    owner_token, owner_headers = _register_and_login(client, "team_owner@example.com", "Team", "Owner")

    # Invite new member
    invite_res = client.post(
        "/api/v1/workspace/invitations",
        headers=owner_headers,
        json={"email": "newbie@example.com", "role": "COMMUNITY_MANAGER"},
    )
    assert invite_res.status_code == 201
    token_str = invite_res.json()["invitation_url"].split("/")[-1]

    # Register the invited user
    user_token, user_headers = _register_and_login(client, "newbie@example.com", "New", "Member")

    # Accept invitation
    accept_res = client.post(
        f"/api/v1/workspace/invitations/{token_str}/accept",
        headers=user_headers,
    )
    assert accept_res.status_code == 200
    member_data = accept_res.json()
    assert member_data["email"] == "newbie@example.com"
    assert member_data["role"] == "COMMUNITY_MANAGER"
    assert member_data["status"] == "ACTIVE"

    # Accepting again fails
    again_res = client.post(
        f"/api/v1/workspace/invitations/{token_str}/accept",
        headers=user_headers,
    )
    assert again_res.status_code == 400

    # Verify members list now contains both
    members_res = client.get("/api/v1/workspace/members", headers=owner_headers)
    emails = [m["email"] for m in members_res.json()]
    assert "team_owner@example.com" in emails
    assert "newbie@example.com" in emails

    # Verify activities logged
    activities = db_session.scalars(select(WorkspaceActivity)).all()
    events = [a.event for a in activities]
    assert "INVITATION_SENT" in events
    assert "MEMBER_ACCEPTED" in events


def test_accept_invitation_email_mismatch_rejected(client, db_session: Session):
    owner_token, owner_headers = _register_and_login(client, "corp_owner@example.com", "Corp", "Owner")

    invite_res = client.post(
        "/api/v1/workspace/invitations",
        headers=owner_headers,
        json={"email": "target@example.com", "role": "COMMUNITY_MANAGER"},
    )
    token_str = invite_res.json()["invitation_url"].split("/")[-1]

    # Different user tries to accept
    wrong_token, wrong_headers = _register_and_login(client, "intruder@example.com", "Wrong", "User")
    accept_res = client.post(
        f"/api/v1/workspace/invitations/{token_str}/accept",
        headers=wrong_headers,
    )
    assert accept_res.status_code == 403


def test_member_role_update_and_permissions(client, db_session: Session):
    owner_token, owner_headers = _register_and_login(client, "lead@example.com", "Lead", "Owner")

    # Invite and accept
    invite_res = client.post(
        "/api/v1/workspace/invitations",
        headers=owner_headers,
        json={"email": "colleague@example.com", "role": "COMMUNITY_MANAGER"},
    )
    token_str = invite_res.json()["invitation_url"].split("/")[-1]
    colleague_token, colleague_headers = _register_and_login(client, "colleague@example.com", "Col", "League")
    client.post(f"/api/v1/workspace/invitations/{token_str}/accept", headers=colleague_headers)

    members = client.get("/api/v1/workspace/members", headers=owner_headers).json()
    colleague_member = next(m for m in members if m["email"] == "colleague@example.com")
    owner_member = next(m for m in members if m["email"] == "lead@example.com")

    colleague_ws_headers = {**colleague_headers, "X-Workspace-ID": str(owner_member["workspace_id"])}

    # Owner can update colleague role to ADMIN
    update_res = client.patch(
        f"/api/v1/workspace/members/{colleague_member['id']}/role",
        headers=owner_headers,
        json={"role": "ADMIN"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["role"] == "ADMIN"

    # Cannot modify owner role
    bad_owner_update = client.patch(
        f"/api/v1/workspace/members/{owner_member['id']}/role",
        headers=colleague_ws_headers,
        json={"role": "COMMUNITY_MANAGER"},
    )
    assert bad_owner_update.status_code == 403

    # Client / CM cannot manage team
    # Demote colleague to CLIENT
    client.patch(
        f"/api/v1/workspace/members/{colleague_member['id']}/role",
        headers=owner_headers,
        json={"role": "CLIENT"},
    )
    forbidden_invite = client.post(
        "/api/v1/workspace/invitations",
        headers=colleague_ws_headers,
        json={"email": "another@example.com", "role": "CLIENT"},
    )
    assert forbidden_invite.status_code == 403


def test_member_deactivation_and_removal(client, db_session: Session):
    owner_token, owner_headers = _register_and_login(client, "super_owner@example.com", "Super", "Owner")

    invite_res = client.post(
        "/api/v1/workspace/invitations",
        headers=owner_headers,
        json={"email": "to_remove@example.com", "role": "COMMUNITY_MANAGER"},
    )
    token_str = invite_res.json()["invitation_url"].split("/")[-1]
    user_token, user_headers = _register_and_login(client, "to_remove@example.com", "To", "Remove")
    client.post(f"/api/v1/workspace/invitations/{token_str}/accept", headers=user_headers)

    members = client.get("/api/v1/workspace/members", headers=owner_headers).json()
    target_member = next(m for m in members if m["email"] == "to_remove@example.com")
    owner_member = next(m for m in members if m["email"] == "super_owner@example.com")

    # Deactivate target member
    deact_res = client.patch(
        f"/api/v1/workspace/members/{target_member['id']}/status",
        headers=owner_headers,
        json={"status": "INACTIVE"},
    )
    assert deact_res.status_code == 200
    assert deact_res.json()["status"] == "INACTIVE"

    # Owner cannot deactivate self
    self_deact = client.patch(
        f"/api/v1/workspace/members/{owner_member['id']}/status",
        headers=owner_headers,
        json={"status": "INACTIVE"},
    )
    assert self_deact.status_code in (400, 403)


    # Remove target member
    del_res = client.delete(
        f"/api/v1/workspace/members/{target_member['id']}",
        headers=owner_headers,
    )
    assert del_res.status_code == 204

    # Owner cannot be removed
    del_owner = client.delete(
        f"/api/v1/workspace/members/{owner_member['id']}",
        headers=owner_headers,
    )
    assert del_owner.status_code == 403

    # Verify notification was sent
    notif = db_session.scalar(
        select(Notification).where(Notification.user_id == target_member["user_id"]).order_by(Notification.id.desc())
    )
    assert notif is not None
    assert "Removed from workspace" in notif.title
