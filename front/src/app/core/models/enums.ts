export const TypeEspace = {
  BureauPrive: 'BUREAU_PRIVE',
  OpenSpace: 'OPEN_SPACE',
  SalleReunion: 'SALLE_REUNION',
} as const;
export type TypeEspace = (typeof TypeEspace)[keyof typeof TypeEspace];

export const CreneauStatut = {
  Disponible: 'DISPONIBLE',
  Reserve: 'RESERVE',
} as const;
export type CreneauStatut = (typeof CreneauStatut)[keyof typeof CreneauStatut];

export const ReservationStatut = {
  EnAttente: 'EN_ATTENTE',
  Confirmee: 'CONFIRMEE',
  Annulee: 'ANNULEE',
} as const;
export type ReservationStatut = (typeof ReservationStatut)[keyof typeof ReservationStatut];

export const PaiementStatut = {
  EnAttente: 'EN_ATTENTE',
  Accepte: 'ACCEPTE',
  Refuse: 'REFUSE',
} as const;
export type PaiementStatut = (typeof PaiementStatut)[keyof typeof PaiementStatut];

export const MoyenPaiement = {
  Carte: 'CARTE',
  Virement: 'VIREMENT',
  Especes: 'ESPECES',
} as const;
export type MoyenPaiement = (typeof MoyenPaiement)[keyof typeof MoyenPaiement];

export const Role = {
  Membre: 'membre',
  Gestionnaire: 'gestionnaire',
  Aucun: 'aucun',
} as const;
export type Role = (typeof Role)[keyof typeof Role];
