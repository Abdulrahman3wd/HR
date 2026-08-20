"""
attendance_import.py
======================
Parses an attendance Excel file (as exported by a biometric/fingerprint
system) and imports it into attendance_records.

Expected columns (case-insensitive, flexible naming):
    Employee ID | Date | Check In | Check Out

Rows with unknown employee IDs or missing required fields are skipped
and reported back, rather than failing the whole import.
"""

import pandas as pd
from io import BytesIO

from app.database import get_user_by_id, upsert_attendance_record

# Maps flexible column name variants to our canonical field names
COLUMN_ALIASES = {
    "employee_id": ["employee id", "employee_id", "empid", "emp id", "id"],
    "date": ["date", "attendance date", "day"],
    "check_in": ["check in", "check_in", "checkin", "time in", "in"],
    "check_out": ["check out", "check_out", "checkout", "time out", "out"],
}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized = {}
    lower_columns = {str(col).strip().lower(): col for col in df.columns}

    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lower_columns:
                normalized[lower_columns[alias]] = canonical
                break

    df = df.rename(columns=normalized)
    return df


def import_attendance_excel(company_id: int, file_bytes: bytes) -> dict:
    df = pd.read_excel(BytesIO(file_bytes))
    df = _normalize_columns(df)

    required = {"employee_id", "date", "check_in", "check_out"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing required column(s): {', '.join(missing)}. "
            f"Expected columns like: Employee ID, Date, Check In, Check Out."
        )

    imported = 0
    skipped = []

    for idx, row in df.iterrows():
        employee_id = str(row.get("employee_id", "")).strip().upper()
        raw_date = row.get("date")
        raw_check_in = row.get("check_in")
        raw_check_out = row.get("check_out")

        if not employee_id or pd.isna(raw_date):
            skipped.append({"row": int(idx) + 2, "reason": "Missing employee_id or date"})
            continue

        if not get_user_by_id(employee_id, company_id):
            skipped.append({"row": int(idx) + 2, "reason": f"Unknown employee_id '{employee_id}'"})
            continue

        try:
            date_str = pd.to_datetime(raw_date).strftime("%Y-%m-%d")
        except Exception:
            skipped.append({"row": int(idx) + 2, "reason": "Invalid date format"})
            continue

        check_in_str = _format_time(raw_check_in)
        check_out_str = _format_time(raw_check_out)

        upsert_attendance_record(
            company_id=company_id,
            employee_id=employee_id,
            date=date_str,
            check_in_time=check_in_str,
            check_out_time=check_out_str,
            source="excel_import",
        )
        imported += 1

    return {
        "imported_rows": imported,
        "skipped_rows": len(skipped),
        "skipped_details": skipped[:20],  # cap the report to avoid huge responses
    }


def _format_time(value) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return pd.to_datetime(str(value)).strftime("%H:%M")
    except Exception:
        return None