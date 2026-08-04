import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Paiement, PaiementStatut } from '../../../core/models';
import { PaiementsService } from '../../../core/services/paiements.service';
import { CurrencyTndPipe } from '../../../shared/pipes/currency-tnd.pipe';
import { DateFrPipe } from '../../../shared/pipes/date-fr.pipe';
import { StatutLabelPipe } from '../../../shared/pipes/statut-label.pipe';
import { Badge } from '../../../shared/ui/badge/badge';
import { statutBadgeTone } from '../../../shared/ui/badge/statut-tone.util';
import { Card } from '../../../shared/ui/card/card';
import { EmptyState } from '../../../shared/ui/empty-state/empty-state';
import { PageHeader } from '../../../shared/layout/page-header/page-header';
import { Pagination } from '../../../shared/ui/pagination/pagination';
import { Select, SelectOption } from '../../../shared/ui/select/select';
import { Skeleton } from '../../../shared/ui/skeleton/skeleton';
import { StatCard } from '../../../shared/ui/stat-card/stat-card';
import { Table } from '../../../shared/ui/table/table';

const STATUT_OPTIONS: SelectOption[] = [
  { value: PaiementStatut.EnAttente, label: 'En attente' },
  { value: PaiementStatut.Accepte, label: 'Accepté' },
  { value: PaiementStatut.Refuse, label: 'Refusé' },
];

const PAGE_SIZE = 20;

@Component({
  selector: 'app-paiements-admin-liste',
  imports: [ReactiveFormsModule, Badge, Card, EmptyState, PageHeader, Pagination, Select, Skeleton, StatCard, Table, CurrencyTndPipe, DateFrPipe, StatutLabelPipe],
  template: `
    <app-page-header title="Paiements" description="Suivi des paiements initiés par les membres." />

    <div class="grid gap-4 sm:grid-cols-3">
      <ui-stat-card label="Acceptés (page)" [value]="countByStatut('ACCEPTE').toString()" icon="circle-check" />
      <ui-stat-card label="En attente (page)" [value]="countByStatut('EN_ATTENTE').toString()" icon="clock" />
      <ui-stat-card label="Montant accepté (page)" [value]="(totalAccepte() | currencyTnd) ?? '0,00 TND'" icon="wallet" />
    </div>

    <div class="mt-6">
      <ui-card>
        <ui-select label="Statut" placeholder="Tous les statuts" [options]="statutOptions" [formControl]="statutControl" />
      </ui-card>
    </div>

    <div class="mt-6">
      @if (loading()) {
        <div class="flex flex-col gap-2">
          <ui-skeleton widthClass="w-full" heightClass="h-10" />
          <ui-skeleton widthClass="w-full" heightClass="h-10" />
        </div>
      } @else if (paiements().length === 0) {
        <ui-card>
          <ui-empty-state icon="receipt-text" title="Aucun paiement" description="Aucun paiement ne correspond à ces critères." />
        </ui-card>
      } @else {
        <div class="hidden md:block">
          <ui-table>
            <thead class="bg-neutral-50 text-xs uppercase text-neutral-500">
              <tr>
                <th class="px-4 py-2.5 font-medium">Référence</th>
                <th class="px-4 py-2.5 font-medium">Réservation</th>
                <th class="px-4 py-2.5 font-medium">Moyen</th>
                <th class="px-4 py-2.5 font-medium">Statut</th>
                <th class="px-4 py-2.5 font-medium">Montant</th>
                <th class="px-4 py-2.5 font-medium">Date</th>
              </tr>
            </thead>
            <tbody>
              @for (p of paiements(); track p.id) {
                <tr class="border-t border-neutral-200 hover:bg-neutral-50">
                  <td class="px-4 py-3 font-mono text-xs text-neutral-500">{{ p.id.slice(0, 8) }}</td>
                  <td class="px-4 py-3 font-mono text-xs text-neutral-500">{{ p.reservation.slice(0, 8) }}</td>
                  <td class="px-4 py-3 text-neutral-600">{{ p.moyen | statutLabel }}</td>
                  <td class="px-4 py-3"><ui-badge [tone]="tone(p.statut)">{{ p.statut | statutLabel }}</ui-badge></td>
                  <td class="px-4 py-3 text-neutral-900">{{ p.montant | currencyTnd }}</td>
                  <td class="px-4 py-3 text-neutral-600">{{ p.date_paiement | dateFr: 'datetime' }}</td>
                </tr>
              }
            </tbody>
          </ui-table>
        </div>

        <div class="flex flex-col gap-3 md:hidden">
          @for (p of paiements(); track p.id) {
            <ui-card>
              <div class="flex items-start justify-between gap-3">
                <div>
                  <p class="font-mono text-xs text-neutral-500">{{ p.id.slice(0, 8) }}</p>
                  <p class="text-sm text-neutral-600">{{ p.moyen | statutLabel }} · {{ p.date_paiement | dateFr: 'datetime' }}</p>
                </div>
                <ui-badge [tone]="tone(p.statut)">{{ p.statut | statutLabel }}</ui-badge>
              </div>
              <p class="mt-2 font-semibold text-neutral-900">{{ p.montant | currencyTnd }}</p>
            </ui-card>
          }
        </div>

        <div class="mt-4">
          <ui-pagination [count]="count()" [pageSize]="pageSize" [page]="page()" (pageChange)="onPageChange($event)" />
        </div>
      }
    </div>
  `,
})
export class PaiementsAdminListe implements OnInit {
  private readonly paiementsService = inject(PaiementsService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  protected readonly statutOptions = STATUT_OPTIONS;
  protected readonly statutControl = new FormControl('', { nonNullable: true });
  protected readonly pageSize = PAGE_SIZE;

  protected readonly loading = signal(true);
  protected readonly paiements = signal<Paiement[]>([]);
  protected readonly count = signal(0);
  protected readonly page = signal(1);
  protected readonly tone = statutBadgeTone;

  protected readonly totalAccepte = computed(() =>
    this.paiements()
      .filter((p) => p.statut === 'ACCEPTE')
      .reduce((sum, p) => sum + Number(p.montant), 0),
  );

  protected countByStatut(statut: string): number {
    return this.paiements().filter((p) => p.statut === statut).length;
  }

  async ngOnInit(): Promise<void> {
    const initial = this.route.snapshot.queryParamMap;
    this.statutControl.setValue(initial.get('statut') ?? '', { emitEvent: false });
    this.page.set(Number(initial.get('page') ?? 1));

    this.statutControl.valueChanges.subscribe(() => {
      this.page.set(1);
      this.syncAndLoad();
    });

    await this.loadPaiements();
  }

  protected onPageChange(page: number): void {
    this.page.set(page);
    this.syncAndLoad();
  }

  private syncAndLoad(): void {
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { statut: this.statutControl.value || null, page: this.page() },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
    void this.loadPaiements();
  }

  protected async loadPaiements(): Promise<void> {
    this.loading.set(true);
    try {
      const result = await this.paiementsService.list({
        statut: (this.statutControl.value || undefined) as PaiementStatut | undefined,
        page: this.page(),
      });
      this.paiements.set(result.results);
      this.count.set(result.count);
    } finally {
      this.loading.set(false);
    }
  }
}
