import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { ChatLogListResponse } from '../models/history.model';

@Injectable({ providedIn: 'root' })
export class HistoryService {
  private readonly http = inject(HttpClient);

  getMyHistory() {
    return this.http.get<ChatLogListResponse>(`${environment.apiUrl}/my-history`);
  }
}