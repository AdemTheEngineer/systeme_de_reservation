import { Component, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { debounceTime } from 'rxjs';
import { Salle, TypeEspace } from '../../../core/models';
import { SallesService } from '../../../core/services/salles.service';
import { CurrencyTndPipe } from '../../../shared/pipes/currency-tnd.pipe';
import { StatutLabelPipe } from '../../../shared/pipes/statut-label.pipe';
import { Badge } from '../../../shared/ui/badge/badge';
import { Card } from '../../../shared/ui/card/card';
import { EmptyState } from '../../../shared/ui/empty-state/empty-state';
import { Icon } from '../../../shared/ui/icon/icon';
import { Input } from '../../../shared/ui/input/input';
import { PageHeader } from '../../../shared/layout/page-header/page-header';
import { Select, SelectOption } from '../../../shared/ui/select/select';
import { Skeleton } from '../../../shared/ui/skeleton/skeleton';

const TYPE_OPTIONS: SelectOption[] = [
  { value: TypeEspace.OpenSpace, label: 'Open space' },
  { value: TypeEspace.BureauPrive, label: 'Bureau privé' },
  { value: TypeEspace.SalleReunion, label: 'Salle de réunion' },
];

@Component({
  selector: 'app-catalogue',
  imports: [ReactiveFormsModule, RouterLink, Badge, Card, EmptyState, Icon, Input, PageHeader, Select, Skeleton, CurrencyTndPipe, StatutLabelPipe],
  template: `
    <app-page-header title="Catalogue des espaces" description="Trouvez l'espace de coworking qui correspond à votre besoin." />

    <div class="grid gap-6 lg:grid-cols-[16rem_1fr]">
      <aside class="flex flex-col gap-4">
        <ui-card>
          <div class="flex flex-col gap-4">
            <ui-input label="Recherche" placeholder="Nom de l'espace…" [formControl]="searchControl" />
            <ui-select label="Type" placeholder="Tous les types" [options]="typeOptions" [formControl]="typeControl" />
            <ui-select label="Ville" placeholder="Toutes les villes" [options]="villeOptions()" [formControl]="villeControl" />
            <ui-input label="Capacité minimum" type="number" placeholder="Ex. 4" [formControl]="capaciteMinControl" />
            <div class="grid grid-cols-2 gap-3">
              <ui-input label="Tarif min (TND)" type="number" [formControl]="tarifMinControl" />
              <ui-input label="Tarif max (TND)" type="number" [formControl]="tarifMaxControl" />
            </div>
            <button
              type="button"
              (click)="resetFilters()"
              class="text-sm font-medium text-neutral-500 hover:text-neutral-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue rounded-lg self-start"
            >
              Réinitialiser les filtres
            </button>
          </div>
        </ui-card>
      </aside>

      <div class="flex flex-col gap-4">
        @if (loading()) {
          <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            @for (i of [1, 2, 3, 4, 5, 6]; track i) {
              <ui-card>
                <div class="flex flex-col gap-3">
                  <ui-skeleton widthClass="w-2/3" heightClass="h-5" />
                  <ui-skeleton widthClass="w-1/2" heightClass="h-4" />
                  <ui-skeleton widthClass="w-full" heightClass="h-4" />
                  <ui-skeleton widthClass="w-1/3" heightClass="h-8" />
                </div>
              </ui-card>
            }
          </div>
        } @else if (filteredSalles().length === 0) {
          <ui-card>
            <ui-empty-state icon="building-2" title="Aucun espace trouvé" description="Essayez d'élargir vos critères de recherche." />
          </ui-card>
        } @else {
          <p class="text-sm text-neutral-500">{{ filteredSalles().length }} espace{{ filteredSalles().length > 1 ? 's' : '' }} trouvé{{ filteredSalles().length > 1 ? 's' : '' }}</p>
          <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            @for (salle of filteredSalles(); track salle.id_espace) {
              <ui-card [padded]="false">
                <a [routerLink]="['/membre/espaces', salle.id_espace]" class="flex flex-col gap-3 p-4 sm:p-6 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue rounded-xl">
                  <div class="flex items-start justify-between gap-2">
                    <h3 class="text-base font-semibold text-neutral-900">{{ salle.nom }}</h3>
                    <ui-badge tone="neutral">{{ salle.type_espace | statutLabel }}</ui-badge>
                  </div>
                  <div class="flex items-center gap-1.5 text-sm text-neutral-500">
                    <ui-icon name="map-pin" [size]="14" />
                    {{ salle.localisation || 'Localisation non renseignée' }}
                  </div>
                  <div class="flex items-center gap-1.5 text-sm text-neutral-500">
                    <ui-icon name="users" [size]="14" />
                    {{ salle.capacite }} personnes
                  </div>
                  <div class="mt-1 flex items-center justify-between">
                    <span class="text-lg font-semibold text-neutral-900">{{ salle.tarif_horaire | currencyTnd }}<span class="text-sm font-normal text-neutral-500">/heure</span></span>
                    @if (!salle.disponible) {
                      <ui-badge tone="danger">Indisponible</ui-badge>
                    }
                  </div>
                </a>
              </ui-card>
            }
          </div>
        }
      </div>
    </div>
  `,
})
export class Catalogue {
  private readonly sallesService = inject(SallesService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  protected readonly typeOptions = TYPE_OPTIONS;
  protected readonly searchControl = new FormControl('', { nonNullable: true });
  protected readonly typeControl = new FormControl('', { nonNullable: true });
  protected readonly villeControl = new FormControl('', { nonNullable: true });
  protected readonly capaciteMinControl = new FormControl('', { nonNullable: true });
  protected readonly tarifMinControl = new FormControl('', { nonNullable: true });
  protected readonly tarifMaxControl = new FormControl('', { nonNullable: true });

  private readonly allSalles = signal<Salle[]>([]);
  protected readonly loading = signal(true);

  private readonly search = signal('');
  private readonly type = signal('');
  private readonly ville = signal('');
  private readonly capaciteMin = signal('');
  private readonly tarifMin = signal('');
  private readonly tarifMax = signal('');

  protected readonly villeOptions = computed<SelectOption[]>(() => {
    const villes = new Set<string>();
    for (const salle of this.allSalles()) {
      const ville = salle.localisation?.split(',').pop()?.trim();
      if (ville) {
        villes.add(ville);
      }
    }
    return [...villes].sort().map((ville) => ({ value: ville, label: ville }));
  });

  protected readonly filteredSalles = computed(() => {
    const type = this.type();
    const ville = this.ville();
    const capaciteMin = Number(this.capaciteMin());
    const tarifMin = Number(this.tarifMin());
    const tarifMax = Number(this.tarifMax());

    return this.allSalles().filter((salle) => {
      if (type && salle.type_espace !== type) return false;
      if (ville && !salle.localisation?.trim().endsWith(ville)) return false;
      if (this.capaciteMin() && salle.capacite < capaciteMin) return false;
      if (this.tarifMin() && Number(salle.tarif_horaire) < tarifMin) return false;
      if (this.tarifMax() && Number(salle.tarif_horaire) > tarifMax) return false;
      return true;
    });
  });

  constructor() {
    const initialParams = this.route.snapshot.queryParamMap;
    this.searchControl.setValue(initialParams.get('q') ?? '', { emitEvent: false });
    this.typeControl.setValue(initialParams.get('type') ?? '', { emitEvent: false });
    this.villeControl.setValue(initialParams.get('ville') ?? '', { emitEvent: false });
    this.capaciteMinControl.setValue(initialParams.get('capacite_min') ?? '', { emitEvent: false });
    this.tarifMinControl.setValue(initialParams.get('tarif_min') ?? '', { emitEvent: false });
    this.tarifMaxControl.setValue(initialParams.get('tarif_max') ?? '', { emitEvent: false });
    this.search.set(this.searchControl.value);
    this.type.set(this.typeControl.value);
    this.ville.set(this.villeControl.value);
    this.capaciteMin.set(this.capaciteMinControl.value);
    this.tarifMin.set(this.tarifMinControl.value);
    this.tarifMax.set(this.tarifMaxControl.value);

    this.searchControl.valueChanges.pipe(debounceTime(300), takeUntilDestroyed()).subscribe((value) => {
      this.search.set(value);
      this.syncQueryParams();
      void this.fetchSalles();
    });
    this.typeControl.valueChanges.pipe(takeUntilDestroyed()).subscribe((value) => {
      this.type.set(value);
      this.syncQueryParams();
    });
    this.villeControl.valueChanges.pipe(takeUntilDestroyed()).subscribe((value) => {
      this.ville.set(value);
      this.syncQueryParams();
    });
    this.capaciteMinControl.valueChanges.pipe(debounceTime(300), takeUntilDestroyed()).subscribe((value) => {
      this.capaciteMin.set(value);
      this.syncQueryParams();
      void this.fetchSalles();
    });
    this.tarifMinControl.valueChanges.pipe(debounceTime(300), takeUntilDestroyed()).subscribe((value) => {
      this.tarifMin.set(value);
      this.syncQueryParams();
    });
    this.tarifMaxControl.valueChanges.pipe(debounceTime(300), takeUntilDestroyed()).subscribe((value) => {
      this.tarifMax.set(value);
      this.syncQueryParams();
    });

    void this.fetchSalles();
  }

  protected resetFilters(): void {
    this.searchControl.setValue('');
    this.typeControl.setValue('');
    this.villeControl.setValue('');
    this.capaciteMinControl.setValue('');
    this.tarifMinControl.setValue('');
    this.tarifMaxControl.setValue('');
  }

  private syncQueryParams(): void {
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: {
        q: this.search() || null,
        type: this.type() || null,
        ville: this.ville() || null,
        capacite_min: this.capaciteMin() || null,
        tarif_min: this.tarifMin() || null,
        tarif_max: this.tarifMax() || null,
      },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
  }

  private async fetchSalles(): Promise<void> {
    this.loading.set(true);
    try {
      const page = await this.sallesService.list({
        search: this.search() || undefined,
        capacite_min: this.capaciteMin() ? Number(this.capaciteMin()) : undefined,
      });
      this.allSalles.set(page.results);
    } finally {
      this.loading.set(false);
    }
  }
}
