export interface TauxOccupation {
  salle_id: string;
  nom: string;
  heures_reservees: string;
  heures_disponibles: string;
  taux: string;
}

export interface RevenuPeriode {
  nombre_reservations: number;
  somme_acomptes: string;
  devise: string;
}

export interface DashboardKPI {
  periode_debut: string;
  periode_fin: string;
  occupation: TauxOccupation[];
  revenu: RevenuPeriode;
}

export interface PeriodeQuery {
  debut: string;
  fin: string;
}
