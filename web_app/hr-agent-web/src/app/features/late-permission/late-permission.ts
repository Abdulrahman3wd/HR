import { Component, inject, signal, OnInit } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { LucideAngularModule, Clock, TrendingDown } from 'lucide-angular';

import { LatePermissionService } from '../../core/services/late-permission.service';
import { I18nService } from '../../core/services/i18n.service';
import { LatePermissionRecord, MonthlyLateUsage, PermissionStatus } from '../../core/models/late-permission.model';
import { TranslationKey } from '../../core/services/translations';
import { ToastService } from '../../core/services/toast.service';
import { ConfirmDialogService } from '../../core/services/confirm-dialog.service';
@Component({
  selector: 'app-late-permission',
  imports: [ReactiveFormsModule, LucideAngularModule],
  templateUrl: './late-permission.html',
  styleUrl: './late-permission.css',
})
export class LatePermission implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly service = inject(LatePermissionService);
  protected readonly i18n = inject(I18nService);
  protected readonly toast = inject(ToastService);
  protected readonly confirmDialog = inject(ConfirmDialogService);

  protected readonly ClockIcon = Clock;
  protected readonly UsageIcon = TrendingDown;

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

  ngOnInit(): void {
    this.loadUsage();
    this.loadRequests();
  }

  private loadUsage(): void {
    this.service.getMyUsage().subscribe({
      next: (data) => this.usage.set(data),
    });
  }

  private loadRequests(): void {
    this.service.getMyPermissions().subscribe({
      next: (data) => this.requests.set(data.permissions),
    });
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
      .submit({
        date: raw.date,
        from_time: raw.from_time,
        to_time: raw.to_time,
        reason: raw.reason || null,
      })
      .subscribe({
        next: () => {
          this.isSubmitting.set(false);
          this.statusMessage.set({ type: 'success', text: this.i18n.t('late_submitted') });
          this.form.reset();
          this.loadRequests();
          this.loadUsage();
          this.toast.success('Late permission submitted successfully');
        },
        error: (err) => {
          this.isSubmitting.set(false);
          this.statusMessage.set({ type: 'error', text: err.error?.detail || 'Error' });
          this.toast.error('Failed to submit late permission');
        },
      });
  }

  protected statusLabel(status: PermissionStatus): string {
    return this.i18n.t(('leave_status_' + status) as TranslationKey);
  }
}