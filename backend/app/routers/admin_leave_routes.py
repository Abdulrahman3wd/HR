"""
admin_leave_routes.py
=======================
Admin-only endpoints to review (approve/reject) leave requests within
THIS company only.
"""

from fastapi import APIRouter, HTTPException, Depends

from app.auth import require_admin
from app.models import LeaveRequestRecord, LeaveRequestListResponse
from app.database import get_leave_requests, update_leave_request_status

router = APIRouter(prefix="/admin/leave-requests", tags=["Admin - Leave Requests"])


@router.get("", response_model=LeaveRequestListResponse)
def get_all_leave_requests(status: str | None = None, admin_user: dict = Depends(require_admin)):
    requests = get_leave_requests(admin_user["company_id"], status=status)
    return LeaveRequestListResponse(requests=requests, total=len(requests))


@router.put("/{request_id}/approve", response_model=LeaveRequestRecord)
def approve_leave_request(request_id: int, admin_user: dict = Depends(require_admin)):
    try:
        updated = update_leave_request_status(
            request_id,
            company_id=admin_user["company_id"],
            new_status="approved",
            reviewed_by=admin_user["employee_id"],
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    if not updated:
        raise HTTPException(status_code=404, detail="Leave request not found")

    return updated


@router.put("/{request_id}/reject", response_model=LeaveRequestRecord)
def reject_leave_request(request_id: int, admin_user: dict = Depends(require_admin)):
    try:
        updated = update_leave_request_status(
            request_id,
            company_id=admin_user["company_id"],
            new_status="rejected",
            reviewed_by=admin_user["employee_id"],
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    if not updated:
        raise HTTPException(status_code=404, detail="Leave request not found")

    return updated