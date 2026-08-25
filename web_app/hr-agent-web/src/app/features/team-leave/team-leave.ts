import { Component, inject, signal, OnInit } from '@angular/core';
import { LucideAngularModule, Check, X, Users2, Clock3 } from 'lucide-angular';

import { TeamLeaveService } from '../../core/services/team-leave.service';
import { LatePermissionService } from '../../core/services/late-permission.service';
import { I18nService } from '../../core/services/i18n.service';
import { LeaveRequestRecord, LeaveStatus } from '../../core/models/leave.model';
import { LatePermissionRecord } from '../../core/models/late-permission.model';
import { TranslationKey } from '../../core/services/translations';
import { ToastService } from '../../core/services/toast.service';
import { ConfirmDialogService } from '../../core/services/confirm-dialog.service';
type TeamTab = 'leave' | 'late';

@Component({
  selector: 'app-team-leave',
  imports: [LucideAngularModule],
  templateUrl: './team-leave.html',
  styleUrl: './team-leave.css',
})
export class TeamLeave implements OnInit {
  private readonly teamLeaveService = inject(TeamLeaveService);
  private readonly latePermissionService = inject(LatePermissionService);
  protected readonly i18n = inject(I18nService);
  protected readonly toast = inject(ToastService);
  protected readonly confirmDialog = inject(ConfirmDialogService);
  protected readonly ApproveIcon = Check;
  protected readonly RejectIcon = X;
  protected readonly EmptyIcon = Users2;
  protected readonly LateIcon = Clock3;

  protected readonly activeTab = signal<TeamTab>('leave');

  protected readonly leaveRequests = signal<LeaveRequestRecord[]>([]);
  protected readonly lateRequests = signal<LatePermissionRecord[]>([]);
  protected readonly processingId = signal<number | null>(null);

  ngOnInit(): void {
    this.loadLeaveRequests();
    this.loadLateRequests();
  }

  protected switchTab(tab: TeamTab): void {
    this.activeTab.set(tab);
  }

  // ---------- Leave requests ----------
  private loadLeaveRequests(): void {
    this.teamLeaveService.getReviewableRequests('pending').subscribe({
      next: (data) => this.leaveRequests.set(data.requests),
    });
  }

  protected approveLeave(requestId: number): void {
    this.processingId.set(requestId);
    this.teamLeaveService.approve(requestId).subscribe({
      next: () => {
        this.processingId.set(null);
        this.loadLeaveRequests();
        this.toast.success('Leave request approved successfully');
      },
      error: () => this.processingId.set(null),
    });
  }

  protected rejectLeave(requestId: number): void {
    this.processingId.set(requestId);
    this.teamLeaveService.reject(requestId).subscribe({
      next: () => {
        this.processingId.set(null);
        this.loadLeaveRequests();
        this.toast.success('Leave request rejected successfully');
      },
      error: () => this.processingId.set(null),
    });
  }

  protected statusLabel(status: LeaveStatus): string {
    return this.i18n.t(('leave_status_' + status) as TranslationKey);
  }

  // ---------- Late permission requests ----------
  private loadLateRequests(): void {
    this.latePermissionService.getReviewable('pending').subscribe({
      next: (data) => this.lateRequests.set(data.permissions),
    });
  }

  protected approveLate(id: number): void {
    this.processingId.set(id);
    this.latePermissionService.approve(id).subscribe({
      next: () => {
        this.processingId.set(null);
        this.loadLateRequests();
        this.toast.success('Late permission approved successfully');
      },
      error: () => this.processingId.set(null),
    });
  }

  protected rejectLate(id: number): void {
    this.processingId.set(id);
    this.latePermissionService.reject(id).subscribe({
      next: () => {
        this.processingId.set(null);
        this.loadLateRequests();
        this.toast.success('Late permission rejected successfully');
      },
      error: () => this.processingId.set(null),
    });
  }
}