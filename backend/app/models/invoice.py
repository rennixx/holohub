"""
Invoice Model

Stores billing invoices and payment history.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Numeric, String, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid4
from uuid_utils.compat import UUID as pyUUID

from app.db.base import Base
from app.models import SoftDeleteMixin, TimestampMixin


class InvoiceStatus:
    """Invoice status constants."""

    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"


class Invoice(Base, TimestampMixin, SoftDeleteMixin):
    """
    Invoice model for billing history.

    Attributes:
        id: Unique invoice identifier
        organization_id: Organization that owns the invoice
        stripe_invoice_id: Stripe invoice ID
        amount: Invoice amount in dollars
        currency: Currency code (USD, EUR, etc.)
        status: Invoice status
        description: Invoice description
        due_date: When payment is due
        paid_at: When payment was completed
        invoice_pdf: URL to PDF invoice
    """

    __tablename__ = "invoices"

    # Primary key
    id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Foreign key
    organization_id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Stripe integration
    stripe_invoice_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    # Invoice details
    amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        SQLEnum(
            InvoiceStatus.DRAFT,
            InvoiceStatus.OPEN,
            InvoiceStatus.PAID,
            InvoiceStatus.VOID,
            InvoiceStatus.UNCOLLECTIBLE,
            name="invoice_status",
        ),
        default=InvoiceStatus.OPEN,
        nullable=False,
        index=True,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    due_date: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
    )

    paid_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
    )

    invoice_pdf: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )  # URL to PDF

    # Relationships
    organization = relationship("Organization", back_populates="invoices")

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, amount=${self.amount}, status={self.status})>"
