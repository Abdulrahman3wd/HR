import { Component, inject, signal, OnInit } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators, AbstractControl, ValidationErrors } from '@angular/forms';
import { LucideAngularModule, KeyRound } from 'lucide-angular';

import { AccountService } from '../../core/services/account.service';
import { DepartmentService } from '../../core/services/department.service';
import { I18nService } from '../../core/services/i18n.service';
import { CurrentUserProfile } from '../../core/models/account.model';
import { Department } from '../../core/models/department.model';

function passwordsMatchValidator(control: AbstractControl): ValidationErrors | null {
  const newPassword = control.get('new_password')?.value;
  const confirmPassword = control.get('confirm_password')?.value;
  return newPassword === confirmPassword ? null : { mismatch: true };
}

@Component({
  selector: 'app-account',
  imports: [ReactiveFormsModule, LucideAngularModule],
  templateUrl: './account.html',
  styleUrl: './account.css',
})
export class Account implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly accountService = inject(AccountService);
  private readonly departmentService = inject(DepartmentService);
  protected readonly i18n = inject(I18nService);

  protected readonly departments = signal<Department[]>([]);
  protected readonly KeyIcon = KeyRound;

  protected readonly profile = signal<CurrentUserProfile | null>(null);
  protected readonly isChanging = signal(false);
  protected readonly statusMessage = signal<{ type: 'success' | 'error'; text: string } | null>(null);

  protected readonly form = this.fb.nonNullable.group(
    {
      current_password: ['', Validators.required],
      new_password: ['', [Validators.required, Validators.minLength(6)]],
      confirm_password: ['', Validators.required],
    },
    { validators: passwordsMatchValidator }
  );

  ngOnInit(): void {
    this.accountService.getMyProfile().subscribe({
      next: (data) => this.profile.set(data),
    });

    this.departmentService.list().subscribe({
      next: (data) => this.departments.set(data.departments),
      error: () => this.departments.set([]), // employees may not have permission; fail silently
    });
  }
protected roleLabel(role: 'admin' | 'hr' | 'employee'): string {
  if (role === 'admin') return this.i18n.t('account_role_admin');
  if (role === 'hr') return this.i18n.t('account_role_hr');
  return this.i18n.t('account_role_employee');
}

  protected departmentName(departmentId: number | null): string {
    if (!departmentId) return '—';
    return this.departments().find((d) => d.id === departmentId)?.name ?? '—';
  }
  protected onSubmit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      if (this.form.hasError('mismatch')) {
        this.statusMessage.set({ type: 'error', text: this.i18n.t('account_password_mismatch') });
      }
      return;
    }

    this.isChanging.set(true);
    this.statusMessage.set(null);

    const raw = this.form.getRawValue();

    this.accountService
      .changePassword({ current_password: raw.current_password, new_password: raw.new_password })
      .subscribe({
        next: () => {
          this.isChanging.set(false);
          this.statusMessage.set({ type: 'success', text: this.i18n.t('account_password_changed') });
          this.form.reset();
        },
        error: (err) => {
          this.isChanging.set(false);
          this.statusMessage.set({
            type: 'error',
            text: err.error?.detail || this.i18n.t('account_password_error'),
          });
        },
      });
  }
}