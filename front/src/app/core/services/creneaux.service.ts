import { Injectable, inject } from '@angular/core';
import { ApiService } from '../api/api.service';
import { Creneau, CreneauRequest, CreneauStatut, Paginated, PageQuery } from '../models';

export interface CreneauxQuery extends PageQuery {
  date?: string;
  espace?: string;
  statut?: CreneauStatut;
}

@Injectable({ providedIn: 'root' })
export class CreneauxService {
  private readonly api = inject(ApiService);

  list(query: CreneauxQuery = {}): Promise<Paginated<Creneau>> {
    return this.api.get<Paginated<Creneau>>('/creneaux/', { params: query });
  }

  get(id: string): Promise<Creneau> {
    return this.api.get<Creneau>(`/creneaux/${id}/`);
  }

  create(payload: CreneauRequest): Promise<Creneau> {
    return this.api.post<Creneau, CreneauRequest>('/creneaux/', payload);
  }

  update(id: string, payload: CreneauRequest): Promise<Creneau> {
    return this.api.put<Creneau, CreneauRequest>(`/creneaux/${id}/`, payload);
  }

  patch(id: string, payload: Partial<CreneauRequest>): Promise<Creneau> {
    return this.api.patch<Creneau, Partial<CreneauRequest>>(`/creneaux/${id}/`, payload);
  }

  remove(id: string): Promise<void> {
    return this.api.delete<void>(`/creneaux/${id}/`);
  }
}
