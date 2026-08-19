import { Injectable, signal, computed, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { environment } from '../../../environments/environment';
import { CurrentUser, LoginRequest, LoginResponse } from '../models/user.model';

const TOKEN_KEY = 'hr_agent_token';
const USER_KEY = 'hr_agent_user';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  readonly currentUser = signal<CurrentUser | null>(this.getStoredUser());
  readonly token = signal<string | null>(localStorage.getItem(TOKEN_KEY));

  readonly isLoggedIn = computed(() => !!this.token());
  readonly isAdmin = computed(() => this.currentUser()?.role === 'admin');

  login(request: LoginRequest) {
    return this.http.post<LoginResponse>(`${environment.apiUrl}/login`, request);
  }

  setSession(response: LoginResponse): void {
    const user: CurrentUser = {
      employee_id: response.employee_id,
      company_id: response.company_id,
      company_name: response.company_name,
      full_name: response.full_name,
      department: response.department,
      role: response.role,
    };

    localStorage.setItem(TOKEN_KEY, response.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));

    this.token.set(response.access_token);
    this.currentUser.set(user);
  }

  logout(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    this.token.set(null);
    this.currentUser.set(null);
    this.router.navigate(['/login']);
  }

  private getStoredUser(): CurrentUser | null {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  }
}