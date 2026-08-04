import { Injectable, computed, inject, signal } from '@angular/core';
import { Salle } from '../models';
import { SallesService } from './salles.service';

/**
 * The salles catalogue is small (a physical list of coworking rooms, not a
 * high-cardinality resource) and the API has no batch-by-ids endpoint, so
 * reservation/paiement views that need to display a salle's name alongside
 * its salle_id load the whole catalogue once and look it up client-side
 * instead of firing one request per row.
 */
@Injectable({ providedIn: 'root' })
export class SallesCacheService {
  private readonly sallesService = inject(SallesService);

  private readonly sallesSignal = signal<Salle[]>([]);
  private loadPromise: Promise<Salle[]> | null = null;

  readonly salles = this.sallesSignal.asReadonly();
  readonly byId = computed(() => new Map(this.sallesSignal().map((salle) => [salle.id_espace, salle])));

  async ensureLoaded(): Promise<Salle[]> {
    if (this.sallesSignal().length > 0) {
      return this.sallesSignal();
    }
    if (!this.loadPromise) {
      this.loadPromise = this.sallesService.list({ page: 1 }).then((page) => {
        this.sallesSignal.set(page.results);
        return page.results;
      });
    }
    return this.loadPromise;
  }

  nom(salleId: string): string {
    return this.byId().get(salleId)?.nom ?? 'Espace inconnu';
  }
}
