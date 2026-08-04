import { Component, inject } from '@angular/core';
import { Icon } from '../icon/icon';
import { ToastTone, ToastService } from './toast.service';

const BORDER_CLASSES: Record<ToastTone, string> = {
  success: 'border-emerald-200',
  error: 'border-rose-200',
  info: 'border-neutral-200',
};

const ICON_CLASSES: Record<ToastTone, string> = {
  success: 'text-emerald-600',
  error: 'text-rose-600',
  info: 'text-brand-blue',
};

const ICON_NAMES: Record<ToastTone, string> = {
  success: 'circle-check',
  error: 'circle-x',
  info: 'info',
};

@Component({
  selector: 'ui-toast-container',
  imports: [Icon],
  template: `
    <div class="fixed bottom-4 right-4 z-[100] flex w-full max-w-sm flex-col gap-2" aria-live="polite">
      @for (toast of toastService.toasts(); track toast.id) {
        <div class="flex items-start gap-3 rounded-xl border bg-white p-4 shadow-lg" [class]="BORDER_CLASSES[toast.tone]">
          <ui-icon [name]="ICON_NAMES[toast.tone]" [size]="18" [class]="ICON_CLASSES[toast.tone]" />
          <p class="flex-1 text-sm text-neutral-700">{{ toast.message }}</p>
          <button
            type="button"
            (click)="toastService.dismiss(toast.id)"
            aria-label="Fermer la notification"
            class="text-neutral-400 hover:text-neutral-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue rounded-lg"
          >
            <ui-icon name="x" [size]="16" />
          </button>
        </div>
      }
    </div>
  `,
})
export class ToastContainer {
  protected readonly toastService = inject(ToastService);
  protected readonly BORDER_CLASSES = BORDER_CLASSES;
  protected readonly ICON_CLASSES = ICON_CLASSES;
  protected readonly ICON_NAMES = ICON_NAMES;
}
