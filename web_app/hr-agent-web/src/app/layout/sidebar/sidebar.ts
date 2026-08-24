import { Component, inject, computed } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import {
  LucideAngularModule,
  MessageCircle,
  CalendarDays,
  History,
  UserRound,
  LayoutDashboard,
  ShieldCheck,
  LogOut,
  PanelLeftClose,
  PanelLeftOpen,
  Users2,
  TrendingUp,
  Briefcase,
  Clock3,
} from 'lucide-angular';
import { AuthService } from '../../core/services/auth.service';
import { I18nService } from '../../core/services/i18n.service';
import { LayoutService } from '../../core/services/layout.service';

@Component({
  selector: 'app-sidebar',
  imports: [RouterLink, RouterLinkActive, LucideAngularModule],
  templateUrl: './sidebar.html',
  styleUrl: './sidebar.css',
})
export class Sidebar {
  protected readonly auth = inject(AuthService);
  protected readonly i18n = inject(I18nService);
  protected readonly layout = inject(LayoutService);
  protected readonly TeamIcon = Users2;
  protected readonly ChatIcon = MessageCircle;
  protected readonly LeaveIcon = CalendarDays;
  protected readonly HistoryIcon = History;
  protected readonly AccountIcon = UserRound;
  protected readonly DashboardIcon = LayoutDashboard;
  protected readonly AdminIcon = ShieldCheck;
  protected readonly LogoutIcon = LogOut;
  protected readonly KpiIcon = TrendingUp;
  protected readonly RecruitmentIcon = Briefcase;
  protected readonly LatePermissionIcon = Clock3;
protected readonly toggleIcon = computed(() => {
  const isRtl = this.i18n.lang() === 'ar';
  const collapsed = this.layout.isSidebarCollapsed();
  // In RTL, the "collapse" direction is visually mirrored
  if (isRtl) {
    return collapsed ? PanelLeftClose : PanelLeftOpen;
  }
  return collapsed ? PanelLeftOpen : PanelLeftClose;
});
  protected logout(): void {
    this.auth.logout();
  }

  protected onNavItemClick(): void {
    // Close the mobile drawer whenever a nav link is tapped
    this.layout.closeMobileSidebar();
  }
}