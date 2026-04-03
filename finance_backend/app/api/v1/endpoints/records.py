from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from beanie import PydanticObjectId

from app.models.user import User
from app.models.record import RecordType
from app.schemas.record import RecordCreate, RecordUpdate, RecordResponse, PaginatedResponse
from app.api.dependencies import get_current_user, allow_admin, allow_all_roles
from app.crud import record_service

router = APIRouter()

@router.post(
    "/",
    response_model=RecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new financial record",
    description="Create a new income or expense record. Requires Admin role.",
)
async def create_record(
    data: RecordCreate,
    current_user: User = Depends(allow_admin),
):
    """
    Create a new record. Only admins can create records.
    """
    record = await record_service.create_record(data=data, user_id=current_user.id)
    return record


@router.get(
    "/",
    response_model=PaginatedResponse[RecordResponse],
    summary="List financial records",
    description="Retrieve a paginated, filterable list of financial records. Available to all roles.",
)
async def list_records(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    type: Optional[RecordType] = Query(None, description="Filter by record type (income/expense)"),
    category: Optional[str] = Query(None, description="Filter by category (partial match)"),
    date_from: Optional[datetime] = Query(None, description="Start date for filtering"),
    date_to: Optional[datetime] = Query(None, description="End date for filtering"),
    search: Optional[str] = Query(None, description="Search text in notes and category"),
    include_deleted: bool = Query(False, description="Include soft-deleted records (Admin only)"),
    current_user: User = Depends(allow_all_roles),
):
    """
    List records with pagination, filtering, and search.
    If include_deleted=True, only admins are authorized.
    """
    if include_deleted and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view deleted records",
        )

    return await record_service.get_records(
        page=page,
        page_size=page_size,
        type_filter=type,
        category=category,
        date_from=date_from,
        date_to=date_to,
        search=search,
        include_deleted=include_deleted,
    )


@router.get(
    "/{record_id}",
    response_model=RecordResponse,
    summary="Get a single record",
    description="Retrieve a specific record by its ID. Available to all roles.",
)
async def get_record(
    record_id: PydanticObjectId,
    current_user: User = Depends(allow_all_roles),
):
    """
    Get a single record by ID. Soft-deleted records will return 404.
    """
    record = await record_service.get_record_by_id(record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found",
        )
    return record


@router.put(
    "/{record_id}",
    response_model=RecordResponse,
    summary="Update a record",
    description="Update fields of an existing record. Requires Admin role.",
)
async def update_record(
    record_id: PydanticObjectId,
    data: RecordUpdate,
    current_user: User = Depends(allow_admin),
):
    """
    Update a record. At least one field must be provided.
    """
    # Validate that at least one field is provided
    if not data.model_dump(exclude_unset=True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided for update",
        )

    record = await record_service.update_record(record_id, data)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found",
        )
    return record


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a record",
    description="Soft-delete a record. Requires Admin role.",
)
async def delete_record(
    record_id: PydanticObjectId,
    current_user: User = Depends(allow_admin),
):
    """
    Soft-delete a record by setting its is_deleted flag.
    """
    record = await record_service.soft_delete_record(record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found",
        )
    return {"detail": "Record soft-deleted successfully"}
