import { Component, inject, signal, OnInit } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { LucideAngularModule, CalendarPlus, Clock, CheckCircle2, XCircle } from 'lucide-angular';

import { LeaveService } from '../../core/services/leave.service';
import { I18nService } from '../../core/services/i18n.service';
import { LeaveRequestRecord, LeaveStatus } from '../../core/models/leave.model';
import { ToastService } from '../../core/services/toast.service';
import { ConfirmDialogService } from '../../core/services/confirm-dialog.service';
@Component({
  selector: 'app-leave',
  imports: [ReactiveFormsModule, LucideAngularModule],
  templateUrl: './leave.html',
  styleUrl: './leave.css',
})
export class Leave implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly leaveService = inject(LeaveService);
  protected readonly i18n = inject(I18nService);
  protected readonly toast = inject(ToastService);
  protected readonly confirmDialog = inject(ConfirmDialogService);
  protected readonly PlusIcon = CalendarPlus;
  protected readonly ClockIcon = Clock;
  protected readonly CheckIcon = CheckCircle2;
  protected readonly XIcon = XCircle;

  protected readonly requests = signal<LeaveRequestRecord[]>([]);
  protected readonly isSubmitting = signal(false);
  protected readonly statusMessage = signal<{ type: 'success' | 'error'; text: string } | null>(null);

  protected readonly form = this.fb.nonNullable.group({
    start_date: ['', Validators.required],
    end_date: ['', Validators.required],
    reason: [''],
  });

  ngOnInit(): void {
    this.loadRequests();
  }

  private loadRequests(): void {
    this.leaveService.getMyRequests().subscribe({
      next: (data) => this.requests.set(data.requests),
    });
  }

  protected onSubmit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.isSubmitting.set(true);
    this.statusMessage.set(null);

    const raw = this.form.getRawValue();

    this.leaveService
      .submitRequest({
        start_date: raw.start_date,
        end_date: raw.end_date,
        reason: raw.reason || null,
      })
      .subscribe({
        next: () => {
          this.isSubmitting.set(false);
          this.statusMessage.set({ type: 'success', text: this.i18n.t('leave_success') });
          this.form.reset();
          this.loadRequests();
          this.toast.success('Leave request submitted successfully');
        },
        error: (err) => {
          this.isSubmitting.set(false);
          this.statusMessage.set({
            type: 'error',
            text: err.error?.detail || this.i18n.t('leave_error'),
            
          });
          this.toast.error('Failed to submit leave request');
        },
      });
  }

  protected statusLabel(status: LeaveStatus): string {
    return this.i18n.t(`leave_status_${status}` as any);
  }
}