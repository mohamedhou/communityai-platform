from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.workspace import MembershipStatus, Workspace, WorkspaceMember, WorkspaceRole
from app.services.workspace_service import WorkspaceService


@dataclass
class WorkspaceContext:
    workspace: Workspace
    membership: WorkspaceMember
    user: User
    workspace_id: int
    role: WorkspaceRole


def get_workspace_context(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    x_workspace_id: int | None = Header(None, alias="X-Workspace-ID"),
) -> WorkspaceContext:
    ws_service = WorkspaceService(db)
    if x_workspace_id is not None:
        membership = db.scalar(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == x_workspace_id,
                WorkspaceMember.user_id == current_user.id,
                WorkspaceMember.status == MembershipStatus.ACTIVE,
            )
        )
        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to specified workspace is forbidden or inactive",
            )
    else:
        membership = ws_service.get_or_create_default_workspace(current_user)

    workspace = db.get(Workspace, membership.workspace_id)
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    return WorkspaceContext(
        workspace=workspace,
        membership=membership,
        user=current_user,
        workspace_id=workspace.id,
        role=membership.role,
    )


def require_workspace_roles(*allowed_roles: WorkspaceRole):
    def dependency(context: WorkspaceContext = Depends(get_workspace_context)) -> WorkspaceContext:
        if context.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient workspace permissions",
            )
        return context

    return dependency


def require_workspace_manager(
    context: WorkspaceContext = Depends(require_workspace_roles(WorkspaceRole.OWNER, WorkspaceRole.ADMIN)),
) -> WorkspaceContext:
    return context


def require_workspace_editor(
    context: WorkspaceContext = Depends(
        require_workspace_roles(WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.COMMUNITY_MANAGER)
    ),
) -> WorkspaceContext:
    return context
