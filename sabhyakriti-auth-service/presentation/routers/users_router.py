from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from application.dtos.auth_dtos import (
    ChangePasswordRequest,
    MessageResponse,
    UpdateProfileRequest,
    UserProfileResponse,
)
from domain.entities.user import User
from presentation.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/users", tags=["users"])


def _svc(request: Request):
    return request.app.state.auth_service


@router.get("/me", response_model=UserProfileResponse)
async def get_profile(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> UserProfileResponse:
    return UserProfileResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        phone_number=current_user.phone_number,
        full_name=current_user.full_name,
        role=str(current_user.role),
        is_email_verified=current_user.is_email_verified,
        profile_picture_url=current_user.profile_picture_url,
        mfa_enabled=current_user.mfa_enabled,
    )


@router.patch("/me", response_model=UserProfileResponse)
async def update_profile(
    request: Request,
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
) -> UserProfileResponse:
    return await _svc(request).update_profile(current_user.user_id, body)


@router.post("/me/change-password", response_model=MessageResponse)
async def change_password(
    request: Request,
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    return await _svc(request).change_password(current_user.user_id, body)
