import type { RunEvent } from '#shared/types/run'
import type { EntryKind, PhaseId, TimelineEntry } from '#shared/types/timeline'
import { buildTimeline } from '#shared/utils/timeline'

export interface TimelineFilters {
  kinds: EntryKind[]
  onlyProblems: boolean
  search: string
}

const PROBLEMS = new Set(['fail', 'warn'])

function matches(entry: TimelineEntry, filters: TimelineFilters): boolean {
  if (!filters.kinds.includes(entry.kind)) return false
  if (filters.onlyProblems && !PROBLEMS.has(entry.status) && !entry.attempts.some(a => PROBLEMS.has(a.status))) return false
  const query = filters.search.trim().toLowerCase()
  if (!query) return true
  const text = [entry.title, entry.subtitle, ...entry.details.map(d => d.text), ...entry.attempts.map(a => a.text)]
  return text.some(t => t.toLowerCase().includes(query))
}

/** The timeline of a run's events, filtered, and the phase to scroll to. */
export function useTimeline(events: MaybeRefOrGetter<RunEvent[]>) {
  const timeline = computed(() => buildTimeline(toValue(events)))
  const filters = reactive<TimelineFilters>({
    kinds: ['plan', 'graph', 'agent', 'task', 'queue', 'replan', 'evolution', 'end'],
    onlyProblems: false,
    search: '',
  })
  const entries = computed(() => timeline.value.entries.filter(entry => matches(entry, filters)))
  const phase = ref<PhaseId | null>(null)
  const visible = computed(() => (phase.value ? entries.value.filter(e => e.phase === phase.value) : entries.value))
  return { phases: computed(() => timeline.value.phases), filters, phase, entries: visible }
}
