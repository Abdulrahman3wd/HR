"""
main.py
=======
FastAPI application entry point. Wires together all routers.

Run from the `backend` folder with:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.routers import (
    auth_routes,
    chat_routes,
    admin_docs_routes,
    admin_users_routes,
    admin_chat_logs_routes,
    leave_routes,
    admin_leave_routes,
    admin_stats_routes,
    notification_routes,
    admin_departments_routes,
    attendance_routes,
    kpi_routes,
)
from app.rate_limiter import limiter

app = FastAPI(title="HR Agent API")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(chat_routes.router)
app.include_router(admin_docs_routes.router)
app.include_router(admin_users_routes.router)
app.include_router(admin_chat_logs_routes.router)
app.include_router(leave_routes.router)
app.include_router(admin_leave_routes.router)
app.include_router(admin_stats_routes.router)
app.include_router(notification_routes.router)
app.include_router(admin_departments_routes.router)
app.include_router(attendance_routes.router)
app.include_router(kpi_routes.router)


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "message": "HR Agent API is running"}