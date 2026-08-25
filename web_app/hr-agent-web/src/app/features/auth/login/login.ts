import { Component, inject, signal } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { LucideAngularModule, Building2, UserRound, Lock } from 'lucide-angular';

import { AuthService } from '../../../core/services/auth.service';
import { I18nService } from '../../../core/services/i18n.service';
import { ThemeToggle } from '../../../shared/components/theme-toggle/theme-toggle';
import { LangToggle } from '../../../shared/components/lang-toggle/lang-toggle';
import { ToastService } from '../../../core/services/toast.service';
import { ConfirmDialogService } from '../../../core/services/confirm-dialog.service';
@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule, LucideAngularModule, ThemeToggle, LangToggle, RouterLink],
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class Login {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  protected readonly i18n = inject(I18nService);
protected readonly toast = inject(ToastService);
protected readonly confirmDialog = inject(ConfirmDialogService);
  protected readonly BuildingIcon = Building2;
  protected readonly UserIcon = UserRound;
  protected readonly LockIcon = Lock;

  protected readonly isLoading = signal(false);
  protected readonly errorMessage = signal<string | null>(null);

  protected readonly form = this.fb.nonNullable.group({
    company_code: ['', Validators.required],
    employee_id: ['', Validators.required],
    password: ['', Validators.required],
  });

  protected onSubmit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.isLoading.set(true);
    this.errorMessage.set(null);

    this.auth.login(this.form.getRawValue()).subscribe({
      next: (response) => {
        this.auth.setSession(response);
        this.isLoading.set(false);
        this.router.navigate(['/chat']);
        this.toast.success('Login successful');
      },
      error: (err) => {
        this.isLoading.set(false);
        this.errorMessage.set(
          err.status === 0
            ? this.i18n.t('login_error_network')
            : this.i18n.t('login_error_generic')
        );
        this.toast.error('Failed to login');
      },
    });
  }
}