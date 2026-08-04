import { Component, forwardRef, input, output } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

@Component({
  selector: 'ui-toggle',
  template: `
    <button
      type="button"
      role="switch"
      [attr.aria-checked]="displayValue()"
      [attr.aria-label]="label()"
      [disabled]="disabled"
      (click)="onToggle()"
      class="relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors
             focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue focus-visible:ring-offset-2
             disabled:opacity-50 disabled:cursor-not-allowed"
      [class]="displayValue() ? 'bg-brand-blue' : 'bg-neutral-300'"
    >
      <span class="inline-block size-4 transform rounded-full bg-white transition-transform" [class]="displayValue() ? 'translate-x-6' : 'translate-x-1'"></span>
    </button>
  `,
  providers: [{ provide: NG_VALUE_ACCESSOR, useExisting: forwardRef(() => Toggle), multi: true }],
})
export class Toggle implements ControlValueAccessor {
  readonly label = input<string>('');
  /** Standalone (non-form) usage: pass the current value directly. */
  readonly checked = input<boolean | undefined>(undefined);
  readonly toggled = output<boolean>();

  protected value = false;
  protected disabled = false;

  private onChange: (value: boolean) => void = () => {};
  private onTouched: () => void = () => {};

  writeValue(value: boolean | null): void {
    this.value = value ?? false;
  }

  registerOnChange(fn: (value: boolean) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }

  protected displayValue(): boolean {
    return this.checked() ?? this.value;
  }

  protected onToggle(): void {
    const next = !this.displayValue();
    this.value = next;
    this.onChange(next);
    this.onTouched();
    this.toggled.emit(next);
  }
}
