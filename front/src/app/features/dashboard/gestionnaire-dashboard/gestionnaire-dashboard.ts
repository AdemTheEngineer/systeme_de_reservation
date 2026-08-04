import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { DashboardKPI, Reservation, ReservationStatut, Salle } from '../../../core/models';
import { KpisService } from '../../../core/services/kpis.service';
import { ReservationsService } from '../../../core/services/reservations.service';
import { SallesService } from '../../../core/services/salles.service';
import { dernierJourDuMoisIso, premierJourDuMoisIso } from '../../../core/utils/date.util';
import { CurrencyTndPipe } from '../../../shared/pipes/currency-tnd.pipe';
import { Card } from '../../../shared/ui/card/card';
import { BarChart, BarChartDatum } from '../../../shared/ui/charts/bar-chart';
import { DonutChart, DonutDatum } from '../../../shared/ui/charts/donut-chart';
import { DatePicker } from '../../../shared/ui/date-picker/date-picker';
import { EmptyState } from '../../../shared/ui/empty-state/empty-state';
import { PageHeader } from '../../../shared/layout/page-header/page-header';
import { Skeleton } from '../../../shared/ui/skeleton/skeleton';
import { StatCard } from '../../../shared/ui/stat-card/stat-card';

@Component({
  selector: 'app-gestionnaire-dashboard',
  imports: [ReactiveFormsModule, BarChart, Card, DatePicker, DonutChart, EmptyState, PageHeader, Skeleton, StatCard, CurrencyTndPipe],
  template: `
    <app-page-header title="Tableau de bord" description="Indicateurs de pilotage des espaces de coworking.">
      <div class="flex items-end gap-3">
        <ui-date-picker label="Du" kind="date" [formControl]="debutControl" />
        <ui-date-picker label="Au" kind="date" [formControl]="finControl" />
      </div>
    </app-page-header>

    @if (loading()) {
      <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        @for (i of [1, 2, 3, 4]; track i) {
          <ui-skeleton widthClass="w-full" heightClass="h-24" rounded="xl" />
        }
      </div>
    } @else {
      <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <ui-stat-card label="Revenus (période)" [value]="(revenu()?.somme_acomptes | currencyTnd) ?? '0,00 TND'" icon="wallet" />
        <ui-stat-card label="Réservations (période)" [value]="(revenu()?.nombre_reservations ?? 0).toString()" icon="calendar-days" />
        <ui-stat-card label="Taux d'occupation moyen" [value]="tauxMoyen() + '%'" icon="building-2" />
        <ui-stat-card label="Espaces actifs" [value]="espacesActifs() + ' / ' + salles().length" icon="layout-grid" />
      </div>

      <div class="mt-6 grid gap-6 lg:grid-cols-2">
        <ui-card>
          <h2 class="mb-4 text-base font-semibold text-neutral-900">Taux d'occupation par salle</h2>
          @if (occupationBars().length === 0) {
            <ui-empty-state icon="building-2" title="Aucune donnée" description="Aucune donnée d'occupation pour cette période." />
          } @else {
            <ui-bar-chart [data]="occupationBars()" />
          }
        </ui-card>

        <ui-card>
          <h2 class="mb-4 text-base font-semibold text-neutral-900">Réservations par statut</h2>
          @if (statutDonut().length === 0) {
            <ui-empty-state icon="calendar-days" title="Aucune donnée" description="Aucune réservation sur cette période." />
          } @else {
            <ui-donut-chart [data]="statutDonut()" />
          }
        </ui-card>
      </div>
    }
  `,
})
export class GestionnaireDashboard implements OnInit {
  private readonly kpisService = inject(KpisService);
  private readonly sallesService = inject(SallesService);
  private readonly reservationsService = inject(ReservationsService);

  protected readonly debutControl = new FormControl(premierJourDuMoisIso(), { nonNullable: true });
  protected readonly finControl = new FormControl(dernierJourDuMoisIso(), { nonNullable: true });

  protected readonly loading = signal(true);
  protected readonly kpi = signal<DashboardKPI | null>(null);
  protected readonly salles = signal<Salle[]>([]);
  protected readonly reservations = signal<Reservation[]>([]);

  protected readonly revenu = computed(() => this.kpi()?.revenu ?? null);

  protected readonly tauxMoyen = computed(() => {
    const occupation = this.kpi()?.occupation ?? [];
    if (occupation.length === 0) return 0;
    const total = occupation.reduce((sum, o) => sum + Number(o.taux), 0);
    return Math.round((total / occupation.length) * 100);
  });

  protected readonly espacesActifs = computed(() => this.salles().filter((s) => s.disponible).length);

  protected readonly occupationBars = computed<BarChartDatum[]>(() =>
    (this.kpi()?.occupation ?? []).map((o) => ({
      label: o.nom,
      value: Number(o.taux) * 100,
      valueLabel: `${Math.round(Number(o.taux) * 100)}%`,
    })),
  );

  protected readonly statutDonut = computed<DonutDatum[]>(() => {
    const reservations = this.reservations();
    if (reservations.length === 0) return [];
    const counts = {
      [ReservationStatut.Confirmee]: 0,
      [ReservationStatut.EnAttente]: 0,
      [ReservationStatut.Annulee]: 0,
    };
    for (const r of reservations) {
      counts[r.statut]++;
    }
    return [
      { label: 'Confirmées', value: counts[ReservationStatut.Confirmee], strokeClass: 'stroke-emerald-500' },
      { label: 'En attente', value: counts[ReservationStatut.EnAttente], strokeClass: 'stroke-amber-500' },
      { label: 'Annulées', value: counts[ReservationStatut.Annulee], strokeClass: 'stroke-rose-500' },
    ].filter((segment) => segment.value > 0);
  });

  ngOnInit(): void {
    this.debutControl.valueChanges.subscribe(() => void this.loadKpis());
    this.finControl.valueChanges.subscribe(() => void this.loadKpis());
    void this.loadAll();
  }

  private async loadAll(): Promise<void> {
    this.loading.set(true);
    try {
      const [sallesPage, reservations] = await Promise.all([
        this.sallesService.list({ page: 1 }),
        this.reservationsService.list(),
      ]);
      this.salles.set(sallesPage.results);
      this.reservations.set(reservations);
      await this.loadKpis();
    } finally {
      this.loading.set(false);
    }
  }

  private async loadKpis(): Promise<void> {
    const debut = this.debutControl.value;
    const fin = this.finControl.value;
    if (!debut || !fin) return;
    const kpi = await this.kpisService.dashboard({ debut, fin });
    this.kpi.set(kpi);
  }
}
