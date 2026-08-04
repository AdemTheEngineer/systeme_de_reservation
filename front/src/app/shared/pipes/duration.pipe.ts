import { Pipe, PipeTransform } from '@angular/core';
import { formatDuree } from '../../core/utils/duration.util';

@Pipe({ name: 'duration' })
export class DurationPipe implements PipeTransform {
  transform(heureDebut: string | null | undefined, heureFin: string | null | undefined): string {
    if (!heureDebut || !heureFin) {
      return '—';
    }
    return formatDuree(heureDebut, heureFin);
  }
}
