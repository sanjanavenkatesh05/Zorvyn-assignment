# =============================================================================
# Zorvyn Finance Backend — Record Service (CRUD + Pagination + Search)
# =============================================================================
# Service layer containing all database operations for financial records.
# This module encapsulates MongoDB queries and keeps endpoint handlers thin.
#
# Feature Mapping:
#   - Feature 2 (Pagination): get_records() with page/page_size params
#   - Feature 3 (Search):     get_records() with filter & regex search
#   - Feature 4 (Soft Delete): soft_delete_record() sets is_deleted=True
#
# Architecture:
#   Endpoint (records.py) → Service (this file) → Beanie ODM → MongoDB
#
# All queries automatically exclude soft-deleted records unless
# include_deleted=True is explicitly passed.
# =============================================================================

import math
from datetime import datetime, timezone
from typing import Optional

from beanie import PydanticObjectId

from app.models.record import Record, RecordType
from app.schemas.record import RecordCreate, RecordUpdate, RecordResponse, PaginatedResponse


# ---------------------------------------------------------------------------
# CREATE — Insert a new financial record
# ---------------------------------------------------------------------------
async def create_record(data: RecordCreate, user_id: PydanticObjectId) -> Record:
    """
    Create a new financial record in the database.

    Args:
        data:    Validated record data from the request body.
        user_id: ObjectId of the authenticated user creating this record.

    Returns:
        The newly created Record document with auto-generated ID and timestamps.

    Example:
        record = await create_record(record_data, current_user.id)
    """
    record = Record(
        amount=data.amount,
        type=data.type,
        category=data.category,
        date=data.date,
        notes=data.notes,
        created_by=user_id,
        # is_deleted defaults to False
        # created_at and updated_at auto-set via default_factory
    )
    await record.insert()
    return record


# ---------------------------------------------------------------------------
# READ — Get a single record by ID
# ---------------------------------------------------------------------------
async def get_record_by_id(record_id: PydanticObjectId) -> Optional[Record]:
    """
    Fetch a single record by its MongoDB ObjectId.

    Only returns non-deleted records. Soft-deleted records are excluded
    from this query.

    Args:
        record_id: The MongoDB ObjectId of the record to fetch.

    Returns:
        The Record document if found and not deleted, otherwise None.
    """
    record = await Record.find_one(
        Record.id == record_id,
        Record.is_deleted == False,  # noqa: E712 — Beanie requires == for query
    )
    return record


# ---------------------------------------------------------------------------
# READ — List records with pagination, filtering, and search
# ---------------------------------------------------------------------------
async def get_records(
    page: int = 1,
    page_size: int = 20,
    type_filter: Optional[RecordType] = None,
    category: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = None,
    include_deleted: bool = False,
) -> PaginatedResponse[RecordResponse]:
    """
    List financial records with pagination, filtering, and text search.

    Feature 2 — Pagination:
        Results are paginated using page/page_size parameters.
        Response includes total count and total_pages for navigation.

    Feature 3 — Search & Filter:
        Filters can be combined (AND logic). Available filters:
        - type_filter:  Filter by 'income' or 'expense'
        - category:     Case-insensitive partial match on category
        - date_from:    Records on or after this date
        - date_to:      Records on or before this date
        - search:       Case-insensitive regex search across notes and category

    Soft Delete:
        By default, soft-deleted records are excluded. Pass include_deleted=True
        to include them (admin-only in the endpoint layer).

    Args:
        page:            Page number (1-indexed, default 1).
        page_size:       Items per page (default 20, max enforced in endpoint).
        type_filter:     Optional RecordType to filter by.
        category:        Optional category substring to match.
        date_from:       Optional start date for date range filter.
        date_to:         Optional end date for date range filter.
        search:          Optional search string for notes/category.
        include_deleted: If True, include soft-deleted records.

    Returns:
        PaginatedResponse containing the items list and pagination metadata.
    """
    # ── Build the query filter dictionary ────────────────────────────
    # We build this dynamically based on which parameters are provided.
    # All conditions are combined with AND logic.
    query_conditions = []

    # Soft delete filter (always applied unless explicitly overridden)
    if not include_deleted:
        query_conditions.append(Record.is_deleted == False)  # noqa: E712

    # Type filter (income/expense)
    if type_filter is not None:
        query_conditions.append(Record.type == type_filter)

    # Category filter (case-insensitive partial match)
    if category is not None:
        query_conditions.append(
            {"category": {"$regex": category, "$options": "i"}}
        )

    # Date range filter
    if date_from is not None:
        query_conditions.append(Record.date >= date_from)
    if date_to is not None:
        query_conditions.append(Record.date <= date_to)

    # Text search (case-insensitive regex across notes and category)
    if search is not None:
        query_conditions.append(
            {
                "$or": [
                    {"notes": {"$regex": search, "$options": "i"}},
                    {"category": {"$regex": search, "$options": "i"}},
                ]
            }
        )

    # ── Execute the query ────────────────────────────────────────────

    # Build the find query with all conditions
    if query_conditions:
        query = Record.find(*query_conditions)
    else:
        query = Record.find()

    # Count total matching documents (for pagination metadata)
    total = await query.count()

    # Calculate pagination values
    total_pages = max(1, math.ceil(total / page_size))
    skip = (page - 1) * page_size

    # Fetch the page of results, sorted by date descending (newest first)
    records = await query.sort(-Record.date).skip(skip).limit(page_size).to_list()

    # ── Build response ───────────────────────────────────────────────
    items = [
        RecordResponse(
            id=str(record.id),
            amount=record.amount,
            type=record.type,
            category=record.category,
            date=record.date,
            notes=record.notes,
            created_by=str(record.created_by),
            is_deleted=record.is_deleted,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
        for record in records
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# ---------------------------------------------------------------------------
# UPDATE — Modify an existing record
# ---------------------------------------------------------------------------
async def update_record(
    record_id: PydanticObjectId,
    data: RecordUpdate,
) -> Optional[Record]:
    """
    Update an existing financial record with partial data.

    Only non-deleted records can be updated. Only fields explicitly provided
    in the request body are modified (PATCH-like behavior using PUT endpoint).

    Args:
        record_id: The MongoDB ObjectId of the record to update.
        data:      Validated update data (only non-None fields are applied).

    Returns:
        The updated Record document, or None if the record wasn't found.
    """
    # Fetch the record (must exist and not be soft-deleted)
    record = await get_record_by_id(record_id)
    if record is None:
        return None

    # Apply only the fields that were explicitly provided
    # exclude_unset=True ensures we only update fields the client sent
    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        # No fields to update — return the record as-is
        return record

    # Apply each update field to the record
    for field, value in update_data.items():
        setattr(record, field, value)

    # Update the timestamp
    record.updated_at = datetime.now(timezone.utc)

    # Save to database
    await record.save()

    return record


# ---------------------------------------------------------------------------
# DELETE — Soft delete a record (Feature 4)
# ---------------------------------------------------------------------------
async def soft_delete_record(record_id: PydanticObjectId) -> Optional[Record]:
    """
    Soft-delete a financial record by setting is_deleted=True.

    The record is NOT physically removed from the database. Instead, the
    is_deleted flag is set to True, which causes all default queries to
    exclude it. Admins can still view soft-deleted records by passing
    include_deleted=True to the list endpoint.

    This approach allows:
    - Data recovery (un-delete by setting is_deleted back to False)
    - Audit trails (deleted records remain in the database)
    - Dashboard accuracy (historical data preserved)

    Args:
        record_id: The MongoDB ObjectId of the record to soft-delete.

    Returns:
        The updated Record document with is_deleted=True, or None if not found.
    """
    # Fetch the record (must exist and not already be soft-deleted)
    record = await get_record_by_id(record_id)
    if record is None:
        return None

    # Mark as deleted and update the timestamp
    record.is_deleted = True
    record.updated_at = datetime.now(timezone.utc)

    # Save to database
    await record.save()

    return record
