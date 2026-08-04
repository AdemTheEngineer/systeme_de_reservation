import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Creneau, Salle } from '../../../core/models';
import { CreneauxService } from '../../../core/services/creneaux.service';
import { SallesService } from '../../../core/services/salles.service';
import { CurrencyTndPipe } from '../../../shared/pipes/currency-tnd.pipe';
import { DateFrPipe } from '../../../shared/pipes/date-fr.pipe';
import { StatutLabelPipe } from '../../../shared/pipes/statut-label.pipe';
import { Badge } from '../../../shared/ui/badge/badge';
import { Button } from '../../../shared/ui/button/button';
import { Card } from '../../../shared/ui/card/card';
import { EmptyState } from '../../../shared/ui/empty-state/empty-state';
import { Icon } from '../../../shared/ui/icon/icon';
import { Skeleton } from '../../../shared/ui/skeleton/skeleton';

@Component({
  selector: 'app-espace-detail',
  imports: [RouterLink, Badge, Button, Card, EmptyState, Icon, Skeleton, CurrencyTndPipe, DateFrPipe, StatutLabelPipe],
  template: `
    @if (loading()) {
      <div class="flex flex-col gap-4">
        <ui-skeleton widthClass="w-1/3" heightClass="h-8" />
        <ui-skeleton widthClass="w-full" heightClass="h-48" rounded="xl" />
      </div>
    } @else if (salle(); as s) {
      <a routerLink="/membre/espaces" class="mb-4 inline-flex items-center gap-1.5 text-sm text-neutral-500 hover:text-neutral-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue rounded-lg">
        <ui-icon name="arrow-left" [size]="16" />
        Retour au catalogue
      </a>

      <div class="grid gap-6 lg:grid-cols-[1fr_20rem]">
        <div class="flex flex-col gap-6">
          <div class="flex aspect-video items-center justify-center rounded-xl border border-neutral-200 bg-neutral-100 text-neutral-400">
            <ui-icon [name]="typeIcon()" [size]="48" />
          </div>

          <ui-card>
            <div class="mb-4 flex items-start justify-between gap-4">
              <div>
                <h1 class="text-xl font-semibold text-neutral-900">{{ s.nom }}</h1>
                <p class="mt-1 flex items-center gap-1.5 text-sm text-neutral-500">
                  <ui-icon name="map-pin" [size]="14" />
                  {{ s.localisation || 'Localisation non renseignée' }}
                </p>
              </div>
              <ui-badge tone="neutral">{{ s.type_espace | statutLabel }}</ui-badge>
            </div>

            <dl class="grid grid-cols-2 gap-4 border-t border-neutral-200 pt-4 sm:grid-cols-3">
              <div>
                <dt class="text-xs uppercase text-neutral-500">Capacité</dt>
                <dd class="text-sm font-medium text-neutral-900">{{ s.capacite }} personnes</dd>
              </div>
              <div>
                <dt class="text-xs uppercase text-neutral-500">Tarif horaire</dt>
                <dd class="text-sm font-medium text-neutral-900">{{ s.tarif_horaire | currencyTnd }}</dd>
              </div>
              <div>
                <dt class="text-xs uppercase text-neutral-500">Statut</dt>
                <dd class="text-sm font-medium text-neutral-900">{{ s.disponible ? 'Disponible' : 'Indisponible' }}</dd>
              </div>
            </dl>

            @if (equipements().length > 0) {
              <div class="mt-4 border-t border-neutral-200 pt-4">
                <p class="mb-2 text-xs uppercase text-neutral-500">Équipements</p>
                <div class="flex flex-wrap gap-2">
                  @for (item of equipements(); track item) {
                    <ui-badge tone="info">{{ item }}</ui-badge>
                  }
                </div>
              </div>
            }
          </ui-card>
        </div>

        <ui-card>
          <h2 class="mb-4 text-base font-semibold text-neutral-900">Créneaux disponibles</h2>
          @if (creneauxLoading()) {
            <div class="flex flex-col gap-2">
              <ui-skeleton widthClass="w-full" heightClass="h-10" />
              <ui-skeleton widthClass="w-full" heightClass="h-10" />
            </div>
          } @else if (creneaux().length === 0) {
            <ui-empty-state icon="calendar-days" title="Aucun créneau disponible" description="Revenez plus tard, de nouveaux créneaux sont ajoutés régulièrement." />
          } @else {
            <ul class="flex flex-col gap-2">
              @for (creneau of creneaux(); track creneau.id) {
                <li class="flex items-center justify-between gap-3 rounded-lg border border-neutral-200 p-3">
                  <div class="flex flex-col">
                    <span class="text-sm font-medium text-neutral-900">{{ creneau.date | dateFr: 'date' }}</span>
                    <span class="text-xs text-neutral-500">{{ creneau.heure_debut.slice(0, 5) }} – {{ creneau.heure_fin.slice(0, 5) }}</span>
                  </div>
                  <a [routerLink]="['/membre/reservations/nouvelle']" [queryParams]="{ creneau: creneau.id }">
                    <ui-button size="sm" variant="primary">Réserver</ui-button>
                  </a>
                </li>
              }
            </ul>
          }
        </ui-card>
      </div>
    } @else {
      <ui-empty-state icon="building-2" title="Espace introuvable" description="Cet espace n'existe pas ou a été retiré du catalogue." />
    }
  `,
})
export class EspaceDetail implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly sallesService = inject(SallesService);
  private readonly creneauxService = inject(CreneauxService);

  protected readonly loading = signal(true);
  protected readonly salle = signal<Salle | null>(null);
  protected readonly creneauxLoading = signal(true);
  protected readonly creneaux = signal<Creneau[]>([]);

  protected readonly equipements = computed(() => {
    const raw = this.salle()?.equipements ?? '';
    return raw
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
  });

  protected readonly typeIcon = computed(() => {
    const type = this.salle()?.type_espace;
    if (type === 'BUREAU_PRIVE') return 'door-closed';
    if (type === 'SALLE_REUNION') return 'users';
    return 'building-2';
  });

  async ngOnInit(): Promise<void> {
    const id = this.route.snapshot.paramMap.get('id');
    if (!id) {
      await this.router.navigateByUrl('/membre/espaces');
      return;
    }

    try {
      const salle = await this.sallesService.get(id);
      this.salle.set(salle);
    } catch {
      this.salle.set(null);
    } finally {
      this.loading.set(false);
    }

    try {
      const page = await this.creneauxService.list({ espace: id, statut: 'DISPONIBLE', ordering: 'date' });
      this.creneaux.set(page.results);
    } finally {
      this.creneauxLoading.set(false);
    }
  }
}
