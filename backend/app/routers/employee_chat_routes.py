"""Company-scoped one-to-one employee messaging."""

from io import BytesIO
import json
from pathlib import Path
from uuid import uuid4
from zipfile import BadZipFile, ZipFile, is_zipfile

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi import WebSocket, WebSocketDisconnect

from app import database
from app.auth import get_current_user
from app.config import EMPLOYEE_CHAT_ATTACHMENTS_DIR
from app.security import decode_access_token
from app.models import (
    EmployeeChatConversation,
    EmployeeChatConversationPage,
    EmployeeChatConversationRequest,
    EmployeeChatEmployeePage,
    EmployeeChatMessage,
    EmployeeChatMessageCreate,
    EmployeeChatMessagePage,
)

router = APIRouter(prefix="/employee-chat", tags=["Employee Chat"])
MAX_ATTACHMENT_SIZE = 15 * 1024 * 1024
ATTACHMENT_TYPES = {
    ".jpg": ("image/jpeg", "image"),
    ".jpeg": ("image/jpeg", "image"),
    ".png": ("image/png", "image"),
    ".gif": ("image/gif", "image"),
    ".webp": ("image/webp", "image"),
    ".pdf": ("application/pdf", "document"),
    ".doc": ("application/msword", "document"),
    ".docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "document"),
    ".xls": ("application/vnd.ms-excel", "spreadsheet"),
    ".xlsx": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "spreadsheet"),
    ".ppt": ("application/vnd.ms-powerpoint", "presentation"),
    ".pptx": ("application/vnd.openxmlformats-officedocument.presentationml.presentation", "presentation"),
    ".zip": ("application/zip", "archive"),
    ".rar": ("application/vnd.rar", "archive"),
    ".7z": ("application/x-7z-compressed", "archive"),
}
LEGACY_OFFICE_SIGNATURE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


def _attachment_type(extension: str, contents: bytes) -> tuple[str, bool] | None:
    if extension not in ATTACHMENT_TYPES:
        return None

    content_type, category = ATTACHMENT_TYPES[extension]
    signatures = {
        ".jpg": contents.startswith(b"\xff\xd8\xff"),
        ".jpeg": contents.startswith(b"\xff\xd8\xff"),
        ".png": contents.startswith(b"\x89PNG\r\n\x1a\n"),
        ".gif": contents.startswith((b"GIF87a", b"GIF89a")),
        ".webp": contents.startswith(b"RIFF") and contents[8:12] == b"WEBP",
        ".pdf": contents.startswith(b"%PDF-"),
        ".doc": contents.startswith(LEGACY_OFFICE_SIGNATURE),
        ".xls": contents.startswith(LEGACY_OFFICE_SIGNATURE),
        ".ppt": contents.startswith(LEGACY_OFFICE_SIGNATURE),
        ".rar": contents.startswith((b"Rar!\x1a\x07\x00", b"Rar!\x1a\x07\x01\x00")),
        ".7z": contents.startswith(b"7z\xbc\xaf\x27\x1c"),
    }

    if extension in {".docx", ".xlsx", ".pptx", ".zip"}:
        if not is_zipfile(BytesIO(contents)):
            return None
        if extension == ".docx":
            required_entry = "word/document.xml"
        elif extension == ".xlsx":
            required_entry = "xl/workbook.xml"
        elif extension == ".pptx":
            required_entry = "ppt/presentation.xml"
        else:
            required_entry = None
        if required_entry:
            try:
                with ZipFile(BytesIO(contents)) as archive:
                    if required_entry not in archive.namelist():
                        return None
            except BadZipFile:
                return None
    elif not signatures.get(extension, False):
        return None

    return content_type, category == "image"


class EmployeeChatConnections:
    def __init__(self) -> None:
        self._connections: dict[tuple[int, str], set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, company_id: int, employee_id: str) -> None:
        await websocket.accept()
        self._connections.setdefault((company_id, employee_id), set()).add(websocket)

    def disconnect(self, websocket: WebSocket, company_id: int, employee_id: str) -> None:
        key = (company_id, employee_id)
        connections = self._connections.get(key)
        if connections is None:
            return
        connections.discard(websocket)
        if not connections:
            self._connections.pop(key, None)

    async def notify(
        self,
        company_id: int,
        employee_ids: list[str],
        event: dict,
    ) -> None:
        for employee_id in set(employee_ids):
            for websocket in tuple(self._connections.get((company_id, employee_id), ())):
                try:
                    await websocket.send_json(event)
                except Exception:
                    self.disconnect(websocket, company_id, employee_id)


connections = EmployeeChatConnections()


@router.websocket("/ws")
async def employee_chat_websocket(websocket: WebSocket):
    token = websocket.query_params.get("token", "")
    payload = decode_access_token(token)
    if not payload or not payload.get("sub") or not payload.get("company_id"):
        await websocket.close(code=1008)
        return

    company_id = int(payload["company_id"])
    employee_id = str(payload["sub"])
    await connections.connect(websocket, company_id, employee_id)
    try:
        while True:
            raw_event = await websocket.receive_text()
            try:
                event = json.loads(raw_event)
            except (json.JSONDecodeError, TypeError):
                continue
            if event.get("type") != "typing" or not isinstance(event.get("is_typing"), bool):
                continue
            conversation_id = event.get("conversation_id")
            if not isinstance(conversation_id, int):
                continue
            conversation = database.get_employee_conversation(company_id, employee_id, conversation_id)
            if not conversation:
                continue
            await connections.notify(
                company_id,
                [conversation["employee_id"]],
                {
                    "type": "typing",
                    "conversation_id": conversation_id,
                    "employee_id": employee_id,
                    "is_typing": event["is_typing"],
                },
            )
    except WebSocketDisconnect:
        connections.disconnect(websocket, company_id, employee_id)


def _person(employee: dict, request: Request) -> dict:
    avatar_filename = employee.get("avatar_filename")
    avatar_url = (
        f"{str(request.base_url).rstrip('/')}/profile-pictures/{avatar_filename}"
        if avatar_filename
        else None
    )
    return {
        "employee_id": employee["employee_id"],
        "full_name": employee["full_name"],
        "avatar_url": avatar_url,
    }


def _conversation(row: dict, request: Request) -> dict:
    return {
        "id": row["id"],
        "employee": _person(row, request),
        "last_message": row.get("last_message"),
        "last_activity_at": row["last_activity_at"],
        "unread_count": row.get("unread_count", 0),
    }


def _message(row: dict) -> dict:
    attachment_id = row.get("attachment_id")
    attachment = None
    if attachment_id is not None:
        content_type = row["content_type"]
        attachment = {
            "id": attachment_id,
            "file_name": row["original_filename"],
            "content_type": content_type,
            "file_size": row["file_size"],
            "is_image": content_type.startswith("image/"),
        }
    return {
        "id": row["id"],
        "conversation_id": row["conversation_id"],
        "sender_id": row["sender_id"],
        "recipient_id": row["recipient_id"],
        "body": row["body"],
        "created_at": row["created_at"],
        "attachment": attachment,
    }


@router.get("/employees", response_model=EmployeeChatEmployeePage)
def list_employees(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    search: str | None = Query(None, max_length=100),
    current_user: dict = Depends(get_current_user),
):
    rows = database.list_chat_employees(
        current_user["company_id"],
        current_user["employee_id"],
        search,
        page_size + 1,
        (page - 1) * page_size,
    )
    has_more = len(rows) > page_size
    return EmployeeChatEmployeePage(
        employees=[_person(row, request) for row in rows[:page_size]],
        page=page,
        page_size=page_size,
        has_more=has_more,
    )


@router.get("/conversations", response_model=EmployeeChatConversationPage)
def list_conversations(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
):
    rows = database.list_employee_conversations(
        current_user["company_id"],
        current_user["employee_id"],
        page_size + 1,
        (page - 1) * page_size,
    )
    has_more = len(rows) > page_size
    return EmployeeChatConversationPage(
        conversations=[_conversation(row, request) for row in rows[:page_size]],
        page=page,
        page_size=page_size,
        has_more=has_more,
        total_unread=database.count_unread_employee_messages(
            current_user["company_id"], current_user["employee_id"]
        ),
    )


@router.post("/conversations", response_model=EmployeeChatConversation)
def start_conversation(
    body: EmployeeChatConversationRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    employee_id = current_user["employee_id"]
    other_employee_id = body.employee_id.strip().upper()
    if other_employee_id == employee_id:
        raise HTTPException(status_code=400, detail="Cannot start a conversation with yourself")

    conversation_id = database.create_employee_conversation(
        current_user["company_id"], employee_id, other_employee_id
    )
    if conversation_id is None:
        raise HTTPException(status_code=404, detail="Employee not found in your company")

    conversation = database.get_employee_conversation(
        current_user["company_id"], employee_id, conversation_id
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return _conversation(conversation, request)


@router.get("/conversations/{conversation_id}/messages", response_model=EmployeeChatMessagePage)
def list_messages(
    conversation_id: int,
    before_id: int | None = Query(None, gt=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    company_id = current_user["company_id"]
    employee_id = current_user["employee_id"]
    if not database.get_employee_conversation(company_id, employee_id, conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")

    rows = database.get_employee_messages(company_id, conversation_id, before_id, limit + 1)
    has_more = len(rows) > limit
    messages = rows[:limit]
    messages.reverse()
    return EmployeeChatMessagePage(
        messages=[_message(message) for message in messages],
        has_more=has_more,
        next_before_id=messages[0]["id"] if has_more and messages else None,
    )


@router.post("/conversations/{conversation_id}/read")
async def mark_conversation_read(
    conversation_id: int,
    current_user: dict = Depends(get_current_user),
):
    company_id = current_user["company_id"]
    employee_id = current_user["employee_id"]
    unread_total = database.mark_employee_conversation_read(company_id, employee_id, conversation_id)
    if unread_total is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await connections.notify(
        company_id,
        [employee_id],
        {
            "type": "read",
            "conversation_id": conversation_id,
            "reader_id": employee_id,
            "total_unread": unread_total,
        },
    )
    return {"conversation_id": conversation_id, "total_unread": unread_total}


@router.post("/conversations/{conversation_id}/messages", response_model=EmployeeChatMessage)
async def send_message(
    conversation_id: int,
    body: EmployeeChatMessageCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    content = body.body.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    message = database.create_employee_message(
        current_user["company_id"], conversation_id, current_user["employee_id"], content
    )
    if not message:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await connections.notify(
        current_user["company_id"],
        [message["sender_id"], message["recipient_id"]],
        {"type": "message", "message": _message(message)},
    )
    return _message(message)


@router.post("/conversations/{conversation_id}/attachments", response_model=EmployeeChatMessage)
async def send_attachment(
    conversation_id: int,
    request: Request,
    file: UploadFile = File(...),
    body: str = Form(""),
    current_user: dict = Depends(get_current_user),
):
    company_id = current_user["company_id"]
    employee_id = current_user["employee_id"]
    if not database.get_employee_conversation(company_id, employee_id, conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")

    original_filename = (file.filename or "").replace("\\", "/").rsplit("/", 1)[-1].strip()
    extension = Path(original_filename).suffix.lower()
    if extension not in ATTACHMENT_TYPES:
        await file.close()
        raise HTTPException(status_code=415, detail="Unsupported attachment type")

    contents = await file.read(MAX_ATTACHMENT_SIZE + 1)
    await file.close()
    if not contents or len(contents) > MAX_ATTACHMENT_SIZE:
        raise HTTPException(status_code=413, detail="Attachments must be between 1 byte and 15 MB")

    file_type = _attachment_type(extension, contents)
    if not file_type:
        raise HTTPException(status_code=415, detail="File content does not match its supported extension")

    content_type, _ = file_type
    storage_filename = f"company_{company_id}/{uuid4().hex}{extension}"
    attachment_path = EMPLOYEE_CHAT_ATTACHMENTS_DIR / storage_filename
    attachment_path.parent.mkdir(parents=True, exist_ok=True)
    attachment_path.write_bytes(contents)
    try:
        message = database.create_employee_attachment_message(
            company_id,
            conversation_id,
            employee_id,
            body.strip(),
            original_filename,
            storage_filename,
            content_type,
            len(contents),
        )
    except Exception:
        attachment_path.unlink(missing_ok=True)
        raise

    if not message:
        attachment_path.unlink(missing_ok=True)
        raise HTTPException(status_code=404, detail="Conversation not found")

    serialized_message = _message(message)
    await connections.notify(
        company_id,
        [message["sender_id"], message["recipient_id"]],
        {"type": "message", "message": serialized_message},
    )
    return serialized_message


@router.get("/conversations/{conversation_id}/messages/{message_id}/attachment", name="download_employee_attachment")
def download_attachment(
    conversation_id: int,
    message_id: int,
    inline: bool = Query(False),
    current_user: dict = Depends(get_current_user),
):
    attachment = database.get_employee_attachment(
        current_user["company_id"],
        current_user["employee_id"],
        conversation_id,
        message_id,
    )
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    storage_root = EMPLOYEE_CHAT_ATTACHMENTS_DIR.resolve()
    attachment_path = (storage_root / attachment["storage_filename"]).resolve()
    if not attachment_path.is_relative_to(storage_root) or not attachment_path.is_file():
        raise HTTPException(status_code=404, detail="Attachment not found")

    is_image = attachment["content_type"].startswith("image/")
    disposition = "inline" if inline and is_image else "attachment"
    return FileResponse(
        attachment_path,
        media_type=attachment["content_type"],
        filename=attachment["original_filename"],
        content_disposition_type=disposition,
    )