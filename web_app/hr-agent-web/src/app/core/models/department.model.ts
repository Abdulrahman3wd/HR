export interface Department {
  id: number;
  company_id: number;
  name: string;
}

export interface DepartmentListResponse {
  departments: Department[];
}

export interface DepartmentCreateRequest {
  name: string;
}