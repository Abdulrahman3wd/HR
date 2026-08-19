import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { adminGuard } from './core/guards/admin.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./features/auth/login/login').then((m) => m.Login),
  },
  {
    path: '',
    canActivate: [authGuard],
    loadComponent: () => import('./layout/main-layout/main-layout').then((m) => m.MainLayout),
    children: [
      {
        path: 'chat',
        loadComponent: () => import('./features/chat/chat').then((m) => m.Chat),
      },
      {
        path: 'leave',
        loadComponent: () => import('./features/leave/leave').then((m) => m.Leave),
      },
      {
        path: 'history',
        loadComponent: () => import('./features/history/history').then((m) => m.History),
      },
    {
        path: 'account',
        loadComponent: () => import('./features/account/account').then((m) => m.Account),
      },
      {
        path: 'dashboard',
        canActivate: [adminGuard],
        loadComponent: () => import('./features/dashboard/dashboard').then((m) => m.Dashboard),
      },
     {
        path: 'admin',
        canActivate: [adminGuard],
        loadComponent: () => import('./features/admin/admin').then((m) => m.Admin),
      },
      { path: '', redirectTo: 'chat', pathMatch: 'full' },
    ],
  },
  { path: '**', redirectTo: 'login' },
];