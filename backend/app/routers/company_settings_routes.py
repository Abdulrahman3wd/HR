"""
company_settings_routes.py
============================
Admin-only endpoints for configuring company-wide work rules: weekend
days, official work hours, flex-time allowance, and the monthly late
allowance used by the attendance/KPI calculations.
"""

from fastapi import APIRouter, HTTPException, Depends

from app.auth import require_admin, get_current_user
from app.models import CompanySettingsResponse, CompanySettingsUpdate, PublicHolidayCreate, PublicHolidayRecord, PublicHolidayListResponse
from app import database

router = APIRouter(prefix="/company-settings", tags=["Company Settings"])


@router.get("", response_model=CompanySettingsResponse)
def get_settings(current_user: dict = Depends(get_current_user)):
    """Readable by anyone logged in — needed by attendance/KPI calculations client-side."""
    return database.get_company_settings(current_user["company_id"])


@router.put("", response_model=CompanySettingsResponse)
def update_settings(request: CompanySettingsUpdate, admin_user: dict = Depends(require_admin)):
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    return database.update_company_settings(admin_user["company_id"], updates)


# ---------- Public Holidays ----------
holidays_router = APIRouter(prefix="/public-holidays", tags=["Public Holidays"])


@holidays_router.get("", response_model=PublicHolidayListResponse)
def list_holidays(year: int | None = None, current_user: dict = Depends(get_current_user)):
    holidays = database.list_public_holidays(current_user["company_id"], year=year)
    return PublicHolidayListResponse(holidays=holidays)


@holidays_router.post("", response_model=PublicHolidayRecord)
def add_holiday(request: PublicHolidayCreate, admin_user: dict = Depends(require_admin)):
    return database.create_public_holiday(admin_user["company_id"], request.date, request.name)


@holidays_router.delete("/{holiday_id}")
def remove_holiday(holiday_id: int, admin_user: dict = Depends(require_admin)):
    deleted = database.delete_public_holiday(holiday_id, admin_user["company_id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Holiday not found")
    return {"message": "Holiday deleted successfully"}