import { Injectable, signal } from '@angular/core';

export type ToastTone = 'success' | 'error' | 'info';

export interface ToastMessage {
  id: number;
  tone: ToastTone;
  message: string;
}

const AUTO_DISMISS_MS = 5000;

@Injectable({ providedIn: 'root' })
export class ToastService {
  private readonly toastsSignal = signal<ToastMessage[]>([]);
  private nextId = 0;

  readonly toasts = this.toastsSignal.asReadonly();

  success(message: string): void {
    this.push('success', message);
  }

  error(message: string): void {
    this.push('error', message);
  }

  info(message: string): void {
    this.push('info', message);
  }

  dismiss(id: number): void {
    this.toastsSignal.update((toasts) => toasts.filter((toast) => toast.id !== id));
  }

  private push(tone: ToastTone, message: string): void {
    const id = this.nextId++;
    this.toastsSignal.update((toasts) => [...toasts, { id, tone, message }]);
    setTimeout(() => this.dismiss(id), AUTO_DISMISS_MS);
  }
}
