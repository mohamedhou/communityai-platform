from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, require_admin
from app.models.user import User, UserRole
from app.schemas.user import (
    ChangePasswordRequest,
    UserResponse,
    UserRoleUpdate,
    UserStatusUpdate,
    UserUpdate,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    user_service = UserService(db)
    updated_user = user_service.update_profile(
        current_user,
        first_name=payload.first_name,
        last_name=payload.last_name,
    )
    return UserResponse.model_validate(updated_user)


@router.post("/me/change-password", status_code=status.HTTP_200_OK)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    user_service = UserService(db)
    try:
        user_service.change_password(
            current_user,
            current_password=payload.current_password,
            new_password=payload.new_password,
        )
    except ValueError as exc:
        if str(exc) == "invalid_current_password":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid current password",
            ) from exc
        raise

    return {"message": "Password changed successfully"}


@router.get("", response_model=list[UserResponse])
def list_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[UserResponse]:
    user_service = UserService(db)
    users = user_service.list_users()
    return [UserResponse.model_validate(u) for u in users]


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserResponse:
    user_service = UserService(db)
    try:
        user = user_service.get_user_by_id(user_id)
    except ValueError as exc:
        if str(exc) == "user_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            ) from exc
        raise

    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
def update_user_by_id(
    user_id: int,
    payload: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserResponse:
    user_service = UserService(db)
    try:
        updated_user = user_service.update_user_profile_admin(
            user_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
        )
    except ValueError as exc:
        if str(exc) == "user_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            ) from exc
        raise

    return UserResponse.model_validate(updated_user)


@router.patch("/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserResponse:
    user_service = UserService(db)
    try:
        updated_user = user_service.update_user_status(
            user_id,
            is_active=payload.is_active,
            current_user_id=current_user.id,
        )
    except ValueError as exc:
        err_msg = str(exc)
        if err_msg == "user_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            ) from exc
        if err_msg == "cannot_deactivate_self":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate yourself",
            ) from exc
        raise

    return UserResponse.model_validate(updated_user)


@router.patch("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserResponse:
    user_service = UserService(db)
    try:
        updated_user = user_service.update_user_role(
            user_id,
            role=payload.role,
            current_user_id=current_user.id,
        )
    except ValueError as exc:
        err_msg = str(exc)
        if err_msg == "user_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            ) from exc
        if err_msg == "cannot_modify_own_role":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify your own role",
            ) from exc
        raise

    return UserResponse.model_validate(updated_user)
