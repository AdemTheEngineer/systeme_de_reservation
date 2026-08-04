import { Injectable, inject, signal } from '@angular/core';
import { Membre } from '../models';
import { MembresService } from './membres.service';

/**
 * Same rationale as `SallesCacheService` (no batch-by-ids endpoint), but
 * membres are paginated (90 in seed data, well above PAGE_SIZE=20). Resolving
 * ids one request at a time (up to ~90 concurrent GETs for a reservations
 * list) saturates Django's single-threaded dev server and stalls the page —
 * paginating through the full membres list instead costs ~5 sequential
 * requests, once, cached for the session.
 */
@Injectable({ providedIn: 'root' })
export class MembresCacheService {
  private readonly membresService = inject(MembresService);
  private readonly cacheSignal = signal<Map<string, Membre>>(new Map());
  private loadPromise: Promise<void> | null = null;

  readonly cache = this.cacheSignal.asReadonly();

  email(membreId: string): string {
    return this.cacheSignal().get(membreId)?.email ?? '…';
  }

  async ensureLoaded(): Promise<void> {
    if (this.cacheSignal().size > 0) {
      return;
    }
    if (!this.loadPromise) {
      this.loadPromise = this.loadAllPages();
    }
    return this.loadPromise;
  }

  private async loadAllPages(): Promise<void> {
    const map = new Map<string, Membre>();
    let page = 1;
    let hasNext = true;
    while (hasNext) {
      const result = await this.membresService.list({ page });
      for (const membre of result.results) {
        map.set(membre.id, membre);
      }
      hasNext = result.next !== null;
      page++;
    }
    this.cacheSignal.set(map);
  }
}
