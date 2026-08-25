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
    basic_salary: float
    has_social_insurance: bool
    social_insurance_percentage: float
    has_health_insurance: bool
    health_insurance_percentage: float


class UserCreateRequest(BaseModel):
    employee_id: str
    full_name: str
    password: str
    role: str = "employee"
    department_id: int | None = None
    manager_id: str | None = None
    annual_leave_balance: int = 21
    sick_leave_balance: int = 7
    basic_salary: float = 0
    has_social_insurance: bool = False
    social_insurance_percentage: float = 0
    has_health_insurance: bool = False
    health_insurance_percentage: float = 0


class UserUpdateRequest(BaseModel):
    full_name: str | None = None
    department_id: int | None = None
    manager_id: str | None = None
    role: str | None = None
    password: str | None = None
    annual_leave_balance: int | None = None
    sick_leave_balance: int | None = None
    basic_salary: float | None = None
    has_social_insurance: bool | None = None
    social_insurance_percentage: float | None = None
    has_health_insurance: bool | None = None
    health_insurance_percentage: float | None = None


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
    total_net_late_minutes: int

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
    
class CandidateInfoUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
# ---------- Company Settings ----------
class CompanySettingsResponse(BaseModel):
    company_id: int
    weekend_days: list[int]  # 0=Monday ... 6=Sunday
    work_start_time: str
    work_end_time: str
    flex_minutes: int
    monthly_late_allowance_minutes: int


class CompanySettingsUpdate(BaseModel):
    weekend_days: list[int] | None = None
    work_start_time: str | None = None
    work_end_time: str | None = None
    flex_minutes: int | None = None
    monthly_late_allowance_minutes: int | None = None


# ---------- Public Holidays ----------
class PublicHolidayCreate(BaseModel):
    date: str  # YYYY-MM-DD
    name: str


class PublicHolidayRecord(BaseModel):
    id: int
    company_id: int
    date: str
    name: str


class PublicHolidayListResponse(BaseModel):
    holidays: list[PublicHolidayRecord]

# ---------- Late Permissions ----------
class LatePermissionCreate(BaseModel):
    date: str  # YYYY-MM-DD
    from_time: str  # HH:MM
    to_time: str  # HH:MM
    reason: str | None = None


class LatePermissionRecord(BaseModel):
    id: int
    company_id: int
    employee_id: str
    date: str
    from_time: str
    to_time: str
    minutes_count: int
    reason: str | None
    status: str
    created_at: str
    reviewed_by: str | None
    reviewed_at: str | None


class LatePermissionListResponse(BaseModel):
    permissions: list[LatePermissionRecord]


class MonthlyLateUsageResponse(BaseModel):
    year: int
    month: int
    allowance_minutes: int
    used_minutes: int
    excess_minutes: int
    from_permissions_minutes: int
    from_attendance_minutes: int


# ---------- Payroll ----------
class NetSalaryResponse(BaseModel):
    employee_id: str
    year: int
    month: int
    basic_salary: float
    social_insurance_amount: float
    health_insurance_amount: float
    late_excess_minutes: int
    late_deduction_amount: float
    total_deductions: float
    net_salary: float