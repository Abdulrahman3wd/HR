export interface AttendanceMetrics {
  days_present: number;
  expected_work_days: number;
  days_on_time: number;
  attendance_rate: number;
  punctuality_rate: number;
}

export interface CurrentQuarter {
  label: string;
  start_date: string;
  end_date: string;
}

export interface AttendanceImportResult {
  imported_rows: number;
  skipped_rows: number;
  skipped_details: { row: number; reason: string }[];
}

export interface KpiEvaluationCreate {
  employee_id: string;
  manager_notes?: string | null;
}

export interface KpiEvaluationRecord {
  id: number;
  company_id: number;
  employee_id: string;
  evaluated_by: string;
  period: string;
  punctuality_rate: number;
  attendance_rate: number;
  manager_notes: string | null;
  created_at: string;
}

export interface KpiEvaluationListResponse {
  evaluations: KpiEvaluationRecord[];
}