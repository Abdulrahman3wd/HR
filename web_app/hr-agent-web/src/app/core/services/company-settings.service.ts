import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import {
  CompanySettings,
  CompanySettingsUpdate,
  PublicHolidayListResponse,
  PublicHolidayCreate,
  PublicHoliday,
} from '../models/company-settings.model';

@Injectable({ providedIn: 'root' })
export class CompanySettingsService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiUrl;

  getSettings() {
    return this.http.get<CompanySettings>(`${this.base}/company-settings`);
  }

  updateSettings(request: CompanySettingsUpdate) {
    return this.http.put<CompanySettings>(`${this.base}/company-settings`, request);
  }

  listHolidays(year?: number) {
    const query = year ? `?year=${year}` : '';
    return this.http.get<PublicHolidayListResponse>(`${this.base}/public-holidays${query}`);
  }

  addHoliday(request: PublicHolidayCreate) {
    return this.http.post<PublicHoliday>(`${this.base}/public-holidays`, request);
  }

  deleteHoliday(id: number) {
    return this.http.delete<{ message: string }>(`${this.base}/public-holidays/${id}`);
  }
}