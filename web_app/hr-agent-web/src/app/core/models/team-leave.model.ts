import { LeaveRequestRecord } from './leave.model';

export interface TeamLeaveListResponse {
  requests: LeaveRequestRecord[];
  total: number;
}