import { BadgeTone } from './badge';

const TONES: Record<string, BadgeTone> = {
  CONFIRMEE: 'success',
  ACCEPTE: 'success',
  DISPONIBLE: 'success',
  EN_ATTENTE: 'warning',
  ANNULEE: 'danger',
  REFUSE: 'danger',
  RESERVE: 'neutral',
};

export function statutBadgeTone(statut: string): BadgeTone {
  return TONES[statut] ?? 'neutral';
}
