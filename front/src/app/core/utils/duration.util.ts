function parseTimeToMinutes(time: string): number {
  const [hoursPart, minutesPart] = time.split(':');
  const hours = Number(hoursPart ?? 0);
  const minutes = Number(minutesPart ?? 0);
  return hours * 60 + minutes;
}

export function dureeEnHeures(heureDebut: string, heureFin: string): number {
  const minutes = parseTimeToMinutes(heureFin) - parseTimeToMinutes(heureDebut);
  return Math.max(minutes, 0) / 60;
}

export function formatDuree(heureDebut: string, heureFin: string): string {
  const heures = dureeEnHeures(heureDebut, heureFin);
  const heuresEntieres = Math.floor(heures);
  const minutes = Math.round((heures - heuresEntieres) * 60);
  return minutes > 0 ? `${heuresEntieres}h${minutes.toString().padStart(2, '0')}` : `${heuresEntieres}h`;
}

export function calculerMontant(tarifHoraire: string | number, heureDebut: string, heureFin: string): number {
  const tarif = typeof tarifHoraire === 'string' ? Number(tarifHoraire) : tarifHoraire;
  return tarif * dureeEnHeures(heureDebut, heureFin);
}
