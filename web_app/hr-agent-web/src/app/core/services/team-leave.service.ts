import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { LeaveRequestRecord } from '../models/leave.model';
import { TeamLeaveListResponse } from '../models/team-leave.model';

@Injectable({ providedIn: 'root' })
export class TeamLeaveService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiUrl;

  getReviewableRequests(status?: string) {
    const query = status ? `?status=${status}` : '';
    return this.http.get<TeamLeaveListResponse>(`${this.base}/admin/leave-requests${query}`);
  }

  approve(requestId: number) {
    return this.http.put<LeaveRequestRecord>(`${this.base}/admin/leave-requests/${requestId}/approve`, {});
  }

  reject(requestId: number) {
    return this.http.put<LeaveRequestRecord>(`${this.base}/admin/leave-requests/${requestId}/reject`, {});
  }
}