import type { LiveMessage } from '#shared/types/live'
import { eventsSince, liveState, liveTask } from '../../utils/live'

const TICK_MS = 1000

/** Server-sent events of the running sandbox: which task, appended events, and the state when it changes. */
export default defineEventHandler((event) => {
  const stream = createEventStream(event)
  const send = (message: LiveMessage) => stream.push(JSON.stringify(message))
  let task: string | null | undefined
  let offset = 0
  let stamp = ''
  let busy = false

  const tick = async () => {
    if (busy) return
    busy = true
    try {
      const current = await liveTask()
      if (current !== task) {
        task = current
        offset = 0
        stamp = ''
        await send({ type: 'run', task })
      }
      if (!task) return
      const fresh = await eventsSince(task, offset)
      offset = fresh.offset
      if (fresh.events.length) await send({ type: 'events', events: fresh.events })
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

  const timer = setInterval(tick, TICK_MS)
  void tick()
  stream.onClosed(() => clearInterval(timer))
  return stream.send()
})
