"""
setup_hr_database.py
=====================
Creates the multi-tenant schema with organizational hierarchy support:
    companies -> departments
    companies -> users (with manager_id self-reference + department_id)
    -> chat_logs / leave_requests / notifications

Run once (or whenever you want to reset sample data) with:
    python scripts/setup_hr_database.py
"""

import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.config import HR_DB_FILE
from app.security import hash_password


def main():
    conn = sqlite3.connect(HR_DB_FILE)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    cursor.execute("DROP TABLE IF EXISTS notifications")
    cursor.execute("DROP TABLE IF EXISTS leave_requests")
    cursor.execute("DROP TABLE IF EXISTS chat_logs")
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS departments")
    cursor.execute("DROP TABLE IF EXISTS companies")

    cursor.execute("""
        CREATE TABLE companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)

    # Note: users.manager_id references another user's (employee_id, company_id).
    # SQLite composite FKs to a composite PK are allowed, but we keep it simple
    # and enforce the relationship in application code instead of a strict FK,
    # since manager_id must be nullable and scoped to the same company.
    cursor.execute("""
        CREATE TABLE users (
            employee_id TEXT NOT NULL,
            company_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            department_id INTEGER,
            manager_id TEXT,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'hr', 'employee')),
            annual_leave_balance INTEGER NOT NULL DEFAULT 21,
            sick_leave_balance INTEGER NOT NULL DEFAULT 7,
            PRIMARY KEY (employee_id, company_id),
            FOREIGN KEY (company_id) REFERENCES companies(id),
            FOREIGN KEY (department_id) REFERENCES departments(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            employee_id TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            source_type TEXT NOT NULL,
            sources TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            employee_id TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            days_count INTEGER NOT NULL,
            reason TEXT,
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
            created_at TEXT NOT NULL,
            reviewed_by TEXT,
            reviewed_at TEXT,
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            employee_id TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE attendance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            employee_id TEXT NOT NULL,
            date TEXT NOT NULL,
            check_in_time TEXT,
            check_out_time TEXT,
            source TEXT NOT NULL DEFAULT 'manual' CHECK(source IN ('manual', 'excel_import', 'biometric_api')),
            created_at TEXT NOT NULL,
            UNIQUE(company_id, employee_id, date),
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE kpi_evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            employee_id TEXT NOT NULL,
            evaluated_by TEXT NOT NULL,
            period TEXT NOT NULL,
            punctuality_rate REAL NOT NULL,
            attendance_rate REAL NOT NULL,
            manager_notes TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(company_id, employee_id, period),
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)
    # ---------- Seed: one company with a small hierarchy ----------
    cursor.execute(
        "INSERT INTO companies (company_code, name, is_active, created_at) VALUES (?, ?, 1, datetime('now'))",
        ("ACME", "Acme Corp"),
    )
    acme_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO companies (company_code, name, is_active, created_at) VALUES (?, ?, 1, datetime('now'))",
        ("GLOBEX", "Globex Inc"),
    )
    globex_id = cursor.lastrowid

    # Departments for Acme
    cursor.execute("INSERT INTO departments (company_id, name) VALUES (?, ?)", (acme_id, "Engineering"))
    eng_dept_id = cursor.lastrowid
    cursor.execute("INSERT INTO departments (company_id, name) VALUES (?, ?)", (acme_id, "Marketing"))
    mkt_dept_id = cursor.lastrowid
    cursor.execute("INSERT INTO departments (company_id, name) VALUES (?, ?)", (acme_id, "Human Resources"))
    hr_dept_id = cursor.lastrowid

    # Department for Globex
    cursor.execute("INSERT INTO departments (company_id, name) VALUES (?, ?)", (globex_id, "Sales"))
    sales_dept_id = cursor.lastrowid

    def insert_user(employee_id, company_id, full_name, department_id, manager_id, password, role, annual, sick):
        cursor.execute(
            "INSERT INTO users "
            "(employee_id, company_id, full_name, department_id, manager_id, password_hash, role, "
            "annual_leave_balance, sick_leave_balance) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (employee_id, company_id, full_name, department_id, manager_id,
             hash_password(password), role, annual, sick),
        )

    # ---------- Acme hierarchy ----------
    # ADMIN1: top-level admin, no manager
    insert_user("ADMIN1", acme_id, "Acme Admin", None, None, "admin123", "admin", 21, 7)

    # HR1: HR role, reports to Admin
    insert_user("HR1", acme_id, "Heba Rashad (HR)", hr_dept_id, "ADMIN1", "hr123", "hr", 21, 7)

    # PM1: Project Manager, reports to Admin
    insert_user("PM1", acme_id, "Ahmed Mostafa (PM)", eng_dept_id, "ADMIN1", "pass123", "employee", 21, 7)

    # TL1: Team Leader, reports to PM1
    insert_user("TL1", acme_id, "Youssef Adel (TL)", eng_dept_id, "PM1", "pass123", "employee", 21, 7)

    # EMP001: Employee, reports to TL1
    insert_user("EMP001", acme_id, "Karim Nabil", eng_dept_id, "TL1", "pass123", "employee", 14, 5)

    # EMP002: Employee, reports directly to PM1 (no team leader)
    insert_user("EMP002", acme_id, "Sara Youssef", mkt_dept_id, "PM1", "pass123", "employee", 21, 7)

    # ---------- Globex (simple, flat) ----------
    insert_user("ADMIN1", globex_id, "Globex Admin", None, None, "admin123", "admin", 21, 7)
    insert_user("EMP001", globex_id, "John Carter", sales_dept_id, "ADMIN1", "pass123", "employee", 18, 6)

    conn.commit()
    conn.close()

    print(f"[DONE] Multi-tenant hierarchical database ready at: {HR_DB_FILE}")
    print("[INFO] Acme hierarchy:")
    print("       ADMIN1 (admin)")
    print("        └── HR1 (hr)")
    print("        └── PM1 (employee, Project Manager)")
    print("             └── TL1 (employee, Team Leader)")
    print("                  └── EMP001 (employee)")
    print("             └── EMP002 (employee)")
    print("[INFO] Passwords: admin123 for ADMIN1, hr123 for HR1, pass123 for everyone else")


if __name__ == "__main__":
    main()