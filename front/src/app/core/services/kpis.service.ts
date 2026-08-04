import { Injectable, inject } from '@angular/core';
import { ApiService } from '../api/api.service';
import { DashboardKPI, PeriodeQuery, RevenuPeriode, TauxOccupation } from '../models';

@Injectable({ providedIn: 'root' })
export class KpisService {
  private readonly api = inject(ApiService);

  occupation(periode: PeriodeQuery): Promise<TauxOccupation[]> {
    return this.api.get<TauxOccupation[]>('/kpis/occupation/', { params: periode });
  }

  revenu(periode: PeriodeQuery): Promise<RevenuPeriode> {
    return this.api.get<RevenuPeriode>('/kpis/revenu/', { params: periode });
  }

  dashboard(periode: PeriodeQuery): Promise<DashboardKPI> {
    return this.api.get<DashboardKPI>('/kpis/dashboard/', { params: periode });
  }
}
