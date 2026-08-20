import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { DepartmentListResponse, DepartmentCreateRequest, Department } from '../models/department.model';

@Injectable({ providedIn: 'root' })
export class DepartmentService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiUrl;

  list() {
    return this.http.get<DepartmentListResponse>(`${this.base}/departments`);
  }

  create(request: DepartmentCreateRequest) {
    return this.http.post<Department>(`${this.base}/departments`, request);
  }

  delete(id: number) {
    return this.http.delete<{ message: string }>(`${this.base}/departments/${id}`);
  }
}