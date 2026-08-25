import { Component, inject, signal, OnInit } from '@angular/core';
import { LucideAngularModule, MessageSquareText } from 'lucide-angular';

import { HistoryService } from '../../core/services/history.service';
import { I18nService } from '../../core/services/i18n.service';
import { ChatLogEntry } from '../../core/models/history.model';

@Component({
  selector: 'app-history',
  imports: [LucideAngularModule],
  templateUrl: './history.html',
  styleUrl: './history.css',
})
export class History implements OnInit {
  private readonly historyService = inject(HistoryService);
  protected readonly i18n = inject(I18nService);

  protected readonly EmptyIcon = MessageSquareText;
  protected readonly logs = signal<ChatLogEntry[]>([]);
  protected readonly isLoading = signal(true);

  ngOnInit(): void {
    this.historyService.getMyHistory().subscribe({
      next: (data) => {
        this.logs.set(data.logs);
        this.isLoading.set(false);
        
      },
      error: () => this.isLoading.set(false),
    });
  }
}