import type { Hypergraph } from '#shared/types/hypergraph'
import type { LiveMessage, QueueTask } from '#shared/types/live'
import type { RunEvent, RunRef } from '#shared/types/run'
import { summarizeRun } from '#shared/utils/summary'

// New events reach the page at most once a second: each batch rebuilds the timeline, graph and board, and
// rebuilding on every message made every open dialog and expanding panel stutter.
const FLUSH_MS = 1000

/** The running sandbox, kept up to date by the server-sent stream `/api/live/stream`. */
export function useLiveRun() {
  const task = ref<string | null>(null)
  const events = shallowRef<RunEvent[]>([])
  const hypergraph = shallowRef<Hypergraph | null>(null)
  const queue = shallowRef<QueueTask[]>([])
  const traceStamp = ref('')
  const loaded = ref(false)

  let incoming: RunEvent[] = []
  let flushing: ReturnType<typeof setTimeout> | undefined
  function flush() {
    flushing = undefined
    if (incoming.length) events.value = [...events.value, ...incoming]
    incoming = []
  }

  function receive(message: LiveMessage) {
    if (message.type === 'run') {
      clearTimeout(flushing)
      incoming = []
      task.value = message.task
      events.value = []
      traceStamp.value = ''
      loaded.value = true
    }
    else if (message.type === 'events') {
      incoming.push(...message.events)
      if (!events.value.length) flush()
      else flushing ??= setTimeout(flush, FLUSH_MS)
    }
    else if (message.type === 'trace') traceStamp.value = message.stamp
    else {
      hypergraph.value = message.hypergraph
      queue.value = message.queue
    }
  }

  const { connected, failed, reconnect } = useEventStream<LiveMessage>('/api/live/stream', receive)
  onBeforeUnmount(() => clearTimeout(flushing))

  const summary = computed(() => (task.value ? summarizeRun(task.value, events.value) : null))
  const at = computed<RunRef | null>(() => (task.value ? { source: 'live', ref: 'current', task: task.value } : null))
  return { task, events, hypergraph, queue, traceStamp, connected, loaded, failed, reconnect, summary, at }
}
