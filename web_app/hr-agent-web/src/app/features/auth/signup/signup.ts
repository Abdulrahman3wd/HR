import { Component, inject, signal } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { LucideAngularModule, Building2, UserRound, Lock, IdCard, CheckCircle2 } from 'lucide-angular';

import { SignupService } from '../../../core/services/signup.service';
import { I18nService } from '../../../core/services/i18n.service';
import { ThemeToggle } from '../../../shared/components/theme-toggle/theme-toggle';
import { LangToggle } from '../../../shared/components/lang-toggle/lang-toggle';
import { ToastService } from '../../../core/services/toast.service';
import { ConfirmDialogService } from '../../../core/services/confirm-dialog.service';
@Component({
  selector: 'app-signup',
  imports: [ReactiveFormsModule, RouterLink, LucideAngularModule, ThemeToggle, LangToggle],
  templateUrl: './signup.html',
  styleUrl: './signup.css',
})
export class Signup {
  private readonly fb = inject(FormBuilder);
  private readonly signupService = inject(SignupService);
  private readonly router = inject(Router);
  protected readonly i18n = inject(I18nService);
private readonly toast = inject(ToastService);
protected readonly confirmDialog = inject(ConfirmDialogService);
  protected readonly BuildingIcon = Building2;
  protected readonly UserIcon = UserRound;
  protected readonly LockIcon = Lock;
  protected readonly IdIcon = IdCard;
  protected readonly SuccessIcon = CheckCircle2;

  protected readonly isLoading = signal(false);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly isSuccess = signal(false);
  protected readonly registeredCompanyCode = signal<string>('');

  protected readonly form = this.fb.nonNullable.group({
    company_name: ['', Validators.required],
    company_code: ['', [Validators.required, Validators.pattern(/^[A-Za-z0-9]+$/)]],
    admin_full_name: ['', Validators.required],
    admin_employee_id: ['', Validators.required],
    admin_password: ['', [Validators.required, Validators.minLength(6)]],
  });

  protected onSubmit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.isLoading.set(true);
    this.errorMessage.set(null);

    this.signupService.signup(this.form.getRawValue()).subscribe({
      next: (response) => {
        this.isLoading.set(false);
        this.isSuccess.set(true);
        this.registeredCompanyCode.set(response.company_code);
        this.toast.success('Signup successful');
      },
      error: (err) => {
        this.isLoading.set(false);
        this.errorMessage.set(err.error?.detail || 'Something went wrong');
        this.toast.error('Failed to signup');
      },
    });
  }

  protected goToLogin(): void {
    this.router.navigate(['/login']);
  }
}