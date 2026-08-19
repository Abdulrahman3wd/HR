export interface ChatLogEntry {
  id: number;
  company_id: number;
  employee_id: string;
  question: string;
  answer: string;
  source_type: 'policy' | 'personal';
  sources: string[];
  created_at: string;
}

export interface ChatLogListResponse {
  logs: ChatLogEntry[];
  total: number;
}