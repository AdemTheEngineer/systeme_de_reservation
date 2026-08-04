import { Component, OnInit, inject, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ApiError, Salle, SalleRequest, TypeEspace } from '../../../core/models';
import { CurrentGestionnaireService } from '../../../core/services/current-gestionnaire.service';
import { SallesService } from '../../../core/services/salles.service';
import { CurrencyTndPipe } from '../../../shared/pipes/currency-tnd.pipe';
import { StatutLabelPipe } from '../../../shared/pipes/statut-label.pipe';
import { Badge } from '../../../shared/ui/badge/badge';
import { Button } from '../../../shared/ui/button/button';
import { Card } from '../../../shared/ui/card/card';
import { EmptyState } from '../../../shared/ui/empty-state/empty-state';
import { Icon } from '../../../shared/ui/icon/icon';
import { Input } from '../../../shared/ui/input/input';
import { PageHeader } from '../../../shared/layout/page-header/page-header';
import { Modal } from '../../../shared/ui/modal/modal';
import { Select, SelectOption } from '../../../shared/ui/select/select';
import { Skeleton } from '../../../shared/ui/skeleton/skeleton';
import { Table } from '../../../shared/ui/table/table';
import { Textarea } from '../../../shared/ui/textarea/textarea';
import { Toggle } from '../../../shared/ui/toggle/toggle';
import { ToastService } from '../../../shared/ui/toast/toast.service';

const TYPE_OPTIONS: SelectOption[] = [
  { value: TypeEspace.OpenSpace, label: 'Open space' },
  { value: TypeEspace.BureauPrive, label: 'Bureau privé' },
  { value: TypeEspace.SalleReunion, label: 'Salle de réunion' },
];

interface SalleFormGroup {
  nom: FormControl<string>;
  type_espace: FormControl<string>;
  capacite: FormControl<string>;
  tarif_horaire: FormControl<string>;
  localisation: FormControl<string>;
  equipements: FormControl<string>;
  disponible: FormControl<boolean>;
}

@Component({
  selector: 'app-espaces-admin-liste',
  imports: [ReactiveFormsModule, RouterLink, Badge, Button, Card, EmptyState, Icon, Input, Modal, PageHeader, Select, Skeleton, Table, Textarea, Toggle, CurrencyTndPipe, StatutLabelPipe],
  template: `
    <app-page-header title="Gestion des espaces" description="Créez et administrez le catalogue d'espaces de coworking.">
      <ui-button variant="primary" (click)="openCreate()">
        <ui-icon name="plus" [size]="16" />
        Nouvel espace
      </ui-button>
    </app-page-header>

    <ui-card [padded]="false">
      <div class="p-4">
        <ui-input placeholder="Rechercher un espace…" [formControl]="searchControl" />
      </div>

      @if (loading()) {
        <div class="flex flex-col gap-2 p-4 pt-0">
          <ui-skeleton widthClass="w-full" heightClass="h-10" />
          <ui-skeleton widthClass="w-full" heightClass="h-10" />
          <ui-skeleton widthClass="w-full" heightClass="h-10" />
        </div>
      } @else if (salles().length === 0) {
        <ui-empty-state icon="building-2" title="Aucun espace" description="Créez votre premier espace de coworking." />
      } @else {
        <div class="hidden md:block">
          <ui-table>
            <thead class="bg-neutral-50 text-xs uppercase text-neutral-500">
              <tr>
                <th class="px-4 py-2.5 font-medium">Nom</th>
                <th class="px-4 py-2.5 font-medium">Type</th>
                <th class="px-4 py-2.5 font-medium">Localisation</th>
                <th class="px-4 py-2.5 font-medium">Capacité</th>
                <th class="px-4 py-2.5 font-medium">Tarif</th>
                <th class="px-4 py-2.5 font-medium">Disponible</th>
                <th class="px-4 py-2.5 font-medium"><span class="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody>
              @for (salle of salles(); track salle.id_espace) {
                <tr class="border-t border-neutral-200 hover:bg-neutral-50">
                  <td class="px-4 py-3 font-medium text-neutral-900">{{ salle.nom }}</td>
                  <td class="px-4 py-3"><ui-badge tone="neutral">{{ salle.type_espace | statutLabel }}</ui-badge></td>
                  <td class="px-4 py-3 text-neutral-600">{{ salle.localisation || '—' }}</td>
                  <td class="px-4 py-3 text-neutral-600">{{ salle.capacite }}</td>
                  <td class="px-4 py-3 text-neutral-900">{{ salle.tarif_horaire | currencyTnd }}</td>
                  <td class="px-4 py-3">
                    <ui-toggle [label]="'Disponibilité de ' + salle.nom" [checked]="salle.disponible" (toggled)="toggleDisponible(salle, $event)" />
                  </td>
                  <td class="px-4 py-3 text-right">
                    <div class="flex justify-end gap-2">
                      <a [routerLink]="['/gestionnaire/espaces', salle.id_espace, 'creneaux']" aria-label="Gérer les créneaux" class="flex size-8 items-center justify-center rounded-lg text-neutral-500 hover:bg-neutral-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue">
                        <ui-icon name="calendar-days" [size]="16" />
                      </a>
                      <button type="button" aria-label="Modifier" (click)="openEdit(salle)" class="flex size-8 items-center justify-center rounded-lg text-neutral-500 hover:bg-neutral-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue">
                        <ui-icon name="pencil" [size]="16" />
                      </button>
                    </div>
                  </td>
                </tr>
              }
            </tbody>
          </ui-table>
        </div>

        <div class="flex flex-col gap-3 p-4 pt-0 md:hidden">
          @for (salle of salles(); track salle.id_espace) {
            <div class="rounded-lg border border-neutral-200 p-3">
              <div class="flex items-start justify-between gap-2">
                <div>
                  <p class="font-medium text-neutral-900">{{ salle.nom }}</p>
                  <p class="text-sm text-neutral-500">{{ salle.localisation || '—' }}</p>
                </div>
                <ui-badge tone="neutral">{{ salle.type_espace | statutLabel }}</ui-badge>
              </div>
              <div class="mt-2 flex items-center justify-between text-sm text-neutral-600">
                <span>{{ salle.capacite }} personnes · {{ salle.tarif_horaire | currencyTnd }}</span>
                <ui-toggle [label]="'Disponibilité de ' + salle.nom" [checked]="salle.disponible" (toggled)="toggleDisponible(salle, $event)" />
              </div>
              <div class="mt-3 flex justify-end gap-2 border-t border-neutral-100 pt-3">
                <a [routerLink]="['/gestionnaire/espaces', salle.id_espace, 'creneaux']" aria-label="Gérer les créneaux" class="flex size-8 items-center justify-center rounded-lg text-neutral-500 hover:bg-neutral-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue">
                  <ui-icon name="calendar-days" [size]="16" />
                </a>
                <button type="button" aria-label="Modifier" (click)="openEdit(salle)" class="flex size-8 items-center justify-center rounded-lg text-neutral-500 hover:bg-neutral-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue">
                  <ui-icon name="pencil" [size]="16" />
                </button>
              </div>
            </div>
          }
        </div>
      }
    </ui-card>

    <ui-modal [open]="modalOpen()" [title]="editingSalle() ? 'Modifier l\\'espace' : 'Nouvel espace'" (closed)="closeModal()">
      <form [formGroup]="form" (ngSubmit)="submit()" class="flex flex-col gap-4">
        <ui-input label="Nom" [required]="true" [formControl]="form.controls.nom" />
        <ui-select label="Type" [options]="typeOptions" [formControl]="form.controls.type_espace" />
        <div class="grid grid-cols-2 gap-3">
          <ui-input label="Capacité" type="number" [required]="true" [formControl]="form.controls.capacite" />
          <ui-input label="Tarif horaire (TND)" type="number" [required]="true" [formControl]="form.controls.tarif_horaire" />
        </div>
        <ui-input label="Localisation" placeholder="Ex. Les Berges du Lac 2, Tunis" [formControl]="form.controls.localisation" />
        <ui-textarea label="Équipements (séparés par des virgules)" placeholder="Wifi dédié, Vidéoprojecteur, Parking" [formControl]="form.controls.equipements" />
        <div class="flex items-center gap-3">
          <ui-toggle label="Espace disponible" [formControl]="form.controls.disponible" />
          <span class="text-sm text-neutral-600">Espace disponible à la réservation</span>
        </div>

        @if (formError()) {
          <p class="text-sm text-rose-600" role="alert">{{ formError() }}</p>
        }

        <div class="mt-2 flex justify-end gap-3">
          <ui-button type="button" variant="secondary" (click)="closeModal()">Annuler</ui-button>
          <ui-button type="submit" variant="primary" [loading]="submitting()" [disabled]="form.invalid">Enregistrer</ui-button>
        </div>
      </form>
    </ui-modal>
  `,
})
export class EspacesAdminListe implements OnInit {
  private readonly sallesService = inject(SallesService);
  private readonly currentGestionnaire = inject(CurrentGestionnaireService);
  private readonly toastService = inject(ToastService);

  protected readonly typeOptions = TYPE_OPTIONS;
  protected readonly searchControl = new FormControl('', { nonNullable: true });

  protected readonly loading = signal(true);
  protected readonly salles = signal<Salle[]>([]);
  protected readonly modalOpen = signal(false);
  protected readonly editingSalle = signal<Salle | null>(null);
  protected readonly submitting = signal(false);
  protected readonly formError = signal('');

  protected readonly form = new FormGroup<SalleFormGroup>({
    nom: new FormControl('', { nonNullable: true, validators: [Validators.required] }),
    type_espace: new FormControl<string>(TypeEspace.OpenSpace, { nonNullable: true }),
    capacite: new FormControl('', { nonNullable: true, validators: [Validators.required, Validators.min(1)] }),
    tarif_horaire: new FormControl('', { nonNullable: true, validators: [Validators.required, Validators.min(0)] }),
    localisation: new FormControl('', { nonNullable: true }),
    equipements: new FormControl('', { nonNullable: true }),
    disponible: new FormControl(true, { nonNullable: true }),
  });

  async ngOnInit(): Promise<void> {
    this.searchControl.valueChanges.subscribe(() => void this.loadSalles());
    await this.loadSalles();
  }

  protected openCreate(): void {
    this.editingSalle.set(null);
    this.form.reset({
      nom: '',
      type_espace: TypeEspace.OpenSpace,
      capacite: '',
      tarif_horaire: '',
      localisation: '',
      equipements: '',
      disponible: true,
    });
    this.formError.set('');
    this.modalOpen.set(true);
  }

  protected openEdit(salle: Salle): void {
    this.editingSalle.set(salle);
    this.form.reset({
      nom: salle.nom,
      type_espace: salle.type_espace,
      capacite: String(salle.capacite),
      tarif_horaire: salle.tarif_horaire,
      localisation: salle.localisation ?? '',
      equipements: salle.equipements,
      disponible: salle.disponible,
    });
    this.formError.set('');
    this.modalOpen.set(true);
  }

  protected closeModal(): void {
    this.modalOpen.set(false);
  }

  protected async submit(): Promise<void> {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.submitting.set(true);
    this.formError.set('');
    try {
      const value = this.form.getRawValue();
      const existing = this.editingSalle();
      const payload: SalleRequest = {
        nom: value.nom,
        type_espace: value.type_espace as TypeEspace,
        capacite: Number(value.capacite),
        tarif_horaire: value.tarif_horaire,
        localisation: value.localisation || null,
        equipements: value.equipements,
        disponible: value.disponible,
        id_gestionnaire: existing?.id_gestionnaire ?? (await this.currentGestionnaire.getId()),
      };

      if (existing) {
        await this.sallesService.update(existing.id_espace, payload);
        this.toastService.success('Espace mis à jour avec succès.');
      } else {
        await this.sallesService.create(payload);
        this.toastService.success('Espace créé avec succès.');
      }
      this.modalOpen.set(false);
      await this.loadSalles();
    } catch (error) {
      this.formError.set((error as ApiError).message);
    } finally {
      this.submitting.set(false);
    }
  }

  protected async toggleDisponible(salle: Salle, disponible: boolean): Promise<void> {
    try {
      await this.sallesService.patch(salle.id_espace, { disponible });
      this.salles.update((salles) => salles.map((s) => (s.id_espace === salle.id_espace ? { ...s, disponible } : s)));
      this.toastService.success(disponible ? 'Espace activé.' : 'Espace désactivé.');
    } catch (error) {
      this.toastService.error((error as ApiError).message);
    }
  }

  private async loadSalles(): Promise<void> {
    this.loading.set(true);
    try {
      const page = await this.sallesService.list({ search: this.searchControl.value || undefined });
      this.salles.set(page.results);
    } finally {
      this.loading.set(false);
    }
  }
}
