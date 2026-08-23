"""
late_permission_routes.py
============================
Employees request late-arrival permission (either in advance or after
the fact) for a specific date and time range. Anyone above the employee
in the management chain (or admin/HR) can approve/reject — same pattern
as leave requests. The monthly late allowance is a single shared budget
consumed by BOTH approved permissions and automatic lateness detected
from imported attendance records.
"""

from datetime import date
from fastapi import APIRouter, HTTPException, Depends

from app.auth import get_current_user
from app.models import (
    LatePermissionCreate,
    LatePermissionRecord,
    LatePermissionListResponse,
    MonthlyLateUsageResponse,
)
from app.database import (
    create_late_permission,
    get_late_permissions,
    get_late_permission_by_id,
    update_late_permission_status,
    get_monthly_late_usage,
    is_in_management_chain,
)

router = APIRouter(prefix="/late-permissions", tags=["Late Permissions"])


@router.post("", response_model=LatePermissionRecord)
def submit_late_permission(request: LatePermissionCreate, current_user: dict = Depends(get_current_user)):
    return create_late_permission(
        company_id=current_user["company_id"],
        employee_id=current_user["employee_id"],
        date=request.date,
        from_time=request.from_time,
        to_time=request.to_time,
        reason=request.reason,
    )


@router.get("/my", response_model=LatePermissionListResponse)
def get_my_permissions(current_user: dict = Depends(get_current_user)):
    permissions = get_late_permissions(current_user["company_id"], employee_id=current_user["employee_id"])
    return LatePermissionListResponse(permissions=permissions)


@router.get("/my-usage", response_model=MonthlyLateUsageResponse)
def get_my_monthly_usage(current_user: dict = Depends(get_current_user)):
    today = date.today()
    return get_monthly_late_usage(current_user["company_id"], current_user["employee_id"], today.year, today.month)


@router.get("", response_model=LatePermissionListResponse)
def get_reviewable_permissions(status: str | None = None, current_user: dict = Depends(get_current_user)):
    """Admins see all; everyone else sees only requests from people below them in the hierarchy."""
    company_id = current_user["company_id"]

    if current_user["role"] == "admin":
        permissions = get_late_permissions(company_id, status=status)
    else:
        all_permissions = get_late_permissions(company_id, status=status)
        permissions = [
            p for p in all_permissions
            if is_in_management_chain(current_user["employee_id"], p["employee_id"], company_id)
        ]

    return LatePermissionListResponse(permissions=permissions)


def _authorize_review(perm_id: int, current_user: dict):
    company_id = current_user["company_id"]
    if current_user["role"] == "admin":
        return

    perm = get_late_permission_by_id(perm_id, company_id)
    if not perm:
        raise HTTPException(status_code=404, detail="Permission request not found")

    if not is_in_management_chain(current_user["employee_id"], perm["employee_id"], company_id):
        raise HTTPException(status_code=403, detail="You are not authorized to review this request")


@router.put("/{perm_id}/approve", response_model=LatePermissionRecord)
def approve_permission(perm_id: int, current_user: dict = Depends(get_current_user)):
    _authorize_review(perm_id, current_user)
    try:
        updated = update_late_permission_status(
            perm_id, current_user["company_id"], "approved", current_user["employee_id"]
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not updated:
        raise HTTPException(status_code=404, detail="Permission request not found")
    return updated


@router.put("/{perm_id}/reject", response_model=LatePermissionRecord)
def reject_permission(perm_id: int, current_user: dict = Depends(get_current_user)):
    _authorize_review(perm_id, current_user)
    try:
        updated = update_late_permission_status(
            perm_id, current_user["company_id"], "rejected", current_user["employee_id"]
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not updated:
        raise HTTPException(status_code=404, detail="Permission request not found")
    return updated