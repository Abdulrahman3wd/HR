import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import {
  AttendanceMetrics,
  CurrentQuarter,
  AttendanceImportResult,
  KpiEvaluationCreate,
  KpiEvaluationRecord,
  KpiEvaluationListResponse,
} from '../models/kpi.model';

@Injectable({ providedIn: 'root' })
export class KpiService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiUrl;

  getCurrentQuarter() {
    return this.http.get<CurrentQuarter>(`${this.base}/kpi/current-quarter`);
  }

  previewMetrics(employeeId: string) {
    return this.http.get<AttendanceMetrics>(`${this.base}/kpi/preview?employee_id=${employeeId}`);
  }

  submitEvaluation(request: KpiEvaluationCreate) {
    return this.http.post<KpiEvaluationRecord>(`${this.base}/kpi`, request);
  }

  getMyEvaluations() {
    return this.http.get<KpiEvaluationListResponse>(`${this.base}/kpi/my`);
  }

  getEmployeeEvaluations(employeeId: string) {
    return this.http.get<KpiEvaluationListResponse>(`${this.base}/kpi/${employeeId}`);
  }

  importAttendanceExcel(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<AttendanceImportResult>(`${this.base}/attendance/import-excel`, formData);
  }
}