"""
public_interview_routes.py
=============================
Unauthenticated endpoints for candidates to view and book their
interview slot. Rate-limited to prevent abuse.
"""

from fastapi import APIRouter, HTTPException, Request

from app.models import PublicInterviewInfo, BookSlotRequest, InterviewScheduleRecord
from app.database import (
    get_interview_schedule_by_id,
    get_candidate_by_id,
    get_job_opening_by_id,
    get_booked_slots_for_day,
    book_interview_slot,
)
from app.interview_slots import get_available_slots
from app.rate_limiter import limiter

router = APIRouter(prefix="/public/interviews", tags=["Public Interview Booking"])


@router.get("/{schedule_id}", response_model=PublicInterviewInfo)
@limiter.limit("30/minute")
def get_interview_info(request: Request, schedule_id: int):
    schedule = get_interview_schedule_by_id(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Interview schedule not found")

    candidate = get_candidate_by_id(schedule["candidate_id"], schedule["company_id"])
    job = get_job_opening_by_id(schedule["job_opening_id"], schedule["company_id"])

    if not candidate or not job:
        raise HTTPException(status_code=404, detail="Related data not found")

    if schedule["booked_slot_time"]:
        return PublicInterviewInfo(
            candidate_name=candidate["full_name"],
            job_title=job["title"],
            interview_type=schedule["interview_type"],
            mode=schedule["mode"],
            duration_minutes=schedule["duration_minutes"],
            interview_date=schedule["interview_date"],
            available_slots=[],
            is_booked=True,
            booked_slot_time=schedule["booked_slot_time"],
        )

    booked_slots = get_booked_slots_for_day(
        schedule["company_id"], schedule["interview_type"], schedule["interview_date"]
    )
    available_slots = get_available_slots(
        schedule["window_start_time"], schedule["window_end_time"], schedule["duration_minutes"], booked_slots
    )

    return PublicInterviewInfo(
        candidate_name=candidate["full_name"],
        job_title=job["title"],
        interview_type=schedule["interview_type"],
        mode=schedule["mode"],
        duration_minutes=schedule["duration_minutes"],
        interview_date=schedule["interview_date"],
        available_slots=available_slots,
        is_booked=False,
        booked_slot_time=None,
    )


@router.post("/{schedule_id}/book", response_model=InterviewScheduleRecord)
@limiter.limit("10/hour")
def book_slot(request: Request, schedule_id: int, body: BookSlotRequest):
    schedule = get_interview_schedule_by_id(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Interview schedule not found")

    try:
        booked = book_interview_slot(schedule_id, body.slot_time)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    if not booked:
        raise HTTPException(status_code=404, detail="Interview schedule not found")

    return booked