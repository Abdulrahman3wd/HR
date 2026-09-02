"""
public_recruitment_routes.py
==============================
Unauthenticated endpoints for the public job application page. Anyone
with a job's link can view its details and submit an application —
no login required. Heavily rate-limited to prevent spam/abuse.
"""

import time
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request

from app.config import DATA_DIR
from app.models import PublicJobResponse, PublicApplicationSubmitResponse
from app.database import get_job_opening_by_id, create_candidate
from app.cv_screening import extract_cv_text, screen_cv
from app.rate_limiter import limiter

router = APIRouter(prefix="/public", tags=["Public Job Application"])

ALLOWED_CV_EXTENSIONS = {".pdf", ".docx", ".txt"}


def get_cv_folder(company_id: int) -> Path:
    folder = DATA_DIR / "candidate_cvs" / f"company_{company_id}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


@router.get("/jobs/{job_id}", response_model=PublicJobResponse)
@limiter.limit("30/minute")
def get_public_job(request: Request, job_id: int):
    job = get_job_opening_by_id(job_id)  # no company_id — public lookup by ID alone

    if not job or job["status"] != "open":
        raise HTTPException(status_code=404, detail="This job opening is not available")

    return PublicJobResponse(
        id=job["id"],
        title=job["title"],
        description=job["description"],
        requirements=job["requirements"],
        custom_questions=job["custom_questions"],
        status=job["status"],
    )


@router.post("/jobs/{job_id}/apply", response_model=PublicApplicationSubmitResponse)
@limiter.limit("5/hour")
async def submit_public_application(
    request: Request,
    job_id: int,
    full_name: str = Form(...),
    email: str | None = Form(None),
    phone: str | None = Form(None),
    custom_answers_json: str = Form("{}"),
    cv_file: UploadFile = File(...),
):
    import json

    job = get_job_opening_by_id(job_id)
    if not job or job["status"] != "open":
        raise HTTPException(status_code=404, detail="This job opening is not available")

    company_id = job["company_id"]

    file_ext = Path(cv_file.filename).suffix.lower()
    if file_ext not in ALLOWED_CV_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported CV file type '{file_ext}'. Allowed: .pdf, .docx, .txt",
        )

    try:
        custom_answers = json.loads(custom_answers_json)
    except Exception:
        custom_answers = {}

    cv_folder = get_cv_folder(company_id)
    safe_filename = f"{int(time.time())}_{cv_file.filename}"
    file_path = cv_folder / safe_filename
    content = await cv_file.read()
    file_path.write_bytes(content)

    match_score = None
    matched_skills = None
    missing_skills = None

    try:
        cv_text = extract_cv_text(file_path)
        screening_result = screen_cv(cv_text, job["requirements"])
        match_score = screening_result["match_score"]
        matched_skills = screening_result["matched_skills"]
        missing_skills = screening_result["missing_skills"]
        if not screening_result["extraction_reliable"]:
            missing_skills = ["⚠ تعذر قراءة نص الملف بشكل موثوق (قد يكون صورة ممسوحة ضوئيًا)"]
    except Exception:
        pass

    candidate = create_candidate(
        company_id=company_id,
        job_opening_id=job_id,
        full_name=full_name,
        added_by=None,
        email=email,
        phone=phone,
        cv_filename=safe_filename,
        cv_text=cv_text if "cv_text" in dir() else None,
        match_score=match_score,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        custom_answers=custom_answers,
        source="self_applied",
    )

    return PublicApplicationSubmitResponse(
        message="Application submitted successfully",
        candidate_id=candidate["id"],
    )