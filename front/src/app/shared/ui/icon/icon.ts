import { Component, input } from '@angular/core';
import { LucideDynamicIcon } from '@lucide/angular';

@Component({
  selector: 'ui-icon',
  imports: [LucideDynamicIcon],
  template: `<svg [lucideIcon]="name()" [size]="size()" class="shrink-0"></svg>`,
})
export class Icon {
  readonly name = input.required<string>();
  readonly size = input(20);
}
