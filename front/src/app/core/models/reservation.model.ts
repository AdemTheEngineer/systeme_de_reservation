import { ReservationStatut } from './enums';

export interface Reservation {
  id: string;
  salle_id: string;
  membre_id: string;
  date: string;
  heure_debut: string;
  heure_fin: string;
  statut: ReservationStatut;
  acompte: string;
  devise: string;
  paiement_id: string | null;
  date_creation: string;
  date_modification: string;
}

export interface CreerReservationRequest {
  creneau: string;
}
