export type UserRole = 'admin' | 'hr' | 'employee';

export interface AdminUserRecord {
  employee_id: string;
  company_id: number;
  full_name: string;
  department_id: number | null;
  manager_id: string | null;
  role: UserRole;
  annual_leave_balance: number;
  sick_leave_balance: number;
}

export interface AdminUserListResponse {
  users: AdminUserRecord[];
  total: number;
}

export interface AdminUserCreateRequest {
  employee_id: string;
  full_name: string;
  password: string;
  role: UserRole;
  department_id: number | null;
  manager_id: string | null;
  annual_leave_balance: number;
  sick_leave_balance: number;
}

export interface AdminUserUpdateRequest {
  full_name?: string;
  department_id?: number | null;
  manager_id?: string | null;
  role?: UserRole;
  password?: string;
  annual_leave_balance?: number;
  sick_leave_balance?: number;
}

export interface AdminUploadResponse {
  message: string;
  total_chunks: number;
  processed_files: string[];
}

export interface AdminDocsListResponse {
  files: string[];
}