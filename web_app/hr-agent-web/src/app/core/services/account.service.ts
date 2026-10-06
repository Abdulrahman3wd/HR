import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { CurrentUserProfile, ChangePasswordRequest } from '../models/account.model';

@Injectable({ providedIn: 'root' })
export class AccountService {
  private readonly http = inject(HttpClient);

  getMyProfile() {
    return this.http.get<CurrentUserProfile>(`${environment.apiUrl}/me`);
  }

  uploadProfilePicture(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<{ avatar_url: string }>(`${environment.apiUrl}/me/profile-picture`, formData);
  }

  changePassword(request: ChangePasswordRequest) {
    return this.http.put<{ message: string }>(`${environment.apiUrl}/me/password`, request);
  }
}