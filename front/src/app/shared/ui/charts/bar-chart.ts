import { Component, input } from '@angular/core';

export interface BarChartDatum {
  label: string;
  /** 0-100 */
  value: number;
  valueLabel: string;
}

@Component({
  selector: 'ui-bar-chart',
  template: `
    <div class="flex flex-col gap-3">
      @for (item of data(); track item.label) {
        <div class="flex flex-col gap-1">
          <div class="flex items-center justify-between text-sm">
            <span class="text-neutral-700">{{ item.label }}</span>
            <span class="font-medium text-neutral-900">{{ item.valueLabel }}</span>
          </div>
          <svg viewBox="0 0 100 8" class="h-2 w-full overflow-visible" preserveAspectRatio="none" role="img" [attr.aria-label]="item.label + ': ' + item.valueLabel">
            <rect x="0" y="0" width="100" height="8" rx="4" class="fill-neutral-100" />
            <rect x="0" y="0" [attr.width]="clamp(item.value)" height="8" rx="4" class="fill-brand-blue" />
          </svg>
        </div>
      }
    </div>
  `,
})
export class BarChart {
  readonly data = input.required<BarChartDatum[]>();

  protected clamp(value: number): number {
    return Math.min(100, Math.max(0, value));
  }
}
