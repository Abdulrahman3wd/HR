import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import {
  AdminUserListResponse,
  AdminUserRecord,
  AdminUserCreateRequest,
  AdminUserUpdateRequest,
  AdminUploadResponse,
  AdminDocsListResponse,
} from '../models/admin.model';

@Injectable({ providedIn: 'root' })
export class AdminService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiUrl;

  // ---------- Users ----------
  listUsers() {
    return this.http.get<AdminUserListResponse>(`${this.base}/admin/users`);
  }

  createUser(request: AdminUserCreateRequest) {
    return this.http.post<AdminUserRecord>(`${this.base}/admin/users`, request);
  }

  updateUser(employeeId: string, request: AdminUserUpdateRequest) {
    return this.http.put<AdminUserRecord>(`${this.base}/admin/users/${employeeId}`, request);
  }

  deleteUser(employeeId: string) {
    return this.http.delete<{ message: string }>(`${this.base}/admin/users/${employeeId}`);
  }

  // ---------- Documents ----------
  listDocs() {
    return this.http.get<AdminDocsListResponse>(`${this.base}/admin/docs/list`);
  }

  uploadDoc(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<AdminUploadResponse>(`${this.base}/admin/docs/upload`, formData);
  }

  deleteDoc(filename: string) {
    return this.http.delete<{ message: string }>(`${this.base}/admin/docs/${filename}`);
  }
}