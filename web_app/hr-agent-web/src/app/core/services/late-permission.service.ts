import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import {
  LatePermissionCreate,
  LatePermissionRecord,
  LatePermissionListResponse,
  MonthlyLateUsage,
} from '../models/late-permission.model';

@Injectable({ providedIn: 'root' })
export class LatePermissionService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiUrl;

  submit(request: LatePermissionCreate) {
    return this.http.post<LatePermissionRecord>(`${this.base}/late-permissions`, request);
  }

  getMyPermissions() {
    return this.http.get<LatePermissionListResponse>(`${this.base}/late-permissions/my`);
  }

  getMyUsage() {
    return this.http.get<MonthlyLateUsage>(`${this.base}/late-permissions/my-usage`);
  }

  getReviewable(status?: string) {
    const query = status ? `?status=${status}` : '';
    return this.http.get<LatePermissionListResponse>(`${this.base}/late-permissions${query}`);
  }

  approve(id: number) {
    return this.http.put<LatePermissionRecord>(`${this.base}/late-permissions/${id}/approve`, {});
  }

  reject(id: number) {
    return this.http.put<LatePermissionRecord>(`${this.base}/late-permissions/${id}/reject`, {});
  }
}