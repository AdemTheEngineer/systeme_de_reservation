import { Injectable, inject } from '@angular/core';
import { ApiService } from '../api/api.service';
import { Membre, MembreRequest, Paginated, PageQuery } from '../models';

@Injectable({ providedIn: 'root' })
export class MembresService {
  private readonly api = inject(ApiService);

  list(query: PageQuery = {}): Promise<Paginated<Membre>> {
    return this.api.get<Paginated<Membre>>('/membres/', { params: query });
  }

  get(id: string): Promise<Membre> {
    return this.api.get<Membre>(`/membres/${id}/`);
  }

  create(payload: MembreRequest): Promise<Membre> {
    return this.api.post<Membre, MembreRequest>('/membres/', payload);
  }

  update(id: string, payload: MembreRequest): Promise<Membre> {
    return this.api.put<Membre, MembreRequest>(`/membres/${id}/`, payload);
  }

  remove(id: string): Promise<void> {
    return this.api.delete<void>(`/membres/${id}/`);
  }
}
