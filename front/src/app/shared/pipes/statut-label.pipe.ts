import { Pipe, PipeTransform } from '@angular/core';

const LABELS: Record<string, string> = {
  EN_ATTENTE: 'En attente',
  CONFIRMEE: 'Confirmée',
  ANNULEE: 'Annulée',
  ACCEPTE: 'Accepté',
  REFUSE: 'Refusé',
  DISPONIBLE: 'Disponible',
  RESERVE: 'Réservé',
  BUREAU_PRIVE: 'Bureau privé',
  OPEN_SPACE: 'Open space',
  SALLE_REUNION: 'Salle de réunion',
  CARTE: 'Carte bancaire',
  VIREMENT: 'Virement',
  ESPECES: 'Espèces',
  membre: 'Membre',
  gestionnaire: 'Gestionnaire',
};

@Pipe({ name: 'statutLabel' })
export class StatutLabelPipe implements PipeTransform {
  transform(value: string | null | undefined): string {
    if (!value) {
      return '—';
    }
    return LABELS[value] ?? value;
  }
}
