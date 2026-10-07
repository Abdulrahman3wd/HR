import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import {
  EmployeeConversation,
  EmployeeConversationPage,
  EmployeeDirectoryPage,
  EmployeeMessage,
  EmployeeMessagePage,
} from '../models/employee-chat.model';

@Injectable({ providedIn: 'root' })
export class EmployeeChatService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/employee-chat`;

  listEmployees(page: number, pageSize: number, search: string) {
    let params = new HttpParams().set('page', page).set('page_size', pageSize);
    if (search.trim()) params = params.set('search', search.trim());
    return this.http.get<EmployeeDirectoryPage>(`${this.baseUrl}/employees`, { params });
  }

  listConversations(page: number, pageSize: number) {
    const params = new HttpParams().set('page', page).set('page_size', pageSize);
    return this.http.get<EmployeeConversationPage>(`${this.baseUrl}/conversations`, { params });
  }

  startConversation(employeeId: string) {
    return this.http.post<EmployeeConversation>(`${this.baseUrl}/conversations`, {
      employee_id: employeeId,
    });
  }

  listMessages(conversationId: number, limit: number, beforeId: number | null = null) {
    let params = new HttpParams().set('limit', limit);
    if (beforeId !== null) params = params.set('before_id', beforeId);
    return this.http.get<EmployeeMessagePage>(
      `${this.baseUrl}/conversations/${conversationId}/messages`,
      { params },
    );
  }

  sendMessage(conversationId: number, body: string) {
    return this.http.post<EmployeeMessage>(
      `${this.baseUrl}/conversations/${conversationId}/messages`,
      { body },
    );
  }

  sendAttachment(conversationId: number, body: string, file: File) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('body', body);
    return this.http.post<EmployeeMessage>(
      `${this.baseUrl}/conversations/${conversationId}/attachments`,
      formData,
    );
  }

  fetchAttachment(conversationId: number, messageId: number, inline = false) {
    const params = inline ? new HttpParams().set('inline', true) : undefined;
    return this.http.get(
      `${this.baseUrl}/conversations/${conversationId}/messages/${messageId}/attachment`,
      { params, responseType: 'blob' },
    );
  }

  markConversationRead(conversationId: number) {
    return this.http.post<{ conversation_id: number; total_unread: number }>(
      `${this.baseUrl}/conversations/${conversationId}/read`,
      {},
    );
  }

  connectRealtime(token: string): WebSocket {
    const url = new URL(`${this.baseUrl}/ws`);
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    url.searchParams.set('token', token);
    return new WebSocket(url);
  }
}