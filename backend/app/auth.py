"""
auth.py
=======
FastAPI dependencies for authentication/authorization, built on JWT.
"""

from fastapi import Header, HTTPException, Depends
from app.security import decode_access_token


def get_current_user(authorization: str = Header(...)) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {
        "employee_id": payload["sub"],
        "role": payload["role"],
        "company_id": payload["company_id"],
    }


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user


def require_hr_or_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    HR manages company-wide data (policies, all employee records), same as
    admin for those purposes — but HR does NOT get user-management or
    role-changing privileges (that stays admin-only).
    """
    if current_user["role"] not in ("admin", "hr"):
        raise HTTPException(status_code=403, detail="HR or admin privileges required")
    return current_user