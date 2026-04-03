# =============================================================================
# Zorvyn Finance Backend — Record Endpoints
# =============================================================================
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from beanie import PydanticObjectId

from app.main import limiter

from app.api.dependencies import allow_admin, allow_all_roles, get_current_user
from app.models.record import RecordType
from app.models.user import User
from app.schemas.record import PaginatedResponse, RecordCreate, RecordResponse, RecordUpdate
from app.crud import record_service

router = APIRouter()


@router.post("/", response_model=RecordResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(allow_admin)])
@limiter.limit("10/minute")
async def create_record(request: Request, data: RecordCreate, current_user: User = Depends(get_current_user)):
    """Create a new financial record. Only admins can create records."""
    return await record_service.create_record(data, current_user.id)


@router.get("/", response_model=PaginatedResponse[RecordResponse], dependencies=[Depends(allow_all_roles)])
@limiter.limit("30/minute")
async def list_records(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    type: Optional[RecordType] = Query(None, description="Filter by type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    search: Optional[str] = Query(None, description="Search notes or category"),
    include_deleted: bool = Query(False, description="Include soft-deleted records"),
    current_user: User = Depends(get_current_user),
):
    """List financial records with pagination, filtering, and search."""
    if include_deleted and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view soft-deleted records.",
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


@router.get("/{record_id}", response_model=RecordResponse, dependencies=[Depends(allow_all_roles)])
async def get_record(record_id: PydanticObjectId):
    """Get a specific financial record by ID."""
    record = await record_service.get_record_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.put("/{record_id}", response_model=RecordResponse, dependencies=[Depends(allow_admin)])
async def update_record(record_id: PydanticObjectId, data: RecordUpdate):
    """Update an existing record's details. Only admins can perform this."""
    if not data.model_dump(exclude_unset=True):
        raise HTTPException(status_code=400, detail="At least one field must be updated")
        
    record = await record_service.update_record(record_id, data)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(allow_admin)])
async def delete_record(record_id: PydanticObjectId):
    """Soft delete a financial record. Only admins can perform this."""
    record = await record_service.soft_delete_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return None
