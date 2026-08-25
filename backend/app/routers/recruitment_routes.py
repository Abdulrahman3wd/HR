"""
recruitment_routes.py
=======================
ATS (Applicant Tracking System) endpoints:
- HR/Admin create and manage job openings
- HR/Admin add candidates (manual entry, CV upload optional)
- CV upload triggers AI screening (match score + skill breakdown) via the
  local LLM, reusing the same document readers as the policy RAG pipeline
- Candidates move through a fixed pipeline of stages
"""

import time
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form

from app.auth import require_hr_or_admin
from app.config import DATA_DIR
from app.models import (
    JobOpeningCreate,
    JobOpeningRecord,
    JobOpeningListResponse,
    CandidateRecord,
    CandidateListResponse,
    CandidateStageUpdate,
    CandidateNotesUpdate,
    CandidateInfoUpdate,
)
from app import database
from app.cv_screening import extract_cv_text, screen_cv

router = APIRouter(prefix="/recruitment", tags=["Recruitment"])

VALID_STAGES = {"applied", "reviewing", "hr_interview", "technical_interview", "accepted", "rejected"}
ALLOWED_CV_EXTENSIONS = {".pdf", ".docx", ".txt"}


def get_cv_folder(company_id: int) -> Path:
    folder = DATA_DIR / "candidate_cvs" / f"company_{company_id}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


# ---------- Job Openings ----------
@router.post("/jobs", response_model=JobOpeningRecord)
def create_job(request: JobOpeningCreate, current_user: dict = Depends(require_hr_or_admin)):
    return database.create_job_opening(
        company_id=current_user["company_id"],
        title=request.title,
        description=request.description,
        requirements=request.requirements,
        created_by=current_user["employee_id"],
        department_id=request.department_id,
    )


@router.get("/jobs", response_model=JobOpeningListResponse)
def list_jobs(status: str | None = None, current_user: dict = Depends(require_hr_or_admin)):
    jobs = database.list_job_openings(current_user["company_id"], status=status)
    return JobOpeningListResponse(jobs=jobs)


@router.put("/jobs/{job_id}/close", response_model=JobOpeningRecord)
def close_job(job_id: int, current_user: dict = Depends(require_hr_or_admin)):
    updated = database.update_job_opening_status(job_id, current_user["company_id"], "closed")
    if not updated:
        raise HTTPException(status_code=404, detail="Job opening not found")
    return updated


@router.put("/jobs/{job_id}/reopen", response_model=JobOpeningRecord)
def reopen_job(job_id: int, current_user: dict = Depends(require_hr_or_admin)):
    updated = database.update_job_opening_status(job_id, current_user["company_id"], "open")
    if not updated:
        raise HTTPException(status_code=404, detail="Job opening not found")
    return updated


# ---------- Candidates ----------
@router.post("/candidates", response_model=CandidateRecord)
async def add_candidate(
    job_opening_id: int = Form(...),
    full_name: str = Form(...),
    email: str | None = Form(None),
    phone: str | None = Form(None),
    cv_file: UploadFile | None = File(None),
    current_user: dict = Depends(require_hr_or_admin),
):
    company_id = current_user["company_id"]

    job = database.get_job_opening_by_id(job_opening_id, company_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job opening not found")

    cv_filename = None
    cv_text = None
    match_score = None
    matched_skills = None
    missing_skills = None

    if cv_file and cv_file.filename:
        file_ext = Path(cv_file.filename).suffix.lower()
        if file_ext not in ALLOWED_CV_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported CV file type '{file_ext}'. Allowed: .pdf, .docx, .txt",
            )

        cv_folder = get_cv_folder(company_id)
        safe_filename = f"{int(time.time())}_{cv_file.filename}"
        file_path = cv_folder / safe_filename
        content = await cv_file.read()
        file_path.write_bytes(content)
        cv_filename = safe_filename

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

    return database.create_candidate(
        company_id=company_id,
        job_opening_id=job_opening_id,
        full_name=full_name,
        added_by=current_user["employee_id"],
        email=email,
        phone=phone,
        cv_filename=cv_filename,
        cv_text=cv_text,
        match_score=match_score,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
    )


@router.get("/candidates", response_model=CandidateListResponse)
def list_candidates(job_opening_id: int | None = None, current_user: dict = Depends(require_hr_or_admin)):
    candidates = database.list_candidates(current_user["company_id"], job_opening_id=job_opening_id)
    return CandidateListResponse(candidates=candidates)


@router.put("/candidates/{candidate_id}/stage", response_model=CandidateRecord)
def update_stage(candidate_id: int, request: CandidateStageUpdate, current_user: dict = Depends(require_hr_or_admin)):
    if request.stage not in VALID_STAGES:
        raise HTTPException(status_code=400, detail=f"Stage must be one of {VALID_STAGES}")

    updated = database.update_candidate_stage(candidate_id, current_user["company_id"], request.stage)
    if not updated:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return updated


@router.put("/candidates/{candidate_id}/notes", response_model=CandidateRecord)
def update_notes(candidate_id: int, request: CandidateNotesUpdate, current_user: dict = Depends(require_hr_or_admin)):
    updated = database.update_candidate_notes(candidate_id, current_user["company_id"], request.notes)
    if not updated:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return updated

@router.put("/candidates/{candidate_id}", response_model=CandidateRecord)
def update_candidate(candidate_id: int, request: CandidateInfoUpdate, current_user: dict = Depends(require_hr_or_admin)):
    updated = database.update_candidate_info(
        candidate_id,
        current_user["company_id"],
        full_name=request.full_name,
        email=request.email,
        phone=request.phone,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return updated


@router.delete("/candidates/{candidate_id}")
def remove_candidate(candidate_id: int, current_user: dict = Depends(require_hr_or_admin)):
    deleted = database.delete_candidate(candidate_id, current_user["company_id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return {"message": "Candidate deleted successfully"}