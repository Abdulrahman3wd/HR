"""
kpi_routes.py
=============
Quarterly KPI evaluations, computed from attendance data that was
imported from the biometric system's Excel export (never entered
manually). Managers review the computed numbers, add notes, and save.
The evaluation period is always the CURRENT quarter — determined by
today's date, not chosen freely by the user.
"""

from datetime import date, timedelta
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


def get_current_quarter() -> dict:
    """Returns the current quarter's label and date range based on today's date."""
    today = date.today()
    quarter_number = (today.month - 1) // 3 + 1
    start_month = (quarter_number - 1) * 3 + 1
    end_month = start_month + 2

    start_date = date(today.year, start_month, 1)
    if end_month == 12:
        end_date = date(today.year, 12, 31)
    else:
        next_month_first = date(today.year, end_month + 1, 1)
        end_date = next_month_first - timedelta(days=1)

    return {
        "label": f"Q{quarter_number} {today.year}",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }


def _authorize_evaluate(current_user: dict, target_employee_id: str):
    if current_user["role"] in ("admin", "hr"):
        return
    if is_in_management_chain(current_user["employee_id"], target_employee_id, current_user["company_id"]):
        return
    raise HTTPException(status_code=403, detail="Not authorized to evaluate this employee")


@router.get("/current-quarter")
def current_quarter():
    """Lets the frontend display which quarter we're currently in."""
    return get_current_quarter()


@router.get("/preview", response_model=AttendanceMetrics)
def preview_metrics(employee_id: str, current_user: dict = Depends(get_current_user)):
    company_id = current_user["company_id"]
    employee_id = employee_id.strip().upper()

    if not get_user_by_id(employee_id, company_id):
        raise HTTPException(status_code=404, detail="Employee not found")

    _authorize_evaluate(current_user, employee_id)

    quarter = get_current_quarter()
    return calculate_attendance_metrics(company_id, employee_id, quarter["start_date"], quarter["end_date"])


@router.post("", response_model=KpiEvaluationRecord)
def submit_evaluation(request: KpiEvaluationCreate, current_user: dict = Depends(get_current_user)):
    company_id = current_user["company_id"]
    employee_id = request.employee_id.strip().upper()

    if not get_user_by_id(employee_id, company_id):
        raise HTTPException(status_code=404, detail="Employee not found")

    _authorize_evaluate(current_user, employee_id)

    quarter = get_current_quarter()
    metrics = calculate_attendance_metrics(company_id, employee_id, quarter["start_date"], quarter["end_date"])

    try:
        created = create_kpi_evaluation(
            company_id=company_id,
            employee_id=employee_id,
            evaluated_by=current_user["employee_id"],
            period=quarter["label"],
            punctuality_rate=metrics["punctuality_rate"],
            attendance_rate=metrics["attendance_rate"],
            manager_notes=request.manager_notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return created


@router.get("/my", response_model=KpiEvaluationListResponse)
def get_my_evaluations(current_user: dict = Depends(get_current_user)):
    evaluations = get_kpi_evaluations(current_user["company_id"], current_user["employee_id"])
    return KpiEvaluationListResponse(evaluations=evaluations)


@router.get("/{employee_id}", response_model=KpiEvaluationListResponse)
def get_employee_evaluations(employee_id: str, current_user: dict = Depends(get_current_user)):
    company_id = current_user["company_id"]
    employee_id = employee_id.strip().upper()

    if not get_user_by_id(employee_id, company_id):
        raise HTTPException(status_code=404, detail="Employee not found")

    _authorize_evaluate(current_user, employee_id)

    evaluations = get_kpi_evaluations(company_id, employee_id)
    return KpiEvaluationListResponse(evaluations=evaluations)