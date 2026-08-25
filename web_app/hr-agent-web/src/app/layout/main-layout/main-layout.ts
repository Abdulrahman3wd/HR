import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { LucideAngularModule, Menu } from 'lucide-angular';

import { Sidebar } from '../sidebar/sidebar';
import { ThemeToggle } from '../../shared/components/theme-toggle/theme-toggle';
import { LangToggle } from '../../shared/components/lang-toggle/lang-toggle';
import { ToastContainer } from '../../shared/components/toast-container/toast-container';
import { ConfirmDialog } from '../../shared/components/confirm-dialog/confirm-dialog';
import { LayoutService } from '../../core/services/layout.service';

@Component({
  selector: 'app-main-layout',
  imports: [RouterOutlet, Sidebar, ThemeToggle, LangToggle, LucideAngularModule, ToastContainer, ConfirmDialog],
  templateUrl: './main-layout.html',
  styleUrl: './main-layout.css',
})
export class MainLayout {
  protected readonly layout = inject(LayoutService);
  protected readonly MenuIcon = Menu;
}