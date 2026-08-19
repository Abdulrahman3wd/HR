"""
admin_users_routes.py
======================
Admin-only endpoints for managing user accounts within THEIR OWN company.
Every query is scoped by the admin's company_id from their token, so an
admin from one company can never see or modify another company's users.
"""

from fastapi import APIRouter, HTTPException, Depends

from app.auth import require_admin
from app.models import (
    UserRecord,
    UserCreateRequest,
    UserUpdateRequest,
    UserListResponse,
)
from app.security import hash_password
from app import database

router = APIRouter(prefix="/admin/users", tags=["Admin - Users"])

VALID_ROLES = {"admin", "employee"}


@router.get("", response_model=UserListResponse, dependencies=[Depends(require_admin)])
def get_all_users(admin_user: dict = Depends(require_admin)):
    users = database.list_users(admin_user["company_id"])
    return UserListResponse(users=users, total=len(users))


@router.get("/{employee_id}", response_model=UserRecord, dependencies=[Depends(require_admin)])
def get_user(employee_id: str, admin_user: dict = Depends(require_admin)):
    user = database.get_user_public_data(employee_id.strip().upper(), admin_user["company_id"])
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
            department=request.department,
            password_hash=hash_password(request.password),
            role=request.role,
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