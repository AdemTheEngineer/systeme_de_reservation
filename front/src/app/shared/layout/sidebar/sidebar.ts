import { Component, input } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { Icon } from '../../ui/icon/icon';

export interface NavItem {
  label: string;
  icon: string;
  route: string;
}

@Component({
  selector: 'app-sidebar',
  imports: [RouterLink, RouterLinkActive, Icon],
  template: `
    <nav class="flex flex-col gap-1 p-4" aria-label="Navigation principale">
      @for (item of items(); track item.route) {
        <a
          [routerLink]="item.route"
          routerLinkActive="text-brand-blue bg-brand-blue/5 border-brand-blue"
          class="flex items-center gap-3 rounded-lg border-l-4 border-transparent px-3 py-2.5 text-sm font-medium text-neutral-600
                 transition-colors hover:bg-neutral-100 hover:text-neutral-900
                 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue"
        >
          <ui-icon [name]="item.icon" [size]="18" />
          {{ item.label }}
        </a>
      }
    </nav>
  `,
})
export class Sidebar {
  readonly items = input.required<NavItem[]>();
}
