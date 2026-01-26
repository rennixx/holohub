"""
Users API

Endpoints for user management including profile updates.
"""
from typing import Any

from fastapi import APIRouter, Body, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import (
    DBSession,
    CurrentUser,
)
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, UserPasswordChange
from app.core.security import verify_password, get_password_hash

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
    - avatar_url: Profile picture URL
    """
    # Only allow updating safe fields for self-update
    if updates.full_name is not None:
        current_user.full_name = updates.full_name
    if updates.avatar_url is not None:
        current_user.avatar_url = updates.avatar_url

    await db.commit()
    await db.refresh(current_user)

    return current_user


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    data: UserPasswordChange,
    current_user: CurrentUser,
    db: DBSession,
) -> None:
    """
    Change the current user's password.

    Requires the current password for verification.
    """
    # Verify current password
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    # Update password
    current_user.hashed_password = get_password_hash(data.new_password)
    await db.commit()
