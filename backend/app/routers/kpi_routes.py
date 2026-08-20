"""
kpi_routes.py
=============
Quarterly KPI evaluations. A manager (anyone above the employee in the
hierarchy) or admin/HR computes attendance/punctuality metrics from raw
attendance_records over a date range, reviews them, adds notes, and
saves the evaluation for that period. Employees can view their own
evaluations (read-only).
"""

from fastapi import APIRouter, HTTPException, Depends

from app.auth import get_current_user
from app.models import KpiEvaluationCreate, KpiEvaluationRecord, KpiEvaluationListResponse, AttendanceMetrics
from app.database import (
    calculate_attendance_metrics,
    create_kpi_evaluation,
    get_kpi_evaluations,
    get_user_by_id,
    is_in_management_chain,
)

router = APIRouter(prefix="/kpi", tags=["KPI Evaluations"])


def _authorize_evaluate(current_user: dict, target_employee_id: str):
    if current_user["role"] in ("admin", "hr"):
        return
    if is_in_management_chain(current_user["employee_id"], target_employee_id, current_user["company_id"]):
        return
    raise HTTPException(status_code=403, detail="Not authorized to evaluate this employee")


@router.get("/preview", response_model=AttendanceMetrics)
def preview_metrics(
    employee_id: str,
    start_date: str,
    end_date: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Lets a manager see the computed attendance/punctuality numbers BEFORE
    committing to save an evaluation, so they can review before submitting.
    """
    company_id = current_user["company_id"]
    employee_id = employee_id.strip().upper()

    if not get_user_by_id(employee_id, company_id):
        raise HTTPException(status_code=404, detail="Employee not found")

    _authorize_evaluate(current_user, employee_id)

    return calculate_attendance_metrics(company_id, employee_id, start_date, end_date)


@router.post("", response_model=KpiEvaluationRecord)
def submit_evaluation(request: KpiEvaluationCreate, current_user: dict = Depends(get_current_user)):
    company_id = current_user["company_id"]
    employee_id = request.employee_id.strip().upper()

    if not get_user_by_id(employee_id, company_id):
        raise HTTPException(status_code=404, detail="Employee not found")

    _authorize_evaluate(current_user, employee_id)

    metrics = calculate_attendance_metrics(company_id, employee_id, request.start_date, request.end_date)

    try:
        created = create_kpi_evaluation(
            company_id=company_id,
            employee_id=employee_id,
            evaluated_by=current_user["employee_id"],
            period=request.period,
            punctuality_rate=metrics["punctuality_rate"],
            attendance_rate=metrics["attendance_rate"],
            manager_notes=request.manager_notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return created


@router.get("/my", response_model=KpiEvaluationListResponse)
def get_my_evaluations(current_user: dict = Depends(get_current_user)):
    """Employees view their own evaluation history (read-only)."""
    evaluations = get_kpi_evaluations(current_user["company_id"], current_user["employee_id"])
    return KpiEvaluationListResponse(evaluations=evaluations)


@router.get("/{employee_id}", response_model=KpiEvaluationListResponse)
def get_employee_evaluations(employee_id: str, current_user: dict = Depends(get_current_user)):
    """Managers/admin/HR view a specific employee's evaluation history."""
    company_id = current_user["company_id"]
    employee_id = employee_id.strip().upper()

    if not get_user_by_id(employee_id, company_id):
        raise HTTPException(status_code=404, detail="Employee not found")

    _authorize_evaluate(current_user, employee_id)

    evaluations = get_kpi_evaluations(company_id, employee_id)
    return KpiEvaluationListResponse(evaluations=evaluations)