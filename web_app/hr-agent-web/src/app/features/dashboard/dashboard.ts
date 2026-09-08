import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { LucideAngularModule, Activity, ArrowUpRight, UsersRound } from 'lucide-angular';

import { DashboardService } from '../../core/services/dashboard.service';
import { I18nService } from '../../core/services/i18n.service';
import { AuthService } from '../../core/services/auth.service';
import { DashboardStats } from '../../core/models/dashboard.model';

@Component({
  selector: 'app-dashboard',
  imports: [LucideAngularModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard implements OnInit {
  private readonly dashboardService = inject(DashboardService);
  protected readonly i18n = inject(I18nService);
  protected readonly auth = inject(AuthService);

  protected readonly ActivityIcon = Activity;
  protected readonly UsersIcon = UsersRound;
  protected readonly ArrowIcon = ArrowUpRight;

  protected readonly stats = signal<DashboardStats | null>(null);

  protected readonly titleKey = computed(() => {
    const role = this.auth.currentUser()?.role;
    if (role === 'hr') return 'dashboard_hr_title';
    if (role === 'employee') return 'dashboard_employee_title';
    return 'dashboard_admin_title';
  });

  protected readonly maxTopUserCount = computed(() => {
    const users = this.stats()?.top_users ?? [];
    return users.length > 0 ? Math.max(...users.map((u) => u.question_count)) : 1;
  });

  ngOnInit(): void {
    this.dashboardService.getStats().subscribe({
      next: (data) => this.stats.set(data),
    });
  }

  protected barWidth(count: number): number {
    return (count / this.maxTopUserCount()) * 100;
  }

  protected roleLabel(): string {
    const role = this.auth.currentUser()?.role ?? 'employee';
    return this.i18n.t(`account_role_${role}` as 'account_role_admin' | 'account_role_hr' | 'account_role_employee');
  }

  protected readonly dispatches = [
    'dashboard_bulletin_1',
    'dashboard_bulletin_2',
    'dashboard_bulletin_3',
  ] as const;
}