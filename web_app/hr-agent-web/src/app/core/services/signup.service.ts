import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { CompanySignupRequest, CompanySignupResponse } from '../models/signup.model';

@Injectable({ providedIn: 'root' })
export class SignupService {
  private readonly http = inject(HttpClient);

  signup(request: CompanySignupRequest) {
    return this.http.post<CompanySignupResponse>(`${environment.apiUrl}/signup`, request);
  }
}