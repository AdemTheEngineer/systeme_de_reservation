import { Component, input, output } from '@angular/core';
import { Button } from '../button/button';
import { Modal } from '../modal/modal';

@Component({
  selector: 'ui-confirm-dialog',
  imports: [Modal, Button],
  template: `
    <ui-modal [open]="open()" [title]="title()" (closed)="cancelled.emit()">
      <p class="text-sm text-neutral-600">{{ message() }}</p>
      <div class="flex justify-end gap-3">
        <ui-button variant="secondary" (click)="cancelled.emit()">{{ cancelLabel() }}</ui-button>
        <ui-button [variant]="danger() ? 'danger' : 'primary'" [loading]="loading()" (click)="confirmed.emit()">
          {{ confirmLabel() }}
        </ui-button>
      </div>
    </ui-modal>
  `,
})
export class ConfirmDialog {
  readonly open = input(false);
  readonly title = input('Confirmer');
  readonly message = input('');
  readonly confirmLabel = input('Confirmer');
  readonly cancelLabel = input('Annuler');
  readonly danger = input(false);
  readonly loading = input(false);

  readonly confirmed = output<void>();
  readonly cancelled = output<void>();
}
