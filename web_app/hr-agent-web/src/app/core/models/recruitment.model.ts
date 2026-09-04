export type CandidateStage =
  | 'applied'
  | 'reviewing'
  | 'hr_interview'
  | 'technical_interview'
  | 'accepted'
  | 'rejected';

export type QuestionType = 'number' | 'text' | 'yes_no';

export interface CustomQuestion {
  question: string;
  type: QuestionType;
  required: boolean;
}

export interface JobOpening {
  id: number;
  company_id: number;
  title: string;
  department_id: number | null;
  description: string;
  requirements: string;
  custom_questions: CustomQuestion[];
  status: 'open' | 'closed';
  created_by: string;
  created_at: string;
}

export interface JobOpeningCreateRequest {
  title: string;
  description: string;
  requirements: string;
  department_id: number | null;
  custom_questions: CustomQuestion[];
}
export interface JobOpeningListResponse {
  jobs: JobOpening[];
}

export interface Candidate {
  id: number;
  company_id: number;
  job_opening_id: number;
  full_name: string;
  email: string | null;
  phone: string | null;
  cv_filename: string | null;
  match_score: number | null;
  matched_skills: string[];
  missing_skills: string[];
  custom_answers: Record<string, string>;
  source: 'manual' | 'self_applied';
  stage: CandidateStage;
  notes: string | null;
  added_by: string | null;
  applied_at: string;
}
export interface CandidateListResponse {
  candidates: Candidate[];
}

export interface CandidateInfoUpdate {
  full_name?: string;
  email?: string;
  phone?: string;
}
export interface PublicJob {
  id: number;
  title: string;
  description: string;
  requirements: string;
  custom_questions: CustomQuestion[];
  status: string;
}

export interface PublicApplicationSubmitResponse {
  message: string;
  candidate_id: number;
}