import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { NetSalary } from '../models/payroll.model';

@Injectable({ providedIn: 'root' })
export class PayrollService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiUrl;

  getMySalary() {
    return this.http.get<NetSalary>(`${this.base}/payroll/my`);
  }
}