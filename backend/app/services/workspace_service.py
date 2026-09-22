from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_token
from app.models.notification import NotificationSeverity, NotificationType
from app.models.user import User
from app.models.workspace import (
    MembershipStatus,
    Workspace,
    WorkspaceActivity,
    WorkspaceInvitation,
    WorkspaceMember,
    WorkspaceRole,
)
from app.schemas.notification import NotificationCreate
from app.schemas.workspace import (
    WorkspaceInvitationCreate,
    WorkspaceInvitationPreview,
    WorkspaceInvitationResponse,
    WorkspaceMemberResponse,
)
from app.services.notification_service import NotificationService


MANAGER_ROLES = {WorkspaceRole.OWNER, WorkspaceRole.ADMIN}


class WorkspaceService:
    def __init__(self, db: Session):
        self.db = db
        self.notifications = NotificationService()

    def get_membership(self, user_id: int, workspace_id: int | None = None) -> WorkspaceMember:
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.status == MembershipStatus.ACTIVE,
        )
        if workspace_id is not None:
            stmt = stmt.where(WorkspaceMember.workspace_id == workspace_id)
        membership = self.db.scalar(stmt.order_by(WorkspaceMember.id.asc()))
        if membership is None:
            if workspace_id is None:
                user = self.db.get(User, user_id)
                if user:
                    return self.get_or_create_default_workspace(user)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No active workspace membership")
        return membership

    def get_or_create_default_workspace(self, user: User) -> WorkspaceMember:
        membership = self.db.scalar(
            select(WorkspaceMember).where(
                WorkspaceMember.user_id == user.id,
                WorkspaceMember.status == MembershipStatus.ACTIVE,
            ).order_by(WorkspaceMember.id.asc())
        )
        if membership is not None:
            return membership

        workspace = self.db.scalar(
            select(Workspace).where(Workspace.owner_id == user.id).order_by(Workspace.id.asc())
        )
        if workspace is None:
            clean_prefix = user.email.split("@", 1)[0].lower()
            slug = f"{clean_prefix}-{user.id}"
            existing = self.db.scalar(select(Workspace).where(Workspace.slug == slug))
            if existing:
                slug = f"{slug}-{secrets.token_hex(3)}"
            workspace = Workspace(
                name=f"{user.first_name}'s Workspace",
                slug=slug,
                owner_id=user.id,
            )
            self.db.add(workspace)
            self.db.flush()

        membership = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=user.id,
            role=WorkspaceRole.OWNER,
            status=MembershipStatus.ACTIVE,
            joined_at=datetime.now(UTC),
        )
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(membership)
        return membership

    def require_manager(self, user_id: int, workspace_id: int | None = None) -> WorkspaceMember:
        membership = self.get_membership(user_id, workspace_id=workspace_id)
        if membership.role not in MANAGER_ROLES:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient workspace permissions")
        return membership

    def list_members(self, user_id: int, workspace_id: int | None = None) -> list[WorkspaceMemberResponse]:
        membership = self.get_membership(user_id, workspace_id=workspace_id)
        rows = self.db.scalars(
            select(WorkspaceMember).where(WorkspaceMember.workspace_id == membership.workspace_id).order_by(WorkspaceMember.id)
        ).all()
        return [self._member_response(row) for row in rows]

    def create_invitation(
        self,
        user_id: int,
        payload: WorkspaceInvitationCreate,
        workspace_id: int | None = None,
    ) -> WorkspaceInvitationResponse:
        membership = self.require_manager(user_id, workspace_id=workspace_id)
        if payload.role == WorkspaceRole.OWNER:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot invite a member as OWNER")

        email = str(payload.email).strip().lower()
        existing_member = self.db.scalar(
            select(WorkspaceMember).join(User).where(
                WorkspaceMember.workspace_id == membership.workspace_id,
                User.email == email,
            )
        )
        if existing_member:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a workspace member")

        active_invitations = self.db.scalars(
            select(WorkspaceInvitation).where(
                WorkspaceInvitation.workspace_id == membership.workspace_id,
                WorkspaceInvitation.email == email,
                WorkspaceInvitation.accepted_at.is_(None),
                WorkspaceInvitation.revoked_at.is_(None),
            )
        ).all()
        for inv in active_invitations:
            exp = self._ensure_utc(inv.expires_at)
            if exp and exp > datetime.now(UTC):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An active invitation already exists")

        raw_token = secrets.token_urlsafe(32)
        invitation = WorkspaceInvitation(
            workspace_id=membership.workspace_id,
            email=email,
            role=payload.role,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(UTC) + timedelta(days=7),
            invited_by=user_id,
        )
        self.db.add(invitation)
        self.db.flush()
        self._activity(membership.workspace_id, user_id, "INVITATION_SENT", email)
        self._notify(user_id, "Invitation created", f"An invitation was created for {email}.", invitation.id)
        self.db.commit()
        self.db.refresh(invitation)
        return self._invitation_response(invitation, raw_token)

    def list_invitations(self, user_id: int, workspace_id: int | None = None) -> list[WorkspaceInvitationResponse]:
        membership = self.require_manager(user_id, workspace_id=workspace_id)
        invitations = self.db.scalars(
            select(WorkspaceInvitation)
            .where(WorkspaceInvitation.workspace_id == membership.workspace_id)
            .order_by(WorkspaceInvitation.created_at.desc())
        ).all()
        return [self._invitation_response(item) for item in invitations]

    def revoke_invitation(self, user_id: int, invitation_id: int, workspace_id: int | None = None) -> None:
        membership = self.require_manager(user_id, workspace_id=workspace_id)
        invitation = self.db.scalar(
            select(WorkspaceInvitation).where(
                WorkspaceInvitation.id == invitation_id,
                WorkspaceInvitation.workspace_id == membership.workspace_id,
            )
        )
        if invitation is None or invitation.accepted_at or invitation.revoked_at:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")

        invitation.revoked_at = datetime.now(UTC)
        self._activity(membership.workspace_id, user_id, "INVITATION_REVOKED", invitation.email)
        self.db.commit()

    def update_member(
        self,
        user_id: int,
        member_id: int,
        *,
        role: WorkspaceRole | None = None,
        member_status: MembershipStatus | None = None,
        workspace_id: int | None = None,
    ) -> WorkspaceMemberResponse:
        manager = self.require_manager(user_id, workspace_id=workspace_id)
        member = self.db.scalar(
            select(WorkspaceMember).where(
                WorkspaceMember.id == member_id,
                WorkspaceMember.workspace_id == manager.workspace_id,
            )
        )
        if member is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

        if member.role == WorkspaceRole.OWNER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace owner cannot be modified")

        if manager.role == WorkspaceRole.ADMIN and role == WorkspaceRole.OWNER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can assign owner")

        if role is not None:
            if role == WorkspaceRole.OWNER and manager.role != WorkspaceRole.OWNER:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can assign owner")
            member.role = role
            event = "ROLE_CHANGED"
        else:
            if member.user_id == user_id and member_status == MembershipStatus.INACTIVE:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate own membership")
            member.status = member_status  # type: ignore[assignment]
            event = "MEMBERSHIP_ENABLED" if member_status == MembershipStatus.ACTIVE else "MEMBERSHIP_DISABLED"

        self._activity(manager.workspace_id, user_id, event, str(member.user_id))
        self._notify(member.user_id, "Workspace membership updated", "Your workspace membership was updated.", member.id)
        self.db.commit()
        self.db.refresh(member)
        return self._member_response(member)

    def remove_member(self, user_id: int, member_id: int, workspace_id: int | None = None) -> None:
        manager = self.require_manager(user_id, workspace_id=workspace_id)
        member = self.db.scalar(
            select(WorkspaceMember).where(
                WorkspaceMember.id == member_id,
                WorkspaceMember.workspace_id == manager.workspace_id,
            )
        )
        if member is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

        if member.role == WorkspaceRole.OWNER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace owner cannot be removed")

        if member.user_id == user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove self from workspace")

        affected_user_id = member.user_id
        self.db.delete(member)
        self._activity(manager.workspace_id, user_id, "MEMBER_REMOVED", str(affected_user_id))
        self._notify(affected_user_id, "Removed from workspace", "You were removed from the workspace.", member_id)
        self.db.commit()

    def preview_invitation(self, token: str) -> WorkspaceInvitationPreview:
        invitation = self._find_invitation(token)
        workspace = self.db.get(Workspace, invitation.workspace_id)
        workspace_name = workspace.name if workspace else "Workspace"
        return WorkspaceInvitationPreview(
            workspace_name=workspace_name,
            email=invitation.email,
            role=invitation.role,
            expires_at=invitation.expires_at,
            status=self._invitation_status(invitation),
        )

    def accept_invitation(self, user_id: int, token: str) -> WorkspaceMemberResponse:
        invitation = self._find_invitation(token)
        if self._invitation_status(invitation) != "PENDING":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation is no longer valid")

        user = self.db.get(User, user_id)
        if user is None or user.email.strip().lower() != invitation.email.strip().lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invitation email does not match the signed-in user")

        existing = self.db.scalar(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == invitation.workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a workspace member")

        member = WorkspaceMember(
            workspace_id=invitation.workspace_id,
            user_id=user_id,
            role=invitation.role,
            status=MembershipStatus.ACTIVE,
            joined_at=datetime.now(UTC),
        )
        invitation.accepted_at = datetime.now(UTC)
        self.db.add(member)
        self.db.flush()
        self._activity(invitation.workspace_id, user_id, "MEMBER_ACCEPTED", user.email)
        self._notify(invitation.invited_by, "Invitation accepted", f"{user.email} accepted the workspace invitation.", invitation.id)
        self.db.commit()
        self.db.refresh(member)
        return self._member_response(member)

    def _find_invitation(self, token: str) -> WorkspaceInvitation:
        invitation = self.db.scalar(
            select(WorkspaceInvitation).where(WorkspaceInvitation.token_hash == hash_token(token))
        )
        if invitation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")
        return invitation

    @staticmethod
    def _ensure_utc(dt: datetime | None) -> datetime | None:
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt

    def _invitation_status(self, invitation: WorkspaceInvitation) -> str:
        if invitation.revoked_at:
            return "REVOKED"
        if invitation.accepted_at:
            return "ACCEPTED"
        expires_at = self._ensure_utc(invitation.expires_at)
        if expires_at and expires_at <= datetime.now(UTC):
            return "EXPIRED"
        return "PENDING"


    def _invitation_response(self, invitation: WorkspaceInvitation, raw_token: str | None = None) -> WorkspaceInvitationResponse:
        return WorkspaceInvitationResponse(
            id=invitation.id,
            email=invitation.email,
            role=invitation.role,
            expires_at=invitation.expires_at,
            accepted_at=invitation.accepted_at,
            revoked_at=invitation.revoked_at,
            created_at=invitation.created_at,
            status=self._invitation_status(invitation),
            invitation_url=f"/invitations/{raw_token}" if raw_token else None,
        )

    def _member_response(self, member: WorkspaceMember) -> WorkspaceMemberResponse:
        user = self.db.get(User, member.user_id)
        name = f"{user.first_name} {user.last_name}".strip() if user else "Unknown User"
        email = user.email if user else ""
        return WorkspaceMemberResponse(
            id=member.id,
            workspace_id=member.workspace_id,
            user_id=member.user_id,
            name=name,
            email=email,
            role=member.role,
            status=member.status,
            joined_at=member.joined_at,
            created_at=member.created_at,
        )


    def _activity(self, workspace_id: int, actor_id: int, event: str, details: str) -> None:
        self.db.add(WorkspaceActivity(workspace_id=workspace_id, actor_id=actor_id, event=event, details=details))

    def _notify(self, user_id: int, title: str, message: str, entity_id: int) -> None:
        self.notifications.create_notification(
            self.db,
            NotificationCreate(
                user_id=user_id,
                type=NotificationType.WORKSPACE,
                title=title,
                message=message,
                severity=NotificationSeverity.INFO,
                action_url="/settings",
                entity_type="workspace",
                entity_id=str(entity_id),
            ),
        )