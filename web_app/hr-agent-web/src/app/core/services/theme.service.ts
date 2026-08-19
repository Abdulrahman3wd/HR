import { Injectable, signal, effect } from '@angular/core';

export type Theme = 'light' | 'dark';

const THEME_STORAGE_KEY = 'app-theme';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  readonly theme = signal<Theme>(this.getInitialTheme());

  constructor() {
    // Whenever the signal changes, apply it to the DOM and persist it.
    effect(() => {
      const currentTheme = this.theme();
      document.documentElement.classList.toggle('dark', currentTheme === 'dark');
      localStorage.setItem(THEME_STORAGE_KEY, currentTheme);
    });
  }

  toggle(): void {
    this.theme.set(this.theme() === 'dark' ? 'light' : 'dark');
  }

  setTheme(theme: Theme): void {
    this.theme.set(theme);
  }

  private getInitialTheme(): Theme {
    const saved = localStorage.getItem(THEME_STORAGE_KEY) as Theme | null;
    if (saved === 'light' || saved === 'dark') {
      return saved;
    }
    return 'light';
  }
}