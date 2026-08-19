import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class LayoutService {
  // Desktop: collapsed = icons-only sidebar
  readonly isSidebarCollapsed = signal(false);

  // Mobile: sidebar as an overlay drawer, closed by default
  readonly isMobileSidebarOpen = signal(false);

  toggleCollapse(): void {
    this.isSidebarCollapsed.update((v) => !v);
  }

  toggleMobileSidebar(): void {
    this.isMobileSidebarOpen.update((v) => !v);
  }

  closeMobileSidebar(): void {
    this.isMobileSidebarOpen.set(false);
  }
}