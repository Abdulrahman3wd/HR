export interface CompanySettings {
  company_id: number;
  weekend_days: number[]; // 0=Monday ... 6=Sunday
  work_start_time: string;
  work_end_time: string;
  flex_minutes: number;
  monthly_late_allowance_minutes: number;
}

export interface CompanySettingsUpdate {
  weekend_days?: number[];
  work_start_time?: string;
  work_end_time?: string;
  flex_minutes?: number;
  monthly_late_allowance_minutes?: number;
}

export interface PublicHoliday {
  id: number;
  company_id: number;
  date: string;
  name: string;
}

export interface PublicHolidayListResponse {
  holidays: PublicHoliday[];
}

export interface PublicHolidayCreate {
  date: string;
  name: string;
}