import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { Role } from '../models';
import { AuthStore } from './auth-store';

export function roleGuard(allowedRoles: Role[]): CanActivateFn {
  return () => {
    const authStore = inject(AuthStore);
    const router = inject(Router);

    if (!authStore.isAuthenticated()) {
      return router.createUrlTree(['/auth/login']);
    }
    const role = authStore.role();
    if (role && allowedRoles.includes(role)) {
      return true;
    }
    return router.createUrlTree(['/403']);
  };
}
