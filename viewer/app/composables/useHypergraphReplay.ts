import type { Hypergraph } from '#shared/types/hypergraph'
import type { RunEvent } from '#shared/types/run'
import { graphElements } from '#shared/utils/graph'
import { stateChanges, statesAt } from '#shared/utils/replay'

const STEP_MS = 450

/** The hypergraph at a moment of the run: a slider over the vertex state changes, with play and pause. */
export function useHypergraphReplay(hypergraph: MaybeRefOrGetter<Hypergraph>, events: MaybeRefOrGetter<RunEvent[]>) {
  const changes = computed(() => stateChanges(toValue(events)))
  const applied = ref(Number.POSITIVE_INFINITY)
  const max = computed(() => changes.value.length)
  const position = computed({
    get: () => Math.min(applied.value, max.value),
    set: (value: number) => { applied.value = value },
  })
  const elements = computed(() => graphElements(toValue(hypergraph), statesAt(toValue(hypergraph), changes.value, position.value)))
  const current = computed(() => (position.value > 0 ? changes.value[position.value - 1] ?? null : null))

  const playing = ref(false)
  let timer: ReturnType<typeof setInterval> | undefined
  function stop() {
    playing.value = false
    clearInterval(timer)
  }
  function play() {
    if (position.value >= max.value) position.value = 0
    playing.value = true
    timer = setInterval(() => (position.value >= max.value ? stop() : position.value++), STEP_MS)
  }
  onBeforeUnmount(stop)

  return { elements, position, max, current, playing, play, stop }
}
