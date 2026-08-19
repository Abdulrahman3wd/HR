"""
admin_stats_routes.py
=======================
Admin-only endpoint providing a summary of THIS company's activity.
"""

from fastapi import APIRouter, Depends

from app.auth import require_admin
from app.models import DashboardStatsResponse
from app.database import get_dashboard_stats

router = APIRouter(prefix="/admin/stats", tags=["Admin - Stats"])


@router.get("", response_model=DashboardStatsResponse)
def get_stats(admin_user: dict = Depends(require_admin)):
    return get_dashboard_stats(admin_user["company_id"])