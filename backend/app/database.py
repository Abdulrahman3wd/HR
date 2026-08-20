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