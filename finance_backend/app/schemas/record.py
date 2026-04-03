# =============================================================================
# Zorvyn Finance Backend — Record Schemas (Request/Response Validation)
# =============================================================================
# Pydantic models for financial record API endpoints.
#
# Feature Mapping:
#   - Feature 2 (Pagination): PaginatedResponse generic schema
#   - Feature 3 (Search): Filter parameters validated by endpoint
#   - Feature 4 (Soft Delete): is_deleted exposed in RecordResponse
#   - Feature 7 (API Docs): All fields have `description` for Swagger UI
# =============================================================================

from datetime import datetime
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.models.record import RecordType

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------
class RecordCreate(BaseModel):
    """Schema for creating a new financial record."""
    amount: float = Field(
        ...,
        gt=0,
        description="Transaction amount. Must be a positive number.",
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
        description="Category label for the transaction (e.g., 'salary').",
        json_schema_extra={"example": "salary"},
    )
    date: datetime = Field(
        ...,
        description="Transaction date in ISO 8601 format.",
        json_schema_extra={"example": "2026-04-01T00:00:00Z"},
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional description or memo.",
        json_schema_extra={"example": "April salary payment"},
    )


class RecordUpdate(BaseModel):
    """Schema for updating an existing financial record."""
    amount: Optional[float] = Field(
        default=None,
        gt=0,
        description="Updated transaction amount.",
    )
    type: Optional[RecordType] = Field(
        default=None,
        description="Updated transaction type.",
    )
    category: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Updated category label.",
    )
    date: Optional[datetime] = Field(
        default=None,
        description="Updated transaction date.",
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Updated notes.",
    )


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------
class RecordResponse(BaseModel):
    """Schema for financial record data in API responses."""
    id: str = Field(..., description="Unique record identifier as string.")
    amount: float = Field(..., description="Transaction amount.")
    type: RecordType = Field(..., description="Transaction type (income or expense).")
    category: str = Field(..., description="Category of the transaction.")
    date: datetime = Field(..., description="Date of the transaction.")
    notes: Optional[str] = Field(default=None, description="Optional notes.")
    created_by: str = Field(..., description="User ID of the creator as string.")
    is_deleted: bool = Field(..., description="Whether this record is soft-deleted.")
    created_at: datetime = Field(..., description="Creation timestamp (UTC).")
    updated_at: datetime = Field(..., description="Last update timestamp (UTC).")

    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper (Feature 2)."""
    items: list[T] = Field(..., description="List of items for the current page.")
    total: int = Field(..., description="Total number of items matching the query.")
    page: int = Field(..., description="Current page number.")
    page_size: int = Field(..., description="Number of items per page.")
    total_pages: int = Field(..., description="Total number of pages available.")
