export type InterviewType = 'hr' | 'technical';
export type InterviewMode = 'online' | 'offline';
export type AttendanceStatus = 'scheduled' | 'attended' | 'no_show';

export interface InterviewScheduleCreate {
  candidate_id: number;
  interview_type: InterviewType;
  mode: InterviewMode;
  duration_minutes: number;
  interview_date: string;
  window_start_time: string;
  window_end_time: string;
}

export interface InterviewScheduleRecord {
  id: number;
  company_id: number;
  candidate_id: number;
  job_opening_id: number;
  interview_type: InterviewType;
  mode: InterviewMode;
  duration_minutes: number;
  interview_date: string;
  window_start_time: string;
  window_end_time: string;
  booked_slot_time: string | null;
  attendance_status: AttendanceStatus;
  created_by: string;
  created_at: string;
}

export interface InterviewScheduleListResponse {
  schedules: InterviewScheduleRecord[];
}

export interface PublicInterviewInfo {
  candidate_name: string;
  job_title: string;
  interview_type: InterviewType;
  mode: InterviewMode;
  duration_minutes: number;
  interview_date: string;
  available_slots: string[];
  is_booked: boolean;
  booked_slot_time: string | null;
}