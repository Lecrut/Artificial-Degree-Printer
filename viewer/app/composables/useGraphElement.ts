import type { Hypergraph } from '#shared/types/hypergraph'
import { BAG_COLOR } from '#shared/utils/roles'
import { vertexStateColor } from '#shared/utils/states'
import { labels } from '~/utils/labels'

/** What a selection key (`v:<vertex>` or `e:<bag>`) points at: its id, kind, color and a one-line description. */
export function useGraphElement(
  hypergraph: MaybeRefOrGetter<Hypergraph>,
  selected: MaybeRefOrGetter<string | null>,
  states: MaybeRefOrGetter<Record<string, string>>,
) {
  const isVertex = computed(() => toValue(selected)?.startsWith('v:') ?? false)
  const id = computed(() => toValue(selected)?.slice(2) ?? '')
  const known = computed(() => id.value in (isVertex.value ? toValue(hypergraph).vertices : toValue(hypergraph).edges))
  const bagType = computed(() => toValue(hypergraph).edges[id.value]?.type ?? 'I')
  const state = computed(() => toValue(states)[id.value] ?? 'spec')
  const color = computed(() => (isVertex.value ? vertexStateColor(state.value) : BAG_COLOR[bagType.value]))
  const subtitle = computed(() => (isVertex.value
    ? `${toValue(hypergraph).vertices[id.value]?.kind ?? ''} · ${state.value}`
    : labels.graph.bagNames[bagType.value]))
  return { isVertex, id, known, state, color, subtitle }
}
