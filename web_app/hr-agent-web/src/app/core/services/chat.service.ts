import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { AskRequest, AskResponse } from '../models/chat.model';

@Injectable({ providedIn: 'root' })
export class ChatService {
  private readonly http = inject(HttpClient);

  ask(request: AskRequest) {
    return this.http.post<AskResponse>(`${environment.apiUrl}/ask`, request);
  }
}