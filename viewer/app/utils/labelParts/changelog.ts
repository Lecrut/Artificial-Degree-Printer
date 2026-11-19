export const changelogLabels = {
  title: 'Postęp prac',
  subtitle: 'sekcje audytu (audit_repairs.md) i commity, dzień po dniu',
  search: 'szukaj w audycie',
  day: (day: string) => new Date(`${day}T12:00:00`).toLocaleDateString('pl-PL', { weekday: 'long', day: 'numeric', month: 'long' }),
  counts: (commits: number, entries: number) => `${commits} commitów · ${entries} sekcji audytu`,
}
