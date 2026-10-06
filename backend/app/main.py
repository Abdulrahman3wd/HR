"""
main.py
=======
FastAPI application entry point. Wires together all routers.

Run from the `backend` folder with:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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
    dashboard_routes,
    notification_routes,
    admin_departments_routes,
    attendance_routes,
    kpi_routes,
    recruitment_routes,
    company_settings_routes,
    late_permission_routes,
    payroll_routes,
    overtime_routes,
    public_recruitment_routes,
    interview_routes,
    public_interview_routes
)
from app.rate_limiter import limiter
from app.config import PROFILE_PICTURES_DIR
from app.database import ensure_avatar_filename_column

app = FastAPI(title="HR Agent API")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://localhost:4201",
        "http://127.0.0.1:4201",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/profile-pictures",
    StaticFiles(directory=str(PROFILE_PICTURES_DIR), check_dir=False),
    name="profile-pictures",
)


@app.on_event("startup")
def prepare_profile_picture_storage():
    PROFILE_PICTURES_DIR.mkdir(parents=True, exist_ok=True)
    ensure_avatar_filename_column()

app.include_router(auth_routes.router)
app.include_router(chat_routes.router)
app.include_router(admin_docs_routes.router)
app.include_router(admin_users_routes.router)
app.include_router(admin_chat_logs_routes.router)
app.include_router(leave_routes.router)
app.include_router(admin_leave_routes.router)
app.include_router(admin_stats_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(notification_routes.router)
app.include_router(admin_departments_routes.router)
app.include_router(attendance_routes.router)
app.include_router(kpi_routes.router)
app.include_router(recruitment_routes.router)
app.include_router(company_settings_routes.router)
app.include_router(company_settings_routes.holidays_router)
app.include_router(late_permission_routes.router)
app.include_router(payroll_routes.router)
app.include_router(overtime_routes.router)
app.include_router(public_recruitment_routes.router)
app.include_router(interview_routes.router)
app.include_router(public_interview_routes.router)
@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "message": "HR Agent API is running"}