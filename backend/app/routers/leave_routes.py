"""
leave_routes.py
================
Employee-facing leave request endpoints, scoped to the current company.
"""

from datetime import date
from fastapi import APIRouter, HTTPException, Depends

from app.auth import get_current_user
from app.models import LeaveRequestCreate, LeaveRequestRecord, LeaveRequestListResponse
from app.database import create_leave_request, get_leave_requests, get_user_public_data

router = APIRouter(prefix="/leave-requests", tags=["Leave Requests"])


def _calculate_days(start_date: str, end_date: str) -> int:
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Dates must be in YYYY-MM-DD format")

    if end < start:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")

    return (end - start).days + 1


@router.post("", response_model=LeaveRequestRecord)
def submit_leave_request(
    request: LeaveRequestCreate,
    current_user: dict = Depends(get_current_user),
):
    employee_id = current_user["employee_id"]
    company_id = current_user["company_id"]
    days_count = _calculate_days(request.start_date, request.end_date)

    user_data = get_user_public_data(employee_id, company_id)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    if days_count > user_data["annual_leave_balance"]:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Requested {days_count} day(s) exceed your remaining balance "
                f"of {user_data['annual_leave_balance']} day(s)"
            ),
        )

    created = create_leave_request(
        company_id=company_id,
        employee_id=employee_id,
        start_date=request.start_date,
        end_date=request.end_date,
        days_count=days_count,
        reason=request.reason,
    )
    return created


@router.get("/my", response_model=LeaveRequestListResponse)
def get_my_leave_requests(current_user: dict = Depends(get_current_user)):
    requests = get_leave_requests(current_user["company_id"], employee_id=current_user["employee_id"])
    return LeaveRequestListResponse(requests=requests, total=len(requests))