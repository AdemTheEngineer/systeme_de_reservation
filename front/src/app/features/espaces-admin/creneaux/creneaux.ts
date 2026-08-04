import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ApiError, Creneau, Salle } from '../../../core/models';
import { CreneauxService } from '../../../core/services/creneaux.service';
import { SallesService } from '../../../core/services/salles.service';
import { DateFrPipe } from '../../../shared/pipes/date-fr.pipe';
import { StatutLabelPipe } from '../../../shared/pipes/statut-label.pipe';
import { Badge } from '../../../shared/ui/badge/badge';
import { statutBadgeTone } from '../../../shared/ui/badge/statut-tone.util';
import { Button } from '../../../shared/ui/button/button';
import { Card } from '../../../shared/ui/card/card';
import { ConfirmDialog } from '../../../shared/ui/confirm-dialog/confirm-dialog';
import { DatePicker } from '../../../shared/ui/date-picker/date-picker';
import { EmptyState } from '../../../shared/ui/empty-state/empty-state';
import { Icon } from '../../../shared/ui/icon/icon';
import { PageHeader } from '../../../shared/layout/page-header/page-header';
import { Skeleton } from '../../../shared/ui/skeleton/skeleton';
import { Table } from '../../../shared/ui/table/table';
import { ToastService } from '../../../shared/ui/toast/toast.service';

interface CreneauFormGroup {
  date: FormControl<string>;
  heure_debut: FormControl<string>;
  heure_fin: FormControl<string>;
}

@Component({
  selector: 'app-espace-creneaux',
  imports: [ReactiveFormsModule, RouterLink, Badge, Button, Card, ConfirmDialog, DatePicker, EmptyState, Icon, PageHeader, Skeleton, Table, DateFrPipe, StatutLabelPipe],
  template: `
    <a routerLink="/gestionnaire/espaces" class="mb-4 inline-flex items-center gap-1.5 text-sm text-neutral-500 hover:text-neutral-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue rounded-lg">
      <ui-icon name="arrow-left" [size]="16" />
      Retour aux espaces
    </a>

    <app-page-header [title]="pageTitle()" description="Ajoutez ou retirez des créneaux réservables pour cet espace." />

    <div class="grid gap-6 lg:grid-cols-[20rem_1fr]">
      <ui-card>
        <h2 class="mb-4 text-base font-semibold text-neutral-900">Ajouter un créneau</h2>
        <form [formGroup]="form" (ngSubmit)="submit()" class="flex flex-col gap-4">
          <ui-date-picker label="Date" kind="date" [required]="true" [formControl]="form.controls.date" />
          <ui-date-picker label="Heure de début" kind="time" [required]="true" [formControl]="form.controls.heure_debut" />
          <ui-date-picker label="Heure de fin" kind="time" [required]="true" [formControl]="form.controls.heure_fin" />
          @if (formError()) {
            <p class="text-sm text-rose-600" role="alert">{{ formError() }}</p>
          }
          <ui-button type="submit" variant="primary" [fullWidth]="true" [loading]="submitting()" [disabled]="form.invalid">
            Ajouter le créneau
          </ui-button>
        </form>
      </ui-card>

      <ui-card [padded]="false">
        @if (loading()) {
          <div class="flex flex-col gap-2 p-4">
            <ui-skeleton widthClass="w-full" heightClass="h-10" />
            <ui-skeleton widthClass="w-full" heightClass="h-10" />
          </div>
        } @else if (creneaux().length === 0) {
          <ui-empty-state icon="calendar-days" title="Aucun créneau" description="Ajoutez un créneau pour rendre cet espace réservable." />
        } @else {
          <ui-table>
            <thead class="bg-neutral-50 text-xs uppercase text-neutral-500">
              <tr>
                <th class="px-4 py-2.5 font-medium">Date</th>
                <th class="px-4 py-2.5 font-medium">Horaire</th>
                <th class="px-4 py-2.5 font-medium">Statut</th>
                <th class="px-4 py-2.5 font-medium"><span class="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody>
              @for (creneau of creneaux(); track creneau.id) {
                <tr class="border-t border-neutral-200 hover:bg-neutral-50">
                  <td class="px-4 py-3 text-neutral-900">{{ creneau.date | dateFr: 'date' }}</td>
                  <td class="px-4 py-3 text-neutral-600">{{ creneau.heure_debut.slice(0, 5) }} – {{ creneau.heure_fin.slice(0, 5) }}</td>
                  <td class="px-4 py-3"><ui-badge [tone]="tone(creneau.statut)">{{ creneau.statut | statutLabel }}</ui-badge></td>
                  <td class="px-4 py-3 text-right">
                    @if (creneau.statut === 'DISPONIBLE') {
                      <ui-button size="sm" variant="danger" (click)="toDelete.set(creneau)">Supprimer</ui-button>
                    }
                  </td>
                </tr>
              }
            </tbody>
          </ui-table>
        }
      </ui-card>
    </div>

    <ui-confirm-dialog
      [open]="!!toDelete()"
      title="Supprimer ce créneau ?"
      message="Ce créneau ne sera plus proposé à la réservation."
      confirmLabel="Supprimer"
      [danger]="true"
      [loading]="deleting()"
      (cancelled)="toDelete.set(null)"
      (confirmed)="confirmDelete()"
    />
  `,
})
export class EspaceCreneaux implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly sallesService = inject(SallesService);
  private readonly creneauxService = inject(CreneauxService);
  private readonly toastService = inject(ToastService);

  protected readonly tone = statutBadgeTone;
  protected readonly loading = signal(true);
  protected readonly salle = signal<Salle | null>(null);
  protected readonly pageTitle = computed(() => {
    const salle = this.salle();
    return salle ? `Créneaux — ${salle.nom}` : 'Créneaux';
  });
  protected readonly creneaux = signal<Creneau[]>([]);
  protected readonly submitting = signal(false);
  protected readonly formError = signal('');
  protected readonly toDelete = signal<Creneau | null>(null);
  protected readonly deleting = signal(false);

  protected readonly form = new FormGroup<CreneauFormGroup>({
    date: new FormControl('', { nonNullable: true, validators: [Validators.required] }),
    heure_debut: new FormControl('', { nonNullable: true, validators: [Validators.required] }),
    heure_fin: new FormControl('', { nonNullable: true, validators: [Validators.required] }),
  });

  private salleId = '';

  async ngOnInit(): Promise<void> {
    this.salleId = this.route.snapshot.paramMap.get('id') ?? '';
    if (!this.salleId) {
      this.loading.set(false);
      return;
    }
    try {
      this.salle.set(await this.sallesService.get(this.salleId));
    } catch {
      this.salle.set(null);
    }
    await this.loadCreneaux();
  }

  protected async submit(): Promise<void> {
    if (this.form.invalid || !this.salleId) {
      this.form.markAllAsTouched();
      return;
    }
    this.submitting.set(true);
    this.formError.set('');
    try {
      const value = this.form.getRawValue();
      await this.creneauxService.create({ espace: this.salleId, ...value });
      this.toastService.success('Créneau ajouté avec succès.');
      this.form.reset({ date: '', heure_debut: '', heure_fin: '' });
      await this.loadCreneaux();
    } catch (error) {
      this.formError.set((error as ApiError).message);
    } finally {
      this.submitting.set(false);
    }
  }

  protected async confirmDelete(): Promise<void> {
    const creneau = this.toDelete();
    if (!creneau) return;
    this.deleting.set(true);
    try {
      await this.creneauxService.remove(creneau.id);
      this.toastService.success('Créneau supprimé.');
      this.toDelete.set(null);
      await this.loadCreneaux();
    } catch (error) {
      this.toastService.error((error as ApiError).message);
    } finally {
      this.deleting.set(false);
    }
  }

  private async loadCreneaux(): Promise<void> {
    this.loading.set(true);
    try {
      const page = await this.creneauxService.list({ espace: this.salleId, ordering: 'date' });
      this.creneaux.set(page.results);
    } finally {
      this.loading.set(false);
    }
  }
}
