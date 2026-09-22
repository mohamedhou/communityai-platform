from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.workspace import MembershipStatus, WorkspaceRole


class WorkspaceMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int
    user_id: int
    name: str
    email: EmailStr
    role: WorkspaceRole
    status: MembershipStatus
    joined_at: datetime | None
    created_at: datetime



class WorkspaceInvitationCreate(BaseModel):
    email: EmailStr
    role: WorkspaceRole = WorkspaceRole.COMMUNITY_MANAGER


class WorkspaceInvitationResponse(BaseModel):
    id: int
    email: EmailStr
    role: WorkspaceRole
    expires_at: datetime
    accepted_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime
    status: str
    invitation_url: str | None = None


class WorkspaceInvitationPreview(BaseModel):
    workspace_name: str
    email: EmailStr
    role: WorkspaceRole
    expires_at: datetime
    status: str


class WorkspaceRoleUpdate(BaseModel):
    role: WorkspaceRole


class WorkspaceMemberStatusUpdate(BaseModel):
    status: MembershipStatus