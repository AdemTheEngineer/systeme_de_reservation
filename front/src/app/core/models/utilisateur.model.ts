import { Role } from './enums';

export interface Utilisateur {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  telephone: string;
  role: Role;
}

export interface Membre {
  id: string;
  email: string;
  telephone: string;
  date_creation: string;
}

export interface Gestionnaire {
  id: string;
  email: string;
  telephone: string;
  date_creation: string;
}

export interface MembreRequest {
  email: string;
  telephone?: string;
  mot_de_passe?: string;
}

export interface GestionnaireRequest {
  email: string;
  telephone?: string;
  mot_de_passe?: string;
}
