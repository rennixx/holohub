"""
Row-Level Security (RLS) Module

Provides utilities for implementing multi-tenancy through
organization-based data isolation.
"""
import uuid
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.core.security import sanitize_input


# =============================================================================
# Row-Level Security Helpers
# =============================================================================
def get_organization_filter(org_id: uuid.UUID):
    """
    Get organization filter for SQLAlchemy queries.

    This function returns a filter condition that restricts queries
    to only return data from the specified organization.

    Args:
        org_id: Organization UUID to filter by

    Returns:
        SQLAlchemy filter condition

    Example:
        stmt = select(User).where(get_organization_filter(org_id))
    """
    # Import here to avoid circular dependency
    from app.db.base import Base

    # Return a binary expression for filtering
    # This will be used like: where(model.organization_id == org_id)
    class OrgFilter:
        def __init__(self, org_id: uuid.UUID):
            self.org_id = org_id

        def __eq__(self, other):
            return other.organization_id == self.org_id

    return OrgFilter(org_id)


def apply_org_filter(stmt: Select, org_id: uuid.UUID) -> Select:
    """
    Apply organization filter to a SQLAlchemy statement.

    Args:
        stmt: SQLAlchemy Select statement
        org_id: Organization UUID to filter by

    Returns:
        Modified Select statement with org filter applied

    Example:
        stmt = apply_org_filter(select(Device), user_org_id)
    """
    # Get the model class from the statement
    if hasattr(stmt, "column_descriptions"):
        # Get the primary entity
        entity = stmt.column_descriptions[0]["entity"]
        if entity and hasattr(entity, "organization_id"):
            stmt = stmt.where(entity.organization_id == org_id)
    return stmt


def apply_org_filters(stmt: Select, org_id: uuid.UUID) -> Select:
    """
    Apply organization filter to all entities in a joined query.

    This is useful for queries with joins that need to filter
    multiple tables by organization.

    Args:
        stmt: SQLAlchemy Select statement with possible joins
        org_id: Organization UUID to filter by

    Returns:
        Modified Select statement with org filters applied to all entities

    Example:
        stmt = select(Device).join(Playlist).where(...)
        stmt = apply_org_filters(stmt, user_org_id)
    """
    if hasattr(stmt, "column_descriptions"):
        for desc in stmt.column_descriptions:
            entity = desc.get("entity")
            if entity and hasattr(entity, "organization_id"):
                stmt = stmt.where(entity.organization_id == org_id)
    return stmt


# =============================================================================
# Organization Context Management
# =============================================================================
class OrgContext:
    """
    Context manager for setting organization context in database sessions.

    This sets a PostgreSQL local variable that can be used by
    Row-Level Security policies.

    Example:
        async with OrgContext(db, user_org_id):
            # All queries in this block are scoped to the org
            result = await db.execute(select(User))
    """

    def __init__(self, db: AsyncSession, org_id: uuid.UUID):
        """
        Initialize organization context.

        Args:
            db: Database session
            org_id: Organization UUID
        """
        self.db = db
        self.org_id = org_id

    async def __aenter__(self):
        """Set organization context."""
        await self.set_org_context(self.db, self.org_id)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clear organization context."""
        await self.clear_org_context(self.db)

    @staticmethod
    async def set_org_context(db: AsyncSession, org_id: uuid.UUID) -> None:
        """
        Set organization context for the current session.

        This sets a PostgreSQL local variable that can be used by RLS policies.

        Args:
            db: Database session
            org_id: Organization UUID
        """
        from sqlalchemy import text

        await db.execute(
            text("SET LOCAL app.current_org_id = :org_id"),
            {"org_id": str(org_id)},
        )

    @staticmethod
    async def clear_org_context(db: AsyncSession) -> None:
        """
        Clear organization context for the current session.

        Args:
            db: Database session
        """
        from sqlalchemy import text

        await db.execute(text("SET LOCAL app.current_org_id = NULL"))


# =============================================================================
# Authorization Checks
# =============================================================================
async def check_org_access(
    db: AsyncSession,
    resource_org_id: uuid.UUID,
    user_org_id: uuid.UUID,
) -> bool:
    """
    Check if user has access to a resource from another organization.

    Args:
        db: Database session
        resource_org_id: Organization ID of the resource
        user_org_id: Organization ID of the user

    Returns:
        True if user has access (same org), False otherwise
    """
    return resource_org_id == user_org_id


async def verify_org_access(
    db: AsyncSession,
    resource_org_id: uuid.UUID,
    user_org_id: uuid.UUID,
) -> bool:
    """
    Verify user has access to resource, raise exception if not.

    Args:
        db: Database session
        resource_org_id: Organization ID of the resource
        user_org_id: Organization ID of the user

    Returns:
        True if access verified

    Raises:
        PermissionError: If user doesn't have access
    """
    if not await check_org_access(db, resource_org_id, user_org_id):
        raise PermissionError(
            f"Access denied: Resource belongs to organization {resource_org_id}, "
            f"user belongs to organization {user_org_id}"
        )
    return True


# =============================================================================
# Role-Based Access Control
# =============================================================================
class Role:
    """User role constants."""

    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


# Role hierarchy (higher roles have all permissions of lower roles)
ROLE_HIERARCHY = {
    Role.OWNER: 4,
    Role.ADMIN: 3,
    Role.EDITOR: 2,
    Role.VIEWER: 1,
}


def has_role_permission(user_role: str, required_role: str) -> bool:
    """
    Check if user role has required permission level.

    Args:
        user_role: User's current role
        required_role: Minimum required role

    Returns:
        True if user has sufficient permissions

    Example:
        has_role_permission("admin", "editor")  # True
        has_role_permission("viewer", "admin")  # False
    """
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    required_level = ROLE_HIERARCHY.get(required_role, 0)
    return user_level >= required_level


def require_role(user_role: str, required_roles: list[str] | str) -> bool:
    """
    Check if user role matches any of the required roles.

    Args:
        user_role: User's current role
        required_roles: Required role(s) - can be single role or list

    Returns:
        True if user has required role

    Example:
        require_role("admin", ["admin", "owner"])  # True
        require_role("viewer", "admin")  # False
    """
    if isinstance(required_roles, str):
        required_roles = [required_roles]
    return user_role in required_roles


# =============================================================================
# Granular Permissions
# =============================================================================
class Permission:
    """Granular permission constants."""

    # User permissions
    CREATE_USER = "create_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    CHANGE_USER_ROLE = "change_user_role"

    # Device permissions
    REGISTER_DEVICE = "register_device"
    ACTIVATE_DEVICE = "activate_device"
    UPDATE_DEVICE = "update_device"
    DELETE_DEVICE = "delete_device"
    SEND_DEVICE_COMMAND = "send_device_command"

    # Asset permissions
    UPLOAD_ASSET = "upload_asset"
    UPDATE_ASSET = "update_asset"
    DELETE_ASSET = "delete_asset"
    REPROCESS_ASSET = "reprocess_asset"

    # Playlist permissions
    CREATE_PLAYLIST = "create_playlist"
    UPDATE_PLAYLIST = "update_playlist"
    DELETE_PLAYLIST = "delete_playlist"
    ASSIGN_PLAYLIST = "assign_playlist"

    # Organization permissions
    UPDATE_ORG = "update_org"
    DELETE_ORG = "delete_org"
    MANAGE_BILLING = "manage_billing"
    MANAGE_SETTINGS = "manage_settings"


# Default permissions for each role
ROLE_PERMISSIONS = {
    Role.OWNER: [
        # All permissions
        Permission.CREATE_USER,
        Permission.UPDATE_USER,
        Permission.DELETE_USER,
        Permission.CHANGE_USER_ROLE,
        Permission.REGISTER_DEVICE,
        Permission.ACTIVATE_DEVICE,
        Permission.UPDATE_DEVICE,
        Permission.DELETE_DEVICE,
        Permission.SEND_DEVICE_COMMAND,
        Permission.UPLOAD_ASSET,
        Permission.UPDATE_ASSET,
        Permission.DELETE_ASSET,
        Permission.REPROCESS_ASSET,
        Permission.CREATE_PLAYLIST,
        Permission.UPDATE_PLAYLIST,
        Permission.DELETE_PLAYLIST,
        Permission.ASSIGN_PLAYLIST,
        Permission.UPDATE_ORG,
        Permission.DELETE_ORG,
        Permission.MANAGE_BILLING,
        Permission.MANAGE_SETTINGS,
    ],
    Role.ADMIN: [
        Permission.CREATE_USER,
        Permission.UPDATE_USER,
        Permission.DELETE_USER,
        Permission.REGISTER_DEVICE,
        Permission.ACTIVATE_DEVICE,
        Permission.UPDATE_DEVICE,
        Permission.DELETE_DEVICE,
        Permission.SEND_DEVICE_COMMAND,
        Permission.UPLOAD_ASSET,
        Permission.UPDATE_ASSET,
        Permission.DELETE_ASSET,
        Permission.REPROCESS_ASSET,
        Permission.CREATE_PLAYLIST,
        Permission.UPDATE_PLAYLIST,
        Permission.DELETE_PLAYLIST,
        Permission.ASSIGN_PLAYLIST,
        Permission.UPDATE_ORG,
        Permission.MANAGE_SETTINGS,
    ],
    Role.EDITOR: [
        Permission.REGISTER_DEVICE,
        Permission.UPDATE_DEVICE,
        Permission.SEND_DEVICE_COMMAND,
        Permission.UPLOAD_ASSET,
        Permission.UPDATE_ASSET,
        Permission.DELETE_ASSET,
        Permission.REPROCESS_ASSET,
        Permission.CREATE_PLAYLIST,
        Permission.UPDATE_PLAYLIST,
        Permission.DELETE_PLAYLIST,
        Permission.ASSIGN_PLAYLIST,
    ],
    Role.VIEWER: [
        # Read-only access, no write permissions
    ],
}


def has_permission(
    user_role: str,
    permission: str,
    custom_permissions: Optional[dict[str, bool]] = None,
) -> bool:
    """
    Check if user has a specific permission.

    Args:
        user_role: User's role
        permission: Permission to check
        custom_permissions: Optional custom permissions override

    Returns:
        True if user has permission

    Example:
        has_permission("editor", "upload_asset")  # True
        has_permission("viewer", "delete_asset")  # False

        # With custom override
        has_permission("viewer", "upload_asset",
                      custom_permissions={"upload_asset": True})  # True
    """
    # Check custom permissions first
    if custom_permissions:
        custom_value = custom_permissions.get(permission)
        if custom_value is not None:
            return custom_value

    # Check role-based permissions
    role_permissions = ROLE_PERMISSIONS.get(user_role, [])
    return permission in role_permissions


def require_permission(
    user_role: str,
    permission: str,
    custom_permissions: Optional[dict[str, bool]] = None,
) -> bool:
    """
    Verify user has permission, raise exception if not.

    Args:
        user_role: User's role
        permission: Permission to check
        custom_permissions: Optional custom permissions override

    Returns:
        True if permission verified

    Raises:
        PermissionError: If user doesn't have permission
    """
    if not has_permission(user_role, permission, custom_permissions):
        raise PermissionError(
            f"Permission denied: '{permission}' requires higher privileges"
        )
    return True
