import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { LeaveRequestCreate, LeaveRequestRecord, LeaveRequestListResponse } from '../models/leave.model';

@Injectable({ providedIn: 'root' })
export class LeaveService {
  private readonly http = inject(HttpClient);

  submitRequest(request: LeaveRequestCreate) {
    return this.http.post<LeaveRequestRecord>(`${environment.apiUrl}/leave-requests`, request);
  }

  getMyRequests() {
    return this.http.get<LeaveRequestListResponse>(`${environment.apiUrl}/leave-requests/my`);
  }
}