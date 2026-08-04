import { Component, forwardRef, input } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

let nextId = 0;

@Component({
  selector: 'ui-input',
  template: `
    <div class="flex flex-col gap-1.5">
      @if (label()) {
        <label [for]="id" class="text-sm font-medium text-neutral-700">
          {{ label() }}
          @if (required()) {
            <span class="text-rose-600">*</span>
          }
        </label>
      }
      <input
        [id]="id"
        [type]="type()"
        [placeholder]="placeholder()"
        [disabled]="disabled"
        [required]="required()"
        [value]="value"
        (input)="onInput($event)"
        (blur)="onTouched()"
        [attr.aria-invalid]="!!errorMessage()"
        [attr.aria-describedby]="errorMessage() ? id + '-error' : null"
        class="h-10 rounded-lg border bg-white px-3 text-sm text-neutral-900 placeholder:text-neutral-400
               focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue
               disabled:bg-neutral-100 disabled:text-neutral-400"
        [class.border-neutral-300]="!errorMessage()"
        [class.border-rose-400]="!!errorMessage()"
      />
      @if (errorMessage()) {
        <p [id]="id + '-error'" class="text-xs text-rose-600">{{ errorMessage() }}</p>
      } @else if (hint()) {
        <p class="text-xs text-neutral-500">{{ hint() }}</p>
      }
    </div>
  `,
  providers: [{ provide: NG_VALUE_ACCESSOR, useExisting: forwardRef(() => Input), multi: true }],
})
export class Input implements ControlValueAccessor {
  protected readonly id = `ui-input-${nextId++}`;

  readonly label = input<string>('');
  readonly type = input<string>('text');
  readonly placeholder = input<string>('');
  readonly required = input(false);
  readonly hint = input<string>('');
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
    const target = event.target as HTMLInputElement;
    this.value = target.value;
    this.onChange(this.value);
  }
}
