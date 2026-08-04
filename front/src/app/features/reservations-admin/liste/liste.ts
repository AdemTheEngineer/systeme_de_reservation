import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { Reservation, ReservationStatut } from '../../../core/models';
import { MembresCacheService } from '../../../core/services/membres-cache.service';
import { ReservationsService } from '../../../core/services/reservations.service';
import { SallesCacheService } from '../../../core/services/salles-cache.service';
import { CurrencyTndPipe } from '../../../shared/pipes/currency-tnd.pipe';
import { DateFrPipe } from '../../../shared/pipes/date-fr.pipe';
import { DurationPipe } from '../../../shared/pipes/duration.pipe';
import { StatutLabelPipe } from '../../../shared/pipes/statut-label.pipe';
import { Badge } from '../../../shared/ui/badge/badge';
import { statutBadgeTone } from '../../../shared/ui/badge/statut-tone.util';
import { Card } from '../../../shared/ui/card/card';
import { DatePicker } from '../../../shared/ui/date-picker/date-picker';
import { Drawer } from '../../../shared/ui/drawer/drawer';
import { EmptyState } from '../../../shared/ui/empty-state/empty-state';
import { Input } from '../../../shared/ui/input/input';
import { PageHeader } from '../../../shared/layout/page-header/page-header';
import { Select, SelectOption } from '../../../shared/ui/select/select';
import { Skeleton } from '../../../shared/ui/skeleton/skeleton';
import { Table } from '../../../shared/ui/table/table';

const STATUT_OPTIONS: SelectOption[] = [
  { value: ReservationStatut.EnAttente, label: 'En attente' },
  { value: ReservationStatut.Confirmee, label: 'Confirmée' },
  { value: ReservationStatut.Annulee, label: 'Annulée' },
];

@Component({
  selector: 'app-reservations-admin-liste',
  imports: [ReactiveFormsModule, Badge, Card, DatePicker, Drawer, EmptyState, Input, PageHeader, Select, Skeleton, Table, CurrencyTndPipe, DateFrPipe, DurationPipe, StatutLabelPipe],
  template: `
    <app-page-header title="Gestion des réservations" description="Consultez l'ensemble des réservations effectuées par les membres." />

    <ui-card>
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <ui-select label="Statut" placeholder="Tous les statuts" [options]="statutOptions" [formControl]="statutControl" />
        <ui-select label="Espace" placeholder="Tous les espaces" [options]="salleOptions()" [formControl]="salleControl" />
        <ui-input label="Membre (e-mail)" placeholder="Rechercher…" [formControl]="membreControl" />
        <ui-date-picker label="Du" kind="date" [formControl]="debutControl" />
        <ui-date-picker label="Au" kind="date" [formControl]="finControl" />
      </div>
    </ui-card>

    <div class="mt-6">
      @if (loading()) {
        <div class="flex flex-col gap-2">
          <ui-skeleton widthClass="w-full" heightClass="h-10" />
          <ui-skeleton widthClass="w-full" heightClass="h-10" />
          <ui-skeleton widthClass="w-full" heightClass="h-10" />
        </div>
      } @else if (filtered().length === 0) {
        <ui-card>
          <ui-empty-state icon="calendar-days" title="Aucune réservation" description="Aucune réservation ne correspond à ces critères." />
        </ui-card>
      } @else {
        <p class="mb-3 text-sm text-neutral-500">{{ filtered().length }} réservation(s)</p>

        <div class="hidden md:block">
          <ui-table>
            <thead class="bg-neutral-50 text-xs uppercase text-neutral-500">
              <tr>
                <th class="px-4 py-2.5 font-medium">Espace</th>
                <th class="px-4 py-2.5 font-medium">Membre</th>
                <th class="px-4 py-2.5 font-medium">Date</th>
                <th class="px-4 py-2.5 font-medium">Statut</th>
                <th class="px-4 py-2.5 font-medium">Montant</th>
              </tr>
            </thead>
            <tbody>
              @for (r of filtered(); track r.id) {
                <tr class="cursor-pointer border-t border-neutral-200 hover:bg-neutral-50" (click)="selected.set(r)">
                  <td class="px-4 py-3 font-medium text-neutral-900">{{ salleNom(r.salle_id) }}</td>
                  <td class="px-4 py-3 text-neutral-600">{{ membreEmail(r.membre_id) }}</td>
                  <td class="px-4 py-3 text-neutral-600">{{ r.date | dateFr: 'date' }}</td>
                  <td class="px-4 py-3"><ui-badge [tone]="tone(r.statut)">{{ r.statut | statutLabel }}</ui-badge></td>
                  <td class="px-4 py-3 text-neutral-900">{{ r.acompte | currencyTnd }}</td>
                </tr>
              }
            </tbody>
          </ui-table>
        </div>

        <div class="flex flex-col gap-3 md:hidden">
          @for (r of filtered(); track r.id) {
            <ui-card (click)="selected.set(r)">
              <div class="flex items-start justify-between gap-3">
                <div>
                  <p class="font-medium text-neutral-900">{{ salleNom(r.salle_id) }}</p>
                  <p class="text-sm text-neutral-500">{{ membreEmail(r.membre_id) }}</p>
                  <p class="text-sm text-neutral-500">{{ r.date | dateFr: 'date' }}</p>
                </div>
                <ui-badge [tone]="tone(r.statut)">{{ r.statut | statutLabel }}</ui-badge>
              </div>
              <p class="mt-2 font-semibold text-neutral-900">{{ r.acompte | currencyTnd }}</p>
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
            <dt class="text-xs uppercase text-neutral-500">Membre</dt>
            <dd class="text-sm font-medium text-neutral-900">{{ membreEmail(r.membre_id) }}</dd>
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
      }
    </ui-drawer>
  `,
})
export class ReservationsAdminListe implements OnInit {
  private readonly reservationsService = inject(ReservationsService);
  private readonly sallesCache = inject(SallesCacheService);
  private readonly membresCache = inject(MembresCacheService);

  protected readonly statutOptions = STATUT_OPTIONS;
  protected readonly statutControl = new FormControl('', { nonNullable: true });
  protected readonly salleControl = new FormControl('', { nonNullable: true });
  protected readonly membreControl = new FormControl('', { nonNullable: true });
  protected readonly debutControl = new FormControl('', { nonNullable: true });
  protected readonly finControl = new FormControl('', { nonNullable: true });

  protected readonly loading = signal(true);
  protected readonly reservations = signal<Reservation[]>([]);
  protected readonly selected = signal<Reservation | null>(null);
  protected readonly tone = statutBadgeTone;

  protected readonly salleOptions = computed<SelectOption[]>(() =>
    this.sallesCache.salles().map((s) => ({ value: s.id_espace, label: s.nom })),
  );

  protected readonly filtered = computed(() => {
    const statut = this.statutControl.value;
    const salle = this.salleControl.value;
    const membreQuery = this.membreQuery();
    const debut = this.debutControl.value;
    const fin = this.finControl.value;

    return this.reservations().filter((r) => {
      if (statut && r.statut !== statut) return false;
      if (salle && r.salle_id !== salle) return false;
      if (debut && r.date < debut) return false;
      if (fin && r.date > fin) return false;
      if (membreQuery && !this.membresCache.email(r.membre_id).toLowerCase().includes(membreQuery)) return false;
      return true;
    });
  });

  private readonly membreQuery = signal('');

  async ngOnInit(): Promise<void> {
    this.membreControl.valueChanges.subscribe((value) => this.membreQuery.set(value.toLowerCase()));
    await this.sallesCache.ensureLoaded();
    await this.loadReservations();
  }

  protected salleNom(salleId: string): string {
    return this.sallesCache.nom(salleId);
  }

  protected membreEmail(membreId: string): string {
    return this.membresCache.email(membreId);
  }

  private async loadReservations(): Promise<void> {
    this.loading.set(true);
    try {
      const [reservations] = await Promise.all([this.reservationsService.list(), this.membresCache.ensureLoaded()]);
      this.reservations.set(reservations);
    } finally {
      this.loading.set(false);
    }
  }
}
