"""
cv_screening.py
================
AI-powered CV screening: extracts text from an uploaded CV file using
layout-aware extraction, then checks each required skill INDIVIDUALLY
against the CV text (yes/no per skill) rather than asking the LLM to
produce the full match list in one shot. This two-step approach is
slower but far more accurate — single-skill yes/no questions hallucinate
much less than "list all matching skills" prompts.
"""

import re
from pathlib import Path

import ollama
from app.config import OLLAMA_MODEL
from app.ingestion import read_txt, read_docx, read_pdf

MIN_VALID_CV_TEXT_LENGTH = 150
MAX_CV_CHARS_FOR_LLM = 10000


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


def is_extraction_reliable(cv_text: str) -> bool:
    return len(cv_text.strip()) >= MIN_VALID_CV_TEXT_LENGTH


def _parse_requirements_to_skills(requirements: str) -> list[str]:
    """
    Splits a free-text requirements string into individual skill labels.
    Handles comma-separated lists (the common case) and falls back to
    treating the whole string as one skill if no separators are found.
    """
    # Split on commas, "و", "and", newlines, or bullet markers
    raw_parts = re.split(r"[,\n،]|(?:\bو\b)|(?:\band\b)", requirements)
    skills = [p.strip(" -•\t") for p in raw_parts]
    skills = [s for s in skills if s]
    return skills if skills else [requirements.strip()]


SKILL_CHECK_PROMPT = """نص السيرة الذاتية:
---
{cv_text}
---

هل المهارة أو التقنية التالية مذكورة صراحة في نص السيرة الذاتية أعلاه، أو مذكورة بصيغة مرادفة معروفة لها (مثل اختصار شائع)؟

المهارة: "{skill}"

أجب بكلمة واحدة فقط بدون أي شرح: "yes" أو "no".
"""


def _check_single_skill(cv_text: str, skill: str) -> bool:
    prompt = SKILL_CHECK_PROMPT.format(cv_text=cv_text[:MAX_CV_CHARS_FOR_LLM], skill=skill)

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.0},
    )

    answer = response["message"]["content"].strip().lower()
    return "yes" in answer[:10]  # check the start, avoid matching stray "yes" elsewhere


def screen_cv(cv_text: str, job_requirements: str) -> dict:
    """
    Returns:
        {
            "match_score": int,
            "matched_skills": list[str],
            "missing_skills": list[str],
            "extraction_reliable": bool,
        }
    """
    extraction_reliable = is_extraction_reliable(cv_text)

    if not extraction_reliable:
        return {
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "extraction_reliable": False,
        }

    required_skills = _parse_requirements_to_skills(job_requirements)

    matched_skills = []
    missing_skills = []

    for skill in required_skills:
        try:
            found = _check_single_skill(cv_text, skill)
        except Exception:
            found = False

        if found:
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    total = len(required_skills)
    match_score = round((len(matched_skills) / total) * 100) if total > 0 else 0

    return {
        "match_score": match_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "extraction_reliable": True,
    }