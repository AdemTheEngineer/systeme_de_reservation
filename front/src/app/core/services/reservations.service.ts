import { Injectable, inject } from '@angular/core';
import { ApiService } from '../api/api.service';
import { CreerReservationRequest, Reservation } from '../models';

@Injectable({ providedIn: 'root' })
export class ReservationsService {
  private readonly api = inject(ApiService);

  list(salle?: string): Promise<Reservation[]> {
    return this.api.get<Reservation[]>('/reservations/', { params: salle ? { salle } : undefined });
  }

  get(id: string): Promise<Reservation> {
    return this.api.get<Reservation>(`/reservations/${id}/`);
  }

  create(payload: CreerReservationRequest): Promise<Reservation> {
    return this.api.post<Reservation, CreerReservationRequest>('/reservations/', payload);
  }

  cancel(id: string): Promise<Reservation> {
    return this.api.patch<Reservation>(`/reservations/${id}/`, {});
  }
}
