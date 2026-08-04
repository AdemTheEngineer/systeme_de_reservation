import { Component, forwardRef, input } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

let nextId = 0;

@Component({
  selector: 'ui-textarea',
  template: `
    <div class="flex flex-col gap-1.5">
      @if (label()) {
        <label [for]="id" class="text-sm font-medium text-neutral-700">{{ label() }}</label>
      }
      <textarea
        [id]="id"
        [placeholder]="placeholder()"
        [disabled]="disabled"
        [rows]="rows()"
        [value]="value"
        (input)="onInput($event)"
        (blur)="onTouched()"
        class="rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900 placeholder:text-neutral-400
               focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue
               disabled:bg-neutral-100 disabled:text-neutral-400"
      ></textarea>
      @if (errorMessage()) {
        <p class="text-xs text-rose-600">{{ errorMessage() }}</p>
      }
    </div>
  `,
  providers: [{ provide: NG_VALUE_ACCESSOR, useExisting: forwardRef(() => Textarea), multi: true }],
})
export class Textarea implements ControlValueAccessor {
  protected readonly id = `ui-textarea-${nextId++}`;

  readonly label = input<string>('');
  readonly placeholder = input<string>('');
  readonly rows = input(3);
  readonly errorMessage = input<string>('');

  protected value = '';
  protected disabled = false;

  private onChange: (value: string) => void = () => {};
  protected onTouched: () => void = () => {};

  writeValue(value: string | null): void {
    this.value = value ?? '';
  }

  registerOnChange(fn: (value: string) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }

  protected onInput(event: Event): void {
    const target = event.target as HTMLTextAreaElement;
    this.value = target.value;
    this.onChange(this.value);
  }
}
