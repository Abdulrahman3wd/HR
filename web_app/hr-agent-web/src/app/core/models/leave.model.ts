export type LeaveStatus = 'pending' | 'approved' | 'rejected';

export interface LeaveRequestCreate {
  start_date: string;
  end_date: string;
  reason?: string | null;
}

export interface LeaveRequestRecord {
  id: number;
  company_id: number;
  employee_id: string;
  start_date: string;
  end_date: string;
  days_count: number;
  reason: string | null;
  status: LeaveStatus;
  created_at: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
}

export interface LeaveRequestListResponse {
  requests: LeaveRequestRecord[];
  total: number;
}