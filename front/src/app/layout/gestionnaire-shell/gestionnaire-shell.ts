import { Component, computed, inject } from '@angular/core';
import { Router } from '@angular/router';
import { AuthStore } from '../../core/auth/auth-store';
import { AuthService } from '../../core/services/auth.service';
import { AppShell } from '../../shared/layout/app-shell/app-shell';
import { NavItem } from '../../shared/layout/sidebar/sidebar';

const NAV_ITEMS: NavItem[] = [
  { label: 'Tableau de bord', icon: 'layout-dashboard', route: '/gestionnaire' },
  { label: 'Espaces', icon: 'building-2', route: '/gestionnaire/espaces' },
  { label: 'Réservations', icon: 'calendar-days', route: '/gestionnaire/reservations' },
  { label: 'Paiements', icon: 'wallet', route: '/gestionnaire/paiements' },
  { label: 'Membres', icon: 'users', route: '/gestionnaire/membres' },
  { label: 'Profil', icon: 'user', route: '/gestionnaire/profil' },
];

@Component({
  selector: 'app-gestionnaire-shell',
  imports: [AppShell],
  template: `
    <app-shell
      [navItems]="navItems"
      [userName]="userName()"
      roleLabel="Gestionnaire"
      (logoutRequested)="onLogout()"
    />
  `,
})
export class GestionnaireShell {
  private readonly authStore = inject(AuthStore);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly navItems = NAV_ITEMS;
  protected readonly userName = computed(() => {
    const user = this.authStore.currentUser();
    return user ? `${user.first_name} ${user.last_name}`.trim() || user.email : '';
  });

  protected async onLogout(): Promise<void> {
    await this.authService.logout();
    await this.router.navigateByUrl('/auth/login');
  }
}
