import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { OvertimeRequestCreate, OvertimeRequestRecord, OvertimeRequestListResponse } from '../models/overtime.model';

@Injectable({ providedIn: 'root' })
export class OvertimeService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiUrl;

  submit(request: OvertimeRequestCreate) {
    return this.http.post<OvertimeRequestRecord>(`${this.base}/overtime-requests`, request);
  }

  getMyRequests() {
    return this.http.get<OvertimeRequestListResponse>(`${this.base}/overtime-requests/my`);
  }

  getReviewable(status?: string) {
    const query = status ? `?status=${status}` : '';
    return this.http.get<OvertimeRequestListResponse>(`${this.base}/overtime-requests${query}`);
  }

  approve(id: number) {
    return this.http.put<OvertimeRequestRecord>(`${this.base}/overtime-requests/${id}/approve`, {});
  }

  reject(id: number) {
    return this.http.put<OvertimeRequestRecord>(`${this.base}/overtime-requests/${id}/reject`, {});
  }
}