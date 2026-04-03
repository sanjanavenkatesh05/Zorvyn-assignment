# =============================================================================
# Zorvyn Finance Backend — Record Service
# =============================================================================
import math
from datetime import datetime, timezone
from typing import Optional

from beanie import PydanticObjectId

from app.models.record import Record, RecordType
from app.schemas.record import RecordCreate, RecordUpdate, RecordResponse, PaginatedResponse


async def create_record(data: RecordCreate, user_id: PydanticObjectId) -> Record:
    """Create a new financial record in the DB."""
    record = Record(
        amount=data.amount,
        type=data.type,
        category=data.category,
        date=data.date,
        notes=data.notes,
        created_by=user_id,
    )
    await record.insert()
    return record


async def get_record_by_id(record_id: PydanticObjectId) -> Optional[Record]:
    """Fetch a non-deleted single record."""
    return await Record.find_one(
        Record.id == record_id,
        Record.is_deleted == False,
    )


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
    """List financial records with pagination, text search, and filtering."""
    query_conditions = []

    if not include_deleted:
        query_conditions.append(Record.is_deleted == False)

    if type_filter is not None:
        query_conditions.append(Record.type == type_filter)

    if category is not None:
        query_conditions.append({"category": {"$regex": category, "$options": "i"}})

    if date_from is not None:
        query_conditions.append(Record.date >= date_from)
        
    if date_to is not None:
        query_conditions.append(Record.date <= date_to)

    if search is not None:
        query_conditions.append(
            {
                "$or": [
                    {"notes": {"$regex": search, "$options": "i"}},
                    {"category": {"$regex": search, "$options": "i"}},
                ]
            }
        )

    query = Record.find(*query_conditions) if query_conditions else Record.find()

    total = await query.count()
    total_pages = max(1, math.ceil(total / page_size))
    skip = (page - 1) * page_size

    records = await query.sort(-Record.date).skip(skip).limit(page_size).to_list()

    items = [
        RecordResponse(
            id=str(r.id),
            amount=r.amount,
            type=r.type,
            category=r.category,
            date=r.date,
            notes=r.notes,
            created_by=str(r.created_by),
            is_deleted=r.is_deleted,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in records
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


async def update_record(record_id: PydanticObjectId, data: RecordUpdate) -> Optional[Record]:
    """Update a non-deleted record."""
    record = await get_record_by_id(record_id)
    if record is None:
        return None

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        return record

    for field, value in update_data.items():
        setattr(record, field, value)

    record.updated_at = datetime.now(timezone.utc)
    await record.save()
    return record


async def soft_delete_record(record_id: PydanticObjectId) -> Optional[Record]:
    """Soft delete a record."""
    record = await get_record_by_id(record_id)
    if record is None:
        return None

    record.is_deleted = True
    record.updated_at = datetime.now(timezone.utc)
    await record.save()
    return record
