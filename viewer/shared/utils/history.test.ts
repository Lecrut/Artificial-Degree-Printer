import { describe, expect, it } from 'bun:test'
import type { CommitSummary, TaskSummary } from '../types/run'
import { entriesForCommit, parseAudit } from './audit'
import { changelogDays } from './changelogDays'
import { filterHistory, historyKpis, trend } from './historyStats'

const AUDIT = [
  '# Audyt VII — 2026-11-17: przebieg na żywo', 'wstęp',
  '## §VIII.1. Diagnoza', 'plan niewykonalny',
  '## §VIII.2. Realizacja (2026-11-18)', 'zrobione',
  '# Bez daty', '## brak', 'nic',
].join('\n')

const task = (name: string, status: string, done: number): TaskSummary => ({
  task: name, status, title: null, started: null, ended: null, durationSeconds: 3600, tasksTotal: 10, tasksDone: done,
  llmCalls: 100, failedVerdicts: 1, rejectedWrites: 0, planVersions: 1, replans: 0,
})
const commit = (sha: string, date: string, tasks: TaskSummary[]): CommitSummary => ({ sha, short: sha, date, message: sha, tasks })
const HISTORY = [
  commit('c', '2026-11-18T20:00:00+01:00', [task('01_rl', 'COMPLETED', 9), task('02_ml', 'CRASHED', 0)]),
  commit('b', '2026-11-17T20:00:00+01:00', [task('01_rl', 'COMPLETED_WITH_GAPS', 5)]),
  commit('a', '2026-11-10T20:00:00+01:00', [task('01_rl', 'COMPLETED', 3)]),
]

describe('audit and history', () => {
  it('dates audit sections from their heading or their chapter, and drops undated ones', () => {
    const entries = parseAudit(AUDIT)
    expect(entries.map(e => [e.title.slice(0, 10), e.date, e.level])).toEqual([
      ['Audyt VII ', '2026-11-17', 1], ['§VIII.1. D', '2026-11-17', 2], ['§VIII.2. R', '2026-11-18', 2],
    ])
    expect(entries[2]!.body).toBe('zrobione')
    expect(entriesForCommit(entries, '2026-11-18T21:00:00+01:00', '2026-11-17T21:00:00+01:00').map(e => e.date)).toEqual(['2026-11-18'])
  })

  it('filters commits by dates, tasks and statuses and sums them up', () => {
    const recent = filterHistory(HISTORY, { from: '2026-11-17', to: null, tasks: ['01_rl'], statuses: [] })
    expect(recent.map(c => c.sha)).toEqual(['c', 'b'])
    expect(recent.every(c => c.tasks.every(t => t.task === '01_rl'))).toBe(true)
    expect(historyKpis(recent)).toEqual({ commits: 2, runs: 2, completed: 1, llmCalls: 200, hours: 2 })
    expect(filterHistory(HISTORY, { from: null, to: null, tasks: [], statuses: ['CRASHED'] }).map(c => c.sha)).toEqual(['c'])
  })

  it('draws a task trend oldest first and groups the changelog by day', () => {
    expect(trend(HISTORY, '01_rl', 'tasksDone').map(p => ({ label: p.label, value: p.value }))).toEqual([{ label: '11-10', value: 3 }, { label: '11-17', value: 5 }, { label: '11-18', value: 9 }])
    expect(trend(HISTORY, '01_rl', 'tasksDone')[0]).toHaveProperty('sha')
    const days = changelogDays({ entries: parseAudit(AUDIT), commits: [] }, 'zrobione')
    expect(days.map(d => [d.day, d.entries.length])).toEqual([['2026-11-18', 1]])
  })
})
