"""
overtime_routes.py
====================
Employees request overtime permission in advance or after the fact.
Approval flows through the management hierarchy, same pattern as leave
requests and late permissions. Approved overtime minutes are converted
to a monetary bonus added to the employee's net salary.
"""

from fastapi import APIRouter, HTTPException, Depends

from app.auth import get_current_user
from app.models import OvertimeRequestCreate, OvertimeRequestRecord, OvertimeRequestListResponse
from app.database import (
    create_overtime_request,
    get_overtime_requests,
    get_overtime_request_by_id,
    update_overtime_request_status,
    is_in_management_chain,
)

router = APIRouter(prefix="/overtime-requests", tags=["Overtime"])


@router.post("", response_model=OvertimeRequestRecord)
def submit_overtime_request(request: OvertimeRequestCreate, current_user: dict = Depends(get_current_user)):
    return create_overtime_request(
        company_id=current_user["company_id"],
        employee_id=current_user["employee_id"],
        date=request.date,
        from_time=request.from_time,
        to_time=request.to_time,
        reason=request.reason,
    )


@router.get("/my", response_model=OvertimeRequestListResponse)
def get_my_overtime_requests(current_user: dict = Depends(get_current_user)):
    requests = get_overtime_requests(current_user["company_id"], employee_id=current_user["employee_id"])
    return OvertimeRequestListResponse(requests=requests)


@router.get("", response_model=OvertimeRequestListResponse)
def get_reviewable_overtime_requests(status: str | None = None, current_user: dict = Depends(get_current_user)):
    company_id = current_user["company_id"]

    if current_user["role"] == "admin":
        requests = get_overtime_requests(company_id, status=status)
    else:
        all_requests = get_overtime_requests(company_id, status=status)
        requests = [
            r for r in all_requests
            if is_in_management_chain(current_user["employee_id"], r["employee_id"], company_id)
        ]

    return OvertimeRequestListResponse(requests=requests)


def _authorize_review(req_id: int, current_user: dict):
    company_id = current_user["company_id"]
    if current_user["role"] == "admin":
        return

    req = get_overtime_request_by_id(req_id, company_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if not is_in_management_chain(current_user["employee_id"], req["employee_id"], company_id):
        raise HTTPException(status_code=403, detail="You are not authorized to review this request")


@router.put("/{req_id}/approve", response_model=OvertimeRequestRecord)
def approve_overtime(req_id: int, current_user: dict = Depends(get_current_user)):
    _authorize_review(req_id, current_user)
    try:
        updated = update_overtime_request_status(
            req_id, current_user["company_id"], "approved", current_user["employee_id"]
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not updated:
        raise HTTPException(status_code=404, detail="Request not found")
    return updated


@router.put("/{req_id}/reject", response_model=OvertimeRequestRecord)
def reject_overtime(req_id: int, current_user: dict = Depends(get_current_user)):
    _authorize_review(req_id, current_user)
    try:
        updated = update_overtime_request_status(
            req_id, current_user["company_id"], "rejected", current_user["employee_id"]
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not updated:
        raise HTTPException(status_code=404, detail="Request not found")
    return updated