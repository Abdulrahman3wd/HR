export type OvertimeStatus = 'pending' | 'approved' | 'rejected';

export interface OvertimeRequestCreate {
  date: string;
  from_time: string;
  to_time: string;
  reason?: string | null;
}

export interface OvertimeRequestRecord {
  id: number;
  company_id: number;
  employee_id: string;
  date: string;
  from_time: string;
  to_time: string;
  minutes_count: number;
  reason: string | null;
  status: OvertimeStatus;
  created_at: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
}

export interface OvertimeRequestListResponse {
  requests: OvertimeRequestRecord[];
}