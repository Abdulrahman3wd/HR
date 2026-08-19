import { Component, inject } from '@angular/core';
import { LucideAngularModule, Sun, Moon } from 'lucide-angular';
import { ThemeService } from '../../../core/services/theme.service';

@Component({
  selector: 'app-theme-toggle',
  imports: [LucideAngularModule],
  templateUrl: './theme-toggle.html',
  styleUrl: './theme-toggle.css',
})
export class ThemeToggle {
  protected readonly theme = inject(ThemeService);
  protected readonly SunIcon = Sun;
  protected readonly MoonIcon = Moon;
}