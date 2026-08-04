import { Component, input } from '@angular/core';

export type BadgeTone = 'neutral' | 'success' | 'warning' | 'danger' | 'info';

const TONE_CLASSES: Record<BadgeTone, string> = {
  neutral: 'bg-neutral-100 text-neutral-700',
  success: 'bg-emerald-50 text-emerald-700',
  warning: 'bg-amber-50 text-amber-700',
  danger: 'bg-rose-50 text-rose-700',
  info: 'bg-blue-50 text-blue-700',
};

@Component({
  selector: 'ui-badge',
  template: `
    <span [class]="classes()">
      <ng-content />
    </span>
  `,
})
export class Badge {
  readonly tone = input<BadgeTone>('neutral');

  protected classes(): string {
    return [
      'inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium',
      TONE_CLASSES[this.tone()],
    ].join(' ');
  }
}
