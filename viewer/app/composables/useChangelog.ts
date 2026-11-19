import type { AuditEntry, Changelog, CommitInfo } from '#shared/types/changelog'
import { entriesForCommit } from '#shared/utils/audit'

/** The audit's sections and all commits, shared by the history and the changelog pages. */
export function useChangelog() {
  const { data, pending, error, refresh } = useFetch<Changelog>('/api/changelog', { key: 'changelog', default: () => ({ entries: [], commits: [] }) })

  const commits = computed(() => data.value.commits)
  const byCommit = computed(() => {
    const map = new Map<string, AuditEntry[]>()
    commits.value.forEach((commit, i) => map.set(commit.sha, entriesForCommit(data.value.entries, commit.date, commits.value[i + 1]?.date ?? null)))
    return map
  })
  const info = (sha: string): CommitInfo | undefined => commits.value.find(c => c.sha === sha)

  return { data, pending, error, refresh, commits, byCommit, info }
}
