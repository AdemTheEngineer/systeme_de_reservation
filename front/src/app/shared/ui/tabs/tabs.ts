import { Component, input, model } from '@angular/core';

export interface TabItem {
  value: string;
  label: string;
}

@Component({
  selector: 'ui-tabs',
  template: `
    <div class="flex gap-1 border-b border-neutral-200" role="tablist">
      @for (tab of tabs(); track tab.value) {
        <button
          type="button"
          role="tab"
          [attr.aria-selected]="tab.value === active()"
          (click)="active.set(tab.value)"
          class="relative px-3 py-2.5 text-sm font-medium transition-colors cursor-pointer
                 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue rounded-t-lg"
          [class]="tab.value === active() ? 'text-brand-blue' : 'text-neutral-500 hover:text-neutral-800'"
        >
          {{ tab.label }}
          @if (tab.value === active()) {
            <span class="absolute inset-x-0 -bottom-px h-0.5 bg-brand-blue rounded-full"></span>
          }
        </button>
      }
    </div>
  `,
})
export class Tabs {
  readonly tabs = input.required<TabItem[]>();
  readonly active = model.required<string>();
}
