import type { RunEvent, TaskSummary } from '../types/run'
import { count, str } from './events'

const END_EVENTS = new Set(['RUN_END', 'RUN_STOPPED'])

/** The headline numbers of one benchmark task, from its events. */
export function summarizeRun(task: string, events: RunEvent[], title: string | null = null): TaskSummary {
  const end = [...events].reverse().find(e => END_EVENTS.has(e.event))
  const started = new Set(events.filter(e => e.event === 'TASK_START').map(e => str(e, 'task_id')))
  const done = new Set(events.filter(e => e.event === 'TASK_DONE').map(e => str(e, 'task_id')))
  return {
    task,
    status: end ? str(end, 'status') || str(end, 'reason') : events.length ? 'RUNNING' : 'NO_EVENTS',
    title,
    started: events[0]?.ts ?? null,
    ended: events.at(-1)?.ts ?? null,
    durationSeconds: events.length > 1 ? (Date.parse(events.at(-1)!.ts) - Date.parse(events[0]!.ts)) / 1000 : null,
    tasksTotal: started.size,
    tasksDone: done.size,
    llmCalls: count(events, 'LLM_CALL_END'),
    failedVerdicts: events.filter(e => e.event === 'VERDICT' && str(e, 'status') === 'FAIL').length,
    rejectedWrites: count(events, 'SPEC_WRITE_REJECTED') + count(events, 'BUILDER_ANSWER_REJECTED'),
    planVersions: count(events, 'PLAN_CHECKED'),
    replans: count(events, 'REPLANNED') + count(events, 'QUEUE_REBUILT'),
  }
}
