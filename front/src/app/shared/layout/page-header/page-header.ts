import { Component, input } from '@angular/core';

@Component({
  selector: 'app-page-header',
  template: `
    <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div class="flex flex-col gap-1">
        <h1 class="text-2xl font-semibold text-neutral-900">{{ title() }}</h1>
        @if (description()) {
          <p class="text-sm text-neutral-500">{{ description() }}</p>
        }
      </div>
      <div class="flex items-center gap-3">
        <ng-content />
      </div>
    </div>
  `,
})
export class PageHeader {
  readonly title = input.required<string>();
  readonly description = input<string>('');
}
