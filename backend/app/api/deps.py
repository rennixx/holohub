"""
API Dependencies Module

Contains dependency injection functions for FastAPI routes.
"""
from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.row_level_security import OrgContext, Role
from app.db.base import get_db
from app.models import User, Organization
from app.schemas.common import MessageResponse
from uuid_utils.compat import UUID as pyUUID

# Security schemes
security = HTTPBearer(auto_error=False)


# =============================================================================
# Database Dependencies
# =============================================================================
# Type alias for database dependency - use get_db() directly
DBSession = Annotated[AsyncSession, Depends(get_db)]


# =============================================================================
# Authentication Dependencies
# =============================================================================
async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: DBSession,
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer credentials
        db: Database session

    Returns:
        User: Authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    from app.core.security import verify_token_type

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = verify_token_type(token, "access")

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Get user from database
    from sqlalchemy import select

    stmt = select(User).where(User.id == pyUUID(user_id))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account has been deleted",
        )

    if user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked. Please contact support.",
        )

    return user


async def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: DBSession,
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise None.

    Similar to get_current_user but doesn't raise exception if not authenticated.

    Returns:
        User if authenticated, None otherwise
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


# Type alias for authenticated user
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[Optional[User], Depends(get_current_user_optional)]


# =============================================================================
# Organization Dependencies
# =============================================================================
async def get_current_organization(
    user: CurrentUser,
    db: DBSession,
) -> Organization:
    """
    Get current user's organization.

    Args:
        user: Authenticated user
        db: Database session

    Returns:
        Organization: User's organization

    Raises:
        HTTPException: If organization not found
    """
    from sqlalchemy import select

    stmt = select(Organization).where(Organization.id == user.organization_id)
    result = await db.execute(stmt)
    org = result.scalar_one_or_none()

    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return org


CurrentOrg = Annotated[Organization, Depends(get_current_organization)]


async def set_organization_context(
    user: CurrentUser,
    db: DBSession,
) -> Organization:
    """
    Set organization context for row-level security.

    This sets the PostgreSQL session variable for RLS policies
    and returns the organization for convenience.

    Args:
        user: Authenticated user
        db: Database session

    Returns:
        Organization: User's organization with context set
    """
    await OrgContext.set_org_context(db, user.organization_id)

    return await get_current_organization(user, db)


OrgContextSet = Annotated[Organization, Depends(set_organization_context)]


# =============================================================================
# Role-Based Authorization Dependencies
# =============================================================================
async def require_role(
    user: CurrentUser,
    required_roles: list[str],
) -> User:
    """
    Require user to have one of the specified roles.

    Args:
        user: Authenticated user
        required_roles: List of allowed roles

    Returns:
        User: Authenticated user

    Raises:
        HTTPException: If user doesn't have required role
    """
    from app.core.row_level_security import require_role as check_role

    if not check_role(user.role, required_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required role: one of {required_roles}",
        )

    return user


def require_role_wrapper(*roles: str):
    """
    Create a dependency that requires specific roles.

    Args:
        *roles: Allowed roles

    Returns:
        Dependency function

    Example:
        @app.get("/admin")
        async def admin_endpoint(
            user: User = Depends(require_role_wrapper("owner", "admin"))
        ):
            return {"message": "Welcome admin"}
    """
    async def check_role(user: CurrentUser) -> User:
        return await require_role(user, list(roles))

    return check_role


# Common role dependencies
require_admin = require_role_wrapper(Role.OWNER, Role.ADMIN)
require_editor = require_role_wrapper(Role.OWNER, Role.ADMIN, Role.EDITOR)
require_owner = require_role_wrapper(Role.OWNER)


# =============================================================================
# Permission-Based Authorization Dependencies
# =============================================================================
async def require_permission(
    user: CurrentUser,
    permission: str,
) -> User:
    """
    Require user to have a specific permission.

    Args:
        user: Authenticated user
        permission: Permission to check

    Returns:
        User: Authenticated user

    Raises:
        HTTPException: If user lacks permission
    """
    from app.core.row_level_security import require_permission as check_permission

    if not check_permission(user.role, permission, user.permissions):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: '{permission}' required",
        )

    return user


def require_permission_wrapper(permission: str):
    """
    Create a dependency that requires a specific permission.

    Args:
        permission: Permission required

    Returns:
        Dependency function

    Example:
        @app.post("/assets")
        async def upload_asset(
            user: User = Depends(require_permission_wrapper("upload_asset"))
        ):
            return {"message": "Asset uploaded"}
    """
    async def check_perm(user: CurrentUser) -> User:
        return await require_permission(user, permission)

    return check_perm


# =============================================================================
# Device Authentication Dependencies
# =============================================================================
async def get_current_device(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: DBSession,
) -> "Device":
    """
    Get current authenticated device from JWT token.

    Similar to get_current_user but for device tokens.

    Args:
        credentials: HTTP Bearer credentials
        db: Database session

    Returns:
        Device: Authenticated device

    Raises:
        HTTPException: If token is invalid or device not found
    """
    from app.core.security import verify_token_type
    from app.models import Device
    from sqlalchemy import select

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = verify_token_type(token, "device")

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired device token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    device_id = payload.get("sub")
    if not device_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    stmt = select(Device).where(Device.id == pyUUID(device_id))
    result = await db.execute(stmt)
    device = result.scalar_one_or_none()

    if device is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device not found",
        )

    return device


CurrentDevice = Annotated["Device", Depends(get_current_device)]


# =============================================================================
# Pagination Dependencies
# =============================================================================
async def get_pagination_params(
    page: int = 1,
    limit: int = 50,
) -> tuple[int, int]:
    """
    Get and validate pagination parameters.

    Args:
        page: Page number (1-indexed)
        limit: Items per page

    Returns:
        Tuple of (page, limit)

    Raises:
        HTTPException: If parameters are invalid
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be >= 1",
        )

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 100",
        )

    return page, limit


PaginationParams = Annotated[tuple[int, int], Depends(get_pagination_params)]


# =============================================================================
# Request Metadata Dependencies
# =============================================================================
async def get_request_ip(
    x_forwarded_for: Annotated[Optional[str], Header()] = None,
    x_real_ip: Annotated[Optional[str], Header()] = None,
) -> Optional[str]:
    """
    Get client IP address from request headers.

    Checks X-Forwarded-For and X-Real-IP headers for proxy setups.

    Args:
        x_forwarded_for: X-Forwarded-For header
        x_real_ip: X-Real-IP header

    Returns:
        IP address or None
    """
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    if x_real_ip:
        return x_real_ip
    return None


RequestIP = Annotated[Optional[str], Depends(get_request_ip)]


async def get_user_agent(
    user_agent: Annotated[Optional[str], Header()] = None,
) -> Optional[str]:
    """
    Get user agent from request headers.

    Args:
        user_agent: User-Agent header

    Returns:
        User agent string or None
    """
    return user_agent


RequestUserAgent = Annotated[Optional[str], Depends(get_user_agent)]
