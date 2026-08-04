import { Injectable, inject } from '@angular/core';
import { ApiService } from '../api/api.service';
import { AuthStore } from '../auth/auth-store';
import { LoginRequest, TokenPair, Utilisateur } from '../models';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly api = inject(ApiService);
  private readonly authStore = inject(AuthStore);

  async login(credentials: LoginRequest): Promise<void> {
    const tokens = await this.api.post<TokenPair, LoginRequest>('/auth/login/', credentials);
    this.authStore.setTokens(tokens);
    await this.loadCurrentUser();
  }

  async logout(): Promise<void> {
    const refresh = this.authStore.refreshToken();
    try {
      if (refresh) {
        await this.api.post('/auth/logout/', { refresh });
      }
    } finally {
      this.authStore.clearSession();
    }
  }

  async loadCurrentUser(): Promise<Utilisateur> {
    const user = await this.api.get<Utilisateur>('/auth/me/');
    this.authStore.setUser(user);
    return user;
  }

  async restoreSession(): Promise<void> {
    if (this.authStore.accessToken()) {
      try {
        await this.loadCurrentUser();
      } catch {
        this.authStore.clearSession();
      }
    }
    this.authStore.markRestored();
  }
}
