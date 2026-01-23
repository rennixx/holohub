"""
Token Schemas

Pydantic schemas for JWT authentication.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from uuid_utils.compat import UUID as pyUUID


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: str | pyUUID  # User ID
    org: str | pyUUID  # Organization ID
    role: str
    type: str  # access, refresh, device
    exp: datetime
    iat: datetime
    jti: Optional[str] = None  # JWT ID for refresh tokens


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiry in seconds")


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str
    mfa_code: Optional[str] = Field(None, pattern=r"^\d{6}$", description="6-digit MFA code")


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str


class LogoutRequest(BaseModel):
    """Logout request schema."""

    refresh_token: str


class MFASetupResponse(BaseModel):
    """MFA setup response."""

    secret: str  # TOTP secret (for display only, will be encrypted)
    backup_codes: list[str]  # One-time recovery codes
    qr_code_url: str  # URL for QR code generation


class MFAVerifyRequest(BaseModel):
    """MFA verification request."""

    code: str = Field(..., pattern=r"^\d{6}$", description="6-digit TOTP code")
    secret: str  # Temporary secret from setup


class MFADisableRequest(BaseModel):
    """MFA disable request."""

    password: str  # Require password to disable MFA
