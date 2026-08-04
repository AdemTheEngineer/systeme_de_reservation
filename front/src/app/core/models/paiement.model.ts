import { MoyenPaiement, PaiementStatut } from './enums';

export interface Paiement {
  id: string;
  reservation: string;
  montant: string;
  devise: string;
  statut: PaiementStatut;
  moyen: MoyenPaiement;
  reference_externe: string | null;
  date_paiement: string;
}

export interface PaiementRequest {
  reservation: string;
  montant: string;
  devise?: string;
  moyen: MoyenPaiement;
}
