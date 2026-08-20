export type UserRole = 'admin' | 'hr' | 'employee';

export interface LoginRequest {
  company_code: string;
  employee_id: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  employee_id: string;
  company_id: number;
  company_name: string;
  full_name: string;
  role: UserRole;
}

export interface CurrentUser {
  employee_id: string;
  company_id: number;
  company_name: string;
  full_name: string;
  role: UserRole;
}