import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { LucideAngularModule, Users, CalendarClock, MessageSquare } from 'lucide-angular';

import { DashboardService } from '../../core/services/dashboard.service';
import { I18nService } from '../../core/services/i18n.service';
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

  protected readonly UsersIcon = Users;
  protected readonly LeaveIcon = CalendarClock;
  protected readonly ChatIcon = MessageSquare;

  protected readonly stats = signal<DashboardStats | null>(null);

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
}