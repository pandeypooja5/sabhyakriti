from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=100)

    @field_validator("full_name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class OTPSendRequest(BaseModel):
    phone_number: str = Field(min_length=10, max_length=15)


class OTPVerifyRequest(BaseModel):
    phone_number: str = Field(min_length=10, max_length=15)
    otp_code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    token: str


class MFAVerifyRequest(BaseModel):
    mfa_token: str
    totp_code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class MFAConfirmSetupRequest(BaseModel):
    totp_code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class UpdateProfileRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=100)
    profile_picture_url: str | None = Field(default=None, max_length=500)


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 1800


class UserProfileResponse(BaseModel):
    user_id: UUID
    email: str | None
    phone_number: str | None
    full_name: str
    role: str
    is_email_verified: bool
    profile_picture_url: str | None
    mfa_enabled: bool


class AuthResponse(BaseModel):
    tokens: TokenPairResponse
    user: UserProfileResponse
    is_new_user: bool = False


class MFAPendingResponse(BaseModel):
    mfa_required: bool = True
    mfa_token: str


class MessageResponse(BaseModel):
    message: str


class MFASetupResponse(BaseModel):
    secret: str
    provisioning_uri: str
    message: str = "Scan the QR code with your authenticator app, then confirm with your first TOTP code."
