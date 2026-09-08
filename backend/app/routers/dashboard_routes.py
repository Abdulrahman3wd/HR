"""Authenticated dashboard summary for all signed-in roles."""

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.database import get_dashboard_stats
from app.models import DashboardStatsResponse

router = APIRouter(prefix="/dashboard/stats", tags=["Dashboard"])


@router.get("", response_model=DashboardStatsResponse)
def get_stats(current_user: dict = Depends(get_current_user)):
    return get_dashboard_stats(current_user["company_id"])