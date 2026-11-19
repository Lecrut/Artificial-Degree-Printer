import type { AuditEntry, Changelog, CommitInfo } from '../types/changelog'
import { dayOf } from './audit'

export interface ChangelogDay {
  day: string
  commits: CommitInfo[]
  entries: AuditEntry[]
}

/** Commits and audit sections grouped by day, newest first; `query` keeps only sections that mention it. */
export function changelogDays(changelog: Changelog, query = ''): ChangelogDay[] {
  const needle = query.trim().toLowerCase()
  const entries = changelog.entries.filter(e => e.level === 2 && (!needle || `${e.title}\n${e.body}`.toLowerCase().includes(needle)))
  const days = new Map<string, ChangelogDay>()
  const day = (key: string) => {
    if (!days.has(key)) days.set(key, { day: key, commits: [], entries: [] })
    return days.get(key)!
  }
  if (!needle) for (const commit of changelog.commits) day(dayOf(commit.date)).commits.push(commit)
  for (const entry of entries) day(entry.date).entries.push(entry)
  return [...days.values()].sort((a, b) => b.day.localeCompare(a.day))
}
