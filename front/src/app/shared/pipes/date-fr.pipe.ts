import { formatDate } from '@angular/common';
import { Pipe, PipeTransform } from '@angular/core';

export type DateFrFormat = 'date' | 'datetime' | 'time';

const ANGULAR_FORMATS: Record<DateFrFormat, string> = {
  date: 'dd/MM/yyyy',
  datetime: 'dd/MM/yyyy HH:mm',
  time: 'HH:mm',
};

@Pipe({ name: 'dateFr' })
export class DateFrPipe implements PipeTransform {
  transform(value: string | Date | null | undefined, format: DateFrFormat = 'date'): string {
    if (!value) {
      return '—';
    }
    try {
      return formatDate(value, ANGULAR_FORMATS[format], 'fr-FR');
    } catch {
      return '—';
    }
  }
}
