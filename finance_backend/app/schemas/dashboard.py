# =============================================================================
# Zorvyn Finance Backend — Dashboard Schemas
# =============================================================================
from pydantic import BaseModel, Field


class SummaryResponse(BaseModel):
    """Overall financial summary."""
    total_income: float = Field(0.0, description="Total income amount.")
    total_expenses: float = Field(0.0, description="Total expenses amount.")
    net_balance: float = Field(0.0, description="Net balance (Income - Expenses).")
    total_records: int = Field(0, description="Total number of non-deleted records.")


class CategoryBreakdown(BaseModel):
    """Breakdown of expenses/income by category."""
    category: str = Field(..., description="The category name.")
    total_amount: float = Field(..., description="Sum of amounts in this category.")
    count: int = Field(..., description="Number of transactions in this category.")
    type: str = Field(..., description="'income' or 'expense'.")


class MonthlyTrend(BaseModel):
    """Trends across months."""
    year: int = Field(..., description="Year of the trend data.")
    month: int = Field(..., description="Month of the trend data (1-12).")
    income: float = Field(0.0, description="Total income for the month.")
    expense: float = Field(0.0, description="Total expense for the month.")
    net: float = Field(0.0, description="Net balance for the month.")
