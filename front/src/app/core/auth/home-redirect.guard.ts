import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { Role } from '../models';
import { AuthStore } from './auth-store';

export const homeRedirectGuard: CanActivateFn = () => {
  const authStore = inject(AuthStore);
  const router = inject(Router);

  if (!authStore.isAuthenticated()) {
    return router.createUrlTree(['/auth/login']);
  }
  return router.createUrlTree([authStore.role() === Role.Gestionnaire ? '/gestionnaire' : '/membre']);
};
