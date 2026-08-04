import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { ApiError, Reservation, ReservationStatut } from '../../../core/models';
import { ReservationsService } from '../../../core/services/reservations.service';
import { SallesCacheService } from '../../../core/services/salles-cache.service';
import { CurrencyTndPipe } from '../../../shared/pipes/currency-tnd.pipe';
import { DateFrPipe } from '../../../shared/pipes/date-fr.pipe';
import { DurationPipe } from '../../../shared/pipes/duration.pipe';
import { StatutLabelPipe } from '../../../shared/pipes/statut-label.pipe';
import { Badge } from '../../../shared/ui/badge/badge';
import { statutBadgeTone } from '../../../shared/ui/badge/statut-tone.util';
import { Button } from '../../../shared/ui/button/button';
import { Card } from '../../../shared/ui/card/card';
import { ConfirmDialog } from '../../../shared/ui/confirm-dialog/confirm-dialog';
import { Drawer } from '../../../shared/ui/drawer/drawer';
import { EmptyState } from '../../../shared/ui/empty-state/empty-state';
import { PageHeader } from '../../../shared/layout/page-header/page-header';
import { Skeleton } from '../../../shared/ui/skeleton/skeleton';
import { Table } from '../../../shared/ui/table/table';
import { TabItem, Tabs } from '../../../shared/ui/tabs/tabs';
import { ToastService } from '../../../shared/ui/toast/toast.service';

const TABS: TabItem[] = [
  { value: 'TOUTES', label: 'Toutes' },
  { value: ReservationStatut.EnAttente, label: 'En attente' },
  { value: ReservationStatut.Confirmee, label: 'Confirmées' },
  { value: ReservationStatut.Annulee, label: 'Annulées' },
];

@Component({
  selector: 'app-mes-reservations',
  imports: [Badge, Button, Card, ConfirmDialog, Drawer, EmptyState, PageHeader, Skeleton, Table, Tabs, CurrencyTndPipe, DateFrPipe, DurationPipe, StatutLabelPipe],
  template: `
    <app-page-header title="Mes réservations" description="Consultez et gérez vos réservations d'espaces." />

    <ui-tabs [tabs]="tabs" [(active)]="activeTab" />

    <div class="mt-6">
      @if (loading()) {
        <div class="flex flex-col gap-3">
          <ui-skeleton widthClass="w-full" heightClass="h-12" />
          <ui-skeleton widthClass="w-full" heightClass="h-12" />
          <ui-skeleton widthClass="w-full" heightClass="h-12" />
        </div>
      } @else if (filtered().length === 0) {
        <ui-card>
          <ui-empty-state icon="calendar-days" title="Aucune réservation" description="Vous n'avez pas encore de réservation dans cette catégorie." />
        </ui-card>
      } @else {
        <!-- desktop table -->
        <div class="hidden md:block">
          <ui-table>
            <thead class="bg-neutral-50 text-xs uppercase text-neutral-500">
              <tr>
                <th class="px-4 py-2.5 font-medium">Espace</th>
                <th class="px-4 py-2.5 font-medium">Date</th>
                <th class="px-4 py-2.5 font-medium">Horaire</th>
                <th class="px-4 py-2.5 font-medium">Statut</th>
                <th class="px-4 py-2.5 font-medium">Montant</th>
                <th class="px-4 py-2.5 font-medium"><span class="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody>
              @for (r of filtered(); track r.id) {
                <tr class="cursor-pointer border-t border-neutral-200 hover:bg-neutral-50" (click)="openDetail(r)">
                  <td class="px-4 py-3 font-medium text-neutral-900">{{ salleNom(r.salle_id) }}</td>
                  <td class="px-4 py-3 text-neutral-600">{{ r.date | dateFr: 'date' }}</td>
                  <td class="px-4 py-3 text-neutral-600">{{ r.heure_debut.slice(0, 5) }} – {{ r.heure_fin.slice(0, 5) }}</td>
                  <td class="px-4 py-3"><ui-badge [tone]="tone(r.statut)">{{ r.statut | statutLabel }}</ui-badge></td>
                  <td class="px-4 py-3 text-neutral-900">{{ r.acompte | currencyTnd }}</td>
                  <td class="px-4 py-3 text-right">
                    @if (peutAnnuler(r)) {
                      <ui-button size="sm" variant="danger" (click)="requestCancel(r, $event)">Annuler</ui-button>
                    }
                  </td>
                </tr>
              }
            </tbody>
          </ui-table>
        </div>

        <!-- mobile card stack -->
        <div class="flex flex-col gap-3 md:hidden">
          @for (r of filtered(); track r.id) {
            <ui-card (click)="openDetail(r)">
              <div class="flex items-start justify-between gap-3">
                <div>
                  <p class="font-medium text-neutral-900">{{ salleNom(r.salle_id) }}</p>
                  <p class="text-sm text-neutral-500">{{ r.date | dateFr: 'date' }} · {{ r.heure_debut.slice(0, 5) }} – {{ r.heure_fin.slice(0, 5) }}</p>
                </div>
                <ui-badge [tone]="tone(r.statut)">{{ r.statut | statutLabel }}</ui-badge>
              </div>
              <div class="mt-3 flex items-center justify-between">
                <span class="font-semibold text-neutral-900">{{ r.acompte | currencyTnd }}</span>
                @if (peutAnnuler(r)) {
                  <ui-button size="sm" variant="danger" (click)="requestCancel(r, $event)">Annuler</ui-button>
                }
              </div>
            </ui-card>
          }
        </div>
      }
    </div>

    <ui-drawer [open]="!!selected()" title="Détail de la réservation" (closed)="selected.set(null)">
      @if (selected(); as r) {
        <dl class="flex flex-col gap-4">
          <div>
            <dt class="text-xs uppercase text-neutral-500">Espace</dt>
            <dd class="text-sm font-medium text-neutral-900">{{ salleNom(r.salle_id) }}</dd>
          </div>
          <div>
            <dt class="text-xs uppercase text-neutral-500">Date &amp; horaire</dt>
            <dd class="text-sm font-medium text-neutral-900">{{ r.date | dateFr: 'date' }} · {{ r.heure_debut.slice(0, 5) }} – {{ r.heure_fin.slice(0, 5) }}</dd>
          </div>
          <div>
            <dt class="text-xs uppercase text-neutral-500">Durée</dt>
            <dd class="text-sm font-medium text-neutral-900">{{ r.heure_debut | duration: r.heure_fin }}</dd>
          </div>
          <div>
            <dt class="text-xs uppercase text-neutral-500">Statut</dt>
            <dd><ui-badge [tone]="tone(r.statut)">{{ r.statut | statutLabel }}</ui-badge></dd>
          </div>
          <div>
            <dt class="text-xs uppercase text-neutral-500">Montant</dt>
            <dd class="text-sm font-medium text-neutral-900">{{ r.acompte | currencyTnd }}</dd>
          </div>
          <div>
            <dt class="text-xs uppercase text-neutral-500">Créée le</dt>
            <dd class="text-sm font-medium text-neutral-900">{{ r.date_creation | dateFr: 'datetime' }}</dd>
          </div>
        </dl>
        @if (peutAnnuler(r)) {
          <div class="mt-6">
            <ui-button variant="danger" [fullWidth]="true" (click)="requestCancel(r)">Annuler la réservation</ui-button>
          </div>
        }
      }
    </ui-drawer>

    <ui-confirm-dialog
      [open]="!!toCancel()"
      title="Annuler la réservation ?"
      message="Cette action est définitive. Voulez-vous vraiment annuler cette réservation ?"
      confirmLabel="Annuler la réservation"
      [danger]="true"
      [loading]="cancelling()"
      (cancelled)="toCancel.set(null)"
      (confirmed)="confirmCancel()"
    />
  `,
})
export class MesReservations implements OnInit {
  private readonly reservationsService = inject(ReservationsService);
  private readonly sallesCache = inject(SallesCacheService);
  private readonly toastService = inject(ToastService);

  protected readonly tabs = TABS;
  protected readonly activeTab = signal('TOUTES');
  protected readonly loading = signal(true);
  protected readonly reservations = signal<Reservation[]>([]);
  protected readonly selected = signal<Reservation | null>(null);
  protected readonly toCancel = signal<Reservation | null>(null);
  protected readonly cancelling = signal(false);

  protected readonly filtered = computed(() => {
    const tab = this.activeTab();
    const all = this.reservations();
    return tab === 'TOUTES' ? all : all.filter((r) => r.statut === tab);
  });

  protected readonly tone = statutBadgeTone;

  async ngOnInit(): Promise<void> {
    await this.sallesCache.ensureLoaded();
    await this.loadReservations();
  }

  protected salleNom(salleId: string): string {
    return this.sallesCache.nom(salleId);
  }

  protected peutAnnuler(reservation: Reservation): boolean {
    return reservation.statut !== ReservationStatut.Annulee;
  }

  protected openDetail(reservation: Reservation): void {
    this.selected.set(reservation);
  }

  protected requestCancel(reservation: Reservation, event?: Event): void {
    event?.stopPropagation();
    this.toCancel.set(reservation);
  }

  protected async confirmCancel(): Promise<void> {
    const reservation = this.toCancel();
    if (!reservation) return;

    this.cancelling.set(true);
    try {
      await this.reservationsService.cancel(reservation.id);
      this.toastService.success('Réservation annulée avec succès.');
      this.toCancel.set(null);
      this.selected.set(null);
      await this.loadReservations();
    } catch (error) {
      this.toastService.error((error as ApiError).message);
    } finally {
      this.cancelling.set(false);
    }
  }

  private async loadReservations(): Promise<void> {
    this.loading.set(true);
    try {
      const reservations = await this.reservationsService.list();
      this.reservations.set(reservations);
    } finally {
      this.loading.set(false);
    }
  }
}
