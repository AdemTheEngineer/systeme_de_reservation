import { Component, input } from '@angular/core';

@Component({
  selector: 'ui-card',
  template: `
    <div [class]="classes()">
      <ng-content />
    </div>
  `,
})
export class Card {
  readonly padded = input(true);

  protected classes(): string {
    return [
      'bg-white border border-neutral-200 rounded-xl shadow-sm',
      this.padded() ? 'p-4 sm:p-6' : '',
    ].join(' ');
  }
}
