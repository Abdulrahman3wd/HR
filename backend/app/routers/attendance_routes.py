"""
attendance_routes.py
======================
Attendance data comes exclusively from importing the biometric system's
Excel export — no manual entry, to avoid human error/tampering. HR/Admin
uploads the file; the parser fills attendance_records for every matched
employee in one batch.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File

from app.auth import require_hr_or_admin
from app.attendance_import import import_attendance_excel

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.post("/import-excel")
async def import_excel(file: UploadFile = File(...), current_user: dict = Depends(require_hr_or_admin)):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="File must be an Excel file (.xlsx or .xls)")

    content = await file.read()

    try:
        result = import_attendance_excel(current_user["company_id"], content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {e}")

    return result