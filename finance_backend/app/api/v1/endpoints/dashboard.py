# =============================================================================
# Zorvyn Finance Backend — Dashboard Endpoints (Heavy Lifting DB Aggregations)
# =============================================================================
from typing import List, Optional
from fastapi import APIRouter, Depends
from datetime import datetime, timedelta, timezone

from app.models.record import Record, RecordType
from app.models.user import User
from app.schemas.dashboard import CategoryBreakdown, MonthlyTrend, SummaryResponse
from app.schemas.record import RecordResponse
from app.api.dependencies import allow_all_roles, allow_analyst_and_above, get_current_user

router = APIRouter()


@router.get("/summary", response_model=SummaryResponse, dependencies=[Depends(allow_all_roles)])
async def get_dashboard_summary():
    """
    Get high-level summary logic computed at the DB level via aggregation.
    """
    pipeline = [
        {"$match": {"is_deleted": False}},
        {"$group": {
            "_id": "$type",
            "total_amount": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }}
    ]
    
    results = await Record.aggregate(pipeline).to_list()
    
    response = SummaryResponse()
    for res in results:
        t_type = res["_id"]
        if t_type == RecordType.income.value:
            response.total_income = res["total_amount"]
        elif t_type == RecordType.expense.value:
            response.total_expenses = res["total_amount"]
        response.total_records += res["count"]
        
    response.net_balance = response.total_income - response.total_expenses
    return response


@router.get("/category-breakdown", response_model=List[CategoryBreakdown], dependencies=[Depends(allow_all_roles)])
async def get_category_breakdown(type: Optional[RecordType] = None):
    """
    Group records by category and sum up their totals via aggregation.
    """
    match_stage = {"is_deleted": False}
    if type:
        match_stage["type"] = type.value

    pipeline = [
        {"$match": match_stage},
        {"$group": {
            "_id": {
                "category": "$category",
                "type": "$type"
            },
            "total_amount": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"total_amount": -1}}
    ]
    
    results = await Record.aggregate(pipeline).to_list()
    return [
        CategoryBreakdown(
            category=res["_id"]["category"],
            type=res["_id"]["type"],
            total_amount=res["total_amount"],
            count=res["count"]
        ) for res in results
    ]


@router.get("/monthly-trends", response_model=List[MonthlyTrend], dependencies=[Depends(allow_analyst_and_above)])
async def get_monthly_trends(months_back: int = 12):
    """
    Extract month/year, group by it, and compute net trends.
    For Analysts and Admins only.
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30 * months_back)
    
    pipeline = [
        {"$match": {
            "is_deleted": False,
            "date": {"$gte": cutoff_date}
        }},
        {"$group": {
            "_id": {
                "year": {"$year": "$date"},
                "month": {"$month": "$date"}
            },
            "income": {
                "$sum": {
                    "$cond": [{"$eq": ["$type", "income"]}, "$amount", 0]
                }
            },
            "expense": {
                "$sum": {
                    "$cond": [{"$eq": ["$type", "expense"]}, "$amount", 0]
                }
            }
        }},
        {"$sort": {"_id.year": 1, "_id.month": 1}}
    ]
    
    results = await Record.aggregate(pipeline).to_list()
    return [
        MonthlyTrend(
            year=res["_id"]["year"],
            month=res["_id"]["month"],
            income=res["income"],
            expense=res["expense"],
            net=res["income"] - res["expense"]
        ) for res in results
    ]


@router.get("/recent-activity", response_model=List[RecordResponse], dependencies=[Depends(allow_all_roles)])
async def get_recent_activity(limit: int = 10):
    """
    Get the most recent non-deleted records.
    """
    if limit > 50:
        limit = 50
    
    records = await Record.find(Record.is_deleted == False).sort(-Record.created_at).limit(limit).to_list()
    
    return [
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
