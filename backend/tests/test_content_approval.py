from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
import pytest
from sqlalchemy.orm import Session
from sqlalchemy import select

os.environ["SOCIAL_TOKEN_ENCRYPTION_KEY"] = "G3cZ84fJd9X2-vK8pQLt8G3cZ84fJd9X2-vK8pQLt8E="
os.environ["SOCIAL_MOCK_MODE"] = "true"

from app.core.encryption import encrypt_token
from app.models.notification import Notification, NotificationType
from app.models.post import Post, PostApprovalStatus, PostStatus
from app.models.user import User
from app.models.workspace import MembershipStatus, WorkspaceActivity, WorkspaceMember, WorkspaceRole
from app.social.models import SocialAccount


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


def _create_social_account(db: Session, workspace_id: int, user_id: int) -> SocialAccount:
    sa = SocialAccount(
        workspace_id=workspace_id,
        user_id=user_id,
        platform="facebook",
        provider="meta",
        external_account_id=f"fb-acc-{user_id}-{workspace_id}",
        account_name="Test FB Account",
        access_token_encrypted=encrypt_token("mock-token"),
        status="CONNECTED",
    )
    db.add(sa)
    db.commit()
    db.refresh(sa)
    return sa


def test_submit_draft_for_review_and_status(client, db_session: Session):
    token, headers = _register_and_login(client, "author1@example.com", "Alice", "Author")
    user = db_session.scalar(select(User).where(User.email == "author1@example.com"))
    member = db_session.scalar(select(WorkspaceMember).where(WorkspaceMember.user_id == user.id))
    sa = _create_social_account(db_session, member.workspace_id, user.id)

    # 1. Create a draft post
    create_res = client.post(
        "/api/v1/posts",
        headers=headers,
        json={"content": "Content to review", "social_account_id": sa.id},
    )
    assert create_res.status_code == 201
    post_data = create_res.json()
    post_id = post_data["id"]
    assert post_data["status"] == "DRAFT"
    assert post_data["approval_status"] == "NOT_REQUIRED"

    # 2. Submit for review
    submit_res = client.post(f"/api/v1/posts/{post_id}/submit-review", headers=headers)
    assert submit_res.status_code == 200
    submitted = submit_res.json()
    assert submitted["approval_status"] == "PENDING"
    assert submitted["submitted_for_review_at"] is not None

    # Submitting again when already PENDING fails
    dup_res = client.post(f"/api/v1/posts/{post_id}/submit-review", headers=headers)
    assert dup_res.status_code == 400
    assert "already pending" in dup_res.json()["detail"].lower()


def test_owner_and_admin_can_approve(client, db_session: Session):
    # Setup Owner
    owner_token, owner_headers = _register_and_login(client, "owner_rev@example.com", "Olivia", "Owner")
    owner = db_session.scalar(select(User).where(User.email == "owner_rev@example.com"))
    owner_member = db_session.scalar(select(WorkspaceMember).where(WorkspaceMember.user_id == owner.id))
    sa = _create_social_account(db_session, owner_member.workspace_id, owner.id)

    # Setup CM in same workspace
    cm_token, cm_headers = _register_and_login(client, "cm_rev@example.com", "Charlie", "CM")
    cm = db_session.scalar(select(User).where(User.email == "cm_rev@example.com"))
    db_session.add(
        WorkspaceMember(
            workspace_id=owner_member.workspace_id,
            user_id=cm.id,
            role=WorkspaceRole.COMMUNITY_MANAGER,
            status=MembershipStatus.ACTIVE,
        )
    )
    db_session.commit()

    cm_ws_headers = {**cm_headers, "X-Workspace-ID": str(owner_member.workspace_id)}

    # CM creates post and submits for review
    post_res = client.post(
        "/api/v1/posts",
        headers=cm_ws_headers,
        json={"content": "Awesome CM post", "social_account_id": sa.id},
    )
    assert post_res.status_code == 201
    post_id = post_res.json()["id"]
    submit_res = client.post(f"/api/v1/posts/{post_id}/submit-review", headers=cm_ws_headers)
    assert submit_res.status_code == 200

    # Owner approves post
    approve_res = client.post(f"/api/v1/posts/{post_id}/approve", headers=owner_headers)
    assert approve_res.status_code == 200
    approved = approve_res.json()
    assert approved["approval_status"] == "APPROVED"
    assert approved["reviewed_by"] == owner.id
    assert approved["reviewed_at"] is not None

    # Approving an already approved post fails
    again_res = client.post(f"/api/v1/posts/{post_id}/approve", headers=owner_headers)
    assert again_res.status_code == 400


def test_reject_requires_reason_and_updates_status(client, db_session: Session):
    owner_token, owner_headers = _register_and_login(client, "owner_rej@example.com", "Oliver", "Owner")
    owner = db_session.scalar(select(User).where(User.email == "owner_rej@example.com"))
    owner_member = db_session.scalar(select(WorkspaceMember).where(WorkspaceMember.user_id == owner.id))
    sa = _create_social_account(db_session, owner_member.workspace_id, owner.id)

    create_res = client.post(
        "/api/v1/posts",
        headers=owner_headers,
        json={"content": "Post with typos", "social_account_id": sa.id},
    )
    post_id = create_res.json()["id"]
    client.post(f"/api/v1/posts/{post_id}/submit-review", headers=owner_headers)

    # Rejection without reason fails
    empty_rej = client.post(f"/api/v1/posts/{post_id}/reject", headers=owner_headers, json={"reason": ""})
    assert empty_rej.status_code in (400, 422)

    # Rejection with valid reason
    rej_res = client.post(
        f"/api/v1/posts/{post_id}/reject",
        headers=owner_headers,
        json={"reason": "Please fix grammatical errors in second sentence."},
    )
    assert rej_res.status_code == 200
    rejected = rej_res.json()
    assert rejected["approval_status"] == "REJECTED"
    assert rejected["rejection_reason"] == "Please fix grammatical errors in second sentence."
    assert rejected["reviewed_by"] == owner.id


def test_rejected_post_can_be_edited_and_resubmitted(client, db_session: Session):
    owner_token, owner_headers = _register_and_login(client, "owner_resub@example.com", "Oscar", "Owner")
    owner = db_session.scalar(select(User).where(User.email == "owner_resub@example.com"))
    owner_member = db_session.scalar(select(WorkspaceMember).where(WorkspaceMember.user_id == owner.id))
    sa = _create_social_account(db_session, owner_member.workspace_id, owner.id)

    create_res = client.post(
        "/api/v1/posts",
        headers=owner_headers,
        json={"content": "Draft with errors", "social_account_id": sa.id},
    )
    post_id = create_res.json()["id"]
    client.post(f"/api/v1/posts/{post_id}/submit-review", headers=owner_headers)
    client.post(f"/api/v1/posts/{post_id}/reject", headers=owner_headers, json={"reason": "Fix typo"})

    # Author edits the post
    edit_res = client.put(
        f"/api/v1/posts/{post_id}",
        headers=owner_headers,
        json={"content": "Corrected and polished draft"},
    )
    assert edit_res.status_code == 200

    # Author resubmits for review
    resubmit_res = client.post(f"/api/v1/posts/{post_id}/submit-review", headers=owner_headers)
    assert resubmit_res.status_code == 200
    resubmitted = resubmit_res.json()
    assert resubmitted["approval_status"] == "PENDING"
    assert resubmitted["rejection_reason"] is None


def test_material_edit_on_approved_post_invalidates_approval(client, db_session: Session):
    owner_token, owner_headers = _register_and_login(client, "owner_inval@example.com", "Otto", "Owner")
    owner = db_session.scalar(select(User).where(User.email == "owner_inval@example.com"))
    owner_member = db_session.scalar(select(WorkspaceMember).where(WorkspaceMember.user_id == owner.id))
    sa = _create_social_account(db_session, owner_member.workspace_id, owner.id)

    create_res = client.post(
        "/api/v1/posts",
        headers=owner_headers,
        json={"content": "Approved post content", "social_account_id": sa.id},
    )
    post_id = create_res.json()["id"]
    client.post(f"/api/v1/posts/{post_id}/submit-review", headers=owner_headers)
    client.post(f"/api/v1/posts/{post_id}/approve", headers=owner_headers)

    # Edit approved post content
    edit_res = client.put(
        f"/api/v1/posts/{post_id}",
        headers=owner_headers,
        json={"content": "Substantially modified post content after approval"},
    )
    assert edit_res.status_code == 200
    edited = edit_res.json()
    # Approval must be invalidated and require resubmission
    assert edited["approval_status"] == "REJECTED"
    assert "resubmission required" in edited["rejection_reason"].lower()
    assert edited["reviewed_by"] is None

    # Now can be resubmitted
    resub_res = client.post(f"/api/v1/posts/{post_id}/submit-review", headers=owner_headers)
    assert resub_res.status_code == 200
    assert resub_res.json()["approval_status"] == "PENDING"


def test_community_manager_cannot_approve_or_reject(client, db_session: Session):
    owner_token, owner_headers = _register_and_login(client, "owner_perm@example.com", "Owen", "Owner")
    owner = db_session.scalar(select(User).where(User.email == "owner_perm@example.com"))
    owner_member = db_session.scalar(select(WorkspaceMember).where(WorkspaceMember.user_id == owner.id))
    sa = _create_social_account(db_session, owner_member.workspace_id, owner.id)

    cm_token, cm_headers = _register_and_login(client, "cm_perm@example.com", "Chris", "CM")
    cm = db_session.scalar(select(User).where(User.email == "cm_perm@example.com"))
    db_session.add(
        WorkspaceMember(
            workspace_id=owner_member.workspace_id,
            user_id=cm.id,
            role=WorkspaceRole.COMMUNITY_MANAGER,
            status=MembershipStatus.ACTIVE,
        )
    )
    db_session.commit()

    cm_ws_headers = {**cm_headers, "X-Workspace-ID": str(owner_member.workspace_id)}

    post_res = client.post(
        "/api/v1/posts",
        headers=cm_ws_headers,
        json={"content": "Draft from CM", "social_account_id": sa.id},
    )
    assert post_res.status_code == 201
    post_id = post_res.json()["id"]
    client.post(f"/api/v1/posts/{post_id}/submit-review", headers=cm_ws_headers)

    # CM cannot approve
    cm_approve = client.post(f"/api/v1/posts/{post_id}/approve", headers=cm_ws_headers)
    assert cm_approve.status_code == 403

    # CM cannot reject
    cm_reject = client.post(f"/api/v1/posts/{post_id}/reject", headers=cm_ws_headers, json={"reason": "No way"})
    assert cm_reject.status_code == 403


def test_client_role_cannot_submit_approve_or_publish(client, db_session: Session):
    owner_token, owner_headers = _register_and_login(client, "owner_cl@example.com", "Olga", "Owner")
    owner = db_session.scalar(select(User).where(User.email == "owner_cl@example.com"))
    owner_member = db_session.scalar(select(WorkspaceMember).where(WorkspaceMember.user_id == owner.id))
    sa = _create_social_account(db_session, owner_member.workspace_id, owner.id)

    client_token, client_headers = _register_and_login(client, "client_user@example.com", "Clara", "Client")
    client_user = db_session.scalar(select(User).where(User.email == "client_user@example.com"))
    db_session.add(
        WorkspaceMember(
            workspace_id=owner_member.workspace_id,
            user_id=client_user.id,
            role=WorkspaceRole.CLIENT,
            status=MembershipStatus.ACTIVE,
        )
    )
    db_session.commit()

    # Owner creates draft and submits
    post_res = client.post(
        "/api/v1/posts",
        headers=owner_headers,
        json={"content": "Owner Draft", "social_account_id": sa.id},
    )
    post_id = post_res.json()["id"]
    client.post(f"/api/v1/posts/{post_id}/submit-review", headers=owner_headers)

    # Client cannot submit
    cl_sub = client.post(f"/api/v1/posts/{post_id}/submit-review", headers=client_headers)
    assert cl_sub.status_code == 403

    # Client cannot approve
    cl_app = client.post(f"/api/v1/posts/{post_id}/approve", headers=client_headers)
    assert cl_app.status_code == 403

    # Client cannot publish
    cl_pub = client.post(f"/api/v1/posts/{post_id}/publish", headers=client_headers)
    assert cl_pub.status_code == 403


def test_publishing_safety_blocks_pending_and_rejected_posts(client, db_session: Session):
    owner_token, owner_headers = _register_and_login(client, "owner_safe@example.com", "Sam", "Owner")
    owner = db_session.scalar(select(User).where(User.email == "owner_safe@example.com"))
    owner_member = db_session.scalar(select(WorkspaceMember).where(WorkspaceMember.user_id == owner.id))
    sa = _create_social_account(db_session, owner_member.workspace_id, owner.id)

    future_time = (datetime.now(UTC) + timedelta(days=2)).isoformat()

    # 1. Post in PENDING state
    post_res = client.post(
        "/api/v1/posts",
        headers=owner_headers,
        json={"content": "Unapproved pending post", "social_account_id": sa.id},
    )
    post_id = post_res.json()["id"]
    client.post(f"/api/v1/posts/{post_id}/submit-review", headers=owner_headers)

    # Direct API calls to schedule or publish must be rejected with 400
    pub_err = client.post(f"/api/v1/posts/{post_id}/publish", headers=owner_headers)
    assert pub_err.status_code == 400
    assert "approval status is PENDING" in pub_err.json()["detail"]

    sched_err = client.post(
        f"/api/v1/posts/{post_id}/schedule",
        headers=owner_headers,
        json={"scheduled_at": future_time},
    )
    assert sched_err.status_code == 400
    assert "approval status is PENDING" in sched_err.json()["detail"]

    # 2. Post in REJECTED state
    client.post(f"/api/v1/posts/{post_id}/reject", headers=owner_headers, json={"reason": "Rejected for testing"})

    pub_rej_err = client.post(f"/api/v1/posts/{post_id}/publish", headers=owner_headers)
    assert pub_rej_err.status_code == 400
    assert "approval status is REJECTED" in pub_rej_err.json()["detail"]

    sched_rej_err = client.post(
        f"/api/v1/posts/{post_id}/schedule",
        headers=owner_headers,
        json={"scheduled_at": future_time},
    )
    assert sched_rej_err.status_code == 400
    assert "approval status is REJECTED" in sched_rej_err.json()["detail"]


def test_approved_post_can_be_scheduled_and_published(client, db_session: Session):
    owner_token, owner_headers = _register_and_login(client, "owner_pub@example.com", "Paul", "Owner")
    owner = db_session.scalar(select(User).where(User.email == "owner_pub@example.com"))
    owner_member = db_session.scalar(select(WorkspaceMember).where(WorkspaceMember.user_id == owner.id))
    sa = _create_social_account(db_session, owner_member.workspace_id, owner.id)

    post_res = client.post(
        "/api/v1/posts",
        headers=owner_headers,
        json={"content": "Legitimate ready post", "social_account_id": sa.id},
    )
    post_id = post_res.json()["id"]
    client.post(f"/api/v1/posts/{post_id}/submit-review", headers=owner_headers)
    client.post(f"/api/v1/posts/{post_id}/approve", headers=owner_headers)

    # Approved post can be published
    pub_res = client.post(f"/api/v1/posts/{post_id}/publish", headers=owner_headers)
    assert pub_res.status_code == 200
    assert pub_res.json()["status"] == "PUBLISHED"


def test_cross_workspace_approval_isolation(client, db_session: Session):
    # Workspace A
    token_a, headers_a = _register_and_login(client, "ws_a_admin@example.com", "Alice", "Admin")
    user_a = db_session.scalar(select(User).where(User.email == "ws_a_admin@example.com"))
    member_a = db_session.scalar(select(WorkspaceMember).where(WorkspaceMember.user_id == user_a.id))
    sa_a = _create_social_account(db_session, member_a.workspace_id, user_a.id)

    # Workspace B
    token_b, headers_b = _register_and_login(client, "ws_b_admin@example.com", "Bob", "Admin")
    user_b = db_session.scalar(select(User).where(User.email == "ws_b_admin@example.com"))
    member_b = db_session.scalar(select(WorkspaceMember).where(WorkspaceMember.user_id == user_b.id))
    sa_b = _create_social_account(db_session, member_b.workspace_id, user_b.id)

    # Workspace A creates post and submits for review
    post_a_res = client.post(
        "/api/v1/posts",
        headers=headers_a,
        json={"content": "Post in Workspace A", "social_account_id": sa_a.id},
    )
    post_a_id = post_a_res.json()["id"]
    client.post(f"/api/v1/posts/{post_a_id}/submit-review", headers=headers_a)

    # Workspace B manager attempts to approve Workspace A post
    b_approve = client.post(f"/api/v1/posts/{post_a_id}/approve", headers=headers_b)
    assert b_approve.status_code in (403, 404)

    # Workspace B manager attempts to reject Workspace A post
    b_reject = client.post(f"/api/v1/posts/{post_a_id}/reject", headers=headers_b, json={"reason": "Hostile rejection"})
    assert b_reject.status_code in (403, 404)

    # Workspace B review queue does not contain Workspace A post
    b_queue = client.get("/api/v1/posts/review/queue", headers=headers_b)
    assert b_queue.status_code == 200
    assert len(b_queue.json()) == 0

    # Workspace A review queue contains the post
    a_queue = client.get("/api/v1/posts/review/queue", headers=headers_a)
    assert a_queue.status_code == 200
    assert len(a_queue.json()) == 1
    assert a_queue.json()[0]["id"] == post_a_id


def test_review_queue_and_history_endpoints(client, db_session: Session):
    token, headers = _register_and_login(client, "lead@example.com", "Laura", "Lead")
    user = db_session.scalar(select(User).where(User.email == "lead@example.com"))
    member = db_session.scalar(select(WorkspaceMember).where(WorkspaceMember.user_id == user.id))
    sa = _create_social_account(db_session, member.workspace_id, user.id)

    # Post 1: Approved
    p1 = client.post("/api/v1/posts", headers=headers, json={"content": "Post 1", "social_account_id": sa.id}).json()["id"]
    client.post(f"/api/v1/posts/{p1}/submit-review", headers=headers)
    client.post(f"/api/v1/posts/{p1}/approve", headers=headers)

    # Post 2: Rejected
    p2 = client.post("/api/v1/posts", headers=headers, json={"content": "Post 2", "social_account_id": sa.id}).json()["id"]
    client.post(f"/api/v1/posts/{p2}/submit-review", headers=headers)
    client.post(f"/api/v1/posts/{p2}/reject", headers=headers, json={"reason": "Not suitable"})

    # Post 3: Pending
    p3 = client.post("/api/v1/posts", headers=headers, json={"content": "Post 3", "social_account_id": sa.id}).json()["id"]
    client.post(f"/api/v1/posts/{p3}/submit-review", headers=headers)

    # Queue should only have Post 3
    q_res = client.get("/api/v1/posts/review/queue", headers=headers)
    assert q_res.status_code == 200
    queue = q_res.json()
    assert len(queue) == 1
    assert queue[0]["id"] == p3

    # History should have Post 1 and Post 2
    h_res = client.get("/api/v1/posts/review/history", headers=headers)
    assert h_res.status_code == 200
    history = h_res.json()
    assert len(history) == 2
    history_ids = [p["id"] for p in history]
    assert p1 in history_ids
    assert p2 in history_ids


def test_notifications_and_workspace_activity_logged(client, db_session: Session):
    owner_token, owner_headers = _register_and_login(client, "owner_audit@example.com", "Auditor", "Owner")
    owner = db_session.scalar(select(User).where(User.email == "owner_audit@example.com"))
    owner_member = db_session.scalar(select(WorkspaceMember).where(WorkspaceMember.user_id == owner.id))
    sa = _create_social_account(db_session, owner_member.workspace_id, owner.id)

    # Create & submit post
    p = client.post("/api/v1/posts", headers=owner_headers, json={"content": "Audit Post", "social_account_id": sa.id}).json()["id"]
    client.post(f"/api/v1/posts/{p}/submit-review", headers=owner_headers)
    client.post(f"/api/v1/posts/{p}/reject", headers=owner_headers, json={"reason": "Audited rejection"})
    client.post(f"/api/v1/posts/{p}/submit-review", headers=owner_headers)
    client.post(f"/api/v1/posts/{p}/approve", headers=owner_headers)

    # Check WorkspaceActivity
    activities = list(
        db_session.scalars(
            select(WorkspaceActivity).where(WorkspaceActivity.workspace_id == owner_member.workspace_id)
        ).all()
    )
    events = [a.event for a in activities]
    assert "POST_SUBMITTED_FOR_REVIEW" in events
    assert "POST_REJECTED" in events
    assert "POST_RESUBMITTED" in events
    assert "POST_APPROVED" in events

    # Check Notifications
    notifs = list(db_session.scalars(select(Notification).where(Notification.user_id == owner.id)).all())
    notif_titles = [n.title for n in notifs]
    assert "Publication approuvée" in notif_titles
    assert "Publication rejetée" in notif_titles


def test_role_based_not_required_and_approved_publication_policy(client, db_session: Session):
    owner_token, owner_headers = _register_and_login(client, "policy_owner@example.com", "Olivia", "Owner")
    owner = db_session.scalar(select(User).where(User.email == "policy_owner@example.com"))
    owner_member = db_session.scalar(select(WorkspaceMember).where(WorkspaceMember.user_id == owner.id))
    sa = _create_social_account(db_session, owner_member.workspace_id, owner.id)

    admin_token, admin_headers = _register_and_login(client, "policy_admin@example.com", "Ada", "Admin")
    admin = db_session.scalar(select(User).where(User.email == "policy_admin@example.com"))
    db_session.add(WorkspaceMember(
        workspace_id=owner_member.workspace_id,
        user_id=admin.id,
        role=WorkspaceRole.ADMIN,
        status=MembershipStatus.ACTIVE,
    ))
    cm_token, cm_headers = _register_and_login(client, "policy_cm@example.com", "Casey", "Manager")
    cm = db_session.scalar(select(User).where(User.email == "policy_cm@example.com"))
    db_session.add(WorkspaceMember(
        workspace_id=owner_member.workspace_id,
        user_id=cm.id,
        role=WorkspaceRole.COMMUNITY_MANAGER,
        status=MembershipStatus.ACTIVE,
    ))
    db_session.commit()

    workspace_headers = lambda headers: {**headers, "X-Workspace-ID": str(owner_member.workspace_id)}
    future_time = (datetime.now(UTC) + timedelta(days=2)).isoformat()

    cm_headers = workspace_headers(cm_headers)
    cm_post = client.post("/api/v1/posts", headers=cm_headers, json={"content": "CM draft", "social_account_id": sa.id}).json()["id"]
    assert client.post(f"/api/v1/posts/{cm_post}/schedule", headers=cm_headers, json={"scheduled_at": future_time}).status_code == 403
    assert client.post(f"/api/v1/posts/{cm_post}/publish", headers=cm_headers).status_code == 403

    approved_schedule = client.post("/api/v1/posts", headers=owner_headers, json={"content": "Approved schedule", "social_account_id": sa.id}).json()["id"]
    client.post(f"/api/v1/posts/{approved_schedule}/submit-review", headers=owner_headers)
    client.post(f"/api/v1/posts/{approved_schedule}/approve", headers=owner_headers)
    assert client.post(f"/api/v1/posts/{approved_schedule}/schedule", headers=cm_headers, json={"scheduled_at": future_time}).status_code == 200

    approved_publish = client.post("/api/v1/posts", headers=owner_headers, json={"content": "Approved publish", "social_account_id": sa.id}).json()["id"]
    client.post(f"/api/v1/posts/{approved_publish}/submit-review", headers=owner_headers)
    client.post(f"/api/v1/posts/{approved_publish}/approve", headers=owner_headers)
    assert client.post(f"/api/v1/posts/{approved_publish}/publish", headers=cm_headers).status_code == 200

    owner_schedule = client.post("/api/v1/posts", headers=owner_headers, json={"content": "Owner schedule", "social_account_id": sa.id}).json()["id"]
    assert client.post(f"/api/v1/posts/{owner_schedule}/schedule", headers=owner_headers, json={"scheduled_at": future_time}).status_code == 200
    owner_publish = client.post("/api/v1/posts", headers=owner_headers, json={"content": "Owner publish", "social_account_id": sa.id}).json()["id"]
    assert client.post(f"/api/v1/posts/{owner_publish}/publish", headers=owner_headers).status_code == 200
    admin_headers = workspace_headers(admin_headers)
    admin_schedule = client.post("/api/v1/posts", headers=owner_headers, json={"content": "Admin schedule", "social_account_id": sa.id}).json()["id"]
    assert client.post(f"/api/v1/posts/{admin_schedule}/schedule", headers=admin_headers, json={"scheduled_at": future_time}).status_code == 200
    admin_publish = client.post("/api/v1/posts", headers=owner_headers, json={"content": "Admin publish", "social_account_id": sa.id}).json()["id"]
    assert client.post(f"/api/v1/posts/{admin_publish}/publish", headers=admin_headers).status_code == 200


def test_failed_and_rejected_posts_can_be_resubmitted(client, db_session: Session):
    token, headers = _register_and_login(client, "resubmit_states@example.com")
    user = db_session.scalar(select(User).where(User.email == "resubmit_states@example.com"))
    member = db_session.scalar(select(WorkspaceMember).where(WorkspaceMember.user_id == user.id))
    sa = _create_social_account(db_session, member.workspace_id, user.id)

    failed_id = client.post("/api/v1/posts", headers=headers, json={"content": "Failed post", "social_account_id": sa.id}).json()["id"]
    failed = db_session.get(Post, failed_id)
    failed.status = PostStatus.FAILED
    failed.error_message = "old provider failure"
    db_session.commit()
    failed_res = client.post(f"/api/v1/posts/{failed_id}/submit-review", headers=headers)
    assert failed_res.status_code == 200
    assert failed_res.json()["status"] == "DRAFT"
    assert failed_res.json()["approval_status"] == "PENDING"
    assert failed_res.json()["error_message"] is None

    rejected_id = client.post("/api/v1/posts", headers=headers, json={"content": "Rejected post", "social_account_id": sa.id}).json()["id"]
    client.post(f"/api/v1/posts/{rejected_id}/submit-review", headers=headers)
    client.post(f"/api/v1/posts/{rejected_id}/reject", headers=headers, json={"reason": "Needs revision"})
    rejected_res = client.post(f"/api/v1/posts/{rejected_id}/submit-review", headers=headers)
    assert rejected_res.status_code == 200
    assert rejected_res.json()["approval_status"] == "PENDING"
    assert rejected_res.json()["rejection_reason"] is None

    scheduled_id = client.post("/api/v1/posts", headers=headers, json={"content": "Invalid state", "social_account_id": sa.id}).json()["id"]
    scheduled = db_session.get(Post, scheduled_id)
    scheduled.status = PostStatus.SCHEDULED
    scheduled.approval_status = PostApprovalStatus.REJECTED
    db_session.commit()
    assert client.post(f"/api/v1/posts/{scheduled_id}/submit-review", headers=headers).status_code == 400


def test_editing_approved_scheduled_post_returns_to_draft(client, db_session: Session):
    token, headers = _register_and_login(client, "scheduled_invalidation@example.com")
    user = db_session.scalar(select(User).where(User.email == "scheduled_invalidation@example.com"))
    member = db_session.scalar(select(WorkspaceMember).where(WorkspaceMember.user_id == user.id))
    sa = _create_social_account(db_session, member.workspace_id, user.id)
    post_id = client.post("/api/v1/posts", headers=headers, json={"content": "Scheduled approved", "social_account_id": sa.id}).json()["id"]
    client.post(f"/api/v1/posts/{post_id}/submit-review", headers=headers)
    client.post(f"/api/v1/posts/{post_id}/approve", headers=headers)
    future_time = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    client.post(f"/api/v1/posts/{post_id}/schedule", headers=headers, json={"scheduled_at": future_time})

    edited = client.put(f"/api/v1/posts/{post_id}", headers=headers, json={"content": "Changed after scheduling"})
    assert edited.status_code == 200
    assert edited.json()["status"] == "DRAFT"
    assert edited.json()["approval_status"] == "REJECTED"
    assert edited.json()["scheduled_at"] is None
    assert client.post(f"/api/v1/posts/{post_id}/publish", headers=headers).status_code == 400
    assert client.post(f"/api/v1/posts/{post_id}/submit-review", headers=headers).status_code == 200
