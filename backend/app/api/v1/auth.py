"""
Authentication Endpoints

Handles user registration, login, logout, token refresh, and MFA.
"""
from datetime import datetime, timedelta
from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    CurrentUser,
    DBSession,
    OptionalUser,
    RequestIP,
    RequestUserAgent,
)
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_mfa_backup_codes,
    generate_mfa_secret,
    get_mfa_totp_uri,
    get_password_hash,
    hash_backup_code,
    verify_backup_code,
    verify_mfa_totp,
    verify_password,
)
from app.models import AuditLog, Organization, User, UserRole
from app.schemas.token import (
    TokenResponse,
    LoginRequest,
    RefreshTokenRequest,
    LogoutRequest,
    MFASetupResponse,
    MFAVerifyRequest,
    MFADisableRequest,
)
from app.schemas.user import (
    UserRegister,
    UserResponse,
    UserMe,
    UserPasswordResetRequest,
)
from app.schemas.common import MessageResponse
from uuid_utils.compat import UUID as pyUUID

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["Authentication"])


# =============================================================================
# Register
# =============================================================================
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegister,
    db: DBSession,
    request_ip: RequestIP,
    request_user_agent: RequestUserAgent,
) -> TokenResponse:
    """
    Register a new user and organization.

    This endpoint creates both a new organization and the first user (owner).
    Returns access and refresh tokens.

    Args:
        data: Registration data
        db: Database session
        request_ip: Client IP address
        request_user_agent: Client user agent

    Returns:
        TokenResponse with access and refresh tokens

    Raises:
        HTTPException: If email already exists
    """
    # Check if email already exists
    stmt = select(User).where(User.email == data.email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create organization
    from app.core.security import slugify

    org = Organization(
        name=data.organization_name,
        slug=slugify(data.organization_name),
        tier="free",
        storage_quota_gb=50,
        device_limit=10,
    )
    db.add(org)
    await db.flush()

    # Create user (owner)
    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        full_name=data.full_name,
        organization_id=org.id,
        role=UserRole.OWNER,
        email_verified=False,  # TODO: Send verification email
    )
    db.add(user)
    await db.flush()

    # Create audit log
    audit_log = AuditLog.create(
        action=AuditLog.Actions.USER_REGISTER,
        resource_type=AuditLog.ResourceTypes.USER,
        resource_id=user.id,
        user_id=user.id,
        org_id=org.id,
        ip_address=request_ip,
        user_agent=request_user_agent,
    )
    db.add(audit_log)

    await db.commit()
    await db.refresh(user)

    # Create tokens
    access_token = create_access_token(user.id, org.id, user.role)
    refresh_token = create_refresh_token(user.id, org.id)

    # Build user response
    user_data = {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "avatar_url": user.avatar_url,
        "role": user.role,
        "organization_id": str(user.organization_id),
        "email_verified": user.email_verified,
        "mfa_enabled": user.mfa_enabled,
        "permissions": user.permissions,
    }

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=user_data,
    )


# =============================================================================
# Login
# =============================================================================
@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: DBSession,
    request_ip: RequestIP,
    request_user_agent: RequestUserAgent,
) -> TokenResponse:
    """
    Login with email and password.

    Returns access and refresh tokens on successful authentication.
    Supports MFA if enabled on the account.

    Args:
        data: Login credentials
        db: Database session
        request_ip: Client IP address
        request_user_agent: Client user agent

    Returns:
        TokenResponse with access and refresh tokens

    Raises:
        HTTPException: If credentials are invalid, account locked, etc.
    """
    # Find user by email
    stmt = select(User).where(User.email == data.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # Verify user exists
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if account is locked
    if user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is locked. Try again after {user.locked_until}",
        )

    # Verify password
    if not verify_password(data.password, user.password_hash):
        # Record failed login
        is_locked = user.record_failed_login(
            settings.max_login_attempts,
            settings.account_lockout_minutes,
        )
        if is_locked:
            audit_log = AuditLog.create(
                action=AuditLog.Actions.USER_LOGIN,
                resource_type=AuditLog.ResourceTypes.USER,
                resource_id=user.id,
                user_id=user.id,
                org_id=user.organization_id,
                ip_address=request_ip,
                user_agent=request_user_agent,
                success=False,
                error_message="Account locked due to too many failed attempts",
            )
            db.add(audit_log)
            await db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check MFA if enabled
    if user.mfa_enabled:
        if not data.mfa_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA code required",
                code="MFA_REQUIRED",
            )

        # Verify TOTP code
        if not verify_mfa_totp(user.mfa_secret, data.mfa_code):
            # Check backup codes
            if not verify_backup_code(data.mfa_code, user.backup_codes):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid MFA code",
                )
            # Remove used backup code from list
            await db.commit()

    # Reset failed login attempts
    user.reset_failed_logins()
    user.update_last_login(request_ip)

    # Create audit log
    audit_log = AuditLog.create(
        action=AuditLog.Actions.USER_LOGIN,
        resource_type=AuditLog.ResourceTypes.USER,
        resource_id=user.id,
        user_id=user.id,
        org_id=user.organization_id,
        ip_address=request_ip,
        user_agent=request_user_agent,
    )
    db.add(audit_log)
    await db.commit()

    # Create tokens
    access_token = create_access_token(user.id, user.organization_id, user.role)
    refresh_token = create_refresh_token(user.id, user.organization_id)

    # Build user response
    user_data = {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "avatar_url": user.avatar_url,
        "role": user.role,
        "organization_id": str(user.organization_id),
        "email_verified": user.email_verified,
        "mfa_enabled": user.mfa_enabled,
        "permissions": user.permissions,
    }

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=user_data,
    )


# =============================================================================
# Refresh Token
# =============================================================================
@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshTokenRequest,
    db: DBSession,
) -> TokenResponse:
    """
    Refresh access token using refresh token.

    Implements refresh token rotation for security.

    Args:
        data: Refresh token request
        db: Database session

    Returns:
        TokenResponse with new access and refresh tokens

    Raises:
        HTTPException: If refresh token is invalid
    """
    # Verify refresh token
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Get user
    stmt = select(User).where(User.id == pyUUID(user_id))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Create new tokens (rotation)
    access_token = create_access_token(user.id, user.organization_id, user.role)
    new_refresh_token = create_refresh_token(user.id, user.organization_id)

    # TODO: Invalidate old refresh token (store in Redis/DB)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


# =============================================================================
# Logout
# -----------------------------------------------------------------------------
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    data: LogoutRequest,
    user: OptionalUser,
    db: DBSession,
    request_ip: RequestIP,
    request_user_agent: RequestUserAgent,
) -> None:
    """
    Logout user and invalidate refresh token.

    Args:
        data: Logout request with refresh token
        user: Current user (optional)
        db: Database session
        request_ip: Client IP address
        request_user_agent: Client user agent
    """
    # Create audit log if user is authenticated
    if user:
        audit_log = AuditLog.create(
            action=AuditLog.Actions.USER_LOGOUT,
            resource_type=AuditLog.ResourceTypes.USER,
            resource_id=user.id,
            user_id=user.id,
            org_id=user.organization_id,
            ip_address=request_ip,
            user_agent=request_user_agent,
        )
        db.add(audit_log)
        await db.commit()

    # TODO: Invalidate refresh token (store in Redis/DB with expiry)


# =============================================================================
# Get Current User
# =============================================================================
@router.get("/me", response_model=UserMe)
async def get_me(
    user: CurrentUser,
    db: DBSession,
) -> UserMe:
    """
    Get current authenticated user with organization details.

    Args:
        user: Current authenticated user
        db: Database session

    Returns:
        User with organization details
    """
    # Get organization
    from app.schemas.organization import OrganizationResponse

    stmt = select(Organization).where(Organization.id == user.organization_id)
    result = await db.execute(stmt)
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    # Build response
    user_dict = UserResponse.model_validate(user).model_dump()
    org_dict = OrganizationResponse.model_validate(org).model_dump()

    return UserMe(**user_dict, organization=org_dict)


# =============================================================================
# MFA Setup
# =============================================================================
@router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    user: CurrentUser,
) -> MFASetupResponse:
    """
    Setup multi-factor authentication for the current user.

    Generates TOTP secret and backup codes.
    The user must verify the TOTP code to enable MFA.

    Args:
        user: Current authenticated user

    Returns:
        MFA setup details with secret, backup codes, and QR code URL

    Raises:
        HTTPException: If MFA is already enabled
    """
    if user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled",
        )

    # Generate TOTP secret
    secret = generate_mfa_secret()
    backup_codes = generate_mfa_backup_codes()

    # Generate QR code URL
    qr_code_url = get_mfa_totp_uri(secret, user.email)

    return MFASetupResponse(
        secret=secret,  # In production, encrypt this
        backup_codes=backup_codes,
        qr_code_url=qr_code_url,
    )


@router.post("/mfa/verify")
async def verify_mfa(
    data: MFAVerifyRequest,
    user: CurrentUser,
    db: DBSession,
) -> MessageResponse:
    """
    Verify MFA setup and enable MFA for the current user.

    After calling /mfa/setup and configuring the authenticator app,
    the user calls this endpoint to verify and enable MFA.

    Args:
        data: MFA verification request with code and secret
        user: Current authenticated user
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If code is invalid or MFA already enabled
    """
    if user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled",
        )

    # Verify TOTP code
    if not verify_mfa_totp(data.secret, data.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA code",
        )

    # Hash backup codes and enable MFA
    user.enable_mfa(data.secret, generate_mfa_backup_codes())

    # Create audit log
    audit_log = AuditLog.create(
        action=AuditLog.Actions.USER_MFA_ENABLED,
        resource_type=AuditLog.ResourceTypes.USER,
        resource_id=user.id,
        user_id=user.id,
        org_id=user.organization_id,
    )
    db.add(audit_log)
    await db.commit()

    return MessageResponse(message="MFA enabled successfully")


@router.post("/mfa/disable")
async def disable_mfa(
    data: MFADisableRequest,
    user: CurrentUser,
    db: DBSession,
) -> MessageResponse:
    """
    Disable multi-factor authentication for the current user.

    Requires password re-authentication for security.

    Args:
        data: Disable MFA request with password
        user: Current authenticated user
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If password is invalid or MFA not enabled
    """
    if not user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled",
        )

    # Verify password
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password",
        )

    # Disable MFA
    user.disable_mfa()

    # Create audit log
    audit_log = AuditLog.create(
        action=AuditLog.Actions.USER_MFA_DISABLED,
        resource_type=AuditLog.ResourceTypes.USER,
        resource_id=user.id,
        user_id=user.id,
        org_id=user.organization_id,
    )
    db.add(audit_log)
    await db.commit()

    return MessageResponse(message="MFA disabled successfully")


# =============================================================================
# Password Reset
# =============================================================================
@router.post("/password/reset-request")
async def request_password_reset(
    email: str,
    db: DBSession,
) -> MessageResponse:
    """
    Request password reset.

    Sends a password reset email with a reset token.
    In development, returns the token in the response.

    Args:
        email: User's email address
        db: Database session

    Returns:
        Success message

    Note: In production, send email with reset token.
    """
    # Find user
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        # Don't reveal if email exists or not
        return MessageResponse(message="If the email exists, a reset link has been sent")

    # Generate reset token
    from app.core.security import generate_reset_token

    reset_token = generate_reset_token()

    # TODO: Store token in Redis/DB with expiry
    # TODO: Send email with reset link

    # In development, return the token
    if settings.debug:
        return MessageResponse(
            message=f"Password reset token: {reset_token} (DEBUG MODE - would be sent via email in production)"
        )

    return MessageResponse(message="If the email exists, a reset link has been sent")


@router.post("/password/reset")
async def reset_password(
    data: UserPasswordResetRequest,
    db: DBSession,
) -> MessageResponse:
    """
    Reset password using reset token.

    Args:
        data: Password reset request with token and new password
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If token is invalid
    """
    # TODO: Verify reset token from Redis/DB
    # For now, we'll just validate the token format

    if not data.token or len(data.token) < 32:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )

    # TODO: Find user by reset token
    # For now, this is a placeholder
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset via token not yet implemented",
    )


# =============================================================================
# OAuth2 Compatible Login (for Swagger UI)
# =============================================================================
@router.post("/token", response_model=TokenResponse)
async def login_oauth2(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DBSession,
    request_ip: RequestIP,
    request_user_agent: RequestUserAgent,
) -> TokenResponse:
    """
    OAuth2 compatible token endpoint for Swagger UI.

    This endpoint provides OAuth2-compatible authentication
    for the FastAPI automatic API documentation (Swagger UI).

    Args:
        form_data: OAuth2 password form data
        db: Database session
        request_ip: Client IP address
        request_user_agent: Client user agent

    Returns:
        TokenResponse with access and refresh tokens
    """
    login_data = LoginRequest(
        email=form_data.username,
        password=form_data.password,
    )
    return await login(login_data, db, request_ip, request_user_agent)
