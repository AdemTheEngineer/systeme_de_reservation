import { Component, input } from '@angular/core';
import { Icon } from '../icon/icon';

@Component({
  selector: 'ui-stat-card',
  imports: [Icon],
  template: `
    <div class="bg-white border border-neutral-200 rounded-xl shadow-sm p-4 sm:p-6 flex items-start justify-between gap-4">
      <div class="flex flex-col gap-1 min-w-0">
        <span class="text-sm text-neutral-500">{{ label() }}</span>
        <span class="text-2xl font-semibold text-neutral-900 truncate">{{ value() }}</span>
        @if (hint()) {
          <span class="text-xs text-neutral-500">{{ hint() }}</span>
        }
      </div>
      @if (icon()) {
        <span class="flex items-center justify-center size-10 rounded-full bg-brand-blue/10 text-brand-blue shrink-0">
          <ui-icon [name]="icon()" [size]="20" />
        </span>
      }
    </div>
  `,
})
export class StatCard {
  readonly label = input.required<string>();
  readonly value = input.required<string>();
  readonly hint = input<string>('');
  readonly icon = input<string>('');
}
