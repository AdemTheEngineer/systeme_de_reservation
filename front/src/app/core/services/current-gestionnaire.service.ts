import { Injectable, inject } from '@angular/core';
import { AuthStore } from '../auth/auth-store';
import { GestionnairesService } from './gestionnaires.service';

/**
 * `GET /auth/me/` only returns the `Utilisateur` PK, never the `Gestionnaire`
 * UUID — but creating a `Salle` requires `id_gestionnaire` in the payload
 * (writable field, no server-side default). `GestionnaireViewSet` is
 * readable by any gestionnaire, so the current gestionnaire's own UUID is
 * resolved by searching gestionnaires by their own (unique) email instead of
 * inventing an endpoint. See project memory `project-backend-contract`.
 */
@Injectable({ providedIn: 'root' })
export class CurrentGestionnaireService {
  private readonly gestionnairesService = inject(GestionnairesService);
  private readonly authStore = inject(AuthStore);

  private idPromise: Promise<string> | null = null;

  async getId(): Promise<string> {
    if (!this.idPromise) {
      this.idPromise = this.resolveId();
    }
    return this.idPromise;
  }

  private async resolveId(): Promise<string> {
    const email = this.authStore.currentUser()?.email;
    if (!email) {
      throw new Error('Utilisateur non authentifié.');
    }
    const page = await this.gestionnairesService.list({ search: email });
    const match = page.results.find((gestionnaire) => gestionnaire.email === email);
    if (!match) {
      throw new Error('Impossible de résoudre le compte gestionnaire actuel.');
    }
    return match.id;
  }
}
