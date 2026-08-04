import { Component, ElementRef, effect, input, output, viewChild } from '@angular/core';
import { Icon } from '../icon/icon';
import { trapTabKey } from '../modal/focus-trap.util';

let nextId = 0;

@Component({
  selector: 'ui-drawer',
  imports: [Icon],
  template: `
    @if (open()) {
      <div class="fixed inset-0 z-50 flex justify-end">
        <div class="absolute inset-0 bg-neutral-900/40" (click)="closed.emit()"></div>
        <div
          #panel
          role="dialog"
          aria-modal="true"
          [attr.aria-labelledby]="titleId"
          tabindex="-1"
          (keydown.escape)="closed.emit()"
          (keydown.tab)="onTab($event)"
          class="relative bg-white shadow-lg h-full w-full max-w-md overflow-y-auto p-6 flex flex-col gap-4 focus:outline-none"
        >
          <div class="flex items-start justify-between gap-4">
            <h2 [id]="titleId" class="text-lg font-semibold text-neutral-900">{{ title() }}</h2>
            <button
              type="button"
              (click)="closed.emit()"
              aria-label="Fermer"
              class="text-neutral-400 hover:text-neutral-700 rounded-lg
                     focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue"
            >
              <ui-icon name="x" [size]="20" />
            </button>
          </div>
          <ng-content />
        </div>
      </div>
    }
  `,
})
export class Drawer {
  readonly open = input(false);
  readonly title = input<string>('');
  readonly closed = output<void>();

  protected readonly titleId = `ui-drawer-title-${nextId++}`;
  private readonly panel = viewChild<ElementRef<HTMLElement>>('panel');

  constructor() {
    effect(() => {
      if (this.open()) {
        queueMicrotask(() => this.panel()?.nativeElement.focus());
      }
    });
  }

  protected onTab(event: Event): void {
    const panel = this.panel()?.nativeElement;
    if (panel) {
      trapTabKey(panel, event as KeyboardEvent);
    }
  }
}
