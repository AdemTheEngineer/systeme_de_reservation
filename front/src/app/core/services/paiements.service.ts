import { Injectable, inject } from '@angular/core';
import { ApiService } from '../api/api.service';
import { Paginated, PageQuery, Paiement, PaiementRequest, PaiementStatut } from '../models';

export interface PaiementsQuery extends PageQuery {
  reservation?: string;
  statut?: PaiementStatut;
}

@Injectable({ providedIn: 'root' })
export class PaiementsService {
  private readonly api = inject(ApiService);

  list(query: PaiementsQuery = {}): Promise<Paginated<Paiement>> {
    return this.api.get<Paginated<Paiement>>('/paiements/', { params: query });
  }

  get(id: string): Promise<Paiement> {
    return this.api.get<Paiement>(`/paiements/${id}/`);
  }

  create(payload: PaiementRequest): Promise<Paiement> {
    return this.api.post<Paiement, PaiementRequest>('/paiements/', payload);
  }

  statut(id: string): Promise<{ statut: PaiementStatut }> {
    return this.api.get<{ statut: PaiementStatut }>(`/paiements/${id}/statut/`);
  }
}
