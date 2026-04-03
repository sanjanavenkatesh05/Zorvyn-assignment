# =============================================================================
# Zorvyn Finance Backend — Financial Record Document Model
# =============================================================================
# Defines the MongoDB document schema for financial records (transactions).
#
# Key Design Decisions:
#   - Soft Delete: Records are never physically removed from the database.
#     Instead, the `is_deleted` flag is set to True. All default queries
#     filter out soft-deleted records. Admins can view them with a flag.
#   - created_by links each record to the admin who created it.
#   - RecordType enum restricts type to 'income' or 'expense'.
#
# Feature Mapping:
#   - Feature 4 (Soft Delete): `is_deleted` field and related logic.
#
# Usage:
#   from app.models.record import Record, RecordType
#   income = await Record.find(
#       Record.type == RecordType.income,
#       Record.is_deleted == False,
#   ).to_list()
# =============================================================================

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from beanie import Document
from pydantic import Field
from beanie import PydanticObjectId


class RecordType(str, Enum):
    """
    Financial record type.

    - income:  Money received (salary, freelance, investment returns, etc.).
    - expense: Money spent (rent, groceries, subscriptions, etc.).
    """

    income = "income"
    expense = "expense"


class Record(Document):
    """
    MongoDB document representing a single financial record (transaction).

    Fields:
        amount:      Transaction amount in the base currency. Must be > 0.
        type:        Either 'income' or 'expense'.
        category:    Categorization label (e.g., 'salary', 'rent', 'groceries').
        date:        Date of the transaction.
        notes:       Optional free-text description or memo.
        created_by:  ObjectId of the User who created this record.
        is_deleted:  Soft delete flag. True = logically deleted, hidden from
                     default queries. Admins can still access deleted records.
        created_at:  Auto-set creation timestamp (UTC).
        updated_at:  Auto-updated timestamp on any modification (UTC).

    MongoDB Collection: "records"
    """

    # ── Core Transaction Fields ──────────────────────────────────────────
    amount: float = Field(
        ...,
        gt=0,
        description="Transaction amount (must be positive).",
        json_schema_extra={"example": 5000.00},
    )
    type: RecordType = Field(
        ...,
        description="Transaction type: 'income' or 'expense'.",
        json_schema_extra={"example": "income"},
    )
    category: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Category label for the transaction.",
        json_schema_extra={"example": "salary"},
    )
    date: datetime = Field(
        ...,
        description="Date of the transaction (ISO 8601 format).",
        json_schema_extra={"example": "2026-04-01T00:00:00Z"},
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional description or memo for the transaction.",
        json_schema_extra={"example": "April salary payment"},
    )

    # ── Ownership ────────────────────────────────────────────────────────
    created_by: PydanticObjectId = Field(
        ...,
        description="ObjectId of the user who created this record.",
    )

    # ── Soft Delete (Feature 4) ─────────────────────────────────────────
    # Records are never physically deleted. Instead, this flag is set to
    # True. All default GET queries exclude soft-deleted records.
    is_deleted: bool = Field(
        default=False,
        description=(
            "Soft delete flag. When True, the record is logically deleted "
            "and hidden from standard queries. Admins can query deleted "
            "records using the 'include_deleted' parameter."
        ),
    )

    # ── Timestamps ───────────────────────────────────────────────────────
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this record was created (UTC, auto-set).",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this record was last modified (UTC, auto-updated).",
    )

    class Settings:
        """Beanie ODM settings for this document."""

        # MongoDB collection name
        name = "records"

    def __repr__(self) -> str:
        return (
            f"<Record type={self.type.value} amount={self.amount} "
            f"category={self.category} deleted={self.is_deleted}>"
        )
