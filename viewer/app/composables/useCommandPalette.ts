import { mdiFlask, mdiHarddisk } from '@mdi/js'
import type { CommitSummary, TaskSummary } from '#shared/types/run'
import { runStatusColor } from '#shared/utils/states'
import { labels } from '~/utils/labels'
import type { NavPage } from '~/utils/nav'
import { runPage } from '~/utils/runUrls'

export interface PaletteItem {
  group: string
  title: string
  subtitle: string
  icon: string
  color: string
  to: string
}

const LIMIT = 40

/** Every page, then every run: the results on disk first, then each commit's tasks, newest first. */
function paletteItems(pages: NavPage[], commits: CommitSummary[], current: TaskSummary[]): PaletteItem[] {
  return [
    ...pages.map(p => ({ group: labels.nav.pages, title: p.title, subtitle: p.to, icon: p.icon, color: 'primary', to: p.to })),
    ...current.map(t => ({
      group: labels.nav.runs, title: t.task, subtitle: `${labels.nav.current} · ${t.status}`, icon: mdiHarddisk, color: runStatusColor(t.status),
      to: runPage({ source: 'results', ref: 'current', task: t.task }),
    })),
    ...commits.flatMap(c => c.tasks.map(t => ({
      group: labels.nav.runs, title: t.task, subtitle: `${c.message} · ${c.short} · ${t.status}`, icon: mdiFlask, color: runStatusColor(t.status),
      to: runPage({ source: 'git', ref: c.short, task: t.task }),
    }))),
  ]
}

/** The search palette (Ctrl K): every page and every run, filtered by all typed words, driven by the keyboard. */
export function useCommandPalette() {
  const open = useState('palette-open', () => false)
  const query = ref('')
  const active = ref(0)
  const { commits, current } = useHistory()
  const pages = useNavPages()

  const items = computed(() => paletteItems(pages.value, commits.data.value, current.data.value))

  const results = computed(() => {
    const words = query.value.toLowerCase().split(/\s+/).filter(Boolean)
    return items.value.filter(i => words.every(w => `${i.title} ${i.subtitle}`.toLowerCase().includes(w))).slice(0, LIMIT)
  })
  watch(query, () => { active.value = 0 })
  watch(open, (now) => { if (now) query.value = '' })

  function go(item: PaletteItem | undefined) {
    if (!item) return
    open.value = false
    void navigateTo(item.to)
  }
  function onKey(event: KeyboardEvent) {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault()
      open.value = !open.value
    }
    if (!open.value) return
    const step = { ArrowDown: 1, ArrowUp: -1 }[event.key]
    if (step) {
      event.preventDefault()
      active.value = (active.value + step + results.value.length) % Math.max(1, results.value.length)
    }
    if (event.key === 'Enter') go(results.value[active.value])
  }
  onMounted(() => window.addEventListener('keydown', onKey))
  onBeforeUnmount(() => window.removeEventListener('keydown', onKey))

  const loading = computed(() => commits.pending.value || current.pending.value)

  return { open, query, active, results, loading, go }
}
