import { Injectable, computed, signal } from '@angular/core';
import { Role, TokenPair, Utilisateur } from '../models';

const ACCESS_TOKEN_KEY = 'coworking.access_token';
const REFRESH_TOKEN_KEY = 'coworking.refresh_token';

@Injectable({ providedIn: 'root' })
export class AuthStore {
  private readonly accessTokenSignal = signal<string | null>(localStorage.getItem(ACCESS_TOKEN_KEY));
  private readonly refreshTokenSignal = signal<string | null>(localStorage.getItem(REFRESH_TOKEN_KEY));
  private readonly currentUserSignal = signal<Utilisateur | null>(null);
  private readonly restoredSignal = signal(false);

  readonly accessToken = this.accessTokenSignal.asReadonly();
  readonly refreshToken = this.refreshTokenSignal.asReadonly();
  readonly currentUser = this.currentUserSignal.asReadonly();
  readonly restored = this.restoredSignal.asReadonly();

  readonly isAuthenticated = computed(() => this.accessTokenSignal() !== null);
  readonly role = computed<Role | null>(() => this.currentUserSignal()?.role ?? null);
  readonly isMembre = computed(() => this.role() === Role.Membre);
  readonly isGestionnaire = computed(() => this.role() === Role.Gestionnaire);

  setTokens(tokens: TokenPair): void {
    this.accessTokenSignal.set(tokens.access);
    this.refreshTokenSignal.set(tokens.refresh);
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh);
  }

  setAccessToken(token: string): void {
    this.accessTokenSignal.set(token);
    localStorage.setItem(ACCESS_TOKEN_KEY, token);
  }

  setUser(user: Utilisateur): void {
    this.currentUserSignal.set(user);
  }

  markRestored(): void {
    this.restoredSignal.set(true);
  }

  clearSession(): void {
    this.accessTokenSignal.set(null);
    this.refreshTokenSignal.set(null);
    this.currentUserSignal.set(null);
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }
}
