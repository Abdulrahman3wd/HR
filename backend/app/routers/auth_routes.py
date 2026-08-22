"""
auth_routes.py
==============
Login (tenant-aware: requires company_code), self-service account
endpoints, and company self-signup.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from app.models import (
    LoginRequest,
    LoginResponse,
    CurrentUserResponse,
    ChangePasswordRequest,
    CompanySignupRequest,
    CompanySignupResponse,
)
from app.database import get_user_by_id, update_user, get_company_by_code
from app.security import verify_password, hash_password, create_access_token
from app.auth import get_current_user
from app.rate_limiter import limiter

router = APIRouter(tags=["Auth"])


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
def login(request: Request, login_data: LoginRequest):
    company = get_company_by_code(login_data.company_code)
    if not company or not company["is_active"]:
        raise HTTPException(status_code=401, detail="Invalid company code")

    employee_id = login_data.employee_id.strip().upper()
    user = get_user_by_id(employee_id, company["id"])

    if not user or not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid employee ID or password")

    token = create_access_token(subject=employee_id, role=user["role"], company_id=company["id"])

    return LoginResponse(
        access_token=token,
        employee_id=employee_id,
        company_id=company["id"],
        company_name=company["name"],
        full_name=user["full_name"],
        role=user["role"],
    )


@router.get("/me", response_model=CurrentUserResponse)
def get_my_profile(current_user: dict = Depends(get_current_user)):
    user = get_user_by_id(current_user["employee_id"], current_user["company_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return CurrentUserResponse(
        employee_id=user["employee_id"],
        company_id=user["company_id"],
        full_name=user["full_name"],
        department_id=user["department_id"],
        manager_id=user["manager_id"],
        role=user["role"],
        annual_leave_balance=user["annual_leave_balance"],
        sick_leave_balance=user["sick_leave_balance"],
    )


@router.put("/me/password")
def change_my_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
):
    employee_id = current_user["employee_id"]
    company_id = current_user["company_id"]
    user = get_user_by_id(employee_id, company_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(request.current_password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters long")

    update_user(employee_id, company_id, {"password_hash": hash_password(request.new_password)})

    return {"message": "Password changed successfully"}


@router.post("/signup", response_model=CompanySignupResponse)
@limiter.limit("3/hour")
def signup_company(request: Request, signup_data: CompanySignupRequest):
    """
    Self-service registration for a brand new company. Creates the company
    record and its first admin user in one step.
    """
    from app.database import _get_connection  # local import to avoid cycles

    company_code = signup_data.company_code.strip().upper()

    if get_company_by_code(company_code):
        raise HTTPException(status_code=409, detail="Company code already in use")

    if len(signup_data.admin_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")

    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO companies (company_code, name, is_active, created_at) VALUES (?, ?, 1, datetime('now'))",
        (company_code, signup_data.company_name.strip()),
    )
    company_id = cursor.lastrowid

    admin_id = signup_data.admin_employee_id.strip().upper()
    cursor.execute(
        "INSERT INTO users "
        "(employee_id, company_id, full_name, department_id, manager_id, password_hash, role, "
        "annual_leave_balance, sick_leave_balance) "
        "VALUES (?, ?, ?, NULL, NULL, ?, 'admin', 21, 7)",
        (admin_id, company_id, signup_data.admin_full_name.strip(), hash_password(signup_data.admin_password)),
    )

    conn.commit()
    conn.close()

    return CompanySignupResponse(
        message="Company registered successfully. You can now log in.",
        company_code=company_code,
    )