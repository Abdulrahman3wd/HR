"""
notification_routes.py
========================
Endpoints for the current user to view and manage their own
notifications, scoped to their company.
"""

from fastapi import APIRouter, HTTPException, Depends

from app.auth import get_current_user
from app.models import NotificationListResponse, UnreadCountResponse
from app.database import (
    get_notifications,
    get_unread_notification_count,
    mark_notification_as_read,
    mark_all_notifications_as_read,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationListResponse)
def list_my_notifications(current_user: dict = Depends(get_current_user)):
    notifications = get_notifications(current_user["company_id"], current_user["employee_id"])
    return NotificationListResponse(notifications=notifications, total=len(notifications))


@router.get("/unread-count", response_model=UnreadCountResponse)
def unread_count(current_user: dict = Depends(get_current_user)):
    count = get_unread_notification_count(current_user["company_id"], current_user["employee_id"])
    return UnreadCountResponse(unread_count=count)


@router.put("/{notification_id}/read")
def mark_as_read(notification_id: int, current_user: dict = Depends(get_current_user)):
    success = mark_notification_as_read(notification_id, current_user["company_id"], current_user["employee_id"])
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification marked as read"}


@router.put("/read-all")
def mark_all_as_read(current_user: dict = Depends(get_current_user)):
    mark_all_notifications_as_read(current_user["company_id"], current_user["employee_id"])
    return {"message": "All notifications marked as read"}