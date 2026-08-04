import { Component, input, output } from '@angular/core';
import { Avatar } from '../../ui/avatar/avatar';
import { Icon } from '../../ui/icon/icon';

@Component({
  selector: 'app-topbar',
  imports: [Icon, Avatar],
  template: `
    <header class="flex items-center justify-between gap-4 border-b border-neutral-200 bg-white px-4 py-3 lg:px-6">
      <button
        type="button"
        (click)="menuToggled.emit()"
        aria-label="Ouvrir le menu"
        class="flex size-9 items-center justify-center rounded-lg text-neutral-600 hover:bg-neutral-100 lg:hidden
               focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue"
      >
        <ui-icon name="menu" [size]="22" />
      </button>

      <div class="flex flex-1 items-center justify-end gap-3">
        <div class="hidden flex-col items-end sm:flex">
          <span class="text-sm font-medium text-neutral-900">{{ userName() }}</span>
          <span class="text-xs text-neutral-500">{{ roleLabel() }}</span>
        </div>
        <ui-avatar [name]="userName()" size="sm" />
        <button
          type="button"
          (click)="logout.emit()"
          aria-label="Se déconnecter"
          class="flex size-9 items-center justify-center rounded-lg text-neutral-500 hover:bg-neutral-100 hover:text-neutral-900
                 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue"
        >
          <ui-icon name="log-out" [size]="18" />
        </button>
      </div>
    </header>
  `,
})
export class Topbar {
  readonly userName = input<string>('');
  readonly roleLabel = input<string>('');

  readonly menuToggled = output<void>();
  readonly logout = output<void>();
}
