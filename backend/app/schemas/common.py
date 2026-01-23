"""
Common Schemas

Shared Pydantic schemas used across multiple endpoints.
"""
from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from uuid_utils.compat import UUID as pyUUID


T = TypeVar("T")


class APIResponse(BaseModel):
    """Standard API response wrapper."""

    success: bool = True
    message: str | None = None
    data: Any = None


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str
    detail: str | None = None
    code: str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)


class UUIDModel(BaseModel):
    """Base model with UUID field."""

    id: pyUUID


class TimestampModel(BaseModel):
    """Base model with timestamp fields."""

    created_at: datetime
    updated_at: datetime


class SoftDeleteModel(BaseModel):
    """Base model with soft delete field."""

    deleted_at: datetime | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Paginated response schema.

    Generic type T allows specifying the item type.

    Attributes:
        items: List of items in current page
        pagination: Pagination metadata
    """

    items: list[T]
    pagination: "PaginationMeta"

    model_config = ConfigDict(
        json_encoders={pyUUID: str},
    )


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    total: int = Field(..., description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    limit: int = Field(..., ge=1, le=100, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")

    @classmethod
    def create(
        cls,
        total: int,
        page: int,
        limit: int,
    ) -> "PaginationMeta":
        """
        Create pagination metadata.

        Args:
            total: Total number of items
            page: Current page number
            limit: Items per page

        Returns:
            PaginationMeta instance
        """
        import math

        total_pages = max(1, math.ceil(total / limit)) if total > 0 else 1

        return cls(
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "0.1.0"
    database: bool = False
    redis: bool = False
