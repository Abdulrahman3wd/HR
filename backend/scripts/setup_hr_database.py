"""
setup_hr_database.py
=====================
Creates the multi-tenant schema:
    companies -> users -> chat_logs / leave_requests / notifications

Every table below `companies` carries a `company_id` foreign key, so all
queries MUST filter by company_id to keep tenants isolated from each other.

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

    # Full reset of the tenant-aware schema. Since this is a structural
    # change (adding company_id everywhere), we drop and recreate all
    # tables this time rather than trying to migrate old data in place.
    cursor.execute("DROP TABLE IF EXISTS notifications")
    cursor.execute("DROP TABLE IF EXISTS leave_requests")
    cursor.execute("DROP TABLE IF EXISTS chat_logs")
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS employees")  # legacy table, if present
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
        CREATE TABLE users (
            employee_id TEXT NOT NULL,
            company_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            department TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'employee')),
            annual_leave_balance INTEGER NOT NULL DEFAULT 21,
            sick_leave_balance INTEGER NOT NULL DEFAULT 7,
            PRIMARY KEY (employee_id, company_id),
            FOREIGN KEY (company_id) REFERENCES companies(id)
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

    # ---------- Seed sample data: two separate companies ----------
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

    sample_users = [
        # employee_id, company_id, full_name,      department,    plain_password, role,       annual, sick
        ("EMP001", acme_id,   "Ahmed Mostafa", "Engineering", "pass123",  "employee", 14, 5),
        ("EMP002", acme_id,   "Sara Youssef",  "Marketing",   "pass123",  "employee", 21, 7),
        ("ADMIN1", acme_id,   "Acme Admin",    "IT",          "admin123", "admin",    21, 7),
        ("EMP001", globex_id, "John Carter",   "Sales",       "pass123",  "employee", 18, 6),
        ("ADMIN1", globex_id, "Globex Admin",  "IT",          "admin123", "admin",    21, 7),
    ]

    for employee_id, company_id, full_name, department, plain_password, role, annual, sick in sample_users:
        password_hash = hash_password(plain_password)
        cursor.execute(
            "INSERT INTO users "
            "(employee_id, company_id, full_name, department, password_hash, role, annual_leave_balance, sick_leave_balance) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (employee_id, company_id, full_name, department, password_hash, role, annual, sick),
        )

    conn.commit()
    conn.close()

    print(f"[DONE] Multi-tenant database ready at: {HR_DB_FILE}")
    print("[INFO] Sample companies:")
    print(f"       ACME   (company_id={acme_id})   -> EMP001/pass123, EMP002/pass123, ADMIN1/admin123")
    print(f"       GLOBEX (company_id={globex_id}) -> EMP001/pass123, ADMIN1/admin123")
    print("[NOTE] Login now requires a company_code alongside employee_id + password.")


if __name__ == "__main__":
    main()