import { existsSync, readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'bun:test'
import { parseJsonl } from '../shared/utils/events'
import { buildTimeline } from '../shared/utils/timeline'

// The last run of task 01 in the repository: the timeline has every plan version, task and queue of it.
const real = fileURLToPath(new URL('../../adk/workspace/benchmarks/01_rl_tictactoe/logs/events.jsonl', import.meta.url))

describe('buildTimeline on a real run', () => {
  it.skipIf(!existsSync(real))('reads the 2026-11-18 run of task 01', () => {
    const events = parseJsonl(readFileSync(real, 'utf-8'))
    const { entries, phases } = buildTimeline(events)
    const checks = entries.filter(e => e.title.startsWith('Weryfikacja planu'))
    const planners = entries.filter(e => e.title === 'Plan początkowy' || e.title.startsWith('Poprawka planu'))
    const tasks = entries.filter(e => e.kind === 'task')
    const started = new Set(events.filter(e => e.event === 'TASK_START').map(e => e.task_id))
    expect(checks.length).toBe(events.filter(e => e.event === 'PLAN_CHECKED').length)
    expect(planners.length).toBe(events.filter(e => e.event === 'LLM_CALL_START' && e.agent === 'task_planner' && !e.task_id).length)
    expect(planners[0]).toMatchObject({ title: 'Plan początkowy', status: 'ok' })
    expect(tasks.length).toBe(started.size)
    expect(entries.filter(e => e.kind === 'queue').length).toBe(events.filter(e => e.event === 'QUEUE_REBUILT').length)
    expect(phases.map(p => p.id)).toEqual(['planning', 'building', 'repairs', 'replans', 'end'])
  })
})
