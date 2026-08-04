export interface LoginRequest {
  email: string;
  mot_de_passe: string;
}

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface TokenRefreshRequest {
  refresh: string;
}

export interface TokenRefresh {
  access: string;
  refresh: string;
}
