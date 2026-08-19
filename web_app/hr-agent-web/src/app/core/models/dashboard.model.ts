export interface TopUserEntry {
  employee_id: string;
  question_count: number;
}

export interface DashboardStats {
  employee_count: number;
  admin_count: number;
  total_users: number;
  pending_leaves: number;
  approved_leaves: number;
  rejected_leaves: number;
  total_leave_requests: number;
  total_questions: number;
  policy_questions: number;
  personal_questions: number;
  top_users: TopUserEntry[];
}