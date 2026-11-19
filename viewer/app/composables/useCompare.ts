import type { ComparedRun } from '#shared/types/compare'
import type { RunBundle } from '#shared/types/run'
import { MAX_COMPARED, parseRunKey, runKey, runProfile, SERIES_COLORS } from '#shared/utils/compare'
import { labels } from '~/utils/labels'
import { runApi } from '~/utils/runUrls'

export interface RunOption {
  value: string
  title: string
  subtitle: string
  label: string
}

/** The runs on the compare page: chosen in the URL (`?runs=git:sha:task,…`), each with a color it keeps. */
export function useCompare() {
  const route = useRoute()
  const router = useRouter()
  const { commits, current } = useHistory()

  const keys = computed<string[]>({
    get: () => String(route.query.runs ?? '').split(',').filter(k => parseRunKey(k)).slice(0, MAX_COMPARED),
    set: next => void router.replace({ query: { ...route.query, runs: next.slice(0, MAX_COMPARED).join(',') || undefined } }),
  })

  const options = computed<RunOption[]>(() => [
    ...current.data.value.map(t => ({ value: runKey({ source: 'results', ref: 'current', task: t.task }), title: t.task, subtitle: labels.nav.current, label: `${labels.nav.current} · ${t.task.slice(0, 2)}` })),
    ...commits.data.value.flatMap(c => c.tasks.map(t => ({
      value: runKey({ source: 'git', ref: c.short, task: t.task }),
      title: `${c.message} · ${t.task}`,
      subtitle: `${c.date.slice(0, 10)} · ${t.status}`,
      label: `${c.message} · ${t.task.slice(0, 2)}`,
    }))),
  ])

  // A run keeps its color while it stays selected; a removed run frees its color for the next one.
  const colors = reactive(new Map<string, string>())
  watch(keys, (next) => {
    for (const key of colors.keys()) if (!next.includes(key)) colors.delete(key)
    for (const key of next) if (!colors.has(key)) colors.set(key, SERIES_COLORS.find(c => ![...colors.values()].includes(c)) ?? SERIES_COLORS[0])
  }, { immediate: true })

  const { data: bundles, pending, error, refresh } = useAsyncData(
    () => `compare-${keys.value.join(',')}`,
    () => Promise.all(keys.value.map(key => $fetch<RunBundle>(runApi(parseRunKey(key)!)))),
    { watch: [keys], default: () => [] },
  )

  const runs = computed<ComparedRun[]>(() => (bundles.value ?? []).map((bundle, i) => {
    const key = keys.value[i] ?? runKey(bundle.ref)
    const profile = { ...runProfile(bundle.ref.task, bundle.events), summary: bundle.summary }
    return { at: bundle.ref, label: options.value.find(o => o.value === key)?.label ?? key, color: colors.get(key) ?? SERIES_COLORS[0], hasEvents: bundle.events.length > 0, profile }
  }))

  /** The same benchmark task in the newest commits that ran it. */
  function sameTask(task: string) {
    keys.value = commits.data.value.filter(c => c.tasks.some(t => t.task === task)).slice(0, MAX_COMPARED)
      .map(c => runKey({ source: 'git', ref: c.short, task }))
  }

  const optionsLoading = computed(() => commits.pending.value || current.pending.value)

  return { keys, options, optionsLoading, runs, pending, error, refresh, sameTask }
}
