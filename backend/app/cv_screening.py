"""
cv_screening.py
================
AI-powered CV screening: extracts text from an uploaded CV file using
layout-aware extraction (see ingestion.py's read_pdf), then asks the
local LLM to compare it against a job's requirements with a structured,
step-by-step matching prompt for higher accuracy.
"""

import json
import re
from pathlib import Path

import ollama
from app.config import OLLAMA_MODEL
from app.ingestion import read_txt, read_docx, read_pdf

# Below this character count, we assume the PDF was likely scanned
# (image-based) rather than containing real extractable text.
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
    """
    Heuristic check: if extracted text is too short, the source file was
    likely a scanned image rather than real text, and any AI score
    computed from it would be misleading.
    """
    return len(cv_text.strip()) >= MIN_VALID_CV_TEXT_LENGTH


SCREENING_PROMPT = """أنت خبير توظيف متخصص في تحليل السير الذاتية التقنية ومقارنتها بمتطلبات الوظائف بدقة عالية.

# متطلبات الوظيفة
{requirements}

# نص السيرة الذاتية للمرشح
{cv_text}

# التعليمات
حلل السيرة الذاتية خطوة بخطوة بالمنهجية التالية قبل إعطاء الإجابة النهائية:

1. استخرج كل المهارات والتقنيات المذكورة صراحة في السيرة الذاتية (من أي قسم: Skills، الخبرات العملية، المشاريع، الدورات).
2. لكل مهارة مطلوبة في متطلبات الوظيفة، تحقق من وجودها في قائمة مهارات المرشح مع مراعاة:
   - المرادفات والاختصارات الشائعة (مثال: "JS" تعني "JavaScript"، ".NET Core" تعادل "ASP.NET Core")
   - التقنيات ذات الصلة القوية التي تدل ضمنيًا على الخبرة (مثال: خبرة عملية موثقة بـ "Entity Framework Core" تدعم مهارة "ORM")
   - لا تعتبر مهارة "موجودة" إذا كانت مجرد ذكر عابر لكلمة مشابهة بدون سياق واضح يدعمها
3. لا تخترع أي مهارة غير مذكورة فعليًا أو مستنتجة بوضوح من السياق.
4. احسب نسبة التطابق (match_score) بناءً على: (عدد المهارات المطلوبة الموجودة فعليًا ÷ إجمالي عدد المهارات المطلوبة) × 100، مع تعديل بسيط حسب سنوات الخبرة ذات الصلة الظاهرة في السيرة الذاتية.

# صيغة الإجابة
أجب حصريًا بصيغة JSON صحيحة وبدون أي نص أو شرح قبلها أو بعدها، بالشكل التالي بالضبط:

{{
  "match_score": <رقم صحيح من 0 إلى 100>,
  "matched_skills": [<قائمة بأسماء المهارات المطلوبة الموجودة فعليًا في السيرة الذاتية، بصيغتها كما وردت في متطلبات الوظيفة>],
  "missing_skills": [<قائمة بأسماء المهارات المطلوبة وغير الموجودة>]
}}
"""


def _extract_json(text: str) -> dict:
    """LLMs sometimes wrap JSON in markdown fences or add stray text before/after;
    this pulls out the first {...} block and parses it defensively."""
    cleaned = re.sub(r"```(?:json)?", "", text)
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        raise ValueError("Model did not return valid JSON")
    return json.loads(match.group(0))


def screen_cv(cv_text: str, job_requirements: str) -> dict:
    """
    Returns:
        {
            "match_score": int,
            "matched_skills": list[str],
            "missing_skills": list[str],
            "extraction_reliable": bool,   # False => likely a scanned PDF
        }
    """
    extraction_reliable = is_extraction_reliable(cv_text)

    if not extraction_reliable:
        # Don't waste an LLM call on near-empty text; be explicit about the issue
        return {
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "extraction_reliable": False,
        }

    prompt = SCREENING_PROMPT.format(
        requirements=job_requirements,
        cv_text=cv_text[:MAX_CV_CHARS_FOR_LLM],
    )

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.1},  # lower temperature = more consistent scoring
    )

    raw_content = response["message"]["content"]

    try:
        parsed = _extract_json(raw_content)
        match_score = int(parsed.get("match_score", 0))
        matched_skills = list(parsed.get("matched_skills", []))
        missing_skills = list(parsed.get("missing_skills", []))
    except (ValueError, TypeError, KeyError):
        match_score = 0
        matched_skills = []
        missing_skills = []

    match_score = max(0, min(100, match_score))

    return {
        "match_score": match_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "extraction_reliable": True,
    }