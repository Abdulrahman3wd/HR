"""
attendance_routes.py
======================
Manual attendance recording. Any manager (anyone above the employee in
the hierarchy) or admin/HR can log a day's check-in/check-out for an
employee. This table is designed to later be filled automatically by
importing the biometric system's Excel export or a direct API — the KPI
calculation logic reads from this table regardless of how it was filled.
"""

from fastapi import APIRouter, HTTPException, Depends

from app.auth import get_current_user
from app.models import AttendanceRecordCreate, AttendanceRecord
from app.database import upsert_attendance_record, get_user_by_id, is_in_management_chain

router = APIRouter(prefix="/attendance", tags=["Attendance"])


def _authorize_manage(current_user: dict, target_employee_id: str):
    if current_user["role"] in ("admin", "hr"):
        return
    if current_user["employee_id"] == target_employee_id:
        return  # employees can log their own attendance (e.g. self check-in)
    if is_in_management_chain(current_user["employee_id"], target_employee_id, current_user["company_id"]):
        return
    raise HTTPException(status_code=403, detail="Not authorized to manage this employee's attendance")


@router.post("", response_model=AttendanceRecord)
def record_attendance(request: AttendanceRecordCreate, current_user: dict = Depends(get_current_user)):
    company_id = current_user["company_id"]
    employee_id = request.employee_id.strip().upper()

    if not get_user_by_id(employee_id, company_id):
        raise HTTPException(status_code=404, detail="Employee not found")

    _authorize_manage(current_user, employee_id)

    return upsert_attendance_record(
        company_id=company_id,
        employee_id=employee_id,
        date=request.date,
        check_in_time=request.check_in_time,
        check_out_time=request.check_out_time,
        source="manual",
    )