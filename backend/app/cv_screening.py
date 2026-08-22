"""
cv_screening.py
================
AI-powered CV screening: extracts text from an uploaded CV file (reusing
the same readers as ingestion.py) and asks the local LLM to compare it
against a job's requirements, returning a structured match score and
skill breakdown.
"""

import json
import re
from pathlib import Path

import ollama
from app.config import OLLAMA_MODEL
from app.ingestion import read_txt, read_docx, read_pdf


def extract_cv_text(file_path: Path) -> str:
    ext = file_path.suffix.lower()
    if ext == ".txt":
        return read_txt(file_path)
    elif ext == ".docx":
        return read_docx(file_path)
    elif ext == ".pdf":
        return read_pdf(file_path)
    else:
        raise ValueError(f"Unsupported CV file type: {ext}")


SCREENING_PROMPT = """أنت مساعد متخصص في تحليل السير الذاتية (CVs) ومقارنتها بمتطلبات الوظائف.

متطلبات الوظيفة:
{requirements}

نص السيرة الذاتية للمرشح:
{cv_text}

قارن السيرة الذاتية بمتطلبات الوظيفة، وأجب حصريًا بصيغة JSON صحيحة وبدون أي نص إضافي قبلها أو بعدها، بالشكل التالي بالضبط:

{{
  "match_score": <رقم صحيح من 0 إلى 100 يمثل نسبة التطابق>,
  "matched_skills": [<قائمة بالمهارات المطلوبة والموجودة فعليًا في السيرة الذاتية>],
  "missing_skills": [<قائمة بالمهارات المطلوبة وغير الموجودة في السيرة الذاتية>]
}}
"""


def _extract_json(text: str) -> dict:
    """LLMs sometimes wrap JSON in markdown fences or add stray text; this
    pulls out the first {...} block and parses it defensively."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("Model did not return valid JSON")
    return json.loads(match.group(0))


def screen_cv(cv_text: str, job_requirements: str) -> dict:
    prompt = SCREENING_PROMPT.format(requirements=job_requirements, cv_text=cv_text[:6000])

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_content = response["message"]["content"]

    try:
        parsed = _extract_json(raw_content)
        match_score = int(parsed.get("match_score", 0))
        matched_skills = list(parsed.get("matched_skills", []))
        missing_skills = list(parsed.get("missing_skills", []))
    except (ValueError, TypeError, KeyError):
        # Fail gracefully: screening is a helpful feature, not a hard
        # requirement — a candidate can still be added without a score.
        match_score = 0
        matched_skills = []
        missing_skills = []

    match_score = max(0, min(100, match_score))

    return {
        "match_score": match_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
    }