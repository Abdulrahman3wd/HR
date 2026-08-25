import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import {
  JobOpening,
  JobOpeningCreateRequest,
  JobOpeningListResponse,
  Candidate,
  CandidateListResponse,
  CandidateStage,
  CandidateInfoUpdate,
} from '../models/recruitment.model';
@Injectable({ providedIn: 'root' })
export class RecruitmentService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiUrl;

  // ---------- Jobs ----------
  listJobs(status?: string) {
    const query = status ? `?status=${status}` : '';
    return this.http.get<JobOpeningListResponse>(`${this.base}/recruitment/jobs${query}`);
  }

  createJob(request: JobOpeningCreateRequest) {
    return this.http.post<JobOpening>(`${this.base}/recruitment/jobs`, request);
  }

  closeJob(jobId: number) {
    return this.http.put<JobOpening>(`${this.base}/recruitment/jobs/${jobId}/close`, {});
  }

  reopenJob(jobId: number) {
    return this.http.put<JobOpening>(`${this.base}/recruitment/jobs/${jobId}/reopen`, {});
  }

  // ---------- Candidates ----------
  listCandidates(jobOpeningId?: number) {
    const query = jobOpeningId ? `?job_opening_id=${jobOpeningId}` : '';
    return this.http.get<CandidateListResponse>(`${this.base}/recruitment/candidates${query}`);
  }

  addCandidate(
    jobOpeningId: number,
    fullName: string,
    email: string | null,
    phone: string | null,
    cvFile: File | null
  ) {
    const formData = new FormData();
    formData.append('job_opening_id', jobOpeningId.toString());
    formData.append('full_name', fullName);
    if (email) formData.append('email', email);
    if (phone) formData.append('phone', phone);
    if (cvFile) formData.append('cv_file', cvFile);

    return this.http.post<Candidate>(`${this.base}/recruitment/candidates`, formData);
  }

  updateStage(candidateId: number, stage: CandidateStage) {
    return this.http.put<Candidate>(`${this.base}/recruitment/candidates/${candidateId}/stage`, { stage });
  }

  updateNotes(candidateId: number, notes: string) {
    return this.http.put<Candidate>(`${this.base}/recruitment/candidates/${candidateId}/notes`, { notes });
  }
  updateCandidateInfo(candidateId: number, updates: CandidateInfoUpdate) {
    return this.http.put<Candidate>(`${this.base}/recruitment/candidates/${candidateId}`, updates);
  }

  deleteCandidate(candidateId: number) {
    return this.http.delete<{ message: string }>(`${this.base}/recruitment/candidates/${candidateId}`);
  }
}