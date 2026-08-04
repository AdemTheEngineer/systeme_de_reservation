import { Component, input } from '@angular/core';

@Component({
  selector: 'ui-tooltip',
  template: `
    <span class="group relative inline-flex">
      <ng-content />
      <span
        role="tooltip"
        class="pointer-events-none absolute bottom-full left-1/2 z-50 mb-2 -translate-x-1/2 whitespace-nowrap
               rounded-lg bg-neutral-900 px-2 py-1 text-xs text-white opacity-0 transition-opacity
               group-hover:opacity-100 group-focus-within:opacity-100"
      >
        {{ text() }}
      </span>
    </span>
  `,
})
export class Tooltip {
  readonly text = input.required<string>();
}
