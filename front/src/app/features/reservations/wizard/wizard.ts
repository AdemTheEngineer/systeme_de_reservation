import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ApiError, Creneau, MoyenPaiement, Paiement, Reservation, Salle } from '../../../core/models';
import { CreneauxService } from '../../../core/services/creneaux.service';
import { PaiementsService } from '../../../core/services/paiements.service';
import { ReservationsService } from '../../../core/services/reservations.service';
import { SallesService } from '../../../core/services/salles.service';
import { calculerMontant } from '../../../core/utils/duration.util';
import { CurrencyTndPipe } from '../../../shared/pipes/currency-tnd.pipe';
import { DateFrPipe } from '../../../shared/pipes/date-fr.pipe';
import { DurationPipe } from '../../../shared/pipes/duration.pipe';
import { Badge } from '../../../shared/ui/badge/badge';
import { Button } from '../../../shared/ui/button/button';
import { Card } from '../../../shared/ui/card/card';
import { EmptyState } from '../../../shared/ui/empty-state/empty-state';
import { Icon } from '../../../shared/ui/icon/icon';
import { Select, SelectOption } from '../../../shared/ui/select/select';
import { Skeleton } from '../../../shared/ui/skeleton/skeleton';

type WizardStep = 'creneau' | 'recap' | 'paiement' | 'confirmation';

const STEPS: { key: WizardStep; label: string }[] = [
  { key: 'creneau', label: 'Créneau' },
  { key: 'recap', label: 'Récapitulatif' },
  { key: 'paiement', label: 'Paiement' },
];

const MOYEN_OPTIONS: SelectOption[] = [
  { value: MoyenPaiement.Carte, label: 'Carte bancaire' },
  { value: MoyenPaiement.Virement, label: 'Virement' },
  { value: MoyenPaiement.Especes, label: 'Espèces' },
];

const CRENEAU_INDISPONIBLE_MESSAGE = "Ce créneau n'est plus disponible pour cet espace.";

@Component({
  selector: 'app-reservation-wizard',
  imports: [ReactiveFormsModule, RouterLink, Badge, Button, Card, EmptyState, Icon, Select, Skeleton, CurrencyTndPipe, DateFrPipe, DurationPipe],
  template: `
    @if (loading()) {
      <ui-skeleton widthClass="w-full" heightClass="h-64" rounded="xl" />
    } @else if (!creneau() || !salle()) {
      <ui-card>
        <ui-empty-state icon="calendar-days" title="Aucun créneau sélectionné" description="Choisissez un espace et un créneau depuis le catalogue pour démarrer une réservation.">
          <a routerLink="/membre/espaces">
            <ui-button variant="primary">Voir le catalogue</ui-button>
          </a>
        </ui-empty-state>
      </ui-card>
    } @else if (salle(); as s) {
      @if (creneau(); as c) {
        @if (step() !== 'confirmation') {
          <nav class="mb-8 flex items-center justify-center gap-4" aria-label="Étapes de réservation">
            @for (item of steps; track item.key; let i = $index) {
              <div class="flex items-center gap-2">
                <span
                  class="flex size-7 items-center justify-center rounded-full text-xs font-semibold"
                  [class]="stepIndex(item.key) <= stepIndex(step()) ? 'bg-brand-blue text-white' : 'bg-neutral-100 text-neutral-400'"
                >
                  {{ i + 1 }}
                </span>
                <span class="text-sm font-medium" [class]="stepIndex(item.key) <= stepIndex(step()) ? 'text-neutral-900' : 'text-neutral-400'">
                  {{ item.label }}
                </span>
              </div>
              @if (i < steps.length - 1) {
                <span class="h-px w-8 bg-neutral-200"></span>
              }
            }
          </nav>
        }

        @switch (step()) {
          @case ('creneau') {
            <ui-card>
              <h2 class="mb-4 text-lg font-semibold text-neutral-900">Créneau sélectionné</h2>
              <div class="flex flex-col gap-3 rounded-lg border border-neutral-200 p-4">
                <div class="flex items-center justify-between">
                  <span class="text-base font-semibold text-neutral-900">{{ s.nom }}</span>
                  <ui-badge tone="neutral">{{ s.tarif_horaire | currencyTnd }}/heure</ui-badge>
                </div>
                <p class="text-sm text-neutral-500">{{ s.localisation }}</p>
                <div class="flex items-center gap-2 text-sm text-neutral-700">
                  <ui-icon name="calendar-days" [size]="16" />
                  {{ c.date | dateFr: 'date' }} · {{ c.heure_debut.slice(0, 5) }} – {{ c.heure_fin.slice(0, 5) }}
                  ({{ c.heure_debut | duration: c.heure_fin }})
                </div>
              </div>
              <div class="mt-6 flex justify-end gap-3">
                <a [routerLink]="['/membre/espaces', s.id_espace]">
                  <ui-button variant="secondary">Changer de créneau</ui-button>
                </a>
                <ui-button variant="primary" (click)="step.set('recap')">Continuer</ui-button>
              </div>
            </ui-card>
          }
          @case ('recap') {
            <ui-card>
              <h2 class="mb-4 text-lg font-semibold text-neutral-900">Récapitulatif</h2>
              <dl class="grid grid-cols-2 gap-4">
                <div class="col-span-2">
                  <dt class="text-xs uppercase text-neutral-500">Espace</dt>
                  <dd class="text-sm font-medium text-neutral-900">{{ s.nom }}</dd>
                </div>
                <div>
                  <dt class="text-xs uppercase text-neutral-500">Date</dt>
                  <dd class="text-sm font-medium text-neutral-900">{{ c.date | dateFr: 'date' }}</dd>
                </div>
                <div>
                  <dt class="text-xs uppercase text-neutral-500">Horaire</dt>
                  <dd class="text-sm font-medium text-neutral-900">{{ c.heure_debut.slice(0, 5) }} – {{ c.heure_fin.slice(0, 5) }}</dd>
                </div>
                <div>
                  <dt class="text-xs uppercase text-neutral-500">Durée</dt>
                  <dd class="text-sm font-medium text-neutral-900">{{ c.heure_debut | duration: c.heure_fin }}</dd>
                </div>
                <div>
                  <dt class="text-xs uppercase text-neutral-500">Montant estimé</dt>
                  <dd class="text-base font-semibold text-neutral-900">{{ montantEstime() | currencyTnd }}</dd>
                </div>
              </dl>

              @if (errorMessage()) {
                <p class="mt-4 text-sm text-rose-600" role="alert">{{ errorMessage() }}</p>
              }

              <div class="mt-6 flex justify-end gap-3">
                <ui-button variant="secondary" (click)="step.set('creneau')">Retour</ui-button>
                <ui-button variant="primary" [loading]="submittingReservation()" (click)="confirmerReservation()">
                  Confirmer la réservation
                </ui-button>
              </div>
            </ui-card>
          }
          @case ('paiement') {
            @if (reservation(); as r) {
              <ui-card>
                <h2 class="mb-4 text-lg font-semibold text-neutral-900">Paiement</h2>
                <p class="mb-4 text-sm text-neutral-500">
                  Réservation créée, en attente de paiement. Montant à régler :
                  <span class="font-semibold text-neutral-900">{{ r.acompte | currencyTnd }}</span>
                </p>
                <ui-select label="Moyen de paiement" [options]="moyenOptions" [formControl]="moyenControl" />

                @if (errorMessage()) {
                  <p class="mt-4 text-sm text-rose-600" role="alert">{{ errorMessage() }}</p>
                }

                <div class="mt-6 flex justify-end gap-3">
                  <ui-button variant="primary" [loading]="submittingPaiement()" (click)="payer()">Payer maintenant</ui-button>
                </div>
              </ui-card>
            }
          }
          @case ('confirmation') {
            <ui-card>
              <div class="flex flex-col items-center gap-4 py-6 text-center">
                <span class="flex size-14 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">
                  <ui-icon name="circle-check" [size]="32" />
                </span>
                <div>
                  <h2 class="text-lg font-semibold text-neutral-900">Réservation confirmée</h2>
                  <p class="mt-1 text-sm text-neutral-500">
                    Votre réservation pour {{ s.nom }} le {{ c.date | dateFr: 'date' }} est confirmée.
                  </p>
                </div>
                <a routerLink="/membre/reservations">
                  <ui-button variant="primary">Voir mes réservations</ui-button>
                </a>
              </div>
            </ui-card>
          }
        }
      }
    }
  `,
})
export class ReservationWizard implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly sallesService = inject(SallesService);
  private readonly creneauxService = inject(CreneauxService);
  private readonly reservationsService = inject(ReservationsService);
  private readonly paiementsService = inject(PaiementsService);

  protected readonly steps = STEPS;
  protected readonly moyenOptions = MOYEN_OPTIONS;
  protected readonly moyenControl = new FormControl<MoyenPaiement>(MoyenPaiement.Carte, { nonNullable: true });

  protected readonly loading = signal(true);
  protected readonly salle = signal<Salle | null>(null);
  protected readonly creneau = signal<Creneau | null>(null);
  protected readonly reservation = signal<Reservation | null>(null);

  protected readonly step = signal<WizardStep>('creneau');
  protected readonly submittingReservation = signal(false);
  protected readonly submittingPaiement = signal(false);
  protected readonly errorMessage = signal('');

  protected readonly montantEstime = computed(() => {
    const s = this.salle();
    const c = this.creneau();
    if (!s || !c) return 0;
    return calculerMontant(s.tarif_horaire, c.heure_debut, c.heure_fin);
  });

  protected stepIndex(step: WizardStep): number {
    return STEPS.findIndex((s) => s.key === step);
  }

  async ngOnInit(): Promise<void> {
    const creneauId = this.route.snapshot.queryParamMap.get('creneau');
    if (!creneauId) {
      this.loading.set(false);
      return;
    }

    try {
      const creneau = await this.creneauxService.get(creneauId);
      const salle = await this.sallesService.get(creneau.espace);
      this.creneau.set(creneau);
      this.salle.set(salle);
    } catch {
      this.creneau.set(null);
      this.salle.set(null);
    } finally {
      this.loading.set(false);
    }
  }

  protected async confirmerReservation(): Promise<void> {
    const creneau = this.creneau();
    if (!creneau) return;

    this.submittingReservation.set(true);
    this.errorMessage.set('');
    try {
      const reservation = await this.reservationsService.create({ creneau: creneau.id });
      this.reservation.set(reservation);
      this.step.set('paiement');
    } catch (error) {
      const apiError = error as ApiError;
      this.errorMessage.set(apiError.status === 409 ? CRENEAU_INDISPONIBLE_MESSAGE : apiError.message);
    } finally {
      this.submittingReservation.set(false);
    }
  }

  protected async payer(): Promise<void> {
    const reservation = this.reservation();
    if (!reservation) return;

    this.submittingPaiement.set(true);
    this.errorMessage.set('');
    try {
      const paiement: Paiement = await this.paiementsService.create({
        reservation: reservation.id,
        montant: reservation.acompte,
        devise: reservation.devise,
        moyen: this.moyenControl.value,
      });
      if (paiement.statut === 'REFUSE') {
        this.errorMessage.set('Le paiement a été refusé. Veuillez réessayer avec un autre moyen de paiement.');
        return;
      }
      const updated = await this.reservationsService.get(reservation.id);
      this.reservation.set(updated);
      this.step.set('confirmation');
    } catch (error) {
      this.errorMessage.set((error as ApiError).message);
    } finally {
      this.submittingPaiement.set(false);
    }
  }
}
