import type { CommitSummary, TaskSummary } from '../types/run'

export interface HistoryFilter {
  from: string | null
  to: string | null
  tasks: string[]
  statuses: string[]
}

export type TrendMetric = 'tasksDone' | 'llmCalls' | 'failedVerdicts' | 'rejectedWrites' | 'durationMinutes'

/** Commits in the date range, each with only the tasks and statuses the filter keeps; empty commits drop out. */
export function filterHistory(commits: CommitSummary[], filter: HistoryFilter): CommitSummary[] {
  return commits
    .filter(c => (!filter.from || c.date.slice(0, 10) >= filter.from) && (!filter.to || c.date.slice(0, 10) <= filter.to))
    .map(c => ({
      ...c,
      tasks: c.tasks.filter(t => (!filter.tasks.length || filter.tasks.includes(t.task))
        && (!filter.statuses.length || filter.statuses.includes(t.status))),
    }))
    .filter(c => c.tasks.length)
}

export interface HistoryKpis {
  commits: number
  runs: number
  completed: number
  llmCalls: number
  hours: number
}

export function historyKpis(commits: CommitSummary[]): HistoryKpis {
  const runs = commits.flatMap(c => c.tasks)
  return {
    commits: commits.length,
    runs: runs.length,
    completed: runs.filter(t => t.status === 'COMPLETED').length,
    llmCalls: runs.reduce((sum, t) => sum + t.llmCalls, 0),
    hours: runs.reduce((sum, t) => sum + (t.durationSeconds ?? 0), 0) / 3600,
  }
}

const value = (t: TaskSummary, metric: TrendMetric) => (metric === 'durationMinutes' ? (t.durationSeconds ?? 0) / 60 : t[metric])

/** One task's metric across the commits, oldest first: the points of a trend line. */
/** One commit on the trend line: its value, and enough of the commit to name it on hover and to open it. */
export interface TrendPoint {
  label: string
  value: number
  date: string
  message: string
  sha: string
  short: string
  status: string
}

export function trend(commits: CommitSummary[], task: string, metric: TrendMetric): TrendPoint[] {
  return [...commits].reverse().flatMap((c) => {
    const run = c.tasks.find(t => t.task === task)
    if (!run) return []
    const point = { label: c.date.slice(5, 10), value: Math.round(value(run, metric) * 10) / 10 }
    return [{ ...point, date: c.date, message: c.message, sha: c.sha, short: c.short, status: run.status }]
  })
}

export function statusesOf(commits: CommitSummary[]): string[] {
  return [...new Set(commits.flatMap(c => c.tasks.map(t => t.status)))].sort()
}

export function tasksOf(commits: CommitSummary[]): string[] {
  return [...new Set(commits.flatMap(c => c.tasks.map(t => t.task)))].sort()
}
