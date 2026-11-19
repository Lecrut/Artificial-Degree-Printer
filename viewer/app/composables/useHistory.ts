import type { CommitSummary, TaskSummary } from '#shared/types/run'

/** Commits with benchmark results, and the results on disk now. */
export function useHistory() {
  const commits = useFetch<CommitSummary[]>('/api/history', { default: () => [] })
  const current = useFetch<TaskSummary[]>('/api/runs/results/current', { default: () => [] })
  return { commits, current }
}
