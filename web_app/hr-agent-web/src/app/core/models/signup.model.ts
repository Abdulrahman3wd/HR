export interface CompanySignupRequest {
  company_name: string;
  company_code: string;
  admin_employee_id: string;
  admin_full_name: string;
  admin_password: string;
}

export interface CompanySignupResponse {
  message: string;
  company_code: string;
}