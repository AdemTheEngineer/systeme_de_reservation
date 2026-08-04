import { Component, input } from '@angular/core';
import { Icon } from '../icon/icon';

@Component({
  selector: 'ui-empty-state',
  imports: [Icon],
  template: `
    <div class="flex flex-col items-center justify-center gap-3 py-12 px-4 text-center">
      <span class="flex items-center justify-center size-12 rounded-full bg-neutral-100 text-neutral-400">
        <ui-icon [name]="icon()" [size]="24" />
      </span>
      <div class="flex flex-col gap-1">
        <p class="text-sm font-medium text-neutral-900">{{ title() }}</p>
        @if (description()) {
          <p class="text-sm text-neutral-500 max-w-sm">{{ description() }}</p>
        }
      </div>
      <ng-content />
    </div>
  `,
})
export class EmptyState {
  readonly icon = input<string>('list-filter');
  readonly title = input.required<string>();
  readonly description = input<string>('');
}
