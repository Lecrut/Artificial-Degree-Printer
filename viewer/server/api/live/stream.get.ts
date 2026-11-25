import type { LiveMessage } from '#shared/types/live'
import { eventsSince, liveState, liveTask, liveTraceStamp } from '../../utils/live'

const TICK_MS = 1000

function startTicker(send: (message: LiveMessage) => Promise<void>) {
  let task: string | null | undefined
  let offset = 0
  let stamp = ''
  let trace = ''
  let busy = false

  return async () => {
    if (busy) return
    busy = true
    try {
      const current = await liveTask()
      if (current !== task) {
        task = current
        offset = 0
        stamp = ''
        trace = ''
        await send({ type: 'run', task })
      }
      if (!task) return
      const fresh = await eventsSince(task, offset)
      offset = fresh.offset
      if (fresh.events.length) await send({ type: 'events', events: fresh.events })
      const nextTrace = await liveTraceStamp(task)
      if (nextTrace !== trace) await send({ type: 'trace', stamp: (trace = nextTrace) })
      const state = await liveState(task)
      if (state.stamp !== stamp) {
        stamp = state.stamp
        await send({ type: 'state', hypergraph: state.hypergraph, queue: state.queue })
      }
    }
    finally {
      busy = false
    }
  }
}

/** Server-sent events of the running sandbox: which task, appended events, trace changes, and the state when it changes. */
export default defineEventHandler((event) => {
  const stream = createEventStream(event)
  const tick = startTicker(message => stream.push(JSON.stringify(message)))
  const timer = setInterval(tick, TICK_MS)
  void tick()
  stream.onClosed(() => clearInterval(timer))
  return stream.send()
})
