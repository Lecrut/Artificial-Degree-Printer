import type { AuditEntry } from '../types/changelog'

const HEADING = /^(#{1,2}) (.+)$/
const DATE = /\b(20\d{2}-\d{2}-\d{2})\b/

/** The sections of the audit (`#` and `##` headings) with their day: their own date, else their chapter's. */
export function parseAudit(markdown: string): AuditEntry[] {
  const entries: AuditEntry[] = []
  let chapter = null as AuditEntry | null
  let current = null as AuditEntry | null
  const body: string[] = []

  const close = () => {
    if (current) current.body = body.join('\n').trim()
    body.length = 0
  }

  for (const line of markdown.split('\n')) {
    const heading = HEADING.exec(line)
    if (!heading) {
      body.push(line)
      continue
    }
    close()
    const level = heading[1]!.length as 1 | 2
    const title = heading[2]!.trim()
    const parent: AuditEntry | null = level === 2 ? chapter : null
    const date: string = DATE.exec(title)?.[1] ?? parent?.date ?? ''
    current = { id: `a${entries.length}`, level, title, date, parent: parent?.id ?? null, body: '' }
    if (level === 1) chapter = current
    entries.push(current)
  }
  close()
  return entries.filter(entry => entry.date)
}

/** Day of an ISO timestamp (`2026-11-18T22:10:00+01:00` → `2026-11-18`). */
export const dayOf = (iso: string) => iso.slice(0, 10)

/** Audit sections written after the previous commit and up to this one (by day). */
export function entriesForCommit(entries: AuditEntry[], date: string, previous: string | null): AuditEntry[] {
  const day = dayOf(date)
  const after = previous ? dayOf(previous) : ''
  return entries.filter(e => e.level === 2 && e.date <= day && (e.date > after || (!after && e.date === day)))
}
