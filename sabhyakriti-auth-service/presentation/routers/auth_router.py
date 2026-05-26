from __future__ import annotations

import secrets
import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status

from application.dtos.auth_dtos import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MFAPendingResponse,
    MessageResponse,
    OTPSendRequest,
    OTPVerifyRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenPairResponse,
    VerifyEmailRequest,
)
from presentation.dependencies import get_current_user, oauth2_scheme

log = structlog.get_logger()

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _svc(request: Request):
    return request.app.state.auth_service


# ── Registration & email verification ────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: Request, body: RegisterRequest):
    # Returns AuthResponse (with tokens) in dev mode; MessageResponse in production
    return await _svc(request).register_with_email(body)


@router.post("/verify-email", response_model=AuthResponse)
async def verify_email(request: Request, body: VerifyEmailRequest) -> AuthResponse:
    return await _svc(request).verify_email(body)


@router.post("/verify-email/resend", response_model=MessageResponse)
async def resend_verification_email(request: Request, body: ForgotPasswordRequest) -> MessageResponse:
    import hashlib
    import secrets as _secrets
    from datetime import datetime, timedelta, timezone

    from domain.entities.tokens import EmailVerificationToken

    svc = _svc(request)
    email = body.email.lower()
    user = await request.app.state.user_repo.find_by_email(email)
    if not user or user.is_email_verified:
        return MessageResponse(message="If that email is registered and unverified, a new link has been sent.")
    now = datetime.now(tz=timezone.utc)
    raw_token = _secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    ev = EmailVerificationToken(
        token_id=uuid.uuid4(),
        user_id=user.user_id,
        token_hash=token_hash,
        expires_at=now + timedelta(hours=48),
        created_at=now,
    )
    await request.app.state.email_verify_repo.create(ev)
    link = f"{request.app.state.frontend_origin}/verify-email?token={raw_token}"
    await request.app.state.email_adapter.send_verification_email(email, link)
    return MessageResponse(message="If that email is registered and unverified, a new link has been sent.")


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/login")
async def login(request: Request, body: LoginRequest) -> AuthResponse | MFAPendingResponse:
    return await _svc(request).login_with_email(body)


# ── OAuth ─────────────────────────────────────────────────────────────────────

@router.get("/oauth/{provider}/init")
async def oauth_init(provider: str, request: Request) -> dict:
    provider = provider.upper()
    _validate_provider(provider)

    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(64)

    import base64
    import hashlib as _hashlib

    digest = _hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

    redis = request.app.state.redis
    await redis.setex(f"oauth_state:{state}", 600, f"{provider}:{code_verifier}")

    adapter = _get_oauth_adapter(request, provider)
    redirect_uri = _oauth_redirect_uri(request, provider)

    from authlib.integrations.httpx_client import AsyncOAuth2Client

    client_id = _oauth_client_id(request, provider)
    async with AsyncOAuth2Client(client_id=client_id, redirect_uri=redirect_uri) as client:
        auth_url, _ = client.create_authorization_url(
            _oauth_auth_url(provider),
            state=state,
            code_challenge=code_challenge,
            code_challenge_method="S256",
            scope=_oauth_scope(provider),
        )
    return {"auth_url": auth_url, "state": state}


@router.get("/oauth/{provider}/callback", response_model=AuthResponse)
async def oauth_callback(
    provider: str,
    code: str,
    state: str,
    request: Request,
) -> AuthResponse:
    provider = provider.upper()
    _validate_provider(provider)

    redis = request.app.state.redis
    stored: str | None = await redis.get(f"oauth_state:{state}")
    if not stored:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state.")
    await redis.delete(f"oauth_state:{state}")

    stored_provider, code_verifier = stored.split(":", 1)
    if stored_provider != provider:
        raise HTTPException(status_code=400, detail="OAuth provider mismatch.")

    adapter = _get_oauth_adapter(request, provider)
    redirect_uri = _oauth_redirect_uri(request, provider)
    return await _svc(request).login_with_oauth(
        provider=provider.lower(),
        code=code,
        redirect_uri=redirect_uri,
        adapter=adapter,
        code_verifier=code_verifier,
    )


# ── OTP ───────────────────────────────────────────────────────────────────────

@router.post("/otp/send", response_model=MessageResponse)
async def send_otp(request: Request, body: OTPSendRequest) -> MessageResponse:
    return await _svc(request).send_otp(body)


@router.post("/otp/verify", response_model=AuthResponse)
async def verify_otp(request: Request, body: OTPVerifyRequest) -> AuthResponse:
    return await _svc(request).verify_otp(body)


# ── Token management ──────────────────────────────────────────────────────────

@router.post("/refresh", response_model=TokenPairResponse)
async def refresh_tokens(request: Request, body: RefreshRequest) -> TokenPairResponse:
    return await _svc(request).refresh_tokens(body)


@router.post("/logout", response_model=MessageResponse)
async def logout(request: Request, body: RefreshRequest) -> MessageResponse:
    return await _svc(request).logout(body.refresh_token)


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all(
    request: Request,
    current_user=Depends(get_current_user),
) -> MessageResponse:
    return await _svc(request).logout_all(current_user.user_id)


# ── Password management ───────────────────────────────────────────────────────

@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(request: Request, body: ForgotPasswordRequest) -> MessageResponse:
    return await _svc(request).forgot_password(body)


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(request: Request, body: ResetPasswordRequest) -> MessageResponse:
    return await _svc(request).reset_password(body)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _validate_provider(provider: str) -> None:
    if provider not in ("GOOGLE", "FACEBOOK"):
        raise HTTPException(status_code=404, detail=f"OAuth provider '{provider}' not supported.")


def _get_oauth_adapter(request: Request, provider: str):
    if provider == "GOOGLE":
        return request.app.state.google_adapter
    return request.app.state.facebook_adapter


def _oauth_redirect_uri(request: Request, provider: str) -> str:
    base = str(request.base_url).rstrip("/")
    return f"{base}/api/v1/auth/oauth/{provider.lower()}/callback"


def _oauth_auth_url(provider: str) -> str:
    if provider == "GOOGLE":
        return "https://accounts.google.com/o/oauth2/v2/auth"
    return "https://www.facebook.com/v19.0/dialog/oauth"


def _oauth_scope(provider: str) -> str:
    if provider == "GOOGLE":
        return "openid email profile"
    return "email,public_profile"


def _oauth_client_id(request: Request, provider: str) -> str:
    if provider == "GOOGLE":
        return request.app.state.settings.google_client_id
    return request.app.state.settings.facebook_client_id
