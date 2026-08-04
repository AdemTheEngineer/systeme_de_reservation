import { Component, forwardRef, input } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

export interface SelectOption {
  value: string;
  label: string;
}

let nextId = 0;

@Component({
  selector: 'ui-select',
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
      <select
        [id]="id"
        [disabled]="disabled"
        [required]="required()"
        [value]="value"
        (change)="onSelect($event)"
        (blur)="onTouched()"
        class="h-10 rounded-lg border border-neutral-300 bg-white px-3 text-sm text-neutral-900
               focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue
               disabled:bg-neutral-100 disabled:text-neutral-400"
      >
        @if (placeholder()) {
          <option value="" disabled selected>{{ placeholder() }}</option>
        }
        @for (option of options(); track option.value) {
          <option [value]="option.value">{{ option.label }}</option>
        }
      </select>
      @if (errorMessage()) {
        <p class="text-xs text-rose-600">{{ errorMessage() }}</p>
      }
    </div>
  `,
  providers: [{ provide: NG_VALUE_ACCESSOR, useExisting: forwardRef(() => Select), multi: true }],
})
export class Select implements ControlValueAccessor {
  protected readonly id = `ui-select-${nextId++}`;

  readonly label = input<string>('');
  readonly placeholder = input<string>('');
  readonly options = input<SelectOption[]>([]);
  readonly required = input(false);
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

  protected onSelect(event: Event): void {
    const target = event.target as HTMLSelectElement;
    this.value = target.value;
    this.onChange(this.value);
  }
}
