from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.api.workspace_context import WorkspaceContext, get_workspace_context
from app.models.user import User
from app.schemas.workspace import (
    WorkspaceInvitationCreate,
    WorkspaceInvitationPreview,
    WorkspaceInvitationResponse,
    WorkspaceMemberResponse,
    WorkspaceMemberStatusUpdate,
    WorkspaceRoleUpdate,
)
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/api/v1/workspace", tags=["workspace"])


@router.get("/members", response_model=list[WorkspaceMemberResponse])
def list_members(
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
):
    return WorkspaceService(db).list_members(context.user.id, workspace_id=context.workspace_id)


@router.post("/invitations", response_model=WorkspaceInvitationResponse, status_code=status.HTTP_201_CREATED)
def create_invitation(
    payload: WorkspaceInvitationCreate,
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
):
    return WorkspaceService(db).create_invitation(context.user.id, payload, workspace_id=context.workspace_id)


@router.get("/invitations", response_model=list[WorkspaceInvitationResponse])
def list_invitations(
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
):
    return WorkspaceService(db).list_invitations(context.user.id, workspace_id=context.workspace_id)


@router.post("/invitations/{invitation_id}/revoke", status_code=status.HTTP_204_NO_CONTENT)
def revoke_invitation(
    invitation_id: int,
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
):
    WorkspaceService(db).revoke_invitation(context.user.id, invitation_id, workspace_id=context.workspace_id)


@router.patch("/members/{member_id}/role", response_model=WorkspaceMemberResponse)
def update_member_role(
    member_id: int,
    payload: WorkspaceRoleUpdate,
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
):
    return WorkspaceService(db).update_member(context.user.id, member_id, role=payload.role, workspace_id=context.workspace_id)


@router.patch("/members/{member_id}/status", response_model=WorkspaceMemberResponse)
def update_member_status(
    member_id: int,
    payload: WorkspaceMemberStatusUpdate,
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
):
    return WorkspaceService(db).update_member(context.user.id, member_id, member_status=payload.status, workspace_id=context.workspace_id)


@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    member_id: int,
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
):
    WorkspaceService(db).remove_member(context.user.id, member_id, workspace_id=context.workspace_id)


@router.get("/invitations/{token}", response_model=WorkspaceInvitationPreview)
def preview_invitation(token: str, db: Session = Depends(get_db)):
    return WorkspaceService(db).preview_invitation(token)


@router.post("/invitations/{token}/accept", response_model=WorkspaceMemberResponse)
def accept_invitation(token: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return WorkspaceService(db).accept_invitation(current_user.id, token)