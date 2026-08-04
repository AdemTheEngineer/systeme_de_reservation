import { Injectable, inject } from '@angular/core';
import { Router } from '@angular/router';
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { environment } from '../../../environments/environment';
import { AuthStore } from '../auth/auth-store';
import { TokenRefresh } from '../models';
import { normalizeApiError } from './api-error.util';

interface RetryableRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly authStore = inject(AuthStore);
  private readonly router = inject(Router);
  private readonly client: AxiosInstance;
  private refreshPromise: Promise<string> | null = null;

  constructor() {
    this.client = axios.create({ baseURL: environment.apiBaseUrl });

    this.client.interceptors.request.use((config) => {
      const token = this.authStore.accessToken();
      if (token) {
        config.headers.set('Authorization', `Bearer ${token}`);
      }
      return config;
    });

    this.client.interceptors.response.use(
      (response) => response,
      (error: unknown) => this.handleResponseError(error),
    );
  }

  get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.client.get<T>(url, config).then((response) => response.data);
  }

  post<T, D = unknown>(url: string, data?: D, config?: AxiosRequestConfig): Promise<T> {
    return this.client.post<T>(url, data, config).then((response) => response.data);
  }

  put<T, D = unknown>(url: string, data?: D, config?: AxiosRequestConfig): Promise<T> {
    return this.client.put<T>(url, data, config).then((response) => response.data);
  }

  patch<T, D = unknown>(url: string, data?: D, config?: AxiosRequestConfig): Promise<T> {
    return this.client.patch<T>(url, data, config).then((response) => response.data);
  }

  delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.client.delete<T>(url, config).then((response) => response.data);
  }

  private async handleResponseError(error: unknown): Promise<AxiosResponse> {
    const isAxiosError = axios.isAxiosError(error);
    const originalRequest = isAxiosError ? (error.config as RetryableRequestConfig | undefined) : undefined;
    const status = isAxiosError ? error.response?.status : undefined;
    const isAuthRoute = originalRequest?.url?.includes('/auth/login') || originalRequest?.url?.includes('/auth/refresh');

    if (status === 401 && originalRequest && !originalRequest._retry && !isAuthRoute) {
      originalRequest._retry = true;
      try {
        const newAccessToken = await this.refreshAccessToken();
        originalRequest.headers.set('Authorization', `Bearer ${newAccessToken}`);
        return await this.client.request(originalRequest);
      } catch {
        this.authStore.clearSession();
        void this.router.navigateByUrl('/auth/login');
      }
    }

    throw normalizeApiError(error);
  }

  private refreshAccessToken(): Promise<string> {
    if (!this.refreshPromise) {
      const refreshToken = this.authStore.refreshToken();
      if (!refreshToken) {
        this.refreshPromise = Promise.reject(new Error('Aucun jeton de rafraîchissement disponible.'));
      } else {
        this.refreshPromise = axios
          .post<TokenRefresh>(`${environment.apiBaseUrl}/auth/refresh/`, { refresh: refreshToken })
          .then((response) => {
            this.authStore.setAccessToken(response.data.access);
            return response.data.access;
          })
          .finally(() => {
            this.refreshPromise = null;
          });
      }
    }
    return this.refreshPromise;
  }
}
