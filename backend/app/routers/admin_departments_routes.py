"""
admin_departments_routes.py
=============================
HR/Admin endpoints for managing departments within a company.
"""

from fastapi import APIRouter, HTTPException, Depends

from app.auth import require_hr_or_admin
from app.models import DepartmentRecord, DepartmentCreateRequest, DepartmentListResponse
from app import database

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("", response_model=DepartmentListResponse)
def list_departments(current_user: dict = Depends(require_hr_or_admin)):
    departments = database.list_departments(current_user["company_id"])
    return DepartmentListResponse(departments=departments)


@router.post("", response_model=DepartmentRecord)
def create_department(request: DepartmentCreateRequest, current_user: dict = Depends(require_hr_or_admin)):
    return database.create_department(current_user["company_id"], request.name.strip())


@router.delete("/{department_id}")
def delete_department(department_id: int, current_user: dict = Depends(require_hr_or_admin)):
    deleted = database.delete_department(department_id, current_user["company_id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Department not found")
    return {"message": "Department deleted successfully"}