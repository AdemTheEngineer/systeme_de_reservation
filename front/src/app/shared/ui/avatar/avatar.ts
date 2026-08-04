import { Component, computed, input } from '@angular/core';

@Component({
  selector: 'ui-avatar',
  template: `
    <span
      class="inline-flex items-center justify-center rounded-full bg-brand-blue/10 text-brand-blue font-semibold select-none"
      [class]="sizeClasses()"
    >
      {{ initials() }}
    </span>
  `,
})
export class Avatar {
  readonly name = input<string>('');
  readonly size = input<'sm' | 'md' | 'lg'>('md');

  protected readonly initials = computed(() => {
    const parts = this.name().trim().split(/\s+/).filter(Boolean);
    if (parts.length === 0) {
      return '?';
    }
    const first = parts[0]?.[0] ?? '';
    const last = parts.length > 1 ? (parts[parts.length - 1]?.[0] ?? '') : '';
    return (first + last).toUpperCase();
  });

  protected sizeClasses(): string {
    const sizes = { sm: 'size-8 text-xs', md: 'size-10 text-sm', lg: 'size-12 text-base' } as const;
    return sizes[this.size()];
  }
}
