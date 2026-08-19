"""
auth.py
=======
FastAPI dependencies for authentication/authorization, built on JWT.

Every authenticated request now carries a company_id, which routers and
database functions MUST use to filter data. This is the core mechanism
that keeps different companies' data isolated from each other.
"""

from fastapi import Header, HTTPException, Depends
from app.security import decode_access_token


def get_current_user(authorization: str = Header(...)) -> dict:
    """
    Expects header: Authorization: Bearer <token>
    Returns {"employee_id": str, "role": str, "company_id": int}
    """
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