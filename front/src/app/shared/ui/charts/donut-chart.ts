import { Component, computed, input } from '@angular/core';

export interface DonutDatum {
  label: string;
  value: number;
  /** Tailwind stroke-* utility, e.g. `stroke-emerald-500`. */
  strokeClass: string;
}

interface DonutSegment extends DonutDatum {
  dasharray: string;
  dashoffset: number;
  dotClass: string;
}

const CIRCUMFERENCE_UNITS = 100;
const RADIUS = 15.915;

@Component({
  selector: 'ui-donut-chart',
  template: `
    <div class="flex items-center gap-6">
      <svg viewBox="0 0 42 42" class="size-28 -rotate-90 shrink-0" role="img" aria-label="Répartition">
        <circle cx="21" cy="21" [attr.r]="radius" class="fill-none stroke-neutral-100" stroke-width="4" />
        @for (segment of segments(); track segment.label) {
          <circle
            cx="21"
            cy="21"
            [attr.r]="radius"
            class="fill-none"
            [class]="segment.strokeClass"
            stroke-width="4"
            [attr.stroke-dasharray]="segment.dasharray"
            [attr.stroke-dashoffset]="segment.dashoffset"
          />
        }
      </svg>
      <ul class="flex flex-col gap-2 text-sm">
        @for (segment of segments(); track segment.label) {
          <li class="flex items-center gap-2">
            <span class="size-2.5 rounded-full" [class]="segment.dotClass"></span>
            <span class="text-neutral-600">{{ segment.label }}</span>
            <span class="font-medium text-neutral-900">{{ segment.value }}</span>
          </li>
        }
      </ul>
    </div>
  `,
})
export class DonutChart {
  readonly data = input.required<DonutDatum[]>();
  protected readonly radius = RADIUS;

  protected readonly segments = computed<DonutSegment[]>(() => {
    const items = this.data();
    const total = items.reduce((sum, item) => sum + item.value, 0) || 1;
    let cumulative = 0;
    return items.map((item) => {
      const percent = (item.value / total) * CIRCUMFERENCE_UNITS;
      const segment: DonutSegment = {
        ...item,
        dasharray: `${percent} ${CIRCUMFERENCE_UNITS - percent}`,
        dashoffset: -cumulative,
        dotClass: item.strokeClass.replace('stroke-', 'bg-'),
      };
      cumulative += percent;
      return segment;
    });
  });
}
