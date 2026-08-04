import { Pipe, PipeTransform } from '@angular/core';
import { formatTnd } from '../../core/utils/currency.util';

@Pipe({ name: 'currencyTnd' })
export class CurrencyTndPipe implements PipeTransform {
  transform(value: string | number | null | undefined): string {
    if (value === null || value === undefined) {
      return '—';
    }
    return formatTnd(value);
  }
}
