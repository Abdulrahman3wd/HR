import { Component, inject, signal, OnInit } from '@angular/core';
import { LucideAngularModule, Check, X, Users2 } from 'lucide-angular';

import { TeamLeaveService } from '../../core/services/team-leave.service';
import { I18nService } from '../../core/services/i18n.service';
import { LeaveRequestRecord, LeaveStatus } from '../../core/models/leave.model';

@Component({
  selector: 'app-team-leave',
  imports: [LucideAngularModule],
  templateUrl: './team-leave.html',
  styleUrl: './team-leave.css',
})
export class TeamLeave implements OnInit {
  private readonly teamLeaveService = inject(TeamLeaveService);
  protected readonly i18n = inject(I18nService);

  protected readonly ApproveIcon = Check;
  protected readonly RejectIcon = X;
  protected readonly EmptyIcon = Users2;

  protected readonly requests = signal<LeaveRequestRecord[]>([]);
  protected readonly processingId = signal<number | null>(null);

  ngOnInit(): void {
    this.loadRequests();
  }

  private loadRequests(): void {
    this.teamLeaveService.getReviewableRequests('pending').subscribe({
      next: (data) => this.requests.set(data.requests),
    });
  }

  protected approve(requestId: number): void {
    this.processingId.set(requestId);
    this.teamLeaveService.approve(requestId).subscribe({
      next: () => {
        this.processingId.set(null);
        this.loadRequests();
      },
      error: () => this.processingId.set(null),
    });
  }

  protected reject(requestId: number): void {
    this.processingId.set(requestId);
    this.teamLeaveService.reject(requestId).subscribe({
      next: () => {
        this.processingId.set(null);
        this.loadRequests();
      },
      error: () => this.processingId.set(null),
    });
  }

  protected statusLabel(status: LeaveStatus): string {
    return this.i18n.t(`leave_status_${status}` as any);
  }
}