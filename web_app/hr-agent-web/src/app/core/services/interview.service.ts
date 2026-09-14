import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import {
  InterviewScheduleCreate,
  InterviewScheduleRecord,
  InterviewScheduleListResponse,
  PublicInterviewInfo,
  AttendanceStatus,
} from '../models/interview.model';

@Injectable({ providedIn: 'root' })
export class InterviewService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiUrl;

  scheduleInterview(request: InterviewScheduleCreate) {
    return this.http.post<InterviewScheduleRecord>(`${this.base}/interviews`, request);
  }

  getCandidateSchedules(candidateId: number) {
    return this.http.get<InterviewScheduleListResponse>(`${this.base}/interviews/candidate/${candidateId}`);
  }

  setAttendance(scheduleId: number, status: AttendanceStatus) {
    return this.http.put<InterviewScheduleRecord>(`${this.base}/interviews/${scheduleId}/attendance`, {
      attendance_status: status,
    });
  }

  // ---------- Public ----------
  getPublicInterviewInfo(scheduleId: number) {
    return this.http.get<PublicInterviewInfo>(`${this.base}/public/interviews/${scheduleId}`);
  }

  bookSlot(scheduleId: number, slotTime: string) {
    return this.http.post<InterviewScheduleRecord>(`${this.base}/public/interviews/${scheduleId}/book`, {
      slot_time: slotTime,
    });
  }
}