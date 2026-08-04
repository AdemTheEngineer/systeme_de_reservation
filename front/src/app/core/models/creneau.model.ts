import { CreneauStatut } from './enums';

export interface Creneau {
  id: string;
  espace: string;
  date: string;
  heure_debut: string;
  heure_fin: string;
  statut: CreneauStatut;
}

export interface CreneauRequest {
  espace: string;
  date: string;
  heure_debut: string;
  heure_fin: string;
}
