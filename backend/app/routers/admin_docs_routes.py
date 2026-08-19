"""
admin_docs_routes.py
=====================
Admin-only endpoints for uploading and indexing THIS company's policy
documents. Each company's documents and vector index are fully isolated.
"""

import time
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends

from app.auth import require_admin
from app.models import UploadResponse
from app import ingestion

router = APIRouter(prefix="/admin/docs", tags=["Admin - Documents"])

ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx"}


def ensure_folder_exists(path: Path):
    try:
        path.mkdir(parents=True, exist_ok=True)
    except FileExistsError:
        pass


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...), admin_user: dict = Depends(require_admin)):
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file_ext}'. Allowed: .txt, .pdf, .docx",
        )

    company_id = admin_user["company_id"]
    docs_path = ingestion.get_company_docs_folder(company_id)
    ensure_folder_exists(docs_path)

    file_path = docs_path / file.filename
    content = await file.read()
    was_replaced = file_path.exists()

    last_error = None
    for attempt in range(5):
        try:
            file_path.write_bytes(content)
            last_error = None
            break
        except (FileNotFoundError, PermissionError) as e:
            last_error = e
            ensure_folder_exists(docs_path)
            time.sleep(0.3)

    if last_error is not None:
        raise HTTPException(status_code=500, detail=f"Could not save file: {last_error}")

    result = ingestion.rebuild_index(company_id)

    action = "replaced" if was_replaced else "uploaded"
    return UploadResponse(
        message=f"File '{file.filename}' {action} and indexed successfully.",
        total_chunks=result["total_chunks"],
        processed_files=result["processed_files"],
    )


@router.get("/list")
def list_documents(admin_user: dict = Depends(require_admin)):
    docs_path = ingestion.get_company_docs_folder(admin_user["company_id"])
    if not docs_path.exists():
        return {"files": []}

    files = [f.name for f in docs_path.iterdir() if f.is_file()]
    return {"files": files}


@router.delete("/{filename}")
def delete_document(filename: str, admin_user: dict = Depends(require_admin)):
    company_id = admin_user["company_id"]
    docs_path = ingestion.get_company_docs_folder(company_id)
    file_path = docs_path / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    file_path.unlink()
    result = ingestion.rebuild_index(company_id)

    return {
        "message": f"File '{filename}' deleted and index rebuilt.",
        "index_summary": result,
    }