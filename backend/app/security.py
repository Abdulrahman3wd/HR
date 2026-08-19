"""
security.py
===========
Low-level security primitives:
- password hashing / verification (bcrypt via passlib)
- JWT creation / decoding (now tenant-aware: every token carries a company_id)
"""

from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError

from app.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, role: str, company_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {
        "sub": subject,          # employee_id
        "role": role,            # "admin" or "employee"
        "company_id": company_id,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None