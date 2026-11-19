export function formatDuration(seconds: number | null): string {
  if (seconds === null) return '—'
  if (seconds < 60) return `${seconds.toFixed(0)} s`
  if (seconds < 3600) return `${(seconds / 60).toFixed(0)} min`
  return `${(seconds / 3600).toFixed(1)} h`
}

export function formatClock(ts: string | null | undefined): string {
  return ts ? ts.slice(11, 19) : ''
}

export function formatDate(ts: string | null | undefined): string {
  return ts ? ts.slice(0, 16).replace('T', ' ') : ''
}
