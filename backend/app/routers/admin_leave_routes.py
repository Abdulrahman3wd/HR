"""
admin_leave_routes.py
=======================
Endpoints for reviewing (approve/reject) leave requests.

Any user who appears ABOVE the requester in the management chain can
approve/reject — not just their direct manager. Admins can also review
any request in the company as a fallback/override.
"""

from fastapi import APIRouter, HTTPException, Depends

from app.auth import get_current_user
from app.models import LeaveRequestRecord, LeaveRequestListResponse
from app.database import (
    get_leave_requests,
    get_team_leave_requests,
    update_leave_request_status,
    is_in_management_chain,
)

router = APIRouter(prefix="/admin/leave-requests", tags=["Leave Requests - Review"])


@router.get("", response_model=LeaveRequestListResponse)
def get_reviewable_leave_requests(status: str | None = None, current_user: dict = Depends(get_current_user)):
    """
    Admins see every request in the company. Everyone else sees only
    requests from people below them in the management chain.
    """
    company_id = current_user["company_id"]

    if current_user["role"] == "admin":
        requests = get_leave_requests(company_id, status=status)
    else:
        requests = get_team_leave_requests(company_id, current_user["employee_id"], status=status)

    return LeaveRequestListResponse(requests=requests, total=len(requests))


def _authorize_review(request_id: int, current_user: dict):
    company_id = current_user["company_id"]

    if current_user["role"] == "admin":
        return  # admins can review anything in their company

    from app.database import get_leave_request_by_id
    request = get_leave_request_by_id(request_id, company_id)
    if not request:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if not is_in_management_chain(current_user["employee_id"], request["employee_id"], company_id):
        raise HTTPException(status_code=403, detail="You are not authorized to review this request")


@router.put("/{request_id}/approve", response_model=LeaveRequestRecord)
def approve_leave_request(request_id: int, current_user: dict = Depends(get_current_user)):
    _authorize_review(request_id, current_user)

    try:
        updated = update_leave_request_status(
            request_id,
            company_id=current_user["company_id"],
            new_status="approved",
            reviewed_by=current_user["employee_id"],
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    if not updated:
        raise HTTPException(status_code=404, detail="Leave request not found")

    return updated


@router.put("/{request_id}/reject", response_model=LeaveRequestRecord)
def reject_leave_request(request_id: int, current_user: dict = Depends(get_current_user)):
    _authorize_review(request_id, current_user)

    try:
        updated = update_leave_request_status(
            request_id,
            company_id=current_user["company_id"],
            new_status="rejected",
            reviewed_by=current_user["employee_id"],
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    if not updated:
        raise HTTPException(status_code=404, detail="Leave request not found")

    return updated