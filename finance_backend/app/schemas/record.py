# =============================================================================
# Zorvyn Finance Backend — Record Schemas (Request/Response Validation)
# =============================================================================
# Pydantic models for financial record API endpoints.
#
# Feature Mapping:
#   - Feature 2 (Pagination): PaginatedResponse generic schema
#   - Feature 3 (Search): Filter parameters validated by endpoint (not here)
#   - Feature 4 (Soft Delete): is_deleted exposed in RecordResponse
#   - Feature 7 (API Docs): All fields have `description` for Swagger UI
#
# Separation of Concerns:
#   - Models (app/models/record.py) → MongoDB document structure
#   - Schemas (this file)           → API validation & serialization
# =============================================================================

from datetime import datetime
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.models.record import RecordType


# ---------------------------------------------------------------------------
# Generic Type Variable for Paginated Responses
# ---------------------------------------------------------------------------
T = TypeVar("T")


# ---------------------------------------------------------------------------
# Request Schemas — Validate incoming data
# ---------------------------------------------------------------------------

class RecordCreate(BaseModel):
    """
    Schema for creating a new financial record (POST /records/).

    Validates:
    - amount must be strictly positive (> 0)
    - type must be 'income' or 'expense'
    - category must be 1-100 characters
    - date must be a valid ISO 8601 datetime
    - notes is optional but capped at 500 characters
    """

    amount: float = Field(
        ...,
        gt=0,
        description="Transaction amount. Must be a positive number (greater than zero).",
        json_schema_extra={"example": 5000.00},
    )
    type: RecordType = Field(
        ...,
        description="Transaction type: 'income' for money received, 'expense' for money spent.",
        json_schema_extra={"example": "income"},
    )
    category: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Category label for the transaction (e.g., 'salary', 'rent', 'groceries').",
        json_schema_extra={"example": "salary"},
    )
    date: datetime = Field(
        ...,
        description="Transaction date in ISO 8601 format (e.g., '2026-04-01T00:00:00Z').",
        json_schema_extra={"example": "2026-04-01T00:00:00Z"},
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional description or memo for this transaction.",
        json_schema_extra={"example": "April salary payment"},
    )


class RecordUpdate(BaseModel):
    """
    Schema for updating an existing financial record (PUT /records/{id}).

    All fields are optional — only provided fields will be updated.
    At least one field must be provided (validated in the endpoint).
    """

    amount: Optional[float] = Field(
        default=None,
        gt=0,
        description="Updated transaction amount (must be positive if provided).",
    )
    type: Optional[RecordType] = Field(
        default=None,
        description="Updated transaction type: 'income' or 'expense'.",
    )
    category: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Updated category label.",
    )
    date: Optional[datetime] = Field(
        default=None,
        description="Updated transaction date (ISO 8601).",
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Updated notes/description.",
    )


# ---------------------------------------------------------------------------
# Response Schemas — Shape outgoing data
# ---------------------------------------------------------------------------

class RecordResponse(BaseModel):
    """
    Schema for financial record data in API responses.

    Includes all record fields plus the MongoDB ObjectId serialized as string.
    The is_deleted field is included so clients can identify soft-deleted records
    when querying with include_deleted=true.
    """

    id: str = Field(
        ...,
        description="Unique record identifier (MongoDB ObjectId as string).",
        json_schema_extra={"example": "660f1a2b3c4d5e6f7a8b9c0d"},
    )
    amount: float = Field(
        ...,
        description="Transaction amount.",
    )
    type: RecordType = Field(
        ...,
        description="Transaction type (income or expense).",
    )
    category: str = Field(
        ...,
        description="Category of the transaction.",
    )
    date: datetime = Field(
        ...,
        description="Date of the transaction.",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Optional notes or description.",
    )
    created_by: str = Field(
        ...,
        description="User ID of the creator (MongoDB ObjectId as string).",
    )
    is_deleted: bool = Field(
        ...,
        description="Whether this record has been soft-deleted.",
    )
    created_at: datetime = Field(
        ...,
        description="Creation timestamp (UTC).",
    )
    updated_at: datetime = Field(
        ...,
        description="Last update timestamp (UTC).",
    )

    # Allow creating this schema from ORM/ODM model attributes
    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response wrapper (Feature 2: Pagination).

    Wraps any list of items with pagination metadata so clients can
    navigate through large datasets efficiently.

    Example Response:
    {
        "items": [...],
        "total": 150,
        "page": 2,
        "page_size": 20,
        "total_pages": 8
    }
    """

    items: list[T] = Field(
        ...,
        description="List of items for the current page.",
    )
    total: int = Field(
        ...,
        description="Total number of items matching the query (across all pages).",
        json_schema_extra={"example": 150},
    )
    page: int = Field(
        ...,
        description="Current page number (1-indexed).",
        json_schema_extra={"example": 1},
    )
    page_size: int = Field(
        ...,
        description="Number of items per page.",
        json_schema_extra={"example": 20},
    )
    total_pages: int = Field(
        ...,
        description="Total number of pages available.",
        json_schema_extra={"example": 8},
    )
