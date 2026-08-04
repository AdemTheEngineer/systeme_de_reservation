import { Injectable, inject } from '@angular/core';
import { ApiService } from '../api/api.service';
import { Gestionnaire, GestionnaireRequest, Paginated, PageQuery } from '../models';

@Injectable({ providedIn: 'root' })
export class GestionnairesService {
  private readonly api = inject(ApiService);

  list(query: PageQuery = {}): Promise<Paginated<Gestionnaire>> {
    return this.api.get<Paginated<Gestionnaire>>('/gestionnaires/', { params: query });
  }

  get(id: string): Promise<Gestionnaire> {
    return this.api.get<Gestionnaire>(`/gestionnaires/${id}/`);
  }

  update(id: string, payload: GestionnaireRequest): Promise<Gestionnaire> {
    return this.api.put<Gestionnaire, GestionnaireRequest>(`/gestionnaires/${id}/`, payload);
  }
}
