import { Component, inject, signal, OnInit } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { LucideAngularModule, Clock, TrendingDown, TrendingUp } from 'lucide-angular';

import { LatePermissionService } from '../../core/services/late-permission.service';
import { OvertimeService } from '../../core/services/overtime.service';
import { I18nService } from '../../core/services/i18n.service';
import { LatePermissionRecord, MonthlyLateUsage, PermissionStatus } from '../../core/models/late-permission.model';
import { OvertimeRequestRecord } from '../../core/models/overtime.model';
import { TranslationKey } from '../../core/services/translations';

type PageTab = 'late' | 'overtime';

@Component({
  selector: 'app-late-permission',
  imports: [ReactiveFormsModule, LucideAngularModule],
  templateUrl: './late-permission.html',
  styleUrl: './late-permission.css',
})
export class LatePermission implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly service = inject(LatePermissionService);
  private readonly overtimeService = inject(OvertimeService);
  protected readonly i18n = inject(I18nService);

  protected readonly ClockIcon = Clock;
  protected readonly UsageIcon = TrendingDown;
  protected readonly OvertimeIcon = TrendingUp;

  protected readonly activeTab = signal<PageTab>('late');

  // ---------- Late permission state ----------
  protected readonly usage = signal<MonthlyLateUsage | null>(null);
  protected readonly requests = signal<LatePermissionRecord[]>([]);
  protected readonly isSubmitting = signal(false);
  protected readonly statusMessage = signal<{ type: 'success' | 'error'; text: string } | null>(null);

  protected readonly form = this.fb.nonNullable.group({
    date: ['', Validators.required],
    from_time: ['', Validators.required],
    to_time: ['', Validators.required],
    reason: [''],
  });

  // ---------- Overtime state ----------
  protected readonly overtimeRequests = signal<OvertimeRequestRecord[]>([]);
  protected readonly isSubmittingOvertime = signal(false);
  protected readonly overtimeStatusMessage = signal<{ type: 'success' | 'error'; text: string } | null>(null);

  protected readonly overtimeForm = this.fb.nonNullable.group({
    date: ['', Validators.required],
    from_time: ['', Validators.required],
    to_time: ['', Validators.required],
    reason: [''],
  });

  ngOnInit(): void {
    this.loadUsage();
    this.loadRequests();
    this.loadOvertimeRequests();
  }

  protected switchTab(tab: PageTab): void {
    this.activeTab.set(tab);
  }

  // ---------- Late permission logic ----------
  private loadUsage(): void {
    this.service.getMyUsage().subscribe({ next: (data) => this.usage.set(data) });
  }

  private loadRequests(): void {
    this.service.getMyPermissions().subscribe({ next: (data) => this.requests.set(data.permissions) });
  }

  protected usagePercentage(): number {
    const u = this.usage();
    if (!u || u.allowance_minutes === 0) return 0;
    return Math.min(100, Math.round((u.used_minutes / u.allowance_minutes) * 100));
  }

  protected onSubmit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.isSubmitting.set(true);
    this.statusMessage.set(null);
    const raw = this.form.getRawValue();

    this.service
      .submit({ date: raw.date, from_time: raw.from_time, to_time: raw.to_time, reason: raw.reason || null })
      .subscribe({
        next: () => {
          this.isSubmitting.set(false);
          this.statusMessage.set({ type: 'success', text: this.i18n.t('late_submitted') });
          this.form.reset();
          this.loadRequests();
          this.loadUsage();
        },
        error: (err) => {
          this.isSubmitting.set(false);
          this.statusMessage.set({ type: 'error', text: err.error?.detail || 'Error' });
        },
      });
  }

  protected statusLabel(status: PermissionStatus): string {
    return this.i18n.t(('leave_status_' + status) as TranslationKey);
  }

  // ---------- Overtime logic ----------
  private loadOvertimeRequests(): void {
    this.overtimeService.getMyRequests().subscribe({ next: (data) => this.overtimeRequests.set(data.requests) });
  }

  protected onSubmitOvertime(): void {
    if (this.overtimeForm.invalid) {
      this.overtimeForm.markAllAsTouched();
      return;
    }

    this.isSubmittingOvertime.set(true);
    this.overtimeStatusMessage.set(null);
    const raw = this.overtimeForm.getRawValue();

    this.overtimeService
      .submit({ date: raw.date, from_time: raw.from_time, to_time: raw.to_time, reason: raw.reason || null })
      .subscribe({
        next: () => {
          this.isSubmittingOvertime.set(false);
          this.overtimeStatusMessage.set({ type: 'success', text: this.i18n.t('overtime_submitted') });
          this.overtimeForm.reset();
          this.loadOvertimeRequests();
        },
        error: (err) => {
          this.isSubmittingOvertime.set(false);
          this.overtimeStatusMessage.set({ type: 'error', text: err.error?.detail || 'Error' });
        },
      });
  }
}