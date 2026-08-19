export type UserRole = 'admin' | 'employee';

export interface AdminUserRecord {
  employee_id: string;
  company_id: number;
  full_name: string;
  department: string;
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
  department: string;
  password: string;
  role: UserRole;
  annual_leave_balance: number;
  sick_leave_balance: number;
}

export interface AdminUserUpdateRequest {
  full_name?: string;
  department?: string;
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