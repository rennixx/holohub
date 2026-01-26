"""
Users API

Endpoints for user management including profile updates.
"""
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    DBSession,
    CurrentUser,
)
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.core.security import get_password_hash

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: CurrentUser,
) -> User:
    """Get the current authenticated user's profile."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    updates: UserUpdate,
    current_user: CurrentUser,
    db: DBSession,
) -> User:
    """
    Update the current user's profile.

    Allows updating:
    - full_name: User's display name
    """
    # Only allow updating full_name for now
    # Other fields like email require special handling
    if updates.full_name is not None:
        current_user.full_name = updates.full_name

    await db.commit()
    await db.refresh(current_user)

    return current_user


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    current_password: str,
    new_password: str,
    current_user: CurrentUser,
    db: DBSession,
) -> None:
    """
    Change the current user's password.

    Requires the current password for verification.
    """
    # TODO: Implement password change with current password verification
    # For now, this is a placeholder
    pass
