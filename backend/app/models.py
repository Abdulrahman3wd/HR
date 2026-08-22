"""
models.py
=========
Pydantic models shared across routers (request/response shapes).
"""

from pydantic import BaseModel

UserRole = str  # 'admin' | 'hr' | 'employee' (kept as str for simplicity with SQLite)


# ---------- Auth ----------
class LoginRequest(BaseModel):
    company_code: str
    employee_id: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    employee_id: str
    company_id: int
    company_name: str
    full_name: str
    role: str


class CurrentUserResponse(BaseModel):
    employee_id: str
    company_id: int
    full_name: str
    department_id: int | None
    manager_id: str | None
    role: str
    annual_leave_balance: int
    sick_leave_balance: int


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# ---------- Company self-signup ----------
class CompanySignupRequest(BaseModel):
    company_name: str
    company_code: str
    admin_employee_id: str
    admin_full_name: str
    admin_password: str


class CompanySignupResponse(BaseModel):
    message: str
    company_code: str


# ---------- Chat ----------
class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    source_type: str
    sources: list[str] = []


# ---------- Chat History / Audit Log ----------
class ChatLogEntry(BaseModel):
    id: int
    company_id: int
    employee_id: str
    question: str
    answer: str
    source_type: str
    sources: list[str]
    created_at: str


class ChatLogListResponse(BaseModel):
    logs: list[ChatLogEntry]
    total: int


# ---------- Documents (Admin/HR) ----------
class UploadResponse(BaseModel):
    message: str
    total_chunks: int
    processed_files: list[str]


# ---------- Departments ----------
class DepartmentRecord(BaseModel):
    id: int
    company_id: int
    name: str


class DepartmentCreateRequest(BaseModel):
    name: str


class DepartmentListResponse(BaseModel):
    departments: list[DepartmentRecord]


# ---------- User management (Admin/HR) ----------
class UserRecord(BaseModel):
    employee_id: str
    company_id: int
    full_name: str
    department_id: int | None
    manager_id: str | None
    role: str
    annual_leave_balance: int
    sick_leave_balance: int


class UserCreateRequest(BaseModel):
    employee_id: str
    full_name: str
    password: str
    role: str = "employee"  # 'admin' | 'hr' | 'employee'
    department_id: int | None = None
    manager_id: str | None = None
    annual_leave_balance: int = 21
    sick_leave_balance: int = 7


class UserUpdateRequest(BaseModel):
    full_name: str | None = None
    department_id: int | None = None
    manager_id: str | None = None
    role: str | None = None
    password: str | None = None
    annual_leave_balance: int | None = None
    sick_leave_balance: int | None = None


class UserListResponse(BaseModel):
    users: list[UserRecord]
    total: int


# ---------- Leave Requests ----------
class LeaveRequestCreate(BaseModel):
    start_date: str
    end_date: str
    reason: str | None = None


class LeaveRequestRecord(BaseModel):
    id: int
    company_id: int
    employee_id: str
    start_date: str
    end_date: str
    days_count: int
    reason: str | None
    status: str
    created_at: str
    reviewed_by: str | None
    reviewed_at: str | None


class LeaveRequestListResponse(BaseModel):
    requests: list[LeaveRequestRecord]
    total: int


# ---------- Notifications ----------
class NotificationRecord(BaseModel):
    id: int
    company_id: int
    employee_id: str
    message: str
    is_read: bool
    created_at: str


class NotificationListResponse(BaseModel):
    notifications: list[NotificationRecord]
    total: int


class UnreadCountResponse(BaseModel):
    unread_count: int


# ---------- Dashboard Stats ----------
class TopUserEntry(BaseModel):
    employee_id: str
    question_count: int


class DashboardStatsResponse(BaseModel):
    employee_count: int
    admin_count: int
    hr_count: int
    total_users: int
    pending_leaves: int
    approved_leaves: int
    rejected_leaves: int
    total_leave_requests: int
    total_questions: int
    policy_questions: int
    personal_questions: int
    top_users: list[TopUserEntry]

# ---------- Attendance ----------
class AttendanceRecordCreate(BaseModel):
    employee_id: str
    date: str  # YYYY-MM-DD
    check_in_time: str | None = None  # HH:MM
    check_out_time: str | None = None  # HH:MM


class AttendanceRecord(BaseModel):
    id: int
    company_id: int
    employee_id: str
    date: str
    check_in_time: str | None
    check_out_time: str | None
    source: str


class AttendanceMetrics(BaseModel):
    days_present: int
    expected_work_days: int
    days_on_time: int
    attendance_rate: float
    punctuality_rate: float


# ---------- KPI Evaluations ----------
class KpiEvaluationCreate(BaseModel):
    employee_id: str
    manager_notes: str | None = None


class KpiEvaluationRecord(BaseModel):
    id: int
    company_id: int
    employee_id: str
    evaluated_by: str
    period: str
    punctuality_rate: float
    attendance_rate: float
    manager_notes: str | None
    created_at: str


class KpiEvaluationListResponse(BaseModel):
    evaluations: list[KpiEvaluationRecord]

# ---------- Recruitment / ATS ----------
class JobOpeningCreate(BaseModel):
    title: str
    description: str
    requirements: str
    department_id: int | None = None


class JobOpeningRecord(BaseModel):
    id: int
    company_id: int
    title: str
    department_id: int | None
    description: str
    requirements: str
    status: str
    created_by: str
    created_at: str


class JobOpeningListResponse(BaseModel):
    jobs: list[JobOpeningRecord]


class CandidateCreate(BaseModel):
    job_opening_id: int
    full_name: str
    email: str | None = None
    phone: str | None = None


class CandidateRecord(BaseModel):
    id: int
    company_id: int
    job_opening_id: int
    full_name: str
    email: str | None
    phone: str | None
    cv_filename: str | None
    match_score: int | None
    matched_skills: list[str]
    missing_skills: list[str]
    stage: str
    notes: str | None
    added_by: str
    applied_at: str


class CandidateListResponse(BaseModel):
    candidates: list[CandidateRecord]


class CandidateStageUpdate(BaseModel):
    stage: str


class CandidateNotesUpdate(BaseModel):
    notes: str