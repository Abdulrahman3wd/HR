"""
chat_routes.py
==============
The main chat endpoint, scoped to the current user's company.
"""

from fastapi import APIRouter, HTTPException, Depends
from app.models import AskRequest, AskResponse, ChatLogListResponse
from app.database import get_user_public_data, log_chat_interaction, get_chat_logs
from app.llm import classify_question, generate_policy_answer, generate_personal_answer
from app.auth import get_current_user

router = APIRouter(tags=["Chat"])


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest, current_user: dict = Depends(get_current_user)):
    employee_id = current_user["employee_id"]
    company_id = current_user["company_id"]
    user_data = get_user_public_data(employee_id, company_id)

    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    category = classify_question(request.question)

    if category == "personal":
        answer = generate_personal_answer(user_data, request.question)
        sources = []
    else:
        answer, sources = generate_policy_answer(company_id, request.question)

    log_chat_interaction(
        company_id=company_id,
        employee_id=employee_id,
        question=request.question,
        answer=answer,
        source_type=category,
        sources=sources,
    )

    return AskResponse(answer=answer, source_type=category, sources=sources)


@router.get("/my-history", response_model=ChatLogListResponse)
def my_chat_history(current_user: dict = Depends(get_current_user), limit: int = 50):
    logs = get_chat_logs(current_user["company_id"], employee_id=current_user["employee_id"], limit=limit)
    return ChatLogListResponse(logs=logs, total=len(logs))