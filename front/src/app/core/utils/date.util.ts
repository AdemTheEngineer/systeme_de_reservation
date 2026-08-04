/** Local-calendar-day ISO string (`YYYY-MM-DD`) — never use `toISOString()` for
 * this, it converts to UTC first and silently shifts the date near midnight
 * in any timezone ahead of UTC. */
export function toLocalIsoDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function aujourdHuiIso(): string {
  return toLocalIsoDate(new Date());
}

export function premierJourDuMoisIso(): string {
  const now = new Date();
  return toLocalIsoDate(new Date(now.getFullYear(), now.getMonth(), 1));
}

export function dernierJourDuMoisIso(): string {
  const now = new Date();
  return toLocalIsoDate(new Date(now.getFullYear(), now.getMonth() + 1, 0));
}
