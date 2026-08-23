"""
payroll_routes.py
==================
Net salary calculation for a given month, combining basic salary,
insurance deductions (if enabled per employee), and any deduction for
late-arrival minutes beyond the monthly allowance.

Employees can view their own net salary; managers/HR/admin can view
anyone below them in the hierarchy (or anyone, for HR/admin).
"""

from datetime import date
from fastapi import APIRouter, HTTPException, Depends

from app.auth import get_current_user
from app.models import NetSalaryResponse
from app.database import calculate_net_salary, get_user_by_id, is_in_management_chain

router = APIRouter(prefix="/payroll", tags=["Payroll"])


def _authorize_view(current_user: dict, target_employee_id: str):
    if current_user["employee_id"] == target_employee_id:
        return
    if current_user["role"] in ("admin", "hr"):
        return
    if is_in_management_chain(current_user["employee_id"], target_employee_id, current_user["company_id"]):
        return
    raise HTTPException(status_code=403, detail="Not authorized to view this employee's salary")


@router.get("/my", response_model=NetSalaryResponse)
def get_my_net_salary(year: int | None = None, month: int | None = None, current_user: dict = Depends(get_current_user)):
    today = date.today()
    y = year or today.year
    m = month or today.month

    try:
        return calculate_net_salary(current_user["company_id"], current_user["employee_id"], y, m)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{employee_id}", response_model=NetSalaryResponse)
def get_employee_net_salary(
    employee_id: str,
    year: int | None = None,
    month: int | None = None,
    current_user: dict = Depends(get_current_user),
):
    company_id = current_user["company_id"]
    employee_id = employee_id.strip().upper()

    if not get_user_by_id(employee_id, company_id):
        raise HTTPException(status_code=404, detail="Employee not found")

    _authorize_view(current_user, employee_id)

    today = date.today()
    y = year or today.year
    m = month or today.month

    try:
        return calculate_net_salary(company_id, employee_id, y, m)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))