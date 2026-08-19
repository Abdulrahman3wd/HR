"""
admin_chat_logs_routes.py
===========================
Admin-only endpoint to view THIS company's full chat audit log.
"""

from fastapi import APIRouter, Depends
from app.auth import require_admin
from app.models import ChatLogListResponse
from app.database import get_chat_logs

router = APIRouter(prefix="/admin/chat-logs", tags=["Admin - Chat Logs"])


@router.get("", response_model=ChatLogListResponse)
def get_all_chat_logs(
    employee_id: str | None = None,
    limit: int = 100,
    admin_user: dict = Depends(require_admin),
):
    logs = get_chat_logs(admin_user["company_id"], employee_id=employee_id, limit=limit)
    return ChatLogListResponse(logs=logs, total=len(logs))