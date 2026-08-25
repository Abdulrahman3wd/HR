import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { ReactiveFormsModule, FormsModule, FormBuilder, Validators } from '@angular/forms';
import { LucideAngularModule, Briefcase, Users, Plus, X, Upload } from 'lucide-angular';
import { DragDropModule, CdkDragDrop, moveItemInArray, transferArrayItem } from '@angular/cdk/drag-drop';
import { TranslationKey } from '../../core/services/translations';
import { RecruitmentService } from '../../core/services/recruitment.service';
import { I18nService } from '../../core/services/i18n.service';
import { JobOpening, Candidate, CandidateStage } from '../../core/models/recruitment.model';

type RecruitmentTab = 'jobs' | 'pipeline';

const PIPELINE_STAGES: CandidateStage[] = [
  'applied',
  'reviewing',
  'hr_interview',
  'technical_interview',
  'accepted',
  'rejected',
];

@Component({
  selector: 'app-recruitment',
  imports: [ReactiveFormsModule, FormsModule, LucideAngularModule, DragDropModule],
  templateUrl: './recruitment.html',
  styleUrl: './recruitment.css',
})
export class Recruitment implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly recruitmentService = inject(RecruitmentService);
  protected readonly i18n = inject(I18nService);

  protected readonly JobsIcon = Briefcase;
  protected readonly PipelineIcon = Users;
  protected readonly PlusIcon = Plus;
  protected readonly CloseIcon = X;
  protected readonly UploadIcon = Upload;

  protected readonly activeTab = signal<RecruitmentTab>('jobs');
  protected readonly stages = PIPELINE_STAGES;

  // ---------- Jobs state ----------
  protected readonly jobs = signal<JobOpening[]>([]);
  protected readonly jobStatus = signal<{ type: 'success' | 'error'; text: string } | null>(null);
  protected readonly isCreatingJob = signal(false);
  protected readonly showJobForm = signal(false);

  protected readonly jobForm = this.fb.nonNullable.group({
    title: ['', Validators.required],
    description: ['', Validators.required],
    requirements: ['', Validators.required],
  });

  // ---------- Pipeline state ----------
  protected readonly candidates = signal<Candidate[]>([]);
  protected readonly selectedJobId = signal<number | null>(null);
  protected readonly showCandidateForm = signal(false);
  protected readonly candidateStatus = signal<{ type: 'success' | 'error'; text: string } | null>(null);
  protected readonly isAddingCandidate = signal(false);
  protected readonly selectedCvFile = signal<File | null>(null);
  protected readonly expandedCandidateId = signal<number | null>(null);

  protected readonly candidateForm = this.fb.nonNullable.group({
    full_name: ['', Validators.required],
    email: [''],
    phone: [''],
  });

  protected readonly openJobs = computed(() => this.jobs().filter((j) => j.status === 'open'));

  ngOnInit(): void {
    this.loadJobs();
  }

  protected switchTab(tab: RecruitmentTab): void {
    this.activeTab.set(tab);
  }

  // ---------- Jobs logic ----------
  private loadJobs(): void {
    this.recruitmentService.listJobs().subscribe({
      next: (data) => this.jobs.set(data.jobs),
    });
  }

  protected toggleJobForm(): void {
    this.showJobForm.update((v) => !v);
  }

  protected createJob(): void {
    if (this.jobForm.invalid) {
      this.jobForm.markAllAsTouched();
      return;
    }

    this.isCreatingJob.set(true);
    this.jobStatus.set(null);

    this.recruitmentService.createJob({ ...this.jobForm.getRawValue(), department_id: null }).subscribe({
      next: () => {
        this.isCreatingJob.set(false);
        this.jobForm.reset();
        this.showJobForm.set(false);
        this.loadJobs();
      },
      error: (err) => {
        this.isCreatingJob.set(false);
        this.jobStatus.set({ type: 'error', text: err.error?.detail || 'Error' });
      },
    });
  }

  protected closeJob(jobId: number): void {
    this.recruitmentService.closeJob(jobId).subscribe({ next: () => this.loadJobs() });
  }

  protected reopenJob(jobId: number): void {
    this.recruitmentService.reopenJob(jobId).subscribe({ next: () => this.loadJobs() });
  }

  // ---------- Pipeline logic ----------
  protected onJobFilterChange(jobId: string): void {
    const id = jobId ? Number(jobId) : null;
    this.selectedJobId.set(id);
    this.loadCandidates();
  }

  private loadCandidates(): void {
    const jobId = this.selectedJobId();
    this.recruitmentService.listCandidates(jobId ?? undefined).subscribe({
      next: (data) => this.candidates.set(data.candidates),
    });
  }

  protected readonly groupedByStage = computed(() => {
    const groups = new Map<CandidateStage, Candidate[]>();
    for (const stage of PIPELINE_STAGES) {
      groups.set(stage, []);
    }
    for (const candidate of this.candidates()) {
      groups.get(candidate.stage)?.push(candidate);
    }
    return groups;
  });

  protected candidatesInStage(stage: CandidateStage): Candidate[] {
    return this.groupedByStage().get(stage) ?? [];
  }

  protected connectedDropLists(): string[] {
    return this.stages.map((s) => 'stage-' + s);
  }
  protected toggleCandidateForm(): void {
    this.showCandidateForm.update((v) => !v);
  }

  protected onCvFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.selectedCvFile.set(input.files?.[0] ?? null);
  }

  protected addCandidate(): void {
    const jobId = this.selectedJobId();
    if (!jobId || this.candidateForm.invalid) {
      this.candidateForm.markAllAsTouched();
      return;
    }

    this.isAddingCandidate.set(true);
    this.candidateStatus.set(null);
    const raw = this.candidateForm.getRawValue();

    this.recruitmentService
      .addCandidate(jobId, raw.full_name, raw.email || null, raw.phone || null, this.selectedCvFile())
      .subscribe({
        next: () => {
          this.isAddingCandidate.set(false);
          this.candidateForm.reset();
          this.selectedCvFile.set(null);
          this.showCandidateForm.set(false);
          this.loadCandidates();
        },
        error: (err) => {
          this.isAddingCandidate.set(false);
          this.candidateStatus.set({ type: 'error', text: err.error?.detail || 'Error' });
        },
      });
  }

  protected moveToStage(candidateId: number, stage: CandidateStage): void {
    this.recruitmentService.updateStage(candidateId, stage).subscribe({
      next: (updated) => {
        this.candidates.update((list) => list.map((c) => (c.id === updated.id ? updated : c)));
      },
    });
  }

  protected toggleExpand(candidateId: number): void {
    this.expandedCandidateId.update((current) => (current === candidateId ? null : candidateId));
  }

  protected scoreColorClass(score: number | null): string {
    if (score === null) return '';
    if (score >= 75) return 'score-high';
    if (score >= 50) return 'score-medium';
    return 'score-low';
  }
    protected stageLabel(stage: CandidateStage): string {
    return this.i18n.t(('stage_' + stage) as TranslationKey);
  }
    protected onDrop(event: CdkDragDrop<Candidate[]>, targetStage: CandidateStage): void {
    if (event.previousContainer === event.container) {
      return; // dropped in the same column, no stage change
    }

    const candidate = event.previousContainer.data[event.previousIndex];

    // Optimistic UI update: move the card immediately, then confirm with the server
    transferArrayItem(
      event.previousContainer.data,
      event.container.data,
      event.previousIndex,
      event.currentIndex
    );

    this.recruitmentService.updateStage(candidate.id, targetStage).subscribe({
      next: (updated) => {
        this.candidates.update((list) => list.map((c) => (c.id === updated.id ? updated : c)));
      },
      error: () => {
        // Revert on failure by reloading the authoritative state from the server
        this.loadCandidates();
      },
    });
  }
}