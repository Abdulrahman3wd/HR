export interface CurrentUserProfile {
  employee_id: string;
  company_id: number;
  full_name: string;
  department_id: number | null;
  manager_id: string | null;
  role: 'admin' | 'hr' | 'employee';
  annual_leave_balance: number;
  sick_leave_balance: number;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}