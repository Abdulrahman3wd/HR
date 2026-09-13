"""
interview_routes.py
=====================
HR/Admin endpoints for scheduling interviews: create a scheduling
session for a candidate (sends an email with the booking link), view
schedules for a candidate, and update attendance status.
"""

from fastapi import APIRouter, HTTPException, Depends

from app.auth import require_hr_or_admin
from app.models import (
    InterviewScheduleCreate,
    InterviewScheduleRecord,
    InterviewScheduleListResponse,
    AttendanceUpdateRequest,
)
from app.database import (
    create_interview_schedule,
    get_candidate_interview_schedules,
    get_candidate_by_id,
    get_job_opening_by_id,
    update_interview_attendance,
)
from app.email_service import send_interview_scheduling_email

router = APIRouter(prefix="/interviews", tags=["Interview Scheduling"])

INTERVIEW_TYPE_LABELS = {"hr": "HR Interview", "technical": "Technical Interview"}


@router.post("", response_model=InterviewScheduleRecord)
def schedule_interview(request: InterviewScheduleCreate, current_user: dict = Depends(require_hr_or_admin)):
    company_id = current_user["company_id"]

    candidate = get_candidate_by_id(request.candidate_id, company_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    if not candidate["email"]:
        raise HTTPException(status_code=400, detail="Candidate has no email on file")

    job = get_job_opening_by_id(candidate["job_opening_id"], company_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job opening not found")

    if request.interview_type not in ("hr", "technical"):
        raise HTTPException(status_code=400, detail="interview_type must be 'hr' or 'technical'")

    if request.mode not in ("online", "offline"):
        raise HTTPException(status_code=400, detail="mode must be 'online' or 'offline'")

    schedule = create_interview_schedule(
        company_id=company_id,
        candidate_id=request.candidate_id,
        job_opening_id=candidate["job_opening_id"],
        interview_type=request.interview_type,
        mode=request.mode,
        duration_minutes=request.duration_minutes,
        interview_date=request.interview_date,
        window_start_time=request.window_start_time,
        window_end_time=request.window_end_time,
        created_by=current_user["employee_id"],
    )

    booking_link = f"http://localhost:4200/book-interview/{schedule['id']}"

    send_interview_scheduling_email(
        to_email=candidate["email"],
        candidate_name=candidate["full_name"],
        job_title=job["title"],
        interview_type_label=INTERVIEW_TYPE_LABELS[request.interview_type],
        booking_link=booking_link,
    )

    return schedule


@router.get("/candidate/{candidate_id}", response_model=InterviewScheduleListResponse)
def get_candidate_schedules(candidate_id: int, current_user: dict = Depends(require_hr_or_admin)):
    schedules = get_candidate_interview_schedules(current_user["company_id"], candidate_id)
    return InterviewScheduleListResponse(schedules=schedules)


@router.put("/{schedule_id}/attendance", response_model=InterviewScheduleRecord)
def set_attendance(schedule_id: int, request: AttendanceUpdateRequest, current_user: dict = Depends(require_hr_or_admin)):
    if request.attendance_status not in ("scheduled", "attended", "no_show"):
        raise HTTPException(status_code=400, detail="Invalid attendance status")

    updated = update_interview_attendance(schedule_id, current_user["company_id"], request.attendance_status)
    if not updated:
        raise HTTPException(status_code=404, detail="Interview schedule not found")
    return updated