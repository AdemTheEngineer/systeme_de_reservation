import { Injectable, inject } from '@angular/core';
import { ApiService } from '../api/api.service';
import { Paginated, PageQuery, Salle, SalleDisponible, SalleRequest } from '../models';

export interface SallesQuery extends PageQuery {
  capacite_min?: number;
}

export interface DisponibiliteQuery {
  date: string;
  heure_debut: string;
  heure_fin: string;
}

@Injectable({ providedIn: 'root' })
export class SallesService {
  private readonly api = inject(ApiService);

  list(query: SallesQuery = {}): Promise<Paginated<Salle>> {
    return this.api.get<Paginated<Salle>>('/salles/', { params: query });
  }

  get(id: string): Promise<Salle> {
    return this.api.get<Salle>(`/salles/${id}/`);
  }

  create(payload: SalleRequest): Promise<Salle> {
    return this.api.post<Salle, SalleRequest>('/salles/', payload);
  }

  update(id: string, payload: SalleRequest): Promise<Salle> {
    return this.api.put<Salle, SalleRequest>(`/salles/${id}/`, payload);
  }

  patch(id: string, payload: Partial<SalleRequest>): Promise<Salle> {
    return this.api.patch<Salle, Partial<SalleRequest>>(`/salles/${id}/`, payload);
  }

  remove(id: string): Promise<void> {
    return this.api.delete<void>(`/salles/${id}/`);
  }

  disponibles(query: DisponibiliteQuery): Promise<SalleDisponible[]> {
    return this.api.get<SalleDisponible[]>('/salles/disponibles/', { params: query });
  }
}
