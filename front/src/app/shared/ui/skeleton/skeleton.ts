import { Component, input } from '@angular/core';

@Component({
  selector: 'ui-skeleton',
  template: `<div [class]="classes()"></div>`,
})
export class Skeleton {
  /** Literal Tailwind width utility, e.g. `w-full`, `w-32`, `w-1/2`. */
  readonly widthClass = input<string>('w-full');
  /** Literal Tailwind height utility, e.g. `h-4`, `h-10`, `h-40`. */
  readonly heightClass = input<string>('h-4');
  readonly rounded = input<'lg' | 'xl' | 'full'>('lg');

  protected classes(): string {
    const roundedClass = { lg: 'rounded-lg', xl: 'rounded-xl', full: 'rounded-full' }[this.rounded()];
    return `animate-pulse bg-neutral-200 ${roundedClass} ${this.widthClass()} ${this.heightClass()}`;
  }
}
