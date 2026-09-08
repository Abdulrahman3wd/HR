import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { LucideAngularModule, Menu, Search } from 'lucide-angular';

import { Sidebar } from '../sidebar/sidebar';
import { ThemeToggle } from '../../shared/components/theme-toggle/theme-toggle';
import { LangToggle } from '../../shared/components/lang-toggle/lang-toggle';
import { ToastContainer } from '../../shared/components/toast-container/toast-container';
import { ConfirmDialog } from '../../shared/components/confirm-dialog/confirm-dialog';
import { LayoutService } from '../../core/services/layout.service';
import { AuthService } from '../../core/services/auth.service';
import { I18nService } from '../../core/services/i18n.service';

@Component({
  selector: 'app-main-layout',
  imports: [RouterOutlet, Sidebar, ThemeToggle, LangToggle, LucideAngularModule, ToastContainer, ConfirmDialog],
  templateUrl: './main-layout.html',
  styleUrl: './main-layout.css',
})
export class MainLayout {
  protected readonly layout = inject(LayoutService);
  protected readonly auth = inject(AuthService);
  protected readonly i18n = inject(I18nService);
  protected readonly MenuIcon = Menu;
  protected readonly SearchIcon = Search;

  protected roleLabel(): string {
    const role = this.auth.currentUser()?.role ?? 'employee';
    return this.i18n.t(`account_role_${role}` as 'account_role_admin' | 'account_role_hr' | 'account_role_employee');
  }
}