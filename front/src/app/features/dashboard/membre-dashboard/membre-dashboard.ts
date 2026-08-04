import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Reservation, ReservationStatut } from '../../../core/models';
import { ReservationsService } from '../../../core/services/reservations.service';
import { SallesCacheService } from '../../../core/services/salles-cache.service';
import { aujourdHuiIso } from '../../../core/utils/date.util';
import { dureeEnHeures } from '../../../core/utils/duration.util';
import { CurrencyTndPipe } from '../../../shared/pipes/currency-tnd.pipe';
import { DateFrPipe } from '../../../shared/pipes/date-fr.pipe';
import { StatutLabelPipe } from '../../../shared/pipes/statut-label.pipe';
import { Badge } from '../../../shared/ui/badge/badge';
import { statutBadgeTone } from '../../../shared/ui/badge/statut-tone.util';
import { Card } from '../../../shared/ui/card/card';
import { EmptyState } from '../../../shared/ui/empty-state/empty-state';
import { PageHeader } from '../../../shared/layout/page-header/page-header';
import { Skeleton } from '../../../shared/ui/skeleton/skeleton';
import { StatCard } from '../../../shared/ui/stat-card/stat-card';

const AUJOURD_HUI = aujourdHuiIso();
const DEBUT_MOIS = AUJOURD_HUI.slice(0, 7);

@Component({
  selector: 'app-membre-dashboard',
  imports: [RouterLink, Badge, Card, EmptyState, PageHeader, Skeleton, StatCard, CurrencyTndPipe, DateFrPipe, StatutLabelPipe],
  template: `
    <app-page-header title="Tableau de bord" description="Vue d'ensemble de vos réservations." />

    @if (loading()) {
      <div class="grid gap-4 sm:grid-cols-3">
        <ui-skeleton widthClass="w-full" heightClass="h-24" rounded="xl" />
        <ui-skeleton widthClass="w-full" heightClass="h-24" rounded="xl" />
        <ui-skeleton widthClass="w-full" heightClass="h-24" rounded="xl" />
      </div>
    } @else {
      <div class="grid gap-4 sm:grid-cols-3">
        <ui-stat-card label="Réservations à venir" [value]="reservationsAVenir().length.toString()" icon="calendar-days" />
        <ui-stat-card label="Heures réservées ce mois" [value]="heuresCeMois() + 'h'" icon="clock" />
        <ui-stat-card label="Montant dépensé" [value]="(montantDepense() | currencyTnd) ?? ''" icon="wallet" />
      </div>

      <div class="mt-6 grid gap-6 lg:grid-cols-2">
        <ui-card>
          <h2 class="mb-4 text-base font-semibold text-neutral-900">Prochaine réservation</h2>
          @if (prochaine(); as p) {
            <div class="flex flex-col gap-2">
              <div class="flex items-center justify-between">
                <span class="font-medium text-neutral-900">{{ salleNom(p.salle_id) }}</span>
                <ui-badge [tone]="tone(p.statut)">{{ p.statut | statutLabel }}</ui-badge>
              </div>
              <p class="text-sm text-neutral-500">{{ p.date | dateFr: 'date' }} · {{ p.heure_debut.slice(0, 5) }} – {{ p.heure_fin.slice(0, 5) }}</p>
              <p class="text-sm font-medium text-neutral-900">{{ p.acompte | currencyTnd }}</p>
            </div>
          } @else {
            <ui-empty-state icon="calendar-days" title="Aucune réservation à venir" description="Réservez un espace depuis le catalogue.">
              <a routerLink="/membre/espaces" class="text-sm font-medium text-brand-blue hover:underline">Voir le catalogue</a>
            </ui-empty-state>
          }
        </ui-card>

        <ui-card>
          <h2 class="mb-4 text-base font-semibold text-neutral-900">Activité récente</h2>
          @if (recentes().length === 0) {
            <p class="text-sm text-neutral-500">Aucune activité récente.</p>
          } @else {
            <ul class="flex flex-col gap-3">
              @for (r of recentes(); track r.id) {
                <li class="flex items-center justify-between gap-3 border-b border-neutral-100 pb-3 last:border-0 last:pb-0">
                  <div>
                    <p class="text-sm font-medium text-neutral-900">{{ salleNom(r.salle_id) }}</p>
                    <p class="text-xs text-neutral-500">{{ r.date_creation | dateFr: 'datetime' }}</p>
                  </div>
                  <ui-badge [tone]="tone(r.statut)">{{ r.statut | statutLabel }}</ui-badge>
                </li>
              }
            </ul>
          }
        </ui-card>
      </div>
    }
  `,
})
export class MembreDashboard implements OnInit {
  private readonly reservationsService = inject(ReservationsService);
  private readonly sallesCache = inject(SallesCacheService);

  protected readonly loading = signal(true);
  protected readonly reservations = signal<Reservation[]>([]);
  protected readonly tone = statutBadgeTone;

  protected readonly reservationsAVenir = computed(() =>
    this.reservations().filter((r) => r.date >= AUJOURD_HUI && r.statut !== ReservationStatut.Annulee),
  );

  protected readonly heuresCeMois = computed(() =>
    this.reservations()
      .filter((r) => r.date.startsWith(DEBUT_MOIS) && r.statut !== ReservationStatut.Annulee)
      .reduce((total, r) => total + dureeEnHeures(r.heure_debut, r.heure_fin), 0),
  );

  protected readonly montantDepense = computed(() =>
    this.reservations()
      .filter((r) => r.statut === ReservationStatut.Confirmee)
      .reduce((total, r) => total + Number(r.acompte), 0),
  );

  protected readonly prochaine = computed(() => {
    const upcoming = this.reservationsAVenir();
    return upcoming.length > 0 ? upcoming[0] : null;
  });

  protected readonly recentes = computed(() =>
    [...this.reservations()]
      .sort((a, b) => b.date_creation.localeCompare(a.date_creation))
      .slice(0, 5),
  );

  async ngOnInit(): Promise<void> {
    await this.sallesCache.ensureLoaded();
    try {
      const reservations = await this.reservationsService.list();
      this.reservations.set(reservations.sort((a, b) => a.date.localeCompare(b.date)));
    } finally {
      this.loading.set(false);
    }
  }

  protected salleNom(salleId: string): string {
    return this.sallesCache.nom(salleId);
  }
}
