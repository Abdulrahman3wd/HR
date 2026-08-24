export type PermissionStatus = 'pending' | 'approved' | 'rejected';

export interface LatePermissionCreate {
  date: string;
  from_time: string;
  to_time: string;
  reason?: string | null;
}

export interface LatePermissionRecord {
  id: number;
  company_id: number;
  employee_id: string;
  date: string;
  from_time: string;
  to_time: string;
  minutes_count: number;
  reason: string | null;
  status: PermissionStatus;
  created_at: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
}

export interface LatePermissionListResponse {
  permissions: LatePermissionRecord[];
}

export interface MonthlyLateUsage {
  year: number;
  month: number;
  allowance_minutes: number;
  used_minutes: number;
  excess_minutes: number;
  from_permissions_minutes: number;
  from_attendance_minutes: number;
}