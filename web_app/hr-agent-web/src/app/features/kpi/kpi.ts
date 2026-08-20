import { Component, inject, signal, OnInit } from '@angular/core';
import { ReactiveFormsModule, FormsModule, FormBuilder } from '@angular/forms';
import { LucideAngularModule, TrendingUp, ClipboardList, CalendarRange } from 'lucide-angular';

import { KpiService } from '../../core/services/kpi.service';
import { AdminService } from '../../core/services/admin.service';
import { AuthService } from '../../core/services/auth.service';
import { I18nService } from '../../core/services/i18n.service';
import { KpiEvaluationRecord, AttendanceMetrics, CurrentQuarter } from '../../core/models/kpi.model';
import { AdminUserRecord } from '../../core/models/admin.model';

type KpiTab = 'my' | 'manage';

@Component({
  selector: 'app-kpi',
  imports: [ReactiveFormsModule, FormsModule, LucideAngularModule],
  templateUrl: './kpi.html',
  styleUrl: './kpi.css',
})
export class Kpi implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly kpiService = inject(KpiService);
  private readonly adminService = inject(AdminService);
  protected readonly auth = inject(AuthService);
  protected readonly i18n = inject(I18nService);

  protected readonly TrendIcon = TrendingUp;
  protected readonly ClipboardIcon = ClipboardList;
  protected readonly QuarterIcon = CalendarRange;

  protected readonly activeTab = signal<KpiTab>('my');
  protected readonly currentQuarter = signal<CurrentQuarter | null>(null);

  // ---------- "My Evaluations" state ----------
  protected readonly myEvaluations = signal<KpiEvaluationRecord[]>([]);

  // ---------- "Manage" state ----------
  protected readonly candidateEmployees = signal<AdminUserRecord[]>([]);
  protected readonly selectedEmployeeId = signal<string>('');
  protected readonly employeeHistory = signal<KpiEvaluationRecord[]>([]);

  protected readonly evalStatus = signal<{ type: 'success' | 'error'; text: string } | null>(null);
  protected readonly metrics = signal<AttendanceMetrics | null>(null);
  protected readonly isLoadingMetrics = signal(false);
  protected readonly isSubmittingEval = signal(false);

  protected readonly notesControl = this.fb.nonNullable.control('');

  ngOnInit(): void {
    this.loadMyEvaluations();
    this.loadCandidateEmployees();
    this.kpiService.getCurrentQuarter().subscribe({
      next: (data) => this.currentQuarter.set(data),
    });
  }

  protected switchTab(tab: KpiTab): void {
    this.activeTab.set(tab);
  }

  // ---------- My evaluations ----------
  private loadMyEvaluations(): void {
    this.kpiService.getMyEvaluations().subscribe({
      next: (data) => this.myEvaluations.set(data.evaluations),
    });
  }

  // ---------- Manage: employee selection ----------
  private loadCandidateEmployees(): void {
    this.adminService.listUsers().subscribe({
      next: (data) =>
        this.candidateEmployees.set(
          data.users.filter((u) => u.employee_id !== this.auth.currentUser()?.employee_id)
        ),
      error: () => this.candidateEmployees.set([]),
    });
  }

  protected onEmployeeSelected(employeeId: string): void {
    this.selectedEmployeeId.set(employeeId);
    this.metrics.set(null);
    this.evalStatus.set(null);
    this.notesControl.setValue('');

    if (employeeId) {
      this.kpiService.getEmployeeEvaluations(employeeId).subscribe({
        next: (data) => this.employeeHistory.set(data.evaluations),
        error: () => this.employeeHistory.set([]),
      });
    } else {
      this.employeeHistory.set([]);
    }
  }

  // ---------- Evaluation ----------
  protected loadMetrics(): void {
    const employeeId = this.selectedEmployeeId();
    if (!employeeId) return;

    this.isLoadingMetrics.set(true);
    this.metrics.set(null);

    this.kpiService.previewMetrics(employeeId).subscribe({
      next: (data) => {
        this.isLoadingMetrics.set(false);
        this.metrics.set(data);
      },
      error: (err) => {
        this.isLoadingMetrics.set(false);
        this.evalStatus.set({ type: 'error', text: err.error?.detail || 'Error' });
      },
    });
  }

  protected submitEvaluation(): void {
    const employeeId = this.selectedEmployeeId();
    if (!employeeId) return;

    this.isSubmittingEval.set(true);
    this.evalStatus.set(null);

    this.kpiService
      .submitEvaluation({ employee_id: employeeId, manager_notes: this.notesControl.value || null })
      .subscribe({
        next: (created) => {
          this.isSubmittingEval.set(false);
          this.evalStatus.set({ type: 'success', text: this.i18n.t('kpi_evaluation_saved') });
          this.notesControl.setValue('');
          this.metrics.set(null);
          this.employeeHistory.update((list) => [created, ...list]);
        },
        error: (err) => {
          this.isSubmittingEval.set(false);
          this.evalStatus.set({ type: 'error', text: err.error?.detail || 'Error' });
        },
      });
  }
}