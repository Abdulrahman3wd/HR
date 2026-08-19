"""
llm.py
======
All interactions with the local Ollama LLM.
Every policy-related answer is scoped to a single company's documents.
"""

import ollama
from app.config import OLLAMA_MODEL, SYSTEM_PROMPT_POLICY, SYSTEM_PROMPT_PERSONAL
from app.vector_store import get_relevant_context

PERSONAL_KEYWORDS = [
    "رصيدي", "باقيلي", "متبقي", "عندي كام", "رصيد اجازتي", "رصيد إجازتي",
    "my balance", "my leave balance", "how many days do i have", "remaining",
]


def classify_question(question: str) -> str:
    lowered = question.lower()
    if any(kw in question or kw in lowered for kw in PERSONAL_KEYWORDS):
        return "personal"

    classification_prompt = f"""صنّف السؤال التالي إلى واحدة من فئتين فقط، وأجب بكلمة واحدة فقط بدون أي شرح:

- اكتب "personal" فقط إذا كان السؤال يسأل تحديدًا عن رصيد إجازات الموظف نفسه أو بياناته الشخصية.
- اكتب "policy" في كل الحالات الأخرى، مثل الأسئلة عن قواعد وشروط الإجازات العامة، حتى لو ذكر السؤال رقمًا معينًا من الأيام.

أمثلة:
"كام يوم إجازة باقيلي؟" -> personal
"هل ينفع آخد 6 أيام إجازة؟" -> policy
"ما هي سياسة الإجازة المرضية؟" -> policy

السؤال: "{question}"

أجب بكلمة واحدة فقط: personal أو policy
"""
    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": classification_prompt}],
    )
    result = response["message"]["content"].strip().lower()
    return "personal" if "personal" in result else "policy"


def generate_policy_answer(company_id: int, question: str):
    """Returns (answer_text, sources_list). Only searches this company's documents."""
    context_chunks, sources = get_relevant_context(company_id, question)
    context_text = "\n---\n".join(context_chunks)

    user_prompt = f"""السياق (من ملفات سياسة الشركة):
{context_text}

سؤال الموظف: {question}
"""
    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_POLICY},
            {"role": "user", "content": user_prompt},
        ],
    )
    answer = response["message"]["content"]
    return answer, list(set(sources))


def generate_personal_answer(user_data: dict, question: str) -> str:
    user_prompt = f"""بيانات الموظف الحالي من قاعدة بيانات الموارد البشرية:
- الاسم: {user_data['full_name']}
- القسم: {user_data['department']}
- رصيد الإجازة السنوية المتبقي: {user_data['annual_leave_balance']} يوم
- رصيد الإجازة المرضية المتبقي: {user_data['sick_leave_balance']} يوم

سؤال الموظف: {question}
"""
    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_PERSONAL},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response["message"]["content"]