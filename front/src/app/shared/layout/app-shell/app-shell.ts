import { Component, input, output, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Icon } from '../../ui/icon/icon';
import { ToastContainer } from '../../ui/toast/toast-container';
import { NavItem, Sidebar } from '../sidebar/sidebar';
import { Topbar } from '../topbar/topbar';

@Component({
  selector: 'app-shell',
  imports: [Sidebar, Topbar, RouterOutlet, ToastContainer, Icon],
  template: `
    <div class="flex min-h-dvh bg-neutral-50">
      <aside class="hidden border-r border-neutral-200 bg-white lg:flex lg:w-64 lg:flex-col">
        <div class="flex h-16 items-center px-6 border-b border-neutral-200">
          <span class="text-lg font-semibold text-brand-blue">Coworking</span>
        </div>
        <app-sidebar [items]="navItems()" />
      </aside>

      @if (mobileMenuOpen()) {
        <div class="fixed inset-0 z-40 flex lg:hidden">
          <div class="absolute inset-0 bg-neutral-900/40" (click)="mobileMenuOpen.set(false)"></div>
          <aside class="relative flex h-full w-64 flex-col bg-white">
            <div class="flex h-16 items-center justify-between border-b border-neutral-200 px-6">
              <span class="text-lg font-semibold text-brand-blue">Coworking</span>
              <button
                type="button"
                (click)="mobileMenuOpen.set(false)"
                aria-label="Fermer le menu"
                class="flex size-9 items-center justify-center rounded-lg text-neutral-500 hover:bg-neutral-100
                       focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue"
              >
                <ui-icon name="x" [size]="20" />
              </button>
            </div>
            <app-sidebar [items]="navItems()" />
          </aside>
        </div>
      }

      <div class="flex min-w-0 flex-1 flex-col">
        <app-topbar
          [userName]="userName()"
          [roleLabel]="roleLabel()"
          (menuToggled)="mobileMenuOpen.set(true)"
          (logout)="logoutRequested.emit()"
        />
        <main class="flex-1 p-4 sm:p-6 lg:p-8">
          <router-outlet />
        </main>
      </div>
    </div>
    <ui-toast-container />
  `,
})
export class AppShell {
  readonly navItems = input.required<NavItem[]>();
  readonly userName = input<string>('');
  readonly roleLabel = input<string>('');

  readonly logoutRequested = output<void>();

  protected readonly mobileMenuOpen = signal(false);
}
