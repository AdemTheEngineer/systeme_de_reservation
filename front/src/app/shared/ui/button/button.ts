import { Component, input } from '@angular/core';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary: 'bg-brand-blue text-white border border-brand-blue hover:bg-brand-blue-dark',
  secondary: 'bg-white text-neutral-700 border border-neutral-300 hover:bg-neutral-50',
  ghost: 'bg-transparent text-neutral-700 border border-transparent hover:bg-neutral-100',
  danger: 'bg-rose-600 text-white border border-rose-600 hover:bg-rose-700',
};

const SIZE_CLASSES: Record<ButtonSize, string> = {
  sm: 'h-8 px-3 text-sm gap-1.5',
  md: 'h-10 px-4 text-sm gap-2',
  lg: 'h-12 px-6 text-base gap-2',
};

@Component({
  selector: 'ui-button',
  template: `
    <button
      [type]="type()"
      [disabled]="disabled() || loading()"
      [class]="classes()"
    >
      @if (loading()) {
        <svg class="size-4 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8V0C5.373 0 0 5.373 0 12h4Z" />
        </svg>
      }
      <ng-content />
    </button>
  `,
})
export class Button {
  readonly variant = input<ButtonVariant>('primary');
  readonly size = input<ButtonSize>('md');
  readonly type = input<'button' | 'submit' | 'reset'>('button');
  readonly disabled = input(false);
  readonly loading = input(false);
  readonly fullWidth = input(false);

  protected classes(): string {
    return [
      'inline-flex items-center justify-center rounded-lg font-medium transition-colors cursor-pointer',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue focus-visible:ring-offset-2',
      VARIANT_CLASSES[this.variant()],
      SIZE_CLASSES[this.size()],
      this.fullWidth() ? 'w-full' : '',
    ].join(' ');
  }
}
