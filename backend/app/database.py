"""
database.py
===========
All interactions with the SQLite database.

CRITICAL: This is a multi-tenant database. Every function that touches
users, chat_logs, leave_requests, or notifications MUST filter by
company_id. Never remove a company_id filter — doing so would leak one
company's data to another.
"""

import sqlite3
from app.config import HR_DB_FILE


def _get_connection():
    conn = sqlite3.connect(HR_DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


# ---------- Companies ----------
def get_company_by_code(company_code: str) -> dict | None:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, company_code, name, is_active FROM companies WHERE company_code = ?",
        (company_code.strip().upper(),),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_company_by_id(company_id: int) -> dict | None:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, company_code, name, is_active FROM companies WHERE id = ?",
        (company_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ---------- Departments ----------
def list_departments(company_id: int) -> list[dict]:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, company_id, name FROM departments WHERE company_id = ? ORDER BY name",
        (company_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def create_department(company_id: int, name: str) -> dict:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO departments (company_id, name) VALUES (?, ?)",
        (company_id, name),
    )
    dept_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": dept_id, "company_id": company_id, "name": name}


def delete_department(department_id: int, company_id: int) -> bool:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM departments WHERE id = ? AND company_id = ?",
        (department_id, company_id),
    )
    if not cursor.fetchone():
        conn.close()
        return False

    cursor.execute("DELETE FROM departments WHERE id = ? AND company_id = ?", (department_id, company_id))
    conn.commit()
    conn.close()
    return True


# ---------- Users ----------
def get_user_by_id(employee_id: str, company_id: int) -> dict | None:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT employee_id, company_id, full_name, department_id, manager_id, role, password_hash, "
        "annual_leave_balance, sick_leave_balance "
        "FROM users WHERE employee_id = ? AND company_id = ?",
        (employee_id, company_id),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_public_data(employee_id: str, company_id: int) -> dict | None:
    user = get_user_by_id(employee_id, company_id)
    if not user:
        return None
    user.pop("password_hash", None)
    return user


def list_users(company_id: int) -> list[dict]:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT employee_id, company_id, full_name, department_id, manager_id, role, "
        "annual_leave_balance, sick_leave_balance FROM users "
        "WHERE company_id = ? ORDER BY employee_id",
        (company_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def create_user(
    employee_id: str,
    company_id: int,
    full_name: str,
    password_hash: str,
    role: str,
    annual_leave_balance: int,
    sick_leave_balance: int,
    department_id: int | None = None,
    manager_id: str | None = None,
) -> dict:
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM users WHERE employee_id = ? AND company_id = ?",
        (employee_id, company_id),
    )
    if cursor.fetchone():
        conn.close()
        raise ValueError(f"User ID '{employee_id}' already exists in this company")

    cursor.execute(
        "INSERT INTO users "
        "(employee_id, company_id, full_name, department_id, manager_id, password_hash, role, "
        "annual_leave_balance, sick_leave_balance) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (employee_id, company_id, full_name, department_id, manager_id, password_hash, role,
         annual_leave_balance, sick_leave_balance),
    )
    conn.commit()
    conn.close()

    return get_user_public_data(employee_id, company_id)


def update_user(employee_id: str, company_id: int, updates: dict) -> dict | None:
    allowed_fields = {
        "full_name", "department_id", "manager_id", "role",
        "annual_leave_balance", "sick_leave_balance", "password_hash",
    }
    fields_to_update = {k: v for k, v in updates.items() if k in allowed_fields and v is not None}

    if not fields_to_update:
        return get_user_public_data(employee_id, company_id)

    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM users WHERE employee_id = ? AND company_id = ?",
        (employee_id, company_id),
    )
    if not cursor.fetchone():
        conn.close()
        return None

    set_clause = ", ".join(f"{field} = ?" for field in fields_to_update)
    values = list(fields_to_update.values()) + [employee_id, company_id]

    cursor.execute(
        f"UPDATE users SET {set_clause} WHERE employee_id = ? AND company_id = ?",
        values,
    )
    conn.commit()
    conn.close()

    return get_user_public_data(employee_id, company_id)


def delete_user(employee_id: str, company_id: int) -> bool:
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM users WHERE employee_id = ? AND company_id = ?",
        (employee_id, company_id),
    )
    if not cursor.fetchone():
        conn.close()
        return False

    cursor.execute(
        "DELETE FROM users WHERE employee_id = ? AND company_id = ?",
        (employee_id, company_id),
    )
    conn.commit()
    conn.close()
    return True


# ---------- Organizational Hierarchy ----------
def get_direct_reports(manager_id: str, company_id: int) -> list[dict]:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT employee_id, company_id, full_name, department_id, manager_id, role, "
        "annual_leave_balance, sick_leave_balance FROM users "
        "WHERE company_id = ? AND manager_id = ? ORDER BY employee_id",
        (company_id, manager_id),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def is_in_management_chain(potential_manager_id: str, employee_id: str, company_id: int) -> bool:
    if potential_manager_id == employee_id:
        return False

    conn = _get_connection()
    cursor = conn.cursor()

    current_id = employee_id
    for _ in range(20):
        cursor.execute(
            "SELECT manager_id FROM users WHERE employee_id = ? AND company_id = ?",
            (current_id, company_id),
        )
        row = cursor.fetchone()
        if not row or not row["manager_id"]:
            break

        manager_id = row["manager_id"]
        if manager_id == potential_manager_id:
            conn.close()
            return True

        current_id = manager_id

    conn.close()
    return False


# ---------- Chat Logs ----------
def log_chat_interaction(
    company_id: int,
    employee_id: str,
    question: str,
    answer: str,
    source_type: str,
    sources: list[str],
) -> None:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_logs (company_id, employee_id, question, answer, source_type, sources, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, datetime('now'))",
        (company_id, employee_id, question, answer, source_type, ",".join(sources)),
    )
    conn.commit()
    conn.close()


def get_chat_logs(company_id: int, employee_id: str | None = None, limit: int = 100) -> list[dict]:
    conn = _get_connection()
    cursor = conn.cursor()

    if employee_id:
        cursor.execute(
            "SELECT id, company_id, employee_id, question, answer, source_type, sources, created_at "
            "FROM chat_logs WHERE company_id = ? AND employee_id = ? ORDER BY created_at DESC LIMIT ?",
            (company_id, employee_id, limit),
        )
    else:
        cursor.execute(
            "SELECT id, company_id, employee_id, question, answer, source_type, sources, created_at "
            "FROM chat_logs WHERE company_id = ? ORDER BY created_at DESC LIMIT ?",
            (company_id, limit),
        )

    rows = cursor.fetchall()
    conn.close()

    logs = []
    for row in rows:
        log = dict(row)
        log["sources"] = log["sources"].split(",") if log["sources"] else []
        logs.append(log)

    return logs


# ---------- Leave Requests ----------
def create_leave_request(
    company_id: int,
    employee_id: str,
    start_date: str,
    end_date: str,
    days_count: int,
    reason: str | None,
) -> dict:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO leave_requests "
        "(company_id, employee_id, start_date, end_date, days_count, reason, status, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, 'pending', datetime('now'))",
        (company_id, employee_id, start_date, end_date, days_count, reason),
    )
    request_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_leave_request_by_id(request_id, company_id)


def get_leave_request_by_id(request_id: int, company_id: int) -> dict | None:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM leave_requests WHERE id = ? AND company_id = ?",
        (request_id, company_id),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_leave_requests(
    company_id: int,
    employee_id: str | None = None,
    status: str | None = None,
) -> list[dict]:
    conn = _get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM leave_requests WHERE company_id = ?"
    params = [company_id]

    if employee_id:
        query += " AND employee_id = ?"
        params.append(employee_id)

    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY created_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_team_leave_requests(company_id: int, manager_id: str, status: str | None = None) -> list[dict]:
    all_requests = get_leave_requests(company_id, status=status)
    return [
        req for req in all_requests
        if is_in_management_chain(manager_id, req["employee_id"], company_id)
    ]


def update_leave_request_status(
    request_id: int,
    company_id: int,
    new_status: str,
    reviewed_by: str,
) -> dict | None:
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM leave_requests WHERE id = ? AND company_id = ?",
        (request_id, company_id),
    )
    request_row = cursor.fetchone()
    if not request_row:
        conn.close()
        return None

    request = dict(request_row)

    if request["status"] != "pending":
        conn.close()
        raise ValueError(f"Leave request is already '{request['status']}' and cannot be changed")

    cursor.execute(
        "UPDATE leave_requests SET status = ?, reviewed_by = ?, reviewed_at = datetime('now') "
        "WHERE id = ? AND company_id = ?",
        (new_status, reviewed_by, request_id, company_id),
    )

    if new_status == "approved":
        cursor.execute(
            "UPDATE users SET annual_leave_balance = annual_leave_balance - ? "
            "WHERE employee_id = ? AND company_id = ?",
            (request["days_count"], request["employee_id"], company_id),
        )

    conn.commit()
    conn.close()

    if new_status == "approved":
        message = (
            f"تمت الموافقة على طلب إجازتك من {request['start_date']} إلى {request['end_date']} "
            f"({request['days_count']} يوم) بواسطة {reviewed_by}."
        )
    else:
        message = f"تم رفض طلب إجازتك من {request['start_date']} إلى {request['end_date']} بواسطة {reviewed_by}."
    create_notification(company_id, request["employee_id"], message)

    return get_leave_request_by_id(request_id, company_id)


# ---------- Notifications ----------
def create_notification(company_id: int, employee_id: str, message: str) -> None:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO notifications (company_id, employee_id, message, is_read, created_at) "
        "VALUES (?, ?, ?, 0, datetime('now'))",
        (company_id, employee_id, message),
    )
    conn.commit()
    conn.close()


def get_notifications(company_id: int, employee_id: str, limit: int = 50) -> list[dict]:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, company_id, employee_id, message, is_read, created_at "
        "FROM notifications WHERE company_id = ? AND employee_id = ? ORDER BY created_at DESC LIMIT ?",
        (company_id, employee_id, limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_unread_notification_count(company_id: int, employee_id: str) -> int:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) as count FROM notifications WHERE company_id = ? AND employee_id = ? AND is_read = 0",
        (company_id, employee_id),
    )
    count = cursor.fetchone()["count"]
    conn.close()
    return count


def mark_notification_as_read(notification_id: int, company_id: int, employee_id: str) -> bool:
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM notifications WHERE id = ? AND company_id = ? AND employee_id = ?",
        (notification_id, company_id, employee_id),
    )
    if not cursor.fetchone():
        conn.close()
        return False

    cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
    conn.commit()
    conn.close()
    return True


def mark_all_notifications_as_read(company_id: int, employee_id: str) -> None:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE notifications SET is_read = 1 WHERE company_id = ? AND employee_id = ? AND is_read = 0",
        (company_id, employee_id),
    )
    conn.commit()
    conn.close()


# ---------- Dashboard Stats ----------
def get_dashboard_stats(company_id: int) -> dict:
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as count FROM users WHERE company_id = ? AND role = 'employee'", (company_id,))
    employee_count = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM users WHERE company_id = ? AND role = 'admin'", (company_id,))
    admin_count = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM users WHERE company_id = ? AND role = 'hr'", (company_id,))
    hr_count = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM leave_requests WHERE company_id = ? AND status = 'pending'", (company_id,))
    pending_leaves = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM leave_requests WHERE company_id = ? AND status = 'approved'", (company_id,))
    approved_leaves = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM leave_requests WHERE company_id = ? AND status = 'rejected'", (company_id,))
    rejected_leaves = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM chat_logs WHERE company_id = ?", (company_id,))
    total_questions = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM chat_logs WHERE company_id = ? AND source_type = 'policy'", (company_id,))
    policy_questions = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM chat_logs WHERE company_id = ? AND source_type = 'personal'", (company_id,))
    personal_questions = cursor.fetchone()["count"]

    cursor.execute("""
        SELECT employee_id, COUNT(*) as question_count
        FROM chat_logs
        WHERE company_id = ?
        GROUP BY employee_id
        ORDER BY question_count DESC
        LIMIT 5
    """, (company_id,))
    top_users = [{"employee_id": row["employee_id"], "question_count": row["question_count"]} for row in cursor.fetchall()]

    conn.close()

    return {
        "employee_count": employee_count,
        "admin_count": admin_count,
        "hr_count": hr_count,
        "total_users": employee_count + admin_count + hr_count,
        "pending_leaves": pending_leaves,
        "approved_leaves": approved_leaves,
        "rejected_leaves": rejected_leaves,
        "total_leave_requests": pending_leaves + approved_leaves + rejected_leaves,
        "total_questions": total_questions,
        "policy_questions": policy_questions,
        "personal_questions": personal_questions,
        "top_users": top_users,
    }

# ---------- Attendance ----------
def upsert_attendance_record(
    company_id: int,
    employee_id: str,
    date: str,
    check_in_time: str | None,
    check_out_time: str | None,
    source: str = "manual",
) -> dict:
    """
    Inserts a new attendance record, or updates the existing one for the
    same (company, employee, date) — this makes bulk Excel imports safe
    to re-run without creating duplicates.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO attendance_records (company_id, employee_id, date, check_in_time, check_out_time, source, created_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(company_id, employee_id, date)
        DO UPDATE SET check_in_time = excluded.check_in_time,
                      check_out_time = excluded.check_out_time,
                      source = excluded.source
        """,
        (company_id, employee_id, date, check_in_time, check_out_time, source),
    )
    conn.commit()
    conn.close()

    return get_attendance_for_employee(company_id, employee_id, date, date)[0]


def get_attendance_for_employee(
    company_id: int, employee_id: str, start_date: str, end_date: str
) -> list[dict]:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, company_id, employee_id, date, check_in_time, check_out_time, source "
        "FROM attendance_records WHERE company_id = ? AND employee_id = ? "
        "AND date >= ? AND date <= ? ORDER BY date",
        (company_id, employee_id, start_date, end_date),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def calculate_attendance_metrics(
    company_id: int,
    employee_id: str,
    start_date: str,
    end_date: str,
) -> dict:
    """
    Computes attendance/punctuality metrics from raw attendance_records,
    using the company's actual configured weekend days, work hours, and
    public holidays — not hardcoded assumptions.

    Net daily lateness = (actual check-in - official start) 
                        + (official end - actual check-out)
    Any early/late arrival that gets offset by staying later/leaving
    earlier reduces the net lateness for that day (never goes negative).
    """
    from datetime import date as date_cls, datetime, timedelta

    settings = get_company_settings(company_id)
    weekend_days = set(settings["weekend_days"])
    work_start = settings["work_start_time"]
    work_end = settings["work_end_time"]

    year = date_cls.fromisoformat(start_date).year
    holiday_dates = get_holiday_dates_set(company_id, year=year)
    # Also include the following year's holidays in case the range spans Dec-Jan
    end_year = date_cls.fromisoformat(end_date).year
    if end_year != year:
        holiday_dates |= get_holiday_dates_set(company_id, year=end_year)

    # Expected work days: weekdays that aren't a configured weekend day
    # and aren't a public holiday
    start = date_cls.fromisoformat(start_date)
    end = date_cls.fromisoformat(end_date)
    expected_work_days = 0
    current = start
    while current <= end:
        is_weekend = current.weekday() in weekend_days
        is_holiday = current.isoformat() in holiday_dates
        if not is_weekend and not is_holiday:
            expected_work_days += 1
        current += timedelta(days=1)

    records = get_attendance_for_employee(company_id, employee_id, start_date, end_date)
    days_present = len(records)

    def to_minutes(t: str) -> int:
        h, m = map(int, t.split(":"))
        return h * 60 + m

    work_start_min = to_minutes(work_start)
    work_end_min = to_minutes(work_end)

    total_net_late_minutes = 0
    days_on_time = 0

    for r in records:
        check_in = r["check_in_time"]
        check_out = r["check_out_time"]

        late_arrival = 0
        if check_in:
            late_arrival = max(0, to_minutes(check_in) - work_start_min)

        late_departure_offset = 0
        if check_out:
            late_departure_offset = max(0, work_end_min - to_minutes(check_out))
            # staying later than official end reduces lateness too
            stayed_extra = max(0, to_minutes(check_out) - work_end_min)
            late_departure_offset = max(0, late_departure_offset - stayed_extra)

        net_late = max(0, late_arrival - 0) + late_departure_offset
        # If the employee arrived early, that can offset a late departure too
        arrived_early = max(0, work_start_min - to_minutes(check_in)) if check_in else 0
        net_late = max(0, late_arrival + late_departure_offset - arrived_early)

        total_net_late_minutes += net_late
        if net_late == 0:
            days_on_time += 1

    attendance_rate = round((days_present / expected_work_days) * 100, 1) if expected_work_days > 0 else 0.0
    punctuality_rate = round((days_on_time / days_present) * 100, 1) if days_present > 0 else 0.0

    return {
        "days_present": days_present,
        "expected_work_days": expected_work_days,
        "days_on_time": days_on_time,
        "attendance_rate": attendance_rate,
        "punctuality_rate": punctuality_rate,
        "total_net_late_minutes": total_net_late_minutes,
    }
# ---------- KPI Evaluations ----------
def create_kpi_evaluation(
    company_id: int,
    employee_id: str,
    evaluated_by: str,
    period: str,
    punctuality_rate: float,
    attendance_rate: float,
    manager_notes: str | None,
) -> dict:
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM kpi_evaluations WHERE company_id = ? AND employee_id = ? AND period = ?",
        (company_id, employee_id, period),
    )
    if cursor.fetchone():
        conn.close()
        raise ValueError(f"An evaluation for period '{period}' already exists for this employee")

    cursor.execute(
        """
        INSERT INTO kpi_evaluations
        (company_id, employee_id, evaluated_by, period, punctuality_rate, attendance_rate, manager_notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """,
        (company_id, employee_id, evaluated_by, period, punctuality_rate, attendance_rate, manager_notes),
    )
    eval_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return get_kpi_evaluation_by_id(eval_id, company_id)


def get_kpi_evaluation_by_id(eval_id: int, company_id: int) -> dict | None:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM kpi_evaluations WHERE id = ? AND company_id = ?",
        (eval_id, company_id),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_kpi_evaluations(company_id: int, employee_id: str) -> list[dict]:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM kpi_evaluations WHERE company_id = ? AND employee_id = ? ORDER BY period DESC",
        (company_id, employee_id),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# ---------- Job Openings ----------
def create_job_opening(
    company_id: int,
    title: str,
    description: str,
    requirements: str,
    created_by: str,
    department_id: int | None = None,
) -> dict:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO job_openings (company_id, title, department_id, description, requirements, status, created_by, created_at) "
        "VALUES (?, ?, ?, ?, ?, 'open', ?, datetime('now'))",
        (company_id, title, department_id, description, requirements, created_by),
    )
    job_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_job_opening_by_id(job_id, company_id)


def get_job_opening_by_id(job_id: int, company_id: int) -> dict | None:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM job_openings WHERE id = ? AND company_id = ?", (job_id, company_id))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def list_job_openings(company_id: int, status: str | None = None) -> list[dict]:
    conn = _get_connection()
    cursor = conn.cursor()
    if status:
        cursor.execute(
            "SELECT * FROM job_openings WHERE company_id = ? AND status = ? ORDER BY created_at DESC",
            (company_id, status),
        )
    else:
        cursor.execute(
            "SELECT * FROM job_openings WHERE company_id = ? ORDER BY created_at DESC",
            (company_id,),
        )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_job_opening_status(job_id: int, company_id: int, status: str) -> dict | None:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM job_openings WHERE id = ? AND company_id = ?", (job_id, company_id))
    if not cursor.fetchone():
        conn.close()
        return None

    cursor.execute(
        "UPDATE job_openings SET status = ? WHERE id = ? AND company_id = ?",
        (status, job_id, company_id),
    )
    conn.commit()
    conn.close()
    return get_job_opening_by_id(job_id, company_id)


# ---------- Candidates ----------
def create_candidate(
    company_id: int,
    job_opening_id: int,
    full_name: str,
    added_by: str,
    email: str | None = None,
    phone: str | None = None,
    cv_filename: str | None = None,
    cv_text: str | None = None,
    match_score: int | None = None,
    matched_skills: list[str] | None = None,
    missing_skills: list[str] | None = None,
) -> dict:
    import json

    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO candidates
        (company_id, job_opening_id, full_name, email, phone, cv_filename, cv_text,
         match_score, matched_skills, missing_skills, stage, added_by, applied_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'applied', ?, datetime('now'))
        """,
        (
            company_id, job_opening_id, full_name, email, phone, cv_filename, cv_text,
            match_score,
            json.dumps(matched_skills) if matched_skills else None,
            json.dumps(missing_skills) if missing_skills else None,
            added_by,
        ),
    )
    candidate_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_candidate_by_id(candidate_id, company_id)


def _parse_candidate_row(row: dict) -> dict:
    import json
    row["matched_skills"] = json.loads(row["matched_skills"]) if row["matched_skills"] else []
    row["missing_skills"] = json.loads(row["missing_skills"]) if row["missing_skills"] else []
    return row


def get_candidate_by_id(candidate_id: int, company_id: int) -> dict | None:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM candidates WHERE id = ? AND company_id = ?", (candidate_id, company_id))
    row = cursor.fetchone()
    conn.close()
    return _parse_candidate_row(dict(row)) if row else None


def list_candidates(company_id: int, job_opening_id: int | None = None) -> list[dict]:
    conn = _get_connection()
    cursor = conn.cursor()
    if job_opening_id:
        cursor.execute(
            "SELECT * FROM candidates WHERE company_id = ? AND job_opening_id = ? ORDER BY applied_at DESC",
            (company_id, job_opening_id),
        )
    else:
        cursor.execute(
            "SELECT * FROM candidates WHERE company_id = ? ORDER BY applied_at DESC",
            (company_id,),
        )
    rows = cursor.fetchall()
    conn.close()
    return [_parse_candidate_row(dict(row)) for row in rows]


def update_candidate_stage(candidate_id: int, company_id: int, stage: str) -> dict | None:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM candidates WHERE id = ? AND company_id = ?", (candidate_id, company_id))
    if not cursor.fetchone():
        conn.close()
        return None

    cursor.execute(
        "UPDATE candidates SET stage = ? WHERE id = ? AND company_id = ?",
        (stage, candidate_id, company_id),
    )
    conn.commit()
    conn.close()
    return get_candidate_by_id(candidate_id, company_id)


def update_candidate_notes(candidate_id: int, company_id: int, notes: str) -> dict | None:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM candidates WHERE id = ? AND company_id = ?", (candidate_id, company_id))
    if not cursor.fetchone():
        conn.close()
        return None

    cursor.execute(
        "UPDATE candidates SET notes = ? WHERE id = ? AND company_id = ?",
        (notes, candidate_id, company_id),
    )
    conn.commit()
    conn.close()
    return get_candidate_by_id(candidate_id, company_id)

# ---------- Company Settings ----------
def get_company_settings(company_id: int) -> dict:
    import json

    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM company_settings WHERE company_id = ?", (company_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        # Sensible defaults if a company somehow has no settings row yet
        return {
            "company_id": company_id,
            "weekend_days": [4],
            "work_start_time": "09:00",
            "work_end_time": "17:00",
            "flex_minutes": 60,
            "monthly_late_allowance_minutes": 120,
        }

    settings = dict(row)
    settings["weekend_days"] = json.loads(settings["weekend_days"])
    return settings


def update_company_settings(company_id: int, updates: dict) -> dict:
    import json

    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM company_settings WHERE company_id = ?", (company_id,))
    exists = cursor.fetchone()

    payload = dict(updates)
    if "weekend_days" in payload:
        payload["weekend_days"] = json.dumps(payload["weekend_days"])

    if not exists:
        cursor.execute(
            "INSERT INTO company_settings (company_id, weekend_days, work_start_time, work_end_time, "
            "flex_minutes, monthly_late_allowance_minutes) VALUES (?, ?, ?, ?, ?, ?)",
            (
                company_id,
                payload.get("weekend_days", "[4]"),
                payload.get("work_start_time", "09:00"),
                payload.get("work_end_time", "17:00"),
                payload.get("flex_minutes", 60),
                payload.get("monthly_late_allowance_minutes", 120),
            ),
        )
    else:
        allowed_fields = {"weekend_days", "work_start_time", "work_end_time", "flex_minutes", "monthly_late_allowance_minutes"}
        fields_to_update = {k: v for k, v in payload.items() if k in allowed_fields}
        if fields_to_update:
            set_clause = ", ".join(f"{field} = ?" for field in fields_to_update)
            values = list(fields_to_update.values()) + [company_id]
            cursor.execute(f"UPDATE company_settings SET {set_clause} WHERE company_id = ?", values)

    conn.commit()
    conn.close()
    return get_company_settings(company_id)


# ---------- Public Holidays ----------
def list_public_holidays(company_id: int, year: int | None = None) -> list[dict]:
    conn = _get_connection()
    cursor = conn.cursor()
    if year:
        cursor.execute(
            "SELECT * FROM public_holidays WHERE company_id = ? AND date LIKE ? ORDER BY date",
            (company_id, f"{year}-%"),
        )
    else:
        cursor.execute(
            "SELECT * FROM public_holidays WHERE company_id = ? ORDER BY date",
            (company_id,),
        )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def create_public_holiday(company_id: int, date: str, name: str) -> dict:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO public_holidays (company_id, date, name) VALUES (?, ?, ?)",
        (company_id, date, name),
    )
    holiday_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": holiday_id, "company_id": company_id, "date": date, "name": name}


def delete_public_holiday(holiday_id: int, company_id: int) -> bool:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM public_holidays WHERE id = ? AND company_id = ?",
        (holiday_id, company_id),
    )
    if not cursor.fetchone():
        conn.close()
        return False

    cursor.execute("DELETE FROM public_holidays WHERE id = ? AND company_id = ?", (holiday_id, company_id))
    conn.commit()
    conn.close()
    return True


def get_holiday_dates_set(company_id: int, year: int | None = None) -> set[str]:
    """Convenience helper: returns just the date strings, for quick membership checks."""
    holidays = list_public_holidays(company_id, year=year)
    return {h["date"] for h in holidays}

# ---------- Late Permissions ----------
def create_late_permission(
    company_id: int, employee_id: str, date: str, from_time: str, to_time: str, reason: str | None
) -> dict:
    def to_minutes(t: str) -> int:
        h, m = map(int, t.split(":"))
        return h * 60 + m

    minutes_count = max(0, to_minutes(to_time) - to_minutes(from_time))

    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO late_permissions "
        "(company_id, employee_id, date, from_time, to_time, minutes_count, reason, status, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', datetime('now'))",
        (company_id, employee_id, date, from_time, to_time, minutes_count, reason),
    )
    perm_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_late_permission_by_id(perm_id, company_id)


def get_late_permission_by_id(perm_id: int, company_id: int) -> dict | None:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM late_permissions WHERE id = ? AND company_id = ?", (perm_id, company_id))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_late_permissions(company_id: int, employee_id: str | None = None, status: str | None = None) -> list[dict]:
    conn = _get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM late_permissions WHERE company_id = ?"
    params = [company_id]
    if employee_id:
        query += " AND employee_id = ?"
        params.append(employee_id)
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY created_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_late_permission_status(perm_id: int, company_id: int, new_status: str, reviewed_by: str) -> dict | None:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM late_permissions WHERE id = ? AND company_id = ?", (perm_id, company_id))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    perm = dict(row)
    if perm["status"] != "pending":
        conn.close()
        raise ValueError(f"Permission is already '{perm['status']}'")

    cursor.execute(
        "UPDATE late_permissions SET status = ?, reviewed_by = ?, reviewed_at = datetime('now') "
        "WHERE id = ? AND company_id = ?",
        (new_status, reviewed_by, perm_id, company_id),
    )
    conn.commit()
    conn.close()

    message = (
        f"تمت الموافقة على إذن التأخير بتاريخ {perm['date']} من {perm['from_time']} إلى {perm['to_time']}."
        if new_status == "approved"
        else f"تم رفض إذن التأخير بتاريخ {perm['date']}."
    )
    create_notification(company_id, perm["employee_id"], message)

    return get_late_permission_by_id(perm_id, company_id)


def get_monthly_late_usage(company_id: int, employee_id: str, year: int, month: int) -> dict:
    """
    Computes total late minutes consumed this month from BOTH sources:
    - approved late_permissions for days that HAVE a permission
    - automatic net-lateness from attendance_records for days WITHOUT one
    (a day is never double-counted between the two sources).
    """
    from calendar import monthrange

    start_date = f"{year:04d}-{month:02d}-01"
    last_day = monthrange(year, month)[1]
    end_date = f"{year:04d}-{month:02d}-{last_day:02d}"

    approved_permissions = [
        p for p in get_late_permissions(company_id, employee_id=employee_id, status="approved")
        if start_date <= p["date"] <= end_date
    ]
    permission_dates = {p["date"] for p in approved_permissions}
    permission_minutes = sum(p["minutes_count"] for p in approved_permissions)

    settings = get_company_settings(company_id)
    work_start = settings["work_start_time"]
    work_end = settings["work_end_time"]

    def to_minutes(t: str) -> int:
        h, m = map(int, t.split(":"))
        return h * 60 + m

    work_start_min = to_minutes(work_start)
    work_end_min = to_minutes(work_end)

    records = get_attendance_for_employee(company_id, employee_id, start_date, end_date)
    attendance_minutes = 0

    for r in records:
        if r["date"] in permission_dates:
            continue  # already counted via the permission for that day

        check_in = r["check_in_time"]
        check_out = r["check_out_time"]

        late_arrival = max(0, to_minutes(check_in) - work_start_min) if check_in else 0
        late_departure = max(0, work_end_min - to_minutes(check_out)) if check_out else 0
        arrived_early = max(0, work_start_min - to_minutes(check_in)) if check_in else 0

        net_late = max(0, late_arrival + late_departure - arrived_early)
        attendance_minutes += net_late

    total_used_minutes = permission_minutes + attendance_minutes
    allowance = settings["monthly_late_allowance_minutes"]
    excess_minutes = max(0, total_used_minutes - allowance)

    return {
        "year": year,
        "month": month,
        "allowance_minutes": allowance,
        "used_minutes": total_used_minutes,
        "excess_minutes": excess_minutes,
        "from_permissions_minutes": permission_minutes,
        "from_attendance_minutes": attendance_minutes,
    }