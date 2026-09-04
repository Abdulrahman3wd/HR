import { Component, inject, signal, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { LucideAngularModule, Briefcase, Upload, FileText, CheckCircle2 } from 'lucide-angular';

import { RecruitmentService } from '../../core/services/recruitment.service';
import { I18nService } from '../../core/services/i18n.service';
import { ThemeToggle } from '../../shared/components/theme-toggle/theme-toggle';
import { LangToggle } from '../../shared/components/lang-toggle/lang-toggle';
import { PublicJob, CustomQuestion } from '../../core/models/recruitment.model';

@Component({
  selector: 'app-public-apply',
  imports: [FormsModule, LucideAngularModule, ThemeToggle, LangToggle],
  templateUrl: './public-apply.html',
  styleUrl: './public-apply.css',
})
export class PublicApply implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly recruitmentService = inject(RecruitmentService);
  protected readonly i18n = inject(I18nService);

  protected readonly BriefcaseIcon = Briefcase;
  protected readonly UploadIcon = Upload;
  protected readonly FileIcon = FileText;
  protected readonly SuccessIcon = CheckCircle2;

  protected readonly job = signal<PublicJob | null>(null);
  protected readonly isLoading = signal(true);
  protected readonly notFound = signal(false);

  protected readonly fullName = signal('');
  protected readonly email = signal('');
  protected readonly phone = signal('');
  protected readonly customAnswers = signal<Record<string, string>>({});
  protected readonly selectedFile = signal<File | null>(null);

  protected readonly isSubmitting = signal(false);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly isSuccess = signal(false);

  ngOnInit(): void {
    const jobId = Number(this.route.snapshot.paramMap.get('jobId'));
    if (!jobId) {
      this.notFound.set(true);
      this.isLoading.set(false);
      return;
    }

    this.recruitmentService.getPublicJob(jobId).subscribe({
      next: (data) => {
        this.job.set(data);
        this.isLoading.set(false);
      },
      error: () => {
        this.notFound.set(true);
        this.isLoading.set(false);
      },
    });
  }

  protected onAnswerChange(question: string, value: string): void {
    this.customAnswers.update((answers) => ({ ...answers, [question]: value }));
  }

  protected onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;

    if (file) {
      const allowedExtensions = ['.pdf', '.docx', '.txt'];
      const fileName = file.name.toLowerCase();
      const isValid = allowedExtensions.some((ext) => fileName.endsWith(ext));

      if (!isValid) {
        this.errorMessage.set(this.i18n.t('apply_invalid_file'));
        this.selectedFile.set(null);
        input.value = '';
        return;
      }
    }

    this.errorMessage.set(null);
    this.selectedFile.set(file);
  }

  protected isFormValid(): boolean {
    const j = this.job();
    if (!j) return false;
    if (!this.fullName().trim()) return false;
    if (!this.selectedFile()) return false;

    for (const q of j.custom_questions) {
      if (q.required && !this.customAnswers()[q.question]?.trim()) {
        return false;
      }
    }
    return true;
  }

  protected submit(): void {
    const j = this.job();
    const file = this.selectedFile();
    if (!j || !file) return;

    if (!this.isFormValid()) {
      this.errorMessage.set(this.i18n.t('apply_fill_required'));
      return;
    }

    this.isSubmitting.set(true);
    this.errorMessage.set(null);

    this.recruitmentService
      .submitPublicApplication(
        j.id,
        this.fullName().trim(),
        this.email().trim() || null,
        this.phone().trim() || null,
        this.customAnswers(),
        file
      )
      .subscribe({
        next: () => {
          this.isSubmitting.set(false);
          this.isSuccess.set(true);
        },
        error: (err) => {
          this.isSubmitting.set(false);
          this.errorMessage.set(err.error?.detail || this.i18n.t('apply_error'));
        },
      });
  }

  protected questionInputType(question: CustomQuestion): string {
    if (question.type === 'number') return 'number';
    return 'text';
  }
}