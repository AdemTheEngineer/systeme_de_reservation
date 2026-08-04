import { Component, OnInit, inject, signal } from '@angular/core';
import { AuthStore } from '../../../core/auth/auth-store';
import { Utilisateur } from '../../../core/models';
import { AuthService } from '../../../core/services/auth.service';
import { Card } from '../../../shared/ui/card/card';
import { Skeleton } from '../../../shared/ui/skeleton/skeleton';
import { StatutLabelPipe } from '../../../shared/pipes/statut-label.pipe';
import { PageHeader } from '../../../shared/layout/page-header/page-header';

@Component({
  selector: 'app-profile',
  imports: [Card, Skeleton, StatutLabelPipe, PageHeader],
  template: `
    <app-page-header title="Mon profil" description="Informations liées à votre compte." />

    <ui-card>
      @if (user(); as u) {
        <dl class="grid gap-4 sm:grid-cols-2">
          <div class="flex flex-col gap-1">
            <dt class="text-xs font-medium uppercase text-neutral-500">Nom complet</dt>
            <dd class="text-sm text-neutral-900">{{ u.first_name || u.last_name ? u.first_name + ' ' + u.last_name : '—' }}</dd>
          </div>
          <div class="flex flex-col gap-1">
            <dt class="text-xs font-medium uppercase text-neutral-500">Rôle</dt>
            <dd class="text-sm text-neutral-900">{{ u.role | statutLabel }}</dd>
          </div>
          <div class="flex flex-col gap-1">
            <dt class="text-xs font-medium uppercase text-neutral-500">Adresse e-mail</dt>
            <dd class="text-sm text-neutral-900">{{ u.email }}</dd>
          </div>
          <div class="flex flex-col gap-1">
            <dt class="text-xs font-medium uppercase text-neutral-500">Téléphone</dt>
            <dd class="text-sm text-neutral-900">{{ u.telephone || '—' }}</dd>
          </div>
        </dl>
        <p class="mt-6 rounded-lg bg-neutral-50 p-3 text-xs text-neutral-500">
          La modification du profil et du mot de passe n'est pas encore proposée par l'API : seul un gestionnaire peut
          mettre à jour une fiche membre ou gestionnaire, et l'identifiant nécessaire à cette mise à jour n'est pas
          exposé par <code>/auth/me/</code>. Contactez un gestionnaire pour toute correction.
        </p>
      } @else {
        <div class="flex flex-col gap-3">
          <ui-skeleton widthClass="w-1/3" heightClass="h-4" />
          <ui-skeleton widthClass="w-1/2" heightClass="h-4" />
          <ui-skeleton widthClass="w-2/3" heightClass="h-4" />
        </div>
      }
    </ui-card>
  `,
})
export class Profile implements OnInit {
  private readonly authService = inject(AuthService);
  private readonly authStore = inject(AuthStore);

  protected readonly user = signal<Utilisateur | null>(null);

  ngOnInit(): void {
    const cachedUser = this.authStore.currentUser();
    if (cachedUser) {
      this.user.set(cachedUser);
      return;
    }
    void this.authService.loadCurrentUser().then((user) => this.user.set(user));
  }
}
