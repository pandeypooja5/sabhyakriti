from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from application.dtos.auth_dtos import (
    AuthResponse,
    MFAConfirmSetupRequest,
    MFASetupResponse,
    MFAVerifyRequest,
    MessageResponse,
)
from domain.entities.user import User
from presentation.dependencies import require_admin

router = APIRouter(prefix="/api/v1/auth/admin", tags=["admin-auth"])


def _svc(request: Request):
    return request.app.state.auth_service


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    request: Request,
    admin: User = Depends(require_admin),
) -> MFASetupResponse:
    return await _svc(request).setup_mfa(admin.user_id)


@router.post("/mfa/confirm-setup", response_model=MessageResponse)
async def confirm_mfa_setup(
    request: Request,
    body: MFAConfirmSetupRequest,
    admin: User = Depends(require_admin),
) -> MessageResponse:
    return await _svc(request).confirm_mfa_setup(admin.user_id, body)


@router.post("/mfa/verify", response_model=AuthResponse)
async def verify_mfa(
    request: Request,
    body: MFAVerifyRequest,
) -> AuthResponse:
    """Verify TOTP code after login returned MFAPendingResponse.

    Only requires the mfa_pending JWT embedded in the request body; no full
    bearer token needed at this point.
    """
    return await _svc(request).verify_mfa(body)
