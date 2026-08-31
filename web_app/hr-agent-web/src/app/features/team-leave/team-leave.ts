import { Component, inject, signal, OnInit } from '@angular/core';
import { LucideAngularModule, Check, X, Users2, Clock3, TrendingUp } from 'lucide-angular';

import { TeamLeaveService } from '../../core/services/team-leave.service';
import { LatePermissionService } from '../../core/services/late-permission.service';
import { OvertimeService } from '../../core/services/overtime.service';
import { I18nService } from '../../core/services/i18n.service';
import { LeaveRequestRecord, LeaveStatus } from '../../core/models/leave.model';
import { LatePermissionRecord } from '../../core/models/late-permission.model';
import { OvertimeRequestRecord } from '../../core/models/overtime.model';
import { TranslationKey } from '../../core/services/translations';

type TeamTab = 'leave' | 'late' | 'overtime';

@Component({
  selector: 'app-team-leave',
  imports: [LucideAngularModule],
  templateUrl: './team-leave.html',
  styleUrl: './team-leave.css',
})
export class TeamLeave implements OnInit {
  private readonly teamLeaveService = inject(TeamLeaveService);
  private readonly latePermissionService = inject(LatePermissionService);
  private readonly overtimeService = inject(OvertimeService);
  protected readonly i18n = inject(I18nService);

  protected readonly ApproveIcon = Check;
  protected readonly RejectIcon = X;
  protected readonly EmptyIcon = Users2;
  protected readonly LateIcon = Clock3;
  protected readonly OvertimeIcon = TrendingUp;

  protected readonly activeTab = signal<TeamTab>('leave');

  protected readonly leaveRequests = signal<LeaveRequestRecord[]>([]);
  protected readonly lateRequests = signal<LatePermissionRecord[]>([]);
  protected readonly overtimeRequests = signal<OvertimeRequestRecord[]>([]);
  protected readonly processingId = signal<number | null>(null);

  ngOnInit(): void {
    this.loadLeaveRequests();
    this.loadLateRequests();
    this.loadOvertimeRequests();
  }

  protected switchTab(tab: TeamTab): void {
    this.activeTab.set(tab);
  }

  // ---------- Leave requests ----------
  private loadLeaveRequests(): void {
    this.teamLeaveService.getReviewableRequests('pending').subscribe({ next: (data) => this.leaveRequests.set(data.requests) });
  }

  protected approveLeave(requestId: number): void {
    this.processingId.set(requestId);
    this.teamLeaveService.approve(requestId).subscribe({
      next: () => { this.processingId.set(null); this.loadLeaveRequests(); },
      error: () => this.processingId.set(null),
    });
  }

  protected rejectLeave(requestId: number): void {
    this.processingId.set(requestId);
    this.teamLeaveService.reject(requestId).subscribe({
      next: () => { this.processingId.set(null); this.loadLeaveRequests(); },
      error: () => this.processingId.set(null),
    });
  }

  protected statusLabel(status: LeaveStatus): string {
    return this.i18n.t(('leave_status_' + status) as TranslationKey);
  }

  // ---------- Late permission requests ----------
  private loadLateRequests(): void {
    this.latePermissionService.getReviewable('pending').subscribe({ next: (data) => this.lateRequests.set(data.permissions) });
  }

  protected approveLate(id: number): void {
    this.processingId.set(id);
    this.latePermissionService.approve(id).subscribe({
      next: () => { this.processingId.set(null); this.loadLateRequests(); },
      error: () => this.processingId.set(null),
    });
  }

  protected rejectLate(id: number): void {
    this.processingId.set(id);
    this.latePermissionService.reject(id).subscribe({
      next: () => { this.processingId.set(null); this.loadLateRequests(); },
      error: () => this.processingId.set(null),
    });
  }

  // ---------- Overtime requests ----------
  private loadOvertimeRequests(): void {
    this.overtimeService.getReviewable('pending').subscribe({ next: (data) => this.overtimeRequests.set(data.requests) });
  }

  protected approveOvertime(id: number): void {
    this.processingId.set(id);
    this.overtimeService.approve(id).subscribe({
      next: () => { this.processingId.set(null); this.loadOvertimeRequests(); },
      error: () => this.processingId.set(null),
    });
  }

  protected rejectOvertime(id: number): void {
    this.processingId.set(id);
    this.overtimeService.reject(id).subscribe({
      next: () => { this.processingId.set(null); this.loadOvertimeRequests(); },
      error: () => this.processingId.set(null),
    });
  }
}