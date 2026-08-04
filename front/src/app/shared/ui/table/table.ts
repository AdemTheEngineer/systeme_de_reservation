import { Component } from '@angular/core';

@Component({
  selector: 'ui-table',
  template: `
    <div class="overflow-x-auto rounded-xl border border-neutral-200 bg-white">
      <table class="w-full text-left text-sm">
        <ng-content />
      </table>
    </div>
  `,
})
export class Table {}
