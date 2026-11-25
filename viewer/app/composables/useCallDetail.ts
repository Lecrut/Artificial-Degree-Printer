import type { AgentCallDetail } from '#shared/types/calls'
import type { RunRef } from '#shared/types/run'
import { callApi } from '~/utils/runUrls'

/** One agent call with its prompt, payload and answer, fetched when shown and refreshed when its state changes. */
export function useCallDetail(
  at: MaybeRefOrGetter<RunRef>,
  step: MaybeRefOrGetter<number>,
  state?: MaybeRefOrGetter<string | undefined>,
) {
  return useFetch<AgentCallDetail>(() => callApi(toValue(at), toValue(step)), {
    lazy: true,
    watch: [() => toValue(state)],
  })
}
