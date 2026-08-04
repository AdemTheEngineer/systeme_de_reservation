import { Routes } from '@angular/router';
import { homeRedirectGuard } from './core/auth/home-redirect.guard';
import { roleGuard } from './core/auth/role.guard';
import { Role } from './core/models';

export const routes: Routes = [
  {
    path: 'dev/ui',
    loadComponent: () => import('./dev-ui/dev-ui').then((m) => m.DevUi),
  },
  {
    path: 'auth/login',
    loadComponent: () => import('./features/auth/login/login').then((m) => m.Login),
  },
  {
    path: 'membre',
    loadComponent: () => import('./layout/membre-shell/membre-shell').then((m) => m.MembreShell),
    canActivate: [roleGuard([Role.Membre])],
    children: [
      {
        path: '',
        loadComponent: () => import('./features/dashboard/membre-dashboard/membre-dashboard').then((m) => m.MembreDashboard),
      },
      {
        path: 'espaces',
        loadComponent: () => import('./features/espaces/catalogue/catalogue').then((m) => m.Catalogue),
      },
      {
        path: 'espaces/:id',
        loadComponent: () => import('./features/espaces/detail/detail').then((m) => m.EspaceDetail),
      },
      {
        path: 'reservations',
        loadComponent: () => import('./features/reservations/mes-reservations/mes-reservations').then((m) => m.MesReservations),
      },
      {
        path: 'reservations/nouvelle',
        loadComponent: () => import('./features/reservations/wizard/wizard').then((m) => m.ReservationWizard),
      },
      {
        path: 'profil',
        loadComponent: () => import('./features/auth/profile/profile').then((m) => m.Profile),
      },
    ],
  },
  {
    path: 'gestionnaire',
    loadComponent: () => import('./layout/gestionnaire-shell/gestionnaire-shell').then((m) => m.GestionnaireShell),
    canActivate: [roleGuard([Role.Gestionnaire])],
    children: [
      {
        path: '',
        loadComponent: () =>
          import('./features/dashboard/gestionnaire-dashboard/gestionnaire-dashboard').then((m) => m.GestionnaireDashboard),
      },
      {
        path: 'espaces',
        loadComponent: () => import('./features/espaces-admin/liste/liste').then((m) => m.EspacesAdminListe),
      },
      {
        path: 'espaces/:id/creneaux',
        loadComponent: () => import('./features/espaces-admin/creneaux/creneaux').then((m) => m.EspaceCreneaux),
      },
      {
        path: 'reservations',
        loadComponent: () => import('./features/reservations-admin/liste/liste').then((m) => m.ReservationsAdminListe),
      },
      {
        path: 'paiements',
        loadComponent: () => import('./features/paiements-admin/liste/liste').then((m) => m.PaiementsAdminListe),
      },
      {
        path: 'membres',
        loadComponent: () => import('./features/membres-admin/liste/liste').then((m) => m.MembresAdminListe),
      },
      {
        path: 'profil',
        loadComponent: () => import('./features/auth/profile/profile').then((m) => m.Profile),
      },
    ],
  },
  {
    path: '403',
    loadComponent: () => import('./features/auth/forbidden/forbidden').then((m) => m.Forbidden),
  },
  { path: '', pathMatch: 'full', canActivate: [homeRedirectGuard], children: [] },
  {
    path: '**',
    loadComponent: () => import('./features/auth/not-found/not-found').then((m) => m.NotFound),
  },
];
