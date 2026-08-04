import { Component, computed, input, model } from '@angular/core';
import { Icon } from '../icon/icon';

@Component({
  selector: 'ui-pagination',
  imports: [Icon],
  template: `
    @if (totalPages() > 1) {
      <nav class="flex items-center justify-between gap-4" aria-label="Pagination">
        <p class="text-sm text-neutral-500">
          Page {{ page() }} sur {{ totalPages() }} — {{ count() }} résultat{{ count() > 1 ? 's' : '' }}
        </p>
        <div class="flex items-center gap-1">
          <button
            type="button"
            [disabled]="page() <= 1"
            (click)="page.set(page() - 1)"
            aria-label="Page précédente"
            class="flex items-center justify-center size-8 rounded-lg border border-neutral-300 text-neutral-600
                   hover:bg-neutral-50 disabled:opacity-40 disabled:cursor-not-allowed
                   focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue"
          >
            <ui-icon name="chevron-left" [size]="16" />
          </button>
          <button
            type="button"
            [disabled]="page() >= totalPages()"
            (click)="page.set(page() + 1)"
            aria-label="Page suivante"
            class="flex items-center justify-center size-8 rounded-lg border border-neutral-300 text-neutral-600
                   hover:bg-neutral-50 disabled:opacity-40 disabled:cursor-not-allowed
                   focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue"
          >
            <ui-icon name="chevron-right" [size]="16" />
          </button>
        </div>
      </nav>
    }
  `,
})
export class Pagination {
  readonly count = input.required<number>();
  readonly pageSize = input(20);
  readonly page = model(1);

  protected readonly totalPages = computed(() => Math.max(1, Math.ceil(this.count() / this.pageSize())));
}
