import { Component, inject, signal } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { LucideAngularModule, Eye, EyeOff, Loader2, AlertCircle, CheckCircle2 } from 'lucide-angular';

import { SignupService } from '../../../core/services/signup.service';
import { I18nService } from '../../../core/services/i18n.service';
import { ThemeToggle } from '../../../shared/components/theme-toggle/theme-toggle';
import { LangToggle } from '../../../shared/components/lang-toggle/lang-toggle';
import { ToastService } from '../../../core/services/toast.service';
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
  protected readonly EyeIcon = Eye;
  protected readonly EyeOffIcon = EyeOff;
  protected readonly LoaderIcon = Loader2;
  protected readonly AlertIcon = AlertCircle;
  protected readonly SuccessIcon = CheckCircle2;

  protected readonly isLoading = signal(false);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly isSuccess = signal(false);
  protected readonly registeredCompanyCode = signal<string>('');
  protected readonly showPassword = signal(false);

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

  protected togglePasswordVisibility(): void {
    this.showPassword.update((value) => !value);
  }

  protected hasError(controlName: keyof typeof this.form.controls): boolean {
    const control = this.form.controls[controlName];
    return control.invalid && (control.touched || control.dirty);
  }

  protected errorFor(controlName: keyof typeof this.form.controls): string | null {
    if (!this.hasError(controlName)) {
      return null;
    }

    const control = this.form.controls[controlName];
    if (control.hasError('pattern')) {
      return this.i18n.t('signup_error_code');
    }
    if (control.hasError('minlength')) {
      return this.i18n.t('signup_error_password');
    }
    return this.i18n.t('signup_error_required');
  }

  protected goToLogin(): void {
    this.router.navigate(['/login']);
  }
}