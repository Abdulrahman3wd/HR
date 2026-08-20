"""
admin_users_routes.py
======================
HR can view all users (needed for org-wide visibility and hiring context).
Only Admin can create/update/delete users or change roles — this keeps
sensitive account management restricted to the top-level admin.
"""

from fastapi import APIRouter, HTTPException, Depends

from app.auth import require_admin, require_hr_or_admin
from app.models import UserRecord, UserCreateRequest, UserUpdateRequest, UserListResponse
from app.security import hash_password
from app import database

router = APIRouter(prefix="/admin/users", tags=["Admin - Users"])

VALID_ROLES = {"admin", "hr", "employee"}


@router.get("", response_model=UserListResponse)
def get_all_users(current_user: dict = Depends(require_hr_or_admin)):
    users = database.list_users(current_user["company_id"])
    return UserListResponse(users=users, total=len(users))


@router.get("/{employee_id}", response_model=UserRecord)
def get_user(employee_id: str, current_user: dict = Depends(require_hr_or_admin)):
    user = database.get_user_public_data(employee_id.strip().upper(), current_user["company_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("", response_model=UserRecord)
def add_user(request: UserCreateRequest, admin_user: dict = Depends(require_admin)):
    employee_id = request.employee_id.strip().upper()

    if request.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Role must be one of {VALID_ROLES}")

    try:
        created = database.create_user(
            employee_id=employee_id,
            company_id=admin_user["company_id"],
            full_name=request.full_name,
            password_hash=hash_password(request.password),
            role=request.role,
            department_id=request.department_id,
            manager_id=request.manager_id,
            annual_leave_balance=request.annual_leave_balance,
            sick_leave_balance=request.sick_leave_balance,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return created


@router.put("/{employee_id}", response_model=UserRecord)
def edit_user(employee_id: str, request: UserUpdateRequest, admin_user: dict = Depends(require_admin)):
    employee_id = employee_id.strip().upper()

    if request.role and request.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Role must be one of {VALID_ROLES}")

    updates = request.model_dump()
    plain_password = updates.pop("password", None)
    if plain_password:
        updates["password_hash"] = hash_password(plain_password)

    updated = database.update_user(employee_id, admin_user["company_id"], updates)

    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    return updated


@router.delete("/{employee_id}")
def remove_user(employee_id: str, admin_user: dict = Depends(require_admin)):
    employee_id = employee_id.strip().upper()
    deleted = database.delete_user(employee_id, admin_user["company_id"])

    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": f"User '{employee_id}' deleted successfully."}