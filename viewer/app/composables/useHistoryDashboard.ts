import type { CommitSummary } from '#shared/types/run'
import { filterHistory, historyKpis, statusesOf, tasksOf, trend, type TrendMetric } from '#shared/utils/historyStats'

export type RangePreset = 'all' | '3d' | '7d' | '14d' | 'custom'

const DAY_MS = 86_400_000
const isoDay = (date: Date) => date.toISOString().slice(0, 10)

/** Filters of the history dashboard (date range, tasks, statuses) and what they show: tiles, trend, commits. */
export function useHistoryDashboard(commits: MaybeRefOrGetter<CommitSummary[]>) {
  const preset = ref<RangePreset>('all')
  const custom = ref<Date[]>([])
  const tasks = ref<string[]>([])
  const statuses = ref<string[]>([])

  const range = computed(() => {
    if (preset.value === 'custom' && custom.value.length) {
      const days = custom.value.map(isoDay).sort()
      return { from: days[0] ?? null, to: days.at(-1) ?? null }
    }
    const days = { '3d': 3, '7d': 7, '14d': 14 }[preset.value as '3d' | '7d' | '14d']
    return { from: days ? isoDay(new Date(Date.now() - days * DAY_MS)) : null, to: null }
  })

  const filtered = computed(() => filterHistory(toValue(commits), { ...range.value, tasks: tasks.value, statuses: statuses.value }))
  const kpis = computed(() => historyKpis(filtered.value))

  const allTasks = computed(() => tasksOf(toValue(commits)))
  // The trend follows the first task until the user picks another one.
  const picked = ref<string | null>(null)
  const trendTask = computed({ get: () => picked.value ?? allTasks.value[0] ?? '', set: (task: string) => { picked.value = task } })
  const trendMetric = ref<TrendMetric>('tasksDone')
  const points = computed(() => trend(filtered.value, trendTask.value, trendMetric.value))

  return {
    preset, custom, tasks, statuses, filtered, kpis, trendTask, trendMetric, points,
    allTasks,
    allStatuses: computed(() => statusesOf(toValue(commits))),
  }
}
