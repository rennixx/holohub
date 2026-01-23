"""
User Schemas

Pydantic schemas for user validation and serialization.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from uuid_utils.compat import UUID as pyUUID


# =============================================================================
# Base Schemas
# =============================================================================
class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=255)
    role: str = Field(default="viewer", pattern="^(owner|admin|editor|viewer)$")


# =============================================================================
# Create Schemas
# =============================================================================
class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(..., min_length=12)
    organization_id: Optional[pyUUID] = None  # If None, creates new org

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        from app.core.security import validate_password_strength

        is_valid, errors = validate_password_strength(v)
        if not is_valid:
            raise ValueError("; ".join(errors))
        return v


class UserRegister(BaseModel):
    """Schema for user registration (creates org + user)."""

    email: EmailStr
    password: str = Field(..., min_length=12)
    full_name: Optional[str] = Field(None, max_length=255)
    organization_name: str = Field(..., min_length=1, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        from app.core.security import validate_password_strength

        is_valid, errors = validate_password_strength(v)
        if not is_valid:
            raise ValueError("; ".join(errors))
        return v


class UserInvite(BaseModel):
    """Schema for inviting a user to an organization."""

    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=255)
    role: str = Field(default="viewer", pattern="^(owner|admin|editor|viewer)$")


# =============================================================================
# Update Schemas
# =============================================================================
class UserUpdate(BaseModel):
    """Schema for updating a user."""

    full_name: Optional[str] = Field(None, max_length=255)
    role: Optional[str] = Field(None, pattern="^(owner|admin|editor|viewer)$")
    permissions: Optional[dict] = None
    avatar_url: Optional[str] = None


class UserPasswordChange(BaseModel):
    """Schema for password change."""

    current_password: str
    new_password: str = Field(..., min_length=12)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        from app.core.security import validate_password_strength

        is_valid, errors = validate_password_strength(v)
        if not is_valid:
            raise ValueError("; ".join(errors))
        return v


class UserPasswordReset(BaseModel):
    """Schema for password reset with token."""

    token: str
    new_password: str = Field(..., min_length=12)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        from app.core.security import validate_password_strength

        is_valid, errors = validate_password_strength(v)
        if not is_valid:
            raise ValueError("; ".join(errors))
        return v


class UserPasswordResetRequest(BaseModel):
    """Schema for requesting password reset."""

    email: EmailStr


# =============================================================================
# Response Schemas
# =============================================================================
class UserResponse(UserBase):
    """Schema for user response."""

    model_config = ConfigDict(from_attributes=True)

    id: pyUUID
    organization_id: pyUUID
    email_verified: bool
    mfa_enabled: bool
    avatar_url: Optional[str]
    permissions: dict
    last_login: Optional[datetime]
    last_ip: Optional[str]
    created_at: datetime
    updated_at: datetime

    # Exclude sensitive data
    model_config = ConfigDict(from_attributes=True, exclude={"password_hash", "mfa_secret", "backup_codes"})


class UserMe(UserResponse):
    """Schema for current user response."""

    organization: "OrganizationResponse"


class UserProfile(BaseModel):
    """User profile for display."""

    id: pyUUID
    email: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    role: str
    organization_id: pyUUID

    @property
    def display_name(self) -> str:
        """Get display name."""
        return self.full_name or self.email.split("@")[0]

    @property
    def initials(self) -> str:
        """Get initials."""
        if self.full_name:
            parts = self.full_name.split()
            if len(parts) >= 2:
                return f"{parts[0][0]}{parts[1][0]}".upper()
            return parts[0][0].upper()
        return self.email[0].upper()


# Import for type hint
from app.schemas.organization import OrganizationResponse

UserMe.model_rebuild()
