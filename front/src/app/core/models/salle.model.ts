import { TypeEspace } from './enums';

export interface Salle {
  id_espace: string;
  nom: string;
  type_espace: TypeEspace;
  capacite: number;
  tarif_horaire: string;
  disponible: boolean;
  localisation: string | null;
  id_gestionnaire: string;
  equipements: string;
  date_creation: string;
}

export interface SalleRequest {
  nom: string;
  type_espace: TypeEspace;
  capacite: number;
  tarif_horaire: string;
  disponible?: boolean;
  localisation?: string | null;
  id_gestionnaire: string;
  equipements?: string;
}

export interface SalleDisponible {
  id: string;
  nom: string;
  capacite: number;
  tarif_horaire: string;
  devise: string;
}
